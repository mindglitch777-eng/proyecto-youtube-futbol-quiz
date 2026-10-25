#!/usr/bin/env python3
"""Arma produccion/salida/<lote>_CALENDARIO.md con el plan de publicación del lote. Uso: calendario_lote.py lote1"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
lote = sys.argv[1]
filas = []
for g_path in sorted((ROOT / "guiones").glob(f"{lote}_*.json")):
    g = json.loads(g_path.read_text())
    pares = ", ".join(f"{r['nombre_a']}+{r['nombre_b']}" for r in g["rondas"])
    filas.append(f"| {g['publicar']} | `{g['id']}` | {g['tema']} | {g['titulos'][0]} | {pares} | {g['comentario_fijado']} |")
txt = f"""# {lote}: calendario de publicación

2 por día, **10:00 y 23:00 hora Argentina**. Cada carpeta `produccion/salida/<id>/` tiene `short_con_beat.mp4`, `short_sin_beat.mp4` y `SUBIR.txt`.

| Cuándo | Video | Tema | Título recomendado | Fusiones | Comentario para fijar |
|---|---|---|---|---|---|
""" + "\n".join(filas) + """

## Rutina de cada publicación (5 minutos)
1. Subí `short_sin_beat.mp4` y en el editor de Shorts sumá un sonido de tendencia (phonk o ritmo rápido) con el volumen al 30–40%.
   Si no hay ninguno bueno, subí `short_con_beat.mp4` tal cual.
2. Título: el A de `SUBIR.txt`. Descripción y hashtags: copiar y pegar. Audiencia: "No es para niños".
3. Apenas sale: **fijá el comentario** y **respondé los primeros 5 comentarios** en la primera hora (cada respuesta suma un comentario más).
4. A las 48 h, anotá en `produccion/registro.csv`: vistas, % "vieron vs. deslizaron", retención media, comentarios.

## Qué mirar al final de la semana
- **Vieron vs. deslizaron** por tema: duplicar los 2 temas que más retienen.
- **Retención media**: si pasa el 100%, el loop funciona; si cae antes de la ronda 2, el gancho no alcanza.
- **Comentarios con puntaje** ("6/8"): señal de que el formato engancha.
"""
out = ROOT / "salida" / f"{lote}_CALENDARIO.md"
out.parent.mkdir(exist_ok=True)
out.write_text(txt, encoding="utf-8")
print(txt[:1500])
