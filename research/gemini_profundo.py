#!/usr/bin/env python3
"""
Análisis visual PROFUNDO de shorts virales (y de los nuestros, con la misma vara), para replicar en serio:
tipo y calidad de imagen, gancho de 0 a 3 s cada medio segundo, cada toma con su efecto y transición, textos exactos,
audio, estructura narrativa, por qué se comenta/comparte, y si se puede hacer sin material ajeno.

Uso: GEMINI_API_KEY=... python3 research/gemini_profundo.py lista.json [carpeta_salida]
lista.json: [{"id": "...", "canal": "...", "vistas": 123, "titulo": "..."}]
Salida: data/raw/gemini_profundo/<id>.json
"""
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

KEY = os.environ.get("GEMINI_API_KEY")
MODELS = ["gemini-3.5-flash", "gemini-3.6-flash", "gemini-flash-latest", "gemini-3.5-flash-lite"]
URL = "https://generativelanguage.googleapis.com/v1beta/models/{}:generateContent"
PROMPT = """Sos editor senior de YouTube Shorts y director de arte. Este short se llama "{titulo}" ({canal}) y tiene {vistas} vistas.
Miralo y escuchalo COMPLETO, cuadro por cuadro. Sé concreto y crítico, nada genérico: si algo no se ve o no se oye, poné null.
No inventes nombres de canciones: si no la reconocés con seguridad, describila. Respondé SOLO JSON en español:
{{
 "tipo_de_imagen": "transmisión real de partido / video generado con IA (decí el estilo) / animación 3D / fotos con movimiento / videojuego / gráficos por código / mezcla (detallá)",
 "calidad_imagen_1a10": 0,
 "por_que_esa_calidad": "nitidez, iluminación, color, consistencia, si se ve barato o premium y por qué",
 "gancho_0_a_3s": [{{"t": "0.0", "en_pantalla": "...", "texto": "...", "sonido": "...", "movimiento_o_efecto": "..."}},
                   {{"t": "0.5"}}, {{"t": "1.0"}}, {{"t": "1.5"}}, {{"t": "2.0"}}, {{"t": "2.5"}}, {{"t": "3.0"}}],
 "por_que_el_gancho_frena_el_scroll": "concreto",
 "tomas": [{{"desde": 0.0, "hasta": 0.0, "contenido": "...", "encuadre": "primer plano/medio/general", "camara": "fija/zoom in/zoom out/paneo/temblor/cámara lenta/aceleración",
            "transicion_de_entrada": "corte seco/flash/zoom/barrido/fundido/ninguna", "efectos": ["..."]}}],
 "cortes_por_10s": 0,
 "sincronia_con_la_musica": "los cortes/efectos caen en el beat? ejemplos con segundos",
 "textos_en_pantalla": [{{"t": "0.0", "texto": "exacto", "estilo": "fuente, color, borde, posición, animación"}}],
 "audio": {{"musica": "género, bpm aprox, si es tendencia, nombre solo si es seguro", "efectos": ["..."], "voz": "hay voz? qué dice?", "momento_clave_de_audio": "drop, silencio, grito… y en qué segundo"}},
 "estructura": "planteo → tensión → remate: qué pasa en cada parte y en qué segundos",
 "giro_o_sorpresa": "qué no se espera el espectador y cuándo",
 "final_y_loop": "cómo termina; si engancha con el inicio para que se repita",
 "emocion_que_busca": "risa / nostalgia / bronca / asombro / ternura / debate…",
 "por_que_comentan": "qué pregunta o pelea dispara en comentarios",
 "por_que_comparten_o_repiten": "concreto",
 "tres_razones_por_las_que_exploto": ["...", "...", "..."],
 "replicable_sin_material_ajeno": {{"se_puede": true, "como": "IA de video (cuál estilo), 3D, código, fotos libres, etc.", "dificultad_1a10": 0, "que_se_pierde_si_no_usamos_ese_material": "..."}},
 "receta_para_hacerlo_igual_o_mejor": ["paso 1 concreto", "paso 2", "..."],
 "puntaje_produccion_1a10": 0,
 "puntaje_idea_1a10": 0
}}"""


def subir(ruta):
    """Sube un mp4 local a la Files API de Gemini y espera a que esté ACTIVE (para analizar nuestros videos igual)."""
    datos = Path(ruta).read_bytes()
    r = requests.post("https://generativelanguage.googleapis.com/upload/v1beta/files", headers={
        "x-goog-api-key": KEY, "X-Goog-Upload-Protocol": "resumable", "X-Goog-Upload-Command": "start",
        "X-Goog-Upload-Header-Content-Length": str(len(datos)), "X-Goog-Upload-Header-Content-Type": "video/mp4",
        "Content-Type": "application/json"}, json={"file": {"display_name": Path(ruta).name}}, timeout=60)
    up = r.headers["x-goog-upload-url"]
    f = requests.post(up, headers={"X-Goog-Upload-Offset": "0", "X-Goog-Upload-Command": "upload, finalize"},
                      data=datos, timeout=300).json()["file"]
    while f.get("state") == "PROCESSING":
        time.sleep(5)
        f = requests.get("https://generativelanguage.googleapis.com/v1beta/" + f["name"], headers={"x-goog-api-key": KEY}, timeout=60).json()
    return f["uri"]


def uno(o, out):
    dst = out / f"{o['id']}.json"
    if dst.exists():
        return
    uri = subir(o["archivo"]) if o.get("archivo") else f"https://www.youtube.com/watch?v={o['id']}"
    parte = {"file_data": {"file_uri": uri, "mime_type": "video/mp4"}} if o.get("archivo") else {"file_data": {"file_uri": uri}}
    body = {"contents": [{"parts": [parte,
                                    {"text": PROMPT.format(titulo=o.get("titulo", ""), canal=o.get("canal", ""), vistas=o.get("vistas", "?"))}]}],
            "generationConfig": {"temperature": 0.2, "responseMimeType": "application/json"}}
    for ronda in range(4):
        for m in MODELS:
            try:
                r = requests.post(URL.format(m), headers={"x-goog-api-key": KEY}, json=body, timeout=400)
            except requests.RequestException:
                continue
            if r.status_code == 200:
                try:
                    a = json.loads("".join(p.get("text", "") for p in r.json()["candidates"][0]["content"]["parts"]))
                    a = a[0] if isinstance(a, list) else a
                except Exception:
                    continue
                dst.write_text(json.dumps({**o, "modelo": m, "analisis": a}, ensure_ascii=False, indent=1))
                print("ok", o.get("canal"), o["id"], flush=True)
                return
        time.sleep(15 * (ronda + 1))
    print("falló", o["id"], flush=True)


if __name__ == "__main__":
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(__file__).resolve().parent.parent / "data" / "raw" / "gemini_profundo"
    out.mkdir(parents=True, exist_ok=True)
    lista = json.loads(Path(sys.argv[1]).read_text())
    with ThreadPoolExecutor(4) as ex:
        list(ex.map(lambda o: uno(o, out), lista))
