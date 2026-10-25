#!/usr/bin/env python3
"""
Baja fotos CON FECHA (año) de cada jugador desde Wikimedia Commons, con licencia libre, para los formatos
"WHO IS HE? · AGE EVOLUTION" y "PRIME vs NOW". Corre en GitHub Actions (la nube de Claude no llega a Wikimedia).

Lee produccion/assets/pedido_epoca.json: ["Lionel Messi", ...]
Busca en Category:<Jugador> by year (o Category:<Jugador> y sus subcategorías), lee la fecha de cada archivo
(DateTimeOriginal) y se queda con hasta POR_ANIO fotos por año.
Salida: produccion/assets/fotos_epoca/<slug>_<año>_<k>.jpg + creditos_epoca.json
"""
import json
import os
import re
import time
from pathlib import Path

import requests

BASE = Path(__file__).resolve().parent / "assets"
OUT = BASE / "fotos_epoca"
OUT.mkdir(parents=True, exist_ok=True)
API = "https://commons.wikimedia.org/w/api.php"
S = requests.Session()
S.headers["User-Agent"] = "futbol-quiz-research/0.1 (https://github.com/mindglitch777-eng/proyecto-youtube-futbol-quiz)"
POR_ANIO = int(os.environ.get("POR_ANIO", "6"))
MAX_ARCHIVOS = 2500
POR_CATEGORIA = 40          # tope por subcategoría, para cubrir todos los años y no solo los primeros
LIBRES = re.compile(r"^(CC BY|CC BY-SA|CC0|Public domain|PD)", re.I)
MALAS = re.compile(r"statue|wax|mural|signature|autograph|logo|shirt|jersey|stadium|poster|stamp|graffiti|crowd|team", re.I)


def get(**p):
    for i in range(5):
        try:
            r = S.get(API, params={"format": "json", **p}, timeout=60)
            if r.status_code == 200:
                return r.json()
        except requests.RequestException:
            pass
        time.sleep(3 * (i + 1))
    return {}


def miembros(cat, tipo):
    out, cont = [], {}
    while True:
        d = get(action="query", list="categorymembers", cmtitle=cat, cmtype=tipo, cmlimit=500, **cont)
        out += [m["title"] for m in d.get("query", {}).get("categorymembers", [])]
        cont = d.get("continue", {})
        if not cont or len(out) > MAX_ARCHIVOS:
            return out


def archivos(nombre):
    cats = [f"Category:{nombre}"]
    for c in (f"Category:{nombre} by year", f"Category:{nombre}"):
        cats += [s for s in miembros(c, "subcat") if not re.search(r"(?i)family|statue|wax|signature|tattoo|museum|car", s)]
    vistos, files = set(), []
    for c in dict.fromkeys(cats):
        for f in miembros(c, "file")[:POR_CATEGORIA if c != f"Category:{nombre}" else 150]:
            if f not in vistos and re.search(r"(?i)\.(jpe?g|png)$", f) and not MALAS.search(f):
                vistos.add(f); files.append((c, f))
        if len(files) > MAX_ARCHIVOS:
            break
    return files


def infos(titulos):
    res = {}
    for k in range(0, len(titulos), 50):
        d = get(action="query", titles="|".join(titulos[k:k + 50]), prop="imageinfo",
                iiprop="url|extmetadata|size", iiurlwidth=1280)
        for pg in d.get("query", {}).get("pages", {}).values():
            if "imageinfo" in pg:
                res[pg["title"]] = pg["imageinfo"][0]
    return res


def anio(cat, titulo, md):
    for k in ("DateTimeOriginal", "DateTime"):
        m = re.search(r"(19[89]\d|20[0-2]\d)", md.get(k, {}).get("value", ""))
        if m:
            return int(m.group(1))
    m = re.search(r"in (19[89]\d|20[0-2]\d)\b", cat) or re.search(r"(19[89]\d|20[0-2]\d)", titulo)
    return int(m.group(1)) if m else None


def main():
    pedido = json.loads((BASE / "pedido_epoca.json").read_text())
    cred_path = OUT / "creditos_epoca.json"
    creditos = json.loads(cred_path.read_text()) if cred_path.exists() else {}
    for nombre in pedido:
        slug = re.sub(r"[^a-z0-9]+", "_", nombre.lower()).strip("_")
        ya = {v["archivo"] for v in creditos.values() if v["jugador"] == nombre}
        solo = [x.strip() for x in os.environ.get("SOLO", "").split(",") if x.strip()]
        if solo and nombre not in solo:
            continue
        if not solo and sum(v["jugador"] == nombre and v.get("v", 1) >= 2 for v in creditos.values()):
            continue      # ya bajado con la versión 2 (más fotos por año y más resolución)
        files = archivos(nombre)
        cat_de = {f: c for c, f in files}
        meta = infos([f for _, f in files])
        por_anio = {}
        for t, ii in meta.items():
            md = ii.get("extmetadata", {})
            limpio = lambda k: re.sub(r"<[^>]+>", "", md.get(k, {}).get("value", "")).strip()
            if not LIBRES.search(limpio("LicenseShortName")) or (ii.get("width") or 0) < 400 or not ii.get("thumburl"):
                continue
            a = anio(cat_de.get(t, ""), t, md)
            if not a:
                continue
            # preferimos archivos con el apellido en el nombre (suelen ser retratos del jugador)
            prio = 0 if nombre.split()[-1].lower() in t.lower() else 1
            por_anio.setdefault(a, []).append((prio, t, ii, limpio("Artist"), limpio("LicenseShortName"), limpio("LicenseUrl")))
        n = 0
        for a in sorted(por_anio):
            elegidos = [x for x in sorted(por_anio[a], key=lambda x: x[0]) if x[1] not in ya][:POR_ANIO]
            for k, (_, t, ii, autor, lic, lic_url) in enumerate(elegidos):
                k += sum(1 for v in creditos.values() if v["jugador"] == nombre and v["anio"] == a)
                try:
                    img = S.get(ii["thumburl"], timeout=60).content
                except requests.RequestException:
                    continue
                clave = f"{slug}_{a}_{k}"
                (OUT / f"{clave}.jpg").write_bytes(img)
                creditos[clave] = {"jugador": nombre, "anio": a, "archivo": t, "pagina": ii.get("descriptionurl"),
                                   "autor": autor, "licencia": lic, "licencia_url": lic_url, "v": 2}
                n += 1
        if n == 0:     # marca de versión aunque no haya fotos nuevas
            creditos[f"{slug}__v2"] = {"jugador": nombre, "anio": 0, "archivo": "", "v": 2}
        print(f"{nombre}: {len(files)} archivos, {n} fotos, años {sorted(por_anio)}", flush=True)
        cred_path.write_text(json.dumps(creditos, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
