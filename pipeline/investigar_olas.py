#!/usr/bin/env python3
"""
INVESTIGACIÓN DE OLAS (API de YouTube): qué mecánicas de Shorts de fútbol están explotando AHORA y cuáles no.
Busca muchas consultas (por mecánica y generales) en 2 ventanas: últimos 3 días y últimos 7 días. Clasifica cada video por familia
(stop, wheel, fit, find, dress, quiz, goat, balance, 3D/IA, skills, memes, transformaciones, satisfying) y calcula por familia:
cantidad, videos con +1 M, mediana de vistas, vistas por hora, cuántos canales CHICOS (<100k subs) la rompieron, duración típica.
Salida: pipeline/datos/olas.json + resumen impreso. Corre en GitHub Actions (secreto YOUTUBE_API_KEY).
"""
import re
import statistics as st
from datetime import datetime, timedelta, timezone

from comun import CONFIG, guardar, yt, yt_videos
from e1_radar import dur_s

CONSULTAS = [
    "stop challenge football", "pause challenge football", "can you stop at 100 football", "stop at 67 football",
    "ronaldo vs messi or mbappe stop challenge", "fit challenge football", "head fit challenge ronaldo",
    "find ronaldo messi yamal", "find the real messi", "dressing challenge ronaldo yamal", "football drip challenge",
    "guess the football player", "football quiz shorts", "who is the best footballer", "goat messi ronaldo shorts",
    "balance challenge football", "football 3d animation shorts", "football ai video shorts", "ronaldo cartoon game",
    "football skills shorts", "football funny shorts", "football meme shorts", "football transformation shorts",
    "satisfying football shorts", "football marble race", "football plinko", "yamal shorts", "ronaldo shorts", "messi shorts",
    "mbappe shorts", "neymar shorts", "football challenge shorts", "football edit shorts",
]
FAMILIAS = [
    ("wheel", r"\bvs\b.+\bor\b|wheel|spin"), ("fit", r"\bfit\b"), ("stop", r"stop|pause"), ("find", r"\bfind\b|spot the"),
    ("dress", r"dress|drip|outfit|style"), ("quiz", r"guess|quiz|who is this|which club|name the"),
    ("goat", r"best|goat|who would win|who wins|who is better"), ("balance", r"balance|wall"),
    ("3d_ia", r"animation|3d|roblox|cartoon|parody|\bai\b|\bia\b|game"), ("transformacion", r"day 1|transform|evolution|then and now|before"),
    ("satisfying", r"satisfying|falling|tower|marble|plinko|race"), ("skills", r"skill|dribbl|goal|edit|nutmeg"),
    ("meme", r"funny|meme|😂|🤣|lol|prank"),
]


def familia(t):
    t = t.lower()
    return next((k for k, p in FAMILIAS if re.search(p, t)), "otros")


def buscar(desde):
    ids = {}
    for q in CONSULTAS:
        try:
            for it in yt("search", part="snippet", q=q, type="video", videoDuration="short", order="viewCount",
                         publishedAfter=desde, maxResults=50)["items"]:
                ids.setdefault(it["id"]["videoId"], q)
        except Exception as e:
            print("falló", q, e)
    return ids


def main():
    ahora = datetime.now(timezone.utc)
    salida = {}
    for nombre, dias in (("7d", 7), ("3d", 3)):
        desde = (ahora - timedelta(days=dias)).strftime("%Y-%m-%dT%H:%M:%SZ")
        ids = buscar(desde)
        vids = [v for v in yt_videos(list(ids)) if 0 < dur_s(v["contentDetails"]["duration"]) <= 180 and v["snippet"]["channelId"] != CONFIG["canal_id"]]
        cids = list({v["snippet"]["channelId"] for v in vids}); subs = {}
        for k in range(0, len(cids), 50):
            for c in yt("channels", part="statistics,snippet", id=",".join(cids[k:k + 50]))["items"]:
                subs[c["id"]] = (int(c["statistics"].get("subscriberCount", 0)), c["snippet"]["publishedAt"][:10])
        filas = []
        for v in vids:
            h = max(1.0, (ahora - datetime.fromisoformat(v["snippet"]["publishedAt"].replace("Z", "+00:00"))).total_seconds() / 3600)
            vistas = int(v["statistics"].get("viewCount", 0)); s, creado = subs.get(v["snippet"]["channelId"], (0, ""))
            filas.append(dict(id=v["id"], titulo=v["snippet"]["title"], canal=v["snippet"]["channelTitle"], subs=s, creado=creado,
                              vistas=vistas, horas=round(h), vph=round(vistas / h), dur=dur_s(v["contentDetails"]["duration"]),
                              likes=int(v["statistics"].get("likeCount", 0) or 0), coment=int(v["statistics"].get("commentCount", 0) or 0),
                              familia=familia(v["snippet"]["title"])))
        fam = {}
        for f in filas:
            fam.setdefault(f["familia"], []).append(f)
        resumen = {}
        for k, xs in fam.items():
            vs = [x["vistas"] for x in xs]
            chicos = [x for x in xs if x["subs"] < 100_000 and x["vistas"] >= 1_000_000]
            resumen[k] = dict(videos=len(xs), mas_1M=sum(v >= 1_000_000 for v in vs), mas_100k=sum(v >= 100_000 for v in vs),
                              mediana=round(st.median(vs)), total=sum(vs), vph_mediana=round(st.median(x["vph"] for x in xs)),
                              canales_chicos_1M=len(chicos), dur_mediana=round(st.median(x["dur"] for x in xs)),
                              like_ratio=round(1000 * sum(x["likes"] for x in xs) / max(1, sum(vs)), 1),
                              top=[dict(id=x["id"], titulo=x["titulo"][:80], vistas=x["vistas"], subs=x["subs"], dur=x["dur"])
                                   for x in sorted(xs, key=lambda x: -x["vistas"])[:5]])
        salida[nombre] = dict(videos=len(filas), familias=dict(sorted(resumen.items(), key=lambda kv: -kv[1]["total"])),
                              filas=sorted(filas, key=lambda f: -f["vistas"])[:400])
        print(f"\n===== últimos {dias} días: {len(filas)} videos")
        for k, r in salida[nombre]["familias"].items():
            print(f"{k:<15} {r['videos']:>4} videos | +1M: {r['mas_1M']:>3} | +100k: {r['mas_100k']:>3} | mediana {r['mediana']:>9,} | "
                  f"vph {r['vph_mediana']:>7,} | chicos+1M {r['canales_chicos_1M']:>2} | dur {r['dur_mediana']}s | likes/1000 {r['like_ratio']}")
    if salida.get("3d", {}).get("videos", 0) < 200 or salida.get("7d", {}).get("videos", 0) < 200:
        print("búsqueda incompleta (¿cuota de la API agotada?): NO se pisan los datos buenos"); return
    # ---- DETECTOR DE OLAS: cada mecánica comparada con los días anteriores (ventana de 3 días)
    from comun import cargar
    hist = cargar("olas_historia.json", {})
    hoy = ahora.date().isoformat()
    hist[hoy] = {k: dict(vph=r["vph_mediana"], med=r["mediana"], m1M=r["mas_1M"], n=r["videos"]) for k, r in salida["3d"]["familias"].items()}
    hist = dict(sorted(hist.items())[-30:])
    previos = [v for d, v in hist.items() if d < hoy][-4:]
    estado = {}
    for k, r in hist[hoy].items():
        antes = [p[k]["vph"] for p in previos if k in p]
        base = sum(antes) / len(antes) if antes else None
        ratio = (r["vph"] / base) if base else None
        r7 = salida.get("7d", {}).get("familias", {}).get(k)
        if base is None and r7:                                                 # sin historia: últimos 3 días vs. últimos 7
            cuota = r["m1M"] / max(1, r7["mas_1M"])                             # lo normal es ~3/7 = 0,43 de los +1M en 3 días
            # (los de 3 días tuvieron menos tiempo para llegar al millón: lo "normal" es ~0,2-0,3)
            ratio = 1.5 if (cuota >= 0.4 and r["m1M"] >= 2) else (0.5 if (r7["mas_1M"] >= 3 and cuota <= 0.1) else 1.0)
            base = r["vph"] / ratio
        if r["med"] < 15_000 and r["m1M"] == 0:
            e = "muerta"
        elif base is None:
            e = "naciente" if r["m1M"] >= 2 else "estable"
        elif ratio >= 1.3:
            e = "subiendo"
        elif ratio <= 0.7:
            e = "bajando"
        else:
            e = "estable"
        estado[k] = dict(estado=e, vph=r["vph"], vph_antes=round(base) if base else None, m1M_3d=r["m1M"], mediana_3d=r["med"])
    guardar("olas_historia.json", hist)
    salida["estado"] = estado
    print("\nESTADO DE LAS OLAS:", {k: v["estado"] for k, v in estado.items()})
    guardar("olas.json", dict(fecha=ahora.isoformat(timespec="seconds"), **salida))


if __name__ == "__main__":
    main()
