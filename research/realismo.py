#!/usr/bin/env python3
"""
Tasa de éxito SIN sesgo: canales que subieron un quiz de fútbol en los últimos días
(búsquedas order=date, data/raw/fresh_sample.json) y cómo les va hoy (fresh_channels.json).
Los títulos se leen del cache de la API (data/raw/api/search). No gasta cuota.
Salida: data/processed/realismo.csv y resumen por consola.
"""
import json
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data/raw"
titulos = {}
for f in (RAW / "api/search").glob("*.json"):
    d = json.loads(f.read_text())
    if d["params"].get("order") != "date":
        continue
    for it in d["respuesta"].get("items", []):
        if it["id"].get("videoId"):
            titulos[it["id"]["videoId"]] = (it["snippet"]["title"], it["snippet"]["channelId"])
FUT = re.compile(r"futbol|fútbol|football|soccer|futebol|jugador|player|jogador|futbolista|footballer|club|escudo|messi|"
                 r"ronaldo|cr7|yamal|mbapp|haaland|neymar|madrid|barça|barca|mundial|world cup|⚽|fifa|liga|equipo", re.I)
QUIZ = re.compile(r"adivin|quiz|trivia|guess|verdadero|true or false|qui[eé]n|who|impostor|sabes|know|pregunta|"
                  r"question|test|reto|challenge|acert|adivinhe|name|nombr", re.I)
ok = {cid for t, cid in titulos.values() if FUT.search(t) and QUIZ.search(t)}
c = pd.DataFrame([{"channelId": k, **v} for k, v in json.loads((RAW / "fresh_channels.json").read_text()).items()])
c = c[c.channelId.isin(ok)].copy()
c["creado"] = pd.to_datetime(c.publishedAt, format="ISO8601")
c["edad_dias"] = (pd.Timestamp("2026-10-24", tz="UTC") - c.creado).dt.days
c.to_csv(ROOT / "data/processed/realismo.csv", index=False)
print(f"canales que subieron un quiz de fútbol (por fecha): {len(c)}")
for nombre, g in [("todos", c), ("creados en los últimos 12 meses", c[c.edad_dias <= 365]),
                  ("últimos 12 meses y 30+ videos (intento serio)", c[(c.edad_dias <= 365) & (c.videos >= 30)])]:
    n = len(g)
    print(f"\n{nombre}: n={n}")
    if not n:
        continue
    for t in (1e5, 1e6, 1e7, 2e7):
        print(f"  >= {t:>12,.0f} vistas totales: {(g.views >= t).sum():3d} ({(g.views >= t).mean():.0%})")
    print(f"  >= 1.000 subs: {(g.subs >= 1000).sum()} ({(g.subs >= 1000).mean():.0%})")
    print(f"  >= 1.000 subs Y >= 10M vistas: {((g.subs >= 1000) & (g.views >= 1e7)).sum()}")
    print(f"  mediana subs {g.subs.median():.0f}, vistas {g.views.median():,.0f}, videos {g.videos.median():.0f}")
