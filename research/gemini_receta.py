#!/usr/bin/env python3
"""
Gemini describe con PRECISIÓN TÉCNICA cómo está hecho un short que explotó, para replicarlo:
layout por zonas de pantalla, tiempos exactos, reglas del juego, física, cámara, tipografías, colores, sonido por evento.
Uso: GEMINI_API_KEY=... python3 research/gemini_receta.py objetivos.json -> data/raw/gemini_recetas/<id>.json
"""
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

OUT = Path(__file__).resolve().parent.parent / "data" / "raw" / "gemini_recetas"
OUT.mkdir(parents=True, exist_ok=True)
KEY = os.environ.get("GEMINI_API_KEY")
MODELS = ["gemini-3.5-flash", "gemini-3.6-flash", "gemini-flash-latest", "gemini-3.5-flash-lite"]
URL = "https://generativelanguage.googleapis.com/v1beta/models/{}:generateContent"
PROMPT = """Sos director técnico de motion graphics. Este short tuvo {vistas} vistas. Necesito REPLICARLO con código (Python, física 2D,
dibujo vectorial). Miralo y escuchalo completo y describí con precisión, sin inventar (null si no se ve). Respondé SOLO JSON en español:
{{
 "regla_del_juego": "qué tiene que pasar para ganar/avanzar, explicado como para programarlo",
 "layout": [{{"zona": "arriba/centro/abajo (porcentaje de alto aprox)", "que_hay": "..."}}],
 "elementos": [{{"objeto": "...", "forma_color_tamano": "...", "movimiento": "velocidad, rotación, gravedad, rebotes"}}],
 "linea_de_tiempo": [{{"t": "0.0-2.0", "que_pasa": "..."}}],
 "camara": "fija / sigue / zoom; transiciones exactas",
 "tipografia_y_textos": "fuente aproximada, tamaños, colores, contornos, animación de entrada",
 "paleta": ["colores principales en hex aproximado"],
 "sonido_por_evento": [{{"evento": "...", "sonido": "..."}}],
 "musica": "tipo, bpm aproximado, si es tendencia",
 "fps_y_suavidad": "si se ve a 60 fps o 30, si hay motion blur, si hay tirones",
 "detalles_que_dan_calidad": ["sombras, brillos, partículas, estelas, etc."],
 "gancho_y_cierre": "primer segundo exacto y último segundo exacto (loop?)",
 "que_mejorarias_para_superarlo": ["..."]
}}"""


def uno(o):
    v = o["video"]; dst = OUT / f"{v['id']}.json"
    if dst.exists():
        return
    body = {"contents": [{"parts": [{"file_data": {"file_uri": f"https://www.youtube.com/watch?v={v['id']}"}},
                                    {"text": PROMPT.format(vistas=v["vistas"])}]}],
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
                dst.write_text(json.dumps({**o, "modelo": m, "receta": a}, ensure_ascii=False, indent=1))
                print("ok", o["canal"], v["id"], flush=True)
                return
        time.sleep(15 * (ronda + 1))
    print("falló", v["id"], flush=True)


if __name__ == "__main__":
    with ThreadPoolExecutor(4) as ex:
        list(ex.map(uno, json.loads(Path(sys.argv[1]).read_text())))
