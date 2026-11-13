#!/usr/bin/env python3
"""
LEGS WHEEL (13/11 · variante de WHEEL, el formato que más rinde): WHEEL al revés.
Arriba, FIJO y desde el cuadro 0: el torso de una superestrella (cara bien visible = reconocimiento inmediato).
Abajo gira una rueda de 8 pares de piernas (los pies hacia el centro); solo uno es del dueño del torso (sale de la
MISMA foto, así que calza perfecto: mismo short, mismas medias). Hay que parar cuando las piernas correctas quedan arriba,
pegadas a la cintura. Contador 1-8, destello, PERFECT!, ding. Loop: vueltas enteras.

Reusa los recortes y el sonido de render_rueda.py (cuerpos/*.png con detección de cara).
Uso: python3 produccion/render_piernas.py guion.json
guion: {"id", "cuerpo": "lionel_messi_3", "nombre": "Messi", "piernas": [7 cuerpos de otros], "dur": 6.6, "vueltas": 4,
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
HUECO = 120
ESCALA = 0.92
TORSO_TOP = 360                                   # debajo de la franja del gancho


def centrada(img, cx):
    """Ensancha la imagen para que el punto cx quede en el centro (así gira alrededor del eje del jugador)."""
    izq, der = cx, img.width - cx
    m = int(max(izq, der))
    out = Image.new("RGBA", (2 * m, img.height), (0, 0, 0, 0))
    out.alpha_composite(img, (int(m - cx), 0))
    return out


def armar(g):
    tor, tcx = RR.torso(g["cuerpo"], True, 1.15 * ESCALA / 0.92)
    pz = [centrada(*RR.piernas(n)) for n in g["piernas"]]
    k = g.get("pos_correcto", 3)
    pz.insert(k, centrada(*RR.piernas(g["cuerpo"])))
    s = ESCALA
    pz = [p.resize((int(p.width * s), int(p.height * s)), Image.LANCZOS) for p in pz]
    alto = max(p.height for p in pz)
    cint_y = TORSO_TOP + tor.height - 10                                       # dónde termina el torso (la cintura)
    r = HUECO + alto / 2
    cy = cint_y + alto / 2 + r                                                 # la pieza de arriba apoya en la cintura
    return dict(torso=tor, tcx=tcx, piezas=pz, correcto=k, r=r, centro=(W / 2, cy), cint_y=cint_y, fondo=RR.fondo(g.get("fondo")))


def angulo(g, A, t):
    """Ángulo de la pieza 0 (270° = arriba). Arranca corrido para que la correcta calce en t_encaje."""
    n = len(A["piezas"]); paso = 360 / n
    vel = g.get("sentido", 1) * 360.0 * g.get("vueltas", 4) / g["dur"]
    return 270 - A["correcto"] * paso - vel * g.get("t_encaje", 0.45) + vel * t


def encajes(g, A):
    n = len(A["piezas"]); paso = 360 / n; out = []
    for f in range(int(round(g["dur"] * FPS))):
        t = f / FPS
        a = (angulo(g, A, t) + A["correcto"] * paso - 270) % 360
        if min(a, 360 - a) < 360 * g.get("vueltas", 4) / g["dur"] / FPS / 1.9 and (not out or t - out[-1] > 0.5):
            out.append(t)
    return out


def cuadro(g, A, t, enc):
    im = A["fondo"].copy()
    cx, cy = A["centro"]
    n = len(A["piezas"]); paso = 360 / n; a0 = angulo(g, A, t)
    capas = []
    for k, img in enumerate(A["piezas"]):
        th = a0 + k * paso
        rad = math.radians(th)
        px, py = cx + A["r"] * math.cos(rad), cy + A["r"] * math.sin(rad)
        rot = img.rotate(270 - th, expand=True, resample=Image.BICUBIC)       # los pies siempre hacia el centro
        arriba = -math.sin(rad)
        if arriba < 0.92:                                                      # las que no están arriba, más apagadas (se lee mejor)
            r_, g_, b_, a_ = rot.split()
            osc = 0.55 + 0.3 * max(0, arriba)
            rot = Image.merge("RGBA", [c.point(lambda v, o=osc: int(v * o)) for c in (r_, g_, b_)] + [a_])
        capas.append((arriba, rot, px, py))                           # la de arriba se dibuja última (adelante)
    for _, rot, px, py in sorted(capas, key=lambda c: c[0]):
        im.alpha_composite(rot, (int(px - rot.width / 2), int(py - rot.height / 2)))
    im.alpha_composite(A["torso"], (int(cx - A["tcx"]), TORSO_TOP))          # el torso de la estrella, fijo y adelante
    d = ImageDraw.Draw(im)
    num = int(((a0 - angulo(g, A, 0)) % 360) // paso) % n + 1
    P.texto(d, (110, 300), f"{num}.", 150, (255, 255, 255), 13, (230, 30, 30))
    P.texto(d, (W / 2, 1860), g["nombre"].upper(), 70, (255, 255, 255), 10, (20, 20, 30))
    for te in enc:
        e = t - te
        if -0.05 <= e < 0.3:
            if e < 0.15:
                im.alpha_composite(Image.new("RGBA", (W, H), (60, 230, 90, int(55 * (1 - max(e, 0) / 0.15)))))
                d = ImageDraw.Draw(im)
            P.texto(d, (W / 2, 1720), "PERFECT!", int(110 * min(1, (e + 0.05) / 0.1)) + 1, (255, 230, 40), 12)
    import gancho as G
    G.capa(im, t, g["dur"], A["textos"], 95, ancho_max=1000, tam=80)
    return im.convert("RGB")


def main(guion):
    g = json.loads(Path(guion).read_text())
    out = ROOT / "salida" / g["id"]; out.mkdir(parents=True, exist_ok=True)
    A = armar(g); dur = g["dur"]; enc = encajes(g, A)
    import gancho as G
    A["textos"] = g.get("textos") or G.elegir("piernas", g["id"], g.get("nombre", ""))
    mudo = out / "mudo.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", str(mudo)], stdin=subprocess.PIPE)
    for f in range(int(round(dur * FPS))):
        p.stdin.write(np.asarray(cuadro(g, A, f / FPS, enc), np.uint8).tobytes())
    p.stdin.close(); p.wait()
    con, solo = RR.audio(dict(g, vueltas=g.get("vueltas", 4)), A, enc, dur)
    M.mezclar(out, mudo, {"short.mp4": con, "short_solo_efectos.mp4": solo})
    print(out / "short.mp4", dur, "s", "encajes", [round(x, 2) for x in enc])


if __name__ == "__main__":
    main(sys.argv[1])
