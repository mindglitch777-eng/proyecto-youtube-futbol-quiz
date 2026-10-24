#!/usr/bin/env python3
"""
Procesa data/raw/*.json -> data/processed/*.csv y data/processed/stats.json.
No usa la API (no gasta cuota). Correr después de yt_research.py y gemini_clasificar.py.

Definiciones (para que todo sea rastreable):
- short: duración <= 180 s.
- formatos "quiz": todos los códigos de gemini_clasificar.FORMATOS salvo no_quiz_futbol, no_futbol, datos_curiosos.
- clase de canal según sus últimos 50 videos clasificados: quiz_puro (>=70 % quiz),
  quiz_mixto (20-70 %), no_quiz (<20 %).
- outlier ("pegó"): video con vistas >= 10 x la mediana de los últimos 50 de su canal.
- canal joven: creado después de 2025-10-24 (12 meses antes de la fecha de corte).
"""
import json
import re
import statistics as st
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW, PROC = ROOT / "data" / "raw", ROOT / "data" / "processed"
PROC.mkdir(parents=True, exist_ok=True)
CORTE = datetime(2026, 10, 24, tzinfo=timezone.utc)
NO_QUIZ = {"no_quiz_futbol", "no_futbol", "datos_curiosos"}
ART = ZoneInfo("America/Argentina/Buenos_Aires")
EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿⭐⬆↔-↪]")


def load(n, d=None):
    p = RAW / n
    return json.loads(p.read_text()) if p.exists() else d


def fecha(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def _get(d, *ks):
    for k in ks:
        if not isinstance(d, dict):
            return None
        d = d.get(k)
    return d


def main():
    videos = load("videos.json", {})
    canales = load("channels.json", {})
    recientes = load("channel_recent.json", {})
    historial = load("channel_history.json", {})
    fmt = load("gemini_formatos.json", {})
    hits = load("search_hits.json", [])
    en_busqueda = {vid for h in hits for vid in h["video_ids"]}

    # ---------------- videos
    filas = []
    for v in videos.values():
        f = fmt.get(v["id"], {})
        pub = fecha(v["publishedAt"])
        edad = max((CORTE - pub).total_seconds() / 86400, 1)
        t = v["title"]
        letras = [c for c in t if c.isalpha()]
        filas.append({
            "id": v["id"], "url": f"https://youtube.com/shorts/{v['id']}",
            "channelId": v["channelId"], "canal": v["channelTitle"], "titulo": t,
            "publicado": v["publishedAt"], "hora_utc": pub.hour, "hora_art": pub.astimezone(ART).hour,
            "dia_semana": pub.strftime("%a"), "edad_dias": round(edad, 1),
            "duracion_s": v["duration_s"], "es_short": (v["duration_s"] or 999) <= 180,
            "vistas": v["views"], "likes": v["likes"], "comentarios": v["comments"],
            "vistas_por_dia": round(v["views"] / edad),
            "likes_por_1000": round(1000 * v["likes"] / v["views"], 2) if v["likes"] is not None and v["views"] else None,
            "coment_por_1000": round(1000 * v["comments"] / v["views"], 3) if v["comments"] is not None and v["views"] else None,
            "formato": f.get("f"), "formato2": f.get("f2"), "cara": f.get("cara"),
            "idioma": f.get("idioma"), "sujeto": f.get("sujeto"),
            "es_quiz": (f.get("f") not in NO_QUIZ) if f else None,
            "en_busqueda": v["id"] in en_busqueda,
            "titulo_len": len(t), "titulo_pregunta": "?" in t,
            "titulo_emojis": len(EMOJI.findall(t)),
            "titulo_mayus": round(sum(c.isupper() for c in letras) / len(letras), 2) if letras else 0,
            "titulo_hashtags": len(re.findall(r"#\w+", t)),
            "desc_hashtags": " ".join(re.findall(r"#\w+", v["description"]))[:200],
            "tiene_shorts_tag": "#shorts" in (t + v["description"]).lower(),
        })
    dv = pd.DataFrame(filas)

    # mediana del canal (últimos 50) para outliers
    med_canal = {}
    for cid, ids in recientes.items():
        vs = [videos[i]["views"] for i in ids if i in videos]
        if vs:
            med_canal[cid] = st.median(vs)
    dv["mediana_canal"] = dv["channelId"].map(med_canal)
    dv["x_mediana_canal"] = (dv["vistas"] / dv["mediana_canal"]).round(2)
    dv["outlier_10x"] = dv["x_mediana_canal"] >= 10
    dv.sort_values("vistas", ascending=False).to_csv(PROC / "videos.csv", index=False)

    # ---------------- canales
    filas = []
    for cid, c in canales.items():
        ids = [i for i in recientes.get(cid, []) if i in videos]
        vs = [videos[i] for i in ids]
        shorts = [v for v in vs if (v["duration_s"] or 999) <= 180]
        clasif = [fmt[v["id"]] for v in vs if v["id"] in fmt]
        quiz_share = (sum(x["f"] not in NO_QUIZ for x in clasif) / len(clasif)) if clasif else None
        futbol_share = (sum(x["f"] != "no_futbol" for x in clasif) / len(clasif)) if clasif else None
        clase = None if quiz_share is None else ("quiz_puro" if quiz_share >= .7 else "quiz_mixto" if quiz_share >= .2 else "no_quiz")
        fechas = sorted(fecha(v["publishedAt"]) for v in vs)
        span = (fechas[-1] - fechas[0]).total_seconds() / 86400 if len(fechas) > 1 else None
        views = [v["views"] for v in vs]
        mejor = max(vs, key=lambda v: v["views"]) if vs else None
        creado = fecha(c["publishedAt"])
        edad_d = (CORTE - creado).days
        fmts = Counter(x["f"] for x in clasif if x["f"] not in NO_QUIZ)
        caras = [x["cara"] for x in clasif if x["cara"] is not None]
        idiomas = Counter(x["idioma"] for x in clasif)
        # primer video del canal (si tenemos historial completo)
        filas.append({
            "channelId": cid, "canal": c["title"], "url": f"https://youtube.com/channel/{cid}",
            "handle": c.get("customUrl"), "creado": c["publishedAt"][:10], "edad_dias": edad_d,
            "pais": c.get("country"), "idioma_principal": idiomas.most_common(1)[0][0] if idiomas else None,
            "subs": c["subs"], "vistas_totales": c["views"], "videos_totales": c["videos"],
            "vistas_por_sub": round(c["views"] / c["subs"]) if c["subs"] else None,
            "vistas_por_dia_vida": round(c["views"] / max(edad_d, 1)),
            "n_ult": len(vs), "pct_shorts_ult": round(len(shorts) / len(vs), 2) if vs else None,
            "subidas_por_dia_ult": round(len(vs) / span, 2) if span else None,
            "media_vistas_ult": round(st.mean(views)) if views else None,
            "mediana_vistas_ult": round(st.median(views)) if views else None,
            "mejor_video": f"https://youtube.com/shorts/{mejor['id']}" if mejor else None,
            "mejor_titulo": mejor["title"] if mejor else None, "mejor_vistas": mejor["views"] if mejor else None,
            "mejor_sobre_mediana": round(mejor["views"] / st.median(views), 1) if views and st.median(views) else None,
            "pct_outliers_10x": round(sum(x >= 10 * st.median(views) for x in views) / len(views), 3) if views and st.median(views) else None,
            "pct_quiz": round(quiz_share, 2) if quiz_share is not None else None,
            "pct_futbol": round(futbol_share, 2) if futbol_share is not None else None,
            "clase": clase, "formato_principal": fmts.most_common(1)[0][0] if fmts else None,
            "formatos": "; ".join(f"{k}:{n}" for k, n in fmts.most_common(4)),
            "pct_con_cara": round(sum(caras) / len(caras), 2) if caras else None,
            "joven_12m": creado >= datetime(2025, 10, 24, tzinfo=timezone.utc),
            "apariciones_busqueda": c.get("apariciones_busqueda", 0),
            "historial_completo": cid in historial,
        })
    dc = pd.DataFrame(filas).sort_values("vistas_totales", ascending=False)
    dc.to_csv(PROC / "canales.csv", index=False)

    # ---------------- formatos
    # base sin sesgo de búsqueda: shorts de uploads recientes de canales de fútbol (pct_futbol >= .5)
    canales_futbol = set(dc.loc[dc["pct_futbol"].fillna(0) >= .5, "channelId"])
    sub_ids = {i for cid in canales_futbol for i in recientes.get(cid, [])}
    base = dv[dv["id"].isin(sub_ids) & dv["es_short"] & dv["formato"].notna()]
    todos = dv[dv["es_short"] & dv["formato"].notna()]
    filas = []
    for f, g in todos.groupby("formato"):
        b = base[base["formato"] == f]
        filas.append({
            "formato": f, "n_videos": len(g), "n_canales": g["channelId"].nunique(),
            "n_base_uploads": len(b), "n_canales_base": b["channelId"].nunique(),
            "mediana_vistas_base": int(b["vistas"].median()) if len(b) else None,
            "mediana_vistas_por_dia_base": int(b["vistas_por_dia"].median()) if len(b) else None,
            "pct_outliers_10x_base": round(b["outlier_10x"].mean(), 3) if len(b) else None,
            "x_mediana_canal_mediana": round(b["x_mediana_canal"].median(), 2) if len(b) else None,
            "mediana_vistas_top_busqueda": int(g[g["en_busqueda"]]["vistas"].median()) if g["en_busqueda"].any() else None,
            "videos_1M_mas": int((g["vistas"] >= 1_000_000).sum()),
            "videos_1M_ult_12m": int(((g["vistas"] >= 1_000_000) & (g["edad_dias"] <= 365)).sum()),
            "likes_por_1000_med": g["likes_por_1000"].median(),
            "coment_por_1000_med": g["coment_por_1000"].median(),
            "pct_con_cara": round(g["cara"].dropna().astype(float).mean(), 2) if g["cara"].notna().any() else None,
            "duracion_mediana": g["duracion_s"].median(),
            "ejemplo_top": g.sort_values("vistas", ascending=False)["url"].iloc[0],
            "ejemplo_top_titulo": g.sort_values("vistas", ascending=False)["titulo"].iloc[0],
            "ejemplo_top_vistas": int(g["vistas"].max()),
        })
    df = pd.DataFrame(filas).sort_values("mediana_vistas_base", ascending=False)
    df.to_csv(PROC / "formatos.csv", index=False)

    # formato x idioma
    fi = (todos[~todos["formato"].isin(NO_QUIZ)].groupby(["formato", "idioma"])
          .agg(n=("id", "size"), canales=("channelId", "nunique"), mediana_vistas=("vistas", "median"),
               v_1M=("vistas", lambda s: int((s >= 1e6).sum())))
          .reset_index().sort_values(["formato", "n"], ascending=[True, False]))
    fi.to_csv(PROC / "formato_idioma.csv", index=False)

    # ---------------- objetivos para comentarios: top quiz shorts sin repetir canal más de 3 veces
    q = dv[dv["es_quiz"].fillna(False) & dv["es_short"]].sort_values("vistas", ascending=False)
    elegidos, por_canal = [], Counter()
    for _, r in q.iterrows():
        if por_canal[r["channelId"]] < 3 and (r["comentarios"] or 0) > 20:
            elegidos.append(r["id"])
            por_canal[r["channelId"]] += 1
        if len(elegidos) >= 80:
            break
    (RAW / "comments_targets.json").write_text(json.dumps(elegidos))

    # ---------------- anatomía (Gemini mirando los videos)
    filas = []
    for f in sorted((RAW / "gemini_shorts").glob("*.json")):
        d = json.loads(f.read_text())
        a = d.get("analisis")
        if not isinstance(a, dict):
            continue
        v = videos.get(d["video_id"], {})
        g = lambda *ks: _get(a, *ks)
        est = a.get("estructura") or []
        filas.append({
            "id": d["video_id"], "url": f"https://youtube.com/shorts/{d['video_id']}", "canal": v.get("channelTitle"),
            "titulo": v.get("title"), "vistas": v.get("views"), "duracion_s": v.get("duration_s"),
            "formato_gemini": g("formato"), "formato_titulo": fmt.get(d["video_id"], {}).get("f"),
            "n_preguntas": g("n_preguntas_o_rondas"), "gancho_fin_s": g("gancho", "fin_s"), "gancho_tipo": g("gancho", "tipo"),
            "gancho_texto": g("gancho", "que_se_dice_o_texto"),
            "pensar_s": g("tiempo_para_pensar_por_pregunta_s"), "cuenta_regresiva": g("cuenta_regresiva", "hay"),
            "cuenta_estilo": g("cuenta_regresiva", "estilo"), "revelacion": g("revelacion", "como"),
            "loop": str(g("cierre_y_loop", "loop")).lower() == "true", "loop_como": g("cierre_y_loop", "como_hace_el_loop"),
            "cta": g("cta", "en_video"), "voz": g("audio", "voz"), "musica": g("audio", "musica"),
            "sfx": "; ".join(map(str, g("audio", "efectos_de_sonido") or [])),
            "texto": g("texto_en_pantalla", "hay_texto"), "subtitulos": g("texto_en_pantalla", "subtitulos_de_voz"),
            "texto_estilo": g("texto_en_pantalla", "estilo"),
            "cara": g("visual", "persona_real_en_camara"), "fotos_jugadores": g("visual", "fotos_de_jugadores"),
            "escudos": g("visual", "escudos_o_logos"), "clips_tv": g("visual", "clips_de_partidos_o_transmisiones"),
            "ia_dibujos": g("visual", "imagenes_generadas_por_ia_o_dibujos"), "planos": g("visual", "cambios_de_plano_aprox"),
            "estilo": g("visual", "estilo_general"), "dificultad": g("dificultad_de_las_preguntas"),
            "invita_comentar": g("invita_a_comentar_la_respuesta"), "por_que_funciona": g("que_hace_que_funcione"),
            "replica_sin_cara": g("como_replicarlo_sin_cara_y_sin_clips"),
            "partes": " | ".join(f"{p.get('inicio_s')}-{p.get('fin_s')} {p.get('parte')}" for p in est if isinstance(p, dict)),
        })
    if filas:
        pd.DataFrame(filas).sort_values("vistas", ascending=False).to_csv(PROC / "anatomia.csv", index=False)

    # ---------------- sujetos (jugadores/clubes) en shorts quiz
    sq = dv[dv["es_quiz"].fillna(False) & dv["sujeto"].notna()]
    (sq.assign(sujeto=sq["sujeto"].str.strip().str.title())
       .groupby("sujeto").agg(videos=("id", "size"), vistas_total=("vistas", "sum"), mediana=("vistas", "median"),
                              coment_por_1000=("coment_por_1000", "median"))
       .query("videos >= 3").sort_values("vistas_total", ascending=False).head(80)
       .to_csv(PROC / "sujetos.csv"))

    # ---------------- resumen
    stats = {
        "fecha_corte": CORTE.isoformat(),
        "videos_total": len(dv), "shorts": int(dv["es_short"].sum()),
        "shorts_clasificados": int(todos.shape[0]),
        "shorts_quiz": int(dv["es_quiz"].fillna(False).sum()),
        "canales": len(dc), "clases_canal": dc["clase"].value_counts().to_dict(),
        "busquedas": len(hits),
        "cuota": load("quota.json", {}),
    }
    (PROC / "stats.json").write_text(json.dumps(stats, indent=1, ensure_ascii=False, default=str))
    print(json.dumps(stats, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
