#!/usr/bin/env python3
"""
PROTOTIPO "WHO WINS THE RACE?": carrera de canicas con las caras de los jugadores (física real con pymunk).
El espectador elige uno al principio (comenta su elegido) y se queda hasta ver si ganó.

Uso: python3 render_carrera.py "Lionel Messi,Cristiano Ronaldo,Neymar,Kylian Mbappé" [salida_id]
Salida: salida/<id>/short.mp4
"""
import csv
import json
import math
import random
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np
import pymunk
from PIL import Image, ImageDraw

from render_find_the_real import (BLANCO, FPS, H, LED, SR, VERDE, W, ROOT, ajustar, fuente,
                                  guardar_wav, sintetizar, texto)

R = 66                     # radio de cada bola
MUNDO = 6200               # alto de la pista
META = MUNDO - 260
COLORES = [(255, 210, 63), (61, 160, 240), (240, 84, 76), (61, 214, 128), (190, 110, 240), (255, 140, 40)]
DT = 1 / 240


# ------------------------------------------------------------------ caras
def mejor_foto(jugador):
    filas = [f for f in csv.DictReader(open(ROOT / "assets" / "poses.csv")) if f["jugador"] == jugador]
    f = max(filas, key=lambda f: float(f["puntaje"]))
    img = cv2.imread(str(next((ROOT / "assets" / "fotos").glob(f["foto"] + ".*"))))
    x, y, w, h = json.loads(f["cara"])[:4]
    cx, cy, s = x + w / 2, y + h * 0.5, max(w, h) * 1.55
    hh, ww = img.shape[:2]
    s = min(s, hh, ww)
    x0 = int(np.clip(cx - s / 2, 0, ww - s)); y0 = int(np.clip(cy - s / 2, 0, hh - s))
    crop = cv2.resize(img[y0:y0 + int(s), x0:x0 + int(s)], (2 * R, 2 * R), interpolation=cv2.INTER_AREA)
    rgb = Image.fromarray(cv2.cvtColor(crop, cv2.COLOR_BGR2RGB))
    m = Image.new("L", rgb.size, 0); ImageDraw.Draw(m).ellipse((0, 0, 2 * R - 1, 2 * R - 1), fill=255)
    out = Image.new("RGBA", rgb.size); out.paste(rgb, (0, 0), m)
    return out


# ------------------------------------------------------------------ pista
def pista(space):
    est = space.static_body
    segs = []

    def seg(a, b, grosor=10):
        s = pymunk.Segment(est, a, b, grosor); s.elasticity = 0.45; s.friction = 0.6
        space.add(s); segs.append((a, b, grosor))

    seg((40, -400), (40, MUNDO)); seg((W - 40, -400), (W - 40, MUNDO))
    pegs = []
    for y0, y1 in ((420, 1500), (3900, 4900)):          # campos de clavos
        for k, y in enumerate(range(y0, y1, 200)):
            xs = np.linspace(220, 860, 4) if k % 2 == 0 else (np.linspace(220, 860, 4)[:-1] + 107)
            for x in xs:
                c = pymunk.Circle(est, 17, (x, y)); c.elasticity = 0.55; c.friction = 0.4
                space.add(c); pegs.append((x, y))
    for k, y in enumerate(range(1700, 3500, 300)):     # zigzag
        if k % 2 == 0:
            seg((40, y), (W - 230, y + 140))
        else:
            seg((W - 40, y), (230, y + 140))
    giros = []
    for y, sentido in ((3620, 1), (5150, -1)):          # aspas giratorias
        b = pymunk.Body(body_type=pymunk.Body.KINEMATIC); b.position = (W / 2, y); b.angular_velocity = 2.2 * sentido
        s1 = pymunk.Segment(b, (-300, 0), (300, 0), 12); s2 = pymunk.Segment(b, (0, -300), (0, 300), 12)
        for s in (s1, s2):
            s.elasticity = 0.5; s.friction = 0.5
        space.add(b, s1, s2); giros.append(b)
    seg((40, 5500), (W / 2 - 110, META - 40)); seg((W - 40, 5500), (W / 2 + 110, META - 40))   # embudo
    seg((40, META + 230), (W - 40, META + 230))                                                 # piso
    return segs, pegs, giros


def simular(n, semilla):
    rnd = random.Random(semilla)
    space = pymunk.Space(); space.gravity = (0, 2300)
    segs, pegs, giros = pista(space)
    bolas = []
    xs = np.linspace(200, W - 200, n)
    for i in rnd.sample(range(n), n):
        b = pymunk.Body(1, pymunk.moment_for_circle(1, 0, R))
        b.position = (xs[len(bolas)] + rnd.uniform(-25, 25), 120 + rnd.uniform(-20, 20))
        b.velocity = (rnd.uniform(-80, 80), 0)
        c = pymunk.Circle(b, R); c.elasticity = 0.6; c.friction = 0.7
        space.add(b, c); bolas.append((i, b))
    bolas.sort()
    golpes, cuadros, llegada = [], [], {}
    t, paso_cuadro = 0.0, 0
    while len(llegada) < n and t < 45:
        for _ in range(int(1 / FPS / DT)):
            space.step(DT); t += DT
        estado = []
        for i, b in bolas:
            if i not in llegada and b.position.y > META:
                llegada[i] = t
            estado.append((b.position.x, b.position.y, b.angle))
            if abs(b.velocity.length - b._v_prev) > 450 if hasattr(b, "_v_prev") else False:
                golpes.append(t)
            b._v_prev = b.velocity.length
        cuadros.append(estado)
        paso_cuadro += 1
    orden = sorted(llegada, key=llegada.get)
    return dict(cuadros=cuadros, llegada=llegada, orden=orden, golpes=golpes, segs=segs, pegs=pegs,
                giros=[(g.position, g.angular_velocity) for g in giros])


def drama(sim, n):
    """Cambios de líder + final ajustado + duración razonable: elegimos una carrera entretenida (la física es real)."""
    lideres = [max(range(n), key=lambda i: c[i][1]) for c in sim["cuadros"][::8]]
    cambios = sum(a != b for a, b in zip(lideres, lideres[1:]))
    ll = sorted(sim["llegada"].values())
    if len(ll) < n:
        return -99
    dur = ll[0]
    return cambios * 1.0 - 6 * (ll[1] - ll[0]) - (0 if 14 < dur < 24 else 20)


# ------------------------------------------------------------------ render
def main(jugadores, sid):
    n = len(jugadores)
    caras = [mejor_foto(j) for j in jugadores]
    nombres = [j.split()[-1].upper() for j in jugadores]
    mejor = max(range(40), key=lambda s: drama(simular(n, s), n))
    sim = simular(n, mejor)
    out = ROOT / "salida" / sid; out.mkdir(parents=True, exist_ok=True)
    ganador = sim["orden"][0]
    t_gan = sim["llegada"][ganador]
    T_INTRO = 1.6          # todos quietos: "PICK ONE"
    T_FIN = 3.0
    nf = int((T_INTRO + t_gan + T_FIN) * FPS)
    print("semilla", mejor, "ganador", nombres[ganador], f"{t_gan:.1f}s", "cuadros", nf)

    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
                           str(out / "mudo.mp4")], stdin=subprocess.PIPE)
    cam = 0.0
    fondo = Image.new("RGB", (W, H), (14, 20, 34))
    eventos = [("whoosh", T_INTRO - 0.2)] + [("tick", T_INTRO + g) for g in sim["golpes"][::3][:60]]
    eventos += [("boom", T_INTRO + t_gan), ("ding", T_INTRO + t_gan + 0.1)]
    for f in range(nf):
        t = f / FPS
        k = min(max(int((t - T_INTRO) * FPS), 0), len(sim["cuadros"]) - 1)
        est = sim["cuadros"][k]
        lider_y = max(e[1] for e in est)
        cam += ((min(lider_y - 760, META - H + 400)) - cam) * 0.12
        cam = max(cam, -150)
        im = fondo.copy(); dr = ImageDraw.Draw(im, "RGBA")
        for a, b, g in sim["segs"]:
            dr.line((a[0], a[1] - cam, b[0], b[1] - cam), fill=(110, 130, 170), width=2 * g)
        for x, y in sim["pegs"]:
            if -40 < y - cam < H + 40:
                dr.ellipse((x - 17, y - cam - 17, x + 17, y - cam + 17), fill=(150, 170, 210))
        tt = max(t - T_INTRO, 0)
        for (p, w) in sim["giros"]:
            ang = w * tt
            for d in (0, math.pi / 2):
                c, s = math.cos(ang + d) * 300, math.sin(ang + d) * 300
                dr.line((p[0] - c, p[1] - s - cam, p[0] + c, p[1] + s - cam), fill=LED, width=24)
        my = META - cam
        for x in range(40, W - 40, 40):
            dr.rectangle((x, my, x + 20, my + 20), fill=BLANCO if (x // 40) % 2 else (0, 0, 0))
        for i, (x, y, a) in enumerate(est):
            cara = caras[i].rotate(-math.degrees(a), resample=Image.BICUBIC)
            im.paste(cara, (int(x - R), int(y - cam - R)), cara)
            dr.ellipse((x - R, y - cam - R, x + R, y - cam + R), outline=COLORES[i], width=8)
            texto(dr, (x, y - cam + R + 28), nombres[i], 38, COLORES[i], 6)
        # HUD: posiciones en vivo
        orden = sorted(range(n), key=lambda i: -(est[i][1] + (1e5 - sim["llegada"].get(i, 1e5) * 100 if i in sim["llegada"] and sim["llegada"][i] <= tt else 0)))
        dr.rectangle((0, 0, W, 300), fill=(0, 0, 0, 150))
        texto(dr, (W / 2, 80), "WHO WINS THE RACE?", ajustar("WHO WINS THE RACE?", 96, W - 80), LED, 10)
        for pos, i in enumerate(orden):
            x0 = 90 + pos * (W - 180) / n + (W - 180) / n / 2
            texto(dr, (x0, 175), f"{pos + 1}", 44, BLANCO, 6)
            texto(dr, (x0, 235), nombres[i], ajustar(nombres[i], 44, (W - 200) / n), COLORES[i], 6)
        if t < T_INTRO + 0.4:
            dr.rectangle((0, H / 2 - 150, W, H / 2 + 150), fill=(0, 0, 0, 170))
            texto(dr, (W / 2, H / 2 - 50), "PICK ONE NOW", 120, BLANCO, 12)
            texto(dr, (W / 2, H / 2 + 80), "AND COMMENT YOUR PLAYER", 60, LED, 8)
        if tt >= t_gan:
            u = min((tt - t_gan) / 0.25, 1)
            dr.rectangle((0, H / 2 - 260, W, H / 2 + 260), fill=(0, 0, 0, int(200 * u)))
            big = caras[ganador].resize((300, 300))
            im.paste(big, (W // 2 - 150, int(H / 2 - 240)), big)
            texto(dr, (W / 2, H / 2 + 120), f"{nombres[ganador]} WINS!", ajustar(f"{nombres[ganador]} WINS!", 130, W - 80), LED, 12)
            texto(dr, (W / 2, H / 2 + 220), "DID YOUR PICK WIN?", 64, BLANCO, 8)
        ff.stdin.write(np.asarray(im, np.uint8).tobytes())
    ff.stdin.close(); ff.wait()
    guardar_wav(out / "audio.wav", sintetizar(nf / FPS, eventos))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(out / "mudo.mp4"), "-i", str(out / "audio.wav"),
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", str(out / "short.mp4")], check=True)
    print("listo", out / "short.mp4")


if __name__ == "__main__":
    main([j.strip() for j in sys.argv[1].split(",")], sys.argv[2] if len(sys.argv) > 2 else "carrera_prueba")
