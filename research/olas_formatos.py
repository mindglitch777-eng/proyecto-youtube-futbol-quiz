#!/usr/bin/env python3
"""
OLAS DE FORMATOS: qué formatos de Shorts de fútbol explotan Y se sostienen (no videos sueltos).
1. ~45 búsquedas de Shorts de fútbol de los últimos 45 días (por vistas).
2. Canales detrás de los virales: fecha de creación, suscriptores, vistas.
3. Para los canales que crecieron rápido: sus últimos ~200 videos → cuántos Shorts hasta el primer 100k / 1M, % de hits,
   mediana reciente (¿se sostiene?), ritmo de subida y qué tan repetido es el formato (títulos con la misma plantilla).
Salida: data/raw/olas/{videos,canales,detalle}.json

Uso: YOUTUBE_API_KEY=... python3 research/olas_formatos.py
"""
import json
import re
import statistics as st
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "pipeline"))
from comun import yt, yt_videos  # noqa: E402

OUT = RAIZ / "data" / "raw" / "olas"
QS = ["football shorts", "soccer shorts", "football challenge", "football quiz", "guess the player football", "football edit",
      "football animation", "football ai video", "messi vs ronaldo", "football simulation", "marble race football", "football game shorts",
      "fc mobile", "pack opening fc", "football rating", "football tier list", "football trivia", "who is better football",
      "football meme", "brainrot football", "football 3d animation", "penalty challenge", "football transformation", "football evolution",
      "guess the footballer", "football emoji quiz", "spin the wheel football", "football draft", "football card", "football ranking",
      "football comparison", "football race", "ronaldo ai", "messi ai", "yamal ai", "neymar shorts", "satisfying football",
      "football puzzle", "impossible football", "football stop challenge", "find the real football", "football plinko",
      "football hole challenge", "football hack", "football vs"]
DIAS = 45


def dur_s(iso):
    m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso or "")
    return sum(int(x or 0) * k for x, k in zip(m.groups(), (3600, 60, 1))) if m else 0


def plantilla(t):
    """Título → plantilla (sin números, nombres propios ni emojis) para medir si el canal repite formato."""
    t = re.sub(r"[^\w\s?!]", " ", t.lower())
    t = re.sub(r"\d+", "#", t)
    pal = [w for w in t.split() if len(w) > 2][:5]
    return " ".join(pal)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    desde = (datetime.now(timezone.utc) - timedelta(days=DIAS)).strftime("%Y-%m-%dT%H:%M:%SZ")
    ids = {}
    for q in QS:
        try:
            r = yt("search", part="snippet", q=q, type="video", videoDuration="short", order="viewCount", publishedAfter=desde, maxResults=50)
        except Exception as e:
            print("búsqueda falló", q, e); break
        for it in r.get("items", []):
            ids.setdefault(it["id"]["videoId"], q)
        print(q, len(ids), flush=True)
    vids = []
    for v in yt_videos(list(ids)):
        s = v["statistics"]
        vids.append(dict(id=v["id"], titulo=v["snippet"]["title"], canal=v["snippet"]["channelId"], canal_nombre=v["snippet"]["channelTitle"],
                         publicado=v["snippet"]["publishedAt"], vistas=int(s.get("viewCount", 0)), likes=int(s.get("likeCount", 0) or 0),
                         comentarios=int(s.get("commentCount", 0) or 0), dur=dur_s(v["contentDetails"]["duration"]), busqueda=ids[v["id"]]))
    (OUT / "videos.json").write_text(json.dumps(vids, ensure_ascii=False, indent=1))
    grandes = [v for v in vids if v["vistas"] >= 300_000]
    cids = sorted({v["canal"] for v in grandes})
    canales = {}
    for k in range(0, len(cids), 50):
        for c in yt("channels", part="snippet,statistics,contentDetails", id=",".join(cids[k:k + 50]))["items"]:
            s = c["statistics"]
            canales[c["id"]] = dict(id=c["id"], nombre=c["snippet"]["title"], creado=c["snippet"]["publishedAt"],
                                    subs=int(s.get("subscriberCount", 0) or 0), vistas=int(s.get("viewCount", 0)), videos=int(s.get("videoCount", 0)),
                                    uploads=c["contentDetails"]["relatedPlaylists"]["uploads"],
                                    virales_45d=sum(1 for v in grandes if v["canal"] == c["id"]))
    ahora = datetime.now(timezone.utc)
    for c in canales.values():
        dias = max(1, (ahora - datetime.fromisoformat(c["creado"].replace("Z", "+00:00"))).days)
        c["dias"] = dias; c["vistas_dia"] = c["vistas"] / dias
    (OUT / "canales.json").write_text(json.dumps(list(canales.values()), ensure_ascii=False, indent=1))
    # canales que crecieron rápido: los de más vistas por día (máx. 70)
    rapidos = sorted(canales.values(), key=lambda c: -c["vistas_dia"])[:70]
    detalle = []
    for c in rapidos:
        vids_c, tok = [], None
        for _ in range(4):                                                     # hasta 200 videos
            r = yt("playlistItems", part="contentDetails", playlistId=c["uploads"], maxResults=50, **({"pageToken": tok} if tok else {}))
            vids_c += [i["contentDetails"]["videoId"] for i in r.get("items", [])]
            tok = r.get("nextPageToken")
            if not tok:
                break
        data = yt_videos(vids_c)
        filas = sorted([dict(id=v["id"], t=v["snippet"]["title"], p=v["snippet"]["publishedAt"], v=int(v["statistics"].get("viewCount", 0)),
                             d=dur_s(v["contentDetails"]["duration"])) for v in data], key=lambda x: x["p"])
        shorts = [f for f in filas if f["d"] <= 180]
        if len(shorts) < 5:
            continue
        def primero(umbral):
            return next((i + 1 for i, f in enumerate(shorts) if f["v"] >= umbral), None)
        recientes = shorts[-30:]
        plant = Counter(plantilla(f["t"]) for f in shorts[-50:])
        top_pl, n_pl = plant.most_common(1)[0]
        dias_act = max(1, (datetime.fromisoformat(shorts[-1]["p"].replace("Z", "+00:00")) - datetime.fromisoformat(shorts[0]["p"].replace("Z", "+00:00"))).days)
        detalle.append(dict(
            canal=c["nombre"], id=c["id"], creado=c["creado"][:10], subs=c["subs"], vistas=c["vistas"], videos_total=c["videos"],
            shorts_vistos=len(shorts), completo=len(vids_c) >= c["videos"],
            hasta_100k=primero(100_000), hasta_1m=primero(1_000_000), hasta_10m=primero(10_000_000),
            hits_100k_pct=round(100 * sum(f["v"] >= 100_000 for f in recientes) / len(recientes)),
            hits_1m_pct=round(100 * sum(f["v"] >= 1_000_000 for f in recientes) / len(recientes)),
            mediana_ult30=int(st.median(f["v"] for f in recientes)), max_v=max(f["v"] for f in shorts),
            subidas_dia=round(len(shorts) / dias_act, 2), dur_mediana=int(st.median(f["d"] for f in recientes)),
            formato_repetido_pct=round(100 * n_pl / min(50, len(shorts))), plantilla=top_pl,
            titulos_top=[f["t"] for f in sorted(shorts, key=lambda x: -x["v"])[:8]],
            titulos_recientes=[f["t"] for f in shorts[-8:]],
            top_ids=[f["id"] for f in sorted(shorts, key=lambda x: -x["v"])[:3]]))
        print(c["nombre"], len(shorts), detalle[-1]["hasta_1m"], detalle[-1]["mediana_ult30"], flush=True)
    (OUT / "detalle.json").write_text(json.dumps(detalle, ensure_ascii=False, indent=1))
    print(len(vids), "videos", len(canales), "canales", len(detalle), "con detalle")


if __name__ == "__main__":
    main()
