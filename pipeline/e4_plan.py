#!/usr/bin/env python3
"""
Etapa 4 · PLAN DE LA SEMANA (grilla "volumen con intención", decisión del 02/11):
5 videos por día = 3 STOP distintos (lo que funciona) intercalados con 2 PRUEBAS (formatos nuevos que rotan).

  (v2, 04/11) 6 por día = 3 que FUNCIONAN + 3 NUEVOS intercalados:
  08:00 STOP grilla · 11:00 PRUEBA · 14:00 WHEEL (14.081 vistas en 37 h: fijo) · 17:00 PRUEBA · 20:00 STOP estrella (HARD día por medio) · 23:00 PRUEBA
  Los dos STOP del día nunca se parecen (uno grilla, otro con zoom a la estrella), para que YouTube no lo vea repetitivo.

Pruebas: config["pruebas"] (solo las que tienen "listo": true). Cada día dos pruebas DISTINTAS; las que rinden mejor
salen más seguido y las que nunca se probaron tienen prioridad (todas tienen su chance).
PODA AUTOMÁTICA (datos/analytics.json): una prueba con ≥4 videos medidos que rinde menos de la mitad que el STOP
(puntaje = % visto x suscriptores cada 1.000 vistas) queda podada y deja su lugar. Si le gana al STOP, se marca "promovida"
y pasa a salir todos los días. Todo queda anotado en datos/poda.json (y se ve en el tablero).
Salida: datos/plan.json
"""
import random
from datetime import date, datetime, timedelta, timezone

from comun import CONFIG, cargar, etapa, guardar

# 15/11 DECISIÓN DEL CEO: sale el STOP clásico (desde el 07/11: mediana 1.650 a 48 h, 0 videos de 10 K, 2 de 6 lugares) y salen los
# quiz. Los 4 lugares de prueba van a la mecánica que funciona (PARAR en el momento justo) con otras lógicas: WHEEL/HEAD FIT y sus
# variantes (LEGS WHEEL, CONVEYOR, HEAD SLOT), BALLON D'OR, FIT ALL, SIUUU, PENALTY, GOAT CIRCLE. El cerebro elige cuál.
# 18/11 DECISIÓN DEL CEO: volvemos a 6 por día SOLO con lo que rinde muy bien. CONVEYOR (2 de 2 videos de 19-23 K) sale todos los
# días; STOP ON YOUR FAVORITE (17 K) también; WHEEL y HEAD FIT (cansados) se turnan: un día cada uno. 3 lugares de prueba para lo
# que rinde + estrenos de formatos nuevos (lo nuevo pega más: CONVEYOR, FAVORITE y HEAD FIT hicieron sus mejores números al debut).
GRILLA = [("13:00", "prueba", None), ("15:00", "favorito", None), ("17:00", "prueba", None),
          ("20:00", "rueda", None), ("21:30", "cinta", None), ("23:00", "prueba", None)]   # WHEEL aguanta (mediana 7,3 K después del debut); HEAD FIT pasa a prueba   # 07/11: la noche rinde 4-7 veces más   # 06/11: HEAD FIT fijo (23.514 vistas en su 1.er video)
FIJOS = {"rueda", "cinta", "favorito"}                                         # 18/11: lugar fijo todos los días
VARIANTES = {"cinta", "piernas", "slot"}
# 15/11 (auditoría B2): FAMILIAS. El público se cansa de la MECÁNICA, no solo del formato: máximo 2 por familia por día.
FAMILIAS = {"rueda": "WHEEL", "piernas": "WHEEL", "cinta": "WHEEL",
            "cabezas": "CABEZAS", "slot": "CABEZAS", "fitall": "CABEZAS",
            "favorito": "ELEGI", "circulo": "ELEGI",
            "balon": "MOMENTO", "siuu": "MOMENTO", "penal": "MOMENTO", "vs": "DUELO", "dress": "MOMENTO", "escape": "ESCAPE", "cano": "SKILL", "goles": "STATS"}
MAX_FAMILIA_DIA = 2
# 15/11 (auditoría B1 + CEO: "arranquemos ya"): SEMANA DE VOLUMEN 16-22/11 (16 y 17 con extras): 8 videos por día. Los 2 lugares extra van SOLO a familias que ya dieron
# videos de 10 K (WHEEL, CABEZAS, ELEGÍ). Se compara contra la semana de 6 (videos de 10 K por día y vistas por día).
VOLUMEN = dict(desde="2026-11-16", hasta="2026-11-20", horas=["11:00", "18:30"], familias={"WHEEL", "CABEZAS", "ELEGI"})                                        # 13/11: variantes de WHEEL/HEAD FIT (Issues #6 y #7): máx. 1 por día (lección: WHEEL 2 veces por día se cansó)
MIN_VIDEOS_PODA = 4
ESTRENO_LUGARES = 3                                                             # 15/11 CEO: cada formato nuevo, 3 lugares asegurados en su 1.ª semana
MAX_PRUEBA_SEMANA = 4                                                           # Fase 2: un formato de prueba sale ≤3 veces por semana (variedad)


def fechas(inicio, dias):
    """Si no se da inicio: el lunes siguiente, o el día después del último plan (nunca se pisa lo ya planificado)."""
    if inicio is not None:
        return inicio, dias
    hoy = datetime.now(timezone.utc).date()
    inicio = hoy + timedelta(days=(7 - hoy.weekday()) % 7 or 7)
    previo = cargar("plan.json")
    if previo and previo.get("slots"):
        fin = date.fromisoformat(previo["slots"][-1]["fecha"])
        if fin >= inicio:
            inicio = fin + timedelta(days=1)
    return inicio, dias


def puntajes():
    """Puntaje por formato desde Analytics: mediana de % visto x (0,5 + subs cada 1.000). Devuelve (puntajes, videos medidos)."""
    an = cargar("analytics.json", {}).get("por_formato", {})
    pts, n = {}, {}
    for k, x in an.items():
        base = k.split("/")[0]
        alcance = min(2.0, max(0.5, (x.get("mediana_vistas", 10_000) / 10_000) ** 0.5))   # 08/11: también cuenta cuánta gente llegó
        p = x["mediana_pct_visto"] * (0.5 + x["mediana_subs_cada_1000"]) * alcance
        if base not in pts or x["videos"] > n[base]:
            pts[base], n[base] = p, x["videos"]
    return pts, n


def podar():
    """15/11 (auditoría A2): poda y promoción contra el CANAL (antes contra STOP, que ya no existe).
    - Mediana del canal = vistas a 48 h de los videos de los últimos 14 días.
    - PROTEGIDO: un formato con un video de 10 K o más entre sus últimos 4 nunca se poda (FIT ALL tenía uno de 21 K y lo sacó).
    - PODA rápida: sus últimos 3 videos medidos, todos debajo de la mediana del canal.
    - PROMOCIÓN: ≥4 videos medidos y mediana ≥ 1,5 veces la del canal.
    - Una podada que pasa a estar protegida vuelve sola. Cada cambio queda en poda.json "historial" (la vigilancia lo avisa)."""
    import statistics as st
    poda = cargar("poda.json", {"podadas": {}, "promovidas": {}})
    poda.setdefault("historial", [])
    pts, _ = puntajes()
    rend = {v["id"]: v for v in cargar("rendimiento.json", {}).get("videos", [])}
    hoy = datetime.now(timezone.utc).date()
    por, canal = {}, []
    for x in sorted(cargar("publicados.json", []), key=lambda x: x["fecha"]):
        r = rend.get(x.get("video_id"))
        if not r or r.get("horas", 0) < 48 or r.get("vistas_48h") is None or x.get("reemplazado"):
            continue
        por.setdefault(x["tipo"], []).append(r["vistas_48h"])
        if (hoy - date.fromisoformat(x["fecha"])).days <= 14:
            canal.append(r["vistas_48h"])
    med = st.median(canal) if canal else None
    if not med:
        guardar("poda.json", poda); return poda, pts
    def anotar(k, que, por_que):
        poda["historial"].append(dict(fecha=hoy.isoformat(), formato=k, cambio=que, motivo=por_que))
    for k, v in CONFIG["pruebas"].items():
        if k in FIJOS or not v.get("listo"):
            continue
        xs = por.get(k, [])
        protegido = any(a >= 10_000 for a in xs[-4:]) or (v.get("protegido_hasta") or "") >= hoy.isoformat()   # 21/11: protección a mano (CEO)
        if k in poda["podadas"] and protegido:
            poda["podadas"].pop(k); anotar(k, "vuelve", f"tiene un video de {max(xs[-4:]):,} entre sus últimos 4 (protegido)")
            continue
        if k not in poda["podadas"] and not protegido and len(xs) >= 3 and all(a < med for a in xs[-3:]):
            poda["podadas"][k] = dict(fecha=hoy.isoformat(), rinde=f"últimos 3: {', '.join(f'{a:,}' for a in xs[-3:])} vs canal {int(med):,}",
                                      videos=len(xs))
            anotar(k, "podado", poda["podadas"][k]["rinde"])
        elif k in poda["promovidas"] and len(xs) >= 4 and st.median(xs[-4:]) < med:   # 24/11: un promovido que ya no rinde, baja
            poda["promovidas"].pop(k)
            anotar(k, "deja de ser promovido", f"mediana de sus últimos 4: {int(st.median(xs[-4:])):,} vs canal {int(med):,}")
        elif len(xs) >= 4 and st.median(xs) >= 1.5 * med and k not in poda["promovidas"]:
            poda["promovidas"][k] = dict(fecha=hoy.isoformat(), rinde=f"mediana {int(st.median(xs)):,} vs canal {int(med):,}", videos=len(xs))
            anotar(k, "promovido", poda["promovidas"][k]["rinde"])
    poda["historial"] = poda["historial"][-100:]
    poda["mediana_canal"] = int(med)
    guardar("poda.json", poda)
    return poda, pts


def main(inicio=None, dias=7):
    etapa("plan", "en_curso")
    inicio, dias = fechas(inicio, dias)
    poda, pts = podar()
    activas = [k for k, v in CONFIG["pruebas"].items() if v.get("listo") and k not in poda["podadas"]]
    promovidas = sorted([k for k in activas if k in poda["promovidas"]], key=lambda k: k in FIJOS)   # las que no tienen lugar fijo primero
    rng = random.Random(inicio.toordinal())
    usos = {k: 0 for k in activas}
    hist = cargar("publicados.json", [])
    for p in hist:                                                              # lo que ya salió cuenta (las nuevas van primero)
        if p.get("tipo") in usos:
            usos[p["tipo"]] += 1
    peso = {k: 1.0 + (pts.get(k, 0) / max(pts.values() or [1])) for k in activas}
    factor = {k: 1.0 for k in activas}                                          # solo olas + investigación (para el cerebro)
    try:                                                                        # FASE 2: el cerebro estadístico decide (si falla, plan clásico)
        import cerebro
        M = cerebro.modelo()
        cerebro.evaluar(M)
        previos = cerebro.recientes()
    except Exception as e:
        print("cerebro no disponible, uso el plan clásico:", e, flush=True)
        cerebro = M = None; previos = []
    OLA_A_FORMATO = {"stop": ["stop", "siuu", "penal", "balon"], "wheel": ["rueda"], "fit": ["fitall", "cabezas"], "find": ["find"],
                     "dress": ["dress"], "quiz": ["trayectoria", "tridente", "q20fichaje", "q20costo"], "goat": ["circulo"]}
    FACTOR_OLA = {"naciente": 2.0, "subiendo": 1.8, "estable": 1.0, "bajando": 0.6, "muerta": 0.2}
    for fam, e in cargar("olas.json", {}).get("estado", {}).items():              # detector diario de olas: subirse y soltar a tiempo
        for k in OLA_A_FORMATO.get(fam, []):
            if k in peso:
                peso[k] *= FACTOR_OLA.get(e["estado"], 1.0); factor[k] *= FACTOR_OLA.get(e["estado"], 1.0)
    for r in cargar("investigacion.json", {}).get("recomendaciones", []):        # la investigación del sábado/miércoles manda
        f = 1.6 if r["accion"].startswith(("SUBIR", "PROBAR MÁS")) else (0.5 if r["accion"].startswith("BAJAR") else 1.0)
        for k in r["nuestros"]:
            if k in peso:
                peso[k] *= f; factor[k] *= f
    # Horarios que aprenden solos: los formatos fijos van a las horas con mejor mediana (si hay ≥2 videos de esa hora)
    hrs = cargar("investigacion.json", {}).get("horas", {})
    def rinde(h):
        if M and (M["horas"].get(h[:5]) or {}).get("videos", 0) >= 2:
            return M["horas"][h[:5]]["efecto"]                                  # cerebro: efecto de la hora descontando el formato
        x = hrs.get(h[:2]); return (x["mediana"] / 8000 - 1) if x and x["videos"] >= 2 else 0.0
    grilla = list(GRILLA)
    tope_ = lambda k: CONFIG["pruebas"].get(k, {}).get("max_semana")              # 24/11: la promovida respeta su tope semanal (BALLON D'OR, tope 2, salía todos los días)
    desde_ = (inicio - timedelta(days=6)).isoformat()
    usados_ = lambda k: sum(1 for p_ in cargar("publicados.json", []) if p_.get("tipo") == k and p_.get("video_id") and not p_.get("cancelado") and desde_ <= p_["fecha"] < inicio.isoformat())
    ola_fija = [k for k in promovidas if k not in FIJOS and not (tope_(k) and usados_(k) >= tope_(k))][:1]   # la promovida de la ola toma un lugar fijo (y compite por las mejores horas)
    if ola_fija:
        i = next(i for i, g in enumerate(grilla) if g[1] == "prueba")
        grilla[i] = (grilla[i][0], ola_fija[0], None)
    esperado = lambda t: (M["formatos"].get(t) or {}).get("media", M["mu0"]) if M else 0
    fijos = sorted([g for g in grilla if g[1] != "prueba"], key=lambda g: (g[1] == "stop", g[1] not in ola_fija, -esperado(g[1])))   # ola, rueda/cabezas primero
    horas_orden = sorted([g[0] for g in grilla], key=rinde, reverse=True)
    nueva = []
    for g_, h_ in zip(fijos, horas_orden):
        nueva.append((h_, g_[1], g_[2]))
    for h_ in horas_orden[len(fijos):]:
        nueva.append((h_, "prueba", None))
    con_datos = sum(1 for g in grilla if (hrs.get(g[0][:2]) or {}).get("videos", 0) >= 2 or (M and (M["horas"].get(g[0][:5]) or {}).get("videos", 0) >= 2))
    GRILLA_SEMANA = sorted(nueva) if con_datos >= 4 else grilla                 # sin datos suficientes: la grilla de noche fija
    try:                                                                       # 22/11 MODO SERIE (serie.py): lo que pegó se repite 5 días
        import serie as SERIE
        SERIE.actualizar()
    except Exception as e:
        print("serie falló:", e); SERIE = None
    slots = []; semana = {}
    # 18/11: el tope semanal (max_semana, estrenos) cuenta también lo ya subido en los 6 días anteriores. Antes el plan se arma de a
    # 1 día y el contador arrancaba en 0 cada vez: BALLON D'OR con tope 2 salió 16, 17, 18 y 20/11.
    desde_sem = (inicio - timedelta(days=6)).isoformat()
    for p_ in cargar("publicados.json", []):
        if p_.get("video_id") and not p_.get("cancelado") and not p_.get("reemplazado") and desde_sem <= p_["fecha"] < inicio.isoformat():
            semana[p_["tipo"]] = semana.get(p_["tipo"], 0) + 1
    for d in range(dias):
        dia = (inicio + timedelta(days=d)).isoformat()
        hoy_pruebas = []
        alt = "rueda" if date.fromisoformat(dia).toordinal() % 2 == 0 else "cabezas"   # 18/11: WHEEL y HEAD FIT descansan día por medio
        grilla_dia = [(h_, alt if t_ == "alterno" else t_, e_) for h_, t_, e_ in GRILLA_SEMANA]
        if VOLUMEN["desde"] <= dia <= VOLUMEN["hasta"]:
            finde = date.fromisoformat(dia).weekday() >= 5                     # IA de YouTube (15/11): sábado y domingo el pico es 11-15 h
            horas_extra = VOLUMEN["horas"]                                    # 15/11 (IA de YouTube): ≥1,5 h entre videos; 11:00 cubre el pico del fin de semana
            grilla_dia = sorted(grilla_dia + [(h_, "fuerte", None) for h_ in horas_extra])
        fijos_dia = [t for _, t, _ in grilla_dia if t not in ("prueba", "fuerte")]

        series_dia = SERIE.activas(dia) if SERIE else {}

        def params(k):                                                         # C2: lo que ganó una prueba A/B + la prueba en curso
            out = {}
            if cerebro:
                out = dict(cerebro.parametros_ganadores(k))
                out.update(cerebro.brazo_para(k, sum(1 for x in slots if x["tipo"] == k)))
            if k in series_dia:                                                # modo serie: mismo título base que el video que pegó
                out["serie_titulo"] = series_dia[k]["titulo"]
            return out
        for hora, tipo, estilo in grilla_dia:
            if tipo in FIJOS or tipo in ola_fija:                             # formato que ya funciona / ola del momento: lugar fijo
                slots.append(dict(fecha=dia, hora=hora, tipo=tipo, **params(tipo))); continue
            if tipo == "stop":
                sl = dict(fecha=dia, hora=hora, tipo="stop", dificil=True, hard=(estilo == "grilla2" and d % 2 == 1),
                          arranque="grilla")                             # 07/11: el zoom estrella no mejoró el "eligió ver"
                if cerebro:                                                   # Fase 2: lo que ganó una prueba A/B + la prueba A/B en curso
                    sl.update(cerebro.parametros_ganadores("stop"))
                    sl.update(cerebro.brazo_para("stop", sum(1 for x in slots if x["tipo"] == "stop") + d))
                slots.append(sl)
                continue
            tope = {k: CONFIG["pruebas"][k].get("max_semana", MAX_PRUEBA_SEMANA) for k in activas}  # algunos formatos solo N por semana
            del_dia = ({x["tipo"] for x in slots if x["fecha"] == dia} |        # variedad: nunca el mismo formato dos veces en el día
                       {t for _, t, _ in GRILLA_SEMANA if t != "prueba"} | FIJOS)  # (los fijos ya tienen su lugar más tarde)
            ya = [x["tipo"] for x in slots if x["fecha"] == dia]
            fam_n = {}
            for t in ya + [t for t in fijos_dia if t not in ya]:               # B2: tope por familia (cuenta también los fijos del día)
                fam_n[FAMILIAS.get(t, t)] = fam_n.get(FAMILIAS.get(t, t), 0) + 1
            del_dia |= {k for k in activas if fam_n.get(FAMILIAS.get(k, k), 0) >= MAX_FAMILIA_DIA}
            flojos = {k for k in activas if FAMILIAS.get(k) not in VOLUMEN["familias"]} if tipo == "fuerte" else set()   # B1
            libres = [k for k in activas if k not in del_dia and k not in ola_fija
                      and not (CONFIG["pruebas"][k].get("tope_duro") and semana.get(k, 0) >= tope[k])]   # 18/11: topes duros (originalidad)
            cand = [k for k in libres if k not in flojos and semana.get(k, 0) < tope[k]] or \
                   [k for k in libres if k not in flojos] or \
                   [k for k in libres if semana.get(k, 0) < tope[k]] or libres or \
                   [k for k in activas if k not in del_dia and k not in ola_fija] or activas   # 18/11: antes pasar un tope que repetir en el día
            if not cand:
                slots.append(dict(fecha=dia, hora=hora, tipo="stop", dificil=False, arranque=rng.choice(["estrella", "grilla"]))); continue
            estrenos = [k for k in cand if (CONFIG["pruebas"][k].get("estreno_hasta") or "") >= dia
                        and semana.get(k, 0) < ESTRENO_LUGARES]                  # 15/11: formato nuevo = lugares asegurados su 1.ª semana
            fijas = [k for k in promovidas if k not in hoy_pruebas and k not in FIJOS and k not in del_dia]   # las fijas ya tienen su lugar
            en_serie = [k for k in series_dia if k in activas and k not in FIJOS and k not in hoy_pruebas
                        and k not in {x["tipo"] for x in slots if x["fecha"] == dia}]
            if en_serie:                                                        # MODO SERIE: 1 por día mientras dure (antes que todo)
                k = en_serie[0]
            elif estrenos:                                                      # ESTRENO: el que menos salió esta semana
                k = min(estrenos, key=lambda k: (semana.get(k, 0), rng.random()))
            elif fijas and not hoy_pruebas and not ola_fija:                   # una promovida sale todos los días
                k = fijas[0]
            else:                                                               # la menos usada (pesada por rendimiento)
                k = (cerebro.elegir(M, cand, rng, factor, previos, [x["tipo"] for x in slots]) if cerebro
                     else min(cand, key=lambda k: (usos[k] / peso[k], rng.random())))   # Fase 2: Thompson + tope de originalidad
            usos[k] += 1; hoy_pruebas.append(k); semana[k] = semana.get(k, 0) + 1
            slots.append(dict(fecha=dia, hora=hora, tipo=k, **params(k)))
    guardar("plan.json", dict(inicio=inicio.isoformat(), grilla=[f"{h} {t}{'/' + e if e else ''}" for h, t, e in GRILLA],
                              pruebas_activas=activas, podadas=poda["podadas"], promovidas=poda["promovidas"],
                              puntaje={k: round(v, 1) for k, v in pts.items()}, motor="cerebro" if cerebro else "clásico", slots=slots))
    cupos = {}
    for s in slots:
        cupos[s["tipo"]] = cupos.get(s["tipo"], 0) + 1
    etapa("plan", "ok", semana=f"{inicio.isoformat()} → {(inicio + timedelta(days=dias - 1)).isoformat()}", cupos=cupos,
          podadas=list(poda["podadas"]), promovidas=list(poda["promovidas"]))
    return inicio


if __name__ == "__main__":
    import sys
    main(date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else None, int(sys.argv[2]) if len(sys.argv) > 2 else 7)
