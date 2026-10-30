#!/usr/bin/env python3
"""
Etapa 2 · ANÁLISIS: Gemini mira cada viral del radar (link oficial de YouTube, video + audio) segundo a segundo
y lo clasifica en nuestro catálogo de formatos (o lo marca como formato NUEVO para construir).
Además procesa la bandeja de grabaciones (pipeline/grabaciones/*.mp4): medición cuadro por cuadro + Gemini.
Salida: datos/analisis.json
"""
import json
import shutil
import sys
from pathlib import Path

from comun import CONFIG, PIPE, RAIZ, cargar, etapa, gemini, gemini_subir, guardar

sys.path.insert(0, str(RAIZ / "research"))

CATALOGO = {k: v["nombre"] for k, v in CONFIG["formatos"].items()}
PROMPT = """Sos editor senior de YouTube Shorts. Mirá y escuchá este short de fútbol COMPLETO ("{titulo}", {vistas} vistas).
Nuestro catálogo de formatos: {catalogo}. Respondé SOLO JSON en español:
{{"formato": "una clave del catálogo si es esa mecánica, o 'nuevo'",
 "nombre_formato": "nombre corto de la mecánica (ej: STOP CHALLENGE, FIND, quiz de caras, carrera, parodia IA...)",
 "mecanica": "qué hace exactamente el video, en 1-2 frases",
 "cuadro_0": "qué se ve en el primer cuadro (layout, colores, textos, caras)",
 "linea_de_tiempo": [{{"t": "0.0", "pantalla": "...", "sonido": "..."}}],
 "gancho": "por qué frena el scroll en el primer segundo",
 "dopamina": ["cada recurso que da recompensa: sonidos, efectos, sorpresas, cuándo"],
 "audio": "música/tendencia y efectos",
 "loop": "si empalma con el inicio y cómo",
 "por_que_comentan": "qué escribe la gente",
 "material": "fotos libres / código / IA de video / clips ajenos / filmación",
 "replicable_con_codigo": true,
 "como_lo_mejoramos": ["3 ideas concretas para hacerlo más adictivo"]}}
La línea de tiempo va cada 0,5 s hasta el final."""


def main():
    etapa("analisis", "en_curso")
    radar = cargar("radar.json", {"virales": []})
    previos = {a["id"]: a for a in cargar("analisis.json", {"virales": []}).get("virales", [])}
    salida, n = [], CONFIG["radar"]["analizar_top"]
    for v in radar["virales"][:n]:
        if v["id"] in previos:
            salida.append(previos[v["id"]]); continue
        a = gemini([{"file_data": {"file_uri": f"https://www.youtube.com/watch?v={v['id']}"}},
                    {"text": PROMPT.format(titulo=v["titulo"], vistas=v["vistas"], catalogo=json.dumps(CATALOGO, ensure_ascii=False))}])
        if a:
            salida.append({**{k: v[k] for k in ("id", "titulo", "canal", "vistas", "vistas_por_hora", "canal_nuevo", "dur")}, "analisis": a})
            print("ok", v["id"], a.get("formato"), a.get("nombre_formato"), flush=True)

    # bandeja de grabaciones: lo que grabaste del celular, medido cuadro por cuadro
    grab = []
    bandeja = PIPE / "grabaciones"; hechas = bandeja / "procesadas"
    for mp4 in sorted(bandeja.glob("*.mp4")):
        from medir_gancho import MODELO, W, H, medir  # noqa: E402
        import cv2
        det = cv2.FaceDetectorYN.create(str(MODELO), "", (W, H), 0.6)
        medida = medir(dict(id=mp4.stem, ruta=str(mp4), grupo="grabacion", recorte=[0, 0.11, 0.87, 0.88]), det)
        uri = gemini_subir(mp4)
        a = gemini([{"file_data": {"mime_type": "video/mp4", "file_uri": uri}},
                    {"text": PROMPT.format(titulo=mp4.stem, vistas="?", catalogo=json.dumps(CATALOGO, ensure_ascii=False))}]) if uri else None
        grab.append(dict(id=mp4.stem, medida=medida, analisis=a))
        hechas.mkdir(parents=True, exist_ok=True); shutil.move(str(mp4), hechas / mp4.name)

    conteo = {}
    for s in salida:
        f = s["analisis"].get("formato", "nuevo"); conteo[f] = conteo.get(f, 0) + 1
    nuevos = [dict(id=s["id"], nombre=s["analisis"].get("nombre_formato"), mecanica=s["analisis"].get("mecanica"), vistas=s["vistas"],
                   replicable=s["analisis"].get("replicable_con_codigo")) for s in salida if s["analisis"].get("formato") == "nuevo"]
    guardar("analisis.json", dict(virales=salida, grabaciones=grab, conteo_formatos=conteo, formatos_nuevos=nuevos))
    etapa("analisis", "ok", analizados=len(salida), grabaciones=len(grab), por_formato=conteo,
          formatos_nuevos=[f"{x['nombre']} ({x['vistas']:,} vistas)" for x in nuevos[:6]])


if __name__ == "__main__":
    main()
