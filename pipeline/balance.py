#!/usr/bin/env python3
"""
BALANCE QUINCENAL (máquina sin IA, 15/11, pedido del CEO): ¿vamos más rápido o más lento hacia la monetización?
Compara las últimas 2 semanas contra las 2 anteriores:
- vistas por día y suscriptores por día del canal (serie en vivo, rama datos-vivos);
- videos de 10 K o más a 48 h por día (la métrica que manda);
- a este ritmo, cuántas semanas faltan para 10 M de vistas de Shorts en 90 días y para 1.000 suscriptores;
- mejores y peores formatos de la quincena, qué entró y qué salió (poda.json "historial").
Da un veredicto (más rápido / igual / más lento) y recomendaciones con reglas fijas.
Salida: datos/balance.json + un Issue con la etiqueta "aviso" (llega al celular por la app de GitHub).
Uso: python3 pipeline/balance.py [--sin-issue]
"""
import json
import statistics as st
import subprocess
import sys
from datetime import date, datetime, timedelta, timezone

from comun import RAIZ, cargar, guardar

ART = timezone(timedelta(hours=-3))
REPO = "mindglitch777-eng/proyecto-youtube-futbol-quiz"


def serie():
    r = subprocess.run(["git", "show", "origin/datos-vivos:vivo.json"], capture_output=True, text=True, cwd=RAIZ)
    try:
        return [(datetime.fromisoformat(t), v, s) for t, v, s in json.loads(r.stdout or "{}").get("canal_serie", [])]
    except Exception:
        return []


def ritmo(cs, desde, hasta):
    """Vistas y suscriptores por día entre dos fechas (con los puntos medidos más cercanos)."""
    xs = [x for x in cs if desde <= x[0] <= hasta]
    if len(xs) < 2:
        return None
    a, b = xs[0], xs[-1]
    dias = (b[0] - a[0]).total_seconds() / 86400
    if dias < 3:
        return None
    return dict(vistas_dia=int((b[1] - a[1]) / dias), subs_dia=round((b[2] - a[2]) / dias, 1), dias=round(dias, 1))


def main():
    hoy = datetime.now(ART).replace(tzinfo=None)
    q1 = (hoy - timedelta(days=14), hoy)
    q0 = (hoy - timedelta(days=28), hoy - timedelta(days=14))
    cs = serie()
    ahora, antes = ritmo(cs, *q1), ritmo(cs, *q0)
    rend = cargar("rendimiento.json", {}).get("videos", [])
    pub = {p["video_id"]: p for p in cargar("publicados.json", []) if p.get("video_id")}

    def fuertes(desde, hasta):
        dias = {}
        for v in rend:
            if v.get("horas", 0) >= 48 and v.get("vistas_48h") is not None:
                d = v["publicado"][:10]
                if desde.date().isoformat() <= d < hasta.date().isoformat():
                    dias.setdefault(d, []).append(v["vistas_48h"])
        return (round(sum(sum(1 for a in xs if a >= 10_000) for xs in dias.values()) / len(dias), 2) if dias else None), dias

    f1, d1 = fuertes(*q1)
    f0, _ = fuertes(*q0)
    por_fmt = {}
    for v in rend:
        p = pub.get(v["id"])
        if p and v.get("horas", 0) >= 48 and v.get("vistas_48h") is not None and q1[0].date().isoformat() <= p["fecha"] < q1[1].date().isoformat():
            por_fmt.setdefault(p["tipo"], []).append(v["vistas_48h"])
    from comun import CONFIG
    activos = {k for k, v in CONFIG["pruebas"].items() if v.get("listo")} | {"rueda", "cabezas"}
    ranking = sorted(((k, int(st.median(x)), len(x)) for k, x in por_fmt.items() if len(x) >= 2 and k in activos), key=lambda t: -t[1])
    ger = cargar("gerente.json", {})
    mon = ger.get("monetizacion", {})
    v90 = mon.get("vistas_shorts_90d") or 0
    subs = mon.get("suscriptores") or 0
    sem_10m = round((10_000_000 - v90) / (ahora["vistas_dia"] * 7), 1) if ahora and ahora["vistas_dia"] > 0 else None
    dias_1000 = int((1000 - subs) / ahora["subs_dia"]) if ahora and ahora["subs_dia"] > 0 and subs < 1000 else (0 if subs >= 1000 else None)
    cambios = [c for c in cargar("poda.json", {}).get("historial", []) if c["fecha"] >= q1[0].date().isoformat()]
    if ahora and antes and antes["vistas_dia"]:
        cambio = ahora["vistas_dia"] / antes["vistas_dia"] - 1
        veredicto = "MÁS RÁPIDO" if cambio > 0.10 else "MÁS LENTO" if cambio < -0.10 else "IGUAL"
    else:
        cambio, veredicto = None, "SIN DATOS SUFICIENTES (falta la quincena anterior completa)"
    rec = []
    if f1 is not None and f1 < 1.5:
        rec.append("Pocos videos de 10 K por día: el Ingeniero tiene que traer formatos nuevos de las familias que pegan (WHEEL, CABEZAS) y el Gerente darles estreno.")
    if veredicto == "MÁS LENTO":
        rec.append("El canal va más lento: revisar si un formato fijo se cansó (WHEEL / HEAD FIT) y si la semana de volumen ayudó o no.")
    if sem_10m and sem_10m > 26:
        rec.append(f"A este ritmo faltan {sem_10m} semanas para 10 M: hay que subir el ritmo de vistas por día (meta 110 K).")
    if ranking:
        rec.append(f"Darle más lugar a {ranking[0][0]} (mediana {ranking[0][1]:,} a 48 h) y vigilar a {ranking[-1][0]} ({ranking[-1][1]:,}).")
    out = dict(fecha=hoy.date().isoformat(), veredicto=veredicto, cambio_vistas=None if cambio is None else round(cambio * 100),
               quincena=ahora, anterior=antes, fuertes_por_dia=f1, fuertes_por_dia_anterior=f0, semanas_a_10M=sem_10m,
               dias_a_1000_subs=dias_1000, ranking=ranking, cambios=cambios, recomendaciones=rec)
    guardar("balance.json", out)
    L = [f"## Balance quincenal · {out['fecha']} · **{veredicto}**" + (f" ({cambio * 100:+.0f} % de vistas por día)" if cambio is not None else ""), "",
         f"- **Vistas por día:** {ahora['vistas_dia']:,}" if ahora else "- Vistas por día: sin datos",
         (f" (antes {antes['vistas_dia']:,})" if antes else ""),
         f"- **Suscriptores por día:** {ahora['subs_dia'] if ahora else '-'}" + (f" (antes {antes['subs_dia']})" if antes else ""),
         f"- **Videos de 10 K por día:** {f1} (antes {f0}) · meta 3",
         f"- **Para 10 M de vistas:** {sem_10m} semanas a este ritmo · **para 1.000 suscriptores:** {dias_1000} días", "",
         "**Mejores formatos de la quincena (mediana a 48 h):** " + (" · ".join(f"{k} {m:,} ({n})" for k, m, n in ranking[:4]) or "sin datos"),
         "**Cambios automáticos:** " + ("; ".join(f"{c['formato']} {c['cambio']}" for c in cambios) or "ninguno"), "",
         "**Qué hacer:**", *[f"- {r}" for r in rec or ["Nada: seguir igual."]], "",
         "_Balance automático (sin IA). El Gerente IA lo lee en su próximo turno._", "", "---", "_Generated by [Claude Code](https://claude.ai/code)_"]
    texto = "\n".join(x for x in L if x is not None).replace("\n (antes", " (antes")
    print(texto)
    if "--sin-issue" not in sys.argv:
        subprocess.run(["gh", "api", "-X", "POST", f"repos/{REPO}/issues", "-f", f"title=Balance quincenal {out['fecha']}: {veredicto}",
                        "-f", f"body={texto}", "-f", "labels[]=aviso"], cwd=RAIZ)
    return out


if __name__ == "__main__":
    main()
