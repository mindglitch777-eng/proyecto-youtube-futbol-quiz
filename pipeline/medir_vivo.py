#!/usr/bin/env python3
"""
Medidor EN VIVO (corre cada hora): vistas, likes y comentarios de cada video del canal + suscriptores, con una serie
hora a hora para dibujar la curva de cada video. Con el permiso de estadísticas (OAuth yt-analytics.readonly) suma
retención: % promedio visto, duración promedio, suscriptores ganados y compartidos por video y por formato.
(YouTube entrega Analytics con 1-2 días de demora; las vistas públicas son casi en tiempo real.)

Uso: python3 pipeline/medir_vivo.py <carpeta_salida>   → <carpeta>/vivo.json (lo lee la app del tablero)
"""
import json
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import requests

from comun import CONFIG, cargar, token_canal, yt, yt_videos
from e3_rendimiento import formato_por_titulo

MAX_PUNTOS = 24 * 14                                                           # 14 días de serie horaria por video


def analytics(tok, desde, hasta):
    base = "https://youtubeanalytics.googleapis.com/v2/reports"
    h = {"Authorization": f"Bearer {tok}"}
    def rep(**p):
        r = requests.get(base, headers=h, params=dict(ids="channel==MINE", startDate=desde, endDate=hasta, **p), timeout=60)
        if r.status_code != 200:
            return {"error": f"{r.status_code} {r.text[:200]}"}
        j = r.json(); cols = [c["name"] for c in j.get("columnHeaders", [])]
        return [dict(zip(cols, fila)) for fila in j.get("rows", [])]
    return dict(
        por_video=rep(dimensions="video", metrics="views,estimatedMinutesWatched,averageViewDuration,averageViewPercentage,subscribersGained,likes,shares,comments",
                      sort="-views", maxResults=200),
        por_dia=rep(dimensions="day", metrics="views,estimatedMinutesWatched,subscribersGained", sort="day"))


def main():
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "_vivo"); out.mkdir(parents=True, exist_ok=True)
    previo = json.loads((out / "vivo.json").read_text()) if (out / "vivo.json").exists() else {}
    series = {v["id"]: v.get("serie", []) for v in previo.get("videos", [])}
    ahora = datetime.now(timezone.utc); marca = ahora.strftime("%Y-%m-%dT%H:%M")
    canal = yt("channels", part="statistics,contentDetails", id=CONFIG["canal_id"])["items"][0]
    ups = canal["contentDetails"]["relatedPlaylists"]["uploads"]
    ids, tok = [], None
    while True:
        r = yt("playlistItems", part="contentDetails", playlistId=ups, maxResults=50, **({"pageToken": tok} if tok else {}))
        ids += [i["contentDetails"]["videoId"] for i in r.get("items", [])]
        tok = r.get("nextPageToken")
        if not tok:
            break
    tipos = {p["video_id"]: p["tipo"] for p in cargar("publicados.json", []) if p.get("video_id")}
    videos = []
    for v in yt_videos(ids):
        st = v["statistics"]; vistas = int(st.get("viewCount", 0))
        serie = series.get(v["id"], [])
        if not serie or serie[-1][0] != marca:
            serie.append([marca, vistas])
        videos.append(dict(id=v["id"], titulo=v["snippet"]["title"], publicado=v["snippet"]["publishedAt"],
                           tipo=tipos.get(v["id"]) or formato_por_titulo(v["snippet"]["title"]), vistas=vistas,
                           likes=int(st.get("likeCount", 0) or 0), comentarios=int(st.get("commentCount", 0) or 0), serie=serie[-MAX_PUNTOS:]))
    videos.sort(key=lambda x: x["publicado"], reverse=True)
    cst = canal["statistics"]
    hist = previo.get("canal_serie", [])
    if not hist or hist[-1][0] != marca:
        hist.append([marca, int(cst.get("viewCount", 0)), int(cst.get("subscriberCount", 0))])
    vivo = dict(actualizado=ahora.isoformat(timespec="seconds"),
                canal=dict(vistas=int(cst.get("viewCount", 0)), suscriptores=int(cst.get("subscriberCount", 0)), videos=int(cst.get("videoCount", 0))),
                canal_serie=hist[-MAX_PUNTOS:], videos=videos)
    tok = token_canal()
    if tok:
        hoy = date.today()
        vivo["analytics"] = analytics(tok, (hoy - timedelta(days=28)).isoformat(), hoy.isoformat())
        vivo["analytics"]["periodo"] = "últimos 28 días"
    else:
        vivo["analytics"] = {"aviso": "Falta el permiso de estadísticas (YT_CLIENT_ID / YT_CLIENT_SECRET / YT_REFRESH_TOKEN con yt-analytics.readonly)."}
    (out / "vivo.json").write_text(json.dumps(vivo, ensure_ascii=False))
    print(marca, len(videos), "videos", vivo["canal"])


if __name__ == "__main__":
    main()
