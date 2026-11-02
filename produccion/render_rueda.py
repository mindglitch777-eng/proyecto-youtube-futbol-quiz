#!/usr/bin/env python3
"""
WHEEL STOP (réplica de "X vs Y or Z stop challenge", 45 M+ en una semana): abajo las piernas de UN jugador, arriba una
rueda de 8 torsos que gira. Hay que frenar el video cuando cae el torso que le corresponde a esas piernas.
Contador arriba a la izquierda (1, 2, 3… cada torso que pasa). Cuando calza el correcto: destello verde, PERFECT!, ding.
Loop perfecto: 2 vueltas completas.

Los recortes (rueda + piernas) salen de capturas en alta resolución del video de referencia: assets/rueda/<set>/.
Uso: python3 produccion/render_rueda.py produccion/guiones/rueda_01.json
guion: {"id": "rueda_01", "set": "vfx1", "vueltas": 2, "dur": 8.4, "sentido": 1, "musica": "trallallero_2"}
"""
import json
import math
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

import motor as M
import render_plinko as P

ROOT = Path(__file__).resolve().parent
W, H, FPS = 1080, 1920, 30


def fondo():
    """Cielo + estadio + cancha (como el original), dibujado por nosotros."""
    y = np.linspace(0, 1, H)[:, None]
    cielo = np.array([70, 150, 230]) * (1 - y) + np.array([190, 225, 250]) * y
    arr = np.repeat(cielo[:, None, :], W, 1)
    im = Image.fromarray(arr.astype(np.uint8)).convert("RGBA"); d = ImageDraw.Draw(im)
    for k in range(9):                                                         # nubes
        cx, cy, r = (k * 263) % W, 120 + (k * 97) % 520, 70 + (k * 31) % 60
        for j in range(5):
            d.ellipse((cx + j * r * 0.6 - r, cy - r * 0.5 + (j % 2) * 20, cx + j * r * 0.6 + r, cy + r * 0.5 + (j % 2) * 20), fill=(255, 255, 255, 170))
    d.rectangle((0, 900, W, 1180), fill=(70, 80, 95, 255))                       # tribunas
    rng = np.random.default_rng(3)
    for _ in range(5000):
        x, yy = rng.uniform(0, W), rng.uniform(910, 1170)
        d.rectangle((x, yy, x + 3, yy + 4), fill=tuple(int(v) for v in rng.choice([[230, 60, 60], [240, 240, 240], [60, 120, 230], [250, 210, 60]])) + (200,))
    d.rectangle((0, 1180, W, H), fill=(60, 150, 60, 255))                         # cancha con franjas
    for k in range(12):
        y0 = 1180 + k * 70
        if k % 2:
            d.rectangle((0, y0, W, y0 + 70), fill=(75, 168, 70, 255))
    d.polygon([(W / 2 - 18, 1180), (W / 2 + 18, 1180), (W / 2 + 160, H), (W / 2 - 160, H)], fill=(245, 245, 245, 255))
    return im


def armar(g):
    base = ROOT / "assets" / "rueda" / g.get("set", "vfx1")
    meta = json.loads((base / "meta.json").read_text())
    return dict(meta=meta, rueda=Image.open(base / "rueda.png").convert("RGBA"), piernas=Image.open(base / "piernas.png").convert("RGBA"),
                fondo=fondo())


def angulo(g, t):
    """El arranque se corre para que el torso correcto calce recién a los ~2,5 s (y otra vez en la 2ª vuelta)."""
    return g.get("fase", 0.0) + g.get("sentido", 1) * 360.0 * g.get("vueltas", 2) * t / g["dur"]


def encajes(g, A):
    """Momentos en que el torso correcto queda abajo (ángulo 90° en pantalla)."""
    meta = A["meta"]; out = []
    n = int(round(g["dur"] * FPS))
    prev = None
    for f in range(n + 1):
        t = f / FPS
        a = (meta["correcto_ang"] + angulo(g, t) - 90) % 360
        d = min(a, 360 - a)
        if prev is not None and d < 1.6 * 360 * g.get("vueltas", 2) / g["dur"] / FPS and (not out or t - out[-1] > 1):
            out.append(t)
        prev = d
    return out


def cuadro(g, A, t, enc):
    meta = A["meta"]
    im = A["fondo"].copy()
    px, py = meta["piernas_xy"]
    pw = A["piernas"]
    im.alpha_composite(pw, (int(meta["rueda_centro"][0] - pw.width / 2 + 18), int(py)))
    rot = A["rueda"].rotate(-angulo(g, t), resample=Image.BICUBIC)
    L = meta["lado"]
    cx, cy = meta["rueda_centro"]
    im.alpha_composite(rot, (int(cx - L / 2), int(cy - L / 2)))
    d = ImageDraw.Draw(im)
    paso = 360 / meta["piezas"]
    n = int(abs(angulo(g, t) - g.get("fase", 0.0)) // paso) % meta["piezas"] + 1
    P.texto(d, (95, 150), f"{n}.", 150, (255, 255, 255), 12, (230, 30, 30))
    P.texto(d, (W / 2 + 90, 1840), "STOP WHEN IT FITS!", 60, (255, 230, 40), 9)
    for te in enc:
        e = t - te
        if -0.05 <= e < 0.5:
            if e < 0.15:
                im.alpha_composite(Image.new("RGBA", (W, H), (60, 230, 90, int(90 * (1 - max(e, 0) / 0.15)))))
            d = ImageDraw.Draw(im)
            P.texto(d, (W / 2, 1740), "PERFECT!", int(110 * min(1, (e + 0.05) / 0.1)) + 1, (255, 230, 40), 12)
    return im.convert("RGB")


def audio(g, A, enc, dur):
    sr = M.SR; n = int(dur * sr); fx = np.zeros(n, np.float32)

    def add(t0, sig, v=1.0):
        if sig is None:
            return
        a = int(t0 * sr) % n; b = min(n, a + len(sig)); fx[a:b] += sig[: b - a] * v
    paso = 360 / A["meta"]["piezas"]
    vel = 360 * g.get("vueltas", 2) / g["dur"]
    k = 0.0
    while k < dur:                                                             # tic por cada torso que pasa
        add(k, M.golpe(0.05), 0.35); k += paso / vel
    for te in enc:
        add(te, M.ding(0.6), 0.6); add(te, M.boom(0.5), 0.4)
    mu = P.musica(g, dur)
    return np.tanh((mu * 0.75 + fx) * 1.1) * 0.9, np.tanh(fx * 1.1) * 0.85


def main(guion):
    g = json.loads(Path(guion).read_text())
    out = ROOT / "salida" / g["id"]; out.mkdir(parents=True, exist_ok=True)
    A = armar(g); dur = g["dur"]
    vel = 360.0 * g.get("vueltas", 2) / dur * g.get("sentido", 1)
    g["fase"] = (90 - A["meta"]["correcto_ang"] - vel * g.get("t_encaje", 2.5)) % 360
    enc = encajes(g, A)
    mudo = out / "mudo.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", str(mudo)], stdin=subprocess.PIPE)
    for f in range(int(round(dur * FPS))):
        p.stdin.write(np.asarray(cuadro(g, A, f / FPS, enc), np.uint8).tobytes())
    p.stdin.close(); p.wait()
    con, solo = audio(g, A, enc, dur)
    M.mezclar(out, mudo, {"short.mp4": con, "short_solo_efectos.mp4": solo})
    print(out / "short.mp4", dur, "s", "encajes", [round(x, 2) for x in enc])


if __name__ == "__main__":
    main(sys.argv[1])
