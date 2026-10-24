#!/usr/bin/env python3
"""
Baja fotos de jugadores con licencia libre de Wikimedia Commons, con autor y
licencia (para atribuir en la descripción del video). Corre en GitHub Actions
porque la nube de Claude no llega a wikimedia.org.

Lee produccion/assets/pedido_fotos.json: ["Lamine Yamal", "Kylian Mbappé", ...]
Para cada jugador toma la foto principal de su artículo de Wikipedia en inglés
y hasta EXTRA fotos más de Commons. Guarda en produccion/assets/fotos/ y
produccion/assets/fotos/creditos.json.
"""
import json
import re
import time
from pathlib import Path

import requests

BASE = Path(__file__).resolve().parent / "assets"
OUT = BASE / "fotos"
OUT.mkdir(parents=True, exist_ok=True)
S = requests.Session()
S.headers["User-Agent"] = "futbol-quiz-research/0.1 (https://github.com/mindglitch777-eng/proyecto-youtube-futbol-quiz)"
EXTRA = 3
LIBRES = re.compile(r"^(CC BY|CC BY-SA|CC0|Public domain|PD)", re.I)


def get(url, **p):
    for i in range(4):
        r = S.get(url, params=p, timeout=60)
        if r.status_code == 200:
            return r
        time.sleep(3 * (i + 1))
    r.raise_for_status()


def info(titulo_archivo):
    d = get("https://commons.wikimedia.org/w/api.php", action="query", titles=titulo_archivo, prop="imageinfo",
            iiprop="url|extmetadata|size", iiurlwidth=900, format="json").json()
    pg = next(iter(d["query"]["pages"].values()))
    if "imageinfo" not in pg:
        return None
    ii = pg["imageinfo"][0]
    md = ii.get("extmetadata", {})
    limpio = lambda k: re.sub(r"<[^>]+>", "", md.get(k, {}).get("value", "")).strip()
    return {"archivo": titulo_archivo, "thumb": ii.get("thumburl"), "pagina": ii.get("descriptionurl"),
            "autor": limpio("Artist"), "licencia": limpio("LicenseShortName"), "licencia_url": limpio("LicenseUrl"),
            "ancho": ii.get("width"), "alto": ii.get("height")}


def principal(nombre):
    d = get("https://en.wikipedia.org/w/api.php", action="query", titles=nombre, prop="pageimages",
            piprop="name", redirects=1, format="json").json()
    pg = next(iter(d["query"]["pages"].values()))
    return ("File:" + pg["pageimage"]) if pg.get("pageimage") else None


def extras(nombre):
    d = get("https://commons.wikimedia.org/w/api.php", action="query", list="search", srsearch=f"{nombre} filetype:bitmap",
            srnamespace=6, srlimit=15, format="json").json()
    return [x["title"] for x in d["query"]["search"]]


def main():
    pedido = json.loads((BASE / "pedido_fotos.json").read_text())
    cred_path = OUT / "creditos.json"
    creditos = json.loads(cred_path.read_text()) if cred_path.exists() else {}
    for nombre in pedido:
        slug = re.sub(r"[^a-z0-9]+", "_", nombre.lower()).strip("_")
        if any(k.startswith(slug + "_") for k in creditos):
            continue
        candidatos = [principal(nombre)] + extras(nombre)
        n = 0
        for t in dict.fromkeys(c for c in candidatos if c):
            meta = info(t)
            if not meta or not meta["thumb"] or not LIBRES.search(meta["licencia"] or ""):
                continue
            if (meta["ancho"] or 0) < 400:
                continue
            img = get(meta["thumb"]).content
            clave = f"{slug}_{n}"
            (OUT / f"{clave}.jpg").write_bytes(img)
            creditos[clave] = {"jugador": nombre, **meta}
            print(f"{clave}: {meta['licencia']} · {meta['autor'][:60]}")
            n += 1
            if n > EXTRA:
                break
        if n == 0:
            print(f"{nombre}: sin foto libre")
    cred_path.write_text(json.dumps(creditos, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
