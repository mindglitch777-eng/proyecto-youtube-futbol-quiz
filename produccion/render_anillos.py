#!/usr/bin/env python3
"""
FACE SPIN (23/11 · idea n.º 1 de la lista: "caras que giran y encajan", con vuelta propia).
La cara GIGANTE de una superestrella (≈85 % del ancho) cortada en 3 ANILLOS concéntricos que giran a distinta velocidad y en
sentidos opuestos: la cara está desarmada (los ojos de un lado, la boca del otro). Dos veces por loop los 3 anillos se frenan
un instante JUSTO alineados: hay que pausar cuando la cara queda armada. "PERFECT FACE!" solo mientras está armada (honesto).
Sin descargas: la foto frontal de siempre (assets/fotos), con borde dorado entre anillos. Loop perfecto (vueltas enteras).

Uso: python3 produccion/render_anillos.py guion.json
guion: {"id", "clave": "lionel_messi", "nombre": "Messi", "dur": 7.0, "giros": [2, -4, 6], "t_encaje": 1.2, "quieto": 0.06,
        "musica", "fondo"}
"""
import json
import math
import subprocess
import sys
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import gancho as G
import motor as M
import render_plinko as P
import render_rueda as R

ROOT = Path(__file__).resolve().parent
W, H, FPS = 1080, 1920, 30
D = 940                                    # diámetro de la cara
CY = 980                                   # centro vertical de la cara
CORTES = (0.36, 0.68)                      # radios relativos de los cortes entre anillos
TOL = 2.5                                  # grados: dentro de esto la cara cuenta como armada


@lru_cache(maxsize=4)
def anillos(clave):
    cara = P.cara(clave, D)
    yy, xx = np.mgrid[0:D, 0:D].astype(np.float32)
    rr = np.hypot(xx - D / 2, yy - D / 2) / (D / 2)
    lim = (0.0,) + CORTES + (1.01,)
    out = []
    for i in range(3):
        m = ((rr >= lim[i]) & (rr < lim[i + 1])).astype(np.uint8) * 255
        im = cara.copy()
        a = np.minimum(np.asarray(im.split()[3]), m)
        im.putalpha(Image.fromarray(a))
        out.append(im)
    return out


@lru_cache(maxsize=2)
def bordes():
    im = Image.new("RGBA", (D + 60, D + 60), (0, 0, 0, 0)); d = ImageDraw.Draw(im); c = (D + 60) / 2
    for rel in CORTES + (1.0,):
        r = rel * D / 2
        d.ellipse([c - r - 5, c - r - 5, c + r + 5, c + r + 5], outline=(255, 205, 50), width=10)
    return im


def fase(g, t):
    """Avance en 'medios loops' desde el encaje, a saltos: se frena `quieto` (fracción) justo en cada alineación."""
    n = math.gcd(*[abs(x) for x in g["giros"]])                               # alineaciones por loop
    u = (t - g["t_encaje"]) / g["dur"] * n + g.get("quieto", 0.06) / 2
    b = math.floor(u); x = u - b
    q = g.get("quieto", 0.06)
    x = min(1.0, max(0.0, (x - q) / (1 - q)))
    return (b + x * x * (3 - 2 * x)) / n                                      # en loops


def angulos(g, t):
    f = fase(g, t)
    return [k * 360.0 * f for k in g["giros"]]


def armada(angs):
    return all(min(a % 360, 360 - a % 360) <= TOL for a in angs)


def cuadro(g, A, t):
    im = A["fondo"].copy()
    angs = angulos(g, t); ok = armada(angs)
    cx = W / 2
    for img, a in zip(A["anillos"], angs):
        rot = img.rotate(a, resample=Image.BICUBIC)
        im.alpha_composite(rot, (int(cx - D / 2), int(CY - D / 2)))
    b = bordes()
    if ok:
        glow = b.filter(ImageFilter.GaussianBlur(10))
        im.alpha_composite(glow, (int(cx - b.width / 2), int(CY - b.height / 2)))
    im.alpha_composite(b, (int(cx - b.width / 2), int(CY - b.height / 2)))
    d = ImageDraw.Draw(im)
    P.texto(d, (W / 2, CY + D / 2 + 110), g["nombre"].upper(), 92, (255, 255, 255), 11, (20, 20, 30))
    if ok:
        im.alpha_composite(Image.new("RGBA", (W, H), (60, 230, 90, 30)))
        d = ImageDraw.Draw(im)
        P.texto(d, (W / 2, CY + D / 2 + 250), "PERFECT FACE!", 120, (255, 230, 40), 13)
    im = G.capa(im, t, g["dur"], A["textos"], 120, sin_fin=True) or im
    return im.convert("RGB"), ok


def audio(g, oks, dur):
    sr = M.SR; n = int(dur * sr); fx = np.zeros(n, np.float32)

    def add(t0, sig, v=1.0):
        a = int(t0 * sr) % n; b = min(n, a + len(sig)); fx[a:b] += sig[: b - a] * v
    k = 0.0
    while k < dur:                                                             # clics de candado que giran
        add(k, M.golpe(0.03), 0.22); k += 0.11
    prev = False
    for f, o in enumerate(oks):
        if o and not prev:
            add(f / FPS, M.ding(0.6), 0.65); add(f / FPS, M.boom(0.5), 0.35)
        prev = o
    add(0, G.silbato(sr), 1.0)
    mu = P.musica(g, dur)
    return np.tanh((mu * 0.75 + fx) * 1.1) * 0.9, np.tanh(fx * 1.1) * 0.85


def armar(g):
    return dict(fondo=R.fondo(g.get("fondo", "estadio_0")).copy(), anillos=anillos(g["clave"]))


def main(guion):
    g = json.loads(Path(guion).read_text())
    out = ROOT / "salida" / g["id"]; out.mkdir(parents=True, exist_ok=True)
    A = armar(g); dur = g["dur"]
    A["textos"] = g.get("textos") or G.elegir("anillos", g["id"], g.get("nombre", ""))
    mudo = out / "mudo.mp4"; oks = []
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", str(mudo)], stdin=subprocess.PIPE)
    for f in range(int(round(dur * FPS))):
        im, o = cuadro(g, A, f / FPS); oks.append(o)
        p.stdin.write(np.asarray(im, np.uint8).tobytes())
    p.stdin.close(); p.wait()
    con, solo = audio(g, oks, dur)
    M.mezclar(out, mudo, {"short.mp4": con, "short_solo_efectos.mp4": solo})
    print(out / "short.mp4", dur, "s", "armada en", [round(f / FPS, 2) for f, o in enumerate(oks) if o and (f == 0 or not oks[f - 1])])


if __name__ == "__main__":
    main(sys.argv[1])
