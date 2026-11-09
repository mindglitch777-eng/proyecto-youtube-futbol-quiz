#!/usr/bin/env python3
"""
FÁBRICA DIARIA (07/11): en vez de armar una semana entera, cada día produce los videos de DENTRO DE 3 DÍAS con lo que dicen
HOY las olas (investigar_olas.py → estado naciente/subiendo/estable/bajando/muerta) y nuestro Analytics. Así nos subimos a una ola
cuando arranca y la soltamos cuando cae, con 2-3 días de reacción en vez de 7.
Si ese día ya tiene videos (de un plan anterior o subidos), no hace nada. Escribe plan.json para e5_produccion.py.
Imprime la fecha objetivo (o "nada") para el workflow.
"""
import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from comun import RAIZ, cargar

ART = timezone(timedelta(hours=-3))


def ocupado(fecha):
    if any(p["fecha"] == fecha and p.get("video_id") and not p.get("reemplazado") and not __import__("re").match(r"o\d{4}_", p["id"]) for p in cargar("publicados.json", [])):
        return True
    for vj in (RAIZ / "produccion").glob("semana_*/videos.json"):
        if any(m["fecha"] == fecha and not m.get("extra") for m in json.loads(vj.read_text())):
            return True
    try:
        tags = subprocess.run(["gh", "release", "list", "--limit", "30", "--json", "tagName", "-q", ".[].tagName"],
                              capture_output=True, text=True, timeout=120).stdout.split()
    except Exception:
        tags = []
    for t in tags:
        if t.startswith("semana-"):
            r = subprocess.run(["gh", "release", "download", t, "-p", "videos.json", "-O", "-"], capture_output=True, text=True, timeout=120)
            try:
                if any(m["fecha"] == fecha and not m.get("extra") for m in json.loads(r.stdout or "[]")):
                    return True
            except Exception:
                pass
    return False


def main():
    dias = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    objetivo = (datetime.now(ART).date() + timedelta(days=dias))
    if ocupado(objetivo.isoformat()):
        print("nada"); return
    import e4_plan
    e4_plan.main(objetivo, 1)
    print(objetivo.isoformat())


if __name__ == "__main__":
    main()
