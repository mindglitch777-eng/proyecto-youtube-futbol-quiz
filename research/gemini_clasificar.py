#!/usr/bin/env python3
"""
Clasifica los shorts de data/raw/videos.json en la taxonomía de formatos usando
Gemini SOLO con texto (título, canal, duración, tags, inicio de descripción).
No mira los videos: eso lo hace gemini_shorts.py con una muestra.

Salida (cacheada, reanudable): data/raw/gemini_formatos.json  {video_id: {...}}
Uso: GEMINI_API_KEY=... python3 research/gemini_clasificar.py [tanda=120]
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
OUT = RAW / "gemini_formatos.json"
KEY = os.environ.get("GEMINI_API_KEY")
MODELS = os.environ.get("GEMINI_MODELS", "gemini-3.5-flash-lite,gemini-flash-lite-latest,gemini-flash-latest,gemini-3.5-flash").split(",")
URL = "https://generativelanguage.googleapis.com/v1beta/models/{}:generateContent"

FORMATOS = {
    "emojis": "adivinar jugador/club/frase por emojis",
    "imagen_oculta": "adivinar por silueta, foto pixelada/borrosa/recortada, zoom, sombra",
    "carrera": "adivinar jugador por su trayectoria de clubes / transferencias",
    "pistas": "adivinar por pistas progresivas o datos ('soy... quién soy')",
    "escudo": "adivinar escudo/logo/camiseta/bandera",
    "estadio": "adivinar estadio",
    "fichaje": "adivinar fichaje, precio o valor de mercado",
    "gol_o_jugada": "adivinar jugador por un gol, jugada o skill (usa clips)",
    "infancia": "adivinar futbolista de bebé / de chico / antes y después",
    "verdadero_falso": "verdadero o falso / mito o realidad",
    "opcion_multiple": "pregunta con opciones A/B/C/D",
    "duelo": "este o este, quién es mejor, higher or lower, comparar dos",
    "ordenar": "ordenar de mayor a menor / ranking objetivo",
    "grilla_conexion": "quién jugó con ambos, grilla tipo futbol-11, conectar jugadores",
    "impostor": "encontrar al impostor / el que no pertenece",
    "reto_nombrar": "nombrá un jugador (con letra, de un país, contrarreloj, 'o te mojás'), con personas reales",
    "preguntas_a_personas": "preguntas a gente / entrevista / quiz battle entre personas en cámara",
    "tier_list": "tier list / ranking de opinión / puntuar jugadores",
    "armar_equipo": "armá tu equipo, draft, elegí uno, 'pick one', build your XI",
    "datos_curiosos": "dato o estadística sin pregunta (cuánto miden, cuánto ganan)",
    "otro_quiz": "otro tipo de quiz o juego interactivo de fútbol",
    "no_quiz_futbol": "fútbol pero no es quiz ni juego (highlights, edit, humor, parodia, noticia)",
    "no_futbol": "no es de fútbol",
}

PROMPT = """Clasificá cada YouTube Short según su FORMATO. Usá solo esta lista de códigos:
{formatos}

Para cada video devolvé un objeto con:
 "i": el número de índice que te doy,
 "f": código de formato (uno de la lista),
 "f2": segundo formato si mezcla dos, o null,
 "cara": true si el título/descr sugiere personas reales en cámara (youtuber, jugador, entrevista), false si parece video "sin cara" (gráficos, texto, imágenes), null si no se sabe,
 "idioma": "es" | "en" | "pt" | "otro" (idioma del título),
 "sujeto": jugador, club o tema principal en 1 a 3 palabras, o null.
Basate en título, tags y descripción. No inventes: si no está claro, elegí "otro_quiz" o "no_quiz_futbol".
Respondé SOLO con un array JSON.

Videos:
{videos}"""


def call(body):
    errs = []
    for ronda in range(6):
        for m in MODELS:
            try:
                r = requests.post(URL.format(m), headers={"x-goog-api-key": KEY}, json=body, timeout=300)
            except requests.RequestException as e:
                errs.append(f"{m} {e}")
                continue
            if r.status_code == 200:
                d = r.json()
                parts = d["candidates"][0].get("content", {}).get("parts", [])
                return "".join(p.get("text", "") for p in parts if not p.get("thought")), d.get("usageMetadata", {}), m
            errs.append(f"{m} {r.status_code}: {r.text[:150]}")
            print("  " + errs[-1][:90].replace("\n", " "), file=sys.stderr)
        time.sleep(10 * (ronda + 1))
    raise RuntimeError(" | ".join(errs[-3:]))


def main(tanda):
    videos = json.loads((RAW / "videos.json").read_text())
    res = json.loads(OUT.read_text()) if OUT.exists() else {}
    pend = [v for v in videos.values() if (v["duration_s"] or 999) <= 180 and v["id"] not in res]
    pend.sort(key=lambda v: -v["views"])
    pend = pend[:int(os.environ.get("LIMITE", "100000"))]
    print(f"pendientes: {len(pend)}", file=sys.stderr)
    lista_f = "\n".join(f"- {k}: {d}" for k, d in FORMATOS.items())
    lock = threading.Lock()

    def procesar(k):
        lote = pend[k:k + tanda]
        txt_v = "\n".join(
            json.dumps({"i": i, "titulo": v["title"], "canal": v["channelTitle"], "seg": v["duration_s"],
                        "tags": v["tags"][:8], "descr": v["description"][:120]}, ensure_ascii=False)
            for i, v in enumerate(lote))
        body = {"contents": [{"parts": [{"text": PROMPT.format(formatos=lista_f, videos=txt_v)}]}],
                "generationConfig": {"temperature": 0, "responseMimeType": "application/json",
                                     "maxOutputTokens": 32000}}
        try:
            txt, uso, model = call(body)
            out = json.loads(txt)
        except (RuntimeError, json.JSONDecodeError) as e:
            print(f"lote {k}: error {str(e)[:200]}", file=sys.stderr)
            return
        with lock:
            for o in out:
                i = o.get("i")
                if isinstance(i, int) and 0 <= i < len(lote) and o.get("f") in FORMATOS:
                    res[lote[i]["id"]] = {kk: o.get(kk) for kk in ("f", "f2", "cara", "idioma", "sujeto")} | {"modelo": model}
            OUT.write_text(json.dumps(res, ensure_ascii=False))
            print(f"lote {k}: {len(out)} clasificados ({model}), total {len(res)}, tokens {uso.get('totalTokenCount')}", file=sys.stderr)

    with ThreadPoolExecutor(int(os.environ.get("HILOS", "4"))) as ex:
        list(ex.map(procesar, range(0, len(pend), tanda)))

if __name__ == "__main__":
    if not KEY:
        raise SystemExit("Falta GEMINI_API_KEY")
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 120)
