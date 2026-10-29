#!/usr/bin/env python3
"""
Caras graciosas para FIND v2: a partir de UNA foto real arma variantes deformadas con los 68 puntos de la cara
(ojos gigantes, bocota, lengua afuera, cachetes, cara de otro color, bigote, espejo...), como los FIND virales.

Uso de prueba: python3 produccion/caras_find.py lamine_yamal_0 salida.jpg
"""
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent
MOD = ROOT / "assets" / "modelos"
LADO = 512

_det = cv2.FaceDetectorYN.create(str(MOD / "face_detection_yunet_2023mar.onnx"), "", (320, 320), 0.6)
_lbf = cv2.face.createFacemarkLBF()
_lbf.loadModel(str(MOD / "lbfmodel.yaml"))


def base(clave, zoom=1.45):
    """Recorte cuadrado LADOxLADO centrado en la cara + sus 68 puntos (en coordenadas del recorte)."""
    im = cv2.imread(str(ROOT / "assets" / "fotos" / f"{clave}.jpg"))
    h, w = im.shape[:2]
    _det.setInputSize((w, h))
    _, f = _det.detect(im)
    x, y, fw, fh = max(f, key=lambda c: c[2] * c[3])[:4]
    s = max(fw, fh) * zoom
    cx, cy = x + fw / 2, y + fh * 0.47
    pad = int(s)
    im2 = cv2.copyMakeBorder(im, pad, pad, pad, pad, cv2.BORDER_REFLECT)
    x0, y0 = int(cx - s / 2) + pad, int(cy - s / 2) + pad
    crop = cv2.resize(im2[y0:y0 + int(s), x0:x0 + int(s)], (LADO, LADO), interpolation=cv2.INTER_AREA)
    k = LADO / s
    rect = np.array([[(x - cx + s / 2) * k, (y - cy + s / 2) * k, fw * k, fh * k]], np.int32)
    ok, pts = _lbf.fit(crop, rect)
    return crop, pts[0][0].astype(np.float32)


# ------------------------------------------------------------------ deformaciones geométricas
def _remap(img, mx, my):
    return cv2.remap(img, mx.astype(np.float32), my.astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


def lupa(img, c, r, k):
    """k>0 agranda lo que está dentro del radio r alrededor de c; k<0 lo achica."""
    yy, xx = np.indices(img.shape[:2], dtype=np.float32)
    dx, dy = xx - c[0], yy - c[1]
    d = np.sqrt(dx * dx + dy * dy) / r
    f = np.where(d < 1, 1 - k * (1 - d) ** 2, 1.0)
    return _remap(img, c[0] + dx * f, c[1] + dy * f)


def estirar(img, c, r, sx, sy):
    """Estira (sx, sy > 1) o encoge una zona elíptica suave alrededor de c."""
    yy, xx = np.indices(img.shape[:2], dtype=np.float32)
    dx, dy = xx - c[0], yy - c[1]
    d = np.sqrt((dx / r[0]) ** 2 + (dy / r[1]) ** 2)
    a = np.clip(1 - d, 0, 1) ** 1.5
    return _remap(img, c[0] + dx / (1 + (sx - 1) * a), c[1] + dy / (1 + (sy - 1) * a))


def remolino(img, c, r, ang):
    yy, xx = np.indices(img.shape[:2], dtype=np.float32)
    dx, dy = xx - c[0], yy - c[1]
    d = np.sqrt(dx * dx + dy * dy) / r
    t = np.where(d < 1, ang * (1 - d) ** 2, 0)
    co, si = np.cos(t), np.sin(t)
    return _remap(img, c[0] + dx * co - dy * si, c[1] + dx * si + dy * co)


# ------------------------------------------------------------------ partes de la cara
def partes(p):
    ojo_i, ojo_d = p[36:42].mean(0), p[42:48].mean(0)
    boca, nariz = p[48:68].mean(0), p[30]
    ancho = np.linalg.norm(p[16] - p[0])
    centro = p[[0, 16, 8, 27]].mean(0)
    return dict(oi=ojo_i, od=ojo_d, boca=boca, nariz=nariz, ancho=ancho, centro=centro, ojos=(ojo_i + ojo_d) / 2)


def mascara_cara(img, p, crecer=1.0):
    m = np.zeros(img.shape[:2], np.uint8)
    contorno = np.vstack([p[0:17], p[26:16:-1] - [0, (p[8, 1] - p[27, 1]) * 0.35]])
    c = contorno.mean(0)
    cv2.fillPoly(m, [((contorno - c) * crecer + c).astype(np.int32)], 255)
    return cv2.GaussianBlur(m, (31, 31), 0).astype(np.float32)[..., None] / 255


def teñir(img, p, color, fuerza):
    m = mascara_cara(img, p, 1.08) * fuerza
    gris = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32)[..., None] / 255
    tinte = np.array(color, np.float32)[None, None] * (0.35 + 0.9 * gris)
    return np.clip(img * (1 - m) + tinte * m, 0, 255).astype(np.uint8)


def lengua(img, P, tam):
    im = img.copy()
    b = P["boca"]; w = P["ancho"] * 0.17 * tam
    cv2.ellipse(im, (int(b[0]), int(b[1] + w * 0.15)), (int(w * 1.05), int(w * 0.45)), 0, 0, 360, (35, 20, 60), -1, cv2.LINE_AA)
    capa = im.copy()
    cv2.ellipse(capa, (int(b[0]), int(b[1] + w * 0.95)), (int(w * 0.75), int(w * 1.0)), 0, 0, 360, (120, 105, 235), -1, cv2.LINE_AA)
    cv2.line(capa, (int(b[0]), int(b[1] + w * 0.35)), (int(b[0]), int(b[1] + w * 1.5)), (90, 70, 190), 3, cv2.LINE_AA)
    return cv2.addWeighted(capa, 0.95, im, 0.05, 0)


def bigote(img, P, tam):
    im = img.copy()
    b, n = P["boca"], P["nariz"]; w = P["ancho"] * 0.2 * tam
    y = int((b[1] * 0.55 + n[1] * 0.45))
    for s in (-1, 1):
        cv2.ellipse(im, (int(b[0] + s * w * 0.55), y), (int(w * 0.62), int(w * 0.22)), s * 12, 0, 360, (25, 25, 30), -1, cv2.LINE_AA)
    return im


def anteojos(img, P, tam):
    im = img.copy(); r = int(P["ancho"] * 0.13 * tam)
    for o in (P["oi"], P["od"]):
        cv2.circle(im, (int(o[0]), int(o[1])), r, (20, 20, 20), max(4, r // 5), cv2.LINE_AA)
    cv2.line(im, (int(P["oi"][0] + r), int(P["oi"][1])), (int(P["od"][0] - r), int(P["od"][1])), (20, 20, 20), max(4, r // 6), cv2.LINE_AA)
    return im


# ------------------------------------------------------------------ catálogo
def efecto(img, p, nombre, f):
    """f = intensidad 0..1 (1 = exagerado, 0.25 = casi igual)."""
    P = partes(p); A = P["ancho"]
    if nombre == "ojos_gigantes":
        for o in (P["oi"], P["od"]):
            img = lupa(img, o, A * 0.27, 0.9 * f)
        return img
    if nombre == "ojos_chiquitos":
        for o in (P["oi"], P["od"]):
            img = lupa(img, o, A * 0.2, -1.6 * f)
        return img
    if nombre == "un_ojo_gigante":
        return lupa(img, P["od"], A * 0.32, 0.92 * f)
    if nombre == "bocota":
        return lupa(img, P["boca"], A * 0.4, 0.88 * f)
    if nombre == "boca_mini":
        return lupa(img, P["boca"], A * 0.3, -2.0 * f)
    if nombre == "narizota":
        return lupa(img, P["nariz"], A * 0.3, 0.9 * f)
    if nombre == "cachetes":
        return estirar(img, (P["boca"] + P["nariz"]) / 2, (A * 0.8, A * 0.6), 1 + 0.9 * f, 1.0)
    if nombre == "cara_larga":
        return estirar(img, P["centro"], (A * 0.65, A * 0.9), 1.0, 1 + 0.6 * f)
    if nombre == "cara_aplastada":
        return estirar(img, P["centro"], (A * 0.7, A * 0.75), 1 + 0.25 * f, 1 - 0.3 * f)
    if nombre == "cabeza_chica":
        return lupa(img, P["centro"], A * 0.95, -1.3 * f)
    if nombre == "remolino":
        return remolino(img, P["centro"], A * 0.75, 1.4 * f)
    if nombre == "lengua":
        return lengua(lupa(img, P["boca"], A * 0.25, 0.3 * f), P, 0.8 + 0.4 * f)
    if nombre == "bigote":
        return bigote(img, P, 0.8 + 0.4 * f)
    if nombre == "anteojos":
        return anteojos(img, P, 1.0)
    if nombre in ("verde", "azul", "violeta", "rojo"):
        col = {"verde": (60, 210, 70), "azul": (235, 140, 40), "violeta": (210, 70, 170), "rojo": (60, 60, 230)}[nombre]
        return teñir(img, p, col, 0.55 * f + 0.15)
    if nombre == "espejo":
        return cv2.flip(img, 1)
    raise ValueError(nombre)


FUERTES = ["ojos_gigantes", "ojos_chiquitos", "un_ojo_gigante", "bocota", "boca_mini", "narizota", "cachetes",
           "cara_larga", "cara_aplastada", "cabeza_chica", "remolino", "lengua", "bigote", "anteojos",
           "verde", "azul", "violeta", "rojo"]
SUTILES = ["ojos_gigantes", "ojos_chiquitos", "bocota", "boca_mini", "narizota", "cachetes", "cara_larga",
           "cara_aplastada", "espejo"]


def variantes(img, p, n, nivel, semilla):
    """nivel: 'facil' (todas exageradas y combinadas), 'medio', 'dificil' (casi iguales). Devuelve n imágenes."""
    rng = np.random.default_rng(semilla)
    out = []
    for i in range(n):
        if nivel == "dificil":
            v = efecto(img, p, SUTILES[i % len(SUTILES)], rng.uniform(0.3, 0.5))
        else:
            k = 2 if (nivel == "facil" and rng.random() < 0.55) else 1
            v = img
            orden = lambda n: 2 if n in ("lengua", "bigote", "anteojos") else 1 if n in ("verde", "azul", "violeta", "rojo") else 0
            for nom in sorted(rng.choice(FUERTES, k, replace=False), key=orden):   # deformar, después teñir, al final lo dibujado
                v = efecto(v, p, nom, rng.uniform(0.75, 1.0) if nivel == "facil" else rng.uniform(0.5, 0.8))
        out.append(v)
    return out


if __name__ == "__main__":
    img, p = base(sys.argv[1])
    vs = [img] + variantes(img, p, 24, sys.argv[3] if len(sys.argv) > 3 else "facil", 1)
    filas = [np.hstack([cv2.resize(v, (200, 200)) for v in vs[r * 5:r * 5 + 5]]) for r in range(5)]
    cv2.imwrite(sys.argv[2], np.vstack(filas))
