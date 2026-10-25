#!/usr/bin/env python3
"""
Elige, para cada jugador, fotos donde (1) la persona ES el jugador y (2) la cara está de frente.

1. Identidad: YuNet detecta todas las caras de cada foto; SFace saca una "huella" de cada una.
   Entre las ~8 fotos de un jugador, la identidad que se repite en más fotos es el jugador;
   las caras que no se parecen a esa mayoría (otra persona, estatua, pintura) se descartan.
2. Pose: con los 68 puntos (LBF) se mide el giro (asimetría nariz-ojos), inclinación, boca abierta y tamaño.

Salida: produccion/assets/poses.csv (una fila por foto válida, con la caja de la cara correcta).
Modelos (no van al repo): produccion/assets/modelos/{face_detection_yunet_2023mar,face_recognition_sface_2021dec}.onnx
  https://media.githubusercontent.com/media/opencv/opencv_zoo/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx
  https://media.githubusercontent.com/media/opencv/opencv_zoo/main/models/face_recognition_sface/face_recognition_sface_2021dec.onnx
"""
import json
import sys
from pathlib import Path

import cv2
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from fusion import alinear  # noqa: E402

FOTOS = ROOT / "assets" / "fotos"
MOD = ROOT / "assets" / "modelos"
UMBRAL_MISMO = 0.40
# revisadas a ojo: no sirven aunque pasen los controles (murales, estatuas, cara tapada, etc.)
BLOQUEADAS = set(json.loads((Path(__file__).resolve().parent / "assets/fotos_bloqueadas.json").read_text())) \
    if (Path(__file__).resolve().parent / "assets/fotos_bloqueadas.json").exists() else set()     # coseno SFace (el umbral recomendado por OpenCV es 0.363)
_det = cv2.FaceDetectorYN.create(str(MOD / "face_detection_yunet_2023mar.onnx"), "", (320, 320), 0.75)
_rec = cv2.FaceRecognizerSF.create(str(MOD / "face_recognition_sface_2021dec.onnx"), "")


def caras(img):
    h, w = img.shape[:2]
    esc = min(1.0, 1600 / max(h, w))
    peq = cv2.resize(img, None, fx=esc, fy=esc) if esc < 1 else img
    _det.setInputSize((peq.shape[1], peq.shape[0]))
    _, fs = _det.detect(peq)
    if fs is None:
        return []
    out = []
    for f in fs:
        f = f.copy(); f[:14] /= esc
        if f[2] < 70:            # cara muy chica: inservible
            continue
        alin = _rec.alignCrop(img, f)
        out.append({"cara": [float(x) for x in f[:14]], "feat": _rec.feature(alin).flatten(), "conf": float(f[14])})
    return out


def pose(path, cara):
    """Giro e inclinación con los 5 puntos de YuNet (confiables también en perfiles);
    boca con los 68 puntos sobre la cara alineada; nitidez con la varianza del Laplaciano."""
    f = np.array(cara, np.float64)
    ojo1, ojo2, nariz, boca1, boca2 = f[4:6], f[6:8], f[8:10], f[10:12], f[12:14]
    ojos = (ojo1 + ojo2) / 2; d_ojos = np.linalg.norm(ojo2 - ojo1); boca = (boca1 + boca2) / 2
    yaw = float((nariz[0] - ojos[0]) / d_ojos)                 # 0 = de frente; ±0.3 = tres cuartos
    pitch = float((nariz[1] - ojos[1]) / max(boca[1] - ojos[1], 1) - 0.55)
    alineada, p = alinear(path, False, cara)
    alto = np.linalg.norm(p[27] - p[8])
    gris = cv2.cvtColor(alineada[160:520, 140:500], cv2.COLOR_BGR2GRAY)
    nitidez = float(cv2.Laplacian(gris, cv2.CV_64F).var())
    return {"asimetria": round(yaw, 3), "pitch": round(pitch, 3), "boca": round(float(np.linalg.norm(p[62] - p[66]) / alto), 3),
            "nitidez": round(nitidez, 1), "cara_px": int(cara[2])}


def puntaje(r):
    return (abs(r["asimetria"]) * 250 + abs(r["pitch"]) * 80 + max(0, r["boca"] - 0.04) * 300
            + (35 if r["nitidez"] < 60 else 0) + (25 if r["cara_px"] < 150 else 0)
            + (200 if r["foto"] in BLOQUEADAS else 0))


def main():
    cred = json.loads((FOTOS / "creditos.json").read_text())
    por_jugador = {}
    for k, v in cred.items():
        img = cv2.imread(str(FOTOS / f"{k}.jpg"))
        if img is None:
            continue
        for i, c in enumerate(caras(img)):
            por_jugador.setdefault(v["jugador"], []).append({"foto": k, **c})
    filas, informe = [], {}
    for jug, lista in por_jugador.items():
        F = np.array([x["feat"] / np.linalg.norm(x["feat"]) for x in lista])
        sim = F @ F.T
        fotos = [x["foto"] for x in lista]
        # apoyo = en cuántas OTRAS fotos hay una cara parecida
        apoyo = [len({fotos[j] for j in range(len(lista)) if fotos[j] != fotos[i] and sim[i, j] >= UMBRAL_MISMO}) for i in range(len(lista))]
        ancla = int(np.argmax(apoyo))
        n_fotos = len(set(fotos))
        validos = 0
        for foto in sorted(set(fotos)):
            idx = [i for i in range(len(lista)) if fotos[i] == foto]
            # la cara de esta foto más parecida a la identidad mayoritaria
            i = max(idx, key=lambda j: sim[ancla, j] if j != ancla else 1.0)
            s = 1.0 if i == ancla else float(sim[ancla, i])
            if s < UMBRAL_MISMO or (apoyo[i] < 1 and n_fotos > 2):
                continue
            try:
                p = pose(FOTOS / f"{foto}.jpg", lista[i]["cara"])
            except Exception:
                continue
            filas.append({"foto": foto, "jugador": jug, "similitud": round(s, 3), "apoyo": apoyo[i],
                          "cara": json.dumps([round(c, 1) for c in lista[i]["cara"]]), **p})
            validos += 1
        informe[jug] = {"fotos": n_fotos, "validas": validos, "apoyo_max": max(apoyo)}
    df = pd.DataFrame(filas)
    df["puntaje"] = df.apply(puntaje, axis=1).round(1)
    df.sort_values(["jugador", "puntaje"]).to_csv(ROOT / "assets/poses.csv", index=False)
    mejor = df.sort_values("puntaje").groupby("jugador").head(1).set_index("jugador")
    print(mejor[["foto", "puntaje", "asimetria", "pitch", "boca", "nitidez", "cara_px", "similitud"]].sort_values("puntaje").to_string())
    flojos = {j: v for j, v in informe.items() if v["validas"] < 2 or v["apoyo_max"] < 2}
    print("\njugadores con identidad dudosa o pocas fotos válidas:", flojos)


if __name__ == "__main__":
    main()
