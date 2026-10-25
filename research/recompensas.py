#!/usr/bin/env python3
"""
¿Qué RECIBE el espectador a cambio de mirar? Gemini (texto) etiqueta la recompensa psicológica principal,
la acción que se le pide en comentarios y si es serie, para cruzarlo con velocidad y vistas.

Uso: GEMINI_API_KEY=... python3 research/recompensas.py   (etiqueta: velocidad <=14 días + nichos + muestra de fútbol)
Salida: data/raw/gemini_recompensas.json {video_id: {r, r2, accion, serie, m}}
"""
import json
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import mecanicas as MC  # noqa: E402

ROOT = MC.ROOT
RAW = MC.RAW
OUT = RAW / "gemini_recompensas.json"

RECOMPENSAS = {
    "logro_acierto": "ponerse a prueba y sentir que acertó / 'solo el 1% puede'",
    "curiosidad_revelacion": "quedarse para ver una revelación o resultado al final",
    "satisfaccion_transformacion": "ver algo cambiar o transformarse (antes/después, morph, evolución, oddly satisfying)",
    "suspenso_competencia": "ver quién gana una carrera, batalla o simulación (no decide el espectador)",
    "nostalgia": "recordar el pasado, 'qué tiempos'",
    "identidad_tribu": "orgullo de país, club o grupo; 'mi equipo'",
    "opinion_debate": "dar su opinión, discutir, polémica, elegir",
    "humor": "reírse",
    "asombro_dato": "dato sorprendente, récord, 'no sabías esto'",
    "emocion_historia": "historia emotiva o dramática",
    "espectaculo_habilidad": "mirar habilidad, goles, jugadas, talento",
    "aprender": "aprender algo útil",
}
ACCIONES = ["puntaje", "respuesta", "opinion", "nada"]

PROMPT = """Para cada YouTube Short decidí qué RECIBE psicológicamente el espectador a cambio de mirarlo hasta el final.
Recompensas (usá solo estos códigos):
{rec}
Mecánicas posibles: {mec}
Para cada video devolvé {{"i": índice, "r": recompensa principal, "r2": secundaria o null,
"accion": qué se le pide comentar: "puntaje" (cuántas acertó), "respuesta" (la respuesta), "opinion", o "nada",
"serie": true si es parte de una serie numerada (part/day/episode N), "m": código de mecánica}}.
Basate en título, tags y descripción. Respondé SOLO con un array JSON.

Videos:
{videos}"""


def main(ids):
    videos = json.loads((RAW / "videos.json").read_text())
    res = json.loads(OUT.read_text()) if OUT.exists() else {}
    pend = [videos[i] for i in dict.fromkeys(ids) if i in videos and i not in res]
    print("pendientes", len(pend))
    rec = "\n".join(f"- {k}: {d}" for k, d in RECOMPENSAS.items())
    lock = threading.Lock()

    def lote(k):
        L = pend[k:k + 100]
        txt = "\n".join(json.dumps({"i": i, "titulo": v["title"], "canal": v["channelTitle"], "tags": v["tags"][:8],
                                    "descr": v["description"][:150]}, ensure_ascii=False) for i, v in enumerate(L))
        body = {"contents": [{"parts": [{"text": PROMPT.format(rec=rec, mec=", ".join(MC.MECANICAS), videos=txt)}]}],
                "generationConfig": {"temperature": 0, "responseMimeType": "application/json", "maxOutputTokens": 32000}}
        try:
            t, _ = MC.call(body)
            out = json.loads(t)
        except Exception as e:
            print("lote", k, "error", str(e)[:100]); return
        with lock:
            for o in out:
                i = o.get("i")
                if isinstance(i, int) and 0 <= i < len(L) and o.get("r") in RECOMPENSAS:
                    res[L[i]["id"]] = {"r": o["r"], "r2": o.get("r2"), "accion": o.get("accion"),
                                       "serie": o.get("serie"), "m": o.get("m")}
            OUT.write_text(json.dumps(res, ensure_ascii=False))
            print("lote", k, "ok", len(res), flush=True)

    with ThreadPoolExecutor(4) as ex:
        list(ex.map(lote, range(0, len(pend), 100)))


if __name__ == "__main__":
    import pandas as pd
    vel = pd.read_csv(ROOT / "data/processed/velocidad.csv")
    ids = list(vel[vel.edad_dias <= 14].id)
    ids += list(json.loads((RAW / "gemini_mecanicas.json").read_text()))
    main(ids)
