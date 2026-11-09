#!/usr/bin/env python3
"""
Gemini mira shorts puntuales (link oficial de YouTube) y los describe para REPLICARLOS con código.
Entrada: pipeline/analizar_ids.json [{"id", "titulo", "vistas", ...}]. Salida: pipeline/datos/analisis_tendencias.json
Corre en GitHub Actions (workflow analizar.yml, con el secreto GEMINI_API_KEY).
"""
import json

from comun import PIPE, cargar, gemini, guardar

PROMPT = """Sos editor senior de YouTube Shorts y programador de animaciones. Mirá y escuchá este short COMPLETO ("{titulo}", {vistas} vistas).
Lo queremos replicar con código (Python + imágenes PNG recortadas de jugadores, sin filmar ni usar clips ajenos).
Respondé SOLO JSON en español:
{{"nombre_formato": "nombre corto", "mecanica": "qué hace exactamente, paso a paso",
 "que_hace_el_espectador": "pausar / adivinar / elegir / solo mirar...",
 "cuadro_0": "qué se ve en el primer cuadro: layout exacto (qué hay arriba, al medio, abajo), colores, textos, caras, tamaños",
 "linea_de_tiempo": [{{"t": "0.0", "pantalla": "...", "sonido": "..."}}],
 "duracion_s": 0, "loop": "si empalma con el inicio y cómo",
 "gancho": "por qué frena el scroll", "dopamina": ["recursos de recompensa y cuándo"],
 "audio": "música/tendencia y efectos", "por_que_comentan": "qué escribe la gente",
 "assets_necesarios": ["lista de imágenes/sonidos que hacen falta"],
 "replicable_con_codigo": true, "dificultad_1a5": 0,
 "receta_para_programarlo": ["pasos concretos con medidas y tiempos para animarlo con código"],
 "como_lo_hacemos_mejor": ["3 ideas para hacerlo más adictivo y original"]}}
La línea de tiempo va cada 0,5 s hasta el final."""


def main():
    pedido = json.loads((PIPE / "analizar_ids.json").read_text())
    previos = {a["id"]: a for a in cargar("analisis_tendencias.json", [])}
    for v in pedido:
        if v["id"] in previos:
            continue
        a = gemini([{"file_data": {"file_uri": f"https://www.youtube.com/watch?v={v['id']}"}},
                    {"text": PROMPT.format(titulo=v["titulo"], vistas=v["vistas"])}])
        if isinstance(a, list):                                                # a veces Gemini devuelve [ {...} ]
            a = next((x for x in a if isinstance(x, dict)), None)
        if a:
            previos[v["id"]] = {**v, "analisis": a}
            print("ok", v["id"], a.get("nombre_formato"), flush=True)
            guardar("analisis_tendencias.json", list(previos.values()))
    guardar("analisis_tendencias.json", list(previos.values()))


if __name__ == "__main__":
    main()
