#!/usr/bin/env python3
"""
STOP TO ESCAPE (18/11 · pedido del CEO: formatos nuevos ya, más difíciles, con la lógica de parar).
Tres superestrellas (2 de hoy + 1 leyenda) ENCERRADAS en jaulas. Arriba, una LLAVE dorada va y viene rápido por un riel con
tres cerraduras. Pausá cuando la llave está justo en la cerradura de TU estrella: los barrotes de esa jaula se abren, la estrella
brilla y aparece "{NOMBRE} ESCAPED!". Solo mientras la llave está en la cerradura (cartel honesto). Las otras siguen presas.
La cerradura del medio es la más difícil (la llave pasa a máxima velocidad); las de los costados, un poco menos.
Lógica ganadora (elegir entre superestrellas + parar en el momento justo) con vuelta propia: "¿a quién liberaste y en qué intento?".
Uso: python3 produccion/render_escape.py guion.json
guion: {"id", "presos": ["cristiano_ronaldo_0", "ronaldinho_1", "lionel_messi_0"], "nombres": [...], "dur": 7.5, "idas": 3,
        "zona": 26, "musica", "fondo", "textos"}
"""
import json
import math
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

import gancho as G
import motor as M
import render_plinko as P
import render_rueda as R

ROOT = Path(__file__).resolve().parent
W, H, FPS = R.W, R.H, R.FPS
JAULAS = [200, 540, 880]               # centro de cada jaula
J_TOP, J_BOT, J_W = 900, 1640, 300
RIEL_Y, RIEL_X0, RIEL_X1 = 720, 110, 970


def x_llave(g, t):
    """La llave recorre el riel de punta a punta (seno): rápida en el medio, más lenta en los costados."""
    s = math.sin(2 * math.pi * t * g.get("idas", 3) / g["dur"] + g.get("fase", 0.0))
    return (RIEL_X0 + RIEL_X1) / 2 + s * (RIEL_X1 - RIEL_X0) / 2


def libre(g, t):
    x = x_llave(g, t)
    for i, xc in enumerate(JAULAS):
        if abs(x - xc) <= g.get("zona", 26):
            return i
    return None


def entradas(g):
    out, prev = [], None
    for f in range(int(round(g["dur"] * FPS))):
        w = libre(g, f / FPS)
        if w is not None and w != prev:
            out.append((f / FPS, w))
        prev = w
    return out


def armar(g):
    fondo = R.fondo(g.get("fondo", "estadio_0")).copy()
    sombra = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(sombra).rectangle([0, J_TOP - 60, W, H], fill=(0, 0, 0, 90))
    fondo.alpha_composite(sombra)
    presos = []
    for c in g["presos"]:
        t, cx = R.torso(c, False, 2.3)                                          # 18/11: caras GRANDES (pedido del CEO)
        k = min(1.0, (J_BOT - J_TOP - 20) / t.height)
        if k < 1:
            t = t.resize((int(t.width * k), int(t.height * k)), Image.LANCZOS); cx *= k
        if t.width > J_W - 6:                                                  # se recortan los costados (brazos), no se achica la cara
            x0 = int(max(0, min(t.width - (J_W - 6), cx - (J_W - 6) / 2)))
            t = t.crop((x0, 0, x0 + J_W - 6, t.height)); cx -= x0
        presos.append((t, cx, ImageEnhance.Brightness(ImageEnhance.Color(t).enhance(0.6)).enhance(0.75)))
    return dict(fondo=fondo, presos=presos)


def llave(d, x, y):
    oro, borde = (255, 205, 40), (90, 60, 0)
    d.ellipse([x - 34, y - 34, x + 34, y + 34], fill=oro, outline=borde, width=6)
    d.ellipse([x - 13, y - 13, x + 13, y + 13], fill=(60, 40, 0))
    d.rectangle([x - 8, y + 30, x + 8, y + 105], fill=oro, outline=borde, width=4)
    d.rectangle([x + 6, y + 70, x + 28, y + 82], fill=oro, outline=borde, width=3)
    d.rectangle([x + 6, y + 90, x + 22, y + 102], fill=oro, outline=borde, width=3)


def cuadro(g, A, t, ent):
    im = A["fondo"].copy()
    d = ImageDraw.Draw(im, "RGBA")
    gana = libre(g, t)
    # riel y cerraduras
    d.rounded_rectangle([RIEL_X0 - 40, RIEL_Y - 18, RIEL_X1 + 40, RIEL_Y + 18], 18, fill=(120, 126, 140, 255), outline=(60, 64, 74), width=4)   # metal (un riel negro liso lo marcaba el inspector)
    for i, xc in enumerate(JAULAS):
        z = g.get("zona", 26)
        col = (255, 215, 40) if gana == i else (230, 230, 240)
        d.rounded_rectangle([xc - z - 10, RIEL_Y + 30, xc + z + 10, RIEL_Y + 120], 14, fill=(96, 100, 114, 255), outline=col, width=6)
        d.ellipse([xc - 14, RIEL_Y + 52, xc + 14, RIEL_Y + 80], fill=col)
        d.rectangle([xc - 6, RIEL_Y + 74, xc + 6, RIEL_Y + 104], fill=col)
    # jaulas con las estrellas
    for i, (xc, (t_, cx, gris)) in enumerate(zip(JAULAS, A["presos"])):
        afuera = gana == i
        img = t_ if afuera else gris
        if afuera:
            aura = img.split()[3].filter(ImageFilter.MaxFilter(21)).filter(ImageFilter.GaussianBlur(14))
            au = Image.new("RGBA", img.size, (255, 210, 40, 0)); au.putalpha(aura.point(lambda v: int(v * 0.9)))
            im.alpha_composite(au, (int(xc - cx), J_BOT - img.height))
        im.alpha_composite(img, (int(xc - cx), J_BOT - img.height))
        d = ImageDraw.Draw(im, "RGBA")
        alfa = 255
        if afuera:                                                             # la jaula se abre (se desvanece) mientras la llave está en la cerradura
            desde = max((te for te, w in ent if w == i and te <= t), default=t)
            alfa = int(255 * (1 - min(1.0, (t - desde) / 0.1)))
        x0, x1 = xc - J_W / 2, xc + J_W / 2
        d.rectangle([x0, J_TOP - 22, x1, J_TOP], fill=(70, 75, 85, alfa))
        for k in range(6):
            bx = x0 + 6 + k * (J_W - 12) / 5
            d.rectangle([bx - 4, J_TOP, bx + 4, J_BOT], fill=(110, 115, 128, alfa), outline=(40, 42, 50, alfa), width=1)
        d.rectangle([x0, J_BOT - 14, x1, J_BOT + 8], fill=(60, 64, 72, 255))
        P.texto(d, (xc, J_BOT + 52), g["nombres"][i].upper(), 54 if len(g["nombres"][i]) <= 8 else 42, (255, 255, 255), 8)
    llave(d, x_llave(g, t), RIEL_Y - 110)
    if gana is not None:
        P.texto(d, (W / 2, 1790), f"{g['nombres'][gana].upper()} ESCAPED!", 84, (255, 230, 40), 11)
    G.capa(im, t, g["dur"], A["textos"], 95, ancho_max=1000, tam=80)
    return im.convert("RGB")


def audio(g, ent, dur):
    sr = M.SR; n = int(dur * sr); fx = np.zeros(n, np.float32)

    def add(t0, sig, v=1.0):
        a = int(t0 * sr) % n; b = min(n, a + len(sig)); fx[a:b] += sig[: b - a] * v
    for te, _ in ent:
        add(te, M.ding(0.6), 0.6); add(te, M.boom(0.5), 0.3)
    add(0, G.silbato(sr), 1.0)
    mu = P.musica(g, dur)
    return np.tanh((mu * 0.75 + fx) * 1.1) * 0.9, np.tanh(fx * 1.1) * 0.85


def main(guion):
    g = json.loads(Path(guion).read_text())
    out = ROOT / "salida" / g["id"]; out.mkdir(parents=True, exist_ok=True)
    A = armar(g); dur = g["dur"]; ent = entradas(g)
    A["textos"] = g.get("textos") or G.elegir("escape", g["id"], "")
    mudo = out / "mudo.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", str(mudo)], stdin=subprocess.PIPE)
    for f in range(int(round(dur * FPS))):
        p.stdin.write(np.asarray(cuadro(g, A, f / FPS, ent), np.uint8).tobytes())
    p.stdin.close(); p.wait()
    con, solo = audio(g, ent, dur)
    M.mezclar(out, mudo, {"short.mp4": con, "short_solo_efectos.mp4": solo})
    print(out / "short.mp4", dur, "s", "entradas", [(round(a, 2), b) for a, b in ent])


if __name__ == "__main__":
    main(sys.argv[1])
