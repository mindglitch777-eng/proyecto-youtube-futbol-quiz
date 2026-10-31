#!/usr/bin/env python3
"""
Etapa 3 · NUESTRO RENDIMIENTO: cómo rindió cada formato en el canal.
Vistas públicas (API con clave) de todas nuestras subidas; el formato sale de datos/publicados.json (lo anota la subida)
o, para los videos viejos, del título. Se compara a igual edad: vistas a las 48 h estimadas = vistas * min(1, 48 / horas)^0.5.
Si hay permiso de Analytics (OAuth con yt-analytics.readonly), suma "se quedó a mirar" y % visto.
Salida: datos/rendimiento.json
"""
import re
import statistics as st
from datetime import datetime, timezone

from comun import CONFIG, cargar, etapa, guardar, yt, yt_videos

PATRONES = [("stop", r"stop challenge"), ("find", r"^find |find the real|can find"), ("look", r"look"),
            ("cabeza", r"right head|head back|which head"), ("runner", r"day 1|day 999"), ("ring", r"rings"),
            ("carrera", r"race"), ("otros", r".")]


def formato_por_titulo(t):
    t = t.lower()
    return next(k for k, p in PATRONES if re.search(p, t))


def main():
    etapa("rendimiento", "en_curso")
    publicados = {p["video_id"]: p["tipo"] for p in cargar("publicados.json", []) if p.get("video_id")}
    ups = "UU" + CONFIG["canal_id"][2:]
    ids, tok = [], None
    while True:
        r = yt("playlistItems", part="contentDetails", playlistId=ups, maxResults=50, **({"pageToken": tok} if tok else {}))
        ids += [i["contentDetails"]["videoId"] for i in r.get("items", [])]
        tok = r.get("nextPageToken")
        if not tok:
            break
    ahora = datetime.now(timezone.utc)
    videos = []
    for v in yt_videos(ids):
        pub = datetime.fromisoformat(v["snippet"]["publishedAt"].replace("Z", "+00:00"))
        horas = max(1.0, (ahora - pub).total_seconds() / 3600)
        vistas = int(v["statistics"].get("viewCount", 0))
        tipo = publicados.get(v["id"]) or formato_por_titulo(v["snippet"]["title"])
        videos.append(dict(id=v["id"], titulo=v["snippet"]["title"], tipo=tipo, vistas=vistas, horas=round(horas),
                           likes=int(v["statistics"].get("likeCount", 0) or 0), vistas_48h=round(vistas * min(1.0, (48 / horas)) ** 0.5)))
    por = {}
    for v in videos:
        if v["horas"] >= 24:                                                   # todavía no terminó su prueba
            por.setdefault(v["tipo"], []).append(v["vistas_48h"])
    resumen = {k: dict(videos=len(x), mediana_48h=round(st.median(x)), mejor=max(x)) for k, x in por.items()}
    guardar("rendimiento.json", dict(fecha=ahora.isoformat(timespec="seconds"), videos=sorted(videos, key=lambda v: -v["vistas"]), por_formato=resumen))
    etapa("rendimiento", "ok", videos=len(videos), vistas_totales=sum(v["vistas"] for v in videos),
          por_formato={k: f"{x['videos']} videos · mediana {x['mediana_48h']:,} · mejor {x['mejor']:,}" for k, x in resumen.items()})


if __name__ == "__main__":
    main()
