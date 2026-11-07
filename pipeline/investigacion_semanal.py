#!/usr/bin/env python3
"""
INVESTIGACIÓN AUTOMÁTICA (sábados y miércoles): qué está funcionando, cómo recrearlo y qué cambiar.
1. Mercado (API de YouTube): olas por mecánica en 7 y 3 días (investigar_olas.py).
2. Nuestro canal: vistas, % visto y suscriptores por formato (rendimiento.json + analytics.json) y comentarios (comentarios.py).
3. Cruce mercado vs. canal: qué ola tiene mercado y nosotros no explotamos, y qué formato nuestro rinde sin ola.
4. Formatos nuevos que suben y no tenemos: Gemini los mira y escribe la receta para programarlos (analisis_tendencias.json).
5. Recomendaciones (subir / mantener / bajar / probar) y las preguntas exactas para la IA de YouTube Studio.
Salida: reports/investigacion_AAAA-MM-DD.md + pipeline/datos/investigacion.json (la usa la fábrica para pesar las pruebas).
"""
import json
import statistics as st
from datetime import datetime, timedelta, timezone
from pathlib import Path

from comun import RAIZ, cargar, gemini, guardar

ART = timezone(timedelta(hours=-3))
NUESTRO = {  # familia del mercado -> nuestros formatos de esa familia
    "stop": ["stop", "siuu", "penal", "balon"], "wheel": ["rueda"], "fit": ["cabezas"], "find": ["find"], "dress": ["dress"],
    "quiz": ["trayectoria", "tridente"], "goat": ["circulo"], "balance": ["pared"],
}
CONOCIDAS = set(NUESTRO) | {"skills", "meme", "otros", "3d_ia", "transformacion", "satisfying"}


def nuestro_canal():
    rend = cargar("rendimiento.json", {}).get("videos", [])
    an = {v["video"]: v for v in cargar("analytics.json", {}).get("por_video", [])}
    pub = {p["video_id"]: p for p in cargar("publicados.json", []) if p.get("video_id")}
    fmt = {}
    for v in rend:
        if v["horas"] < 24:
            continue
        x = an.get(v["id"], {}); p = pub.get(v["id"], {})
        imposible = (p.get("fecha", "") + p.get("hora", "")) > "2026-11-0917:00"
        fmt.setdefault(v["tipo"], []).append(dict(v48=v["vistas_48h"], pct=x.get("averageViewPercentage"), subs=x.get("subscribersGained"),
                                                    vistas=v["vistas"], imposible=imposible))
    out = {}
    for k, xs in fmt.items():
        pcts = [x["pct"] for x in xs if x["pct"]]
        out[k] = dict(videos=len(xs), mediana_48h=round(st.median(x["v48"] for x in xs)), mejor=max(x["vistas"] for x in xs),
                      pct_visto=round(st.median(pcts)) if pcts else None, mas_10k=sum(x["vistas"] >= 10_000 for x in xs),
                      imposible=dict(videos=sum(x["imposible"] for x in xs),
                                     mediana_48h=round(st.median([x["v48"] for x in xs if x["imposible"]])) if any(x["imposible"] for x in xs) else None))
    return out


def recomendar(olas7, olas3, canal):
    recs = []
    for fam, nuestros in NUESTRO.items():
        m7 = olas7.get(fam); m3 = olas3.get(fam)
        if not m7:
            continue
        sube = m3 and m7["mas_1M"] and (m3["mas_1M"] / max(1, m7["mas_1M"])) > 0.5
        nos = [canal[n] for n in nuestros if n in canal]
        nos_med = max((n["mediana_48h"] for n in nos), default=None)
        if m7["mediana"] >= 150_000 and (nos_med or 0) >= 8_000:
            acc = "SUBIR: ola fuerte y a nosotros nos rinde"
        elif m7["mediana"] >= 150_000:
            acc = "PROBAR MÁS: el mercado explota y todavía no lo exprimimos"
        elif (nos_med or 0) >= 8_000:
            acc = "MANTENER: nos rinde aunque el mercado esté tibio"
        elif nos_med is None:
            acc = "PROBAR POCO: todavía no tenemos datos propios"
        else:
            acc = "BAJAR: sin ola y sin resultado propio"
        recs.append(dict(familia=fam, nuestros=nuestros, mercado_mediana=m7["mediana"], mercado_1M=m7["mas_1M"], subiendo=bool(sube),
                         nuestra_mediana_48h=nos_med, accion=acc + (" · en subida" if sube else "")))
    return sorted(recs, key=lambda r: -r["mercado_mediana"])


def nuevas_tendencias(olas3, filas7):
    """Videos +1 M de canales chicos en familias que no tenemos o que no son de clips reales: candidatos a formato nuevo."""
    cand = [f for f in filas7 if f["vistas"] >= 1_000_000 and f["dur"] <= 20 and f["familia"] not in ("skills", "meme")
            and f["subs"] < 2_000_000]
    vistos = {a["id"] for a in cargar("analisis_tendencias.json", [])}
    return [c for c in cand if c["id"] not in vistos][:6]


def gemini_recetas(cands):
    if not cands:
        return
    import analizar_ids as A
    previos = {a["id"]: a for a in cargar("analisis_tendencias.json", [])}
    for v in cands:
        try:
            a = gemini([{"file_data": {"file_uri": f"https://www.youtube.com/watch?v={v['id']}"}},
                        {"text": A.PROMPT.format(titulo=v["titulo"], vistas=v["vistas"])}])
        except Exception as e:
            print("gemini falló", v["id"], e); a = None
        if a:
            previos[v["id"]] = {**v, "analisis": a}; print("receta", v["id"], a.get("nombre_formato"), flush=True)
    guardar("analisis_tendencias.json", list(previos.values()))


def preguntas_ia(recs, canal):
    top = sorted(canal.items(), key=lambda kv: -(kv[1]["mediana_48h"]))[:3]
    fl = ", ".join(k for k, _ in top)
    return [
        "Hacé una tabla con mis videos de los últimos 7 días: título, vistas, porcentaje que eligió ver (visto vs. descartado), "
        "% promedio visto y suscriptores. Ordenala por porcentaje que eligió ver.",
        f"Comparame mis formatos {fl}: ¿cuál tiene mejor 'eligió ver' en el primer segundo y por qué? Dame 3 cambios concretos para el cuadro 0.",
        "Mis videos desde el 9/11 son más difíciles (modo imposible). ¿Subió la cantidad de repeticiones y el % visto respecto de la semana anterior?",
        "¿En qué momento exacto se van los espectadores en mis 3 videos con menos % visto de esta semana?",
        "¿Qué formatos interactivos de fútbol (pausar, encajar, adivinar) están creciendo esta semana en canales chicos? "
        "Dame 5 ideas nuevas de menos de 8 segundos que mi audiencia también mire.",
        "¿Qué jugadores, partidos o memes de fútbol son tendencia esta semana entre mi público? 10 ideas de título.",
        "¿Qué videos me trajeron más suscriptores por cada 1.000 vistas esta semana y qué tienen en común?",
    ]


def main():
    import comentarios
    import investigar_olas
    investigar_olas.main(); comentarios.main()
    olas = cargar("olas.json", {})
    o7, o3 = olas.get("7d", {}).get("familias", {}), olas.get("3d", {}).get("familias", {})
    canal = nuestro_canal()
    recs = recomendar(o7, o3, canal)
    cands = nuevas_tendencias(o3, olas.get("7d", {}).get("filas", []))
    gemini_recetas(cands)
    com = cargar("comentarios.json", [])
    hoy = datetime.now(ART).date().isoformat()
    res = dict(fecha=hoy, recomendaciones=recs, canal=canal, nuevas=[dict(id=c["id"], titulo=c["titulo"], vistas=c["vistas"]) for c in cands],
               comentarios=dict(total=sum(c["comentarios"] for c in com), facil=sum(c["facil"] for c in com), dificil=sum(c["dificil"] for c in com)),
               preguntas_ia=preguntas_ia(recs, canal))
    guardar("investigacion.json", res)
    L = [f"# Investigación {hoy}", "", "## Olas del mercado (7 días)", "", "| Mecánica | Videos | +1 M | Mediana | Vistas/hora | Duración |", "|---|---|---|---|---|---|"]
    for k, r in list(o7.items())[:14]:
        L.append(f"| {k} | {r['videos']} | {r['mas_1M']} | {r['mediana']:,} | {r['vph_mediana']:,} | {r['dur_mediana']} s |")
    L += ["", "## Nuestro canal por formato", "", "| Formato | Videos | Mediana 48 h | Mejor | % visto | +10k | Modo imposible (mediana 48 h) |", "|---|---|---|---|---|---|---|"]
    for k, r in sorted(canal.items(), key=lambda kv: -kv[1]["mediana_48h"]):
        L.append(f"| {k} | {r['videos']} | {r['mediana_48h']:,} | {r['mejor']:,} | {r['pct_visto'] or '-'} | {r['mas_10k']} | "
                 f"{r['imposible']['mediana_48h'] or '-'} ({r['imposible']['videos']}) |")
    L += ["", "## Qué hacer", ""] + [f"- **{r['familia']}** ({', '.join(r['nuestros'])}): {r['accion']} — mercado {r['mercado_mediana']:,}, "
                                     f"nosotros {r['nuestra_mediana_48h'] or '-'}" for r in recs]
    L += ["", "## Tendencias nuevas para recrear (Gemini)", ""]
    for a in cargar("analisis_tendencias.json", []):
        if a["id"] in {c["id"] for c in cands}:
            x = a["analisis"]; L.append(f"- **{x.get('nombre_formato')}** ({a['vistas']:,} vistas): {x.get('mecanica')}")
    L += ["", f"## Comentarios: {res['comentarios']['total']} leídos · dicen fácil {res['comentarios']['facil']} · difícil {res['comentarios']['dificil']}",
          "", "## Preguntas para la IA de YouTube Studio (copiar y pegar, una por mensaje)", ""] + [f"{i + 1}. {q}" for i, q in enumerate(res["preguntas_ia"])]
    (RAIZ / "reports" / f"investigacion_{hoy}.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
