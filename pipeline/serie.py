#!/usr/bin/env python3
"""
MODO SERIE (22/11, CEO; patrón de los 24 canales que explotaron: cuando un video pega, lo REPITEN igual varios días).
- Un video "pegó" si, dentro de sus primeras 72 h, ya tiene ≥3 veces la mediana a 48 h del canal (últimos 14 días).
- Su formato entra en SERIE por 5 días: sale 1 vez por día (aunque no sea fijo) con el MISMO título base, cambiando los jugadores
  (la IA de YouTube: el 82 % del público es nuevo; repetir funciona, pero no dos títulos casi iguales el mismo día).
- Máximo 2 series a la vez; si el mismo formato vuelve a pegar, la serie se renueva con el título nuevo.
Estado: datos/series.json. Lo usa e4_plan (lugar diario) y fabrica (título).
"""
import re
import statistics as st
from datetime import date, datetime, timedelta, timezone

from comun import cargar, guardar

ART = timezone(timedelta(hours=-3))
DIAS_SERIE, MAX_SERIES, FACTOR = 5, 2, 3.0


def mediana_canal():
    desde = (datetime.now(ART).date() - timedelta(days=14)).isoformat()
    xs = [v["vistas_48h"] for v in cargar("rendimiento.json", {}).get("videos", [])
          if v.get("horas", 0) >= 48 and v.get("vistas_48h") is not None and v.get("publicado", "")[:10] >= desde]
    return st.median(xs) if len(xs) >= 10 else None


def actualizar(hoy=None):
    hoy = hoy or datetime.now(ART).date()
    series = {k: s for k, s in cargar("series.json", {}).items() if s["hasta"] >= hoy.isoformat()}   # vencidas afuera
    med = mediana_canal()
    if med:
        pub = {p["video_id"]: p for p in cargar("publicados.json", []) if p.get("video_id") and not p.get("cancelado")}
        for v in cargar("rendimiento.json", {}).get("videos", []):
            p = pub.get(v["id"])
            if not p or v.get("horas", 999) > 72 or v.get("vistas", 0) < FACTOR * med or p["tipo"] == "goles":
                continue
            s = series.get(p["tipo"])
            if s and s.get("vistas", 0) >= v["vistas"] and s.get("video") != v["id"]:
                continue
            if not s and len(series) >= MAX_SERIES:
                continue
            series[p["tipo"]] = dict(video=v["id"], titulo=p["titulo"], vistas=v["vistas"], x_canal=round(v["vistas"] / med, 1),
                                     desde=hoy.isoformat(), hasta=(hoy + timedelta(days=DIAS_SERIE)).isoformat())
            print(f"SERIE: {p['tipo']} · {v['vistas']:,} vistas ({v['vistas'] / med:.1f}x el canal) · «{p['titulo']}»", flush=True)
    guardar("series.json", series)
    return series


def activas(dia):
    return {k: s for k, s in cargar("series.json", {}).items() if s["desde"] <= dia <= s["hasta"]}


def titulo_serie(base, nombres, tag):
    """El título del video que pegó, con los jugadores nuevos (mismo armado; los hashtags se rehacen)."""
    t = " ".join(w for w in base.split() if not w.startswith("#"))
    import fabrica as F                                                        # nombres conocidos (JUGADORES + NOMBRE)
    conocidos = sorted({n for n, _, _ in F.JUGADORES} | set(F.NOMBRE.values()) | {"Haaland", "R9", "Vinícius", "Mbappé"}, key=len, reverse=True)
    pat = re.compile(r"\b(" + "|".join(re.escape(n) for n in conocidos) + r")\b")
    nuevos = [n for n in nombres if isinstance(n, str)]
    usados = {}

    def cambio(m):
        viejo = m.group(1)
        if viejo not in usados:
            usados[viejo] = nuevos[len(usados)] if len(usados) < len(nuevos) else viejo
        return usados[viejo]
    t = pat.sub(cambio, t)
    for n in nuevos[:3]:
        if len(t) + len(tag(n)) + 1 <= 100:
            t += " " + tag(n)
    return t


if __name__ == "__main__":
    print(actualizar())
