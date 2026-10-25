#!/usr/bin/env python3
"""
Fotos libres de Wikimedia Commons de OBJETOS por año (pelotas de cada Mundial) para "EVOLUTION" de objetos.
Corre en GitHub Actions. Lee assets/pedido_objetos.json {"balones": [[año, "consulta"], ...]} y baja hasta 4
candidatas por año (se elige a ojo con la hoja de control). Salida: assets/objetos/<serie>/<año>_<k>.jpg + creditos.json
"""
import json
import re
import time
from pathlib import Path

import requests

BASE = Path(__file__).resolve().parent / "assets"
API = "https://commons.wikimedia.org/w/api.php"
S = requests.Session()
S.headers["User-Agent"] = "futbol-quiz-research/0.1 (https://github.com/mindglitch777-eng/proyecto-youtube-futbol-quiz)"
LIBRES = re.compile(r"^(CC BY|CC BY-SA|CC0|Public domain|PD)", re.I)


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


def candidatos(consultas, tope=14):
    """Varias fuentes de Commons: búsqueda de archivos por cada consulta + archivos de la categoría que mejor coincide."""
    vistos = []
    for q in consultas:
        d = get(action="query", list="search", srsearch=f"{q} filetype:bitmap", srnamespace=6, srlimit=8)
        vistos += [x["title"] for x in d.get("query", {}).get("search", [])]
        c = get(action="query", list="search", srsearch=q, srnamespace=14, srlimit=2)
        for cat in [x["title"] for x in c.get("query", {}).get("search", [])]:
            m = get(action="query", list="categorymembers", cmtitle=cat, cmtype="file", cmlimit=10)
            vistos += [x["title"] for x in m.get("query", {}).get("categorymembers", [])]
    return [t for t in dict.fromkeys(vistos) if re.search(r"(?i)\.(jpe?g|png)$", t)][:tope]


def main():
    pedido = json.loads((BASE / "pedido_objetos.json").read_text())
    for serie, items in pedido.items():
        out = BASE / "objetos" / serie; out.mkdir(parents=True, exist_ok=True)
        cred_p = out / "creditos.json"
        cred = json.loads(cred_p.read_text()) if cred_p.exists() else {}
        for anio, consultas in items:
            if isinstance(consultas, str):
                consultas = [consultas]
            if any(v["anio"] == anio for v in cred.values()):
                continue
            titulos = candidatos(consultas)
            d = get(action="query", titles="|".join(titulos), prop="imageinfo", iiprop="url|extmetadata|size", iiurlwidth=1000) if titulos else {}
            k = 0
            for pg in d.get("query", {}).get("pages", {}).values():
                ii = (pg.get("imageinfo") or [{}])[0]
                md = ii.get("extmetadata", {})
                limpio = lambda x: re.sub(r"<[^>]+>", "", md.get(x, {}).get("value", "")).strip()
                if not LIBRES.search(limpio("LicenseShortName")) or (ii.get("width") or 0) < 400 or not ii.get("thumburl"):
                    continue
                try:
                    r = S.get(ii["thumburl"], timeout=60)
                except requests.RequestException:
                    continue
                if not r.headers.get("content-type", "").startswith("image/"):
                    continue          # a veces Commons devuelve una página HTML en vez de la imagen
                clave = f"{anio}_{k}"
                (out / f"{clave}.jpg").write_bytes(r.content)
                cred[clave] = {"anio": anio, "consulta": consultas[0], "archivo": pg["title"], "pagina": ii.get("descriptionurl"),
                               "autor": limpio("Artist"), "licencia": limpio("LicenseShortName"), "licencia_url": limpio("LicenseUrl")}
                k += 1
            print(serie, anio, len(titulos), "candidatos,", k, "bajadas", flush=True)
            cred_p.write_text(json.dumps(cred, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
