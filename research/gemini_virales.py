#!/usr/bin/env python3
"""
Gemini mira shorts virales (simulaciones, predicciones y los sin cara de fútbol más vistos) con la guía de
competencia.py, más preguntas de CALIDAD de producción (render, animación, cámara, sonido, duración por tramo).
Uso: GEMINI_API_KEY=... python3 research/gemini_virales.py objetivos.json  -> data/raw/gemini_virales/<id>.json
"""
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from competencia import MODELS, PROMPT, URL  # noqa: E402

OUT = Path(__file__).resolve().parent.parent / "data" / "raw" / "gemini_virales"
OUT.mkdir(parents=True, exist_ok=True)
KEY = os.environ.get("GEMINI_API_KEY")
EXTRA = """
Además, agregá estas claves al mismo JSON:
 "calidad_produccion": "cómo está hecho: 3D/2D/IA/juego/fotos; nivel de pulido 1-10 y por qué",
 "camara_y_movimiento": "zooms, seguimiento, cortes, velocidad",
 "diseno_sonoro": "qué sonidos marcan cada evento y cómo arman la tensión",
 "tramos": "cómo se reparte el tiempo (ej: 0-2 gancho, 2-20 juego, 20-25 final)",
 "repetibilidad": "qué hace que alguien lo vea 2 o más veces (loop, detalle oculto, final rápido)",
 "como_replicarlo_sin_cara_y_sin_clips": "cómo podría hacerlo un canal sin cara, con fotos libres y animación por código"
}"""


def uno(o):
    v = o["video"]; dst = OUT / f"{v['id']}.json"
    if dst.exists():
        return
    med = o.get("mediana") or 0
    texto = PROMPT.format(vistas=v["vistas"], mediana=int(med) or "desconocida",
                          lift=round(v["vistas"] / med, 2) if med else "?").rstrip().rstrip("}") + "," + EXTRA
    body = {"contents": [{"parts": [{"file_data": {"file_uri": f"https://www.youtube.com/watch?v={v['id']}"}}, {"text": texto}]}],
            "generationConfig": {"temperature": 0.2, "responseMimeType": "application/json"}}
    for ronda in range(4):
        for m in MODELS:
            try:
                r = requests.post(URL.format(m), headers={"x-goog-api-key": KEY}, json=body, timeout=300)
            except requests.RequestException:
                continue
            if r.status_code == 200:
                try:
                    a = json.loads("".join(p.get("text", "") for p in r.json()["candidates"][0]["content"]["parts"]))
                    a = a[0] if isinstance(a, list) else a
                except Exception:
                    continue
                dst.write_text(json.dumps({**o, "modelo": m, "analisis": a}, ensure_ascii=False, indent=1))
                print("ok", o["canal"], v["id"], v["vistas"], flush=True)
                return
        time.sleep(15 * (ronda + 1))
    print("falló", v["id"], flush=True)


if __name__ == "__main__":
    objs = json.loads(Path(sys.argv[1]).read_text())
    with ThreadPoolExecutor(4) as ex:
        list(ex.map(uno, objs))
