#!/usr/bin/env python3
"""
Analiza videos de YouTube con la API de Gemini (le pasa el link; Google mira
el video de su lado, no se baja nada). Lee la clave de GEMINI_API_KEY (nunca
se guarda en el repo).

Por video guarda en research/analisis_gemini/<id>.json:
  - transcripcion: lo que dice la narración, con tiempos (la hace Gemini
    escuchando el audio, NO son los subtítulos oficiales de YouTube)
  - analisis: gancho, bloques, cierre, ritmo visual, estilo, textos en pantalla

Uso: python3 gemini_video.py <video_id> [<video_id> ...]
"""
import json
import os
import sys
import time
from pathlib import Path

import requests

KEY = os.environ.get("GEMINI_API_KEY")
# se prueban en orden; si uno está saturado (503) o sin cupo (429) se pasa al siguiente
MODELS = os.environ.get("GEMINI_MODELS", "gemini-flash-latest,gemini-3.5-flash-lite,gemini-3.5-flash,gemini-3.8-flash").split(",")
OUT = Path(__file__).parent / "analisis_gemini"
OUT.mkdir(exist_ok=True)
URL = "https://generativelanguage.googleapis.com/v1beta/models/{}:generateContent"

PROMPT_TRANSCRIPCION = """Transcribe the narration of this video VERBATIM, in its original language, with no translation and no summary.
Format: one line per sentence or short group of sentences, each starting with the timestamp [MM:SS].
If there is no speech in a segment, write [MM:SS] (sin narración: <what is shown in 5 words>).
Do not add anything else."""

PROMPT_ANALISIS = """Sos un analista de videos de YouTube. Analizá este video mirando la imagen Y escuchando el audio.
Respondé SOLO con JSON válido (sin markdown) con esta forma exacta, en español:
{
 "gancho_0_30s": {"que_se_dice": "...", "que_se_ve": "...", "tecnica": "pregunta | paradoja | escena en 2da persona | dato impactante | promesa | otra", "momento_en_que_se_repite_la_promesa_del_titulo_s": 0},
 "bloques": [{"inicio": "MM:SS", "fin": "MM:SS", "tema": "...", "como_abre": "...", "como_cierra_o_engancha_al_siguiente": "..."}],
 "cierre": {"inicio": "MM:SS", "que_hace": "...", "pide_suscripcion_o_like": true, "pregunta_a_comentarios": true},
 "visual": {
   "estilo": "descripción precisa del estilo de imagen (ilustración IA, stickman, 3D, fotorealista, stock, mapas...)",
   "personaje_recurrente": "...",
   "tipo_de_movimiento": "imágenes fijas con zoom/paneo | animación real | video | mezcla",
   "cambios_de_imagen_aprox_por_minuto": 0,
   "duracion_tipica_de_cada_imagen_s": 0,
   "textos_en_pantalla": "si hay subtítulos, títulos, flechas, números; cómo son",
   "mapas_graficos_o_diagramas": "..."
 },
 "audio": {"voz": "humana o IA probable; género; ritmo (palabras/min aprox); tono", "musica": "...", "efectos_de_sonido": "..."},
 "tecnicas_de_retencion": ["lista concreta de recursos que usa para que no te vayas, con el minuto"],
 "frases_cortas_de_ejemplo": ["3 a 5 frases textuales cortas (máx 15 palabras) que muestren el estilo del guion"],
 "por_que_creo_que_se_hizo_viral": "opinión breve basada en lo que viste",
 "cara_humana_real_en_camara": false
}"""


def call(vid, prompt, max_tokens):
    body = {
        "contents": [{"parts": [
            {"file_data": {"file_uri": f"https://www.youtube.com/watch?v={vid}"}},
            {"text": prompt},
        ]}],
        "generationConfig": {"temperature": 0.2, "maxOutputTokens": max_tokens},
    }
    errores = []
    for ronda in range(3):
        for model in MODELS:
            r = requests.post(URL.format(model), headers={"x-goog-api-key": KEY}, json=body, timeout=600)
            if r.status_code == 200:
                d = r.json()
                parts = d["candidates"][0].get("content", {}).get("parts", [])
                return "".join(p.get("text", "") for p in parts), d.get("usageMetadata", {}), model
            msg = r.json().get("error", {}).get("message", r.text)[:200]
            errores.append(f"{model} HTTP {r.status_code}: {msg[:100]}")
            print(f"  {vid}: {errores[-1]}", file=sys.stderr)
        time.sleep(60 * (ronda + 1))
    raise SystemExit(f"{vid}: ningún modelo respondió. " + " | ".join(errores[-4:]))


def main(ids):
    for vid in ids:
        dest = OUT / f"{vid}.json"
        res = json.loads(dest.read_text()) if dest.exists() else {"video_id": vid}
        if "transcripcion" not in res:
            txt, uso, model = call(vid, PROMPT_TRANSCRIPCION, 16000)
            res["transcripcion"], res["uso_transcripcion"], res["modelo_transcripcion"] = txt, uso, model
            dest.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
            print(f"{vid}: transcripción {len(txt)} caracteres, tokens {uso.get('totalTokenCount')}", file=sys.stderr)
        if "analisis" not in res:
            txt, uso, model = call(vid, PROMPT_ANALISIS, 8000)
            res["modelo_analisis"] = model
            t = txt.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            try:
                res["analisis"] = json.loads(t)
            except json.JSONDecodeError:
                res["analisis_texto_crudo"] = txt
                res["analisis"] = None
            res["uso_analisis"] = uso
            dest.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
            print(f"{vid}: análisis ok={res['analisis'] is not None}, tokens {uso.get('totalTokenCount')}", file=sys.stderr)


if __name__ == "__main__":
    if not KEY:
        raise SystemExit("Falta GEMINI_API_KEY")
    main(sys.argv[1:])
