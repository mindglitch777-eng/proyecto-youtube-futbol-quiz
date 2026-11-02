#!/usr/bin/env python3
"""
PENALTY 100 (idea de la IA de YouTube Studio, mecánica STOP): el arco de frente con el arquero moviéndose; una MIRA recorre el arco
y pasa por el ÁNGULO de arriba (zona 100). El espectador pausa cuando la mira está en el ángulo. Arriba, el % gigante sube a medida
que la mira se acerca al ángulo. En el 100: la pelota vuela al ángulo, la red se sacude, "GOLAZO!" y el relato.
El que patea es una superestrella (cara grande abajo, regla fija). Loop perfecto (vueltas enteras).
Uso: python3 produccion/render_penal.py guion.json
guion: {"id", "pateador": "lionel_messi", "nombre": "Messi", "arco": "arco_0", "arquero": "arquero_0", "dur": 6.0, "vueltas": 3}
"""
import json
import math
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import caras_find as CF
import gancho as G
import motor as M
import render_plinko as P
import render_rueda as R

ROOT = Path(__file__).resolve().parent
W, H, FPS = 1080, 1920, 30
EXT = ROOT / "assets" / "recortes" / "extras"
FOTOS = json.loads((ROOT / "assets" / "fotos" / "frontales.json").read_text())
T_ENCAJE = 0.45
GX0, GX1, GY0, GY1 = 90, 990, 560, 1130                                       # rectángulo del arco (boca)


def arco_img():
    f = EXT / "arco_1.png"
    if f.exists():
        im = Image.open(f).convert("RGBA")
        return im.resize((GX1 - GX0 + 80, GY1 - GY0 + 60), Image.LANCZOS)      # los palos coinciden con la zona de juego
    im = Image.new("RGBA", (GX1 - GX0 + 80, GY1 - GY0 + 60), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for x in range(40, im.width - 40, 34):                                     # red
        d.line([(x, 40), (x, im.height)], fill=(255, 255, 255, 90), width=3)
    for y in range(40, im.height, 34):
        d.line([(40, y), (im.width - 40, y)], fill=(255, 255, 255, 90), width=3)
    d.rectangle([22, 22, im.width - 22, 48], fill=(250, 250, 250)); d.rectangle([22, 22, 48, im.height], fill=(250, 250, 250))
    d.rectangle([im.width - 48, 22, im.width - 22, im.height], fill=(250, 250, 250))
    return im


def cara_circulo(clave, lado=300):
    img, _ = CF.base(FOTOS.get(clave, clave + "_0"), 1.25)
    im = Image.fromarray(img[..., ::-1]).resize((lado, lado), Image.LANCZOS).convert("RGBA")
    m = Image.new("L", (lado, lado), 0); ImageDraw.Draw(m).ellipse([0, 0, lado - 1, lado - 1], fill=255); im.putalpha(m)
    out = Image.new("RGBA", (lado + 20, lado + 20), (0, 0, 0, 0)); ImageDraw.Draw(out).ellipse([0, 0, lado + 19, lado + 19], fill=(255, 220, 0))
    out.alpha_composite(im, (10, 10))
    return out


def main(guion):
    g = json.loads(Path(guion).read_text())
    out = ROOT / "salida" / g["id"]; out.mkdir(parents=True, exist_ok=True)
    dur = g.get("dur", 6.0); vueltas = g.get("vueltas", 3)
    fondo = R.fondo(g.get("fondo", "estadio_0")).copy()
    arco = arco_img(); ax, ay = GX0 - 40, GY0 - 40
    arq = None
    if (EXT / f"{g.get('arquero', 'arquero_5')}.png").exists():
        a = Image.open(EXT / f"{g.get('arquero', 'arquero_5')}.png").convert("RGBA"); s = 470 / a.height
        arq = a.resize((int(a.width * s), 470), Image.LANCZOS)
    cara = cara_circulo(g.get("pateador", "lionel_messi"))
    pelota = None
    if (EXT / "pelota_1.png").exists():
        pelota = Image.open(EXT / "pelota_1.png").convert("RGBA").resize((120, 120), Image.LANCZOS)
    cx, cy = (GX0 + GX1) / 2, (GY0 + GY1) / 2
    rx, ry = (GX1 - GX0) / 2 * 0.86, (GY1 - GY0) / 2 * 0.80
    esq = (-math.pi / 4)                                                       # ángulo de la elipse donde está el ángulo de arriba a la derecha
    ex, ey = cx + rx * math.cos(esq) * 1.0, cy + ry * math.sin(esq)
    fase = esq - 2 * math.pi * vueltas * T_ENCAJE / dur

    def mira(t):
        th = 2 * math.pi * vueltas * t / dur + fase
        return cx + rx * math.cos(th), cy + ry * math.sin(th)

    goles = sorted(((T_ENCAJE + k * dur / vueltas) % dur) for k in range(vueltas))
    tx = dict(gancho="SHOOT AT 100%", apuesta=f"{g['nombre'].upper()} NEVER MISSES?", cta="COMMENT YOUR % · FOLLOW FOR PART 2")
    mudo = out / "mudo.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", str(mudo)], stdin=subprocess.PIPE)
    for f in range(int(round(dur * FPS))):
        t = f / FPS
        im = fondo.copy()
        tras = min(((t - e) % dur) for e in goles)
        temblor = int(8 * math.sin(tras * 60)) if tras < 0.25 else 0
        im.alpha_composite(arco, (ax, ay + temblor))
        d = ImageDraw.Draw(im)
        pul = 0.5 + 0.5 * abs(math.sin(t * 2 * math.pi * 1.5))                # zona 100 en el ángulo, latiendo
        d.ellipse([ex - 70, ey - 70, ex + 70, ey + 70], outline=(255, 215, 0, int(150 + 105 * pul)), width=8)
        P.texto(d, (ex, ey - 105), "100", 54, (255, 215, 0), 8, (20, 20, 30))
        if arq is not None:                                                    # el arquero va y viene
            kx = cx + 230 * math.sin(2 * math.pi * 2 * t / dur)
            im.alpha_composite(arq, (int(kx - arq.width / 2), int(GY1 + 20 - arq.height)))
        mx, my = mira(t)
        d = ImageDraw.Draw(im)
        for r_, w_ in ((52, 8), (14, 0)):
            if w_:
                d.ellipse([mx - r_, my - r_, mx + r_, my + r_], outline=(230, 30, 30), width=w_)
            else:
                d.ellipse([mx - r_, my - r_, mx + r_, my + r_], fill=(230, 30, 30))
        d.line([(mx - 80, my), (mx + 80, my)], fill=(230, 30, 30), width=6); d.line([(mx, my - 80), (mx, my + 80)], fill=(230, 30, 30), width=6)
        dist = math.hypot(mx - ex, my - ey)
        pct = max(0, min(99, round(100 * (1 - dist / 1400) ** 1.5)))
        if min(min(abs(t - e), dur - abs(t - e)) for e in goles) < 0.5 / FPS:
            pct = 100
        col = (255, 215, 0) if pct >= 98 else ((255, 255, 255) if pct < 85 else (255, 150, 40))
        P.texto(d, (W / 2, 330), f"{pct}%", 170, col, 14, (20, 20, 30))
        spot = (W / 2, 1560)                                                   # pelota en el punto penal o volando al ángulo
        if tras < 0.35:
            k = min(1, tras / 0.18); bx = spot[0] + (ex - spot[0]) * k; by = spot[1] + (ey - spot[1]) * k; tam = int(120 - 50 * k)
        else:
            bx, by, tam = spot[0], spot[1], 120
        if pelota is not None:
            im.alpha_composite(pelota.resize((tam, tam)), (int(bx - tam / 2), int(by - tam / 2)))
        else:
            d.ellipse([bx - tam / 2, by - tam / 2, bx + tam / 2, by + tam / 2], fill=(255, 255, 255), outline=(20, 20, 30), width=6)
        im.alpha_composite(cara, (int(W / 2 - cara.width / 2), 1600))
        d = ImageDraw.Draw(im)
        P.texto(d, (W / 2, 1600 + cara.height + 10), g["nombre"].upper(), 56, (255, 255, 255), 8, (20, 20, 30))
        if tras < 0.45:
            if tras < 0.12:
                im.alpha_composite(Image.new("RGBA", (W, H), (255, 255, 255, int(90 * (1 - tras / 0.12)))))
                d = ImageDraw.Draw(im)
            P.texto(d, (W / 2, 470), "GOLAZO!", int(130 * min(1, 0.6 + tras * 3)), (255, 230, 40), 12)
        im = G.capa(im, t, dur, tx, 120, sin_fin=True)
        p.stdin.write(np.asarray(im.convert("RGB"), np.uint8).tobytes())
    p.stdin.close(); p.wait()
    sr = M.SR; n = int(dur * sr); fx = np.zeros(n, np.float32)

    def add(t0, sig, v=1.0):
        if sig is None:
            return
        a = int(t0 * sr) % n; b = min(n, a + len(sig)); fx[a:b] += sig[: b - a] * v
    for e in goles:
        add(e, M.boom(0.5), 0.6); add(e, P.cargar("crowd_cheer_0", 0.6), 0.6)
    add(0, G.silbato(sr), 1.0)
    mu = P.musica(g, dur)
    M.mezclar(out, mudo, {"short.mp4": np.tanh((mu * 0.7 + fx) * 1.1) * 0.9, "short_solo_efectos.mp4": np.tanh(fx * 1.1) * 0.85})
    print(out / "short.mp4", dur, "s", "goles", [round(x, 2) for x in goles])


if __name__ == "__main__":
    main(sys.argv[1])
