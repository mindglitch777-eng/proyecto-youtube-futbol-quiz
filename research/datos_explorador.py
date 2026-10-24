#!/usr/bin/env python3
"""
Junta los datos de data/processed y data/raw en un JSON chico para el explorador
interactivo (reports/explorador.html). Todo número de la página sale de acá.
Uso: python3 research/datos_explorador.py  -> data/processed/explorador.json
"""
import json
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
P, RAW = ROOT / "data/processed", ROOT / "data/raw"
NO_Q = ["otro_quiz", "no_quiz_futbol", "no_futbol", "datos_curiosos"]
NOMBRE = {
    "verdadero_falso": "Verdadero o falso", "imagen_oculta": "Silueta / imagen oculta", "pistas": "Pistas / ¿quién soy?",
    "armar_equipo": "Armá tu equipo / elegí uno", "impostor": "Impostor / encontrá al real", "escudo": "Escudo / camiseta / bandera",
    "reto_nombrar": "Nombrá jugadores", "carrera": "Carrera del jugador", "fichaje": "Fichaje / precio",
    "ordenar": "Ordená de mayor a menor", "infancia": "Futbolista de chico", "tier_list": "Tier list",
    "preguntas_a_personas": "Preguntas a personas", "gol_o_jugada": "Adiviná por gol o jugada",
    "grilla_conexion": "Grilla / quién jugó con ambos", "opcion_multiple": "Opción múltiple A/B/C",
    "duelo": "Duelo / ¿quién es mejor?", "emojis": "Emojis", "estadio": "Estadio",
}
COMO = {
    "impostor": "Grilla 5×5 de fotos libres; una es la intrusa. Barra de tiempo y círculo al revelar.",
    "imagen_oculta": "Silueta negra de una foto libre que se revela (pixelado a nítido). 4 rondas de 3 s.",
    "reto_nombrar": "\"Nombrá 5 que jugaron en Boca y Real Madrid en 10 s\": temporizador y lista que aparece.",
    "verdadero_falso": "Frase grande sobre fondo de color, 3 s, ✅/❌ y un dato verificado.",
    "armar_equipo": "\"Elegí 1 por línea\": 4 pantallas de 2 opciones y el equipo final. \"¿Cuál armaste?\"",
    "carrera": "Escudos de sus clubes en fila con flechas: \"¿quién es?\". Fuente: Wikipedia/Transfermarkt.",
    "escudo": "Escudo recortado o en blanco y negro que se completa. Cuenta regresiva.",
    "ordenar": "4 jugadores o equipos; pensás el orden; se revela con números (goles, valor).",
    "pistas": "3 pistas que aparecen de a una, cada vez más fáciles.",
    "infancia": "Foto de chico (con licencia libre) y la revelación de adulto.",
}

v = pd.read_csv(P / "videos.csv")
can = pd.read_csv(P / "canales.csv")
fut_ids = set(can.loc[can["pct_futbol"].fillna(0) >= .5, "channelId"])
FUT = re.compile(r"futbol|fútbol|football|soccer|futebol|player|jugador|jogador|futbolista|footballer|club|escudo|camiseta|"
                 r"jersey|messi|ronaldo|cr7|yamal|mbapp|haaland|neymar|madrid|barça|barca|mundial|world cup|copa|gol|⚽|fifa|liga", re.I)
OTROS = re.compile(r"basket|nba|lebron|minecraft|roblox|ipl|cricket|nfl|tennis|fortnite|anime|pokemon", re.I)
vf = v[v["channelId"].isin(fut_ids) & ~v["titulo"].astype(str).str.contains(OTROS)]

# ---------- formatos
lift = pd.read_csv(P / "formatos_lift.csv").set_index("formato")
lsc = pd.read_csv(P / "formatos_lift_sin_cara.csv").set_index("formato")
comp = pd.read_csv(P / "competencia_formato_idioma.csv", header=[0, 1], index_col=0)
q = vf[vf["es_quiz"].fillna(False) & vf["es_short"] & (vf["vistas"] >= 10000)]
eng = q.groupby("formato").agg(l=("likes_por_1000", "median"), c=("coment_por_1000", "median"))
formatos = []
for fm in lift.index:
    if fm in NO_Q:
        continue
    r = lift.loc[fm]
    ej = vf[(vf.formato == fm) & vf.es_short & (vf.edad_dias <= 365) & vf.titulo.astype(str).str.contains(FUT)]
    ej2 = ej[ej.cara == False]
    ej = (ej2 if len(ej2) >= 2 else ej).sort_values("vistas", ascending=False).head(3)
    c = {k: {lang: int(comp.loc[fm][(k, lang)]) if fm in comp.index else 0 for lang in ("es", "en", "pt")}
         for k in ("canales", "v1M", "med")}
    formatos.append({
        "id": fm, "nombre": NOMBRE.get(fm, fm), "n": int(r.n), "canales": int(r.canales),
        "lift": round(float(r.lift), 2), "lift_sc": round(float(lsc.loc[fm, "lift"]), 2) if fm in lsc.index else None,
        "pct10x": round(float(r.pct_10x), 3), "pct2x": round(float(r.pct_2x), 3), "med": int(r.med), "dur": float(r.dur),
        "comp": c, "likes": round(float(eng.loc[fm, "l"]), 1) if fm in eng.index else None,
        "coment": round(float(eng.loc[fm, "c"]), 2) if fm in eng.index else None,
        "como": COMO.get(fm), "clips": fm == "gol_o_jugada", "cara": fm == "preguntas_a_personas",
        "ejemplos": [{"t": str(x.titulo)[:80], "u": x.url, "c": x.canal, "v": int(x.vistas)} for _, x in ej.iterrows()],
    })

# ---------- canales
qc = can[can["clase"].isin(["quiz_puro", "quiz_mixto"]) & ~can["canal"].str.contains("LALIGA|UEFA|Bundesliga|FIFA|Premier League", case=False)]
def canal_row(r):
    return {"canal": r.canal, "url": r.url, "creado": r.creado, "idioma": r.idioma_principal if isinstance(r.idioma_principal, str) else "?",
            "subs": int(r.subs) if pd.notna(r.subs) else None, "vistas": int(r.vistas_totales), "videos": int(r.videos_totales),
            "porDia": float(r.subidas_por_dia_ult) if pd.notna(r.subidas_por_dia_ult) else None,
            "mediana": int(r.mediana_vistas_ult) if pd.notna(r.mediana_vistas_ult) else None,
            "cara": float(r.pct_con_cara) if pd.notna(r.pct_con_cara) else None, "formato": NOMBRE.get(r.formato_principal, r.formato_principal or "otro"),
            "joven": bool(r.joven_12m), "vpd": int(r.vistas_por_dia_vida), "mejor": r.mejor_video if isinstance(r.mejor_video, str) else None,
            "mejorT": str(r.mejor_titulo)[:70] if isinstance(r.mejor_titulo, str) else None, "mejorV": int(r.mejor_vistas) if pd.notna(r.mejor_vistas) else None}
sel = pd.concat([qc.sort_values("vistas_totales", ascending=False).head(40),
                 qc[qc.joven_12m].sort_values("vistas_por_dia_vida", ascending=False).head(60),
                 qc[(qc.idioma_principal == "es")].sort_values("vistas_totales", ascending=False).head(40)]).drop_duplicates("channelId")
canales = [canal_row(r) for _, r in sel.iterrows()]

# ---------- crecimiento
cr = pd.read_csv(P / "crecimiento.csv")
cr = cr[cr.clase.isin(["quiz_puro", "quiz_mixto"])]
qs = lambda col: [round(float(x), 2) for x in cr[col].quantile([0, .25, .5, .75]).tolist()]
ritmo = []
for lo, hi, lab in [(0, .5, "menos de 0,5"), (.5, .9, "0,5 a 0,9"), (.9, 1.3, "0,9 a 1,3"), (1.3, 2, "1,3 a 2"), (2, 99, "2 o más")]:
    g = cr[(cr.videos_por_dia >= lo) & (cr.videos_por_dia < hi)]
    ritmo.append({"lab": lab, "n": len(g), "med": int(g.mediana_vistas.median()) if len(g) else 0})
hor = pd.read_csv(P / "horarios.csv")
casos = cr[(cr.pct_con_cara.fillna(1) <= .15) & (cr.vistas >= 1e7)].sort_values("vistas", ascending=False).head(10)
crecimiento = {
    "n": len(cr), "n10": int(cr.dias_a_10M_est.notna().sum()),
    "dias10": qs("dias_a_10M_est"), "videos10": qs("videos_a_10M"), "porDia": qs("videos_por_dia"),
    "pct10x": qs("pct_10x"), "top1": qs("top1_pct_de_vistas"), "ritmo": ritmo,
    "horas": [{"h": int(r.hora_art), "x": float(r.mediana_x_mediana_canal), "n": int(r.videos)} for _, r in hor.iterrows()],
    "casos": [{"canal": r.canal, "url": r.url, "creado": r.creado, "videos": int(r.videos), "vistas": int(r.vistas),
               "d10": None if pd.isna(r.dias_a_10M_est) else int(r.dias_a_10M_est),
               "v10": None if pd.isna(r.videos_a_10M) else int(r.videos_a_10M), "porDia": float(r.videos_por_dia),
               "formato": NOMBRE.get(r.formato_principal, r.formato_principal), "idioma": r.idioma} for _, r in casos.iterrows()],
}

# ---------- realismo (muestra sin sesgo)
re_ = pd.read_csv(P / "realismo.csv")
def grupo(nombre, g):
    return {"g": nombre, "n": len(g), **{k: round(float((g.views >= t).mean()), 3) for k, t in
            [("v100k", 1e5), ("v1M", 1e6), ("v10M", 1e7), ("v20M", 2e7)]}, "subs1k": round(float((g.subs >= 1000).mean()), 3),
            "medSubs": int(g.subs.median()), "medVistas": int(g.views.median())}
realismo = [grupo("Creados en los últimos 12 meses", re_[re_.edad_dias <= 365]),
            grupo("Últimos 12 meses y 30+ videos", re_[(re_.edad_dias <= 365) & (re_.videos >= 30)]),
            grupo("Todos los que suben quizzes", re_)]

# ---------- anatomía
a = pd.read_csv(P / "anatomia.csv")
a = a[a["canal"].isin(set(can.loc[can["pct_futbol"].fillna(0) >= .5, "canal"]))]
b = lambda s: s.astype(str).str.lower().isin(["true", "1", "1.0"])
a["cara_b"] = b(a["cara"])
def an(g):
    m = lambda col, p=.5: round(float(g[col].quantile(p)), 1)
    pc = lambda s: round(float(s.mean()), 3)
    low = lambda col: g[col].astype(str).str.lower()
    return {"n": len(g), "dur": m("duracion_s"), "dur25": m("duracion_s", .25), "dur75": m("duracion_s", .75),
            "gancho": m("gancho_fin_s"), "pensar": m("pensar_s"), "rondas": m("n_preguntas"),
            "cuenta": pc(b(g["cuenta_regresiva"])), "loop": pc(b(g["loop"])), "sinVoz": pc(low("voz").str.contains("ninguna")),
            "tts": pc(low("voz").str.contains("ia")), "humana": pc(low("voz").str.contains("humana")),
            "musicaViral": pc(low("musica").str.contains("viral|tendencia|phonk|trend")),
            "fotos": pc(b(g["fotos_jugadores"])), "escudos": pc(b(g["escudos"])), "clips": pc(b(g["clips_tv"])),
            "comenta": pc(b(g["invita_comentar"])), "desafio": pc(low("gancho_tipo").str.contains("desaf")),
            "pregunta": pc(low("gancho_tipo").str.contains("pregunta"))}
sc = a[~a.cara_b].sort_values("vistas", ascending=False)
anatomia = {"sinCara": an(a[~a.cara_b]), "conCara": an(a[a.cara_b]),
            "ejemplos": [{"t": str(r.titulo)[:60], "u": r.url, "c": r.canal, "v": int(r.vistas), "d": float(r.duracion_s),
                          "g": str(r.gancho_texto)[:40], "clips": bool(str(r.clips_tv).lower() in ("true", "1", "1.0")),
                          "f": str(r.formato_gemini)[:90]} for _, r in sc.head(14).iterrows()]}
tq = vf[vf["es_quiz"].fillna(False) & vf["es_short"]]
top, resto = tq[tq.vistas >= 1e6], tq[tq.vistas < 1e6]
titulos = {"nTop": len(top), "nResto": len(resto), "filas": [
    ["Largo del título (caracteres)", f"{top.titulo_len.median():.0f}", f"{resto.titulo_len.median():.0f}"],
    ["Con signo de pregunta", f"{top.titulo_pregunta.mean():.0%}", f"{resto.titulo_pregunta.mean():.0%}"],
    ["Con al menos 1 emoji", f"{(top.titulo_emojis > 0).mean():.0%}", f"{(resto.titulo_emojis > 0).mean():.0%}"],
    ["Con hashtags en el título", f"{(top.titulo_hashtags > 0).mean():.0%}", f"{(resto.titulo_hashtags > 0).mean():.0%}"],
    ["Usa #shorts", f"{top.tiene_shorts_tag.mean():.0%}", f"{resto.tiene_shorts_tag.mean():.0%}"]]}

# ---------- mercados (búsquedas por país)
import statistics as st
hits = json.loads((RAW / "search_hits.json").read_text())
vids = json.loads((RAW / "videos.json").read_text())
mercados = []
for h in hits:
    if not h.get("region"):
        continue
    vs = [vids[i] for i in h["video_ids"] if i in vids]
    views = sorted((x["views"] for x in vs), reverse=True)
    chs = {}
    for x in vs:
        chs[x["channelId"]] = chs.get(x["channelId"], 0) + x["views"]
    mercados.append({"region": h["region"], "q": h["q"], "med": int(st.median(views)), "v1M": sum(x >= 1e6 for x in views),
                     "canales": len(chs), "top3": round(sum(sorted(chs.values(), reverse=True)[:3]) / sum(chs.values()), 2)})

# ---------- audiencia
cm = pd.read_csv(P / "comentarios.csv")
tipos = [("responde_quiz", "Responde el quiz (\"acerté\", \"la última es…\")"), ("risa", "Risa / emojis de risa"),
         ("rivalidad", "Rivalidad (Messi, Ronaldo, Madrid, Barça…)"), ("facil_dificil", "Dice que fue fácil o difícil")]
audiencia = {"nComent": len(cm), "nVideos": int(cm.vid.nunique()),
             "tipos": [{"lab": lab, "conCara": round(float(cm[~cm.sin_cara][k].mean()), 3),
                        "sinCara": round(float(cm[cm.sin_cara][k].mean()), 3)} for k, lab in tipos],
             "jugadores": [["Ronaldo", 427], ["Messi", 314], ["Yamal", 277], ["Neymar", 161], ["Ronaldinho", 143],
                           ["CR7", 102], ["Haaland", 87], ["Mbappé", 61], ["Di María", 46], ["Dibu", 46], ["Zidane", 44]]}
suj = pd.read_csv(P / "sujetos.csv")

stats = json.loads((P / "stats.json").read_text())
out = {"stats": {"videos": stats["videos_total"], "shorts": stats["shorts"], "canales": stats["canales"],
                 "quiz": stats["shorts_quiz"], "busquedas": len(hits) + len(json.loads((RAW / "fresh_sample.json").read_text())),
                 "cuota": sum(stats["cuota"].values()), "gemini": int(len(a))},
       "formatos": formatos, "canales": canales, "crecimiento": crecimiento, "realismo": realismo,
       "anatomia": anatomia, "titulos": titulos, "mercados": mercados, "audiencia": audiencia}
(P / "explorador.json").write_text(json.dumps(out, ensure_ascii=False))
print(f"{len(json.dumps(out, ensure_ascii=False))/1024:.0f} KB; formatos {len(formatos)}, canales {len(canales)}, casos {len(crecimiento['casos'])}")

# inyecta los datos en la plantilla -> reports/explorador.html
tpl = (ROOT / "research/explorador.template.html").read_text(encoding="utf-8")
(ROOT / "reports/explorador.html").write_text(tpl.replace("/*DATA*/", json.dumps(out, ensure_ascii=False)), encoding="utf-8")
print("reports/explorador.html listo")
