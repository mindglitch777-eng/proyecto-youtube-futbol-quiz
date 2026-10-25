#!/usr/bin/env python3
"""
Locución con edge-tts (voces neurales de Microsoft, gratis y sin límite diario). Corre en GitHub Actions
porque la nube de Claude no llega a speech.platform.bing.com. Genera una frase por archivo (sin cortes).

Lee todos los produccion/guiones/*.json y guarda produccion/assets/voz_edge/<hash>.mp3 + indice.json.
"""
import asyncio
import hashlib
import json
from pathlib import Path

import edge_tts

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "assets" / "voz_edge"
OUT.mkdir(parents=True, exist_ok=True)
VOZ, VELOCIDAD, TONO = "en-US-GuyNeural", "+18%", "+3Hz"


def clave(texto):
    return hashlib.sha1(f"{texto}|{VOZ}|{VELOCIDAD}|{TONO}".encode()).hexdigest()[:14]


async def main():
    indice_p = OUT / "indice.json"
    indice = json.loads(indice_p.read_text()) if indice_p.exists() else {}
    lineas = []
    for g in sorted((ROOT / "guiones").glob("*.json")):
        d = json.loads(g.read_text())
        lineas += [x for r in d["rondas"] for x in (r["voz_pregunta"], r["voz_revela"])] + [d["voz_cierre"]]
    for t in dict.fromkeys(lineas):
        k = clave(t)
        if (OUT / f"{k}.mp3").exists():
            continue
        await edge_tts.Communicate(t, VOZ, rate=VELOCIDAD, pitch=TONO).save(str(OUT / f"{k}.mp3"))
        indice[t] = {"archivo": f"{k}.mp3", "voz": VOZ, "velocidad": VELOCIDAD, "tono": TONO}
        print(k, t)
    indice_p.write_text(json.dumps(indice, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    asyncio.run(main())
