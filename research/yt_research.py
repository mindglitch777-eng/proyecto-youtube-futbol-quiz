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
    ("spin the wheel football", "en", True),
    ("ruleta futbol armo mi equipo", "es", True),
    ("guess the jersey football", "en", True),
    ("would you rather football", "en", True),
    ("football bingo", "en", True),
    ("adivina el jugador por la silueta", "es", True),
]

# validación de los formatos propuestos (24-oct, 2da tanda)
PROPUESTOS_SEEDS = [
    ("encuentra al verdadero messi", "es", True),
    ("find the real ronaldo", "en", True),
    ("adivina el jugador por la sombra", "es", True),
    ("name that player football", "en", True),
    ("en que equipos jugo adivina el futbolista", "es", True),
    ("career path football quiz", "en", True),
    ("verdadero o falso fútbol quiz", "es", True),
    ("true or false football quiz", "en", True),
]

# frente B (25-oct): mecánicas interactivas virales en OTROS nichos, para trasladar al fútbol
NICHOS_SEEDS = [(q, "en", True) for q in [
    "guess the celebrity", "guess the nba player", "guess the anime character", "guess the rapper", "guess the country",
    "guess the flag", "guess the logo", "guess the song", "guess the movie", "guess the price",
    "find the odd one out", "spot the difference", "optical illusion test", "eye test only 1%", "memory test",
    "brain test only genius", "which one is real", "pick one", "would you rather", "higher or lower game",
    "guess the fusion", "guess by the eyes", "guess by the voice", "guess the zoomed", "blurry picture guess",
    "guess the age", "who is older", "if they were", "ai version of", "evolution of",
    "guess the character by shadow", "count the", "find the hidden", "riddle only smart people", "what happens next",
]]

# frente C (25-oct): competencia en fútbol de las mecánicas candidatas + validación de la fusión
FUTBOL_MEC_SEEDS = [(q, "en", True) for q in [
    "footballer evolution", "evolution of messi", "guess the footballer evolution", "football evolution shorts",
    "only one door is real football", "pick a door football", "guess the footballer by voice", "guess the anthem football",
    "face fusion football", "2 players 1 face", "guess the fused footballers", "merged footballers",
    "footballers ai version", "footballers if they were",
]]

# validación del cruce "menos explotado + más fuerte": candidatas top de oportunidad_mecanicas.csv
CRUCE_SEEDS = [(q, "en", True) for q in [
    "guess the footballer by emoji", "football emoji quiz", "guess the club by emoji",
    "guess the footballer age", "how old is this footballer",
    "football true or false", "football myth or fact",
    "footballers then and now quiz", "guess the young footballer", "guess the footballer as a kid",
    "how many footballers can you count", "guess the footballer by celebration sound",
]]

# candidatos a formato nuevo (patrón fuerte + mecánica poco usada en fútbol)
NUEVOS_SEEDS = [(q, "en", True) for q in [
    "football squad then vs now", "prime vs now football team", "football marble race", "footballers race simulation",
    "countries marble race", "football riddle", "guess the player by career path", "higher or lower football",
    "guess the transfer fee", "find the ball football", "football who would win", "guess the footballer by hairstyle",
    "football tier list",
]]

# simulaciones físicas (pelota en círculo giratorio con arcos, bouncing ball, predicciones)
SIM_SEEDS = [(q, "en", True) for q in [
    "football simulation rotating circle goal", "ball in rotating circle goal football", "bouncing ball football simulation",
    "world cup prediction simulation ball", "football match simulation circle", "penalty simulation ball circle",
    "who will win simulation football", "ball escape circle football", "countryballs football simulation",
    "satisfying ball simulation football", "football physics simulation who wins", "champions league prediction simulation",
    "el clasico simulation", "messi vs ronaldo simulation ball", "football marble simulation goal",
    "spinning circle football goal", "rotating ring ball goal simulation", "ball bouncing inside circle goal",
    "who will win world cup simulation circle", "country ball inside circle goal", "football prediction bouncing ball",
    "flag ball simulation football", "goal simulation who scores first",
]]

# mercados: misma consulta acotada por país (regionCode) para comparar tamaño y competencia
MARKET_SEEDS = [
    ("quiz de futbol", "es", "AR"),
    ("quiz de futbol", "es", "MX"),
    ("quiz de futbol", "es", "ES"),
    ("football quiz", "en", "US"),
    ("football quiz", "en", "GB"),
    ("quiz de futebol", "pt", "BR"),
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


def cmd_markets():
    hits = cargar("search_hits.json", [])
    hechas = {(h["q"], h.get("region")) for h in hits}
    videos = cargar("videos.json", {})
    nuevos = []
    for q, lang, region in MARKET_SEEDS:
        if (q, region) in hechas:
            continue
        d = api("search", part="snippet", q=q, type="video", videoDuration="short", order="viewCount",
                maxResults=50, relevanceLanguage=lang, regionCode=region, publishedAfter=HACE_12M)
        ids = [it["id"]["videoId"] for it in d.get("items", []) if it["id"].get("videoId")]
        hits.append({"q": q, "lang": lang, "region": region, "ultimos_12m": True, "video_ids": ids,
                     "total_estimado": d.get("pageInfo", {}).get("totalResults")})
        nuevos += ids
        guardar("search_hits.json", hits)
        print(f"  '{q}' [{region}]: {len(ids)}", file=sys.stderr)
    detalles_videos(nuevos, videos)
    guardar("videos.json", videos)


# muestra SIN sesgo de éxito: lo último que se subió (order=date), para ver cómo le va
# al canal típico que hace quizzes de fútbol, no solo a los que pegaron
FRESH_SEEDS = [("football quiz", "en"), ("quiz de futbol", "es"), ("adivina el jugador", "es"),
               ("guess the player", "en"), ("trivia futbol", "es"), ("quiz futebol", "pt"),
               ("impostor futbol", "es"), ("guess the footballer", "en"), ("adivina el escudo", "es"),
               ("football trivia", "en"), ("adivina el futbolista", "es"), ("preguntas de futbol", "es")]


def cmd_fresh():
    out = cargar("fresh_sample.json", {})
    canales_out = cargar("fresh_channels.json", {})
    for q, lang in FRESH_SEEDS:
        if q in out:
            continue
        d = api("search", part="snippet", q=q, type="video", videoDuration="short", order="date",
                maxResults=50, relevanceLanguage=lang)
        out[q] = [{"videoId": it["id"]["videoId"], "channelId": it["snippet"]["channelId"],
                   "publishedAt": it["snippet"]["publishedAt"]} for it in d.get("items", []) if it["id"].get("videoId")]
        guardar("fresh_sample.json", out)
    ids = list(dict.fromkeys(x["channelId"] for v in out.values() for x in v if x["channelId"] not in canales_out))
    for k in range(0, len(ids), 50):
        d = api("channels", part="snippet,statistics", id=",".join(ids[k:k + 50]))
        for it in d.get("items", []):
            st = it.get("statistics", {})
            canales_out[it["id"]] = {"title": it["snippet"]["title"], "publishedAt": it["snippet"]["publishedAt"],
                                     "subs": int(st.get("subscriberCount", 0)), "views": int(st.get("viewCount", 0)),
                                     "videos": int(st.get("videoCount", 0))}
    guardar("fresh_channels.json", canales_out)
    print(f"muestra fresca: {sum(len(v) for v in out.values())} videos, {len(canales_out)} canales", file=sys.stderr)


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


def cmd_channels(top_canales=220, extra_ids=()):
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
    ids = [c for c, _ in peso.most_common(top_canales)] + [c for c in extra_ids if c not in peso]
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
            if c["id"] not in ids:
                continue
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
        if cmd == "futbol_mec":
            cmd_search(FUTBOL_MEC_SEEDS)
        if cmd == "nichos":
            cmd_search(NICHOS_SEEDS)
        if cmd == "sim":
            cmd_search(SIM_SEEDS)
        if cmd == "nuevos":
            cmd_search(NUEVOS_SEEDS)
        if cmd == "cruce":
            cmd_search(CRUCE_SEEDS)
        if cmd == "propuestos":
            cmd_search(PROPUESTOS_SEEDS)
        if cmd == "fresco":
            cmd_fresh()
        if cmd == "mercados":
            cmd_markets()
        if cmd in ("iterate", "all"):
            cmd_iterate(arg or 8)
        if cmd in ("channels", "all"):
            cmd_channels()
        if cmd == "canales_quiz":
            # canales con shorts quiz (según Gemini) de >= 1M vistas que no entraron por ranking de búsqueda
            import csv
            filas = list(csv.DictReader(open(ROOT / "data" / "processed" / "videos.csv")))
            ya = cargar("channels.json", {})
            extra = list(dict.fromkeys(r["channelId"] for r in filas if r["es_quiz"] == "True"
                                       and r["en_busqueda"] == "True" and int(r["vistas"]) >= 1_000_000
                                       and r["channelId"] not in ya))
            cmd_channels(len(ya), extra)
        if cmd in ("history", "all"):
            cmd_history(arg or 20)
        if cmd == "comments":
            cmd_comments(arg or 60)
    except SinCuota as e:
        print("FRENO:", e, file=sys.stderr)
    print(f"cuota usada hoy ({dia_pacifico()} PT): {quota()[1]} / tope {QUOTA_CAP}", file=sys.stderr)
