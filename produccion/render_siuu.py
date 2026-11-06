#!/usr/bin/env python3
"""
SIUUU 67 (idea de la IA de YouTube Studio: la figura más exitosa del canal + el número que pasó las 25.000 vistas):
un contador gigante corre 0→99 sin parar y Cristiano salta en cada vuelta; el punto más alto del salto es justo el 67.
El espectador tiene que PAUSAR en el 67 (con Cristiano arriba). En el 67: "SIUUU!" + destello dorado + el sonido.
Loop perfecto (vueltas enteras del contador).
Uso: python3 produccion/render_siuu.py guion.json
guion: {"id", "imagen": "extras/siuu_0" | "cuerpos/cristiano_ronaldo_11", "dur": 6.0, "ciclo": 1.5, "fondo": "estadio_0"}
"""
import json
import math
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

import gancho as G
import motor as M
import render_plinko as P
import render_rueda as R

ROOT = Path(__file__).resolve().parent
W, H, FPS = 1080, 1920, 30
PICO = 67


def jugador(ruta, alto=900):
    im = Image.open(R.REC / f"{ruta}.png").convert("RGBA")
    s = alto / im.height
    return im.resize((int(im.width * s), alto), Image.LANCZOS)


def salto(c):
    """Altura del salto (0..1) según el contador: despega en 34, punto más alto EXACTO en 67, cae en 100."""
    if c < 34:
        return 0.0
    return max(0.0, math.sin(math.pi * (c - 34) / 66)) ** 0.8


def main(guion):
    g = json.loads(Path(guion).read_text())
    out = ROOT / "salida" / g["id"]; out.mkdir(parents=True, exist_ok=True)
    dur = g.get("dur", 6.0); ciclo = g.get("ciclo", 1.5)
    n_ciclos = max(1, round(dur / ciclo)); ciclo = dur / n_ciclos              # vueltas enteras: loop perfecto
    fondo = R.fondo(g.get("fondo", "estadio_0")).copy()
    cr = jugador(g.get("imagen", "cuerpos/cristiano_ronaldo_11"))
    off = g.get("desfase", 0.25)                                              # el primer 67 cae a los ~0,9 s (gancho temprano)

    def contador(t):
        return ((t / ciclo + off) % 1.0) * 100

    picos = sorted(((PICO / 100 - off) % 1.0) * ciclo + k * ciclo for k in range(n_ciclos))
    tx = dict(gancho="PAUSE AT 67", apuesta="99% IMPOSSIBLE", cta="COMMENT YOUR NUMBER · FOLLOW FOR PART 2")
    mudo = out / "mudo.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", str(mudo)], stdin=subprocess.PIPE)
    for f in range(int(round(dur * FPS))):
        t = f / FPS
        c = contador(t); h = salto(c)
        im = fondo.copy()
        sombra = Image.new("RGBA", (int(cr.width * (0.7 - 0.3 * h)), 60), (0, 0, 0, 0))
        ImageDraw.Draw(sombra).ellipse([0, 0, sombra.width - 1, 59], fill=(0, 0, 0, int(120 * (1 - 0.6 * h))))
        im.alpha_composite(sombra, (int(W / 2 - sombra.width / 2), 1800))
        y = int(1830 - cr.height - h * 230)
        giro = cr.rotate(0, expand=False)
        im.alpha_composite(giro, (int(W / 2 - cr.width / 2), y))
        d = ImageDraw.Draw(im)
        num = int(c)
        cerca = min(min(abs(t - e), dur - abs(t - e)) for e in picos)
        en_67 = num == PICO or cerca < 0.5 / FPS
        if en_67:
            num = PICO
        col = (255, 205, 0) if en_67 else ((255, 255, 255) if abs(num - PICO) > 8 else (255, 140, 40))
        P.texto(d, (W / 2, 470), f"{num}", 300 if en_67 else 260, col, 18, (20, 20, 30))
        # barra de progreso con la marca del 67
        bx0, bx1, by = 140, W - 140, 660
        d.rounded_rectangle([bx0, by - 16, bx1, by + 16], 16, fill=(20, 20, 30))
        d.rounded_rectangle([bx0 + 4, by - 12, bx0 + 4 + (bx1 - bx0 - 8) * c / 100, by + 12], 12, fill=(255, 205, 0))
        mx = bx0 + (bx1 - bx0) * PICO / 100
        d.polygon([(mx, by + 22), (mx - 20, by + 52), (mx + 20, by + 52)], fill=(230, 30, 30))
        tras = min(((t - e) % dur) for e in picos)                            # tiempo desde el último 67 (solo DESPUÉS: no delata)
        if tras < 0.35:
            if tras < 0.1:
                im.alpha_composite(Image.new("RGBA", (W, H), (255, 205, 0, int(80 * (1 - tras / 0.1)))))
                d = ImageDraw.Draw(im)
            P.texto(d, (W / 2, 1700), "SIUUU!", int(150 * min(1, 0.6 + tras * 4)), (255, 230, 40), 14)
        im = G.capa(im, t, dur, tx, 120, sin_fin=True)
        p.stdin.write(np.asarray(im.convert("RGB"), np.uint8).tobytes())
    p.stdin.close(); p.wait()
    sr = M.SR; n = int(dur * sr); fx = np.zeros(n, np.float32)

    def add(t0, sig, v=1.0):
        a = int(t0 * sr) % n; b = min(n, a + len(sig)); fx[a:b] += sig[: b - a] * v
    siu = P.cargar("siuuu_0", 0.9) if hasattr(P, "cargar") else None
    for e in picos:
        if siu is not None:
            add(e - 0.05, siu[: int(0.9 * sr)], 0.9)
        add(e, M.ding(0.5), 0.5)
    add(0, G.silbato(sr), 1.0)
    mu = P.musica(g, dur)
    M.mezclar(out, mudo, {"short.mp4": np.tanh((mu * 0.7 + fx) * 1.1) * 0.9, "short_solo_efectos.mp4": np.tanh(fx * 1.1) * 0.85})
    print(out / "short.mp4", dur, "s", "67 en", [round(x, 2) for x in picos])


if __name__ == "__main__":
    main(sys.argv[1])
