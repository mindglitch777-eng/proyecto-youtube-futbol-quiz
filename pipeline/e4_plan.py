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

GRILLA = [("08:00", "stop", "grilla"), ("11:00", "prueba", None), ("14:00", "rueda", None),
          ("17:00", "cabezas", None), ("20:00", "stop", "grilla2"), ("23:00", "prueba", None)]   # 06/11: HEAD FIT fijo (23.514 vistas en su 1.er video)
FIJOS = {"rueda", "cabezas"}                                                    # formatos que ya funcionan, con lugar fijo
MIN_VIDEOS_PODA = 4


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
        p = x["mediana_pct_visto"] * (0.5 + x["mediana_subs_cada_1000"])
        if base not in pts or x["videos"] > n[base]:
            pts[base], n[base] = p, x["videos"]
    return pts, n


def podar():
    """Decide podas y promociones con los datos; las guarda en datos/poda.json (persisten entre semanas)."""
    poda = cargar("poda.json", {"podadas": {}, "promovidas": {}})
    pts, n = puntajes()
    stop = pts.get("stop")
    hoy = datetime.now(timezone.utc).date().isoformat()
    for k in CONFIG["pruebas"]:
        if k not in pts or n.get(k, 0) < MIN_VIDEOS_PODA or not stop:
            continue
        rel = pts[k] / stop
        if rel < 0.5 and k not in poda["podadas"]:
            poda["podadas"][k] = dict(fecha=hoy, rinde=f"{rel:.0%} del STOP", videos=n[k])
        elif rel >= 1.0:
            poda["promovidas"][k] = dict(fecha=hoy, rinde=f"{rel:.0%} del STOP", videos=n[k])
    guardar("poda.json", poda)
    return poda, pts


def main(inicio=None, dias=7):
    etapa("plan", "en_curso")
    inicio, dias = fechas(inicio, dias)
    poda, pts = podar()
    activas = [k for k, v in CONFIG["pruebas"].items() if v.get("listo") and k not in poda["podadas"]]
    promovidas = [k for k in activas if k in poda["promovidas"]]
    rng = random.Random(inicio.toordinal())
    usos = {k: 0 for k in activas}
    hist = cargar("publicados.json", [])
    for p in hist:                                                              # lo que ya salió cuenta (las nuevas van primero)
        if p.get("tipo") in usos:
            usos[p["tipo"]] += 1
    peso = {k: 1.0 + (pts.get(k, 0) / max(pts.values() or [1])) for k in activas}
    for r in cargar("investigacion.json", {}).get("recomendaciones", []):        # la investigación del sábado/miércoles manda
        f = 1.6 if r["accion"].startswith(("SUBIR", "PROBAR MÁS")) else (0.5 if r["accion"].startswith("BAJAR") else 1.0)
        for k in r["nuestros"]:
            if k in peso:
                peso[k] *= f
    slots = []; semana = {}
    for d in range(dias):
        dia = (inicio + timedelta(days=d)).isoformat()
        hoy_pruebas = []
        for hora, tipo, estilo in GRILLA:
            if tipo in FIJOS:                                                 # formato que ya funciona: lugar fijo
                slots.append(dict(fecha=dia, hora=hora, tipo=tipo)); continue
            if tipo == "stop":
                slots.append(dict(fecha=dia, hora=hora, tipo="stop", dificil=True, hard=(estilo == "grilla2" and d % 2 == 1),
                                  arranque="grilla"))                    # 07/11: el zoom estrella no mejoró el "eligió ver"
                continue
            tope = {k: CONFIG["pruebas"][k].get("max_semana", 99) for k in activas}  # algunos formatos solo N por semana
            cand = [k for k in activas if k not in hoy_pruebas and semana.get(k, 0) < tope[k]] or \
                   [k for k in activas if semana.get(k, 0) < tope[k]] or activas
            if not cand:
                slots.append(dict(fecha=dia, hora=hora, tipo="stop", dificil=False, arranque=rng.choice(["estrella", "grilla"]))); continue
            fijas = [k for k in promovidas if k not in hoy_pruebas]
            if fijas and not hoy_pruebas:                                       # una promovida sale todos los días
                k = fijas[0]
            else:                                                               # la menos usada (pesada por rendimiento)
                k = min(cand, key=lambda k: (usos[k] / peso[k], rng.random()))
            usos[k] += 1; hoy_pruebas.append(k); semana[k] = semana.get(k, 0) + 1
            slots.append(dict(fecha=dia, hora=hora, tipo=k))
    guardar("plan.json", dict(inicio=inicio.isoformat(), grilla=[f"{h} {t}{'/' + e if e else ''}" for h, t, e in GRILLA],
                              pruebas_activas=activas, podadas=poda["podadas"], promovidas=poda["promovidas"],
                              puntaje={k: round(v, 1) for k, v in pts.items()}, slots=slots))
    cupos = {}
    for s in slots:
        cupos[s["tipo"]] = cupos.get(s["tipo"], 0) + 1
    etapa("plan", "ok", semana=f"{inicio.isoformat()} → {(inicio + timedelta(days=dias - 1)).isoformat()}", cupos=cupos,
          podadas=list(poda["podadas"]), promovidas=list(poda["promovidas"]))
    return inicio


if __name__ == "__main__":
    import sys
    main(date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else None, int(sys.argv[2]) if len(sys.argv) > 2 else 7)
