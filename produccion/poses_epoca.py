#!/usr/bin/env python3
"""
Igual que poses.py pero para las fotos CON FECHA (assets/fotos_epoca): verifica que la cara sea el jugador
(identidad mayoritaria con SFace, reforzada con sus fotos ya verificadas si las hay) y mide la pose.
Salida: assets/poses_epoca.csv (foto, jugador, anio, cara, asimetria, pitch, boca, nitidez, cara_px, similitud, puntaje)
"""
import json

import cv2
import numpy as np
import pandas as pd

from poses import ROOT, UMBRAL_MISMO, caras, pose, puntaje

EP = ROOT / "assets" / "fotos_epoca"


def main():
    cred = json.loads((EP / "creditos_epoca.json").read_text())
    ref = pd.read_csv(ROOT / "assets" / "poses.csv")
    por_jugador = {}
    for k, v in cred.items():
        img = cv2.imread(str(EP / f"{k}.jpg"))
        if img is None:
            continue
        for c in caras(img):
            por_jugador.setdefault(v["jugador"], []).append({"foto": k, "anio": v["anio"], **c})
    filas = []
    for jug, lista in por_jugador.items():
        F = np.array([x["feat"] / np.linalg.norm(x["feat"]) for x in lista])
        sim = F @ F.T
        fotos = [x["foto"] for x in lista]
        apoyo = np.array([len({fotos[j] for j in range(len(lista)) if fotos[j] != fotos[i] and sim[i, j] >= UMBRAL_MISMO})
                          for i in range(len(lista))])
        # huella de referencia: media de las caras con más apoyo (la identidad que más se repite)
        top = np.argsort(-apoyo)[:max(3, len(lista) // 6)]
        cen = F[top].mean(0); cen /= np.linalg.norm(cen)
        r = ref[ref.jugador == jug]
        if len(r):   # si ya tenemos fotos verificadas del jugador, chequeamos que el centro coincida
            img = cv2.imread(str(next((ROOT / "assets/fotos").glob(r.iloc[0].foto + ".*"))))
            cc = [c for c in caras(img)]
            if cc:
                fr = max((c["feat"] / np.linalg.norm(c["feat"]) for c in cc), key=lambda f: float(f @ cen))
                print(f"{jug}: coincidencia con foto verificada {float(fr @ cen):.2f}")
        for foto in sorted(set(fotos)):
            idx = [i for i in range(len(lista)) if fotos[i] == foto]
            i = max(idx, key=lambda j: float(F[j] @ cen))
            s = float(F[i] @ cen)
            if s < UMBRAL_MISMO + 0.05:
                continue
            try:
                p = pose(EP / f"{foto}.jpg", lista[i]["cara"])
            except Exception:
                continue
            filas.append({"foto": foto, "jugador": jug, "anio": lista[i]["anio"], "similitud": round(s, 3),
                          "cara": json.dumps([round(c, 1) for c in lista[i]["cara"]]), **p})
        print(f"{jug}: {len(set(fotos))} fotos con cara -> {sum(f['jugador'] == jug for f in filas)} verificadas", flush=True)
    df = pd.DataFrame(filas)
    df["puntaje"] = df.apply(puntaje, axis=1).round(1)
    df.sort_values(["jugador", "anio", "puntaje"]).to_csv(ROOT / "assets/poses_epoca.csv", index=False)


if __name__ == "__main__":
    main()
