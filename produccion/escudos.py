#!/usr/bin/env python3
"""
Escudos reales de clubes (imagen del infobox de Wikipedia en inglés) para las carreras y copas.
Corre en GitHub Actions (la nube de Claude no llega a Wikipedia). Lee assets/pedido_escudos.json
{"clave": "Título del artículo"} y guarda assets/escudos/<clave>.png + fuentes.json.
"""
import json
import time
from pathlib import Path

import requests

BASE = Path(__file__).resolve().parent / "assets"
OUT = BASE / "escudos"; OUT.mkdir(parents=True, exist_ok=True)
S = requests.Session()
S.headers["User-Agent"] = "futbol-quiz-research/0.1 (https://github.com/mindglitch777-eng/proyecto-youtube-futbol-quiz)"


def get(url, **p):
    for i in range(5):
        try:
            r = S.get(url, params=p, timeout=60)
            if r.status_code == 200:
                return r
        except requests.RequestException:
            pass
        time.sleep(3 * (i + 1))
    return None


def main():
    pedido = json.loads((BASE / "pedido_escudos.json").read_text())
    fuentes_p = OUT / "fuentes.json"
    fuentes = json.loads(fuentes_p.read_text()) if fuentes_p.exists() else {}
    for clave, titulo in pedido.items():
        if (OUT / f"{clave}.png").exists():
            continue
        r = get("https://en.wikipedia.org/w/api.php", action="query", titles=titulo, prop="pageimages",
                piprop="thumbnail|name", pithumbsize=600, redirects=1, format="json")
        if not r:
            print(clave, "sin respuesta"); continue
        pg = next(iter(r.json()["query"]["pages"].values()))
        th = pg.get("thumbnail", {}).get("source")
        if not th:
            print(clave, "sin imagen"); continue
        img = get(th)
        if not img or not img.headers.get("content-type", "").startswith("image/"):
            print(clave, "descarga fallida"); continue
        (OUT / f"{clave}.png").write_bytes(img.content)
        fuentes[clave] = {"articulo": titulo, "archivo": pg.get("pageimage"), "url": th}
        print(clave, "ok", pg.get("pageimage"))
        fuentes_p.write_text(json.dumps(fuentes, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
