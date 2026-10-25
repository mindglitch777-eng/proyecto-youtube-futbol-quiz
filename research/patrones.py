#!/usr/bin/env python3
"""
Cruza la recompensa psicológica (gemini_recompensas.json) con:
- velocidad real (vistas/hora entre dos mediciones) de shorts de <= 14 días -> qué pega MÁS RÁPIDO
- vistas totales de shorts de otros nichos y de la muestra de fútbol -> qué pega MÁS
- oferta en fútbol (muestra al azar) -> qué está MENOS explotado
Salida: data/processed/patrones_recompensa.csv, patrones_mecanica_velocidad.csv
"""
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
P = ROOT / "data" / "processed"

rec = json.loads((RAW / "gemini_recompensas.json").read_text())
mec = json.loads((RAW / "gemini_mecanicas.json").read_text())
videos = json.loads((RAW / "videos.json").read_text())
vel = pd.read_csv(P / "velocidad.csv")
vel = vel[vel.edad_dias <= 14].copy()
for k in ("r", "accion", "serie", "m"):
    vel[k] = vel.id.map(lambda i: rec.get(i, {}).get(k))
vel["cara"] = vel.id.map(lambda i: mec.get(i, {}).get("cara"))

filas = []
for i, r in rec.items():
    if i not in videos or i not in mec:
        continue
    filas.append({"id": i, "r": r["r"], "accion": r.get("accion"), "serie": r.get("serie"), "m": mec[i]["m"],
                  "nicho": mec[i].get("nicho"), "cara": mec[i].get("cara"), "views": videos[i]["views"]})
tot = pd.DataFrame(filas)
fut = tot[tot.nicho == "futbol"]
otros = tot[(tot.nicho != "futbol") & (tot.cara == False)]  # noqa: E712


def tabla(col):
    v = vel[vel[col].notna()]
    a = v.groupby(col).agg(n_vel=("id", "size"), vph_mediana=("vistas_por_hora", "median"),
                           pct_10k_vph=("vistas_por_hora", lambda s: round(100 * (s >= 10000).mean(), 1)),
                           pct_1k_vph=("vistas_por_hora", lambda s: round(100 * (s >= 1000).mean(), 1)))
    b = otros.groupby(col).agg(n_otros=("id", "size"), med_otros=("views", "median"))
    c = fut.groupby(col).agg(n_fut=("id", "size"), med_fut=("views", "median"))
    c["pct_oferta_fut"] = (100 * c.n_fut / len(fut)).round(2)
    return a.join(b, how="outer").join(c, how="outer").sort_values("vph_mediana", ascending=False)


if __name__ == "__main__":
    pd.set_option("display.width", 200)
    t = tabla("r"); t.to_csv(P / "patrones_recompensa.csv"); print(t.to_string())
    t2 = tabla("m"); t2.to_csv(P / "patrones_mecanica_velocidad.csv"); print(t2.to_string())
    t3 = tabla("accion"); print(t3.to_string())
    print(tabla("serie").to_string())
