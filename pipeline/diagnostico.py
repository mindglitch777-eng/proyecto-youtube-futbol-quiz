#!/usr/bin/env python3
"""
DIAGNÓSTICO "POR QUÉ FALLÓ" (08/11): no solo qué repetir, también qué evitar.
Para cada formato con ≥4 videos medidos (≥24 h) compara los que se quedaron cortos (<50% de la mediana del formato)
con los que la rompieron (>150%) según: hora, superestrella del título, plantilla del título y variante.
Un factor se marca EVITAR si con ≥2 videos rinde menos de la mitad de la mediana del formato, y REPETIR si rinde 1,5 veces más.
Salida: datos/diagnostico.json (lo usan la investigación y el tablero) + resumen impreso.
"""
import re
import statistics as st

from comun import cargar, guardar

ESTRELLAS = ["Ronaldo", "Messi", "Mbappé", "Yamal", "Neymar", "Vinícius"]


def plantilla(t):
    t = re.sub(r"#\w+", "", t)
    for n in ESTRELLAS + ["CR7"]:
        t = t.replace(n, "{X}")
    t = re.sub(r"\b[A-Z][a-zé]+\b(?= or| vs|,|\?|'s)", "{Y}", t)               # otros nombres propios
    return " ".join(re.sub(r"[^\w{}%' ]+", " ", t).split()[:7]).lower()


def main():
    rend = {v["id"]: v for v in cargar("rendimiento.json", {}).get("videos", []) if v["horas"] >= 24}
    an = {v["video"]: v for v in cargar("analytics.json", {}).get("por_video", [])}
    filas = []
    for p in cargar("publicados.json", []):
        v = rend.get(p.get("video_id"))
        if not v:
            continue
        t = p.get("titulo") or v["titulo"]
        filas.append(dict(id=p["video_id"], tipo=v["tipo"], v48=v["vistas_48h"], hora=p["hora"][:2] + " h",
                          estrella=next((n for n in ESTRELLAS if n in t), "sin estrella"), plantilla=plantilla(t),
                          variante=p.get("variante") or "-", pct=(an.get(p["video_id"]) or {}).get("averageViewPercentage"), titulo=t))
    out = {}
    for tipo in sorted({f["tipo"] for f in filas}):
        xs = [f for f in filas if f["tipo"] == tipo]
        if len(xs) < 4:
            continue
        med = st.median(f["v48"] for f in xs)
        factores = []
        for campo in ("hora", "estrella", "plantilla", "variante"):
            for val in sorted({f[campo] for f in xs}):
                g = [f["v48"] for f in xs if f[campo] == val]
                if len(g) < 2 or len(g) == len(xs):
                    continue
                rel = st.median(g) / max(1, med)
                if rel < 0.5 or rel > 1.5:
                    factores.append(dict(campo=campo, valor=val, videos=len(g), rinde=f"{rel:.0%} de la mediana",
                                         accion="EVITAR" if rel < 0.5 else "REPETIR"))
        flojos = sorted([f for f in xs if f["v48"] < 0.5 * med], key=lambda f: f["v48"])[:5]
        out[tipo] = dict(videos=len(xs), mediana_48h=round(med), factores=sorted(factores, key=lambda f: f["accion"]),
                         flojos=[dict(titulo=f["titulo"][:70], v48=f["v48"], hora=f["hora"], pct=f["pct"]) for f in flojos])
    guardar("diagnostico.json", out)
    for tipo, d in out.items():
        print(f"\n== {tipo}: {d['videos']} videos, mediana 48 h {d['mediana_48h']:,}")
        for f in d["factores"]:
            print(f"  {f['accion']:<8} {f['campo']}: {f['valor']} ({f['videos']} videos, {f['rinde']})")
    return out


if __name__ == "__main__":
    main()
