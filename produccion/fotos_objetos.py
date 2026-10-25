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


def main():
    pedido = json.loads((BASE / "pedido_objetos.json").read_text())
    for serie, items in pedido.items():
        out = BASE / "objetos" / serie; out.mkdir(parents=True, exist_ok=True)
        cred_p = out / "creditos.json"
        cred = json.loads(cred_p.read_text()) if cred_p.exists() else {}
        for anio, consulta in items:
            if any(v["anio"] == anio for v in cred.values()):
                continue
            d = get(action="query", generator="search", gsrsearch=f"{consulta} filetype:bitmap", gsrnamespace=6, gsrlimit=12,
                    prop="imageinfo", iiprop="url|extmetadata|size", iiurlwidth=1000)
            pags = sorted(d.get("query", {}).get("pages", {}).values(), key=lambda p: p.get("index", 99))
            k = 0
            for pg in pags:
                ii = (pg.get("imageinfo") or [{}])[0]
                md = ii.get("extmetadata", {})
                limpio = lambda x: re.sub(r"<[^>]+>", "", md.get(x, {}).get("value", "")).strip()
                if not LIBRES.search(limpio("LicenseShortName")) or (ii.get("width") or 0) < 400 or not ii.get("thumburl"):
                    continue
                try:
                    img = S.get(ii["thumburl"], timeout=60).content
                except requests.RequestException:
                    continue
                clave = f"{anio}_{k}"
                (out / f"{clave}.jpg").write_bytes(img)
                cred[clave] = {"anio": anio, "consulta": consulta, "archivo": pg["title"], "pagina": ii.get("descriptionurl"),
                               "autor": limpio("Artist"), "licencia": limpio("LicenseShortName"), "licencia_url": limpio("LicenseUrl")}
                k += 1
                if k >= 4:
                    break
            print(serie, anio, consulta, k, flush=True)
            cred_p.write_text(json.dumps(cred, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
