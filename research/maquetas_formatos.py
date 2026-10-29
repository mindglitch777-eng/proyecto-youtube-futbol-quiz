#!/usr/bin/env python3
"""
Maquetas (un cuadro) de los formatos nuevos del reporte 26, hechas solo con nuestras herramientas
(fotos de Wikimedia + 68 puntos de la cara + dibujo por código), para mostrar que se pueden producir.
Salida: reports/maquetas_26/*.jpg
"""
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "produccion"))
import caras_find as CF  # noqa: E402

OUT = RAIZ / "reports" / "maquetas_26"
F = str(RAIZ / "produccion" / "assets" / "fuentes" / "ArchivoBlack-Regular.ttf")
W, H = 1080, 1920


def f(t):
    return ImageFont.truetype(F, t)


def txt(d, xy, s, t, fill=(255, 255, 255), sw=8, sc=(15, 25, 60)):
    d.text(xy, s, font=f(t), fill=fill, anchor="mm", stroke_width=sw, stroke_fill=sc)


def pil(bgr, lado):
    return Image.fromarray(bgr[..., ::-1]).resize((lado, lado), Image.LANCZOS)


def fondo(c1, c2):
    y = np.linspace(0, 1, H)[:, None, None]
    a = np.array(c1) * (1 - y) + np.array(c2) * y
    return Image.fromarray(np.repeat(a, W, 1).astype(np.uint8))


def stop_challenge():
    """Eddy Kicks: 4 cuadrantes, un 'filtro' de cara que tiembla y se frena; gana el que calza 99 %."""
    im = fondo((20, 20, 30), (40, 10, 60)); d = ImageDraw.Draw(im)
    txt(d, (W // 2, 120), "STOP AT 99%", 110, (255, 220, 40), 12)
    for k, (clave, pct, dx, dy, s) in enumerate([("cristiano_ronaldo_0", "1%", 60, -40, 1.25), ("lionel_messi_4", "49%", -30, 25, 0.9),
                                                ("neymar_1", "69%", 18, 10, 1.08), ("erling_haaland_0", "99%", 2, 1, 1.0)]):
        img, p = CF.base(clave, 1.3)
        lado = 520; x0, y0 = 10 + (k % 2) * 540, 260 + (k // 2) * 560
        im.paste(pil(img, lado), (x0, y0))
        q = p * lado / CF.LADO
        c = q.mean(0)
        q2 = (q - c) * s + c + [dx, dy]
        dd = ImageDraw.Draw(im, "RGBA")
        for a, b in [(0, 17), (17, 22), (22, 27), (36, 42), (42, 48), (48, 60)]:
            pts = [tuple(v + [x0, y0]) for v in q2[a:b]] + ([tuple(q2[a] + [x0, y0])] if b - a > 5 and a >= 36 else [])
            dd.line(pts, fill=(0, 255, 140, 230), width=6)
        col = (61, 214, 110) if pct == "99%" else (255, 80, 60)
        txt(d, (x0 + lado // 2, y0 + lado - 50), pct, 90, col, 10)
    txt(d, (W // 2, 1450), "WHO GETS 99%?", 70)
    return im


def cabeza_correcta():
    """FOOTBALL_UNIVERSE6: cara con la parte de arriba cortada; caen 3 pelos y uno solo encaja."""
    im = fondo((80, 170, 255), (190, 235, 255)); d = ImageDraw.Draw(im)
    txt(d, (W // 2, 120), "CATCH THE RIGHT HEAD", 76, (255, 220, 40), 10)
    img, p = CF.base("erling_haaland_0", 1.3)
    lado = 760; q = p * lado / CF.LADO
    corte = int(min(q[17:27, 1]) - 10)
    cara = pil(img, lado).convert("RGBA")
    m = Image.new("L", (lado, lado), 0); ImageDraw.Draw(m).rectangle([0, corte, lado, lado], fill=255)
    cara.putalpha(m)
    im.paste(cara, ((W - lado) // 2, 760), cara)
    for k, clave in enumerate(["neymar_1", "lionel_messi_4", "erling_haaland_0"]):
        im2, p2 = CF.base(clave, 1.3)
        q2 = p2 * 300 / CF.LADO; c2 = int(min(q2[17:27, 1]) - 4)
        pelo = pil(im2, 300).crop((0, 0, 300, c2))
        x = 60 + k * 340
        im.paste(pelo, (x, 330))
        txt(d, (x + 150, 330 + c2 + 50), str(k + 1), 70)
    txt(d, (W // 2, 1600), "1, 2 OR 3?", 80)
    return im


def cual_look():
    """TrendPick / Yuzix / Muzam: foto del jugador al centro, lista 1-4 a la izquierda, cada look cae al beat."""
    im = fondo((255, 214, 40), (255, 160, 20)); d = ImageDraw.Draw(im)
    txt(d, (W // 2, 120), "WHICH LOOK IS BEST?", 80, (255, 255, 255), 10)
    img, p = CF.base("neymar_1", 1.5)
    P = CF.partes(p)
    img = CF.efecto(img, p, "anteojos", 1.0)
    lado = 820; x0, y0 = 220, 420
    im.paste(pil(img, lado), (x0, y0))
    k = lado / CF.LADO
    cx, top = x0 + P["centro"][0] * k, y0 + min(p[17:27, 1]) * k - 150
    d.polygon([(cx - 180, top + 120), (cx - 140, top), (cx - 60, top + 80), (cx, top - 20), (cx + 60, top + 80), (cx + 140, top), (cx + 180, top + 120)],
              fill=(255, 205, 0), outline=(140, 90, 0))
    for i, s in enumerate(["CROWN", "SHADES", "CAP", "WIG"]):
        y = 520 + i * 200
        d.rounded_rectangle([20, y - 70, 190, y + 70], 24, fill=(255, 255, 255), outline=(15, 25, 60), width=6)
        txt(d, (105, y), str(i + 1), 80, (15, 25, 60), 0)
    txt(d, (W // 2, 1460), "COMMENT 1, 2, 3 OR 4", 64)
    return im


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for nombre, fn in [("stop_99", stop_challenge), ("cabeza_correcta", cabeza_correcta), ("cual_look", cual_look)]:
        fn().convert("RGB").save(OUT / f"{nombre}.jpg", quality=86)
        print(OUT / f"{nombre}.jpg")


if __name__ == "__main__":
    main()
