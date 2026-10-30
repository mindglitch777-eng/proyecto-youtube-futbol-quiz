#!/usr/bin/env python3
"""
¿CUÁL LOOK? 1-4 (TrendPick / Yuzix / Muzam, reporte 26): la cara grande del jugador y, al ritmo, le caen 4 looks
(corona, anteojos "deal with it", peluca de payaso, cuernos...). Lista 1-4 a la izquierda y "COMMENT 1, 2, 3 OR 4".

Dopamina: cada look cae con rebote + golpe + destello, el fondo cambia de color con rayos girando, el número salta,
reacción con emoji, nombre del look. Loop: 4 looks x 2 s = 8 s; al terminar vuelve a caer el 1.
Música: beat 6 7 (render_stop.musica_67).

Uso: python3 produccion/render_look.py produccion/guiones/look_01.json
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
S, FX, FY = 800, 175, 420            # tamaño y posición de la cara
T_LOOK = 2.0
FONDOS = [(255, 196, 0), (0, 190, 255), (255, 70, 140), (120, 220, 60), (160, 90, 255), (255, 120, 30)]
REACCION = {"corona": "👑", "anteojos": "😎", "payaso": "🤡", "cowboy": "🤠", "cuernos": "😈", "aureola": "😇",
            "cadena": "🤑", "cabezon": "😂", "alien": "👽", "bigote": "🧐"}
NOMBRE = {"corona": "KING", "anteojos": "DEAL WITH IT", "payaso": "CLOWN", "cowboy": "COWBOY", "cuernos": "DEVIL",
          "aureola": "ANGEL", "cadena": "DRIP", "cabezon": "BIG HEAD", "alien": "ALIEN", "bigote": "GENTLEMAN"}


def texto(d, xy, s, tam, fill, stroke=10, sc=(20, 20, 30)):
    d.text(xy, s, font=ImageFont.truetype(F_TIT, tam), fill=fill, anchor="mm", stroke_width=stroke, stroke_fill=sc)


def caer(lt):
    """Desplazamiento vertical (px) del accesorio: cae desde arriba con rebote en 0,35 s."""
    if lt >= 0.35:
        return 0.0
    x = lt / 0.35
    return -700 * (1 - x) ** 2 + 60 * math.sin(x * math.pi) * (1 - x)


def accesorio(nombre, P, p, k):
    """Capa RGBA (S x S) con el accesorio dibujado, en coordenadas de la cara mostrada (k = S / LADO)."""
    capa = Image.new("RGBA", (S, S), (0, 0, 0, 0)); d = ImageDraw.Draw(capa)
    A = P["ancho"] * k
    oi, od, boca, nariz = P["oi"] * k, P["od"] * k, P["boca"] * k, P["nariz"] * k
    cx = (p[0, 0] + p[16, 0]) / 2 * k
    cejas = min(p[17:27, 1]) * k
    top = cejas - A * 0.55
    if nombre == "corona":
        w = A * 0.95
        pts = [(cx - w / 2, top + A * 0.05), (cx - w / 2, top - A * 0.35), (cx - w / 4, top - A * 0.12), (cx, top - A * 0.45),
               (cx + w / 4, top - A * 0.12), (cx + w / 2, top - A * 0.35), (cx + w / 2, top + A * 0.05)]
        d.polygon(pts, fill=(255, 205, 20), outline=(150, 95, 0), width=8)
        for j, col in enumerate([(230, 30, 60), (40, 120, 255), (230, 30, 60)]):
            jx = cx - w / 3 + j * w / 3
            d.ellipse([jx - 18, top - A * 0.08 - 18, jx + 18, top - A * 0.08 + 18], fill=col, outline=(255, 255, 255), width=4)
    elif nombre == "anteojos":                                               # "deal with it" pixelados
        y = (oi[1] + od[1]) / 2; px = max(8, int(A / 26))
        x0 = oi[0] - A * 0.22
        for fila, (desde, hasta) in enumerate([(0, 22), (0, 22), (1, 9), (13, 21), (2, 8), (14, 20)]):
            for c in range(desde, hasta):
                d.rectangle([x0 + c * px, y - 2 * px + fila * px, x0 + (c + 1) * px, y - px + fila * px], fill=(10, 10, 10))
        for c in (2, 3, 14, 15):
            d.rectangle([x0 + c * px, y - px, x0 + (c + 1) * px, y], fill=(255, 255, 255))
    elif nombre == "payaso":
        r = A * 0.11
        d.ellipse([nariz[0] - r, nariz[1] - r * 0.8, nariz[0] + r, nariz[1] + r * 1.2], fill=(235, 25, 35), outline=(140, 0, 0), width=4)
        colores = [(255, 60, 60), (255, 170, 0), (255, 235, 0), (60, 200, 80), (40, 140, 255), (170, 80, 255)]
        for j in range(26):
            a = math.pi * (0.95 + 1.1 * j / 25)
            rr = A * 0.68 + (j % 3) * A * 0.05
            bx, by = cx + rr * math.cos(a) * 1.05, cejas + rr * math.sin(a) * 0.75
            br = A * 0.17
            d.ellipse([bx - br, by - br, bx + br, by + br], fill=colores[j % len(colores)])
    elif nombre == "cowboy":
        w = A * 1.7
        d.ellipse([cx - w / 2, top + A * 0.02, cx + w / 2, top + A * 0.3], fill=(130, 80, 35), outline=(70, 40, 10), width=6)
        d.rounded_rectangle([cx - A * 0.42, top - A * 0.42, cx + A * 0.42, top + A * 0.18], int(A * 0.15), fill=(150, 95, 45), outline=(70, 40, 10), width=6)
        d.rectangle([cx - A * 0.42, top + A * 0.02, cx + A * 0.42, top + A * 0.12], fill=(40, 25, 10))
    elif nombre == "cuernos":
        for sgn in (-1, 1):
            bx = cx + sgn * A * 0.32
            d.polygon([(bx - A * 0.12, top + A * 0.12), (bx + A * 0.12, top + A * 0.12), (bx + sgn * A * 0.18, top - A * 0.42)],
                      fill=(225, 25, 25), outline=(110, 0, 0))
    elif nombre == "aureola":
        d.ellipse([cx - A * 0.45, top - A * 0.42, cx + A * 0.45, top - A * 0.18], outline=(255, 215, 0), width=int(A * 0.07))
    elif nombre == "cadena":
        y = p[8, 1] * k + A * 0.25
        for j in range(15):
            a = math.pi * (0.15 + 0.7 * j / 14)
            bx, by = cx + A * 0.62 * math.cos(a), y - A * 0.18 + A * 0.32 * math.sin(a)
            d.ellipse([bx - A * 0.06, by - A * 0.045, bx + A * 0.06, by + A * 0.045], outline=(255, 205, 20), width=int(A * 0.035))
        d.rounded_rectangle([cx - A * 0.14, y + A * 0.1, cx + A * 0.14, y + A * 0.36], 12, fill=(255, 205, 20), outline=(150, 95, 0), width=5)
        texto(d, (cx, y + A * 0.23), "$", int(A * 0.2), (150, 95, 0), 0)
    elif nombre == "bigote":
        for sgn in (-1, 1):
            d.ellipse([boca[0] + sgn * A * 0.18 - A * 0.17, (boca[1] + nariz[1]) / 2 - A * 0.06,
                       boca[0] + sgn * A * 0.18 + A * 0.17, (boca[1] + nariz[1]) / 2 + A * 0.07], fill=(25, 20, 20))
        d.ellipse([od[0] - A * 0.13, od[1] - A * 0.13, od[0] + A * 0.13, od[1] + A * 0.13], outline=(200, 170, 40), width=8)
        d.line([(od[0] + A * 0.13, od[1]), (od[0] + A * 0.2, od[1] + A * 0.5)], fill=(200, 170, 40), width=4)
    return capa


def caras(g):
    img, p = CF.base(g["foto"], g.get("zoom", 1.7))
    P = CF.partes(p); k = S / CF.LADO
    looks = []
    for nom in g["looks"]:
        base = img
        if nom == "cabezon":
            base = CF.lupa(img, P["centro"], P["ancho"] * 1.25, 0.8)              # cabeza gigante
            base = CF.lupa(base, P["ojos"], P["ancho"] * 0.45, 0.35)
        elif nom == "alien":
            base = CF.efecto(CF.efecto(img, p, "ojos_gigantes", 1.0), p, "verde", 1.0)
        cara = Image.fromarray(cv2.cvtColor(base, cv2.COLOR_BGR2RGB)).resize((S, S), Image.LANCZOS).convert("RGBA")
        looks.append(dict(nombre=nom, cara=cara, acc=None if nom in ("cabezon", "alien") else accesorio(nom, P, p, k)))
    return looks


def rayos(col, ang):
    im = Image.new("RGB", (W, H), col); d = ImageDraw.Draw(im)
    claro = tuple(min(255, int(v * 1.18 + 25)) for v in col)
    cx, cy, R = W / 2, FY + S / 2, 2400
    for j in range(16):
        a0 = math.radians(ang + j * 22.5); a1 = a0 + math.radians(11)
        d.polygon([(cx, cy), (cx + R * math.cos(a0), cy + R * math.sin(a0)), (cx + R * math.cos(a1), cy + R * math.sin(a1))], fill=claro)
    return im


def cuadro(g, looks, t, dur):
    i = int(t // T_LOOK) % len(looks); lt = t - i * T_LOOK
    L = looks[i]
    im = rayos(FONDOS[(g.get("color0", 0) + i) % len(FONDOS)], 360 * t / 8.0).convert("RGBA")
    d = ImageDraw.Draw(im)
    texto(d, (W // 2, 120), g["titulo_pantalla"], 84 if len(g["titulo_pantalla"]) < 16 else 64, (255, 255, 255), 12)
    texto(d, (W // 2, 235), g["nombre"].upper(), 110, (255, 230, 40), 14)
    golpe = 1 + 0.06 * math.exp(-max(0, lt - 0.33) * 12) if lt >= 0.33 else 1.0   # la cara "recibe" el golpe
    lado = int(S * golpe)
    cara = L["cara"].resize((lado, lado), Image.BICUBIC) if lado != S else L["cara"]
    m = Image.new("L", (lado, lado), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, lado - 1, lado - 1], 40, fill=255)
    x0, y0 = FX + (S - lado) // 2, FY + (S - lado) // 2
    d.rounded_rectangle([x0 - 12, y0 - 12, x0 + lado + 11, y0 + lado + 11], 48, fill=(255, 255, 255))
    im.paste(cara, (x0, y0), m)
    if L["acc"] is not None:
        im.alpha_composite(L["acc"], (FX, FY + int(caer(lt))))
    elif lt < 0.35:                                                           # looks de deformación: entran con destello
        pass
    if 0.33 <= lt < 0.6:                                                      # destello del impacto
        a = int(170 * (1 - (lt - 0.33) / 0.27))
        im.alpha_composite(Image.new("RGBA", (W, H), (255, 255, 255, a)))
    d = ImageDraw.Draw(im)
    for j in range(len(looks)):                                               # lista 1-4
        y = FY + 70 + j * 190
        activo = j == i
        z = 1.0 + (0.35 * math.exp(-max(0, lt - 0.33) * 6) if activo and lt >= 0.33 else 0) + (0.12 if activo else 0)
        w = int(64 * z)
        d.rounded_rectangle([90 - w, y - w, 90 + w, y + w], int(22 * z), fill=(255, 230, 40) if activo else (255, 255, 255), outline=(20, 20, 30), width=7)
        texto(d, (90, y), str(j + 1), int(70 * z), (20, 20, 30), 0)
    if lt >= 0.33:                                                            # emoji de reacción + nombre del look
        p = min(1, (lt - 0.33) / 0.25)
        tam = int(150 * (0.5 + 0.5 * p) * (1 + 0.08 * math.sin(lt * 9)))
        em = RS.emoji(REACCION[L["nombre"]], tam)
        im.alpha_composite(em, (FX + S - tam // 2 - 40, FY - tam // 2 + 40))
        texto(d, (W // 2 + 40, FY + S + 75), f"{i + 1}. {NOMBRE[L['nombre']]}", int(78 * (0.7 + 0.3 * p)), (255, 255, 255), 11)
    texto(d, (W // 2, FY + S + 185), "COMMENT 1, 2, 3 OR 4", 58, (255, 230, 40), 10)
    return im.convert("RGB")


def audio(looks, dur):
    sr = M.SR; n = int(dur * sr)
    musica = RS.musica_67(dur)[:n]
    fx = np.zeros(n, np.float32)
    import render_runner as RR
    boom = RR.sfx("vine_boom_0", 0, 1.0, 0.55)
    for i in range(len(looks)):
        for sig, t0, v in ((M.whoosh(0.35), i * T_LOOK, 0.5), (boom, i * T_LOOK + 0.33, 1.0), (M.ding(0.6), i * T_LOOK + 0.35, 0.3)):
            a = int(t0 * sr); b = min(n, a + len(sig)); fx[a:b] += sig[: b - a] * v
    return np.tanh((musica * 0.85 + fx) * 1.1) * 0.9, np.tanh(fx * 1.1) * 0.85


def main(guion):
    g = json.loads(Path(guion).read_text())
    out = ROOT / "salida" / g["id"]; out.mkdir(parents=True, exist_ok=True)
    looks = caras(g); dur = T_LOOK * len(looks)
    mudo = out / "mudo.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", str(mudo)], stdin=subprocess.PIPE)
    for f in range(int(round(dur * FPS))):
        p.stdin.write(np.asarray(cuadro(g, looks, f / FPS, dur), np.uint8).tobytes())
    p.stdin.close(); p.wait()
    con, solo = audio(looks, dur)
    M.mezclar(out, mudo, {"short.mp4": con, "short_solo_efectos.mp4": solo})
    print(out / "short.mp4", dur, "s")


if __name__ == "__main__":
    main(sys.argv[1])
