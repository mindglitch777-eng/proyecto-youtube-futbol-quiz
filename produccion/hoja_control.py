#!/usr/bin/env python3
"""Hoja de control: las N mejores fotos (ya alineadas) de cada jugador, para revisar a ojo. Uso: hoja_control.py salida.jpg [N] [jugadores...]"""
import json
import sys
from pathlib import Path

import cv2
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from fusion import alinear  # noqa: E402

p = pd.read_csv(ROOT / "assets/poses.csv").sort_values(["jugador", "puntaje"])
n = int(sys.argv[2]) if len(sys.argv) > 2 else 1
if len(sys.argv) > 3:
    p = p[p.jugador.isin(sys.argv[3:])]
tiles = []
for _, r in p.groupby("jugador").head(n).iterrows():
    im, _ = alinear(ROOT / f"assets/fotos/{r.foto}.jpg", cara=json.loads(r.cara))
    im = cv2.resize(im, (150, 150))
    cv2.putText(im, f"{r.foto[:18]}", (2, 132), cv2.FONT_HERSHEY_SIMPLEX, 0.36, (0, 255, 255), 1)
    cv2.putText(im, f"p{r.puntaje:.0f} y{r.asimetria:+.2f}", (2, 146), cv2.FONT_HERSHEY_SIMPLEX, 0.36, (0, 255, 255), 1)
    tiles.append(im)
while len(tiles) % 10:
    tiles.append(np.zeros((150, 150, 3), np.uint8))
cv2.imwrite(sys.argv[1], np.vstack([np.hstack(tiles[i:i + 10]) for i in range(0, len(tiles), 10)]))
