#!/usr/bin/env python3
"""
Módulo D: curvas de crecimiento de canales jóvenes con historial completo
(data/raw/channel_history.json). No gasta cuota.

ESTIMACIÓN (la API no da historial de vistas ni de suscriptores): ordenamos los
videos por fecha y acumulamos sus vistas ACTUALES. "Día en que llegó a 10M" =
primer día en que la suma de vistas actuales de lo ya publicado supera 10M.
Sobreestima la velocidad (los videos viejos siguieron sumando después), así que
es una cota optimista. Subs: no hay historial; se informa subs actuales / videos.
Salida: data/processed/crecimiento.csv, data/processed/horarios.csv
"""
import json
import statistics as st
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW, PROC = ROOT / "data" / "raw", ROOT / "data" / "processed"
ART = ZoneInfo("America/Argentina/Buenos_Aires")


def f(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


videos = json.loads((RAW / "videos.json").read_text())
canales = json.loads((RAW / "channels.json").read_text())
hist = json.loads((RAW / "channel_history.json").read_text())
cls = pd.read_csv(PROC / "canales.csv").set_index("channelId")
filas, horas = [], []
for cid, ids in hist.items():
    vs = sorted((videos[i] for i in ids if i in videos), key=lambda v: v["publishedAt"])
    if not vs:
        continue
    c = canales[cid]
    t0 = f(vs[0]["publishedAt"])
    acum, hitos = 0, {}
    for n, v in enumerate(vs, 1):
        acum += v["views"]
        for meta in (1e6, 1e7, 2e7):
            if acum >= meta and meta not in hitos:
                hitos[meta] = ((f(v["publishedAt"]) - t0).days, n)
    dias = max((f(vs[-1]["publishedAt"]) - t0).days, 1)
    views = [v["views"] for v in vs]
    med = st.median(views)
    # ritmo por semana y rendimiento: ¿semanas con más subidas rinden menos por video?
    df = pd.DataFrame({"t": [f(v["publishedAt"]) for v in vs], "views": views})
    df["sem"] = df["t"].dt.tz_localize(None).dt.to_period("W")
    sem = df.groupby("sem").agg(n=("views", "size"), med=("views", "median"))
    corr = sem["n"].rank().corr(sem["med"].rank()) if len(sem) >= 6 else None
    # primeros 30 días
    p30 = [v for v in vs if (f(v["publishedAt"]) - t0).days < 30]
    filas.append({
        "canal": c["title"], "channelId": cid, "url": f"https://youtube.com/channel/{cid}",
        "creado": c["publishedAt"][:10], "primer_video": vs[0]["publishedAt"][:10],
        "clase": cls.loc[cid, "clase"] if cid in cls.index else None,
        "idioma": cls.loc[cid, "idioma_principal"] if cid in cls.index else None,
        "formato_principal": cls.loc[cid, "formato_principal"] if cid in cls.index else None,
        "pct_con_cara": cls.loc[cid, "pct_con_cara"] if cid in cls.index else None,
        "subs": c["subs"], "vistas": c["views"], "videos": len(vs), "dias_activo": dias,
        "videos_por_dia": round(len(vs) / dias, 2),
        "mediana_vistas": int(med), "pct_10x": round(sum(x >= 10 * med for x in views) / len(views), 3),
        "pct_1M": round(sum(x >= 1e6 for x in views) / len(views), 3),
        "top1_pct_de_vistas": round(max(views) / sum(views), 2) if sum(views) else None,
        "dias_a_1M_est": hitos.get(1e6, (None,))[0], "videos_a_1M": hitos.get(1e6, (None, None))[1],
        "dias_a_10M_est": hitos.get(1e7, (None,))[0], "videos_a_10M": hitos.get(1e7, (None, None))[1],
        "dias_a_20M_est": hitos.get(2e7, (None,))[0], "videos_a_20M": hitos.get(2e7, (None, None))[1],
        "videos_primeros_30d": len(p30), "vistas_primeros_30d": sum(v["views"] for v in p30),
        "corr_subidas_semana_vs_mediana": round(corr, 2) if corr is not None and corr == corr else None,
    })
    for v in vs:
        t = f(v["publishedAt"])
        horas.append({"canal": c["title"], "hora_utc": t.hour, "hora_art": t.astimezone(ART).hour, "vistas": v["views"],
                      "x_mediana": v["views"] / med if med else None})
pd.DataFrame(filas).sort_values("vistas", ascending=False).to_csv(PROC / "crecimiento.csv", index=False)
h = pd.DataFrame(horas)
(h.groupby("hora_art").agg(videos=("vistas", "size"), canales=("canal", "nunique"),
                            mediana_x_mediana_canal=("x_mediana", "median"))
  .round(2).to_csv(PROC / "horarios.csv"))
print(pd.DataFrame(filas).sort_values("vistas", ascending=False).drop(columns=["channelId", "url"]).to_string())
