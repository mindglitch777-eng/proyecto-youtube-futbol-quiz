#!/usr/bin/env python3
"""
Frente A: ¿cómo y cuándo se hacen virales los shorts?

Toma los shorts publicados en los últimos N días que ya medimos (data/raw/videos.json, con la hora
exacta de esa medición = fecha del archivo de cache de la API) y los vuelve a medir AHORA.
Con dos fotos en el tiempo calcula la velocidad (vistas/hora) de cada video.

Uso: python3 research/velocidad.py medir [dias=90]   -> data/raw/snapshots/<fecha>.json (1 unidad c/50 videos)
     python3 research/velocidad.py analizar          -> data/processed/velocidad.csv + resumen
"""
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
import yt_research as Y  # noqa: E402

RAW = Y.RAW
SNAP = RAW / "snapshots"
SNAP.mkdir(exist_ok=True)


def medicion_base():
    """id -> (hora de la medición, vistas, likes, comentarios) de la primera vez que se bajó cada video."""
    base = {}
    for f in (RAW / "api" / "videos").glob("*.json"):
        t = datetime.fromtimestamp(f.stat().st_mtime, timezone.utc).isoformat()
        for it in json.loads(f.read_text())["respuesta"].get("items", []):
            st = it.get("statistics", {})
            if it["id"] not in base or t < base[it["id"]][0]:
                base[it["id"]] = (t, int(st.get("viewCount", 0)), int(st.get("likeCount", 0) or 0), int(st.get("commentCount", 0) or 0))
    return base


def medir(dias=90):
    videos = Y.cargar("videos.json", {})
    lim = datetime.now(timezone.utc).timestamp() - dias * 86400
    ids = [v["id"] for v in videos.values() if (v["duration_s"] or 999) <= 180
           and datetime.fromisoformat(v["publishedAt"].replace("Z", "+00:00")).timestamp() >= lim]
    ahora = datetime.now(timezone.utc)
    out = {"medido": ahora.isoformat(), "videos": {}}
    for k in range(0, len(ids), 50):
        _, usado = Y.quota()
        if usado + 1 > Y.QUOTA_CAP:
            print("tope de cuota"); break
        r = requests.get(Y.BASE + "videos", params={"part": "statistics", "id": ",".join(ids[k:k + 50]), "key": Y.KEY}, timeout=60)
        Y.gastar(1)
        for it in r.json().get("items", []):
            st = it.get("statistics", {})
            out["videos"][it["id"]] = [int(st.get("viewCount", 0)), int(st.get("likeCount", 0) or 0), int(st.get("commentCount", 0) or 0)]
    dest = SNAP / f"{ahora.strftime('%Y-%m-%dT%H%M')}.json"
    dest.write_text(json.dumps(out))
    print(f"{len(out['videos'])} videos medidos -> {dest.name}; cuota hoy {Y.quota()[1]}")


def analizar():
    import pandas as pd
    base = medicion_base()
    snaps = sorted(SNAP.glob("*.json"))
    ultimo = json.loads(snaps[-1].read_text())
    t1 = datetime.fromisoformat(ultimo["medido"])
    videos = Y.cargar("videos.json", {})
    fmt = Y.cargar("gemini_formatos.json", {})
    can = pd.read_csv(Y.ROOT / "data/processed/canales.csv").set_index("channelId")
    filas = []
    for vid, (v1, l1, c1) in ultimo["videos"].items():
        if vid not in base or vid not in videos:
            continue
        t0s, v0, l0, c0 = base[vid]
        t0 = datetime.fromisoformat(t0s)
        horas = (t1 - t0).total_seconds() / 3600
        if horas < 2:
            continue
        v = videos[vid]
        pub = datetime.fromisoformat(v["publishedAt"].replace("Z", "+00:00"))
        edad_d = (t1 - pub).total_seconds() / 86400
        vph = (v1 - v0) / horas
        prom_vida = v1 / max(edad_d * 24, 1)
        ch = v["channelId"]
        filas.append({
            "id": vid, "url": f"https://youtube.com/shorts/{vid}", "canal": v["channelTitle"], "titulo": v["title"],
            "edad_dias": round(edad_d, 2), "horas_entre_mediciones": round(horas, 1), "vistas": v1,
            "vistas_ganadas": v1 - v0, "vistas_por_hora": round(vph), "prom_vida_por_hora": round(prom_vida),
            "aceleracion": round(vph / prom_vida, 2) if prom_vida else None,
            "likes_ganados": l1 - l0, "coment_ganados": c1 - c0,
            "formato": fmt.get(vid, {}).get("f"), "cara": fmt.get(vid, {}).get("cara"), "idioma": fmt.get(vid, {}).get("idioma"),
            "subs_canal": can.loc[ch, "subs"] if ch in can.index else None,
            "mediana_canal": can.loc[ch, "mediana_vistas_ult"] if ch in can.index else None,
            "duracion_s": v["duration_s"],
        })
    df = pd.DataFrame(filas)
    df.to_csv(Y.ROOT / "data/processed/velocidad.csv", index=False)
    print(len(df), "videos con dos mediciones")
    return df


if __name__ == "__main__":
    if sys.argv[1] == "medir":
        if not Y.KEY:
            raise SystemExit("Falta YOUTUBE_API_KEY")
        medir(int(sys.argv[2]) if len(sys.argv) > 2 else 90)
    else:
        analizar()
