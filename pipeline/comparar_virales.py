#!/usr/bin/env python3
"""
COMPARAR CON LOS VIRALES (21/11, CEO: "copiar bien la ejecución de lo que ya explotó"). Sin Claude: Gemini mira, cuadro por
cuadro, NUESTRO video y el VIRAL del mismo formato de otro canal, y dice exactamente qué cambia (primer segundo, duración, ritmo,
tamaño de caras, dificultad, texto, sonido, final/loop, título). No copia contenido ajeno: saca la receta de ejecución.
Salida: reports/29_comparacion_virales.md + pipeline/datos/comparacion_virales.json
"""
import json

from comun import RAIZ, gemini, guardar

PARES = [
    dict(formato="FIT ALL", nuestro="AMH-L0FzyfE", nuestro_vistas=10137, nuestro_peor="OPrij2qKXXw", peor_vistas=772,
         viral="vSCSgT8so3c", viral_vistas=12614559, canal="RyukX (canal de 2 semanas)"),
    dict(formato="DRESS UP", nuestro="CCJLnw_evdY", nuestro_vistas=8116, nuestro_peor="PjgPAqW0sKg", peor_vistas=818,
         viral="PwYDlELz-f8", viral_vistas=30979765, canal="Muzam"),
    dict(formato="STOP", nuestro="wDxr4u26r4E", nuestro_vistas=29884, nuestro_peor=None, peor_vistas=None,
         viral="4k5Zzh5S4Mk", viral_vistas=6916100, canal="TURBO06 (canal de 11 días)"),
]
PROMPT = """Sos experto en YouTube Shorts. Te paso {n} Shorts del MISMO formato de juego ("{formato}"):
- Video 1: el VIRAL de otro canal ({canal}): {viral_vistas:,} vistas.
- Video 2: el MEJOR nuestro: {nuestro_vistas:,} vistas.
{peor}
Compará CUADRO POR CUADRO la EJECUCIÓN (no la idea). Respondé SOLO JSON en español:
{{"primer_segundo": {{"viral": "...", "nuestro": "..."}},
 "duracion_y_ritmo": {{"viral": "...", "nuestro": "..."}},
 "tamano_y_claridad": {{"viral": "qué tan grandes y claras son las caras/objetos", "nuestro": "..."}},
 "dificultad": {{"viral": "cuántas oportunidades, velocidad, ventana", "nuestro": "..."}},
 "texto_en_pantalla": {{"viral": "...", "nuestro": "..."}},
 "sonido": {{"viral": "...", "nuestro": "..."}},
 "final_y_loop": {{"viral": "cómo termina y si engancha con el inicio", "nuestro": "..."}},
 "diferencia_clave": "LA diferencia que más explica la brecha de vistas (1-2 frases)",
 "cambios": ["hasta 5 cambios concretos y medibles para nuestro video (ej: 'caras de 420 px', 'durar 6 s', 'texto X en el cuadro 0')"]}}"""


def main():
    out, L = [], ["# 29 · Comparación con los virales (cuadro por cuadro, Gemini)", ""]
    for p in PARES:
        partes = [{"file_data": {"file_uri": f"https://www.youtube.com/watch?v={p['viral']}"}},
                  {"file_data": {"file_uri": f"https://www.youtube.com/watch?v={p['nuestro']}"}}]
        peor = ""
        if p["nuestro_peor"]:
            partes.append({"file_data": {"file_uri": f"https://www.youtube.com/watch?v={p['nuestro_peor']}"}})
            peor = f"- Video 3: nuestro PEOR del mismo formato: {p['peor_vistas']:,} vistas (usalo para ver qué NO hacer)."
        partes.append({"text": PROMPT.format(n=3 if peor else 2, peor=peor, **p)})
        r = gemini(partes, intentos=2, timeout=300)
        if isinstance(r, list):
            r = next((x for x in r if isinstance(x, dict)), None)
        if not r:
            print("sin respuesta", p["formato"]); continue
        out.append(dict(p, analisis=r))
        L += [f"## {p['formato']} · viral {p['viral_vistas']:,} ({p['canal']}) vs nuestro {p['nuestro_vistas']:,}", "",
              f"https://www.youtube.com/shorts/{p['viral']} · https://www.youtube.com/shorts/{p['nuestro']}", "",
              f"**Diferencia clave:** {r.get('diferencia_clave')}", ""]
        for k in ("primer_segundo", "duracion_y_ritmo", "tamano_y_claridad", "dificultad", "texto_en_pantalla", "sonido", "final_y_loop"):
            x = r.get(k) or {}
            L.append(f"- **{k.replace('_', ' ')}** · viral: {x.get('viral')} · nuestro: {x.get('nuestro')}")
        L += ["", "**Cambios:**"] + [f"- {c}" for c in r.get("cambios", [])] + [""]
        print(p["formato"], "ok", flush=True)
    guardar("comparacion_virales.json", out)
    (RAIZ / "reports" / "29_comparacion_virales.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
