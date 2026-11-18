#!/usr/bin/env python3
"""
VS STOP (16/11 · pedido del CEO/Gerente: la comparativa cara a cara es el 2.º interés de nuestro público según Studio):
dos superestrellas GRANDES frente a frente (duelos que pide el público: Ronaldo vs Messi, Yamal vs Mbappé/Vinícius) y arriba
un MEDIDOR de duelo: la pelota va y viene entre los dos. Pausá cuando la pelota está en la zona dorada de TU estrella:
esa estrella se lleva la corona (brilla, corona que cae, "MESSI WINS!") y la otra se apaga. En el medio no gana nadie.
Misma mecánica ganadora (decisión entre superestrellas + parar en el momento justo) con vuelta propia: acá ELEGÍS a quién
hacer ganar, y el comentario natural es "¿a quién paraste?". Honesto: la corona aparece SOLO mientras la pelota está en la zona.
Loop: 2 idas y vueltas enteras.

Uso: python3 produccion/render_vs.py guion.json
guion: {"id", "cuerpos": ["cristiano_ronaldo_14", "lionel_messi_3"], "nombres": ["Ronaldo", "Messi"], "dur": 7.0,
        "colores": [[220, 30, 40], [40, 110, 230]], "musica", "fondo"}
"""
import json
import math
import subprocess
import sys
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

import gancho as G
import motor as M
import render_plinko as P
import render_rueda as R

ROOT = Path(__file__).resolve().parent
W, H, FPS = 1080, 1920, 30
BAR_Y, BAR_X0, BAR_X1 = 800, 90, 990
UMBRAL = 0.88                         # |posición| desde la que la pelota está en la zona dorada (≈0,5 s por pasada)
ESC = 2.1
ANCHO_MAX = 800


@lru_cache(maxsize=8)
def corona():
    im = Image.open(ROOT / "assets" / "fluent" / "crown_3d.png").convert("RGBA")
    return im.resize((190, int(im.height * 190 / im.width)), Image.LANCZOS)


def armar(g):
    fondo = R.fondo(g.get("fondo", "estadio_0")).copy()
    tor = []
    for c in g["cuerpos"]:
        t, cx = R.torso(c, True, ESC)
        if t.width > ANCHO_MAX:                                                # poses abiertas (Yamal agachado) taparían al otro
            k = ANCHO_MAX / t.width
            t = t.resize((ANCHO_MAX, int(t.height * k)), Image.LANCZOS); cx *= k
        tor.append((t, cx))
    pos = [(290, 1830), (790, 1830)]                                           # centro de la cara en x, pie del torso en y
    brillo = [ImageEnhance.Brightness(t).enhance(1.12) for t, _ in tor]
    apagado = []
    for t, _ in tor:
        gris = ImageEnhance.Color(t).enhance(0.15)
        apagado.append(ImageEnhance.Brightness(gris).enhance(0.55))
    aura = []
    for t, _ in tor:
        a = t.split()[3].filter(ImageFilter.MaxFilter(21)).filter(ImageFilter.GaussianBlur(14))
        au = Image.new("RGBA", t.size, (255, 210, 40, 0)); au.putalpha(a.point(lambda v: int(v * 0.9)))
        aura.append(au)
    return dict(fondo=fondo, tor=tor, pos=pos, brillo=brillo, apagado=apagado, aura=aura)


def x_de(g, t):
    """Posición de la pelota en el medidor, de -1 (estrella izquierda) a 1 (derecha). Arranca en el medio, ya moviéndose."""
    return math.sin(2 * math.pi * t * g.get("idas", 2) / g["dur"] + g.get("fase", 0.0))   # 18/11 CEO: más rápido = más difícil


def ganador(g, t):
    x = x_de(g, t)
    u = g.get("umbral", UMBRAL)                                               # 18/11: zona dorada más chica = más difícil
    return 0 if x <= -u else 1 if x >= u else None


def entradas(g):
    """Momentos en que la pelota entra a una zona dorada (para el sonido y el destello)."""
    out, prev = [], None
    for f in range(int(round(g["dur"] * FPS))):
        w = ganador(g, f / FPS)
        if w is not None and w != prev:
            out.append((f / FPS, w))
        prev = w
    return out


def medidor(im, g, t, gana):
    d = ImageDraw.Draw(im, "RGBA")
    c0, c1 = [tuple(c) for c in g["colores"]]
    xm = (BAR_X0 + BAR_X1) / 2
    d.rounded_rectangle([BAR_X0 - 10, BAR_Y - 50, BAR_X1 + 10, BAR_Y + 50], 48, fill=(10, 10, 16, 230))
    d.rounded_rectangle([BAR_X0, BAR_Y - 38, xm, BAR_Y + 38], 38, fill=c0)
    d.rounded_rectangle([xm, BAR_Y - 38, BAR_X1, BAR_Y + 38], 38, fill=c1)
    d.rectangle([xm - 40, BAR_Y - 38, xm + 40, BAR_Y + 38], fill=c0); d.rectangle([xm, BAR_Y - 38, xm + 40, BAR_Y + 38], fill=c1)
    mitad = (BAR_X1 - BAR_X0) / 2
    zona = mitad - (mitad - 40) * g.get("umbral", UMBRAL) + 22                                  # lo dorado = donde está la pelota cuando gana
    for k, (xa, xb) in enumerate(((BAR_X0, BAR_X0 + zona), (BAR_X1 - zona, BAR_X1))):
        on = gana == k
        d.rounded_rectangle([xa, BAR_Y - 38, xb, BAR_Y + 38], 30, fill=(255, 214, 40) if on else (255, 196, 30, 200),
                            outline=(255, 255, 255), width=6 if on else 3)
    d.line([(xm, BAR_Y - 46), (xm, BAR_Y + 46)], fill=(255, 255, 255), width=6)
    P.texto(d, (xm, BAR_Y - 100), "VS", 84, (255, 255, 255), 10)
    for k, xc in enumerate((BAR_X0 + 150, BAR_X1 - 150)):
        P.texto(d, (xc, BAR_Y - 100), g["nombres"][k].upper(), 66, (255, 230, 40) if gana == k else (255, 255, 255), 9)
    cr = corona().resize((70, int(corona().height * 58 / corona().width)))
    for xc in (BAR_X0 + zona / 2, BAR_X1 - zona / 2):                          # la zona dorada se entiende sin leer
        im.alpha_composite(cr, (int(xc - cr.width / 2), int(BAR_Y - cr.height / 2)))
    d = ImageDraw.Draw(im, "RGBA")
    x = x_de(g, t)
    bx = xm + x * ((BAR_X1 - BAR_X0) / 2 - 40)
    r = 44
    d.ellipse([bx - r + 6, BAR_Y - r + 10, bx + r + 6, BAR_Y + r + 10], fill=(0, 0, 0, 90))
    d.ellipse([bx - r, BAR_Y - r, bx + r, BAR_Y + r], fill=(255, 255, 255), outline=(20, 20, 30), width=5)
    ang = t * 9 * (1 if math.cos(2 * math.pi * t * 2 / g["dur"]) > 0 else -1)
    for j in range(5):                                                         # paneles negros que giran
        a = ang + j * 2 * math.pi / 5
        px, py = bx + r * 0.55 * math.cos(a), BAR_Y + r * 0.55 * math.sin(a)
        d.regular_polygon((px, py, r * 0.22), 5, rotation=math.degrees(a), fill=(20, 20, 30))
    d.regular_polygon((bx, BAR_Y, r * 0.3), 5, rotation=math.degrees(ang), fill=(20, 20, 30))


def cuadro(g, A, t, ent):
    im = A["fondo"].copy()
    gana = ganador(g, t)
    orden = [1, 0] if gana == 0 else [0, 1]                                   # el ganador adelante
    for k in orden:
        t_img, cx = A["tor"][k]
        x = int(A["pos"][k][0] - cx); y = int(A["pos"][k][1] - t_img.height)
        if gana is None:
            im.alpha_composite(t_img, (x, y))
        elif gana == k:
            im.alpha_composite(A["aura"][k], (x, y)); im.alpha_composite(A["brillo"][k], (x, y))
        else:
            im.alpha_composite(A["apagado"][k], (x, y))
    medidor(im, g, t, gana)
    d = ImageDraw.Draw(im)
    if gana is not None:
        t0 = max(te for te, w in ent if w == gana and te <= t + 1e-6) if any(w == gana and te <= t + 1e-6 for te, w in ent) else t
        e = t - t0
        if e < 0.12:
            im.alpha_composite(Image.new("RGBA", (W, H), (255, 220, 60, int(70 * (1 - e / 0.12)))))
            d = ImageDraw.Draw(im)
        cr = corona(); t_img, cx = A["tor"][gana]
        top = A["pos"][gana][1] - t_img.height
        cy = top - cr.height * 0.55 - 120 * max(0.0, 1 - e / 0.15)          # cae sobre la cabeza
        im.alpha_composite(cr, (int(A["pos"][gana][0] - cr.width / 2), int(cy)))
        d = ImageDraw.Draw(im)
        txt = f"{g['nombres'][gana].upper()} WINS!"
        tam = 118 if len(txt) <= 11 else 100
        P.texto(d, (W / 2, 1660), txt, int(tam * min(1, 0.65 + e * 4)), (255, 230, 40), 13)
    im = G.capa(im, t, g["dur"], A["textos"], 120, sin_fin=True) or im
    return im.convert("RGB")


def audio(g, ent, dur):
    sr = M.SR; n = int(dur * sr); fx = np.zeros(n, np.float32)

    def add(t0, sig, v=1.0):
        a = int(t0 * sr) % n; b = min(n, a + len(sig)); fx[a:b] += sig[: b - a] * v
    k = 0.0
    while k < dur:                                                             # latido que acompaña la pelota
        add(k, M.golpe(0.05), 0.25); k += dur / 16
    for te, _ in ent:
        add(te, M.ding(0.6), 0.6); add(te, M.boom(0.5), 0.35)
    add(0, G.silbato(sr), 1.0)
    mu = P.musica(g, dur)
    return np.tanh((mu * 0.75 + fx) * 1.1) * 0.9, np.tanh(fx * 1.1) * 0.85


def main(guion):
    g = json.loads(Path(guion).read_text())
    out = ROOT / "salida" / g["id"]; out.mkdir(parents=True, exist_ok=True)
    A = armar(g); dur = g["dur"]; ent = entradas(g)
    A["textos"] = g.get("textos") or G.elegir("vs", g["id"], "")
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
