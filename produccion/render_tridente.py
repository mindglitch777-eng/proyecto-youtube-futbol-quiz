#!/usr/bin/env python3
"""
BUILD YOUR TRIDENT · €150M (idea de la IA de YouTube Studio, 05/11), en versión tragamonedas de 7 s:
3 rodillos (EXTREMO IZQ · 9 · EXTREMO DER) giran con caras y precios. El espectador PAUSA y arma su tridente con lo que quedó
en la línea del medio. Abajo, el total en vivo: verde si entra en el presupuesto, rojo "BANKRUPT 💀" si se pasa.
Loop perfecto: cada rodillo avanza un número entero de cartas.
Uso: python3 produccion/render_tridente.py guion.json
guion: {"id", "presupuesto": 150, "rodillos": [[[clave, nombre, millones], ...] x3], "dur": 7.0}
"""
import json
import math
import subprocess
import sys
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

import caras_find as CF
import gancho as G
import motor as M
import render_plinko as P

ROOT = Path(__file__).resolve().parent
W, H, FPS = 1080, 1920, 30
FOTOS = json.loads((ROOT / "assets" / "fotos" / "frontales.json").read_text())
CW, CH = 320, 300                      # carta
Y_LINEA = 1000                         # línea de selección
COLS = [W / 2 - 350, W / 2, W / 2 + 350]
TITULOS = ["LEFT WING", "STRIKER", "RIGHT WING"]


@lru_cache(maxsize=64)
def carta(clave, nombre, precio):
    img, _ = CF.base(FOTOS.get(clave, clave + "_0"), 1.3)
    cara = Image.fromarray(img[..., ::-1]).resize((190, 190), Image.LANCZOS).convert("RGBA")
    m = Image.new("L", (190, 190), 0); ImageDraw.Draw(m).ellipse([0, 0, 189, 189], fill=255); cara.putalpha(m)
    c = Image.new("RGBA", (CW, CH), (0, 0, 0, 0)); d = ImageDraw.Draw(c)
    d.rounded_rectangle([6, 6, CW - 6, CH - 6], 26, fill=(28, 30, 48), outline=(255, 255, 255), width=4)
    c.alpha_composite(cara, ((CW - 190) // 2, 18))
    P.texto(d, (CW / 2, 228), nombre.upper(), 34, (255, 255, 255), 5, (10, 10, 16))
    P.texto(d, (CW / 2, 268), f"€{precio}M", 40, (255, 210, 0), 6, (10, 10, 16))
    return c


def main(guion):
    g = json.loads(Path(guion).read_text())
    out = ROOT / "salida" / g["id"]; out.mkdir(parents=True, exist_ok=True)
    dur = g.get("dur", 7.0); pres = g.get("presupuesto", 150)
    rod = g["rodillos"]
    cartas = [[carta(*x) for x in r] for r in rod]
    vueltas = g.get("vueltas", [9, 7, 8])                                       # cartas que avanza cada rodillo en todo el video (enteras)
    fondo = Image.new("RGBA", (W, H), (12, 14, 26, 255)); d = ImageDraw.Draw(fondo)
    for i, x in enumerate(COLS):
        d.rounded_rectangle([x - CW / 2 - 14, 520, x + CW / 2 + 14, 1480], 30, fill=(22, 24, 40), outline=(70, 75, 110), width=4)
        P.texto(d, (x, 480), TITULOS[i], 40, (255, 255, 255), 6, (10, 10, 16))
    P.texto(d, (W / 2, 330), f"BUDGET €{pres}M", 96, (255, 210, 0), 11, (10, 10, 16))
    tx = dict(gancho=f"BUILD YOUR TRIDENT €{pres}M", apuesta="PAUSE TO PICK YOUR 3", cta="COMMENT YOUR TRIDENT · FOLLOW FOR PART 2")
    mudo = out / "mudo.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", str(mudo)], stdin=subprocess.PIPE)
    clics = []
    for fr in range(int(round(dur * FPS))):
        t = fr / FPS
        im = fondo.copy()
        elegidos = []
        for i, x in enumerate(COLS):
            n = len(cartas[i]); despl = vueltas[i] * t / dur * CH * 1.0          # px recorridos
            off = despl % (n * CH)
            capa = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            for k in range(-2, 4):
                idx = (int(off // CH) + k) % n
                y = Y_LINEA + (k - (off % CH) / CH) * CH
                if 520 < y + CH / 2 and y - CH / 2 < 1480:
                    capa.alpha_composite(cartas[i][idx], (int(x - CW / 2), int(y - CH / 2)))
            m = Image.new("L", (W, H), 0); ImageDraw.Draw(m).rectangle([x - CW / 2 - 10, 526, x + CW / 2 + 10, 1474], fill=255)
            im.paste(capa, (0, 0), Image.fromarray(np.minimum(np.asarray(m), np.asarray(capa.split()[3]))))
            centro = int(round(off / CH)) % n
            elegidos.append(rod[i][centro])
        d = ImageDraw.Draw(im)
        d.rectangle([20, Y_LINEA - CH / 2 - 6, W - 20, Y_LINEA - CH / 2 + 2], fill=(255, 210, 0))       # línea de selección
        d.rectangle([20, Y_LINEA + CH / 2 - 2, W - 20, Y_LINEA + CH / 2 + 6], fill=(255, 210, 0))
        d.polygon([(4, Y_LINEA - 30), (40, Y_LINEA), (4, Y_LINEA + 30)], fill=(255, 210, 0))
        d.polygon([(W - 4, Y_LINEA - 30), (W - 40, Y_LINEA), (W - 4, Y_LINEA + 30)], fill=(255, 210, 0))
        total = sum(e[2] for e in elegidos)
        ok = total <= pres
        P.texto(d, (W / 2, 1600), f"TOTAL €{total}M", 104, (60, 230, 90) if ok else (235, 40, 40), 12, (10, 10, 16))
        P.texto(d, (W / 2, 1730), "UNDER BUDGET!" if ok else "BANKRUPT", 78, (60, 230, 90) if ok else (235, 40, 40), 10, (10, 10, 16))
        if not ok:
            e = P.texto  # noqa
        im = G.capa(im, t, dur, tx, 120, sin_fin=True)
        p.stdin.write(np.asarray(im.convert("RGB"), np.uint8).tobytes())
    p.stdin.close(); p.wait()
    sr = M.SR; nm = int(dur * sr); fx = np.zeros(nm, np.float32)

    def add(t0, sig, v=1.0):
        a = int(t0 * sr) % nm; b = min(nm, a + len(sig)); fx[a:b] += sig[: b - a] * v
    for i in range(3):                                                          # clic cada vez que pasa una carta por la línea
        for k in range(vueltas[i]):
            add((k + 0.5) * dur / vueltas[i], M.golpe(0.03), 0.18)
    add(0, G.silbato(sr), 1.0)
    mu = P.musica(g, dur)
    M.mezclar(out, mudo, {"short.mp4": np.tanh((mu * 0.75 + fx) * 1.1) * 0.9, "short_solo_efectos.mp4": np.tanh(fx * 1.1) * 0.85})
    print(out / "short.mp4", dur, "s")


if __name__ == "__main__":
    main(sys.argv[1])
