#!/usr/bin/env python3
"""
CONVEYOR STOP (13/11 · variante de WHEEL, el formato que más rinde): misma decisión (¿cuál es el torso de la estrella?)
y mismo "parar en el momento justo", pero sin rueda: los torsos cuelgan de ganchos de una CINTA aérea que corre de costado.
Abajo, fijas, las piernas de una superestrella. SOLO superestrellas en la cinta (6 torsos: el correcto + las otras 5),
así el título siempre es "estrella vs estrella o estrella". Cuando el torso correcto queda justo sobre las piernas:
destello, la cinta se pone verde, chispas doradas en la cintura, PERFECT!, ding. Loop: vueltas enteras de la cinta.
Desde el cuadro 0 se ve una superestrella sobre las piernas (no la correcta: el encaje cae en la costura del loop).

Reusa los recortes y el audio de render_rueda.py.
Uso: python3 produccion/render_cinta.py guion.json
guion: {"id", "cuerpo": "lionel_messi_3", "nombre": "Messi", "torsos": [5 torsos de otras estrellas], "dur": 6.6, "vueltas": 2,
        "t_encaje": 0.45, "sentido": 1, "musica", "fondo", "pos_correcto": 3}
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
import render_rueda as RR

ROOT = Path(__file__).resolve().parent
W, H, FPS = RR.W, RR.H, RR.FPS
S = 1.35                       # todo más grande que en WHEEL: acá no hay rueda que ocupar, la estrella llena la pantalla
PASO = 600                     # distancia entre torsos en la cinta
PIE_Y = 1800
QUIETO = 0.35                  # fracción de cada paso en que la cinta se frena con un torso justo sobre las piernas (avanza a saltos)


def escalar(img, s):
    return img.resize((max(1, int(img.width * s)), max(1, int(img.height * s))), Image.LANCZOS)


def armar(g):
    pz = []
    for n in g["torsos"]:
        t, cx = RR.torso(n)
        pz.append((escalar(t, S), cx * S))
    t, cx = RR.torso(g["cuerpo"], True, RR.CHICO)
    k = g.get("pos_correcto", 3)
    pz.insert(k, (escalar(t, S), cx * S))
    leg, leg_cx = RR.piernas(g["cuerpo"])
    leg = escalar(leg, S); leg_cx *= S
    cint_y = PIE_Y - leg.height
    alto = max(p[0].height for p in pz)
    riel_y = int(cint_y + 8 - alto - 60)
    return dict(piezas=pz, correcto=k, piernas=leg, leg_cx=leg_cx, cint_y=cint_y, riel_y=riel_y, fondo=RR.fondo(g.get("fondo")))


def largo(A):
    return len(A["piezas"]) * PASO


def vel(g, A):
    return g.get("sentido", 1) * largo(A) * g.get("vueltas", 2) / g["dur"]


def pasos(g, A, t):
    """Cuántos torsos avanzó la cinta desde el encaje (a saltos: se frena QUIETO en cada uno, centrado en el número entero)."""
    u = vel(g, A) * (t - g.get("t_encaje", 0.45)) / PASO + QUIETO / 2
    b = math.floor(u); x = u - b
    x = min(1.0, max(0.0, (x - QUIETO) / (1 - QUIETO)))
    return b + x * x * (3 - 2 * x)


def desplaz(g, A, k, t):
    """Distancia en x del torso k al centro (0 = justo sobre las piernas), envuelta en la cinta."""
    L = largo(A)
    d = (k - A["correcto"]) * PASO + PASO * pasos(g, A, t)
    return (d + L / 2) % L - L / 2


def quieto_t(g, A):
    return QUIETO * PASO / abs(vel(g, A))


def encajes(g):
    v = g.get("vueltas", 2)
    return [(g.get("t_encaje", 0.45) + j * g["dur"] / v) % g["dur"] for j in range(v)]


def riel(d, A, g, t, verde):
    y = A["riel_y"]
    col = (60, 200, 90) if verde else (70, 76, 92)
    d.rectangle([0, y - 26, W, y + 26], fill=(28, 30, 38))
    d.rectangle([0, y - 20, W, y + 20], fill=col)
    d.line([(0, y - 20), (W, y - 20)], fill=(150, 156, 172), width=3)
    off = (PASO * pasos(g, A, t)) % 60                                                 # eslabones que corren con la cinta
    x = -60 + off
    while x < W + 60:
        d.rounded_rectangle([x, y - 9, x + 34, y + 9], 8, fill=(24, 26, 32))
        x += 60
    for cx in (40, W - 40):                                                    # rodillos en las puntas
        d.ellipse([cx - 34, y - 34, cx + 34, y + 34], fill=(40, 42, 52), outline=(150, 156, 172), width=4)
        a = math.radians(PASO * pasos(g, A, t) * 1.6)
        d.line([(cx - 26 * math.cos(a), y - 26 * math.sin(a)), (cx + 26 * math.cos(a), y + 26 * math.sin(a))], fill=(150, 156, 172), width=5)


def chispas(im, t_desde, cx, cy):
    d = ImageDraw.Draw(im)
    for j in range(16):
        ang = j * 2 * math.pi / 16 + 0.3
        r = 60 + 520 * t_desde
        x, y = cx + r * math.cos(ang), cy + r * math.sin(ang) * 0.6
        s = max(2, int(18 * (1 - t_desde / 0.55)))
        d.polygon([(x, y - s * 2), (x + s * 0.6, y - s * 0.6), (x + s * 2, y), (x + s * 0.6, y + s * 0.6),
                   (x, y + s * 2), (x - s * 0.6, y + s * 0.6), (x - s * 2, y), (x - s * 0.6, y - s * 0.6)], fill=(255, 214, 40))


def cuadro(g, A, t, enc):
    im = A["fondo"].copy()
    cx = W / 2
    im.alpha_composite(A["piernas"], (int(cx - A["leg_cx"]), int(A["cint_y"])))
    q = quieto_t(g, A)
    tras = min(((t - e + q / 2) % g["dur"]) for e in enc)                       # desde que el correcto se frena sobre las piernas
    verde = tras < q + 0.06
    d = ImageDraw.Draw(im)
    riel(d, A, g, t, verde)
    capas, cerca = [], (99, 10 ** 9)
    for k, (img, fx) in enumerate(A["piezas"]):
        dx = desplaz(g, A, k, t)
        if abs(dx) > W / 2 + 400:
            continue
        x = cx + dx - fx
        top = A["cint_y"] + 8 - img.height
        if abs(dx) < abs(cerca[1]):
            cerca = (k, dx)
        foco = max(0.0, 1 - abs(dx) / PASO)
        if foco < 0.9:                                                         # los que no están sobre las piernas, apagados
            osc = 0.55 + 0.45 * foco
            r_, g_, b_, a_ = img.split()
            img = Image.merge("RGBA", [c.point(lambda v, o=osc: int(v * o)) for c in (r_, g_, b_)] + [a_])
        capas.append((foco, img, int(x), int(top), cx + dx))
    for foco, img, x, top, hx in sorted(capas, key=lambda c: c[0]):
        d.line([(hx, A["riel_y"] + 20), (hx, top + 14)], fill=(200, 205, 215), width=6)       # el gancho
        d.arc([hx - 22, A["riel_y"] + 4, hx + 22, A["riel_y"] + 40], 200, 340, fill=(200, 205, 215), width=6)
        im.alpha_composite(img, (x, top))
    d = ImageDraw.Draw(im)
    P.texto(d, (110, A["riel_y"] - 110), f"{cerca[0] + 1}.", 150, (255, 255, 255), 13, (230, 30, 30))
    if verde:
        if tras < 0.15:
            im.alpha_composite(Image.new("RGBA", (W, H), (60, 230, 90, int(55 * (1 - tras / 0.15)))))
        chispas(im, tras * 0.55 / (q + 0.06), cx, A["cint_y"])
        d = ImageDraw.Draw(im)
        P.texto(d, (W / 2, 1860), "PERFECT!", int(110 * min(1, 0.6 + tras * 4)) + 1, (255, 230, 40), 12)
    else:
        P.texto(d, (W / 2, 1860), g["nombre"].upper(), 66, (255, 255, 255), 10, (20, 20, 30))
    import gancho as G
    im = G.capa(im, t, g["dur"], A["textos"], 120, sin_fin=True) or im
    return im.convert("RGB")


def audio(g, A, enc, dur):
    sr = M.SR; n = int(dur * sr); fx = np.zeros(n, np.float32)

    def add(t0, sig, v=1.0):
        a = int(t0 * sr) % n; b = min(n, a + len(sig)); fx[a:b] += sig[: b - a] * v
    paso_t = PASO / abs(vel(g, A)); q = quieto_t(g, A)
    k = (g.get("t_encaje", 0.45) - q / 2) % paso_t
    while k < dur:
        add(k, M.golpe(0.05), 0.35); k += paso_t                              # "clac" cada vez que la cinta frena un torso en el centro
    for te in enc:
        add(te - q / 2, M.ding(0.6), 0.6); add(te - q / 2, M.boom(0.5), 0.4)
    import gancho as G
    add(0, G.silbato(sr), 1.0)
    mu = P.musica(g, dur)
    return np.tanh((mu * 0.75 + fx) * 1.1) * 0.9, np.tanh(fx * 1.1) * 0.85


def main(guion):
    g = json.loads(Path(guion).read_text())
    out = ROOT / "salida" / g["id"]; out.mkdir(parents=True, exist_ok=True)
    A = armar(g); dur = g["dur"]; enc = encajes(g)
    import gancho as G
    A["textos"] = g.get("textos") or G.elegir("cinta", g["id"], g.get("nombre", ""))
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
