#!/usr/bin/env python3
"""
Módulo C: Gemini mira cada short desde su link de YouTube (no se descarga nada)
y devuelve su anatomía en JSON: gancho, tiempo para pensar, revelación, loop,
voz, música, textos, elementos visuales con riesgo de copyright, CTA.

Uso: GEMINI_API_KEY=... python3 research/gemini_shorts.py ID [ID ...]
     GEMINI_API_KEY=... python3 research/gemini_shorts.py --lista data/raw/gemini_shorts_targets.json
Salida: data/raw/gemini_shorts/<id>.json (reanudable: si existe, no lo repite)
"""
import json
import os
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "raw" / "gemini_shorts"
OUT.mkdir(parents=True, exist_ok=True)
KEY = os.environ.get("GEMINI_API_KEY")
MODELS = os.environ.get("GEMINI_MODELS", "gemini-flash-latest,gemini-3.5-flash,gemini-3.5-flash-lite").split(",")
URL = "https://generativelanguage.googleapis.com/v1beta/models/{}:generateContent"

PROMPT = """Sos analista de YouTube Shorts de fútbol. Mirá la imagen Y escuchá el audio de este short completo.
No inventes: si algo no se ve o no se oye, poné null. Tiempos en segundos desde el inicio, con un decimal.
Respondé SOLO con JSON válido, en español, con esta forma:
{
 "duracion_s": 0.0,
 "formato": "describí el formato en una frase (ej: adivinar jugador por emojis, 3 preguntas A/B/C, nombrá un jugador o te mojás...)",
 "n_preguntas_o_rondas": 0,
 "gancho": {"fin_s": 0.0, "que_se_ve": "...", "que_se_dice_o_texto": "texto exacto", "tipo": "pregunta directa | desafío ('solo el 1% sabe') | promesa | acción/sorpresa | otro"},
 "estructura": [{"inicio_s": 0.0, "fin_s": 0.0, "parte": "gancho | pregunta | tiempo_para_pensar | pista | revelacion | transicion | cierre | otro", "descripcion": "..."}],
 "tiempo_para_pensar_por_pregunta_s": 0.0,
 "cuenta_regresiva": {"hay": false, "estilo": "número, barra, reloj, sonido de tic-tac..."},
 "revelacion": {"como": "cómo se muestra la respuesta (foto, nombre, efecto, sonido)", "efecto_sonido": "..."},
 "cierre_y_loop": {"que_pasa_al_final": "...", "loop": "true si el final empalma con el inicio para que se repita sin cortar", "como_hace_el_loop": "..."},
 "cta": {"en_video": "texto/voz exacta de llamados a la acción ('comentá', 'seguime', 'parte 2') o null", "momento_s": null},
 "audio": {"voz": "ninguna | humana | IA/TTS probable", "idioma_y_acento": "...", "musica": "describí (tendencia/viral, de fondo, ninguna)", "efectos_de_sonido": ["..."]},
 "texto_en_pantalla": {"hay_texto": true, "subtitulos_de_voz": false, "estilo": "tipografía, color, contorno, posición", "idioma": "..."},
 "visual": {
   "fondo": "...",
   "persona_real_en_camara": false,
   "fotos_de_jugadores": false,
   "escudos_o_logos": false,
   "clips_de_partidos_o_transmisiones": false,
   "imagenes_generadas_por_ia_o_dibujos": false,
   "estilo_general": "...",
   "cambios_de_plano_aprox": 0
 },
 "dificultad_de_las_preguntas": "muy fácil | fácil | media | difícil",
 "invita_a_comentar_la_respuesta": true,
 "que_hace_que_funcione": "2 o 3 razones concretas basadas en lo que viste",
 "como_replicarlo_sin_cara_y_sin_clips": "cómo haría una versión con plantilla, sin persona ni clips de transmisión, o null si no se puede"
}"""


def call(vid):
    body = {
        "contents": [{"parts": [
            {"file_data": {"file_uri": f"https://www.youtube.com/watch?v={vid}"}},
            {"text": PROMPT},
        ]}],
        "generationConfig": {"temperature": 0.1, "responseMimeType": "application/json", "maxOutputTokens": 12000},
    }
    errores = []
    for ronda in range(3):
        for model in MODELS:
            try:
                r = requests.post(URL.format(model), headers={"x-goog-api-key": KEY}, json=body, timeout=600)
            except requests.RequestException as e:
                errores.append(f"{model} {e}")
                continue
            if r.status_code == 200:
                d = r.json()
                parts = d["candidates"][0].get("content", {}).get("parts", [])
                return "".join(p.get("text", "") for p in parts if not p.get("thought")), d.get("usageMetadata", {}), model
            errores.append(f"{model} HTTP {r.status_code}: {r.text[:160]}")
            print(f"  {vid}: {errores[-1]}", file=sys.stderr)
            if r.status_code == 400:  # video privado / no disponible: no tiene sentido reintentar
                return None, {}, errores[-1]
        time.sleep(40 * (ronda + 1))
    return None, {}, " | ".join(errores[-3:])


def main(ids):
    for vid in ids:
        dest = OUT / f"{vid}.json"
        if dest.exists() and json.loads(dest.read_text()).get("analisis"):
            continue
        txt, uso, model = call(vid)
        res = {"video_id": vid, "modelo": model, "uso": uso}
        if txt is None:
            res["error"] = model
        else:
            try:
                res["analisis"] = json.loads(txt)
            except json.JSONDecodeError:
                res["analisis"], res["crudo"] = None, txt
        dest.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"{vid}: ok={bool(res.get('analisis'))} {model} tokens={uso.get('totalTokenCount')}", file=sys.stderr)


if __name__ == "__main__":
    if not KEY:
        raise SystemExit("Falta GEMINI_API_KEY")
    a = sys.argv[1:]
    if a and a[0] == "--lista":
        a = json.loads(Path(a[1]).read_text())
    main(a)
