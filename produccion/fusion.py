#!/usr/bin/env python3
"""
Fusión de caras (morphing por triángulos) con OpenCV: 68 puntos faciales (LBF)
+ triangulación de Delaunay. fusionar(a, b, t) devuelve la cara intermedia:
t=0 es A, t=1 es B, t=0.5 mitad y mitad.

Modelo: produccion/assets/modelos/lbfmodel.yaml (no va al repo, 56 MB). Se baja con:
  curl -L -o produccion/assets/modelos/lbfmodel.yaml \
    https://raw.githubusercontent.com/kurnianggoro/GSOC2017/master/data/lbfmodel.yaml
"""
from functools import lru_cache
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent
LADO = 640
_cascada = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")


@lru_cache(maxsize=1)
def _facemark():
    fm = cv2.face.createFacemarkLBF()
    fm.loadModel(str(ROOT / "assets/modelos/lbfmodel.yaml"))
    return fm


def puntos(img, caja=None):
    gris = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    if caja is not None:
        cara = np.array([int(v) for v in caja])
    else:
        caras = _cascada.detectMultiScale(gris, 1.1, 5, minSize=(80, 80))
        if not len(caras):
            raise ValueError("no encontré cara")
        cara = max(caras, key=lambda c: c[2] * c[3])
    ok, lm = _facemark().fit(gris, np.array([cara]))
    return lm[0][0].astype(np.float32)


def alinear(path, espejar=False, cara=None):
    """Recorte LADOxLADO con los ojos en una posición fija (para que las caras coincidan).
    cara: 14 valores de YuNet (caja + 5 puntos) de la persona correcta; si falta, se detecta.
    espejar=True da vuelta la foto para que mire hacia el mismo lado que la otra."""
    img = cv2.imread(str(path))
    if cara is not None:
        f = np.array(cara, np.float32)
        ojo_i, ojo_d = f[4:6].copy(), f[6:8].copy()      # YuNet: ojo derecho del sujeto (izq. en la imagen) primero
    else:
        p = puntos(img)
        ojo_i, ojo_d = p[36:42].mean(0), p[42:48].mean(0)
    if espejar:
        w = img.shape[1]
        img = img[:, ::-1].copy()
        ojo_i, ojo_d = np.array([w - 1 - ojo_d[0], ojo_d[1]]), np.array([w - 1 - ojo_i[0], ojo_i[1]])
    if ojo_i[0] > ojo_d[0]:
        ojo_i, ojo_d = ojo_d, ojo_i
    dst_i, dst_d = np.array([LADO * 0.35, LADO * 0.40]), np.array([LADO * 0.65, LADO * 0.40])
    ang = np.degrees(np.arctan2(*(ojo_d - ojo_i)[::-1]))
    esc = np.linalg.norm(dst_d - dst_i) / np.linalg.norm(ojo_d - ojo_i)
    centro = (ojo_i + ojo_d) / 2
    M = cv2.getRotationMatrix2D(tuple(map(float, centro)), float(ang), float(esc))
    M[:, 2] += (dst_i + dst_d) / 2 - centro
    out = cv2.warpAffine(img, M, (LADO, LADO), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
    # ya alineada, la cara está siempre en el mismo lugar: caja fija para los 68 puntos
    return out, puntos(out, [LADO * 0.18, LADO * 0.20, LADO * 0.64, LADO * 0.70])


def _con_borde(p):
    n = LADO - 1
    borde = np.array([[0, 0], [n / 2, 0], [n, 0], [n, n / 2], [n, n], [n / 2, n], [0, n], [0, n / 2]], np.float32)
    return np.vstack([p, borde])


def _triangulos(p):
    sub = cv2.Subdiv2D((0, 0, LADO, LADO))
    for x, y in p:
        sub.insert((float(min(max(x, 0), LADO - 1)), float(min(max(y, 0), LADO - 1))))
    tris = []
    for t in sub.getTriangleList():
        v = t.reshape(3, 2)
        idx = [int(np.argmin(np.linalg.norm(p - q, axis=1))) for q in v]
        if len(set(idx)) == 3:
            tris.append(idx)
    return tris


def _warp_tri(src, dst, t_src, t_dst):
    r1, r2 = cv2.boundingRect(np.float32([t_src])), cv2.boundingRect(np.float32([t_dst]))
    t1 = [(p[0] - r1[0], p[1] - r1[1]) for p in t_src]
    t2 = [(p[0] - r2[0], p[1] - r2[1]) for p in t_dst]
    parche = src[r1[1]:r1[1] + r1[3], r1[0]:r1[0] + r1[2]]
    if parche.size == 0 or r2[2] == 0 or r2[3] == 0:
        return
    M = cv2.getAffineTransform(np.float32(t1), np.float32(t2))
    w = cv2.warpAffine(parche, M, (r2[2], r2[3]), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT_101)
    mask = np.zeros((r2[3], r2[2], 3), np.float32)
    cv2.fillConvexPoly(mask, np.int32(t2), (1, 1, 1), 16, 0)
    zona = dst[r2[1]:r2[1] + r2[3], r2[0]:r2[0] + r2[2]]
    if zona.shape != w.shape:
        return
    zona[:] = zona * (1 - mask) + w * mask


class Fusion:
    def __init__(self, path_a, path_b, espejar_a=False, espejar_b=False, cara_a=None, cara_b=None):
        self.a, pa = alinear(path_a, espejar_a, cara_a)
        self.b, pb = alinear(path_b, espejar_b, cara_b)
        self.pa, self.pb = _con_borde(pa), _con_borde(pb)
        self.tris = _triangulos((self.pa + self.pb) / 2)
        self.a32, self.b32 = self.a.astype(np.float32), self.b.astype(np.float32)

    def cuadro(self, t):
        pm = (1 - t) * self.pa + t * self.pb
        wa, wb = self.a32.copy(), self.b32.copy()   # relleno: donde no cae triángulo queda la foto
        for i, j, k in self.tris:
            tri_m = [pm[i], pm[j], pm[k]]
            _warp_tri(self.a32, wa, [self.pa[i], self.pa[j], self.pa[k]], tri_m)
            _warp_tri(self.b32, wb, [self.pb[i], self.pb[j], self.pb[k]], tri_m)
        return np.clip((1 - t) * wa + t * wb, 0, 255).astype(np.uint8)


if __name__ == "__main__":
    import sys
    f = Fusion(sys.argv[1], sys.argv[2])
    cv2.imwrite(sys.argv[3], np.hstack([f.cuadro(x) for x in (0, 0.5, 1)]))
