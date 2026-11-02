#!/usr/bin/env python3
"""
BALLON D'OR 100% (idea de la IA de YouTube Studio, misma mecánica que el STOP): la superestrella de cuerpo entero en el estadio,
con la SILUETA del Balón de Oro marcada en sus manos. El trofeo real orbita y gira; el espectador pausa cuando calza en la
silueta (100%). Arriba un medidor gigante de % que sube a medida que se acerca. Loop perfecto (vueltas enteras).
Uso: python3 produccion/render_balon.py guion.json
guion: {"id", "cuerpo": "lionel_messi_3", "nombre": "Messi", "trofeo": "balon_oro_0", "dur": 6.0, "vueltas": 3, "fondo": "estadio_0"}
"""
import json
import math
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import gancho as G
import motor as M
import render_plinko as P
import render_rueda as R

ROOT = Path(__file__).resolve().parent
W, H, FPS = 1080, 1920, 30
EXT = ROOT / "assets" / "recortes" / "extras"
T_ENCAJE = 0.45


def cuerpo(nombre, alto=1180):
    im = Image.open(R.REC / "cuerpos" / f"{nombre}.png").convert("RGBA")
    x, y, fw, fh = R.cara(im)
    s = alto / im.height
    im = im.resize((int(im.width * s), alto), Image.LANCZOS)
    return im, dict(cx=(x + fw / 2) * s, cara_y=y * s, fh=fh * s)


def trofeo(nombre, alto=330):
    im = Image.open(EXT / f"{nombre}.png").convert("RGBA")
    s = alto / im.height
    return im.resize((int(im.width * s), alto), Image.LANCZOS)


def silueta(tr):
    """Hueco con la forma del trofeo: negro translúcido + borde blanco punteado que late."""
    a = tr.split()[3].point(lambda v: 255 if v > 60 else 0)
    hueco = Image.new("RGBA", tr.size, (10, 10, 10, 0)); hueco.putalpha(a.point(lambda v: int(v * 0.72)))
    borde = a.filter(ImageFilter.MaxFilter(9)); arr = np.asarray(borde).astype(int) - np.asarray(a).astype(int)
    b = Image.new("RGBA", tr.size, (255, 255, 255, 0)); b.putalpha(Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)))
    hueco.alpha_composite(b)
    return hueco


def main(guion):
    g = json.loads(Path(guion).read_text())
    out = ROOT / "salida" / g["id"]; out.mkdir(parents=True, exist_ok=True)
    dur = g.get("dur", 6.0); vueltas = g.get("vueltas", 3)
    fondo = R.fondo(g.get("fondo", "estadio_0")).copy()
    cu, info = cuerpo(g["cuerpo"])
    x0 = int(W / 2 - info["cx"]); y0 = 1840 - cu.height
    fondo.alpha_composite(cu, (x0, y0))
    tr = trofeo(g.get("trofeo", "trofeo_bo_1"))
    tx, ty = W / 2, y0 + info["cara_y"] + info["fh"] * 3.6                    # a la altura de las manos
    sil = silueta(tr)
    RX, RY = 215, 270
    fase = math.pi - 2 * math.pi * vueltas * T_ENCAJE / dur                   # calza a los 0,45 s (la costura cae en plena tensión)

    def pos(t):
        th = 2 * math.pi * vueltas * t / dur + fase
        return tx + RX + RX * math.cos(th), ty + RY * math.sin(th), th

    encajes = [((math.pi - fase) / (2 * math.pi) + k) * dur / vueltas for k in range(vueltas)]
    encajes = [e % dur for e in encajes]
    tx_g = G.elegir("rueda", g["id"], g["nombre"])
    tx_g = dict(tx_g, gancho=f"FREEZE IT AT 100%", apuesta=f"BALLON D'OR FOR {g['nombre'].upper()}?",
                cta="COMMENT YOUR % · FOLLOW FOR PART 2")
    mudo = out / "mudo.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", str(mudo)], stdin=subprocess.PIPE)
    for f in range(int(round(dur * FPS))):
        t = f / FPS
        im = fondo.copy()
        pulso = 0.6 + 0.4 * abs(math.sin(t * 2 * math.pi * 1.1))
        s2 = sil.copy(); s2.putalpha(s2.split()[3].point(lambda v: int(v * pulso)))
        im.alpha_composite(s2, (int(tx - tr.width / 2), int(ty - tr.height / 2)))
        x, y, th = pos(t)
        ang = 25 * math.sin(th * 2)                                            # el trofeo se bambolea (en el encaje queda derecho)
        rot = tr.rotate(ang, resample=Image.BICUBIC, expand=True)
        im.alpha_composite(rot, (int(x - rot.width / 2), int(y - rot.height / 2)))
        dist = math.hypot(x - tx, y - ty)
        pct = max(0, min(100, round(100 * (1 - dist / (2 * RX)) ** 1.6)))
        de = min(min(abs(t - e), dur - abs(t - e)) for e in encajes)
        if de < 1 / FPS:
            pct = 100
        d = ImageDraw.Draw(im)
        col = (255, 215, 0) if pct >= 98 else ((255, 255, 255) if pct < 80 else (255, 150, 40))
        P.texto(d, (W / 2, 420), f"{pct}%", 190, col, 14, (20, 20, 30))
        P.texto(d, (W / 2, 1880 - 30), g["nombre"].upper(), 64, (255, 255, 255), 9, (20, 20, 30))
        tras = min(((t - x_) % dur) for x_ in encajes)                       # solo DESPUÉS del encaje (no delata)
        if tras < 0.4:
            e = tras
            if e < 0.12:
                im.alpha_composite(Image.new("RGBA", (W, H), (255, 215, 0, int(70 * (1 - e / 0.12)))))
                d = ImageDraw.Draw(im)
            P.texto(d, (W / 2, 610), "PERFECT!", int(120 * min(1, 0.6 + e * 4)), (255, 230, 40), 12)
        im = G.capa(im, t, dur, tx_g, 120, sin_fin=True)
        p.stdin.write(np.asarray(im.convert("RGB"), np.uint8).tobytes())
    p.stdin.close(); p.wait()
    sr = M.SR; n = int(dur * sr); fx = np.zeros(n, np.float32)

    def add(t0, sig, v=1.0):
        a = int(t0 * sr) % n; b = min(n, a + len(sig)); fx[a:b] += sig[: b - a] * v
    for e in encajes:
        add(e, M.ding(0.6), 0.7); add(e, M.boom(0.5), 0.45)
    add(0, G.silbato(sr), 1.0)
    mu = P.musica(g, dur)
    M.mezclar(out, mudo, {"short.mp4": np.tanh((mu * 0.75 + fx) * 1.1) * 0.9, "short_solo_efectos.mp4": np.tanh(fx * 1.1) * 0.85})
    print(out / "short.mp4", dur, "s")


if __name__ == "__main__":
    main(sys.argv[1])
