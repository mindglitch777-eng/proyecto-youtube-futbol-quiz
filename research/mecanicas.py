#!/usr/bin/env python3
"""
Frente B: etiqueta la MECÁNICA interactiva de shorts de cualquier nicho (no solo fútbol) con Gemini (texto).
Sirve para comparar qué mecánicas explotan en otros nichos y cuánto existen en fútbol.

Uso: GEMINI_API_KEY=... python3 research/mecanicas.py <consultas separadas por |>   (o "nichos" / "futbol_mec")
Salida: data/raw/gemini_mecanicas.json {video_id: {...}}
"""
import json
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
OUT = RAW / "gemini_mecanicas.json"
KEY = os.environ.get("GEMINI_API_KEY")
MODELS = os.environ.get("GEMINI_MODELS", "gemini-3.1-flash-lite,gemini-3.5-flash-lite,gemini-flash-lite-latest").split(",")
URL = "https://generativelanguage.googleapis.com/v1beta/models/{}:generateContent"

MECANICAS = {
    "imagen_oculta": "adivinar por silueta, sombra, borroso, pixelado, zoom, recorte",
    "parte_del_cuerpo": "adivinar por una parte: ojos, pelo, sonrisa, manos, tatuaje",
    "sonido_voz": "adivinar por sonido, voz, canción, celebración",
    "emojis": "adivinar por emojis",
    "fusion": "dos o más personas/personajes fusionados o mezclados en uno",
    "encontrar_el_real": "encontrar al verdadero entre versiones falsas o deformadas",
    "odd_one_out": "encontrar el elemento distinto en una grilla (emoji, letra, color)",
    "diferencias": "encontrar diferencias entre dos imágenes",
    "ilusion_optica": "ilusión óptica / test de vista / imagen escondida en patrón",
    "contar": "contar objetos/personas en la imagen",
    "objeto_escondido": "encontrar algo escondido en una escena",
    "memoria": "mirar algo unos segundos y después recordar dónde/qué era",
    "acertijo_logica": "acertijo, adivinanza, problema de lógica o matemática",
    "verdadero_falso": "verdadero o falso / mito o realidad",
    "opcion_multiple": "pregunta con opciones A/B/C",
    "elegir_uno": "elegí uno / would you rather / pick one (opinión, sin respuesta correcta)",
    "mas_o_menos": "más o menos / higher or lower / quién es mayor / precio / comparar números",
    "ranking": "ranking / tier list / top N",
    "adivinar_edad": "adivinar la edad",
    "version_ia": "versión IA / 'si fueran…' / transformación / cambio de estilo",
    "evolucion": "evolución en el tiempo / antes y después",
    "que_pasa_despues": "predecir qué pasa después",
    "adivinar_identidad_directo": "adivinar quién es con foto normal o pistas de texto",
    "no_interactivo": "no es un juego ni pregunta para el espectador",
}
NICHOS = ["futbol", "otro_deporte", "celebridades", "anime_dibujos", "musica", "peliculas_series", "paises_geografia",
          "marcas_logos", "comida", "videojuegos", "general_cerebro", "otro"]

PROMPT = """Clasificá cada YouTube Short por su MECÁNICA (qué tiene que hacer el espectador) y su NICHO.
Mecánicas (usá solo estos códigos):
{mec}
Nichos: {nichos}
Para cada video devolvé {{"i": índice, "m": código de mecánica, "m2": segunda mecánica o null, "nicho": código,
"cara": true si hay una persona real en cámara (youtuber/presentador), false si es sin cara (gráficos/imágenes), null si no se sabe}}.
Basate en título, tags y descripción. Respondé SOLO con un array JSON.

Videos:
{videos}"""


def call(body):
    for ronda in range(6):
        for m in MODELS:
            try:
                r = requests.post(URL.format(m), headers={"x-goog-api-key": KEY}, json=body, timeout=300)
            except requests.RequestException:
                continue
            if r.status_code == 200:
                d = r.json()
                return "".join(p.get("text", "") for p in d["candidates"][0]["content"]["parts"]), m
        time.sleep(10 * (ronda + 1))
    raise RuntimeError("sin respuesta")


def main(ids):
    videos = json.loads((RAW / "videos.json").read_text())
    res = json.loads(OUT.read_text()) if OUT.exists() else {}
    pend = [videos[i] for i in dict.fromkeys(ids) if i in videos and i not in res]
    print("pendientes", len(pend))
    mec = "\n".join(f"- {k}: {d}" for k, d in MECANICAS.items())
    lock = threading.Lock()

    def lote(k):
        L = pend[k:k + 100]
        txt = "\n".join(json.dumps({"i": i, "titulo": v["title"], "canal": v["channelTitle"], "tags": v["tags"][:8],
                                    "descr": v["description"][:150]}, ensure_ascii=False) for i, v in enumerate(L))
        body = {"contents": [{"parts": [{"text": PROMPT.format(mec=mec, nichos=", ".join(NICHOS), videos=txt)}]}],
                "generationConfig": {"temperature": 0, "responseMimeType": "application/json", "maxOutputTokens": 32000}}
        try:
            t, m = call(body)
            out = json.loads(t)
        except Exception as e:
            print("lote", k, "error", str(e)[:100]); return
        with lock:
            for o in out:
                i = o.get("i")
                if isinstance(i, int) and 0 <= i < len(L) and o.get("m") in MECANICAS:
                    res[L[i]["id"]] = {"m": o["m"], "m2": o.get("m2"), "nicho": o.get("nicho"), "cara": o.get("cara")}
            OUT.write_text(json.dumps(res, ensure_ascii=False))
            print("lote", k, "ok", len(res))

    with ThreadPoolExecutor(4) as ex:
        list(ex.map(lote, range(0, len(pend), 100)))


if __name__ == "__main__":
    hits = json.loads((RAW / "search_hits.json").read_text())
    qs = set(sys.argv[1].split("|")) if len(sys.argv) > 1 and sys.argv[1] not in ("nichos", "todo") else None
    if len(sys.argv) > 1 and sys.argv[1] == "nichos":
        sys.path.insert(0, str(ROOT / "research"))
        from yt_research import NICHOS_SEEDS
        qs = {q for q, _, _ in NICHOS_SEEDS}
    ids = [v for h in hits if qs is None or h["q"] in qs for v in h["video_ids"]]
    main(ids)
