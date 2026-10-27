#!/usr/bin/env python3
"""
Casos de estudio: historial COMPLETO (desde el primer video) de canales que crecieron de la nada.
Calcula días hasta el primer video de 1 M, el video que lo cambió todo, videos y días hasta 10 M acumulados
(umbral de YPP para Shorts), ritmo de subida y fórmula de títulos.
Uso: YOUTUBE_API_KEY=... python3 research/casos.py  -> data/raw/casos/<id>.json + data/processed/casos.csv
"""
import json
import re
import statistics as st
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import yt_research as Y  # noqa: E402

OUT = Y.RAW / "casos"; OUT.mkdir(exist_ok=True)
CANALES = {
    "FULYON SHORTS": "UC5PgkslN0-aal256mrdnyxg", "DriveLabs": "UC-3xq-bcNGEb0obHvSeIROQ", "Footrix": "UCGBigtxg8XGmR3F65KVBH4w",
    "MainFutLab": "UCS18jNCi118VWY9_1_Z8jtw", "Frox": "UCD2CLDW14h82BRSvjxGGRgQ", "Icon Stories": "UCH-4iUlUJR57mC4evjkLhGQ",
    "Fire Rankings": "UC2hGyiVFV1LZvdc1TLLucng", "Footypoints": "UCQg42PAMjcOz1-YoVkoJlcg", "Sphere Stars": "UCybOrEQ3PNWG54esMw_hy3Q",
    "Rival Stats": "UC8CFPYt0JQ1lPqAKWzd6bKg", "bouncyball": "UCSQvQmNMP6uC-3zaeCoyifA", "GreyHaT Sim": "UCDRJF1QAtjPnymkSAVIEoKQ",
}


def dur(s):
    m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", s or "")
    return int(m.group(1) or 0) * 3600 + int(m.group(2) or 0) * 60 + int(m.group(3) or 0) if m else None


def historial(cid):
    ch = Y.api("channels", part="snippet,statistics,contentDetails", id=cid)["items"][0]
    up = ch["contentDetails"]["relatedPlaylists"]["uploads"]
    ids, tok = [], None
    while True:
        kw = dict(part="contentDetails", playlistId=up, maxResults=50)
        if tok:
            kw["pageToken"] = tok
        p = Y.api("playlistItems", **kw)
        ids += [x["contentDetails"]["videoId"] for x in p.get("items", [])]
        tok = p.get("nextPageToken")
        if not tok or len(ids) >= 1500:
            break
    vids = []
    for k in range(0, len(ids), 50):
        for v in Y.api("videos", part="snippet,statistics,contentDetails", id=",".join(ids[k:k + 50])).get("items", []):
            vids.append({"id": v["id"], "fecha": v["snippet"]["publishedAt"], "titulo": v["snippet"]["title"],
                         "vistas": int(v["statistics"].get("viewCount", 0)), "dur": dur(v["contentDetails"]["duration"])})
    return ch, sorted(vids, key=lambda v: v["fecha"])


def main():
    filas = []
    for nombre, cid in CANALES.items():
        dst = OUT / f"{cid}.json"
        if dst.exists():
            d = json.loads(dst.read_text()); ch, vids = d["canal"], d["videos"]
        else:
            ch, vids = historial(cid)
            dst.write_text(json.dumps({"canal": ch, "videos": vids}, ensure_ascii=False))
        if not vids:
            continue
        f0 = datetime.fromisoformat(vids[0]["fecha"][:19])
        dias = lambda v: (datetime.fromisoformat(v["fecha"][:19]) - f0).days
        primer_m = next((v for v in vids if v["vistas"] >= 1e6), None)
        acum, d10 = 0, None
        for i, v in enumerate(vids):
            acum += v["vistas"]
            if acum >= 1e7 and d10 is None:
                d10 = (dias(v), i + 1)
        total = sum(v["vistas"] for v in vids)
        top = sorted(vids, key=lambda v: -v["vistas"])[:3]
        filas.append({
            "canal": nombre, "creado": ch["snippet"]["publishedAt"][:10], "primer_video": vids[0]["fecha"][:10],
            "videos": len(vids), "subs": int(ch["statistics"].get("subscriberCount", 0)), "vistas_total": total,
            "dias_al_primer_1M": dias(primer_m) if primer_m else None, "videos_al_primer_1M": vids.index(primer_m) + 1 if primer_m else None,
            "primer_1M": primer_m["titulo"][:70] if primer_m else None, "vistas_primer_1M": primer_m["vistas"] if primer_m else None,
            "dias_a_10M": d10[0] if d10 else None, "videos_a_10M": d10[1] if d10 else None,
            "ritmo_por_dia": round(len(vids) / max(dias(vids[-1]), 1), 2),
            "dur_mediana_s": st.median([v["dur"] for v in vids if v["dur"]]) if vids else None,
            "pct_1M": round(100 * sum(v["vistas"] >= 1e6 for v in vids) / len(vids), 1),
            "top": " | ".join(f"{t['vistas'] / 1e6:.1f}M {t['titulo'][:45]}" for t in top),
        })
    import pandas as pd
    df = pd.DataFrame(filas).sort_values("vistas_total", ascending=False)
    df.to_csv(Y.ROOT / "data/processed/casos.csv", index=False)
    pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 80)
    print(df.drop(columns=["top"]).to_string(index=False))
    for f in filas:
        print(f"\n{f['canal']}: {f['top']}")
    print(Y.quota())


if __name__ == "__main__":
    main()
