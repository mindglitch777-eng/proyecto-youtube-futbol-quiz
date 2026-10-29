#!/usr/bin/env python3
"""
Arma el dataset para estudiar cómo se mueve el algoritmo de Shorts en fútbol (reporte 25).
Semillas: canales de virales_rapidos.csv + canales con algún short de fútbol de 1M+ en los últimos 3 meses.
Por canal: estadísticas + hasta 300 subidas con vistas, duración, fecha y título.
Salida: data/raw/algoritmo/{canales,videos}.json

Uso: YOUTUBE_API_KEY=... python3 research/algoritmo_dataset.py
"""
import csv
import json
import os
import re
from pathlib import Path

import requests

B = "https://www.googleapis.com/youtube/v3/"
K = os.environ["YOUTUBE_API_KEY"]
RAIZ = Path(__file__).resolve().parents[1]
OUT = RAIZ / "data" / "raw" / "algoritmo"
DESDE = "2026-07-29T00:00:00Z"
BUSQUEDAS = ["football shorts", "ronaldo shorts", "messi shorts", "football edit", "football quiz",
             "find the real ronaldo", "football evolution", "football funny", "yamal shorts", "football challenge",
             "futbol shorts", "ronaldo vs messi"]
MAX_CANALES, MAX_VIDEOS = 130, 300


def get(ep, **p):
    r = requests.get(B + ep, params={**p, "key": K}, timeout=60)
    r.raise_for_status()
    return r.json()


def dur_s(iso):
    m = re.match(r"P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso or "")
    d, h, mi, s = (int(x or 0) for x in m.groups()) if m else (0, 0, 0, 0)
    return d * 86400 + h * 3600 + mi * 60 + s


def detalles(ids):
    out = []
    for k in range(0, len(ids), 50):
        out += get("videos", part="snippet,statistics,contentDetails", id=",".join(ids[k:k + 50]))["items"]
    return out


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    semillas = {}
    with open(RAIZ / "data" / "processed" / "virales_rapidos.csv") as f:
        for row in csv.DictReader(f):
            semillas[row["canal_id"]] = "virales_rapidos"
    for q in BUSQUEDAS:
        ids = [i["id"]["videoId"] for i in get("search", part="snippet", q=q, type="video", videoDuration="short",
                                                 order="viewCount", publishedAfter=DESDE, maxResults=50)["items"]]
        for v in detalles(ids):
            if int(v["statistics"].get("viewCount", 0)) >= 1_000_000:
                semillas.setdefault(v["snippet"]["channelId"], "busqueda:" + q)
        print(q, len(semillas), flush=True)
    previo = json.loads((OUT / "videos.json").read_text()) if (OUT / "videos.json").exists() else {}
    canales, videos = {}, previo
    cids = list(semillas)[:MAX_CANALES]
    for k in range(0, len(cids), 50):
        for c in get("channels", part="snippet,statistics,contentDetails", id=",".join(cids[k:k + 50]))["items"]:
            canales[c["id"]] = dict(id=c["id"], titulo=c["snippet"]["title"], creado=c["snippet"]["publishedAt"],
                                    pais=c["snippet"].get("country"), subs=int(c["statistics"].get("subscriberCount", 0)),
                                    vistas=int(c["statistics"].get("viewCount", 0)), n_videos=int(c["statistics"].get("videoCount", 0)),
                                    origen=semillas[c["id"]], uploads=c["contentDetails"]["relatedPlaylists"]["uploads"])
    for n, c in enumerate(canales.values()):
        ids, tok = [], None
        while len(ids) < MAX_VIDEOS:
            try:
                p = get("playlistItems", part="contentDetails", playlistId=c["uploads"], maxResults=50, pageToken=tok)
            except requests.HTTPError:
                break
            ids += [i["contentDetails"]["videoId"] for i in p.get("items", [])]
            tok = p.get("nextPageToken")
            if not tok:
                break
        nuevos = [i for i in ids if i not in videos]
        for v in detalles(nuevos):
            sn, st = v["snippet"], v["statistics"]
            videos[v["id"]] = dict(id=v["id"], canal=sn["channelId"], publicado=sn["publishedAt"], titulo=sn["title"],
                                   dur=dur_s(v["contentDetails"].get("duration")), vistas=int(st.get("viewCount", 0)),
                                   likes=int(st["likeCount"]) if "likeCount" in st else None,
                                   coment=int(st["commentCount"]) if "commentCount" in st else None,
                                   tags=sn.get("tags", [])[:15], idioma=sn.get("defaultAudioLanguage"))
        print(n + 1, c["titulo"], len(ids), flush=True)
    (OUT / "canales.json").write_text(json.dumps(canales, ensure_ascii=False, indent=1))
    (OUT / "videos.json").write_text(json.dumps(videos, ensure_ascii=False))
    print(len(canales), "canales", len(videos), "videos")


if __name__ == "__main__":
    main()
