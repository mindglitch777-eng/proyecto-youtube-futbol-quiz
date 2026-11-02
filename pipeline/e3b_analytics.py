#!/usr/bin/env python3
"""
Etapa 3b · ANALYTICS (permiso yt-analytics.readonly): lo que YouTube no muestra en público, medido solo y todos los días.
Reparto de tareas: este script = los NÚMEROS de cada video (exactos, con historia, automáticos).
La IA de YouTube Studio = el "eligió ver" (visto vs. descartado), ideas, tendencias y explicaciones (ver reports/preguntas_ia_youtube.md).

Mide:
- por video: vistas, vistas comprometidas, % promedio visto, duración media, likes, comentarios, compartidos, suscriptores ganados
- curva de retención de los últimos videos (en qué momento se va la gente y si se repite el loop)
- fuentes de tráfico, países, edades, dispositivos, suscriptos vs. no suscriptos (canal)
- resumen por formato: mediana de % visto y de suscriptores cada 1.000 vistas (para que la fábrica decida qué repetir y qué podar)
Salida: datos/analytics.json + datos/analytics_historia.json (una foto por día, para comparar antes/después de cada cambio)
Sin el permiso: deja la etapa "pendiente" con el aviso (no rompe nada).
"""
import statistics as st
from datetime import datetime, timedelta, timezone

import requests

from comun import cargar, etapa, guardar, token_canal

API = "https://youtubeanalytics.googleapis.com/v2/reports"
INICIO = "2026-10-20"
CURVAS = 12                     # curvas de retención de los últimos N videos


def reporte(tok, **p):
    p = {"ids": "channel==MINE", "startDate": INICIO, "endDate": datetime.now(timezone.utc).date().isoformat(), **p}
    r = requests.get(API, params=p, headers={"Authorization": f"Bearer {tok}"}, timeout=60)
    if r.status_code != 200:
        raise RuntimeError(f"{r.status_code} {r.text[:300]}")
    j = r.json(); cols = [c["name"] for c in j.get("columnHeaders", [])]
    return [dict(zip(cols, fila)) for fila in j.get("rows", [])]


def main():
    try:
        tok = token_canal()
    except Exception as e:
        tok = None; print("permiso rechazado:", e)
    if not tok:
        etapa("analytics", "pendiente", aviso="Falta el permiso del canal."); return
    try:
        por_video = reporte(tok, dimensions="video", sort="-views", maxResults=200,
                            metrics="views,engagedViews,estimatedMinutesWatched,averageViewDuration,averageViewPercentage,"
                                    "likes,comments,shares,subscribersGained")
    except RuntimeError as e:
        msg = str(e)
        if msg.startswith("403") or "insufficient" in msg.lower() or "scope" in msg.lower():
            etapa("analytics", "pendiente", aviso="El permiso del canal no incluye YouTube Analytics (yt-analytics.readonly). "
                                                  "Ver los pasos en reports/preguntas_ia_youtube.md.", detalle=msg[:200])
        else:
            etapa("analytics", "error", detalle=msg[:300])
        print(msg); return

    tipos = {p["video_id"]: p for p in cargar("publicados.json", []) if p.get("video_id")}
    rend = {v["id"]: v for v in cargar("rendimiento.json", {}).get("videos", [])}
    for v in por_video:
        vid = v["video"]
        v["tipo"] = (tipos.get(vid) or {}).get("tipo") or (rend.get(vid) or {}).get("tipo") or "otros"
        if (tipos.get(vid) or {}).get("variante"):                             # pruebas A/B: se comparan por separado (ej. stop/estrella vs stop/grilla)
            v["tipo"] += "/" + tipos[vid]["variante"]
        v["titulo"] = (rend.get(vid) or {}).get("titulo", "")
        v["subs_cada_1000"] = round(1000 * v["subscribersGained"] / v["views"], 2) if v["views"] else 0

    def seguro(nombre, **p):
        try:
            return reporte(tok, **p)
        except RuntimeError as e:
            print("sin", nombre, e); return []

    curvas = {}
    for v in sorted(por_video, key=lambda v: (tipos.get(v["video"]) or {}).get("subido", ""), reverse=True)[:CURVAS]:
        filas = seguro("curva", dimensions="elapsedVideoTimeRatio", filters=f"video=={v['video']}",
                       metrics="audienceWatchRatio,relativeRetentionPerformance")
        if filas:
            curvas[v["video"]] = [[round(f["elapsedVideoTimeRatio"], 2), round(f["audienceWatchRatio"], 3),
                                   round(f.get("relativeRetentionPerformance", 0), 3)] for f in filas]
    canal = dict(
        trafico=seguro("tráfico", dimensions="insightTrafficSourceType", metrics="views", sort="-views"),
        paises=seguro("países", dimensions="country", metrics="views,averageViewPercentage", sort="-views", maxResults=15),
        edades=seguro("edades", dimensions="ageGroup,gender", metrics="viewerPercentage"),
        dispositivos=seguro("dispositivos", dimensions="deviceType", metrics="views"),
        suscripcion=seguro("suscripción", dimensions="subscribedStatus", metrics="views,averageViewPercentage"),
        por_dia=seguro("por día", dimensions="day", metrics="views,subscribersGained,averageViewPercentage", sort="day"),
    )
    formatos = {}
    for v in por_video:
        if v["views"] >= 300:                                                  # con menos vistas el % es ruido
            formatos.setdefault(v["tipo"], []).append(v)
    resumen = {k: dict(videos=len(x), mediana_pct_visto=round(st.median(y["averageViewPercentage"] for y in x), 1),
                       mediana_subs_cada_1000=round(st.median(y["subs_cada_1000"] for y in x), 2),
                       mediana_vistas=round(st.median(y["views"] for y in x))) for k, x in formatos.items()}
    hoy = datetime.now(timezone(timedelta(hours=-3))).date().isoformat()
    guardar("analytics.json", dict(fecha=hoy, por_video=por_video, por_formato=resumen, curvas=curvas, canal=canal))
    hist = cargar("analytics_historia.json", {})
    hist[hoy] = dict(por_formato=resumen, videos={v["video"]: [v["views"], v["averageViewPercentage"], v["subscribersGained"]] for v in por_video})
    guardar("analytics_historia.json", dict(sorted(hist.items())[-120:]))
    etapa("analytics", "ok", videos=len(por_video),
          por_formato={k: f"{x['videos']} videos · {x['mediana_pct_visto']}% visto · {x['mediana_subs_cada_1000']} subs/1000"
                       for k, x in resumen.items()})
    print("analytics ok:", len(por_video), "videos ·", resumen)


if __name__ == "__main__":
    main()
