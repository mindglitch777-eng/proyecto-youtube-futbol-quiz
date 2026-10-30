#!/usr/bin/env python3
"""
CATCH THE RIGHT HEAD (FOOTBALL_UNIVERSE6, reporte 26): la cara del jugador cortada a la altura de las cejas y 3
"cabezas" (frente + pelo de distintos jugadores) numeradas arriba. Caen de a una: las que no van quedan ridículas,
X roja + "nope" y se caen; la correcta encaja con PERFECT!, destello dorado, emojis y campana. Loop.

Uso: python3 produccion/render_cabeza.py produccion/guiones/cabeza_01.json
"""
import json
import math
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

import caras_find as CF
import motor as M
import render_stop as RS

ROOT = Path(__file__).resolve().parent
W, H, FPS = 1080, 1920, 30
F_TIT = str(ROOT / "assets" / "fuentes" / "ArchivoBlack-Regular.ttf")
S, FX, FY = 760, 160, 700            # cara grande
T_INTENTO, T_FINAL = 2.0, 1.4


def texto(d, xy, s, tam, fill, stroke=10, sc=(20, 20, 30)):
    d.text(xy, s, font=ImageFont.truetype(F_TIT, tam), fill=fill, anchor="mm", stroke_width=stroke, stroke_fill=sc)


def segmentar(img, q, cx, corte, A):
    """Recorta cabeza + cara del fondo con GrabCut, sembrado con los 68 puntos. Devuelve alfa suave (uint8)."""
    h, w = img.shape[:2]
    m = np.full((h, w), cv2.GC_PR_BGD, np.uint8)
    cv2.ellipse(m, (int(cx), int(corte + A * 0.2)), (int(A * 0.62), int(A * 1.0)), 0, 0, 360, cv2.GC_PR_FGD, -1)
    cara = cv2.convexHull(q[:27].astype(np.int32))
    cv2.fillConvexPoly(m, cara, cv2.GC_FGD)
    cv2.rectangle(m, (int(cx - A * 0.25), int(corte - A * 0.35)), (int(cx + A * 0.25), int(corte)), cv2.GC_FGD, -1)   # frente/pelo
    m[:6, :] = cv2.GC_BGD; m[:, :6] = cv2.GC_BGD; m[:, -6:] = cv2.GC_BGD
    m[: max(0, int(corte - A * 0.72)), :] = cv2.GC_BGD                        # el pelo no pasa de ~0,7 caras arriba de las cejas
    m[:, : max(6, int(cx - A * 1.0))] = cv2.GC_BGD; m[:, min(w - 6, int(cx + A * 1.0)):] = cv2.GC_BGD
    bg, fg = np.zeros((1, 65), np.float64), np.zeros((1, 65), np.float64)
    cv2.grabCut(img, m, None, bg, fg, 5, cv2.GC_INIT_WITH_MASK)
    a = np.where((m == cv2.GC_FGD) | (m == cv2.GC_PR_FGD), 255, 0).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(a)                          # quedarse con la mancha de la cara
    if n > 1:
        k = lab[int(q[30, 1]), int(q[30, 0])]
        a = np.where(lab == k, 255, 0).astype(np.uint8)
    return cv2.GaussianBlur(a, (7, 7), 0)


def recorte(foto, ancho_obj=None):
    """Cara en S x S + línea de corte (cejas) + centro x + ancho de cara, normalizada al ancho de cara objetivo."""
    img, p = CF.base(foto, 1.6)
    k = S / CF.LADO
    A = np.linalg.norm(p[16] - p[0]) * k
    big = cv2.resize(img, (S, S), interpolation=cv2.INTER_LANCZOS4)
    corte = min(p[17:27, 1]) * k - A * 0.04
    cx = (p[0, 0] + p[16, 0]) / 2 * k
    alfa = segmentar(big, p * k, cx, corte, A)
    im = Image.fromarray(cv2.cvtColor(big, cv2.COLOR_BGR2RGB)).convert("RGBA"); im.putalpha(Image.fromarray(alfa))
    if ancho_obj:                                                             # escalar para que la frente calce en ancho
        f = ancho_obj / A
        im = im.resize((int(S * f), int(S * f)), Image.LANCZOS); corte *= f; cx *= f; A = ancho_obj
    return im, corte, cx, A


def cabeza(im, corte, cx):
    """Parte de arriba (frente + pelo) recortada con borde suave curvo; ancla = (cx, corte)."""
    c = int(corte)
    top = im.crop((0, 0, im.width, c + 6)).copy()
    bb = top.getbbox()                                                       # recortar lo vacío de arriba y costados
    if bb:
        top = top.crop((bb[0], bb[1], bb[2], top.height)); cx -= bb[0]
    return top, cx


def armar(g):
    base, corte, cx, A = recorte(g["foto"])
    abajo = base.copy(); a = np.asarray(abajo.split()[3]).copy(); a[: int(corte)] = 0; abajo.putalpha(Image.fromarray(a))
    cabezas = []
    for foto in g["opciones"]:
        im, c2, cx2, _ = (base, corte, cx, A) if foto == g["foto"] else recorte(foto, A)
        top, ax = cabeza(im, c2, cx2)
        cabezas.append(dict(img=top, ax=ax, ok=foto == g["foto"]))
    return dict(abajo=abajo, corte=corte, cx=cx, cabezas=cabezas, real=g["opciones"].index(g["foto"]))


def fondo(col):
    im = Image.new("RGB", (W, H), col); d = ImageDraw.Draw(im)
    for j in range(0, H, 90):
        d.rectangle([0, j, W, j + 45], fill=tuple(min(255, v + 18) for v in col))
    return im


def cuadro(g, A, t, dur):
    im = fondo(tuple(g.get("color", (60, 170, 255)))).convert("RGBA"); d = ImageDraw.Draw(im)
    texto(d, (W // 2, 105), "CATCH THE RIGHT HEAD", 74, (255, 230, 40), 12)
    texto(d, (W // 2, 200), g["nombre"].upper(), 92, (255, 255, 255), 12)
    i = min(int(t // T_INTENTO), A["real"]); lt = t - i * T_INTENTO
    # miniaturas 1-2-3
    for j, cz in enumerate(A["cabezas"]):
        mini = cz["img"].copy(); f = min(260 / mini.width, 190 / mini.height)
        mini = mini.resize((max(1, int(mini.width * f)), max(1, int(mini.height * f))), Image.BICUBIC)
        x = 60 + j * 330 + (260 - mini.width) // 2; y = 470 - mini.height
        usado = j < i or (j == i and lt > 0.15)
        if usado:
            mini.putalpha(mini.split()[3].point(lambda v: v // 4))
        im.alpha_composite(mini, (x, max(250, y)))
        texto(d, (60 + j * 330 + 130, 515), str(j + 1), 70, (255, 230, 40) if j == i else (255, 255, 255), 9)
    # la cara de abajo
    im.alpha_composite(A["abajo"], (FX, FY))
    cz = A["cabezas"][i]
    ok = cz["ok"]
    if lt < 0.45:                                                             # cae
        x = lt / 0.45; dy = -900 * (1 - x) ** 2
    elif ok:
        dy = 0.0
    elif lt < 1.3:
        dy = 0.0
    else:                                                                     # la mala se cae
        x = (lt - 1.3) / 0.7; dy = 1400 * x * x
    hx = FX + A["cx"] - cz["ax"]; hy = FY + A["corte"] - cz["img"].height + 6 + dy
    im.alpha_composite(cz["img"], (int(hx), int(hy)))
    d = ImageDraw.Draw(im)
    if lt >= 0.45:
        p = min(1, (lt - 0.45) / 0.3)
        if ok:
            a = int(160 * max(0, 1 - (lt - 0.45) / 0.35))
            im.alpha_composite(Image.new("RGBA", (W, H), (255, 220, 60, a)))
            d = ImageDraw.Draw(im)
            d.rounded_rectangle([FX - 10, FY - 140, FX + S + 10, FY + S + 10], 40, outline=(255, 215, 0), width=14)
            texto(d, (W // 2, FY + S + 120), "PERFECT!", int(120 * (0.6 + 0.4 * p)), (255, 230, 40), 14)
            for j, e in enumerate(["🔥", "😱", "💯"]):
                tam = int(150 * (0.5 + 0.5 * p)); ang = math.radians(-150 + j * 60)
                ex, ey = W / 2 + 380 * p * math.cos(ang), FY + 250 + 300 * p * math.sin(ang)
                im.alpha_composite(RS.emoji(e, tam), (int(ex - tam / 2), int(ey - tam / 2)))
        elif lt < 1.3:
            cxx, cyy, r = W // 2, FY + 330, int(170 * (0.6 + 0.4 * p))
            d.line([(cxx - r, cyy - r), (cxx + r, cyy + r)], fill=(235, 30, 30), width=34)
            d.line([(cxx - r, cyy + r), (cxx + r, cyy - r)], fill=(235, 30, 30), width=34)
            texto(d, (W // 2, FY + S + 120), "NOPE 💀".replace(" 💀", ""), int(110 * (0.6 + 0.4 * p)), (255, 70, 70), 12, (255, 255, 255))
            im.alpha_composite(RS.emoji("💀", 140), (W // 2 + 200, FY + S + 50))
    d = ImageDraw.Draw(im)
    texto(d, (W // 2, 590), "1, 2 OR 3? COMMENT IT", 54, (255, 255, 255), 9)
    return im.convert("RGB")


def audio(A, dur):
    sr = M.SR; n = int(dur * sr)
    musica = RS.musica_67(dur)[:n]; fx = np.zeros(n, np.float32)
    import render_runner as RR
    nope, boom, wow = RR.sfx("nope_0", 0, 0.8, 0.6), RR.sfx("vine_boom_0", 0, 1.0, 0.6), RR.sfx("wow_0", 0, 1.3, 0.55)
    def add(t0, sig, v=1.0):
        a = int(t0 * sr); b = min(n, a + len(sig)); fx[a:b] += sig[: b - a] * v
    for i in range(A["real"] + 1):
        t0 = i * T_INTENTO
        add(t0, M.whoosh(0.4), 0.5)
        if i == A["real"]:
            add(t0 + 0.45, M.ding(0.8), 0.6); add(t0 + 0.45, boom); add(t0 + 0.6, wow)
        else:
            add(t0 + 0.45, M.golpe(0.12), 0.8); add(t0 + 0.5, nope); add(t0 + 1.3, M.whoosh(0.5), 0.4)
    return np.tanh((musica * 0.85 + fx) * 1.1) * 0.9, np.tanh(fx * 1.1) * 0.85


def main(guion):
    g = json.loads(Path(guion).read_text())
    out = ROOT / "salida" / g["id"]; out.mkdir(parents=True, exist_ok=True)
    A = armar(g); dur = A["real"] * T_INTENTO + T_INTENTO
    mudo = out / "mudo.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", str(mudo)], stdin=subprocess.PIPE)
    for f in range(int(round(dur * FPS))):
        p.stdin.write(np.asarray(cuadro(g, A, f / FPS, dur), np.uint8).tobytes())
    p.stdin.close(); p.wait()
    con, solo = audio(A, dur)
    M.mezclar(out, mudo, {"short.mp4": con, "short_solo_efectos.mp4": solo})
    print(out / "short.mp4", dur, "s")


if __name__ == "__main__":
    main(sys.argv[1])
