#!/usr/bin/env python3
"""
ESTUDIO DE COMPETENCIA (21/11, pedido del CEO: "cómo evolucionaron los canales virales y qué hicieron para mantener la viralidad").
Para cada canal de la lista baja TODOS sus videos (fecha, vistas, duración, título) con la API de YouTube (barato: 1 unidad por
página de 50) y guarda la historia completa en reports/competencia/videos.json. El análisis se hace aparte (analizar_competencia).
Sin scraping: solo la API oficial. Corre en GitHub Actions (estudio_competencia.yml).
"""
import json
import re

from comun import RAIZ, yt, yt_videos

CANALES = {
    # referencias de las investigaciones anteriores (reportes 15, 17 y 20)
    "UC5PgkslN0-aal256mrdnyxg": "FULYON SHORTS", "UChr7usZtWvWet3w4vRUPQNw": "Funny Sharpener", "UCSY6No0ec_0BP_Z9Bm0C0Vg": "MStriker",
    "UCFa04zYV0EUB9NSr2-WD-LQ": "SpotVerse", "UCDDRq5ef2u8JaM-pf49LanA": "Migelftbl", "UC5_bl5EXSUXplvOj67NOQgg": "Muzam",
    "UCQg42PAMjcOz1-YoVkoJlcg": "Footypoints", "UCIlPE_mrOYGW-0tzilMa88g": "TIER", "UCOLow8szhPZjhDrQZmqz55A": "Goatline Theory",
    "UCqS4bcdaEwg24mctA5kPANA": "FootballRanks", "UCNOi0ZWYrhlo26d5M1G1jOQ": "MUK FT MIND", "UCuk5pDlj8SG7BTLQlqEMvBg": "SRD Game",
    # los que más explotaron esta semana en la investigación diaria
    "UC1-UVNyt7FggN5BMA4RIxOQ": "Zayden FC", "UC3LicumasYreZmhiYBCkAcQ": "RyukX", "UCAcw8q1UeGKQCT_5o4DIDCw": "PULSE",
    "UCPgTUHzLWt3ubMh5xDk6-ow": "Rono", "UCFxupmDJ4-9-bKUTFjKIV3A": "Danix", "UCscCo34Qi_ApBsm0GQGnT6g": "FootyEdits FC",
    "UCYTJQNcGDmSx6SJOHfQzqlQ": "PENALTY TIME", "UCy4__VoL7e11dJn6cLHniXw": "xrrftbl", "UCO0ikXESPLsRY_tcKZUQCOQ": "JOLLY FCC",
    "UC7hzHj2FLVtgGyOaVbR8O4g": "TURBO06", "UCyHBxsnw_nISlN4rvaGWsRw": "WEX TOON", "UCPjOBToQ50PnTg4-b6vEk0g": "Football POV Official",
    "UCFdCI9RSuLb1sbggcmv1bew": "zxpic7", "UC6m22Zend2aJkPhfMDrpnjg": "Sihax Fc",
}
MAX_PAGINAS = 16                                                                # hasta 800 videos por canal


def dur_s(iso):
    m = re.fullmatch(r"P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso or "")
    if not m:
        return 0
    d, h, mi, s = (int(x or 0) for x in m.groups())
    return d * 86400 + h * 3600 + mi * 60 + s


def main():
    out = {}
    cids = list(CANALES)
    info = {}
    for k in range(0, len(cids), 50):
        for c in yt("channels", part="snippet,statistics,contentDetails", id=",".join(cids[k:k + 50]))["items"]:
            info[c["id"]] = c
    for cid, nombre in CANALES.items():
        c = info.get(cid)
        if not c:
            print("no encontrado", nombre); continue
        ids, tok = [], None
        for _ in range(MAX_PAGINAS):
            r = yt("playlistItems", part="contentDetails", playlistId=c["contentDetails"]["relatedPlaylists"]["uploads"], maxResults=50,
                   **({"pageToken": tok} if tok else {}))
            ids += [it["contentDetails"]["videoId"] for it in r.get("items", [])]
            tok = r.get("nextPageToken")
            if not tok:
                break
        vids = []
        for v in yt_videos(ids):
            vids.append(dict(id=v["id"], t=v["snippet"]["title"][:140], pub=v["snippet"]["publishedAt"][:16],
                             dur=dur_s(v["contentDetails"]["duration"]), v=int(v["statistics"].get("viewCount", 0)),
                             l=int(v["statistics"].get("likeCount", 0) or 0), c=int(v["statistics"].get("commentCount", 0) or 0)))
        vids.sort(key=lambda x: x["pub"])
        out[cid] = dict(nombre=c["snippet"]["title"], creado=c["snippet"]["publishedAt"][:10], pais=c["snippet"].get("country"),
                        subs=int(c["statistics"].get("subscriberCount", 0)), vistas=int(c["statistics"].get("viewCount", 0)),
                        n_videos=int(c["statistics"].get("videoCount", 0)), videos=vids)
        print(f"{nombre}: {len(vids)} videos · {out[cid]['subs']:,} subs · {out[cid]['vistas']:,} vistas", flush=True)
    d = RAIZ / "reports" / "competencia"; d.mkdir(parents=True, exist_ok=True)
    (d / "videos.json").write_text(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    main()
