#!/usr/bin/env python3
"""
Etapa 1 · RADAR: los shorts de fútbol que más explotaron en los últimos N días.
Puntaje = vistas por hora desde la publicación (velocidad), con bonus si el canal es nuevo (creado este año) o chico.
Salida: datos/radar.json (top ordenado) para que el análisis mire primero lo más caliente.
"""
from datetime import datetime, timedelta, timezone

from comun import CONFIG, etapa, guardar, yt, yt_videos


def dur_s(iso):
    import re
    m = re.match(r"P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso or "")
    d, h, mi, s = (int(x or 0) for x in m.groups()) if m else (0, 0, 0, 0)
    return d * 86400 + h * 3600 + mi * 60 + s


def main():
    etapa("radar", "en_curso")
    cfg = CONFIG["radar"]
    ahora = datetime.now(timezone.utc)
    desde = (ahora - timedelta(days=cfg["dias"])).strftime("%Y-%m-%dT%H:%M:%SZ")
    ids = {}
    for q in cfg["busquedas"]:
        for it in yt("search", part="snippet", q=q, type="video", videoDuration="short", order="viewCount",
                     publishedAfter=desde, maxResults=50)["items"]:
            ids.setdefault(it["id"]["videoId"], q)
    vids = [v for v in yt_videos(list(ids)) if 0 < dur_s(v["contentDetails"]["duration"]) <= 180
            and int(v["statistics"].get("viewCount", 0)) >= cfg["minimo_vistas"] and v["snippet"]["channelId"] != CONFIG["canal_id"]]
    canales = {}
    cids = list({v["snippet"]["channelId"] for v in vids})
    for k in range(0, len(cids), 50):
        for c in yt("channels", part="snippet,statistics", id=",".join(cids[k:k + 50]))["items"]:
            canales[c["id"]] = dict(titulo=c["snippet"]["title"], creado=c["snippet"]["publishedAt"][:10],
                                    subs=int(c["statistics"].get("subscriberCount", 0)), videos=int(c["statistics"].get("videoCount", 0)))
    filas = []
    for v in vids:
        pub = datetime.fromisoformat(v["snippet"]["publishedAt"].replace("Z", "+00:00"))
        horas = max(1.0, (ahora - pub).total_seconds() / 3600)
        vistas = int(v["statistics"].get("viewCount", 0))
        c = canales.get(v["snippet"]["channelId"], {})
        nuevo = c.get("creado", "0000") >= f"{ahora.year}-01-01"
        filas.append(dict(id=v["id"], titulo=v["snippet"]["title"], canal=c.get("titulo"), canal_creado=c.get("creado"), canal_subs=c.get("subs"),
                          canal_videos=c.get("videos"), vistas=vistas, likes=int(v["statistics"].get("likeCount", 0) or 0),
                          comentarios=int(v["statistics"].get("commentCount", 0) or 0), horas=round(horas, 1),
                          vistas_por_hora=round(vistas / horas), dur=dur_s(v["contentDetails"]["duration"]), busqueda=ids[v["id"]],
                          canal_nuevo=nuevo, puntaje=round(vistas / horas * (1.5 if nuevo else 1.0) * (1.3 if (c.get("subs") or 0) < 100_000 else 1.0))))
    filas.sort(key=lambda f: -f["puntaje"])
    guardar("radar.json", dict(fecha=ahora.isoformat(timespec="seconds"), busquedas=len(cfg["busquedas"]), virales=filas))
    etapa("radar", "ok", virales=len(filas), canales_nuevos=sum(f["canal_nuevo"] for f in filas),
          top=[dict(titulo=f["titulo"][:70], canal=f["canal"], vistas=f["vistas"], vph=f["vistas_por_hora"]) for f in filas[:5]])


if __name__ == "__main__":
    main()
