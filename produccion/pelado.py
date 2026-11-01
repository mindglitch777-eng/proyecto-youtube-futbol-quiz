#!/usr/bin/env python3
"""
Recorte de busto (cabeza + hombros + camiseta) sin fondo y versión PELADA del jugador (para DRESS UP).
busto(clave) → dict(img=RGBA, pelado=RGBA, puntos=68 landmarks en coords del recorte, A=ancho de cara, cejas=y)

Uso de prueba: python3 produccion/pelado.py cristiano_ronaldo lamine_yamal → salida/pelado_prueba.png
"""
import json
import sys
from functools import lru_cache
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

import caras_find as CF

ROOT = Path(__file__).resolve().parent
FRONT = json.loads((ROOT / "assets" / "fotos" / "frontales.json").read_text())


def landmarks(img):
    h, w = img.shape[:2]
    CF._det.setInputSize((w, h))
    _, f = CF._det.detect(img)
    x, y, fw, fh = max(f, key=lambda c: c[2] * c[3])[:4]
    ok, pts = CF._lbf.fit(img, np.array([[[x, y, fw, fh]]], np.int32))
    return np.asarray(pts[0], np.float32).reshape(-1, 2)[:68]


@lru_cache(maxsize=32)
def busto(clave, ancho=560):
    im = cv2.imread(str(ROOT / "assets" / "fotos" / f"{FRONT.get(clave, clave + '_0')}.jpg"))
    p = landmarks(im)
    A = np.linalg.norm(p[16] - p[0]); cx = (p[0, 0] + p[16, 0]) / 2; cejas = p[17:27, 1].min()
    x0, x1 = int(cx - A * 1.55), int(cx + A * 1.55)
    y0, y1 = int(cejas - A * 0.95), int(p[8, 1] + A * 1.25)
    H, W = im.shape[:2]
    pad = [max(0, -y0), max(0, y1 - H), max(0, -x0), max(0, x1 - W)]
    im = cv2.copyMakeBorder(im, pad[0], pad[1], pad[2], pad[3], cv2.BORDER_REPLICATE)
    y0 += pad[0]; y1 += pad[0]; x0 += pad[2]; x1 += pad[2]
    p = p + np.array([pad[2], pad[0]])
    crop = im[y0:y1, x0:x1].copy(); p = p - np.array([x0, y0])
    s = ancho / crop.shape[1]
    crop = cv2.resize(crop, (ancho, int(crop.shape[0] * s)), interpolation=cv2.INTER_LANCZOS4); p = p * s; A *= s
    cx = (p[0, 0] + p[16, 0]) / 2; cejas = p[17:27, 1].min()
    h, w = crop.shape[:2]
    # GrabCut sembrado: cara y cuello seguros, torso abajo probable, bordes de arriba fondo
    m = np.full((h, w), cv2.GC_PR_BGD, np.uint8)
    cv2.ellipse(m, (int(cx), int(cejas)), (int(A * 0.75), int(A * 0.95)), 0, 180, 360, cv2.GC_PR_FGD, -1)
    cv2.rectangle(m, (int(cx - A * 1.4), int(p[8, 1] + A * 0.25)), (int(cx + A * 1.4), h), cv2.GC_PR_FGD, -1)
    cv2.fillConvexPoly(m, cv2.convexHull(p[:27].astype(np.int32)), cv2.GC_FGD)
    cv2.rectangle(m, (int(cx - A * 0.22), int(p[8, 1])), (int(cx + A * 0.22), int(p[8, 1] + A * 0.5)), cv2.GC_FGD, -1)
    cv2.rectangle(m, (int(cx - A * 0.8), int(p[8, 1] + A * 0.75)), (int(cx + A * 0.8), h - 2), cv2.GC_FGD, -1)
    m[:3, :] = cv2.GC_BGD; m[:, :3] = cv2.GC_BGD; m[:, -3:] = cv2.GC_BGD
    bg, fg = np.zeros((1, 65)), np.zeros((1, 65))
    cv2.grabCut(crop, m, None, bg, fg, 6, cv2.GC_INIT_WITH_MASK)
    a = np.where((m == cv2.GC_FGD) | (m == cv2.GC_PR_FGD), 255, 0).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(a)
    if n > 1:
        a = np.where(lab == lab[int(p[30, 1]), int(p[30, 0])], 255, 0).astype(np.uint8)
    a = cv2.GaussianBlur(a, (5, 5), 0)
    rgb = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)
    img = Image.fromarray(np.dstack([rgb, a]))
    return dict(img=img, pelado=pelar(rgb, a, p, A), puntos=p, A=A, cejas=cejas, cx=cx)


def pelar(rgb, a, p, A):
    """Saca el pelo: cráneo liso con color de piel (de las mejillas), sombreado y unido a la frente con degradé."""
    h, w = a.shape
    cx = (p[0, 0] + p[16, 0]) / 2; cejas = p[17:27, 1].min()
    mej = np.vstack([rgb[int(p[k, 1]) - 3:int(p[k, 1]) + 3, int((p[k, 0] + p[30, 0]) / 2) - 3:int((p[k, 0] + p[30, 0]) / 2) + 3].reshape(-1, 3)
                     for k in (3, 13)])
    piel = np.median(mej, 0).astype(np.float32) * 1.06
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    ry, rx = A * 0.66, A * 0.54                                                   # cráneo
    cyk = cejas + A * 0.08
    e = ((xx - cx) / rx) ** 2 + ((yy - cyk) / ry) ** 2
    craneo = (e <= 1) & (yy < cyk)
    # sombreado: luz arriba a la izquierda, borde más oscuro
    luz = np.clip(1.08 - 0.25 * e - 0.10 * ((xx - cx + A * 0.15) / A) ** 2, 0.72, 1.12)
    piel_img = np.clip(piel[None, None, :] * luz[..., None], 0, 255)
    brillo = np.exp(-(((xx - cx + A * 0.12) / (A * 0.16)) ** 2 + ((yy - (cyk - ry * 0.62)) / (A * 0.08)) ** 2)) * 38
    piel_img = np.clip(piel_img + brillo[..., None], 0, 255)
    # mezcla con la frente original cerca de las cejas
    t = np.clip((cejas - A * 0.03 - yy) / (A * 0.07), 0, 1)                      # 0 en las cejas → 1 arriba (corto: tapa vinchas y rulos)
    peso = np.where(craneo, t, 0)[..., None]
    out = rgb.astype(np.float32) * (1 - peso) + piel_img * peso
    alfa = a.astype(np.float32).copy()
    arriba = yy < cyk
    alfa[arriba & ~(e <= 1.0)] = 0                                                # pelo fuera del cráneo: afuera
    # forma de cabeza = cráneo ∪ contorno de la cara (subido hasta las sienes) ∪ orejas; arriba de la nariz, lo demás es pelo
    cab = np.zeros((h, w), np.uint8)
    cont = np.vstack([p[:17], [[p[16, 0], cyk], [p[0, 0], cyk]]]).astype(np.int32)
    cv2.fillConvexPoly(cab, cv2.convexHull(cont), 1)
    for sgn, k in ((-1, 0), (1, 16)):
        ox = p[k, 0] + sgn * A * 0.07
        cv2.ellipse(cab, (int(ox), int((cejas + p[33, 1]) / 2 + A * 0.06)), (int(A * 0.15), int(A * 0.32)), 0, 0, 360, 1, -1)
    cab = (cab > 0) | (e <= 1.0)
    alfa[(yy < cejas + A * 0.12) & ~cab] = 0
    alfa[craneo] = 255
    borde = cv2.GaussianBlur((e <= 1).astype(np.float32), (0, 0), 2.0)
    alfa = np.where(arriba, np.minimum(alfa, borde * 255 + (~arriba) * 255), alfa)
    return Image.fromarray(np.dstack([np.clip(out, 0, 255).astype(np.uint8), alfa.astype(np.uint8)]))


@lru_cache(maxsize=32)
def pelo(clave):
    """Solo el pelo del jugador (sin frente ni cara), con su ancla: dict(img RGBA, cx, cejas, A)."""
    b = busto(clave)
    rgb = np.asarray(b["img"])[..., :3].astype(np.float32); a = np.asarray(b["img"])[..., 3].astype(np.float32)
    p, A, cx, cejas = b["puntos"], b["A"], b["cx"], b["cejas"]
    h, w = a.shape
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    lab = cv2.cvtColor(rgb.astype(np.uint8), cv2.COLOR_RGB2LAB).astype(np.float32)
    mej = np.vstack([lab[int(p[k, 1]) - 4:int(p[k, 1]) + 4, int((p[k, 0] + p[30, 0]) / 2) - 4:int((p[k, 0] + p[30, 0]) / 2) + 4].reshape(-1, 3) for k in (3, 13)])
    piel = np.median(mej, 0)
    fr = lab[int(cejas - A * 0.1):int(cejas - A * 0.03), int(cx - A * 0.15):int(cx + A * 0.15)].reshape(-1, 3)
    frente = np.median(fr, 0)
    dist = np.minimum(np.linalg.norm(lab - piel, axis=2), np.linalg.norm(lab - frente, axis=2))
    cara = np.zeros((h, w), np.uint8)
    cv2.fillConvexPoly(cara, cv2.convexHull(np.vstack([p[:17], p[17:27] - [0, A * 0.04]]).astype(np.int32)), 1)
    zona = (yy < cejas + A * 0.45) & (yy < p[30, 1]) & ~((cara > 0) & (yy > cejas - A * 0.12))
    es_pelo = zona & (dist > 26) & (a > 40)
    m = cv2.morphologyEx(es_pelo.astype(np.uint8), cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    m = cv2.GaussianBlur(m.astype(np.float32), (0, 0), 1.2)
    alfa = np.clip(m * a / 255 * 255, 0, 255)
    img = Image.fromarray(np.dstack([rgb, alfa]).astype(np.uint8))
    bb = img.getbbox()
    return dict(img=img.crop(bb), cx=cx - bb[0], cejas=cejas - bb[1], A=A)


def teñir(img, tono, sat=0.85, luz=0.25):
    """Recolorea el pelo conservando la textura (tono 0-360)."""
    arr = np.asarray(img).astype(np.float32)
    hsv = cv2.cvtColor(arr[..., :3].astype(np.uint8), cv2.COLOR_RGB2HSV).astype(np.float32)
    v = hsv[..., 2] / 255
    hsv[..., 0] = tono / 2; hsv[..., 1] = 255 * sat; hsv[..., 2] = 255 * np.clip(luz + (1 - luz) * v ** 0.6, 0, 1)
    rgb = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2RGB)
    return Image.fromarray(np.dstack([rgb, arr[..., 3]]).astype(np.uint8))


if __name__ == "__main__":
    ks = sys.argv[1:] or ["cristiano_ronaldo", "lamine_yamal"]
    bs = [busto(k) for k in ks]
    W = sum(b["img"].width for b in bs) * 2 + 40
    H = max(b["img"].height for b in bs)
    out = Image.new("RGBA", (W, H), (255, 236, 0, 255)); x = 0
    for b in bs:
        out.alpha_composite(b["img"], (x, 0)); x += b["img"].width
    for b in bs:
        out.alpha_composite(b["pelado"], (x + 40, 0)); x += b["img"].width
    out.convert("RGB").save(ROOT / "salida" / "pelado_prueba.png")
    print(ROOT / "salida" / "pelado_prueba.png")
