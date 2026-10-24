#!/usr/bin/env python3
"""
Investigación de canales de quizzes de fútbol en Shorts con la API de YouTube v3.

- Lee la clave de YOUTUBE_API_KEY (nunca se guarda en el repo).
- Cachea cada respuesta en data/raw/api/ (si se corre de nuevo no gasta cuota).
- Lleva un contador de cuota por día del Pacífico (así resetea YouTube) en
  data/raw/quota.json, con tope configurable: QUOTA_CAP (default 9000).

Uso:
  python3 research/yt_research.py search      # Módulo A: búsquedas (100 u c/u)
  python3 research/yt_research.py formatos N  # búsquedas de formatos alternativos (las primeras N)
  python3 research/yt_research.py iterate     # 2da ronda con términos de los títulos top
  python3 research/yt_research.py channels    # stats de canales + últimos 50 videos
  python3 research/yt_research.py history N   # historial completo de los N canales chicos que más crecen
  python3 research/yt_research.py comments N  # comentarios de los N mejores shorts
  python3 research/yt_research.py all         # todo lo anterior en orden
"""
import hashlib
import json
import os
import re
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
CACHE = RAW / "api"
QUOTA_FILE = RAW / "quota.json"
KEY = os.environ.get("YOUTUBE_API_KEY")
QUOTA_CAP = int(os.environ.get("QUOTA_CAP", "9000"))
BASE = "https://www.googleapis.com/youtube/v3/"
COST = {"search": 100, "videos": 1, "channels": 1, "playlistItems": 1, "commentThreads": 1}
SHORT_MAX_S = 180  # desde oct-2024 un Short puede durar hasta 3 min

# fecha de referencia fija para que las búsquedas cacheadas sean reproducibles
HOY = datetime(2026, 10, 24, tzinfo=timezone.utc)
HACE_12M = (HOY - timedelta(days=365)).strftime("%Y-%m-%dT00:00:00Z")

# (consulta, idioma, solo últimos 12 meses)
SEEDS = [
    ("adivina el jugador futbol", "es", True),
    ("adivina el jugador por emojis", "es", True),
    ("adivina el escudo futbol", "es", True),
    ("quiz de futbol", "es", True),
    ("trivia de futbol", "es", True),
    ("verdadero o falso futbol", "es", True),
    ("solo los cracks saben futbol", "es", True),
    ("adivina el jugador por su carrera", "es", True),
    ("adivina el estadio futbol", "es", True),
    ("adivina el fichaje", "es", True),
    ("preguntas de futbol", "es", True),
    ("cuanto sabes de futbol", "es", True),
    ("adivina el equipo futbol", "es", True),
    ("quiz mundial futbol", "es", True),
    ("adivina el jugador argentino", "es", True),
    ("football quiz", "en", True),
    ("guess the player", "en", True),
    ("guess the footballer emoji", "en", True),
    ("guess the club logo", "en", True),
    ("football trivia", "en", True),
    ("soccer quiz", "en", True),
    ("guess the player by career", "en", True),
    ("guess the stadium football", "en", True),
    ("only real fans football quiz", "en", True),
    ("quiz de futebol", "pt", True),
    ("adivinhe o jogador", "pt", True),
    # todos los tiempos, para ver los clásicos del nicho
    ("adivina el jugador futbol", "es", False),
    ("quiz de futbol", "es", False),
    ("football quiz", "en", False),
    ("guess the player", "en", False),
]

# formatos de quiz/juego distintos al clásico (pedido del 24-oct)
FORMAT_SEEDS = [
    ("tier list futbol", "es", True),
    ("higher or lower football", "en", True),
    ("nombra un jugador futbol reto", "es", True),
    ("adivina el futbolista de niño", "es", True),
    # para correr con cuota de otro día
    ("who is better football", "en", True),
    ("elige un jugador futbol", "es", True),
    ("build your team football", "en", True),
    ("futbol 11 grid quien jugo con ambos", "es", True),
    ("this or that football", "en", True),
    ("ordena de mayor a menor futbol", "es", True),
]

QUIZ_WORDS = re.compile(
    r"adivin|quiz|trivia|guess|verdadero|falso|true or false|cuanto sabes|cuánto sabes|"
    r"quien es|quién es|who am i|who is|solo los|only real|test|pregunta|question|emoji|"
    r"adivinhe|acerta|sabes|know|challenge|desaf[ií]o|reto|imposible|impossible", re.I)


# ---------------------------------------------------------------- cuota / cache
def dia_pacifico():
    return datetime.now(ZoneInfo("America/Los_Angeles")).strftime("%Y-%m-%d")


def quota():
    q = json.loads(QUOTA_FILE.read_text()) if QUOTA_FILE.exists() else {}
    return q, q.get(dia_pacifico(), 0)


def gastar(units):
    q, usado = quota()
    q[dia_pacifico()] = usado + units
    QUOTA_FILE.write_text(json.dumps(q, indent=1))


class SinCuota(Exception):
    pass


def api(endpoint, **params):
    """GET a la API con cache en disco y control de cuota."""
    clave = json.dumps([endpoint, sorted(params.items())], ensure_ascii=False)
    h = hashlib.sha1(clave.encode()).hexdigest()[:16]
    dest = CACHE / endpoint / f"{h}.json"
    if dest.exists():
        return json.loads(dest.read_text())["respuesta"]
    costo = COST[endpoint]
    _, usado = quota()
    if usado + costo > QUOTA_CAP:
        raise SinCuota(f"tope de cuota alcanzado ({usado}/{QUOTA_CAP}); seguí mañana")
    r = requests.get(BASE + endpoint, params={**params, "key": KEY}, timeout=60)
    gastar(costo)
    if r.status_code != 200:
        err = r.json().get("error", {})
        motivos = [e.get("reason") for e in err.get("errors", [])]
        if "quotaExceeded" in motivos:
            raise SinCuota("YouTube dice quotaExceeded")
        # comentarios desactivados, etc.: se cachea el error para no repetir
        data = {"error": err}
    else:
        data = r.json()
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps({"endpoint": endpoint, "params": params, "respuesta": data}, ensure_ascii=False))
    return data


def dur_s(iso):
    m = re.match(r"P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso or "")
    if not m:
        return None
    d, h, mi, s = (int(x or 0) for x in m.groups())
    return d * 86400 + h * 3600 + mi * 60 + s


# ---------------------------------------------------------------- almacenamiento
def cargar(nombre, default):
    p = RAW / nombre
    return json.loads(p.read_text()) if p.exists() else default


def guardar(nombre, obj):
    (RAW / nombre).write_text(json.dumps(obj, ensure_ascii=False, indent=1))


def detalles_videos(ids, videos):
    """videos.list en tandas de 50; agrega a dict videos."""
    faltan = [i for i in dict.fromkeys(ids) if i not in videos]
    for k in range(0, len(faltan), 50):
        d = api("videos", part="snippet,contentDetails,statistics", id=",".join(faltan[k:k + 50]), maxResults=50)
        for it in d.get("items", []):
            sn, st = it["snippet"], it.get("statistics", {})
            videos[it["id"]] = {
                "id": it["id"],
                "channelId": sn["channelId"],
                "channelTitle": sn.get("channelTitle"),
                "title": sn["title"],
                "description": sn.get("description", "")[:1500],
                "tags": sn.get("tags", [])[:30],
                "publishedAt": sn["publishedAt"],
                "lang": sn.get("defaultAudioLanguage") or sn.get("defaultLanguage"),
                "duration_s": dur_s(it["contentDetails"].get("duration")),
                "views": int(st.get("viewCount", 0)),
                "likes": int(st["likeCount"]) if "likeCount" in st else None,
                "comments": int(st["commentCount"]) if "commentCount" in st else None,
            }
    return videos


# ---------------------------------------------------------------- módulos
def correr_busqueda(q, lang, recientes, hits):
    params = dict(part="snippet", q=q, type="video", videoDuration="short", order="viewCount",
                  maxResults=50, relevanceLanguage=lang, safeSearch="none")
    if recientes:
        params["publishedAfter"] = HACE_12M
    d = api("search", **params)
    ids = [it["id"]["videoId"] for it in d.get("items", []) if it["id"].get("videoId")]
    hits.append({"q": q, "lang": lang, "ultimos_12m": recientes, "video_ids": ids})
    print(f"  '{q}' [{lang}{', 12m' if recientes else ''}]: {len(ids)} videos", file=sys.stderr)
    return ids


def cmd_search(seeds=SEEDS):
    hits = cargar("search_hits.json", [])
    hechas = {(h["q"], h["lang"], h["ultimos_12m"]) for h in hits}
    videos = cargar("videos.json", {})
    nuevos = []
    for q, lang, rec in seeds:
        if (q, lang, rec) in hechas:
            continue
        nuevos += correr_busqueda(q, lang, rec, hits)
        guardar("search_hits.json", hits)
    detalles_videos(nuevos, videos)
    guardar("videos.json", videos)


STOP = set("""de el la los las y a en que un una por con para del al es se lo su sus mas más the of to and in a is
on for you your this who what with by from are be o vs shorts short futbol fútbol football soccer quiz trivia
futebol fyp viral parati foryou tiktok edit""".split())


def cmd_iterate(n=8):
    """Arma consultas nuevas con las palabras más frecuentes en los títulos top
    (ponderadas por vistas) que no aparecen en las consultas ya hechas."""
    videos = cargar("videos.json", {})
    hits = cargar("search_hits.json", [])
    usadas = set(" ".join(h["q"] for h in hits).lower().split())
    top = sorted((v for v in videos.values() if (v["duration_s"] or 999) <= SHORT_MAX_S and QUIZ_WORDS.search(v["title"])),
                 key=lambda v: -v["views"])[:300]
    bigramas = Counter()
    for v in top:
        toks = [t for t in re.findall(r"[a-záéíóúñü]+", v["title"].lower()) if len(t) > 2]
        for a, b in zip(toks, toks[1:]):
            if a in STOP or b in STOP or (a in usadas and b in usadas):
                continue
            bigramas[f"{a} {b}"] += 1
    propuestas = [b for b, c in bigramas.most_common(40) if c >= 3][:n]
    print("Términos nuevos desde títulos top:", propuestas, file=sys.stderr)
    guardar("iteracion_terminos.json", {"bigramas_top": bigramas.most_common(60), "elegidos": propuestas})
    seeds = []
    for p in propuestas:
        es = re.search(r"[ñáéíóú]|adivina|jugador|equipo|cual|quien", p)
        seeds.append((p + (" futbol" if es else " football"), "es" if es else "en", True))
    cmd_search(seeds)


def cmd_channels(top_canales=220):
    videos = cargar("videos.json", {})
    hits = cargar("search_hits.json", [])
    # canales que aparecen en búsquedas, ordenados por vistas sumadas de sus shorts encontrados
    peso, apariciones = Counter(), Counter()
    for h in hits:
        for vid in h["video_ids"]:
            v = videos.get(vid)
            if v and (v["duration_s"] or 999) <= SHORT_MAX_S and QUIZ_WORDS.search(v["title"] + " " + " ".join(v["tags"])):
                peso[v["channelId"]] += v["views"]
                apariciones[v["channelId"]] += 1
    ids = [c for c, _ in peso.most_common(top_canales)]
    canales = cargar("channels.json", {})
    faltan = [c for c in ids if c not in canales]
    for k in range(0, len(faltan), 50):
        d = api("channels", part="snippet,statistics,contentDetails,brandingSettings", id=",".join(faltan[k:k + 50]))
        for it in d.get("items", []):
            sn, st = it["snippet"], it.get("statistics", {})
            canales[it["id"]] = {
                "id": it["id"], "title": sn["title"], "customUrl": sn.get("customUrl"),
                "description": sn.get("description", "")[:800], "publishedAt": sn["publishedAt"],
                "country": sn.get("country"), "lang": sn.get("defaultLanguage"),
                "subs": int(st["subscriberCount"]) if not st.get("hiddenSubscriberCount") and "subscriberCount" in st else None,
                "views": int(st.get("viewCount", 0)), "videos": int(st.get("videoCount", 0)),
                "uploads": it["contentDetails"]["relatedPlaylists"]["uploads"],
            }
    for c in canales.values():
        c["apariciones_busqueda"] = apariciones.get(c["id"], 0)
    guardar("channels.json", canales)
    # últimos 50 subidos de cada canal (1 u de playlistItems + 1 u de videos.list)
    recientes = cargar("channel_recent.json", {})
    try:
        for c in sorted(canales.values(), key=lambda c: -peso.get(c["id"], 0)):
            if c["id"] in recientes:
                continue
            d = api("playlistItems", part="contentDetails", playlistId=c["uploads"], maxResults=50)
            vids = [it["contentDetails"]["videoId"] for it in d.get("items", [])]
            detalles_videos(vids, videos)
            recientes[c["id"]] = vids
    finally:
        guardar("channel_recent.json", recientes)
        guardar("videos.json", videos)
    print(f"canales: {len(canales)}, con últimos 50: {len(recientes)}, videos: {len(videos)}", file=sys.stderr)


def cmd_history(n=20, max_videos=700):
    """Historial completo de uploads de los canales jóvenes con más vistas/sub
    (para curvas de crecimiento del Módulo D)."""
    canales = cargar("channels.json", {})
    videos = cargar("videos.json", {})
    historial = cargar("channel_history.json", {})
    hace_18m = (HOY - timedelta(days=548)).isoformat()
    candidatos = [c for c in canales.values()
                  if c["publishedAt"] >= hace_18m and c["videos"] <= max_videos and c["views"] >= 1_000_000]
    candidatos.sort(key=lambda c: -c["views"])
    try:
        for c in candidatos[:n]:
            if c["id"] in historial:
                continue
            vids, token = [], None
            while True:
                kw = dict(part="contentDetails", playlistId=c["uploads"], maxResults=50)
                if token:
                    kw["pageToken"] = token
                d = api("playlistItems", **kw)
                vids += [it["contentDetails"]["videoId"] for it in d.get("items", [])]
                token = d.get("nextPageToken")
                if not token:
                    break
            detalles_videos(vids, videos)
            historial[c["id"]] = vids
            print(f"  historial {c['title']}: {len(vids)} videos", file=sys.stderr)
    finally:
        guardar("channel_history.json", historial)
        guardar("videos.json", videos)


def cmd_comments(n=60):
    videos = cargar("videos.json", {})
    elegidos = cargar("comments_targets.json", None)
    if elegidos is None:
        raise SystemExit("Falta data/raw/comments_targets.json (lo arma analyze.py)")
    out = cargar("comments.json", {})
    try:
        for vid in elegidos[:n]:
            if vid in out:
                continue
            d = api("commentThreads", part="snippet", videoId=vid, maxResults=100, order="relevance", textFormat="plainText")
            out[vid] = [{
                "text": it["snippet"]["topLevelComment"]["snippet"]["textDisplay"][:500],
                "likes": it["snippet"]["topLevelComment"]["snippet"].get("likeCount", 0),
                "replies": it["snippet"].get("totalReplyCount", 0),
                "author_is_channel": it["snippet"]["topLevelComment"]["snippet"].get("authorChannelId", {}).get("value")
                == videos.get(vid, {}).get("channelId"),
            } for it in d.get("items", [])] if "error" not in d else {"error": d["error"].get("message", "")[:200]}
    finally:
        guardar("comments.json", out)
    print(f"comentarios de {len(out)} videos", file=sys.stderr)


if __name__ == "__main__":
    if not KEY:
        raise SystemExit("Falta YOUTUBE_API_KEY")
    RAW.mkdir(parents=True, exist_ok=True)
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
    arg = int(sys.argv[2]) if len(sys.argv) > 2 else None
    try:
        if cmd in ("search", "all"):
            cmd_search()
        if cmd == "formatos":
            cmd_search(FORMAT_SEEDS[:arg] if arg else FORMAT_SEEDS)
        if cmd in ("iterate", "all"):
            cmd_iterate(arg or 8)
        if cmd in ("channels", "all"):
            cmd_channels()
        if cmd in ("history", "all"):
            cmd_history(arg or 20)
        if cmd == "comments":
            cmd_comments(arg or 60)
    except SinCuota as e:
        print("FRENO:", e, file=sys.stderr)
    print(f"cuota usada hoy ({dia_pacifico()} PT): {quota()[1]} / tope {QUOTA_CAP}", file=sys.stderr)
