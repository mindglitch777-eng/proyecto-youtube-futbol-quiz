#!/usr/bin/env python3
"""
SKILL STOP · NUTMEG (19/11 · pedido del CEO: duelo de habilidad entre dos estrellas, parar justo en el caño).
Un DEFENSOR superestrella de cuerpo entero, grande, con las piernas abiertas. La pelota corre por el piso a toda velocidad
POR DETRÁS de sus piernas (solo se ve por el hueco entre los pies y a los costados) y va y viene. Arriba, la cara del ATACANTE
(otra superestrella o leyenda). Pausá justo cuando la pelota está en el hueco: "RONALDO NUTMEGS MESSI!", el defensor se
apaga y se tambalea. Vuelta propia: cuando la pelota entra al hueco el tiempo se frena (cámara lenta de 3x) y vuelve a
acelerar; el cartel se ve SOLO mientras la pelota está de verdad entre los pies (honesto).
Solo superestrellas y leyendas, sin descargar videos: recortes reales (assets/recortes/cuerpos, sin descartados).

Uso: python3 produccion/render_cano.py guion.json
guion: {"id", "defensor": "kylian_mbapp_12", "nombre_def": "Mbappé", "atacante": "cristiano_ronaldo", "nombre_atq": "Ronaldo",
        "dur": 7.5, "pasadas": 4, "lento": 4.0, "musica", "fondo"}
"""
import json
import math
import subprocess
import sys
from functools import lru_cache
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance

import gancho as G
import motor as M
import render_plinko as P
import render_rueda as R

ROOT = Path(__file__).resolve().parent
W, H, FPS = 1080, 1920, 30
PISO = 1840                         # dónde apoyan los pies
ALTO_DEF = 1480                     # el defensor llena la pantalla (cara grande en el cuadro 0)


def hueco(a, y):
    """Hueco transparente más ancho entre dos partes opacas en la fila y → (ancho, centro_x)."""
    fila = a[int(y)]; xs = np.where(fila)[0]
    if len(xs) < 2:
        return 0, 0
    mejor, cx, cur = 0, 0, 0
    for i in range(xs[0], xs[-1] + 1):
        cur = 0 if fila[i] else cur + 1
        if cur > mejor:
            mejor, cx = cur, i - cur // 2
    return mejor, cx


@lru_cache(maxsize=8)
def defensor(clave):
    im = Image.open(R.REC / "cuerpos" / f"{clave}.png").convert("RGBA")
    al = np.asarray(im.split()[3])                                             # solo el jugador: se va la pelota suelta del recorte
    n, lab, st, _ = cv2.connectedComponentsWithStats((al > 60).astype(np.uint8))
    if n > 2:
        k = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
        im.putalpha(Image.fromarray(np.where(lab == k, al, 0).astype(np.uint8)))
    if clave == "cristiano_ronaldo_10":                                       # mancha rosa del short (viene de la foto) → blanco
        arr = np.asarray(im).copy(); rr, gg, bb = (arr[..., i].astype(int) for i in range(3))
        rosa = (rr > 150) & (bb > 90) & (gg < rr * 0.62) & (bb > rr * 0.45)
        arr[rosa, :3] = (236, 236, 240); im = Image.fromarray(arr)
    im = im.crop(im.getbbox())
    s = ALTO_DEF / im.height
    im = im.resize((int(im.width * s), ALTO_DEF), Image.LANCZOS)
    a = np.asarray(im.split()[3]) > 100
    for r in range(124, 63, -2):                                               # 19/11 (#15): pelota GRANDE (mín. 64), la mayor que entra en el hueco
        ancho, cx = hueco(a, ALTO_DEF - 1 - r - 4)                             # (medido a la altura del centro de la pelota)
        arriba, _ = hueco(a, ALTO_DEF - 1 - 2 * r - 4)
        if min(ancho, arriba) / 2 * 0.9 >= r:
            return im, r, ancho, cx
    raise ValueError(f"{clave}: sin hueco entre las piernas")


@lru_cache(maxsize=8)
def brillo(r):
    from PIL import ImageFilter
    lado = int(r * 4.4); c = lado / 2
    im = Image.new("RGBA", (lado, lado), (255, 220, 40, 0))
    ImageDraw.Draw(im).ellipse([c - r * 1.65, c - r * 1.65, c + r * 1.65, c + r * 1.65], fill=(255, 220, 40, 190))
    return im.filter(ImageFilter.GaussianBlur(r * 0.35))


def armar(g):
    im, r, ancho, cx = defensor(g["defensor"])
    x0 = int(W / 2 - cx) + g.get("corrido", 0)                                # el hueco queda en el medio de la pantalla
    x0 = max(-im.width // 3, min(W - im.width * 2 // 3, x0))
    gx = x0 + cx
    gris = ImageEnhance.Brightness(ImageEnhance.Color(im).enhance(0.1)).enhance(0.55)
    cara = P.con_aro(P.cara(g["atacante"], 300), (255, 214, 40), 12)
    return dict(fondo=R.fondo(g.get("fondo", "estadio_0")).copy(), defe=im, gris=gris, x0=x0, y0=PISO - im.height, r=r,
                gx=gx, tol=tol(ancho, r), cara=cara, tabla=recorrido(g, gx, tol(ancho, r), r))


def tol(ancho, r):
    """Caño = la pelota con el centro dentro del hueco y a lo sumo media pelota tapada por una pierna."""
    return min(max(ancho / 2 - r * 0.5, r * 0.6), r * 0.75, 40)              # tope: zona chica también con pelota grande


def recorrido(g, gx, tol, r):
    """x de la pelota en cada cuadro: va y viene de borde a borde; dentro del hueco va `lento` veces más despacio.
    La velocidad base se ajusta para que entren `pasadas` cruces enteros en `dur` (loop perfecto)."""
    xa, xb = -r - 20, W + r + 20
    lento = g.get("lento", 4.0); zona = tol + r * 1.2

    def t_cruce(v):                                                            # tiempo de un cruce entero a velocidad v
        dentro = 2 * zona; fuera = (xb - xa) - dentro
        return fuera / v + dentro * lento / v
    T = g["dur"] / g.get("pasadas", 4)
    v = t_cruce(1.0) / T
    xs = []
    for f in range(int(round(g["dur"] * FPS))):
        t = (f / FPS + g.get("t0", 0.0)) % g["dur"]
        k = int(t // T); u = t - k * T                                         # tiempo dentro de este cruce
        a1 = (gx - zona - xa) / v; a2 = a1 + 2 * zona * lento / v
        if u < a1:
            x = xa + v * u
        elif u < a2:
            x = gx - zona + (u - a1) * v / lento
        else:
            x = gx + zona + (u - a2) * v
        xs.append(x if k % 2 == 0 else xa + xb - x)                           # los cruces impares vuelven
    return xs


def cuadro(g, A, f):
    t = f / FPS
    im = A["fondo"].copy()
    x = A["tabla"][f]; r = A["r"]
    cano = abs(x - A["gx"]) <= A["tol"]
    y = PISO - r - 4
    d = ImageDraw.Draw(im, "RGBA")
    d.ellipse([x - r * 1.1, PISO - 10, x + r * 1.1, PISO + 6], fill=(0, 0, 0, 90))  # sombra
    prev = A["tabla"][f - 1] if f else A["tabla"][-1]
    for k in (5, 4, 3, 2, 1):                                                  # estela dorada larga (se sigue en el celular)
        xx = x + (prev - x) * k * 0.8
        rk = r * (0.55 + 0.08 * (5 - k))
        d.ellipse([xx - rk, y - rk, xx + rk, y + rk], fill=(255, 214, 40, 35 + 22 * (5 - k)))
    br = brillo(r); pulso = 0.75 + 0.25 * math.sin(t * 2 * math.pi * 3)      # aro de luz que late alrededor de la pelota
    im.alpha_composite(Image.eval(br, lambda v: int(v * pulso)) if pulso < 1 else br, (int(x - br.width / 2), int(y - br.height / 2)))
    d = ImageDraw.Draw(im, "RGBA")
    d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 255), outline=(20, 20, 30), width=4)
    ang = x / r
    for j in range(5):
        a = ang + j * 2 * math.pi / 5
        d.regular_polygon((x + r * 0.55 * math.cos(a), y + r * 0.55 * math.sin(a), r * 0.22), 5, rotation=math.degrees(a), fill=(20, 20, 30))
    d.regular_polygon((x, y, r * 0.3), 5, rotation=math.degrees(ang), fill=(20, 20, 30))
    if cano:                                                                   # el defensor queda pagando
        sx = int(8 * math.sin(t * 60))
        im.alpha_composite(A["gris"], (A["x0"] + sx, A["y0"]))
    else:
        im.alpha_composite(A["defe"], (A["x0"], A["y0"]))                     # la pelota pasa por DETRÁS de las piernas
    d = ImageDraw.Draw(im)
    cara = A["cara"]
    im.alpha_composite(cara, (24, 270))
    nom = g["nombre_atq"].upper(); xc = max(24 + cara.width / 2, P.fuente(60).getlength(nom) / 2 + 24)   # que no se corte
    P.texto(d, (xc, 270 + cara.height + 40), nom, 60, (255, 230, 40), 9)
    P.texto(d, (W / 2, 1870), g["nombre_def"].upper(), 60, (255, 255, 255), 9, (20, 20, 30))
    if cano:
        im.alpha_composite(Image.new("RGBA", (W, H), (60, 230, 90, 22)))
        d = ImageDraw.Draw(im)
        txt = f"{g['nombre_atq'].upper()} NUTMEGS {g['nombre_def'].upper()}!"
        tam = 96
        while tam > 50 and P.fuente(tam).getlength(txt) > W - 60:
            tam -= 4
        P.texto(d, (W / 2, 1060), "NUTMEG!", 150, (255, 255, 255), 14, (230, 30, 30))
        P.texto(d, (W / 2, 1190), txt, tam, (255, 230, 40), 12)
    im = G.capa(im, t, g["dur"], A["textos"], 120, sin_fin=True) or im
    return im.convert("RGB"), cano


def audio(g, A, canos, dur):
    sr = M.SR; n = int(dur * sr); fx = np.zeros(n, np.float32)

    def add(t0, sig, v=1.0):
        a = int(t0 * sr) % n; b = min(n, a + len(sig)); fx[a:b] += sig[: b - a] * v
    T = dur / g.get("pasadas", 4)
    for k in range(g.get("pasadas", 4)):
        add(k * T + 0.05, M.whoosh(0.5), 0.5)
    prev = False
    for f, c in enumerate(canos):
        if c and not prev:
            add(f / FPS, M.ding(0.6), 0.6); add(f / FPS, M.boom(0.5), 0.35)
        prev = c
    add(0, G.silbato(sr), 1.0)
    mu = P.musica(g, dur)
    return np.tanh((mu * 0.75 + fx) * 1.1) * 0.9, np.tanh(fx * 1.1) * 0.85


def main(guion):
    g = json.loads(Path(guion).read_text())
    out = ROOT / "salida" / g["id"]; out.mkdir(parents=True, exist_ok=True)
    A = armar(g); dur = g["dur"]
    A["textos"] = g.get("textos") or G.elegir("cano", g["id"], g.get("nombre_def", ""))
    mudo = out / "mudo.mp4"; canos = []
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", str(mudo)], stdin=subprocess.PIPE)
    for f in range(int(round(dur * FPS))):
        im, c = cuadro(g, A, f); canos.append(c)
        p.stdin.write(np.asarray(im, np.uint8).tobytes())
    p.stdin.close(); p.wait()
    con, solo = audio(g, A, canos, dur)
    M.mezclar(out, mudo, {"short.mp4": con, "short_solo_efectos.mp4": solo})
    print(out / "short.mp4", dur, "s", "caños en", [round(f / FPS, 2) for f, c in enumerate(canos) if c and (f == 0 or not canos[f - 1])])


if __name__ == "__main__":
    main(sys.argv[1])
