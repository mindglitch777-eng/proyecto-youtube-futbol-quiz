#!/usr/bin/env python3
"""
Busca FORMATOS de shorts de fútbol que explotaron rápido en canales nuevos (creados en 2026), para tener varios
formatos que rotar (reporte 26).

1. Muchas búsquedas por tipo de formato (últimos 90 días, ordenadas por vistas).
2. Se quedan los canales creados en 2026 que tienen algún short de 500 K+.
3. De cada canal: todas sus subidas → en qué video y a los cuántos días llegó el primer hit, cuántos hits tiene,
   cadencia, y sus títulos (para clasificar el formato).
Salida: data/raw/formatos_nuevos/{busquedas,canales}.json

Uso: YOUTUBE_API_KEY=... python3 research/formatos_nuevos.py
"""
import json
import os
import re
from datetime import datetime
from pathlib import Path

import requests

B = "https://www.googleapis.com/youtube/v3/"
K = os.environ["YOUTUBE_API_KEY"]
OUT = Path(__file__).resolve().parents[1] / "data" / "raw" / "formatos_nuevos"
DESDE = "2026-07-31T00:00:00Z"
HIT = 500_000
QUERIES = [
    "guess the football player", "guess the player by", "who is stronger football", "football would you rather",
    "rate the footballer", "football ranking shorts", "football tier list", "which one is real football",
    "football emoji challenge", "football quiz shorts", "football transformation", "footballer as baby",
    "football players as", "football vs challenge", "messi vs ronaldo who wins", "football fake or real",
    "football player height comparison", "football players then and now", "football logo quiz", "guess the club",
    "football mystery box", "football spin wheel", "football pack opening", "football simulation marble",
    "football players outfit", "football car", "football celebration", "football players kids",
]


def get(ep, **p):
    r = requests.get(B + ep, params={**p, "key": K}, timeout=60)
    r.raise_for_status()
    return r.json()


def dur_s(iso):
    m = re.match(r"P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso or "")
    d, h, mi, s = (int(x or 0) for x in m.groups()) if m else (0, 0, 0, 0)
    return d * 86400 + h * 3600 + mi * 60 + s


def videos(ids):
    out = []
    for k in range(0, len(ids), 50):
        out += get("videos", part="snippet,statistics,contentDetails", id=",".join(ids[k:k + 50]))["items"]
    return out


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    busq, cand = {}, {}
    for q in QUERIES:
        ids = [i["id"]["videoId"] for i in get("search", part="snippet", q=q, type="video", videoDuration="short",
                                                 order="viewCount", publishedAfter=DESDE, maxResults=50)["items"]]
        vs = videos(ids)
        busq[q] = [dict(id=v["id"], canal=v["snippet"]["channelId"], titulo=v["snippet"]["title"],
                        vistas=int(v["statistics"].get("viewCount", 0)), publicado=v["snippet"]["publishedAt"]) for v in vs]
        for v in busq[q]:
            if v["vistas"] >= HIT:
                cand.setdefault(v["canal"], []).append(q)
        print(q, len(vs), "candidatos", len(cand), flush=True)
    (OUT / "busquedas.json").write_text(json.dumps(busq, ensure_ascii=False, indent=1))

    info = {}
    cids = list(cand)
    for k in range(0, len(cids), 50):
        for c in get("channels", part="snippet,statistics,contentDetails", id=",".join(cids[k:k + 50]))["items"]:
            if c["snippet"]["publishedAt"] >= "2026-01-01":
                info[c["id"]] = dict(titulo=c["snippet"]["title"], creado=c["snippet"]["publishedAt"], subs=int(c["statistics"].get("subscriberCount", 0)),
                                     n_videos=int(c["statistics"].get("videoCount", 0)), uploads=c["contentDetails"]["relatedPlaylists"]["uploads"],
                                     busquedas=cand[c["id"]])
    print(len(info), "canales nuevos", flush=True)
    for cid, c in info.items():
        ids, tok = [], None
        while len(ids) < 200:
            try:
                p = get("playlistItems", part="contentDetails", playlistId=c["uploads"], maxResults=50, pageToken=tok)
            except requests.HTTPError:
                break
            ids += [i["contentDetails"]["videoId"] for i in p.get("items", [])]
            tok = p.get("nextPageToken")
            if not tok:
                break
        vs = sorted(videos(ids), key=lambda v: v["snippet"]["publishedAt"])
        c["videos"] = [dict(id=v["id"], titulo=v["snippet"]["title"], publicado=v["snippet"]["publishedAt"], dur=dur_s(v["contentDetails"].get("duration")),
                            vistas=int(v["statistics"].get("viewCount", 0)), likes=int(v["statistics"].get("likeCount", 0) or 0),
                            coment=int(v["statistics"].get("commentCount", 0) or 0)) for v in vs]
        hits = [i for i, v in enumerate(c["videos"]) if v["vistas"] >= HIT]
        if hits and c["videos"]:
            f0 = datetime.fromisoformat(c["videos"][0]["publicado"][:19])
            h = c["videos"][hits[0]]
            c["primer_hit"] = dict(video_n=hits[0] + 1, dias=(datetime.fromisoformat(h["publicado"][:19]) - f0).days, vistas=h["vistas"], titulo=h["titulo"], id=h["id"])
            c["n_hits"] = len(hits)
        print(c["titulo"], len(c["videos"]), c.get("primer_hit", {}).get("video_n"), flush=True)
    (OUT / "canales.json").write_text(json.dumps(info, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
