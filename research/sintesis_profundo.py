#!/usr/bin/env python3
"""Resumen compacto de data/raw/gemini_profundo/*.json para leer y comparar (virales vs nuestros)."""
import json
import statistics
import sys
from pathlib import Path

D = Path(__file__).resolve().parent.parent / "data" / "raw" / "gemini_profundo"


def corto(a, k, n=220):
    v = a.get(k)
    return (json.dumps(v, ensure_ascii=False) if not isinstance(v, str) else v or "")[:n]


def main(filtro=""):
    filas = []
    for p in sorted(D.glob("*.json")):
        d = json.loads(p.read_text()); a = d["analisis"]
        if filtro and filtro not in d["id"]:
            continue
        g = a.get("gancho_0_a_3s") or [{}]
        rep = a.get("replicable_sin_material_ajeno") or {}
        filas.append(d)
        print(f"\n### {d.get('canal')} · {d.get('vistas')} vistas · video #{d.get('video_del_hit', '-')} · {d['id']}\n{d.get('titulo', '')[:90]}")
        print(f"- imagen: {corto(a, 'tipo_de_imagen', 120)} | calidad {a.get('calidad_imagen_1a10')} | prod {a.get('puntaje_produccion_1a10')} | idea {a.get('puntaje_idea_1a10')} | cortes/10s {a.get('cortes_por_10s')}")
        print(f"- 0.0s: {g[0].get('en_pantalla')} / texto: {g[0].get('texto')} / sonido: {g[0].get('sonido')}")
        print(f"- frena el scroll: {corto(a, 'por_que_el_gancho_frena_el_scroll', 200)}")
        print(f"- estructura: {corto(a, 'estructura', 300)}")
        print(f"- giro: {corto(a, 'giro_o_sorpresa', 180)} | final: {corto(a, 'final_y_loop', 140)}")
        print(f"- emoción: {corto(a, 'emocion_que_busca', 80)} | comentan: {corto(a, 'por_que_comentan', 160)}")
        print(f"- razones: {corto(a, 'tres_razones_por_las_que_exploto', 300)}")
        print(f"- sin material ajeno: {rep.get('se_puede')} · {str(rep.get('como'))[:160]} · dificultad {rep.get('dificultad_1a10')}")
        print(f"- audio: {corto(a.get('audio') or {}, 'musica', 140)}")
    for clave in ("calidad_imagen_1a10", "puntaje_produccion_1a10", "puntaje_idea_1a10", "cortes_por_10s"):
        vals = [float(d["analisis"].get(clave)) for d in filas if isinstance(d["analisis"].get(clave), (int, float))]
        if vals:
            print(f"\nmediana {clave}: {statistics.median(vals):.1f} (n={len(vals)})")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "")
