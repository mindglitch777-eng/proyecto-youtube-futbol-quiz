#!/usr/bin/env python3
"""
Arma la app del tablero para GitHub Pages (_tablero/): index.html (la app, que lee todo EN VIVO desde el repo y la API
pública de Actions) + datos.js con una foto del estado, que usa solo si no hay conexión.
Uso: python3 pipeline/tablero.py [vivo.json]
"""
import json
import shutil
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
D = RAIZ / "pipeline" / "datos"
OUT = RAIZ / "_tablero"


def cargar(p, defecto):
    p = Path(p)
    return json.loads(p.read_text()) if p.exists() else defecto


def main():
    OUT.mkdir(exist_ok=True)
    vivo = cargar(sys.argv[1], None) if len(sys.argv) > 1 else None
    foto = dict(estado=cargar(D / "estado.json", {}), radar=cargar(D / "radar.json", {}).get("virales", [])[:20],
                plan=cargar(D / "plan.json", {}), gerente=cargar(D / "gerente.json", None), cerebro=cargar(D / "cerebro.json", None),
                analisis_ia=cargar(D / "analisis_ia.json", None), semana=cargar(D / "semana_actual.json", {}), publicados=cargar(D / "publicados.json", []), vivo=vivo)
    (OUT / "datos.js").write_text("window.SNAPSHOT = " + json.dumps(foto, ensure_ascii=False) + ";\n")
    shutil.copy(RAIZ / "pipeline" / "tablero" / "app.html", OUT / "index.html")
    shutil.copy(RAIZ / "pipeline" / "tablero" / "privacidad.html", OUT / "privacidad.html")
    print(OUT)


if __name__ == "__main__":
    main()
