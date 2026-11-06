#!/usr/bin/env python3
"""
Lee los comentarios públicos de nuestros videos (API de YouTube, 1 unidad por página) y cuenta qué dice la gente sobre la
DIFICULTAD: "easy / first try / got it" vs "hard / impossible / can't". Salida: pipeline/datos/comentarios.json
"""
import re

from comun import cargar, guardar, yt

FACIL = r"\beasy\b|first try|1st try|got it|did it|i stopped|stopped it|too easy|facil|fácil|lo logr|primer intento|ez\b"
DIFICIL = r"\bhard\b|impossible|can'?t|cant\b|difficult|imposible|dif[ií]cil|no puedo|never|tried \d+|\d+ tries|attempt"


def main():
    rend = cargar("rendimiento.json", {}).get("videos", [])
    salida = []
    for v in sorted(rend, key=lambda v: -v["vistas"])[:25]:
        coms, tok = [], None
        for _ in range(3):
            try:
                r = yt("commentThreads", part="snippet", videoId=v["id"], maxResults=100, order="relevance", textFormat="plainText",
                       **({"pageToken": tok} if tok else {}))
            except Exception as e:
                print("sin comentarios", v["id"], e); break
            coms += [it["snippet"]["topLevelComment"]["snippet"]["textDisplay"] for it in r.get("items", [])]
            tok = r.get("nextPageToken")
            if not tok:
                break
        f = sum(bool(re.search(FACIL, c.lower())) for c in coms); d = sum(bool(re.search(DIFICIL, c.lower())) for c in coms)
        salida.append(dict(id=v["id"], tipo=v["tipo"], vistas=v["vistas"], titulo=v["titulo"][:60], comentarios=len(coms), facil=f, dificil=d,
                           ejemplos=coms[:25]))
        print(f"{v['vistas']:>7} {v['tipo']:<7} coment={len(coms):>3} fácil={f:>3} difícil={d:>3} | {v['titulo'][:50]}", flush=True)
    guardar("comentarios.json", salida)


if __name__ == "__main__":
    main()
