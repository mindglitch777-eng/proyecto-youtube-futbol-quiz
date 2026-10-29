#!/usr/bin/env python3
"""
Análisis del dataset de research/algoritmo_dataset.py (130 canales de fútbol en Shorts).
Todo se compara DENTRO de cada canal (vistas / mediana del canal) para no mezclar canales grandes y chicos.
Salida: data/processed/algoritmo_resultados.json + impresión resumida.
"""
import json
import re
import statistics as st
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import numpy as np

RAIZ = Path(__file__).resolve().parents[1]
D = RAIZ / "data" / "raw" / "algoritmo"
HOY = datetime(2026, 10, 29)
EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿]")


def fecha(s):
    return datetime.strptime(s[:19], "%Y-%m-%dT%H:%M:%S")


def palabras(t):
    return set(w for w in re.findall(r"[a-záéíóúñü0-9]+", t.lower()) if len(w) > 2)


def main():
    canales = json.loads((D / "canales.json").read_text())
    todos = json.loads((D / "videos.json").read_text())
    por = defaultdict(list)
    for v in todos.values():
        if 0 < v["dur"] <= 180 and v["canal"] in canales:     # solo Shorts
            por[v["canal"]].append(v)
    for c in por:
        por[c].sort(key=lambda v: v["publicado"])
    # saco los videos de menos de 3 días (todavía no terminaron su prueba)
    res = {}

    # 1. concentración / lotería
    conc, tasa_hits = [], []
    for c, vs in por.items():
        vv = sorted([v["vistas"] for v in vs if (HOY - fecha(v["publicado"])).days >= 3], reverse=True)
        if len(vv) < 20 or sum(vv) == 0:
            continue
        top = vv[:max(1, len(vv) // 10)]
        conc.append(sum(top) / sum(vv))
        med = st.median(vv)
        tasa_hits.append(sum(x >= 10 * max(med, 1) for x in vv) / len(vv))
    res["1_concentracion"] = dict(canales=len(conc), top10pct_se_lleva_mediana=round(st.median(conc), 3),
                                  pct_videos_10x_la_mediana=round(st.median(tasa_hits), 3))

    # 2. canales nacidos en 2026: en qué video llega el primer 1M y cuántos días
    primer = []
    for c, vs in por.items():
        if not canales[c]["creado"].startswith("2026") or canales[c]["n_videos"] > 300:
            continue
        for i, v in enumerate(vs):
            if v["vistas"] >= 1_000_000:
                dias = (fecha(v["publicado"]) - fecha(vs[0]["publicado"])).days
                primer.append(dict(canal=canales[c]["titulo"], video_n=i + 1, dias=dias, vistas=v["vistas"]))
                break
    vn = [p["video_n"] for p in primer]
    res["2_primer_millon_canales_2026"] = dict(n=len(primer), mediana_video_n=st.median(vn) if vn else None,
                                               p25=float(np.percentile(vn, 25)) if vn else None, p75=float(np.percentile(vn, 75)) if vn else None,
                                               en_los_primeros_10=sum(x <= 10 for x in vn), mediana_dias=st.median([p["dias"] for p in primer]) if primer else None,
                                               ejemplos=sorted(primer, key=lambda p: p["video_n"])[:15])

    # 3. después de un hit: ¿repiten formato? ¿suben los siguientes?
    antes, despues, parecido_post, parecido_base = [], [], [], []
    for c, vs in por.items():
        vv = [v["vistas"] for v in vs]
        if len(vs) < 30:
            continue
        med = st.median(vv)
        for i, v in enumerate(vs):
            if v["vistas"] >= 10 * max(med, 1000) and 10 <= i < len(vs) - 10:
                a = st.median(vv[i - 10:i]); d = st.median(vv[i + 1:i + 11])
                antes.append(a / med); despues.append(d / med)
                w = palabras(v["titulo"])
                sim = lambda x: len(w & palabras(x["titulo"])) / max(1, len(w | palabras(x["titulo"])))
                parecido_post.append(st.mean(sim(x) for x in vs[i + 1:i + 11]))
                parecido_base.append(st.mean(sim(x) for x in vs[i - 10:i]))
    res["3_despues_de_un_hit"] = dict(hits=len(antes), vistas_10_antes_vs_mediana=round(st.median(antes), 2) if antes else None,
                                      vistas_10_despues_vs_mediana=round(st.median(despues), 2) if despues else None,
                                      parecido_titulo_10_despues=round(st.median(parecido_post), 3) if parecido_post else None,
                                      parecido_titulo_10_antes=round(st.median(parecido_base), 3) if parecido_base else None)

    # 4. frecuencia: vistas relativas según cuántos subió ese día el canal
    porfreq = defaultdict(list); freq_canal = []
    for c, vs in por.items():
        med = st.median([v["vistas"] for v in vs]) or 1
        dia = defaultdict(list)
        for v in vs:
            dia[v["publicado"][:10]].append(v)
        if len(vs) >= 20:
            span = max(1, (fecha(vs[-1]["publicado"]) - fecha(vs[0]["publicado"])).days)
            freq_canal.append(dict(canal=canales[c]["titulo"], por_dia=round(len(vs) / span, 2), subs=canales[c]["subs"]))
        for d, lst in dia.items():
            k = min(len(lst), 5)
            for v in lst:
                porfreq[k].append(v["vistas"] / med)
    res["4_frecuencia"] = dict(vistas_rel_segun_subidas_ese_dia={str(k): dict(n=len(x), mediana=round(st.median(x), 2)) for k, x in sorted(porfreq.items())},
                               subidas_por_dia_mediana=st.median([f["por_dia"] for f in freq_canal]),
                               canales_top_subs=sorted(freq_canal, key=lambda f: -f["subs"])[:15])

    # 5. hora de subida (UTC)
    hora = defaultdict(list); horas_canal = []
    for c, vs in por.items():
        med = st.median([v["vistas"] for v in vs]) or 1
        for v in vs:
            hora[int(v["publicado"][11:13])].append(v["vistas"] / med)
        horas_canal.append(st.mode([int(v["publicado"][11:13]) for v in vs]))
    res["5_hora_utc"] = dict(vistas_rel={str(h): dict(n=len(x), mediana=round(st.median(x), 2)) for h, x in sorted(hora.items())},
                             hora_mas_usada_por_canal=dict(sorted(((str(h), horas_canal.count(h)) for h in set(horas_canal)), key=lambda x: -x[1])[:8]))

    # 6. duración
    rangos = [(0, 10), (10, 15), (15, 20), (20, 30), (30, 45), (45, 60), (60, 90), (90, 180)]
    dur = defaultdict(list)
    for c, vs in por.items():
        med = st.median([v["vistas"] for v in vs]) or 1
        for v in vs:
            for a, b in rangos:
                if a < v["dur"] <= b:
                    dur[f"{a}-{b}s"].append(v["vistas"] / med)
    res["6_duracion"] = {k: dict(n=len(x), mediana=round(st.median(x), 2), pct_hits_10x=round(sum(y >= 10 for y in x) / len(x), 3)) for k, x in dur.items()}

    # 7. títulos
    rasgos = {
        "MAYUSCULAS (>60%)": lambda t: sum(ch.isupper() for ch in t if ch.isalpha()) / max(1, sum(ch.isalpha() for ch in t)) > 0.6,
        "tiene emoji": lambda t: bool(EMOJI.search(t)),
        "tiene #hashtag": lambda t: "#" in t,
        "3+ hashtags": lambda t: t.count("#") >= 3,
        "pregunta (?)": lambda t: "?" in t,
        "'only 1%' / '99%'": lambda t: bool(re.search(r"1%|99%", t)),
        "'vs'": lambda t: bool(re.search(r"\bvs\.?\b", t, re.I)),
        "ronaldo/cr7": lambda t: bool(re.search(r"ronaldo|cr7", t, re.I)),
        "messi": lambda t: bool(re.search(r"messi", t, re.I)),
        "yamal": lambda t: bool(re.search(r"yamal", t, re.I)),
        "neymar": lambda t: bool(re.search(r"neymar", t, re.I)),
        "ishowspeed/speed": lambda t: bool(re.search(r"speed", t, re.I)),
        "mr beast": lambda t: bool(re.search(r"beast", t, re.I)),
        "'find'": lambda t: bool(re.search(r"\bfind\b", t, re.I)),
        "'evolution'": lambda t: bool(re.search(r"evolution", t, re.I)),
        "'day'": lambda t: bool(re.search(r"\bday\b", t, re.I)),
        "corto (<=30 car.)": lambda t: len(t) <= 30,
        "largo (>70 car.)": lambda t: len(t) > 70,
    }
    tit = {}
    for nombre, f in rasgos.items():
        si, no = [], []
        for c, vs in por.items():
            med = st.median([v["vistas"] for v in vs]) or 1
            for v in vs:
                (si if f(v["titulo"]) else no).append(v["vistas"] / med)
        if si and no:
            tit[nombre] = dict(n_si=len(si), con=round(st.median(si), 2), sin=round(st.median(no), 2),
                               hits_con=round(sum(x >= 10 for x in si) / len(si), 3), hits_sin=round(sum(x >= 10 for x in no) / len(no), 3))
    res["7_titulos"] = tit

    # 8. vida del video: vistas según edad (relativas al canal) — más edad = ¿siguen sumando?
    edad = defaultdict(list)
    for c, vs in por.items():
        med = st.median([v["vistas"] for v in vs]) or 1
        for v in vs:
            dd = (HOY - fecha(v["publicado"])).days
            k = "0-2d" if dd <= 2 else "3-7d" if dd <= 7 else "8-30d" if dd <= 30 else "31-90d" if dd <= 90 else "90d+"
            edad[k].append(v["vistas"] / med)
    res["8_edad"] = {k: dict(n=len(x), mediana=round(st.median(x), 2)) for k, x in edad.items()}

    # engagement de hits vs resto
    eng = defaultdict(list)
    for c, vs in por.items():
        med = st.median([v["vistas"] for v in vs]) or 1
        for v in vs:
            if v["vistas"] >= 1000 and v["likes"] is not None and v["coment"] is not None:
                g = "hit (10x)" if v["vistas"] >= 10 * med else "normal"
                eng[g + " likes/vista"].append(v["likes"] / v["vistas"]); eng[g + " coment/vista"].append(v["coment"] / v["vistas"])
    res["9_engagement"] = {k: round(st.median(x) * 100, 3) for k, x in eng.items()}

    (RAIZ / "data" / "processed" / "algoritmo_resultados.json").write_text(json.dumps(res, ensure_ascii=False, indent=1))
    print(json.dumps(res, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
