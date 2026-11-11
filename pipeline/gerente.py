#!/usr/bin/env python3
"""
GERENTE · tablero de números del día (lo lee el Gerente IA antes de decidir; también lo muestra la app del tablero).
No decide nada: junta los hechos para que las decisiones salgan de datos, no de impresiones.

Mide:
- Canal: vistas a las 48 h (mediana) de los videos de los últimos 7 días contra los 7 anteriores; suscriptores; % visto.
- Formatos (últimos 14 días): videos, mediana 48 h, mejor, % visto, subs cada 1.000, tendencia, y un semáforo
  ESTRELLA (≥ 1,5x la mediana del canal) · SANO (≥ 0,7x) · FLOJO (≥ 0,3x) · MUERTO (< 0,3x con ≥ 3 videos).
- Horas: mediana a las 48 h por hora de publicación (últimos 21 días).
- Mejores y peores videos de las últimas 72 h (con su ritmo de vistas por hora).
- Olas: mecánicas nacientes/subiendo y si tenemos formato para cada una.
- Salud del sistema: subidas programadas para hoy y los próximos 3 días, alerta de la vigía, etapas con error,
  antigüedad de los datos de olas e investigación.
Salida: pipeline/datos/gerente.json (números + "parte" que escribe el Gerente IA) y reports/gerente/numeros_<fecha>.md
"""
import json
import statistics as st
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from comun import RAIZ, cargar, guardar

ART = timezone(timedelta(hours=-3))
NUESTRO = {"stop": ["stop", "siuu", "penal", "balon"], "wheel": ["rueda"], "fit": ["fitall", "cabezas"], "find": ["find"],
           "dress": ["dress"], "quiz": ["trayectoria", "tridente", "q20fichaje", "q20costo"], "goat": ["circulo"]}


def med(xs):
    xs = [x for x in xs if x is not None]
    return round(st.median(xs)) if xs else None


def main():
    hoy = datetime.now(ART).date()
    rend = {v["id"]: v for v in cargar("rendimiento.json", {}).get("videos", [])}
    an = {v["video"]: v for v in cargar("analytics.json", {}).get("por_video", [])}
    pub = [p for p in cargar("publicados.json", []) if p.get("video_id") and not p.get("reemplazado")]
    filas = []
    for p in pub:
        v = rend.get(p["video_id"])
        if not v:
            continue
        a = an.get(p["video_id"], {})
        filas.append(dict(fecha=p["fecha"], hora=p["hora"], tipo=p.get("tipo") or v.get("tipo"), titulo=(p.get("titulo") or v["titulo"])[:70],
                          vistas=v["vistas"], v48=v["vistas_48h"] if v["horas"] >= 48 else None, horas=v["horas"],
                          vph=round(v["vistas"] / max(1, v["horas"])), pct=a.get("averageViewPercentage"), subs1000=a.get("subs_cada_1000"),
                          id=p["video_id"]))
    f = lambda d0, d1: [x for x in filas if d0 <= date.fromisoformat(x["fecha"]) < d1]
    sem, sem_ant = f(hoy - timedelta(days=9), hoy - timedelta(days=2)), f(hoy - timedelta(days=16), hoy - timedelta(days=9))
    canal = dict(mediana_48h_semana=med(x["v48"] for x in sem), mediana_48h_semana_anterior=med(x["v48"] for x in sem_ant),
                 videos_semana=len(sem), pct_visto_semana=med(x["pct"] for x in sem))
    if canal["mediana_48h_semana"] and canal["mediana_48h_semana_anterior"]:
        canal["cambio"] = f"{(canal['mediana_48h_semana'] / canal['mediana_48h_semana_anterior'] - 1) * 100:+.0f}%"
    base = canal["mediana_48h_semana"] or med(x["v48"] for x in filas) or 1
    formatos = {}
    for t in sorted({x["tipo"] for x in f(hoy - timedelta(days=14), hoy + timedelta(days=1))}):
        xs = [x for x in f(hoy - timedelta(days=14), hoy + timedelta(days=1)) if x["tipo"] == t]
        m48 = med(x["v48"] for x in xs)
        prim = [x["v48"] for x in sorted(xs, key=lambda x: x["fecha"]) if x["v48"] is not None]
        tend = None
        if len(prim) >= 4:
            mitad = len(prim) // 2
            a_, b_ = med(prim[:mitad]), med(prim[mitad:])
            tend = f"{(b_ / max(1, a_) - 1) * 100:+.0f}%"
        rel = (m48 or 0) / base
        medidos = sum(1 for x in xs if x["v48"] is not None)
        sem_ = ("SIN DATOS" if not medidos else "ESTRELLA" if rel >= 1.5 else "SANO" if rel >= 0.7 else "FLOJO" if rel >= 0.3 or medidos < 3 else "MUERTO")
        formatos[t] = dict(videos=len(xs), medidos=medidos, mediana_48h=m48, mejor=max((x["vistas"] for x in xs), default=0),
                           pct_visto=med(x["pct"] for x in xs), subs_cada_1000=round(st.median([x["subs1000"] for x in xs if x["subs1000"] is not None]), 2)
                           if any(x["subs1000"] is not None for x in xs) else None, tendencia=tend, vs_canal=f"{rel:.1f}x", semaforo=sem_)
    horas = {}
    for x in f(hoy - timedelta(days=21), hoy):
        if x["v48"] is not None:
            horas.setdefault(x["hora"][:5], []).append(x["v48"])
    horas = {h: dict(mediana=med(v), videos=len(v)) for h, v in sorted(horas.items())}
    recientes = sorted(f(hoy - timedelta(days=3), hoy + timedelta(days=1)), key=lambda x: -x["vph"])
    recientes = [x for x in recientes if x["horas"] >= 6]
    olas = cargar("olas.json", {}).get("estado", {})
    calientes = [dict(mecanica=k, estado=v["estado"], vph=v.get("vph"), nuestros=NUESTRO.get(k, []))
                 for k, v in olas.items() if v["estado"] in ("naciente", "subiendo")]
    prox = {}
    for d in range(4):
        dd = (hoy + timedelta(days=d)).isoformat()
        prox[dd] = sum(1 for p in pub if p["fecha"] == dd)
    alerta = cargar("alerta.json", {})
    etapas = cargar("estado.json", {}).get("etapas", {})
    errores = {k: v.get("resumen", {}).get("errores") or v.get("estado") for k, v in etapas.items() if v.get("estado") == "error"}

    def edad(iso):
        try:
            return round((datetime.now(timezone.utc) - datetime.fromisoformat(iso)).total_seconds() / 3600)
        except Exception:
            return None
    salud = dict(subidas_programadas=prox, alerta_ok=alerta.get("ok"), alerta_problemas=alerta.get("problemas", []),
                 en_cola=len(alerta.get("en_cola", [])), etapas_con_error=errores,
                 olas_hace_h=edad(cargar("olas.json", {}).get("fecha", "")), investigacion=cargar("investigacion.json", {}).get("fecha"),
                 poda=cargar("poda.json", {}))
    previo = cargar("gerente.json", {})
    out = dict(fecha=hoy.isoformat(), hora=datetime.now(ART).strftime("%H:%M"), canal=canal, formatos=formatos, horas=horas,
               mejores=recientes[:3], peores=recientes[-3:][::-1] if len(recientes) > 3 else [], olas_calientes=calientes, salud=salud,
               parte=previo.get("parte"))                                     # el "parte" lo escribe el Gerente IA (se conserva hasta el próximo)
    guardar("gerente.json", out)
    L = [f"# Números del día · {hoy.isoformat()}", "",
         f"**Canal:** mediana a las 48 h esta semana {canal['mediana_48h_semana'] or '-'} (antes {canal['mediana_48h_semana_anterior'] or '-'}, "
         f"{canal.get('cambio', 's/d')}) · {canal['videos_semana']} videos · % visto {canal['pct_visto_semana'] or '-'}", "",
         "| Formato | Semáforo | Videos (medidos) | Mediana 48 h | vs canal | Mejor | % visto | Subs/1000 | Tendencia |", "|---|---|---|---|---|---|---|---|---|"]
    for t, r in sorted(formatos.items(), key=lambda kv: -(kv[1]["mediana_48h"] or 0)):
        L.append(f"| {t} | {r['semaforo']} | {r['videos']} ({r['medidos']}) | {r['mediana_48h'] or '-'} | {r['vs_canal']} | {r['mejor']:,} | "
                 f"{r['pct_visto'] or '-'} | {r['subs_cada_1000'] if r['subs_cada_1000'] is not None else '-'} | {r['tendencia'] or '-'} |")
    L += ["", "**Horas (mediana 48 h):** " + " · ".join(f"{h} {v['mediana']:,} ({v['videos']})" for h, v in horas.items()), "",
          "**Mejores últimas 72 h:** " + " · ".join(f"{x['tipo']} {x['hora']} {x['vistas']:,} ({x['vph']}/h)" for x in out["mejores"]),
          "**Peores últimas 72 h:** " + " · ".join(f"{x['tipo']} {x['hora']} {x['vistas']:,} ({x['vph']}/h)" for x in out["peores"]), "",
          "**Olas calientes:** " + (", ".join(f"{c['mecanica']} ({c['estado']}; nuestros: {', '.join(c['nuestros']) or 'NO TENEMOS'})" for c in calientes) or "ninguna"),
          "", f"**Salud:** subidas programadas {prox} · vigía {'OK' if alerta.get('ok') else 'PROBLEMAS: ' + '; '.join(alerta.get('problemas', []))} · "
          f"en cola {salud['en_cola']} · etapas con error {list(errores) or 'ninguna'} · olas de hace {salud['olas_hace_h']} h · investigación {salud['investigacion']}"]
    d = RAIZ / "reports" / "gerente"; d.mkdir(parents=True, exist_ok=True)
    (d / f"numeros_{hoy.isoformat()}.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
