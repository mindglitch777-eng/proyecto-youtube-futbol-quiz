#!/usr/bin/env python3
"""
Canales de fútbol que explotaron de la nada: su primer video de 1M+ fue uno de sus primeros 5.
Usa los videos ya bajados (data/raw/videos.json) + info de canal + historial de subidas (playlistItems).
Salida: data/processed/virales_rapidos.csv (un canal por fila, con el hit y su posición).
"""
import csv
import json
import re
import sys
from datetime import datetime
from pathlib import Path

sys.argv = sys.argv[:1]
import yt_research as Y

RAW = Path(__file__).resolve().parent.parent / "data" / "raw"
OUT = RAW.parent / "processed" / "virales_rapidos.csv"
F = re.compile(r"football|soccer|f[uú]tbol|futebol|messi|ronaldo|cr7|neymar|mbapp|yamal|haaland|real madrid|barcelona|bar[cç]a|"
               r"premier league|champions league|\bucl\b|\bgoal|\bgol\b|fifa|ballon|world cup|mundial|copa|libertadores|kane|"
               r"vinicius|bellingham|salah|ronaldinho|zidane|maradona|pel[eé]|benzema|modric|neymar|liverpool|arsenal|chelsea|psg|"
               r"juventus|bayern|boca|flamengo|penalt|free kick|footballer", re.I)
NO = re.compile(r"basketball|nba|mario|minecraft|cricket|ufc|boxing|muhammad ali", re.I)


def fecha(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def main():
    v = json.loads((RAW / "videos.json").read_text())
    ch = json.loads((RAW / "channels.json").read_text())
    extra_p = RAW / "channels_virales_extra.json"
    extra = json.loads(extra_p.read_text()) if extra_p.exists() else {}
    ch.update(extra)
    big = [x for x in v.values() if x["views"] >= 1e6 and (x["duration_s"] or 999) <= 180
           and F.search(x["title"] + " " + " ".join(x.get("tags", [])) + " " + x.get("description", "")[:300])
           and not NO.search(x["title"])]
    falt = sorted({x["channelId"] for x in big if x["channelId"] not in ch})
    for i in range(0, len(falt), 50):
        d = Y.api("channels", part="snippet,statistics,contentDetails", id=",".join(falt[i:i + 50]), maxResults=50)
        for it in d.get("items", []):
            sn, st = it["snippet"], it.get("statistics", {})
            extra[it["id"]] = ch[it["id"]] = dict(
                id=it["id"], title=sn["title"], publishedAt=sn["publishedAt"], country=sn.get("country"),
                subs=int(st.get("subscriberCount", 0)), views=int(st.get("viewCount", 0)), videos=int(st.get("videoCount", 0)),
                uploads=it["contentDetails"]["relatedPlaylists"]["uploads"])
    extra_p.write_text(json.dumps(extra, ensure_ascii=False, indent=1))
    cand = sorted({x["channelId"] for x in big if x["channelId"] in ch and fecha(ch[x["channelId"]]["publishedAt"]).year >= 2025
                   and (fecha(x["publishedAt"]) - fecha(ch[x["channelId"]]["publishedAt"])).days <= 150})
    hist_p = RAW / "virales_hist.json"
    hist = json.loads(hist_p.read_text()) if hist_p.exists() else {}
    for k in cand:
        if k in hist:
            continue
        ids, tok = [], None
        while True:
            p = dict(part="contentDetails", playlistId=ch[k]["uploads"], maxResults=50)
            if tok:
                p["pageToken"] = tok
            r = Y.api("playlistItems", **p)
            ids += [it["contentDetails"]["videoId"] for it in r.get("items", [])]
            tok = r.get("nextPageToken")
            if not tok or len(ids) >= 600:
                break
        hist[k] = ids[::-1]
    hist_p.write_text(json.dumps(hist))
    Y.detalles_videos([i for k in cand for i in hist[k][:15]], v)
    (RAW / "videos.json").write_text(json.dumps(v, ensure_ascii=False))
    filas = []
    for k in cand:
        pri = [v[i] for i in hist[k][:15] if i in v]
        idx = next((n for n, x in enumerate(pri, 1) if x["views"] >= 1e6), None)
        if not pri or idx is None or idx > 5:
            continue
        hit = pri[idx - 1]
        if NO.search(hit["title"]) or not F.search(hit["title"] + " " + " ".join(hit.get("tags", []))):
            continue
        filas.append(dict(canal=ch[k]["title"], canal_id=k, video_del_hit=idx,
                          dias_desde_1er_video=(fecha(hit["publishedAt"]) - fecha(pri[0]["publishedAt"])).days,
                          subs=ch[k]["subs"], videos_canal=len(hist[k]), hit_id=hit["id"], hit_vistas=hit["views"],
                          hit_titulo=hit["title"], hit_dur=hit["duration_s"], hit_fecha=hit["publishedAt"][:10],
                          primeros5=" | ".join(f"{x['views']}" for x in pri[:5])))
    filas.sort(key=lambda f: (f["video_del_hit"], -f["hit_vistas"]))
    with open(OUT, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(filas[0]))
        w.writeheader(); w.writerows(filas)
    print(len(filas), "canales; cuota", Y.quota()[1])


if __name__ == "__main__":
    main()
