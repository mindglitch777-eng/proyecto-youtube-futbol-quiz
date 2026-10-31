#!/usr/bin/env python3
"""
Etapa 4 · PLAN DE LA SEMANA: reparte 28 lugares (7 días x 4) entre los formatos que la fábrica sabe hacer.
Puntaje de cada formato = 60 % cómo rinde en NUESTRO canal (mediana de vistas a 48 h) + 40 % cuánto aparece en los virales
de la semana (radar + Gemini). Siempre respeta un mínimo y un máximo por formato (para seguir probando y no caer en plantilla).
Salida: datos/plan.json con la grilla día por día (sin dos videos seguidos del mismo formato).
"""
import random
from datetime import date, datetime, timedelta, timezone

from comun import CONFIG, cargar, etapa, guardar


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


def main(inicio=None, dias=7):
    etapa("plan", "en_curso")
    inicio, dias = fechas(inicio, dias)
    fmts = CONFIG["formatos"]; horas = CONFIG["horas"]
    total = dias * CONFIG["videos_por_dia"]
    rend = cargar("rendimiento.json", {}).get("por_formato", {})
    conteo = cargar("analisis.json", {}).get("conteo_formatos", {})
    med = {k: rend.get(k, {}).get("mediana_48h", 0) for k in fmts}
    tope_r = max(med.values()) or 1; tope_m = max([conteo.get(k, 0) for k in fmts] + [1])
    puntaje = {k: 0.6 * med[k] / tope_r + 0.4 * conteo.get(k, 0) / tope_m + 0.05 for k in fmts}
    cupos = {k: max(1, round(fmts[k]["min"] * dias / 7)) for k in fmts}
    resto = total - sum(cupos.values())
    while resto > 0:                                                           # el resto, proporcional al puntaje
        k = max((k for k in fmts if cupos[k] < max(1, round(fmts[k]["max"] * dias / 7))), key=lambda k: puntaje[k] / (cupos[k] + 1))
        cupos[k] += 1; resto -= 1
    rng_inicio = inicio
    rng = random.Random(rng_inicio.toordinal())
    bolsa = [k for k, n in cupos.items() for _ in range(n)]
    for _ in range(200):                                                       # mezclar sin repetir formato seguido
        rng.shuffle(bolsa)
        if all(bolsa[i] != bolsa[i + 1] for i in range(len(bolsa) - 1)):
            break
    slots, dificil = [], True
    for i, tipo in enumerate(bolsa):
        d, h = divmod(i, len(horas))
        sl = dict(fecha=(inicio + timedelta(days=d)).isoformat(), hora=horas[h], tipo=tipo)
        if tipo == "stop":
            sl["dificil"] = dificil; dificil = not dificil
        slots.append(sl)
    guardar("plan.json", dict(inicio=inicio.isoformat(), puntaje={k: round(v, 3) for k, v in puntaje.items()}, cupos=cupos, slots=slots))
    etapa("plan", "ok", semana=f"{inicio.isoformat()} → {(inicio + timedelta(days=dias - 1)).isoformat()}",
          cupos={fmts[k]["nombre"]: n for k, n in cupos.items()}, por_que={fmts[k]["nombre"]: round(v, 2) for k, v in puntaje.items()})
    return inicio


if __name__ == "__main__":
    import sys
    main(date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else None, int(sys.argv[2]) if len(sys.argv) > 2 else 7)
