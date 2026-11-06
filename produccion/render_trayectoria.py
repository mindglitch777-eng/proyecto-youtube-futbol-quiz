#!/usr/bin/env python3
"""
GUESS HIM BY HIS CAREER (idea de la IA de YouTube Studio, 05/11): los escudos de los clubes de un crack aparecen en orden
(Sporting → Man United → Real Madrid → Juventus → Al Nassr), con su SILUETA negra y una cuenta regresiva de 5 s.
"Pausá antes de que termine el tiempo". A los 5,2 s se revela la cara y el nombre. Dura 7 s y empalma con el inicio.
Uso: python3 produccion/render_trayectoria.py guion.json
guion: {"id", "clave": "cristiano_ronaldo", "nombre": "Ronaldo", "clubes": ["sporting", ...], "dur": 7.0}
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
import render_rueda as R

ROOT = Path(__file__).resolve().parent
W, H, FPS = 1080, 1920, 30
ESC = ROOT / "assets" / "escudos"
T_REVELA = 3.6          # modo imposible: 3 segundos para adivinar
T_ESCUDO = 0.42

CARRERAS = {   # solo clubes con escudo en assets/escudos
    "cristiano_ronaldo": ("Ronaldo", ["sporting", "man_united", "real_madrid", "juventus", "al_nassr"]),
    "lionel_messi": ("Messi", ["barcelona", "psg", "inter_miami"]),
    "neymar": ("Neymar", ["santos", "barcelona", "psg", "al_hilal"]),
    "zlatan_ibrahimovi": ("Zlatan", ["ajax", "juventus", "inter", "barcelona", "milan"]),
    "robert_lewandowski": ("Lewandowski", ["dortmund", "bayern", "barcelona"]),
    "ronaldinho": ("Ronaldinho", ["psg", "barcelona", "milan", "flamengo"]),
    "ngel_di_mar_a": ("Di María", ["benfica", "real_madrid", "man_united", "psg", "juventus"]),
    "david_beckham": ("Beckham", ["man_united", "real_madrid", "la_galaxy", "milan", "psg"]),
    "thierry_henry": ("Henry", ["juventus", "arsenal", "barcelona"]),
    "harry_kane": ("Kane", ["tottenham", "bayern"]),
    "kak": ("Kaká", ["milan", "real_madrid"]),
}


def escudo(nombre, lado=250):
    im = Image.open(ESC / f"{nombre}.png").convert("RGBA")
    im = im.crop(im.getbbox()); k = lado / max(im.size)                         # agrandar también los escudos chicos
    im = im.resize((max(1, int(im.width * k)), max(1, int(im.height * k))), Image.LANCZOS)
    out = Image.new("RGBA", (lado + 40, lado + 40), (0, 0, 0, 0))
    sombra = Image.new("RGBA", out.size, (0, 0, 0, 0)); sombra.alpha_composite(im.split()[3].point(lambda v: v * 0.5).convert("L").convert("RGBA"), (24, 28))
    out.alpha_composite(im, ((out.width - im.width) // 2, (out.height - im.height) // 2))
    return out


def fondo():
    yy = np.linspace(0, 1, H)[:, None, None]
    arr = np.array([18, 26, 60]) * (1 - yy) + np.array([60, 20, 90]) * yy
    im = Image.fromarray(np.broadcast_to(arr, (H, W, 3)).astype(np.uint8)).convert("RGBA")
    rayos = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(rayos)
    for k in range(14):                                                         # rayos de luz desde el centro
        a = k * math.pi / 7
        d.polygon([(W / 2, 1350), (W / 2 + 1800 * math.cos(a), 1350 + 1800 * math.sin(a)),
                   (W / 2 + 1800 * math.cos(a + 0.12), 1350 + 1800 * math.sin(a + 0.12))], fill=(255, 255, 255, 22))
    im.alpha_composite(rayos)
    return im


def main(guion):
    g = json.loads(Path(guion).read_text())
    out = ROOT / "salida" / g["id"]; out.mkdir(parents=True, exist_ok=True)
    dur = g.get("dur", 5.5); clubes = g["clubes"]; n = len(clubes)
    base = fondo()
    escs = [escudo(c, 290 if n <= 4 else 260) for c in clubes]
    cara = RC.cabeza(g["clave"])[0]; cara = cara.resize((int(cara.width * 1.55), int(cara.height * 1.55)), Image.LANCZOS)
    a = np.asarray(cara).copy(); a[..., :3] = 15; silueta = Image.fromarray(a)
    # escudos en fila (hasta 3 por renglón), con flechas
    cols = min(3, n); filas = math.ceil(n / cols); paso_x = W / (cols + 0.25)
    pos = []
    for i in range(n):
        f, c = divmod(i, cols)
        if f % 2:                                                               # zigzag: la 2.ª fila va de derecha a izquierda
            c = cols - 1 - c
        en_fila = min(cols, n - f * cols)
        x0 = W / 2 - (en_fila - 1) * paso_x / 2
        pos.append((x0 + c * paso_x if not (f % 2) else W / 2 + (en_fila - 1) * paso_x / 2 - (cols - 1 - c) * paso_x, 470 + f * 290))
    tx = dict(gancho="GUESS HIM IN 3 SECONDS", apuesta="99% CAN'T GUESS HIM", cta="COMMENT IF YOU GOT IT · FOLLOW FOR PART 2")
    mudo = out / "mudo.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", str(mudo)], stdin=subprocess.PIPE)
    for fr in range(int(round(dur * FPS))):
        t = fr / FPS
        im = base.copy(); d = ImageDraw.Draw(im)
        for i in range(n):                                                      # cada escudo entra con un golpe
            e = t - (0.15 + i * T_ESCUDO)
            if e < 0:
                continue
            s = 1 + 0.35 * math.exp(-e * 9) * math.cos(e * 22)
            es = escs[i].resize((max(1, int(escs[i].width * s)), max(1, int(escs[i].height * s))), Image.BICUBIC)
            x, y = pos[i]
            if i > 0:
                px, py = pos[i - 1]
                d.line([(px, py), (x, y)], fill=(255, 225, 0, 200), width=10)
            im.alpha_composite(es, (int(x - es.width / 2), int(y - es.height / 2)))
        d = ImageDraw.Draw(im)
        cx, cy = W / 2, 1380
        if t < T_REVELA:
            im.alpha_composite(silueta, (int(cx - silueta.width / 2), int(cy - silueta.height / 2)))
            d = ImageDraw.Draw(im)
            P.texto(d, (cx, cy), "?", 260, (255, 225, 0), 14, (20, 20, 30))
            resto = max(0.0, T_REVELA - 0.6 - t); seg = math.ceil(resto)              # cuenta 5-4-3-2-1 y barra que se vacía
            d.rounded_rectangle([140, 1770, W - 140, 1810], 20, fill=(20, 20, 30))
            d.rounded_rectangle([144, 1774, 144 + (W - 288) * resto / (T_REVELA - 0.6), 1806], 16,
                                fill=(255, 225, 0) if seg > 2 else (235, 40, 40))
            P.texto(d, (W - 110, 1700), str(max(1, seg)), 120, (255, 255, 255), 12, (235, 40, 40))
        else:
            e = t - T_REVELA
            if e < 0.12:
                im.alpha_composite(Image.new("RGBA", (W, H), (255, 255, 255, int(150 * (1 - e / 0.12)))))
            s = min(1.0, 0.7 + e * 2)
            cr = cara.resize((int(cara.width * s), int(cara.height * s)), Image.BICUBIC)
            im.alpha_composite(cr, (int(cx - cr.width / 2), int(cy - cr.height / 2)))
            d = ImageDraw.Draw(im)
            P.texto(d, (cx, 1760), g["nombre"].upper(), 130, (255, 225, 0), 13, (20, 20, 30))
        im = G.capa(im, t, dur, tx, 120, sin_fin=True)
        p.stdin.write(np.asarray(im.convert("RGB"), np.uint8).tobytes())
    p.stdin.close(); p.wait()
    sr = M.SR; nm = int(dur * sr); fx = np.zeros(nm, np.float32)

    def add(t0, sig, v=1.0):
        a_ = int(t0 * sr) % nm; b = min(nm, a_ + len(sig)); fx[a_:b] += sig[: b - a_] * v
    for i in range(n):
        add(0.15 + i * T_ESCUDO, M.golpe(0.07), 0.7)
    for k in range(3):
        add(T_REVELA - 0.6 - k, M.golpe(0.03), 0.35)                      # tic-tac de la cuenta
    add(T_REVELA, M.ding(0.7), 0.8); add(T_REVELA, M.boom(0.5), 0.5)
    add(0, G.silbato(sr), 1.0)
    mu = P.musica(g, dur)
    M.mezclar(out, mudo, {"short.mp4": np.tanh((mu * 0.65 + fx) * 1.1) * 0.9, "short_solo_efectos.mp4": np.tanh(fx * 1.1) * 0.85})
    print(out / "short.mp4", dur, "s", g["nombre"])


if __name__ == "__main__":
    main(sys.argv[1])
