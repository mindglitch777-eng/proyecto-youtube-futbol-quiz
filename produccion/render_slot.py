#!/usr/bin/env python3
"""
HEAD SLOT (13/11 · variante de HEAD FIT, el 2.º formato que más rinde): la misma decisión (¿cuál es la cabeza de la estrella?)
y el mismo "pausar cuando calza", pero en vez de una rueda hay una TRAGAMONEDAS: un rodillo vertical de cabezas que baja
y desemboca en el cuello del cuerpo de una superestrella. SOLO superestrellas en el rodillo (6 cabezas: la correcta + las otras 5).
Recompensa propia: cuando calza la correcta se prenden todas las luces, baja la palanca, JACKPOT! y lluvia de monedas.
Desde el cuadro 0: cuerpo de una superestrella + cabeza de otra superestrella casi en el cuello (el encaje cae en la costura del loop).

Reusa las cabezas y los cuerpos sin cabeza de render_cabezas.py.
Uso: python3 produccion/render_slot.py guion.json
guion: {"id", "cuerpo": "kylian_mbapp_13", "clave": "kylian_mbapp", "nombre": "Mbappé", "cabezas": [5 claves de estrellas],
        "dur": 6.4, "vueltas": 3, "t_encaje": 0.45, "musica", "fondo", "pos_correcto": 2}
"""
import json
import math
import random
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

import gancho as G
import motor as M
import render_cabezas as RC
import render_plinko as P
import render_rueda as R

ROOT = Path(__file__).resolve().parent
W, H, FPS = 1080, 1920, 30
PASO = 300                      # alto de cada casilla del rodillo
VENT = 230                      # medio ancho de la ventana
DORADO = (255, 196, 30)
QUIETO = 0.4                    # fracción de cada casilla en que el rodillo se frena (avanza a saltos, como una tragamonedas)


def armar(g):
    fondo = R.fondo(g.get("fondo", "estadio_0")).copy()
    cu, cx_cu = RC.cuerpo_sin_cabeza(g["cuerpo"], 860)
    y_cu = 1880 - cu.height
    cuello = y_cu + 10
    piezas = [RC.cabeza(k) for k in g["cabezas"]]
    k_ok = g.get("pos_correcto", 2); piezas.insert(k_ok, RC.cabeza(g["clave"]))
    y_fit = cuello - max(p[1] for p in piezas)                                 # tope de la casilla de abajo (la que calza)
    win_top = int(y_fit - PASO - 40)
    return dict(fondo=fondo, cuerpo=cu, x_cu=int(W / 2 - cx_cu), y_cu=y_cu, cuello=cuello, piezas=piezas, correcto=k_ok,
                win_top=win_top, win_bot=int(cuello + 6), luces=luces(win_top, cuello))


def luces(top, bot):
    pts = []
    for y in range(top - 10, int(bot) - 10, 58):
        pts += [(W / 2 - VENT - 34, y), (W / 2 + VENT + 34, y)]
    for x in range(int(W / 2 - VENT - 34), int(W / 2 + VENT + 35), 58):
        pts.append((x, top - 62))
    return pts


def vel(g, A):
    return len(A["piezas"]) * PASO * g.get("vueltas", 2) / g["dur"]


def pasos(g, A, t):
    """Casillas que bajó el rodillo desde el encaje (a saltos: se frena QUIETO en cada una, centrado en el número entero)."""
    u = vel(g, A) * (t - g.get("t_encaje", 0.45)) / PASO + QUIETO / 2
    b = math.floor(u); x = u - b
    x = min(1.0, max(0.0, (x - QUIETO) / (1 - QUIETO)))
    return b + x * x * (3 - 2 * x)


def quieto_t(g, A):
    return QUIETO * PASO / vel(g, A)


def desplaz(g, A, k, t):
    """Cuánto le falta a la cabeza k para llegar a la casilla del cuello (0 = calza; negativo = todavía arriba)."""
    L = len(A["piezas"]) * PASO
    d = (A["correcto"] - k) * PASO + PASO * pasos(g, A, t)
    return (d + L / 2) % L - L / 2


def encajes(g):
    v = g.get("vueltas", 2)
    return [(g.get("t_encaje", 0.45) + j * g["dur"] / v) % g["dur"] for j in range(v)]


def monedas(semilla):
    r = random.Random(semilla)
    return [(r.uniform(-1, 1) * 520, r.uniform(-900, -300), r.uniform(0, 6.28), r.uniform(24, 40)) for _ in range(26)]


def cuadro(g, A, t, enc, MON):
    im = A["fondo"].copy()
    q = quieto_t(g, A)
    tras = min(((t - e + q / 2) % g["dur"]) for e in enc)                       # desde que la cabeza correcta se frena en el cuello
    premio = tras < q + 0.06
    luces_on = tras < q + 0.12                                                # se apaga antes de que llegue la cabeza siguiente
    d = ImageDraw.Draw(im, "RGBA")
    x0, x1 = W / 2 - VENT, W / 2 + VENT
    top, bot = A["win_top"], A["win_bot"]
    # el gabinete: cartel arriba, columnas a los costados, fondo oscuro del rodillo
    d.rounded_rectangle([x0 - 70, top - 120, x1 + 70, top - 10], 30, fill=(150, 20, 30), outline=DORADO, width=8)
    P.texto(d, (W / 2, top - 66), "JACKPOT!" if luces_on else "HEAD SLOT", 64, (255, 235, 90) if luces_on else (255, 255, 255), 6, (60, 0, 0))
    d.rectangle([x0 - 56, top - 10, x0 - 12, bot], fill=(150, 20, 30), outline=DORADO, width=6)
    d.rectangle([x1 + 12, top - 10, x1 + 56, bot], fill=(150, 20, 30), outline=DORADO, width=6)
    d.rectangle([x0, top, x1, bot], fill=(14, 14, 22, 215))
    fase = int(t * 8)
    for i, (lx, ly) in enumerate(A["luces"]):
        on = luces_on or (i + fase) % 2 == 0
        d.ellipse([lx - 11, ly - 11, lx + 11, ly + 11], fill=(255, 240, 150) if on else (110, 70, 20))
    # palanca a la derecha: baja cuando calza
    baja = max(0.0, 1 - tras / 0.35) if luces_on else 0.0
    px, py = x1 + 56, top + 80
    ang = math.radians(-70 + 120 * baja)
    ex, ey = px + 120 * math.cos(ang), py + 120 * math.sin(ang)
    d.line([(px, py), (ex, ey)], fill=(200, 205, 215), width=14)
    d.ellipse([ex - 30, ey - 30, ex + 30, ey + 30], fill=(225, 25, 30), outline=(255, 255, 255), width=4)
    # el rodillo: solo dentro de la ventana; la casilla de abajo desemboca en el cuello
    capa = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    y_fit = A["cuello"] - max(p[1] for p in A["piezas"])
    cerca = (99, 10 ** 9)
    for k, (img, ym) in enumerate(A["piezas"]):
        dy = desplaz(g, A, k, t)
        if abs(dy) < abs(cerca[1]):
            cerca = (k, dy)
        y = y_fit + dy + (max(p[1] for p in A["piezas"]) - ym)                 # todas las barbillas a la misma altura relativa
        if y > bot or y + img.height < top:
            continue
        capa.alpha_composite(img, (int(W / 2 - img.width / 2), int(y)))
    for j in range(-1, len(A["piezas"]) + 1):                                  # separadores de casillas (corren con el rodillo)
        sy = y_fit - PASO / 2 + 30 + ((PASO * pasos(g, A, t)) % PASO) + (j - 2) * PASO
        if top < sy < bot - 40:
            ImageDraw.Draw(capa).line([(x0 + 10, sy), (x1 - 10, sy)], fill=(255, 196, 30, 120), width=3)
    mask = Image.new("L", (W, H), 0); ImageDraw.Draw(mask).rectangle([x0, top, x1, bot], fill=255)
    capa.putalpha(Image.fromarray(np.minimum(np.asarray(capa.split()[3]), np.asarray(mask))))
    im.alpha_composite(A["cuerpo"], (A["x_cu"], A["y_cu"]))
    im.alpha_composite(capa)
    d = ImageDraw.Draw(im)
    P.texto(d, (110, 300), f"{cerca[0] + 1}.", 150, (255, 255, 255), 13, (230, 30, 30))
    if luces_on:                                                               # lluvia de monedas desde los costados del gabinete
        if tras < 0.12:                                                        # (nunca tapan la cara que calzó)
            im.alpha_composite(Image.new("RGBA", (W, H), (255, 220, 60, int(70 * (1 - tras / 0.12)))))
            d = ImageDraw.Draw(im)
        for mx, vy, fa, r in MON:
            lado = 1 if mx >= 0 else -1
            x = W / 2 + lado * (VENT + 70) + mx * 0.9 * tras / 0.7
            y = top + 60 + (vy + 300) * tras + 2600 * tras * tras
            ancho = abs(math.cos(fa + tras * 14)) * r + 4
            d.ellipse([x - ancho, y - r, x + ancho, y + r], fill=DORADO, outline=(150, 100, 0), width=3)
    if premio:
        P.texto(d, (W / 2, 1760), "PERFECT FIT!", int(110 * min(1, 0.6 + tras * 3)), (255, 230, 40), 12)
    else:
        P.texto(d, (W / 2, 1860), g["nombre"].upper(), 62, (255, 255, 255), 9, (20, 20, 30))
    im = G.capa(im, t, g["dur"], A["textos"], 120, sin_fin=True) or im
    return im.convert("RGB")


def audio(g, A, enc, dur):
    sr = M.SR; n = int(dur * sr); fx = np.zeros(n, np.float32)

    def add(t0, sig, v=1.0):
        a = int(t0 * sr) % n; b = min(n, a + len(sig)); fx[a:b] += sig[: b - a] * v
    paso_t = PASO / vel(g, A); q = quieto_t(g, A)
    k = (g.get("t_encaje", 0.45) - q / 2) % paso_t
    while k < dur:
        add(k, M.golpe(0.05), 0.3); k += paso_t                               # "clac" cada vez que el rodillo frena una casilla
    for te in enc:
        te -= q / 2
        add(te, M.ding(0.6), 0.6); add(te, M.boom(0.5), 0.35)
        for j in range(7):                                                     # monedas
            add(te + 0.06 + j * 0.07, M.pluck(1800 + 260 * (j % 3), 0.18, 0.22), 1.0)
    add(0, G.silbato(sr), 1.0)
    mu = P.musica(g, dur)
    return np.tanh((mu * 0.75 + fx) * 1.1) * 0.9, np.tanh(fx * 1.1) * 0.85


def main(guion):
    g = json.loads(Path(guion).read_text())
    out = ROOT / "salida" / g["id"]; out.mkdir(parents=True, exist_ok=True)
    A = armar(g); dur = g["dur"]; enc = encajes(g); MON = monedas(g["id"])
    A["textos"] = g.get("textos") or G.elegir("slot", g["id"], g.get("nombre", ""))
    mudo = out / "mudo.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", str(mudo)], stdin=subprocess.PIPE)
    for f in range(int(round(dur * FPS))):
        p.stdin.write(np.asarray(cuadro(g, A, f / FPS, enc, MON), np.uint8).tobytes())
    p.stdin.close(); p.wait()
    con, solo = audio(g, A, enc, dur)
    M.mezclar(out, mudo, {"short.mp4": con, "short_solo_efectos.mp4": solo})
    print(out / "short.mp4", dur, "s", "encajes", [round(x, 2) for x in enc])


if __name__ == "__main__":
    main(sys.argv[1])
