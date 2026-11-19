#!/usr/bin/env python3
"""
CATÁLOGO DINÁMICO DE "GOALS BY AGE" (19/11, pedido del CEO: "que nunca se repitan, que cambien de tema").
Combina GRUPOS coherentes de jugadores (solo muy famosos, con historia) × ESTADÍSTICAS reales (goles totales, de selección,
de liga, en copas europeas, de club) × ESCENARIOS (carrera completa / "a la misma edad que X").
Cada escenario es válido solo si los datos lo sostienen (todos los del grupo tienen ese dato y la carrera es pareja).
elegir(rng, usados) devuelve el escenario menos usado/más viejo + variaciones visuales (paleta, música, ritmo).
Datos: assets/goles/goles_edad.json (Wikipedia, goles oficiales; goles_edad.py).
"""
import json
from pathlib import Path

DATOS = Path(__file__).resolve().parent / "assets" / "goles" / "goles_edad.json"

# grupos coherentes (CEO: "los mejores y más conocidos", "con histórico", nada de comparar a uno de 19 con la carrera entera)
GRUPOS = [
    dict(id="goat", jug=["ronaldo", "messi"], nombre="RONALDO vs MESSI"),
    dict(id="big4", jug=["ronaldo", "messi", "lewandowski", "zlatan"]),
    dict(id="goat3", jug=["ronaldo", "messi", "lewandowski"]),
    dict(id="nueves", jug=["lewandowski", "kane", "benzema", "zlatan"], nombre="THE BEST STRIKERS"),
    dict(id="brasil", jug=["neymar", "r9", "ronaldinho", "vinicius"], nombre="BRAZIL LEGENDS"),
    dict(id="francia", jug=["mbappe", "henry", "benzema", "zidane"], nombre="FRANCE LEGENDS"),
    dict(id="madrid", jug=["ronaldo", "benzema", "r9", "zidane"], nombre="REAL MADRID LEGENDS"),
    dict(id="barca", jug=["messi", "neymar", "ronaldinho", "lewandowski"], nombre="BARCELONA LEGENDS"),
    dict(id="premier", jug=["kane", "rooney", "henry", "ronaldo"], nombre="PREMIER LEAGUE LEGENDS"),
    dict(id="psg", jug=["mbappe", "neymar", "messi", "zlatan"], nombre="PSG LEGENDS"),
    dict(id="leyendas", jug=["r9", "henry", "zlatan", "ronaldinho"], nombre="LEGENDS"),
    dict(id="fenomenos", jug=["r9", "messi", "ronaldo"], nombre="R9 vs MESSI vs RONALDO"),
    dict(id="goat_neymar", jug=["ronaldo", "messi", "neymar"]),
    dict(id="nueva_era", jug=["mbappe", "haaland", "kane"], nombre="THE NEW ERA"),
]
# "a la misma edad que X": el más joven marca el final (comparación justa)
MISMA_EDAD = [
    dict(id="yamal", jug=["yamal", "messi", "ronaldo", "mbappe"], ref="yamal", nombre="YAMAL vs LEGENDS AT THE SAME AGE"),
    dict(id="mbappe", jug=["mbappe", "messi", "ronaldo"], ref="mbappe", nombre="MBAPPÉ vs MESSI vs RONALDO AT THE SAME AGE"),
    dict(id="haaland", jug=["haaland", "messi", "ronaldo", "lewandowski"], ref="haaland", nombre="HAALAND vs LEGENDS AT THE SAME AGE"),
    dict(id="vinicius", jug=["vinicius", "neymar", "ronaldinho", "messi"], ref="vinicius", nombre="VINÍCIUS vs LEGENDS AT THE SAME AGE"),
]
ESTAD = {
    "total": dict(titulo="GOALS BY AGE", yt="goals by age", minimo=150),
    "seleccion": dict(titulo="INTERNATIONAL GOALS BY AGE", yt="international goals by age", minimo=30),
    "liga": dict(titulo="LEAGUE GOALS BY AGE", yt="league goals by age", minimo=90),
    "europa": dict(titulo="EUROPEAN CUP GOALS BY AGE", yt="Champions League & European goals by age", minimo=25),
    "club": dict(titulo="CLUB GOALS BY AGE", yt="club goals by age", minimo=120),
}


def _datos():
    return json.loads(DATOS.read_text())["jugadores"]


def escenarios():
    """Todos los escenarios válidos con los datos de hoy."""
    d = _datos()
    out = []

    def fin(k, est):
        s = d[k]["series"][est]; return s[max(s, key=int)]

    for g in GRUPOS:
        if not all(k in d for k in g["jug"]):
            continue
        for est, cfg in ESTAD.items():
            finales = [fin(k, est) for k in g["jug"]]
            if min(finales) < cfg["minimo"] or (est == "club" and g["id"] not in ("goat", "big4", "nueves")):
                continue
            out.append(dict(clave=f"{g['id']}|{est}|full", jugadores=g["jug"], estadistica=est,
                            titulo=cfg["titulo"], subtitulo=g.get("nombre") or "  ·  ".join(d[k]["nombre"].upper() for k in g["jug"]),
                            yt=cfg["yt"]))
    for g in MISMA_EDAD:
        if not all(k in d for k in g["jug"]):
            continue
        edad = d[g["ref"]]["edad_hoy"]
        for est in ("total", "club", "seleccion"):
            vals = [d[k]["series"][est].get(str(edad), 0) for k in g["jug"]]
            if max(vals) < 15:
                continue
            out.append(dict(clave=f"{g['id']}|{est}|edad{edad}", jugadores=g["jug"], estadistica=est, hasta=edad,
                            titulo=ESTAD[est]["titulo"].replace(" BY AGE", f" UNTIL {edad}"), subtitulo=g["nombre"],
                            yt=ESTAD[est]["yt"].replace("by age", f"until age {edad}"), ref=g["ref"]))
    return out


def elegir(rng, usados):
    """El escenario que hace más que no sale (los nunca usados primero); evita repetir grupo y estadística seguidos."""
    todos = escenarios()
    ult = usados[-1] if usados else ""
    ug, ue = (ult.split("|")[:2] + ["", ""])[:2]

    def edad_uso(c):
        return max((i for i, u in enumerate(usados) if u == c), default=-1)
    cand = [e for e in todos if e["clave"].split("|")[0] != ug and e["clave"].split("|")[1] != ue] or todos
    cand.sort(key=lambda e: (edad_uso(e["clave"]), rng.random()))
    e = dict(cand[0])
    d = _datos()
    edades = [min(map(int, d[k]["series"][e["estadistica"]])) for k in e["jugadores"]]
    primeros = [min((int(a) for a, v in d[k]["series"][e["estadistica"]].items() if v > 0), default=30) for k in e["jugadores"]]
    e["desde"] = max(min(edades), min(primeros) - 1, 16)
    return e


if __name__ == "__main__":
    import random
    es = escenarios()
    print(len(es), "escenarios válidos")
    for e in es:
        print(" ", e["clave"], "·", e["subtitulo"])
    usados = []
    r = random.Random(1)
    for _ in range(8):
        e = elegir(r, usados); usados.append(e["clave"]); print("→", e["clave"], e["desde"], e.get("hasta"))
