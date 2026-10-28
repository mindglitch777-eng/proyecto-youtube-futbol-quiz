#!/usr/bin/env python3
"""
Baja memes de verdad para el runner (corre en GitHub Actions: desde la nube de Claude no se llega a estos sitios).
1) Plantillas famosas de imgflip (Stonks, Crying Jordan, Sad Pablo Escobar, etc.).
2) Memes de fútbol más votados de Reddit que nombran al jugador (Ronaldo, Messi, ...).
Guarda produccion/assets/memes/<fuente>/<id>.jpg + indice.json (título, url, puntos, subreddit).
"""
import json
import re
import time
from pathlib import Path

import requests

OUT = Path(__file__).resolve().parent / "assets" / "memes"
S = requests.Session()
S.headers["User-Agent"] = "futbol-edition-research/0.1 (by u/futbol_edition_bot)"
JUGADORES = ["ronaldo", "cr7", "messi", "neymar", "mbappe", "yamal", "haaland"]
SUBS = ["soccercirclejerk", "footballmemes", "soccermemes", "memes", "FootballMemes", "realmadrid", "soccer"]


def bajar(url, dst):
    if dst.exists():
        return True
    try:
        r = S.get(url, timeout=40)
        if r.status_code == 200 and r.headers.get("content-type", "").startswith("image/") and len(r.content) > 8000:
            dst.write_bytes(r.content)
            return True
    except requests.RequestException:
        pass
    return False


def imgflip(indice):
    d = OUT / "imgflip"; d.mkdir(parents=True, exist_ok=True)
    r = S.get("https://api.imgflip.com/get_memes", timeout=40).json()
    for m in r["data"]["memes"]:
        dst = d / f"{m['id']}.jpg"
        if bajar(m["url"], dst):
            indice.append(dict(fuente="imgflip", archivo=str(dst.relative_to(OUT)), titulo=m["name"], url=m["url"]))
    print("imgflip:", sum(1 for x in indice if x["fuente"] == "imgflip"))


def reddit(indice):
    d = OUT / "reddit"; d.mkdir(parents=True, exist_ok=True)
    vistos = set()
    for sub in SUBS:
        for q in JUGADORES[:4]:
            for t in ("year", "all"):
                url = f"https://www.reddit.com/r/{sub}/search.json?q={q}&restrict_sr=1&sort=top&t={t}&limit=100"
                try:
                    r = S.get(url, timeout=40)
                except requests.RequestException:
                    continue
                if r.status_code != 200:
                    print("reddit", sub, q, r.status_code); time.sleep(3); continue
                for c in r.json().get("data", {}).get("children", []):
                    p = c["data"]
                    img = p.get("url_overridden_by_dest") or p.get("url", "")
                    if p["id"] in vistos or not re.search(r"\.(jpe?g|png)$", img) or p.get("over_18"):
                        continue
                    vistos.add(p["id"])
                    dst = d / f"{p['id']}.jpg"
                    if bajar(img, dst):
                        indice.append(dict(fuente="reddit", archivo=str(dst.relative_to(OUT)), titulo=p["title"], url=img,
                                           puntos=p.get("score"), subreddit=sub, busqueda=q, permalink="https://reddit.com" + p["permalink"]))
                time.sleep(2)
    print("reddit:", sum(1 for x in indice if x["fuente"] == "reddit"))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    indice = []
    for f in (imgflip, reddit):
        try:
            f(indice)
        except Exception as e:  # una fuente caída no frena la otra
            print(f.__name__, "falló:", e)
    (OUT / "indice.json").write_text(json.dumps(indice, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
