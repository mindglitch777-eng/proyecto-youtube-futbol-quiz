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


def imgflip_busqueda(indice):
    """Plantillas de memes de fútbol de la búsqueda de imgflip (Ronaldo llorando, Siuuu, el busto, Messi...)."""
    d = OUT / "imgflip_futbol"; d.mkdir(parents=True, exist_ok=True)
    for q in ["ronaldo", "cristiano ronaldo", "cr7", "siuuu", "messi", "neymar", "mbappe", "haaland", "football", "soccer"]:
        for pag in (1, 2):
            try:
                r = S.get("https://imgflip.com/memesearch", params={"q": q, "page": pag}, timeout=40)
            except requests.RequestException:
                continue
            print("imgflip busqueda", q, pag, r.status_code)
            for href, titulo in re.findall(r'href="/meme/([^"]+)"[^>]*>(?:<[^>]+>)*\s*([^<]{2,80})<', r.text):
                pass
            for ruta, alt in re.findall(r'<img[^>]+src="(//i\.imgflip\.com/[^"]+)"[^>]*alt="([^"]*)"', r.text):
                url = "https:" + ruta
                ident = re.sub(r"\W", "", ruta.split("/")[-1].split(".")[0])
                dst = d / f"{ident}.jpg"
                if any(x["archivo"].endswith(dst.name) for x in indice):
                    continue
                if bajar(url.replace("/4/", "/"), dst) or bajar(url, dst):
                    indice.append(dict(fuente="imgflip_futbol", archivo=str(dst.relative_to(OUT)), titulo=alt, url=url, busqueda=q))
            time.sleep(1.5)
    print("imgflip futbol:", sum(1 for x in indice if x["fuente"] == "imgflip_futbol"))


def commons(indice):
    """Fotos libres que son meme por sí mismas: el busto de Ronaldo del aeropuerto de Madeira, figuras de cera, etc."""
    d = OUT / "commons"; d.mkdir(parents=True, exist_ok=True)
    for q in ["Cristiano Ronaldo bust", "Busto Cristiano Ronaldo", "Cristiano Ronaldo wax figure", "Cristiano Ronaldo statue",
              "Cristiano Ronaldo celebration", "Messi wax figure", "Cristiano Ronaldo crying", "Cristiano Ronaldo funny"]:
        r = S.get("https://commons.wikimedia.org/w/api.php", params=dict(action="query", generator="search", gsrsearch=q, gsrnamespace=6,
                  gsrlimit=20, prop="imageinfo", iiprop="url|extmetadata", iiurlwidth=900, format="json"), timeout=40).json()
        for pg in (r.get("query", {}).get("pages", {}) or {}).values():
            ii = (pg.get("imageinfo") or [{}])[0]
            url = ii.get("thumburl") or ii.get("url")
            if not url or not re.search(r"\.(jpe?g|png)", url, re.I):
                continue
            dst = d / f"{pg['pageid']}.jpg"
            meta = ii.get("extmetadata", {})
            if bajar(url, dst):
                indice.append(dict(fuente="commons", archivo=str(dst.relative_to(OUT)), titulo=pg["title"], url=url, busqueda=q,
                                   autor=re.sub("<[^>]+>", "", meta.get("Artist", {}).get("value", ""))[:120],
                                   licencia=meta.get("LicenseShortName", {}).get("value", "")))
        time.sleep(1)
    print("commons:", sum(1 for x in indice if x["fuente"] == "commons"))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    previo = OUT / "indice.json"
    indice = [x for x in (json.loads(previo.read_text()) if previo.exists() else []) if x["fuente"] == "imgflip"]
    for f in (imgflip_busqueda, commons, reddit):
        try:
            f(indice)
        except Exception as e:  # una fuente caída no frena la otra
            print(f.__name__, "falló:", e)
    (OUT / "indice.json").write_text(json.dumps(indice, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
