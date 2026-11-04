#!/usr/bin/env python3
"""
WALL BALANCE (tendencia "Who has the best balance at the wall?", 6,9 M): 5 jugadores contra una pared de ladrillos, inclinados
(el "lean" de Michael Jackson). Cuenta regresiva 3-2-1: se tambalean y caen todos MENOS UNO, que gana la corona.
El espectador elige ANTES quién queda parado y lo comenta. Loop: la última parte funde con el cuadro 0.
Uso: python3 produccion/render_pared.py guion.json
guion: {"id", "cuerpos": [5 nombres de assets/recortes/cuerpos], "nombres": [5], "ganador": 2, "dur": 7.0}
"""
import json
import math
import random
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
PISO = 1640
ALTO = 760
INCL = 18          # grados de inclinación inicial
T_CAE = 3.3


def pared():
    """Pared de ladrillos con relieve, mortero y luz de arriba + piso de cemento."""
    rng = np.random.default_rng(4)
    im = Image.new("RGB", (W, H), (70, 70, 74)); d = ImageDraw.Draw(im)
    bw, bh = 150, 62
    for fila in range(0, PISO // bh + 1):
        off = (bw // 2) if fila % 2 else 0
        for col in range(-1, W // bw + 2):
            x0 = col * bw - off; y0 = fila * bh
            c = np.array([150, 52, 40]) + rng.integers(-22, 22, 3)
            d.rectangle([x0 + 4, y0 + 4, x0 + bw - 4, y0 + bh - 4], fill=tuple(int(v) for v in c))
            d.line([(x0 + 5, y0 + 5), (x0 + bw - 5, y0 + 5)], fill=tuple(int(min(255, v + 30)) for v in c), width=3)
            d.line([(x0 + 5, y0 + bh - 5), (x0 + bw - 5, y0 + bh - 5)], fill=tuple(int(v * 0.65) for v in c), width=3)
    d.rectangle([0, PISO, W, H], fill=(120, 120, 125))
    d.rectangle([0, PISO, W, PISO + 14], fill=(60, 60, 64))
    arr = np.asarray(im).astype(np.float32)
    yy, xx = np.mgrid[0:H, 0:W]
    luz = 1.15 - 0.55 * (((xx - W / 2) / W) ** 2 + ((yy - 500) / H) ** 2)
    arr = np.clip(arr * luz[..., None] + rng.normal(0, 6, arr.shape), 0, 255)
    return Image.fromarray(arr.astype(np.uint8)).convert("RGBA")


@lru_cache(maxsize=16)
def sprite(nombre, alto=ALTO, ancho_max=250):
    im = Image.open(R.REC / "cuerpos" / f"{nombre}.png").convert("RGBA")
    s = min(alto / im.height, ancho_max / im.width)                             # que no se pisen entre ellos
    im = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
    alto = im.height
    lado = alto * 2 + 40                                                        # lienzo cuadrado con los pies en el centro (pivote)
    c = Image.new("RGBA", (lado, lado), (0, 0, 0, 0))
    c.alpha_composite(im, (lado // 2 - im.width // 2, lado // 2 - alto))
    return c


def angulo(t, k, ganador, dur):
    """Inclinación del jugador k en el segundo t (grados, positivo = hacia la derecha)."""
    if t > dur - 0.6:                                                           # vuelve a la pose inicial (loop)
        a_fin = angulo(dur - 0.6, k, ganador, dur)
        u = (t - (dur - 0.6)) / 0.6; u = u * u * (3 - 2 * u)
        return a_fin * (1 - u) + INCL * u
    tembl = 0.0
    if t < T_CAE:
        amp = 1.0 + 4.0 * (t / T_CAE) ** 2                                      # tiembla cada vez más
        tembl = amp * math.sin(t * (9 + k * 1.7) + k)
    if k == ganador or t < T_CAE + 0.06 * ((k * 7) % 5):
        return INCL + tembl if t < T_CAE else (INCL if k != ganador else max(0.0, INCL - (t - T_CAE) * 30))
    e = t - (T_CAE + 0.06 * ((k * 7) % 5))
    return min(88.0, INCL + 300 * e * e + 60 * e)                               # cae acelerando


def main(guion):
    g = json.loads(Path(guion).read_text())
    out = ROOT / "salida" / g["id"]; out.mkdir(parents=True, exist_ok=True)
    dur = g.get("dur", 7.0); gan = g["ganador"]
    fondo = pared()
    asp = [Image.open(R.REC / "cuerpos" / f"{n}.png").size for n in g["cuerpos"]]
    alto = int(min(880, min(330 * h / w for w, h in asp)))                     # misma altura para todos, lo más grandes posible
    sp = [sprite(n, alto, 400) for n in g["cuerpos"]]
    N = len(sp); xs = [W * (0.44 + (k - (N - 1) / 2) * 0.225) for k in range(N)]       # corrido a la izquierda: se inclinan a la derecha
    tx = dict(gancho="WHO WON'T FALL?", apuesta=f"PICK ONE: 1 TO {len(sp)}", cta="COMMENT YOUR PICK · FOLLOW FOR PART 2")
    caidas = [T_CAE + 0.06 * ((k * 7) % 5) + 0.28 for k in range(len(sp)) if k != gan]
    mudo = out / "mudo.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", str(mudo)], stdin=subprocess.PIPE)
    for f in range(int(round(dur * FPS))):
        t = f / FPS
        im = fondo.copy(); d = ImageDraw.Draw(im)
        for k in range(N):                                                      # número y nombre arriba de cada uno
            P.texto(d, (xs[k], 700), str(k + 1), 100, (255, 230, 40), 10, (20, 20, 30))
            P.texto(d, (xs[k], 790), g["nombres"][k].upper(), 42, (255, 255, 255), 7, (20, 20, 30))
        orden = sorted(range(N), key=lambda k: k == gan)
        for k in orden:
            a = angulo(t, k, gan, dur)
            rot = sp[k].rotate(-a, resample=Image.BICUBIC)
            im.alpha_composite(rot, (int(xs[k] - rot.width / 2), int(PISO + 6 - rot.height / 2)))
        d = ImageDraw.Draw(im)
        if t < T_CAE:                                                           # cuenta regresiva gigante
            n = 3 - int(t / (T_CAE / 3)); e = (t % (T_CAE / 3)) / (T_CAE / 3)
            P.texto(d, (W / 2, 330), str(max(1, n)), int(230 * (1.25 - 0.25 * e)), (255, 255, 255), 16, (225, 25, 30))
        elif t < dur - 0.6:
            e = t - T_CAE
            if e > 0.45:
                cx = xs[gan]
                d.polygon([(cx - 70, 640), (cx - 70, 560), (cx - 35, 600), (cx, 545), (cx + 35, 600), (cx + 70, 560), (cx + 70, 640)][:0] or
                          [(cx - 70, 620), (cx - 70, 540), (cx - 35, 580), (cx, 525), (cx + 35, 580), (cx + 70, 540), (cx + 70, 620)],
                          fill=(255, 205, 0), outline=(120, 70, 0), width=5)
                P.texto(d, (W / 2, 330), "WINNER!", int(150 * min(1, 0.6 + (e - 0.45) * 3)), (255, 230, 40), 14)
                P.texto(d, (W / 2, 1780), g["nombres"][gan].upper(), 96, (255, 230, 40), 11, (20, 20, 30))
        im = G.capa(im, t, dur, tx, 120, sin_fin=True)
        p.stdin.write(np.asarray(im.convert("RGB"), np.uint8).tobytes())
    p.stdin.close(); p.wait()
    sr = M.SR; nm = int(dur * sr); fx = np.zeros(nm, np.float32)

    def add(t0, sig, v=1.0):
        if sig is None:
            return
        a = int(t0 * sr) % nm; b = min(nm, a + len(sig)); fx[a:b] += sig[: b - a] * v
    for j in range(3):
        add(j * T_CAE / 3, M.golpe(0.08), 0.6)
    for c in caidas:
        add(c, M.boom(0.4), 0.55)
    add(T_CAE + 0.6, M.ding(0.7), 0.7); add(T_CAE + 0.6, P.cargar("crowd_cheer_0", 0.5), 0.5)
    add(0, G.silbato(sr), 1.0)
    mu = P.musica(g, dur)
    M.mezclar(out, mudo, {"short.mp4": np.tanh((mu * 0.7 + fx) * 1.1) * 0.9, "short_solo_efectos.mp4": np.tanh(fx * 1.1) * 0.85})
    print(out / "short.mp4", dur, "s ganador", g["nombres"][gan])


if __name__ == "__main__":
    main(sys.argv[1])
