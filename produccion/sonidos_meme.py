#!/usr/bin/env python3
"""
Baja efectos de sonido de meme (Siuuu, vine boom, bruh, oh no, ...) de myinstants.com para el runner.
Corre en GitHub Actions (desde la nube de Claude no se llega). Guarda produccion/assets/sonidos_meme/<clave>_<n>.mp3 + indice.json.
"""
import json
import re
import time
from pathlib import Path
from urllib.parse import quote

import requests

OUT = Path(__file__).resolve().parent / "assets" / "sonidos_meme"
S = requests.Session()
S.headers["User-Agent"] = "Mozilla/5.0 (futbol-edition-research)"
BUSCAR = {
    "siuuu": "siuuu", "siu_estadio": "ronaldo siu", "vine_boom": "vine boom", "bruh": "bruh", "oh_no": "oh no no no",
    "emotional_damage": "emotional damage", "caja_registradora": "cash register", "airhorn": "mlg airhorn",
    "triste_violin": "sad violin", "fail": "fail sound effect", "wow": "anime wow", "money": "money money",
    "rizz": "rizz", "among_us": "among us", "nope": "nope", "yeah_boy": "yeah boiii", "dramatic": "dun dun dun",
    "ronaldo": "cristiano ronaldo", "messi": "messi", "ankara_messi": "ankara messi",
}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    indice = []
    for clave, q in BUSCAR.items():
        try:
            r = S.get(f"https://www.myinstants.com/en/search/?name={quote(q)}", timeout=40)
        except requests.RequestException as e:
            print(clave, "error", e); continue
        sonidos = re.findall(r"play\('(/media/sounds/[^']+\.mp3)'", r.text)
        nombres = re.findall(r'class="instant-link[^"]*"[^>]*>([^<]+)<', r.text)
        print(clave, r.status_code, len(sonidos))
        for n, ruta in enumerate(dict.fromkeys(sonidos)):
            if n >= 3:
                break
            dst = OUT / f"{clave}_{n}.mp3"
            try:
                a = S.get("https://www.myinstants.com" + ruta, timeout=40)
            except requests.RequestException:
                continue
            if a.status_code == 200 and len(a.content) > 3000:
                dst.write_bytes(a.content)
                indice.append(dict(clave=clave, archivo=dst.name, origen="https://www.myinstants.com" + ruta,
                                   nombre=nombres[n].strip() if n < len(nombres) else ""))
        time.sleep(1.5)
    (OUT / "indice.json").write_text(json.dumps(indice, ensure_ascii=False, indent=1))
    print(len(indice), "sonidos")


if __name__ == "__main__":
    main()
