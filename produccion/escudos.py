#!/usr/bin/env python3
"""
Escudos reales de clubes (imagen del infobox de Wikipedia en inglés) para las carreras y copas.
Corre en GitHub Actions (la nube de Claude no llega a Wikipedia). Lee assets/pedido_escudos.json
{"clave": "Título del artículo"} y guarda assets/escudos/<clave>.png + fuentes.json.
"""
import json
import re
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


def desde_infobox(titulo):
    r = get("https://en.wikipedia.org/w/api.php", action="parse", page=titulo, prop="wikitext",
            section=0, redirects=1, format="json", formatversion=2)
    if not r or "parse" not in r.json():
        return None, None
    texto = r.json()["parse"]["wikitext"]
    m = re.search(r"\|\s*(?:image|logo|crest|clubcrest)\s*=\s*(?:\[\[)?(?:File:|Image:)?([^|\]\n<]+?\.(?:svg|png|jpg|gif))",
                  texto, re.I)
    if not m:
        return None, None
    archivo = m.group(1).strip()
    r = get("https://en.wikipedia.org/w/api.php", action="query", titles="File:" + archivo, prop="imageinfo",
            iiprop="url", iiurlwidth=600, format="json")
    if not r:
        return None, None
    info = next(iter(r.json()["query"]["pages"].values())).get("imageinfo", [{}])[0]
    return info.get("thumburl") or info.get("url"), archivo


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
        nombre = pg.get("pageimage")
        if not th:
            # Los logos no libres (fair use) no salen en pageimages: leer el campo image= del infobox
            th, nombre = desde_infobox(pg.get("title", titulo))
        if not th:
            print(clave, "sin imagen"); continue
        img = get(th)
        if not img or not img.headers.get("content-type", "").startswith("image/"):
            print(clave, "descarga fallida"); continue
        (OUT / f"{clave}.png").write_bytes(img.content)
        fuentes[clave] = {"articulo": titulo, "archivo": nombre, "url": th}
        print(clave, "ok", nombre)
        fuentes_p.write_text(json.dumps(fuentes, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
