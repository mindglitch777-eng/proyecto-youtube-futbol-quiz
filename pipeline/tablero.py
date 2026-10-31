#!/usr/bin/env python3
"""
Arma el tablero (sitio estático en _tablero/) con el estado del pipeline. Lo publica GitHub Pages en cada corrida:
index.html (fijo, en pipeline/tablero/) + datos.js (todo el estado, generado acá).
"""
import json
import os
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
D = RAIZ / "pipeline" / "datos"
OUT = RAIZ / "_tablero"


def cargar(n, defecto):
    p = D / n
    return json.loads(p.read_text()) if p.exists() else defecto


def main():
    OUT.mkdir(exist_ok=True)
    repo = os.environ.get("GITHUB_REPOSITORY", "mindglitch777-eng/proyecto-youtube-futbol-quiz")
    semana = cargar("semana_actual.json", {"inicio": None, "videos": []})
    analisis = cargar("analisis.json", {"virales": [], "formatos_nuevos": []})
    datos = dict(
        repo=repo,
        estado=cargar("estado.json", {}),
        radar=cargar("radar.json", {"virales": []}).get("virales", [])[:12],
        analisis=[dict(id=a["id"], titulo=a["titulo"], canal=a.get("canal"), vistas=a.get("vistas"),
                       formato=a["analisis"].get("formato"), nombre=a["analisis"].get("nombre_formato"), mecanica=a["analisis"].get("mecanica"),
                       gancho=a["analisis"].get("gancho"), dopamina=a["analisis"].get("dopamina", [])[:4],
                       mejoras=a["analisis"].get("como_lo_mejoramos", [])[:3]) for a in analisis.get("virales", [])],
        formatos_nuevos=analisis.get("formatos_nuevos", []),
        grabaciones=len(analisis.get("grabaciones", [])),
        rendimiento=cargar("rendimiento.json", {}),
        plan=cargar("plan.json", {}),
        semana=semana,
        base_videos=f"https://github.com/{repo}/releases/download/semana-{semana['inicio']}/" if semana["inicio"] else "",
        publicados=cargar("publicados.json", []),
    )
    (OUT / "datos.js").write_text("window.DATOS = " + json.dumps(datos, ensure_ascii=False) + ";\n")
    pagina = (RAIZ / "pipeline" / "tablero" / "pagina.html").read_text()            # el mismo archivo sirve de artefacto
    (OUT / "index.html").write_text('<!doctype html><html lang="es"><head><meta charset="utf-8">'
                                    '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"></head><body>'
                                    '<script src="datos.js"></script>' + pagina + "</body></html>")
    print(OUT)


if __name__ == "__main__":
    main()
