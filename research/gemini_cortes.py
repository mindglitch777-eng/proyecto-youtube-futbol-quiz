#!/usr/bin/env python3
"""
Análisis de cortes de un video de YouTube con la API de Gemini, en trozos de
60 s (videoMetadata startOffset/endOffset), a 2 cuadros por segundo.

Por cada trozo guarda la respuesta cruda y un chequeo de desfase:
  - todos los tiempos deben caer dentro del trozo pedido
  - los títulos de era que ve Gemini se comparan con los capítulos que
    publicó el creador en la descripción (referencia independiente)

Uso: GEMINI_API_KEY=... python3 gemini_cortes.py <video_id> <duracion_s>
Salida: research/analisis_gemini/<video_id>_trozos.json
"""
import json
import os
import sys
import time
from pathlib import Path

import requests

KEY = os.environ.get("GEMINI_API_KEY")
MODELS = os.environ.get("GEMINI_MODELS", "gemini-3.8-flash,gemini-3.5-flash-lite,gemini-flash-latest").split(",")
URL = "https://generativelanguage.googleapis.com/v1beta/models/{}:generateContent"
OUT = Path(__file__).parent / "analisis_gemini"
TROZO = 60

PROMPT = """Estás viendo SOLO el tramo del video que va del segundo {a} al segundo {b} del video completo (duración total {total} s).
Reportá TODOS los tiempos en segundos absolutos desde el inicio del video completo (no desde el inicio del tramo), con un decimal, y siempre entre {a} y {b}.
No inventes: si algo no se ve o no se oye, poné null. Respondé en español.

Listá CADA cambio de imagen (corte o transición a un plano nuevo) del tramo, en orden. Para el primer elemento usá el plano que está en pantalla en el segundo {a}.
Devolvé SOLO este JSON:
{{
 "control": {{
   "primeras_palabras_del_tramo": "texto exacto de lo primero que se oye",
   "segundo_primeras_palabras": 0.0,
   "texto_en_pantalla_en_el_primer_segundo": "texto exacto o null",
   "ultimas_palabras_del_tramo": "texto exacto",
   "segundo_ultimas_palabras": 0.0
 }},
 "planos": [
  {{
   "inicio_s": 0.0,
   "fin_s": 0.0,
   "tipo": "ilustración | mapa | gráfico | stickman | animación 3D | video real | texto | otro",
   "que_se_ve": "descripción corta",
   "movimiento_camara": "zoom in | zoom out | paneo | fijo | otro",
   "transicion_de_entrada": "corte seco | fundido | deslizamiento | sacudida | otra",
   "texto_en_pantalla": [{{"texto": "palabra exacta", "aparece_s": 0.0}}],
   "efectos_de_sonido": [{{"efecto": "cuál", "s": 0.0, "en_la_frase": "frase que se dice en ese momento"}}],
   "musica": "sube | baja | se corta | entra | sigue igual | sin música",
   "narracion": "lo que se dice durante este plano, textual"
  }}
 ],
 "tier_list": [{{"aparece_s": 0.0, "hasta_s": 0.0, "descripcion": "cómo es el medidor/tabla y qué se agrega"}}],
 "titulos_de_era": [{{"texto": "nombre de la era tal como aparece", "aparece_s": 0.0}}]
}}"""


def call(body):
    errs = []
    for ronda in range(3):
        for m in MODELS:
            r = requests.post(URL.format(m), headers={"x-goog-api-key": KEY}, json=body, timeout=600)
            if r.status_code == 200:
                d = r.json()
                parts = d["candidates"][0].get("content", {}).get("parts", [])
                return "".join(p.get("text", "") for p in parts), d.get("usageMetadata", {}), m
            errs.append(f"{m} {r.status_code}: {r.json().get('error', {}).get('message', '')[:90]}")
            print("  " + errs[-1], file=sys.stderr)
        time.sleep(45 * (ronda + 1))
    raise RuntimeError(" | ".join(errs[-3:]))


def main(vid, total):
    dest = OUT / f"{vid}_trozos.json"
    res = json.loads(dest.read_text()) if dest.exists() else {"video_id": vid, "duracion_s": total, "trozos": {}}
    for a in range(0, total, TROZO):
        b = min(a + TROZO, total)
        k = f"{a}-{b}"
        if k in res["trozos"] and res["trozos"][k].get("datos"):
            continue
        body = {"contents": [{"parts": [
            {"fileData": {"fileUri": f"https://www.youtube.com/watch?v={vid}"},
             "videoMetadata": {"startOffset": f"{a}s", "endOffset": f"{b}s", "fps": 2}},
            {"text": PROMPT.format(a=a, b=b, total=total)}]}],
            "generationConfig": {"temperature": 0, "responseMimeType": "application/json", "maxOutputTokens": 16000,
                                 "mediaResolution": "MEDIA_RESOLUTION_HIGH"}}
        try:
            txt, uso, model = call(body)
        except RuntimeError as e:
            res["trozos"][k] = {"error": str(e)}
            dest.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
            print(f"{k}: ERROR {e}", file=sys.stderr)
            continue
        try:
            datos = json.loads(txt)
        except json.JSONDecodeError:
            datos = None
        # chequeo de desfase: tiempos fuera del tramo
        fuera = []
        if datos:
            for p in datos.get("planos", []):
                for t in (p.get("inicio_s"), p.get("fin_s")):
                    if isinstance(t, (int, float)) and not (a - 1 <= t <= b + 1):
                        fuera.append(t)
        res["trozos"][k] = {"modelo": model, "uso": uso, "datos": datos, "crudo": None if datos else txt,
                            "tiempos_fuera_del_tramo": fuera}
        dest.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"{k}: {model} planos={len(datos.get('planos', [])) if datos else 'JSON inválido'} fuera={fuera[:5]} tokens={uso.get('totalTokenCount')}", file=sys.stderr)


if __name__ == "__main__":
    if not KEY:
        raise SystemExit("Falta GEMINI_API_KEY")
    main(sys.argv[1], int(sys.argv[2]))
