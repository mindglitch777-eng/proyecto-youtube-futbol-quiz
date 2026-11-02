#!/usr/bin/env python3
"""
GANCHO + APUESTA + CTA (guía de la IA de YouTube para subir "visto vs. descartado" del 51% a +65%):
- 0 a 1,5 s: texto grande, centrado, 4-6 palabras, amarillo con borde negro sobre fondo oscuro (el reto ya está en marcha).
- Durante el reto: la "apuesta" (condición que compromete: "STOP AT 100% OR LOSE", "ONLY 3 TRIES").
- Último 1,2 s: CTA corto ("COMMENT YOUR NUMBER · FOLLOW FOR PART 2"), sin pantalla fija ni silencio: el loop sigue.
- Silbato de árbitro en el segundo 0 (estímulo agudo que frena el scroll).
Cada formato tiene sus propios textos (no todos iguales).
"""
import math
import random
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
FUENTE = ROOT / "assets" / "fuentes" / "ArchivoBlack-Regular.ttf"
T_GANCHO, T_CTA = 1.5, 1.2

TEXTOS = {
    "stop": dict(gancho=["ONLY 1% STOP AT 100%", "CAN YOU STOP AT 100%?", "STOP IT AT 100%"],
                 apuesta=["STOP AT 100% OR LOSE", "MISS IT = YOUR TEAM LOSES", "ONLY 3 TRIES"],
                 dificil=["IMPOSSIBLE LEVEL: 3 TRIES", "HARD MODE: ONLY 3 TRIES"],
                 cta=["COMMENT 1-4 · FOLLOW FOR PART 2"]),
    "rueda": dict(gancho=["STOP IT ON {n}'S BODY", "FIND {n}'S REAL BODY", "ONLY 1% STOP IT ON {n}"],
                  apuesta=["PERFECT FIT OR YOU LOSE", "ONLY 3 TRIES", "STOP ON THE PERFECT ONE"],
                  cta=["COMMENT YOUR NUMBER · FOLLOW FOR PART 2"]),
    "find": dict(gancho=["FIND THE REAL {n}", "ONLY 1% FIND THEM ALL"], apuesta=["3 ROUNDS · NO MISTAKES"],
                 cta=["COMMENT YOUR NUMBERS · FOLLOW FOR PART 2"]),
    "plinko": dict(gancho=["PICK YOUR PLAYER NOW", "WHO LANDS ON 99?"], apuesta=["WRONG PICK = YOU LOSE"],
                   cta=["COMMENT YOUR PICK · FOLLOW FOR PART 2"]),
    "cabeza": dict(gancho=["CATCH {n}'S REAL HEAD", "WHICH HEAD IS {n}?"], apuesta=["GUESS BEFORE IT LANDS"],
                   cta=["COMMENT 1, 2 OR 3 · FOLLOW FOR PART 2"]),
    "dress": dict(gancho=["PAUSE WHEN IT FITS", "STOP IT ON THE FACE"], apuesta=["4 TRIES · NO MISTAKES"],
                  cta=["COMMENT HOW MANY · FOLLOW FOR PART 2"]),
    "torre": dict(gancho=["GUESS THE FLAG FIRST", "WHOSE FLAG IS THIS?"], apuesta=["GUESS BEFORE THE COLORS"],
                  cta=["COMMENT YOUR GUESS · FOLLOW FOR PART 2"]),
}
FIJADO = {"stop": "How many tries did it take you? 😤 I read them all 👇",
          "rueda": "What number did you stop it on? 👀 I read them all 👇",
          "find": "How many did you get right? Be honest 👀 I read them all 👇",
          "plinko": "Who did you pick? 👀 I read them all 👇",
          "cabeza": "Did you get it before it landed? 👀 I read them all 👇",
          "dress": "How many did you stop on time? 😂 I read them all 👇",
          "torre": "Did you guess it before the colors? 👀 I read them all 👇"}


def elegir(tipo, semilla, nombre="", dificil=False):
    """Textos del video (dict gancho/apuesta/cta), estables por semilla."""
    r = random.Random(semilla); T = TEXTOS[tipo]
    ap = T.get("dificil") if dificil and T.get("dificil") else T["apuesta"]
    f = lambda xs: r.choice(xs).format(n=nombre.upper())
    return dict(gancho=f(T["gancho"]), apuesta=f(ap), cta=f(T["cta"]))


@lru_cache(maxsize=16)
def _fuente(tam):
    return ImageFont.truetype(str(FUENTE), tam)


def cartel(im, txt, cy, ancho_max=1000, tam=88, pop=1.0, fondo=(10, 10, 16, 215), color=(255, 230, 40)):
    d = ImageDraw.Draw(im, "RGBA")
    tam = int(tam * pop)
    while tam > 30 and _fuente(tam).getlength(txt) > ancho_max:
        tam -= 2
    f = _fuente(tam); w = f.getlength(txt); h = tam * 1.2
    cx = im.width / 2
    d.rounded_rectangle([cx - w / 2 - 26, cy - h / 2 - 10, cx + w / 2 + 26, cy + h / 2 + 10], int(h / 2.6), fill=fondo)
    d.text((cx, cy), txt, font=f, fill=color, anchor="mm", stroke_width=max(3, tam // 14), stroke_fill=(0, 0, 0))
    return im


def capa(im, t, dur, tx, cy, ancho_max=1000, tam=88):
    """Dibuja el texto que toca en el segundo t: gancho (0-1,5 s), apuesta (medio) o CTA (último 1,2 s)."""
    if t < T_GANCHO:
        txt, t0 = tx["gancho"], 0.0
    elif t >= dur - T_CTA:
        txt, t0 = tx["cta"], dur - T_CTA
    else:
        txt, t0 = tx["apuesta"], T_GANCHO
    e = t - t0
    pop = 1.0 + 0.18 * math.exp(-e * 14) * (e > 0.0)                    # golpe chiquito al cambiar de texto
    col = (255, 255, 255) if txt == tx["cta"] else (255, 230, 40)
    return cartel(im, txt, cy, ancho_max, tam, pop, color=col)


def silbato(sr, dur=0.42):
    """Pitazo de árbitro (dos tonos con trino), corto y agudo."""
    t = np.arange(int(dur * sr)) / sr
    trino = 1 + 0.035 * np.sign(np.sin(2 * np.pi * 26 * t))
    s = np.sin(2 * np.pi * 2900 * np.cumsum(trino) / sr) * 0.6 + np.sin(2 * np.pi * 3400 * np.cumsum(trino) / sr) * 0.3
    s += np.random.default_rng(1).standard_normal(len(t)) * 0.05
    env = np.minimum(1, t / 0.012) * np.minimum(1, (dur - t) / 0.06)
    return (s * env * 0.45).astype(np.float32)


def textos_de(g, tipo, nombre="", con_gancho=True):
    """Textos del guion (si los trae) o elegidos por formato. Si el formato ya tiene su título-gancho arriba,
    el cartel arranca directo con la apuesta (no repite el título)."""
    tx = g.get("textos") or elegir(tipo, g["id"], nombre, dificil=g.get("nivel_dificil", False))
    if not con_gancho:
        tx = dict(tx, gancho=tx["apuesta"])
    return tx


def con_pito(x, sr=None):
    """Suma el pitazo en el segundo 0 a una pista (array) o a todas las de un dict {archivo: array}."""
    import motor as M
    sr = sr or M.SR
    if isinstance(x, dict):
        return {k: con_pito(v, sr) for k, v in x.items()}
    p = silbato(sr); a = np.array(x, np.float32, copy=True)
    if a.ndim == 1:
        a[:len(p)] = np.tanh(a[:len(p)] + p)
    else:
        a[:len(p)] = np.tanh(a[:len(p)] + p[:, None])
    return a
