#!/usr/bin/env python3
"""
GOLES POR EDAD (19/11, pedido del CEO): baja de Wikipedia (en inglés) la sección "Career statistics" (club por temporada +
selección por año) y la fecha de nacimiento de cada jugador. Corre en GitHub Actions (la nube de Claude no llega a Wikipedia).
Guarda el texto crudo en assets/goles/<clave>.txt; goles_edad.py lo convierte en goles acumulados por edad (datos reales).
"""
import json
import time
from pathlib import Path

import requests

OUT = Path(__file__).resolve().parent / "assets" / "goles"; OUT.mkdir(parents=True, exist_ok=True)
JUGADORES = {"messi": "Lionel Messi", "ronaldo": "Cristiano Ronaldo", "mbappe": "Kylian Mbappé", "yamal": "Lamine Yamal",
             "neymar": "Neymar", "zlatan": "Zlatan Ibrahimović", "henry": "Thierry Henry", "ronaldinho": "Ronaldinho",
             "vinicius": "Vinícius Júnior", "zidane": "Zinedine Zidane", "beckham": "David Beckham"}
S = requests.Session()
S.headers["User-Agent"] = "futbol-quiz-research/0.1 (https://github.com/mindglitch777-eng/proyecto-youtube-futbol-quiz)"


def api(**p):
    for i in range(5):
        try:
            r = S.get("https://en.wikipedia.org/w/api.php", params=dict(p, format="json", formatversion=2, redirects=1), timeout=60)
            if r.status_code == 200:
                return r.json()
        except requests.RequestException:
            pass
        time.sleep(3 * (i + 1))
    return {}


def main():
    hechos = {}
    for k, t in JUGADORES.items():
        secs = api(action="parse", page=t, prop="sections").get("parse", {}).get("sections", [])
        partes = [api(action="parse", page=t, prop="wikitext", section=0).get("parse", {}).get("wikitext", "")[:6000]]
        en = False
        for s in secs:
            if s["level"] == "2":
                en = "career statistics" in s["line"].lower() or s["line"].lower() == "statistics"
            if en:
                w = api(action="parse", page=t, prop="wikitext", section=s["index"]).get("parse", {}).get("wikitext", "")
                partes.append(f"\n\n#### SECCION {s['line']}\n{w}")
        (OUT / f"{k}.txt").write_text("".join(partes))
        hechos[k] = dict(titulo=t, secciones=len(partes) - 1)
        print(k, hechos[k], flush=True)
    (OUT / "fuentes.json").write_text(json.dumps(dict(fuente="Wikipedia (en), sección Career statistics", jugadores=hechos), ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
