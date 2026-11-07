#!/usr/bin/env python3
"""
HEAD FIT (tendencia "99.9% WILL FAIL the FIT challenge", 6,6 M): abajo el cuerpo de una superestrella SIN cabeza con la etiqueta
roja "TARGET" y una flecha; arriba una rueda de 8 CABEZAS recortadas que gira. Pausar cuando la cabeza correcta calza en el cuello.
Distinto a WHEEL (ahí giran torsos): acá giran caras, más grandes y graciosas. Loop perfecto (vueltas enteras).
Uso: python3 produccion/render_cabezas.py guion.json
guion: {"id", "cuerpo": "kylian_mbapp_13", "clave": "kylian_mbapp", "nombre": "Mbappé", "cabezas": [7 claves], "dur": 8.0, "vueltas": 2}
"""
import json
import math
import subprocess
import sys
from functools import lru_cache
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import caras_find as CF
import gancho as G
import motor as M
import render_plinko as P
import render_rueda as R

ROOT = Path(__file__).resolve().parent
W, H, FPS = 1080, 1920, 30
FOTOS = json.loads((ROOT / "assets" / "fotos" / "frontales.json").read_text())
ALTO_CABEZA = 255
T_ENCAJE = 0.45          # encaje en la costura del loop: nunca hay un "ya se resolvió" (Studio 07/11)


@lru_cache(maxsize=32)
def cabeza(clave):
    """Cabeza recortada (cara + pelo) con borde suave, de ALTO_CABEZA px; devuelve (img, y_menton)."""
    img, p = CF.base(FOTOS.get(clave, clave + "_0"), 1.6)
    A = np.linalg.norm(p[16] - p[0]); cx = (p[0, 0] + p[16, 0]) / 2
    cejas = p[17:27, 1].min(); menton = p[8, 1]
    h, w = img.shape[:2]
    m = np.zeros((h, w), np.uint8)
    cyh = (cejas - A * 0.55 + menton) / 2
    cv2.ellipse(m, (int(cx), int(cyh)), (int(A * 0.64), int((menton - (cejas - A * 0.55)) / 2 + A * 0.04)), 0, 0, 360, 255, -1)
    m = cv2.GaussianBlur(m, (0, 0), 3)
    rgba = np.dstack([img[..., ::-1], m])
    im = Image.fromarray(rgba).crop(Image.fromarray(m).getbbox())
    y_menton = menton - Image.fromarray(m).getbbox()[1]
    s = ALTO_CABEZA / im.height
    im = im.resize((int(im.width * s), ALTO_CABEZA), Image.LANCZOS)
    borde = im.split()[3].filter(ImageFilter.MaxFilter(7))
    out = Image.new("RGBA", im.size, (255, 255, 255, 0)); out.putalpha(borde); out.alpha_composite(im)
    return out, y_menton * s


def cuerpo_sin_cabeza(nombre, alto=900):
    im = Image.open(R.REC / "cuerpos" / f"{nombre}.png").convert("RGBA")
    x, y, fw, fh = R.cara(im)
    s = alto / (im.height - (y + fh * 1.02))
    im = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
    corte = int((y + fh * 1.02) * s)                                           # justo debajo del mentón
    c = im.crop((0, corte, im.width, im.height))
    return c, (x + fw / 2) * s


def main(guion):
    g = json.loads(Path(guion).read_text())
    out = ROOT / "salida" / g["id"]; out.mkdir(parents=True, exist_ok=True)
    dur = g.get("dur", 8.0); vueltas = g.get("vueltas", 2)
    fondo = R.fondo(g.get("fondo", "estadio_0")).copy()
    cu, cx_cu = cuerpo_sin_cabeza(g["cuerpo"])
    x_cu = int(W / 2 - cx_cu); y_cu = 1870 - cu.height
    fondo.alpha_composite(cu, (x_cu, y_cu))
    d = ImageDraw.Draw(fondo)                                                  # etiqueta TARGET + flecha al cuello
    d.rounded_rectangle([W / 2 + 150, y_cu + 120, W / 2 + 430, y_cu + 210], 22, fill=(225, 25, 30), outline=(255, 255, 255), width=5)
    P.texto(d, (W / 2 + 290, y_cu + 165), "TARGET", 54, (255, 255, 255), 0)
    d.line([(W / 2 + 150, y_cu + 165), (W / 2 + 60, y_cu + 40)], fill=(225, 25, 30), width=14)
    d.polygon([(W / 2 + 40, y_cu + 10), (W / 2 + 95, y_cu + 40), (W / 2 + 50, y_cu + 75)], fill=(225, 25, 30))
    P.texto(d, (W / 2, 1880), g["nombre"].upper(), 60, (255, 255, 255), 9, (20, 20, 30))
    piezas = [cabeza(k) for k in g["cabezas"]]
    k_ok = g.get("pos_correcto", 3); piezas.insert(k_ok, cabeza(g["clave"]))
    n = len(piezas); paso = 360 / n
    r = 290
    cuello = (W / 2, y_cu + 10)
    centro = (cuello[0], cuello[1] - r - piezas[k_ok][1] + ALTO_CABEZA / 2 - 10)
    vel = g.get("sentido", 1) * 360.0 * vueltas / dur
    base = 90 - k_ok * paso - vel * T_ENCAJE
    encajes = [(T_ENCAJE + j * dur / vueltas) % dur for j in range(vueltas)]
    tx = dict(gancho=f"FIT {g['nombre'].upper()}'S HEAD", apuesta="99.9% IMPOSSIBLE", cta="COMMENT YOUR NUMBER · FOLLOW FOR PART 2")
    mudo = out / "mudo.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", str(mudo)], stdin=subprocess.PIPE)
    for f in range(int(round(dur * FPS))):
        t = f / FPS
        im = fondo.copy()
        a0 = base + vel * t
        capas = []
        for k, (img, ym) in enumerate(piezas):
            th = math.radians(a0 + k * paso)
            px, py = centro[0] + r * math.cos(th), centro[1] + r * math.sin(th)
            rot = img.rotate(90 - math.degrees(th), expand=True, resample=Image.BICUBIC)
            capas.append((math.sin(th), rot, px, py))
        for _, rot, px, py in sorted(capas, key=lambda c: c[0]):
            im.alpha_composite(rot, (int(px - rot.width / 2), int(py - rot.height / 2)))
        d = ImageDraw.Draw(im)
        num = int(((a0 - base) % 360) // paso) % n + 1
        P.texto(d, (110, 300), f"{num}.", 150, (255, 255, 255), 13, (230, 30, 30))
        tras = min(((t - e) % dur) for e in encajes)
        if tras < 0.5:
            if tras < 0.12:
                im.alpha_composite(Image.new("RGBA", (W, H), (60, 230, 90, int(60 * (1 - tras / 0.12)))))
                d = ImageDraw.Draw(im)
            P.texto(d, (W / 2, 1720), "PERFECT FIT!", int(110 * min(1, 0.6 + tras * 3)), (255, 230, 40), 12)
        im = G.capa(im, t, dur, tx, 120, sin_fin=True)
        p.stdin.write(np.asarray(im.convert("RGB"), np.uint8).tobytes())
    p.stdin.close(); p.wait()
    sr = M.SR; nm = int(dur * sr); fx = np.zeros(nm, np.float32)

    def add(t0, sig, v=1.0):
        a = int(t0 * sr) % nm; b = min(nm, a + len(sig)); fx[a:b] += sig[: b - a] * v
    k = 0.0
    while k < dur:
        add(k, M.golpe(0.05), 0.3); k += paso / abs(vel)
    for e in encajes:
        add(e, M.ding(0.6), 0.6); add(e, M.boom(0.5), 0.4)
    add(0, G.silbato(sr), 1.0)
    mu = P.musica(g, dur)
    M.mezclar(out, mudo, {"short.mp4": np.tanh((mu * 0.75 + fx) * 1.1) * 0.9, "short_solo_efectos.mp4": np.tanh(fx * 1.1) * 0.85})
    print(out / "short.mp4", dur, "s encajes", [round(e, 2) for e in encajes])


if __name__ == "__main__":
    main(sys.argv[1])
