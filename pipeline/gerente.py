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
    # ---- CAMINO A LA MONETIZACIÓN (Programa de Socios: 1.000 suscriptores + 10 M de vistas de Shorts en 90 días;
    #      nivel inicial: 500 suscriptores + 3 M de vistas de Shorts en 90 días). Vistas de 90 días ≈ suma de los videos de los últimos 90 días.
    rdat = cargar("rendimiento.json", {})
    c90 = (hoy - timedelta(days=90)).isoformat()
    v90 = sum(v["vistas"] for v in rdat.get("videos", []) if v.get("publicado", "9999") >= c90)
    subs = (rdat.get("canal") or {}).get("suscriptores")
    v7 = sum(x["vistas"] for x in f(hoy - timedelta(days=7), hoy + timedelta(days=1)))
    monet = dict(suscriptores=subs, vistas_shorts_90d=v90, meta_completa=dict(suscriptores=1000, vistas_90d=10_000_000),
                 meta_inicial=dict(suscriptores=500, vistas_90d=3_000_000),
                 avance_vistas=f"{v90 / 10_000_000:.0%}", ritmo_semanal=v7,
                 semanas_a_10M=round((10_000_000 - v90) / v7, 1) if v7 and v90 < 10_000_000 else None)
    # ---- HISTORIA COMPLETA DEL CANAL (desde el primer video, con nuestros datos: no dependemos de nadie)
    historia = {}
    todos = [dict(fecha=v.get("publicado") or "2026-10-20", hora="", tipo=v["tipo"], vistas=v["vistas"],
                  v48=v["vistas_48h"] if v["horas"] >= 48 else None) for v in cargar("rendimiento.json", {}).get("videos", [])]
    total = len(todos)
    for t in sorted({x["tipo"] for x in todos}):
        xs = sorted([x for x in todos if x["tipo"] == t], key=lambda x: (x["fecha"], x["hora"]))
        med_ = [x["v48"] for x in xs if x["v48"] is not None]
        semanas = {}
        for x in xs:
            if x["v48"] is not None:
                y_, w_, _ = date.fromisoformat(x["fecha"]).isocalendar()
                semanas.setdefault(f"{y_}-S{w_:02d}", []).append(x["v48"])
        cansancio = None
        if len(med_) >= 8:                                                     # últimos 4 contra los 4 anteriores
            ult, ant = st.median(med_[-4:]), st.median(med_[-8:-4])
            cansancio = round(ult / max(1, ant), 2)
        historia[t] = dict(videos=len(xs), medidos=len(med_), mediana_48h=med(med_), mejor=max((x["vistas"] for x in xs), default=0),
                           primero=xs[0]["fecha"], ultimo=xs[-1]["fecha"], peso_en_el_canal=round(len(xs) / max(1, total), 2),
                           por_semana={k: med(v) for k, v in sorted(semanas.items())},
                           cansancio=cansancio, cansado=bool(cansancio is not None and cansancio < 0.6))
    base_h = med(x["v48"] for x in todos) or 1
    oportunidades = [dict(formato=t, mediana_48h=h["mediana_48h"], vs_canal=round(h["mediana_48h"] / base_h, 1), peso=h["peso_en_el_canal"])
                     for t, h in historia.items() if h["medidos"] >= 3 and (h["mediana_48h"] or 0) >= 1.5 * base_h
                     and len([x for x in f(hoy - timedelta(days=7), hoy + timedelta(days=4)) if x["tipo"] == t]) / max(1, len(f(hoy - timedelta(days=7), hoy + timedelta(days=4)))) < 0.15]
    cansados = [dict(formato=t, ultimos4_vs_4anteriores=h["cansancio"]) for t, h in historia.items() if h["cansado"]]
    insp = [x for x in cargar("inspeccion.json", []) if x.get("fecha", "")[:10] >= (hoy - timedelta(days=7)).isoformat()]
    inspeccion = dict(revisados=len(insp), con_defectos=sum(1 for x in insp if x["defectos"]),
                      ejemplos=[f"{x['id']}: {'; '.join(x['defectos'])}" for x in insp if x["defectos"]][-5:])
    # ---- FASE 1 · BLINDAJE: días seguidos (hasta ayer) con ≥6 videos subidos, reserva y vigilancia
    racha, d = 0, hoy - timedelta(days=1)
    while racha < 60:
        if sum(1 for p in pub if p["fecha"] == d.isoformat()) >= 6:
            racha += 1; d -= timedelta(days=1)
        else:
            break
    vig = cargar("vigilancia.json", {}).get("ultimo", {})
    reserva_libre = sum(1 for v in cargar("reserva.json", {"videos": []})["videos"] if not v.get("usado"))
    blindaje = dict(dias_seguidos_con_6=racha, meta=14, reserva=reserva_libre, vigilancia=vig)
    try:                                                                       # Fase 2: el cerebro estadístico (sin IA)
        import cerebro
        cer = cerebro.main()
    except Exception as e:
        cer = dict(error=str(e))
    import originalidad                                                        # auditor sin IA: ¿se ve "plantilla"?
    orig = originalidad.reporte()
    # ---- ADVERTENCIAS (manual del gerente, errores 1, 2, 9 y 10): cuándo un número NO alcanza o el dato puede estar roto
    adv = []
    for t, r in formatos.items():
        if r["medidos"] < 4:
            r["confianza"] = "BAJA: menos de 4 videos medidos, no decidir con esto"
        else:
            xs = sorted(x["v48"] for x in filas if x["tipo"] == t and x["v48"] is not None)
            r["confianza"] = "MEDIA" if r["medidos"] < 8 else "ALTA"
            if xs and max(xs) > 3 * (st.median(xs) or 1):
                r["confianza"] += " · ojo: un solo video muy por encima del resto (outlier)"
    if (salud["olas_hace_h"] or 99) > 30:
        adv.append(f"Las olas tienen {salud['olas_hace_h']} h: el detector no corrió; no concluyas nada de olas hoy.")
    o_ = cargar("olas.json", {})
    if o_.get("3d", {}).get("videos", 999) < 200:
        adv.append("El detector de olas trajo menos de 200 videos (¿cuota agotada?): datos de olas incompletos.")
    fa = cargar("analytics.json", {}).get("fecha")
    if fa and (hoy - date.fromisoformat(str(fa)[:10])).days >= 2:
        adv.append(f"Analytics es del {fa}: % visto y suscriptores están atrasados (YouTube tarda 1-2 días).")
    if not rend:
        adv.append("rendimiento.json vacío: sin vistas no se puede evaluar nada.")
    manana = (hoy + timedelta(days=1)).isoformat()
    if prox.get(manana, 0) < 6:
        adv.append(f"Mañana ({manana}) tiene {prox.get(manana, 0)} videos subidos de 6: revisá producción y subida YA.")
    pasado = (hoy + timedelta(days=2)).isoformat()
    if prox.get(pasado, 0) == 0:
        adv.append(f"Pasado mañana ({pasado}) no tiene videos subidos todavía (normal si la fábrica de hoy aún no corrió; si ya corrió, es un problema).")
    if canal["videos_semana"] < 10:
        adv.append("Menos de 10 videos medidos en la semana: las comparaciones de canal son débiles.")
    salud["advertencias"] = adv
    previo = cargar("gerente.json", {})
    out = dict(fecha=hoy.isoformat(), hora=datetime.now(ART).strftime("%H:%M"), canal=canal, monetizacion=monet, originalidad=orig, inspeccion=inspeccion, blindaje=blindaje, cerebro=cer, historia=historia,
               oportunidades=oportunidades, cansados=cansados, formatos=formatos, horas=horas,
               mejores=recientes[:3], peores=recientes[-3:][::-1] if len(recientes) > 3 else [], olas_calientes=calientes, salud=salud,
               parte=previo.get("parte"))                                     # el "parte" lo escribe el Gerente IA (se conserva hasta el próximo)
    guardar("gerente.json", out)
    L = [f"# Números del día · {hoy.isoformat()}", "",
         f"**Monetización:** suscriptores {monet['suscriptores'] if monet['suscriptores'] is not None else 's/d'} / 1.000 · vistas de Shorts 90 días "
         f"{monet['vistas_shorts_90d']:,} / 10.000.000 ({monet['avance_vistas']}) · ritmo de la semana {monet['ritmo_semanal']:,} · "
         f"semanas para 10 M al ritmo actual: {monet['semanas_a_10M'] or '-'}", "",
         f"**Originalidad (riesgo de 'contenido inauténtico'):** índice {orig['indice']}/100 · {orig['lectura']} · "
         + ("; ".join(orig["alertas"]) or "sin alertas"), "",
         "**Historia completa (desde el primer video):** " + " · ".join(f"{t} {h['videos']} videos, mediana {h['mediana_48h'] or '-'}"
                                                                         for t, h in sorted(historia.items(), key=lambda kv: -(kv[1]['mediana_48h'] or 0))), "",
         "**Oportunidades (funcionan y los usamos poco):** " + (", ".join(f"{o_['formato']} ({o_['vs_canal']}x el canal, {o_['peso']:.0%} de los videos)" for o_ in oportunidades) or "ninguna"),
         "**Cansancio (los últimos 4 rinden < 60 % de los 4 anteriores):** " + (", ".join(f"{c['formato']} ({c['ultimos4_vs_4anteriores']:.0%})" for c in cansados) or "ninguno"), "",
         f"**Inspector visual (7 días):** {inspeccion['revisados']} videos revisados, {inspeccion['con_defectos']} con defectos"
         + (": " + " · ".join(inspeccion["ejemplos"]) if inspeccion["ejemplos"] else ""), "",
         f"**Fase 1 · Blindaje:** {racha}/14 días seguidos con 6 o más videos · reserva {reserva_libre}/12 · vigilancia: "
         + (("; ".join(vig.get("problemas", [])) or "sin problemas") + f" ({vig.get('hora', 's/d')})" if vig else "todavía no corrió"), "",
         "**Fase 2 · Cerebro (estadística sin IA):** " + (
             f"error: {cer['error']}" if cer.get("error") else
             " · ".join(f"{t} esperado {f['vistas_48h_esperadas']:,} ({f['confianza']}, {f['prob_mejor']:.0%} de ser el mejor)" for t, f in list(cer["formatos"].items())[:6])
             + " | Pruebas A/B en curso: " + ("; ".join(f"{e['id']}: " + ", ".join(f"{k} {v['videos']} videos {v['p_mejor']:.0%}" for k, v in (e.get("medicion") or {}).items())
                                                       for e in cer["experimentos"]["activos"]) or "ninguna")
             + " | Terminadas: " + ("; ".join(f"{e['id']} → {e['estado']} {e.get('ganador')}" for e in cer["experimentos"]["terminados"]) or "ninguna")
             + f" | Meta: mediana 48 h {cer['meta'].get('mediana_48h_inicial')} → {cer['meta'].get('mediana_48h_ultimos_7_dias')} (objetivo +25 % en 3 semanas)"), "",
         "**ADVERTENCIAS (leer antes de decidir):** " + (" · ".join(adv) if adv else "ninguna"), "",
         f"**Canal:** mediana a las 48 h esta semana {canal['mediana_48h_semana'] or '-'} (antes {canal['mediana_48h_semana_anterior'] or '-'}, "
         f"{canal.get('cambio', 's/d')}) · {canal['videos_semana']} videos · % visto {canal['pct_visto_semana'] or '-'}", "",
         "| Formato | Semáforo | Confianza | Videos (medidos) | Mediana 48 h | vs canal | Mejor | % visto | Subs/1000 | Tendencia |", "|---|---|---|---|---|---|---|---|---|---|"]
    for t, r in sorted(formatos.items(), key=lambda kv: -(kv[1]["mediana_48h"] or 0)):
        L.append(f"| {t} | {r['semaforo']} | {r.get('confianza', '-')} | {r['videos']} ({r['medidos']}) | {r['mediana_48h'] or '-'} | {r['vs_canal']} | {r['mejor']:,} | "
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
