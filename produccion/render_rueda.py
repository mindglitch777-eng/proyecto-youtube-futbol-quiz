#!/usr/bin/env python3
"""
WHEEL STOP (réplica de "X vs Y or Z stop challenge", 45 M+ en una semana).
Abajo: las piernas de UN jugador (de un PNG de cuerpo entero, de frente). Arriba: rueda de 8 torsos PNG sin fondo
(cabeza hacia el centro) que gira; el de abajo se apoya sobre las piernas. Uno solo es el del dueño de las piernas
(sale de la MISMA foto, así que calza perfecto). Contador 1-8 arriba. Cuando calza el correcto: destello, PERFECT!, ding.
Loop: 2 vueltas completas.

Recortes: assets/recortes/torsos/*.png y assets/recortes/cuerpos/*.png (los baja GitHub: pipeline/buscar_recortes.py).
Uso: python3 produccion/render_rueda.py produccion/guiones/rueda_01.json
guion: {"id": "rueda_01", "cuerpo": "lionel_messi_3", "torsos": ["cristiano_ronaldo_0", ...7], "nombre": "Messi",
        "dur": 8.8, "sentido": 1, "musica": "trallallero_2", "fondo": "estadio_0"}
"""
import json
import math
import subprocess
import sys
from functools import lru_cache
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw

import motor as M
import render_plinko as P

ROOT = Path(__file__).resolve().parent
REC = ROOT / "assets" / "recortes"
W, H, FPS = 1080, 1920, 30
CARA = 104                    # alto de cara (px) de todos los torsos, para que queden parejos
K_CINTURA = 4.0               # los torsos llegan hasta la cadera (4 caras debajo del borde de arriba de la cara)
K_PIERNA = 4.45               # las piernas arrancan en el short: no se ve la camiseta del dueño (no delata quién es)
CHICO = 0.92                  # el torso correcto, un poco más chico (que no salte a la vista)
HUECO = 105                   # radio del agujero del centro
PIE_Y = 1830                 # dónde apoyan los botines

_det = cv2.FaceDetectorYN.create(str(ROOT / "assets" / "modelos" / "face_detection_yunet_2023mar.onnx"), "", (320, 320), 0.6)


def cara(im):
    a = np.asarray(im)
    bgr = cv2.cvtColor(a[..., :3], cv2.COLOR_RGB2BGR); bgr[a[..., 3] < 30] = 255
    _det.setInputSize((bgr.shape[1], bgr.shape[0]))
    _, f = _det.detect(bgr)
    if f is None or not len(f):
        raise ValueError("sin cara")
    return max(f, key=lambda c: c[2] * c[3])[:4]


@lru_cache(maxsize=64)
def torso(nombre, desde_cuerpo=False, escala=1.0):
    """Torso (de la cabeza a la cintura) escalado para que la cara mida CARA px. Devuelve (img, fx_centro_cara)."""
    im = Image.open(REC / ("cuerpos" if desde_cuerpo else "torsos") / f"{nombre}.png").convert("RGBA")
    x, y, fw, fh = cara(im)
    s = CARA * escala / fh
    im = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)
    x, y, fw, fh = x * s, y * s, fw * s, fh * s
    corte = int(y + K_CINTURA * fh)
    t = im.crop((0, 0, im.width, min(im.height, corte)))
    bb = t.getbbox()
    t = t.crop((bb[0], bb[1], bb[2], t.height))
    return t, (x + fw / 2) - bb[0]


@lru_cache(maxsize=8)
def piernas(nombre):
    im = Image.open(REC / "cuerpos" / f"{nombre}.png").convert("RGBA")
    x, y, fw, fh = cara(im)
    s = CARA / fh
    im = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
    x, y, fw, fh = x * s, y * s, fw * s, fh * s
    corte = int(y + K_PIERNA * fh) - 6
    p = im.crop((0, corte, im.width, im.height))
    bb = p.getbbox()
    return p.crop((bb[0], 0, bb[2], bb[3])), (x + fw / 2) - bb[0]


@lru_cache(maxsize=4)
def fondo(nombre=None):
    f = ROOT / "assets" / "fondos" / f"{nombre}.jpg" if nombre else None
    if f and f.exists():
        return Image.open(f).convert("RGBA").resize((W, H))
    import render_rueda_fondo as RF
    return RF.dibujado()


def armar(g):
    pz = [torso(n) for n in g["torsos"]]
    correcto = torso(g["cuerpo"], True, g.get("chico", CHICO))
    k = g.get("pos_correcto", 3)
    pz.insert(k, correcto)
    leg, leg_cx = piernas(g["cuerpo"])
    alto = max(p[0].height for p in pz)
    r = HUECO + alto / 2                                                       # radio hasta el centro de cada torso
    cint_y = PIE_Y - leg.height                                                # cintura de las piernas
    cy = cint_y - pz[k][0].height / 2 - r + 8                                  # el torso de abajo apoya en la cintura
    return dict(piezas=pz, correcto=k, piernas=leg, leg_cx=leg_cx, r=r, centro=(W / 2, cy), cint_y=cint_y, fondo=fondo(g.get("fondo")))


def angulo(g, A, t):
    """Ángulo de la pieza 0 (90° = abajo). Arranca corrido para que el correcto calce recién a ~2,5 s."""
    n = len(A["piezas"]); paso = 360 / n
    vel = g.get("sentido", 1) * 360.0 * g.get("vueltas", 2) / g["dur"]
    base = 90 - A["correcto"] * paso - vel * g.get("t_encaje", 2.5)
    return base + vel * t


def encajes(g, A):
    n = len(A["piezas"]); paso = 360 / n; out = []
    for f in range(int(round(g["dur"] * FPS))):
        t = f / FPS
        a = (angulo(g, A, t) + A["correcto"] * paso - 90) % 360
        if min(a, 360 - a) < 360 * g.get("vueltas", 2) / g["dur"] / FPS / 1.9 and (not out or t - out[-1] > 1):
            out.append(t)
    return out


def cuadro(g, A, t, enc):
    im = A["fondo"].copy()
    cx, cy = A["centro"]
    leg = A["piernas"]
    im.alpha_composite(leg, (int(cx - A["leg_cx"]), int(A["cint_y"])))
    n = len(A["piezas"]); paso = 360 / n; a0 = angulo(g, A, t)
    capas = []
    for k, (img, fx) in enumerate(A["piezas"]):
        th = a0 + k * paso
        rad = math.radians(th)
        px, py = cx + A["r"] * math.cos(rad), cy + A["r"] * math.sin(rad)
        rot = img.rotate(90 - th, expand=True, resample=Image.BICUBIC)
        abajo = math.sin(rad)                                                  # la de abajo se dibuja última (adelante)
        capas.append((abajo, rot, px, py))
    for _, rot, px, py in sorted(capas, key=lambda c: c[0]):
        im.alpha_composite(rot, (int(px - rot.width / 2), int(py - rot.height / 2)))
    d = ImageDraw.Draw(im)
    num = int(((a0 - angulo(g, A, 0)) % 360) // paso) % n + 1
    P.texto(d, (110, 260), f"{num}.", 150, (255, 255, 255), 13, (230, 30, 30))
    for te in enc:
        e = t - te
        if -0.05 <= e < 0.55:
            if e < 0.15:
                im.alpha_composite(Image.new("RGBA", (W, H), (60, 230, 90, int(55 * (1 - max(e, 0) / 0.15)))))
                d = ImageDraw.Draw(im)
            P.texto(d, (W / 2, 1860), "PERFECT!", int(110 * min(1, (e + 0.05) / 0.1)) + 1, (255, 230, 40), 12)
    import gancho as G
    G.capa(im, t, g["dur"], A["textos"], 95, ancho_max=1000, tam=80)
    return im.convert("RGB")


def audio(g, A, enc, dur):
    sr = M.SR; n = int(dur * sr); fx = np.zeros(n, np.float32)

    def add(t0, sig, v=1.0):
        a = int(t0 * sr) % n; b = min(n, a + len(sig)); fx[a:b] += sig[: b - a] * v
    paso = 360 / len(A["piezas"]); vel = 360 * g.get("vueltas", 2) / g["dur"]
    k = 0.0
    while k < dur:
        add(k, M.golpe(0.05), 0.35); k += paso / vel
    for te in enc:
        add(te, M.ding(0.6), 0.6); add(te, M.boom(0.5), 0.4)
    import gancho as G
    add(0, G.silbato(sr), 1.0)                                                 # pitazo en el segundo 0
    mu = P.musica(g, dur)
    return np.tanh((mu * 0.75 + fx) * 1.1) * 0.9, np.tanh(fx * 1.1) * 0.85


def main(guion):
    g = json.loads(Path(guion).read_text())
    out = ROOT / "salida" / g["id"]; out.mkdir(parents=True, exist_ok=True)
    A = armar(g); dur = g["dur"]; enc = encajes(g, A)
    import gancho as G
    A["textos"] = g.get("textos") or G.elegir("rueda", g["id"], g.get("nombre", ""))
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
