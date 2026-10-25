#!/usr/bin/env python3
"""Hoja de control de todas las fusiones de un lote: A | fusión 50% | B por fila. Uso: hoja_fusiones.py salida_prefijo guiones..."""
import json
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from fusion import Fusion  # noqa: E402

pref, guiones = sys.argv[1], sys.argv[2:]
celdas = []
for gp in guiones:
    g = json.loads(Path(gp).read_text())
    for r in g["rondas"]:
        f = Fusion(ROOT / f"assets/fotos/{r['a']}.jpg", ROOT / f"assets/fotos/{r['b']}.jpg", r.get("espejar_a", False),
                   r.get("espejar_b", False), r.get("cara_a"), r.get("cara_b"))
        fila = np.hstack([cv2.resize(f.cuadro(x), (170, 170)) for x in (0, 0.5, 1)])
        cv2.putText(fila, f"{g['id'][-2:]} {r['nombre_a']}+{r['nombre_b']} c{r.get('costo_pose', 0):.0f}", (3, 164),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1)
        celdas.append(fila)
while len(celdas) % 3:
    celdas.append(np.zeros_like(celdas[0]))
filas = [np.hstack(celdas[i:i + 3]) for i in range(0, len(celdas), 3)]
mitad = (len(filas) + 1) // 2
cv2.imwrite(f"{pref}_1.jpg", np.vstack(filas[:mitad])); cv2.imwrite(f"{pref}_2.jpg", np.vstack(filas[mitad:]))
print(len(celdas))
