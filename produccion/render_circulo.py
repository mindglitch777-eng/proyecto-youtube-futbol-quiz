#!/usr/bin/env python3
"""
GOAT CIRCLE (tendencia "Which footballer is the BEST?!", 6 M): vista desde abajo, un anillo de 8 caras de superestrellas mirando
hacia la cámara contra el cielo; la pelota salta del centro a cada cara por turno. Mecánica de pausa: "PAUSE ON YOUR GOAT"
(pausá cuando la pelota toca a tu jugador y comentalo). El anillo da una vuelta exacta: loop perfecto.
Uso: python3 produccion/render_circulo.py guion.json
guion: {"id", "claves": [8 claves de fotos], "nombres": [8], "dur": 8.0}
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
import render_cabezas as RC
import render_plinko as P

ROOT = Path(__file__).resolve().parent
W, H, FPS = 1080, 1920, 30
EXT = ROOT / "assets" / "recortes" / "extras"
CX, CY, RADIO = W / 2, 1000, 365


def cielo():
    yy = np.linspace(0, 1, H)[:, None]
    top, bot = np.array([40, 110, 220]), np.array([150, 205, 255])
    arr = (top * (1 - yy) + bot * yy)[..., None].repeat(1, 2).transpose(0, 2, 1)
    arr = np.broadcast_to(top * (1 - yy[..., None]) + bot * yy[..., None], (H, W, 3)).copy()
    im = Image.fromarray(arr.astype(np.uint8)).convert("RGBA")
    nubes = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(nubes)
    rng = np.random.default_rng(7)
    for _ in range(16):
        x, y = rng.uniform(-100, W + 100), rng.uniform(150, H - 150); r = rng.uniform(80, 190)
        for k in range(5):
            d.ellipse([x + k * r * 0.5 - r, y - r * 0.6, x + k * r * 0.5 + r, y + r * 0.6], fill=(255, 255, 255, 120))
    im.alpha_composite(nubes.filter(ImageFilter.GaussianBlur(40)))
    return im


def main(guion):
    g = json.loads(Path(guion).read_text())
    out = ROOT / "salida" / g["id"]; out.mkdir(parents=True, exist_ok=True)
    dur = g.get("dur", 8.0); n = len(g["claves"])
    fondo = cielo()
    caras = []
    for k in g["claves"]:                                                       # caras grandes (las del FIT, x1,3)
        c = RC.cabeza(k)[0]; caras.append(c.resize((int(c.width * 1.3), int(c.height * 1.3)), Image.LANCZOS))
    pelota = Image.open(EXT / "pelota_1.png").convert("RGBA").resize((150, 150), Image.LANCZOS)
    paso_t = dur / n                                                            # la pelota visita una cara por turno
    tx = dict(gancho="PAUSE ON YOUR GOAT", apuesta="WHO IS THE BEST?", cta="COMMENT YOUR GOAT · FOLLOW FOR PART 2")
    mudo = out / "mudo.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", str(mudo)], stdin=subprocess.PIPE)
    golpes = [(j * paso_t + paso_t * 0.5) for j in range(n)]
    for f in range(int(round(dur * FPS))):
        t = f / FPS
        im = fondo.copy()
        giro = 360.0 * t / dur                                                  # una vuelta exacta en todo el video
        j = int(t // paso_t) % n; u = (t % paso_t) / paso_t                   # turno de la cara j: va (0→0,5) y vuelve (0,5→1)
        pos = []
        for k in range(n):
            th = math.radians(giro + k * 360 / n - 90)
            pos.append((CX + RADIO * math.cos(th), CY + RADIO * math.sin(th), th))
        for k, (x, y, th) in enumerate(pos):
            c = caras[k]
            golpe = k == j and abs(u - 0.5) < 0.12
            if golpe:
                c = c.resize((int(c.width * 1.18), int(c.height * 1.18)), Image.BICUBIC)
            rot = c.rotate(-math.degrees(th) - 90, expand=True, resample=Image.BICUBIC)   # la pera mira al centro (nos mira desde arriba)
            im.alpha_composite(rot, (int(x - rot.width / 2), int(y - rot.height / 2)))
        x, y, _ = pos[j]
        ida = 1 - abs(1 - 2 * u)                                                # 0 en el centro, 1 en la cara
        bx = CX + (x - CX) * ida * 0.78; by = CY + (y - CY) * ida * 0.78
        esc = 1 + 0.25 * math.sin(math.pi * ida)
        pl = pelota.rotate(-t * 540, resample=Image.BICUBIC).resize((int(150 * esc), int(150 * esc)))
        im.alpha_composite(pl, (int(bx - pl.width / 2), int(by - pl.height / 2)))
        d = ImageDraw.Draw(im)
        if abs(u - 0.5) < 0.2:
            P.texto(d, (W / 2, 1650), g["nombres"][j].upper(), 120, (255, 230, 40), 13, (20, 20, 30))
        im = G.capa(im, t, dur, tx, 120, sin_fin=True)
        p.stdin.write(np.asarray(im.convert("RGB"), np.uint8).tobytes())
    p.stdin.close(); p.wait()
    sr = M.SR; nm = int(dur * sr); fx = np.zeros(nm, np.float32)

    def add(t0, sig, v=1.0):
        a = int(t0 * sr) % nm; b = min(nm, a + len(sig)); fx[a:b] += sig[: b - a] * v
    for gt in golpes:
        add(gt, M.golpe(0.08), 0.7); add(gt, M.ding(0.3), 0.3)
    add(0, G.silbato(sr), 1.0)
    mu = P.musica(g, dur)
    M.mezclar(out, mudo, {"short.mp4": np.tanh((mu * 0.75 + fx) * 1.1) * 0.9, "short_solo_efectos.mp4": np.tanh(fx * 1.1) * 0.85})
    print(out / "short.mp4", dur, "s")


if __name__ == "__main__":
    main(sys.argv[1])
