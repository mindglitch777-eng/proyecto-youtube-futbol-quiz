#!/usr/bin/env python3
"""
Guiones de los formatos de 20 s (render_q20.py) con SISTEMA ANTI-REPETICIÓN (11/11).

Materia prima: todos los recortes descargados (assets/recortes/torsos y cuerpos), la base de fichajes reales
(assets/fichajes.json) y los escudos. Memoria permanente en datos/variedad.json (clase Variedad):
- HIDDEN TRANSFER: cada fichaje sale UNA vez; cuando se usaron todos, vuelve el que hace más tiempo que salió.
- WHO COST MORE?: cada par de jugadores se usa una sola vez; en un video no se repite jugador; los precios tienen que ser
  claramente distintos (≥ 25 %); la final siempre tiene una superestrella (cuadro 0).
- BALLON D'OR: la combinación (pierna izquierda, pierna derecha, academias, compañeros) nunca se repite.
- En los 3: un jugador que fue protagonista no vuelve a serlo en los próximos 6 videos de 20 s (cola "q20_ult").
Cada guion trae sus frases de voz ("voz_lineas"), su título y el comentario fijado.
"""
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REC = ROOT / "assets" / "recortes"
DATOS = json.loads((ROOT / "assets" / "fichajes.json").read_text())
CLUB = DATOS["clubes"]
MALAS = {"cristiano_ronaldo_2", "vin_cius_j_nior_12", "cristiano_ronaldo_3"}            # marca de agua / recorte malo (revisadas a ojo)
ESTRELLAS = {"cristiano_ronaldo": "Ronaldo", "lionel_messi": "Messi", "kylian_mbapp": "Mbappé", "neymar": "Neymar",
             "lamine_yamal": "Yamal", "vin_cius_j_nior": "Vinícius"}
ZURDOS = {"lionel_messi": "MESSI", "lamine_yamal": "YAMAL", "mohamed_salah": "SALAH", "bukayo_saka": "SAKA", "erling_haaland": "HAALAND",
          "ngel_di_mar_a": "DI MARÍA", "gareth_bale": "BALE", "arjen_robben": "ROBBEN", "martin_degaard": "ØDEGAARD", "cole_palmer": "PALMER"}
DIESTROS = {"cristiano_ronaldo": "RONALDO", "kylian_mbapp": "MBAPPÉ", "neymar": "NEYMAR", "vin_cius_j_nior": "VINÍCIUS", "harry_kane": "KANE",
            "jude_bellingham": "BELLINGHAM", "kevin_de_bruyne": "DE BRUYNE", "zinedine_zidane": "ZIDANE", "ronaldinho": "RONALDINHO",
            "robert_lewandowski": "LEWANDOWSKI", "pedri": "PEDRI", "raphinha": "RAPHINHA"}
ACADEMIAS = [("barcelona", "LA MASIA"), ("sporting", "SPORTING"), ("santos", "SANTOS"), ("ajax", "AJAX"), ("river", "RIVER PLATE"),
             ("benfica", "BENFICA"), ("flamengo", "FLAMENGO"), ("boca", "BOCA JUNIORS"), ("man_united", "MAN UNITED"),
             ("real_madrid", "REAL MADRID"), ("dortmund", "DORTMUND"), ("porto", "PORTO"), ("psg", "PSG"), ("monaco", "MONACO")]
NOMBRE_CORTO = {}


def recortes(clave, carpeta="torsos"):
    return sorted(f"{carpeta}/{p.stem}" for p in (REC / carpeta).glob(f"{clave}_*.png") if p.stem not in MALAS)


def escudo_ok(c):
    return (ROOT / "assets" / "escudos" / f"{c}.png").exists()


def nombre(clave):
    for f in DATOS["fichajes"]:
        if f["clave"] == clave:
            return f["nombre"]
    return ESTRELLAS.get(clave) or ZURDOS.get(clave, DIESTROS.get(clave, clave.split("_")[0])).title()


def _ultimos(V):
    return V.contadores.setdefault("q20_ult", [])


def _marcar(V, *claves):
    u = _ultimos(V); u.extend(claves); del u[:-18]


def _libre(V, clave, n=6):
    return clave not in _ultimos(V)[-n:]


def precio_txt(p):
    return "FREE" if p == 0 else f"€{p}M"


def precio_voz(p):
    return "nothing. Free transfer" if p == 0 else f"{p} million euros"


# ------------------------------------------------------------------ 1 · HIDDEN TRANSFER
def fichaje(gid, rng, V):
    usados = V.contadores.setdefault("q20_fichajes", [])                     # orden de uso (el más viejo vuelve primero)
    cand = [f for f in DATOS["fichajes"] if (recortes(f["clave"], "cuerpos") or recortes(f["clave"]))
            and escudo_ok(f["de"]) and escudo_ok(f["a"]) and f["precio"] > 0]
    nuevos = [f for f in cand if f["id"] not in usados and _libre(V, f["clave"])]
    if not nuevos:
        nuevos = sorted([f for f in cand if _libre(V, f["clave"])] or cand, key=lambda f: usados.index(f["id"]) if f["id"] in usados else -1)[:3]
    f = rng.choice(nuevos)
    if f["id"] in usados:
        usados.remove(f["id"])
    usados.append(f["id"]); _marcar(V, f["clave"])
    cuerpo = rng.choice(recortes(f["clave"], "cuerpos") or recortes(f["clave"]))
    no_son = [c for c in ESTRELLAS if c != f["clave"] and recortes(c)]
    rng.shuffle(no_son)
    lineas = ["Only one percent get this transfer before the timer ends!", "He played for these two clubs...",
              f"He cost {precio_voz(f['precio'])}...", "And this is his silhouette. Do you know him yet?",
              f"It's {f['nombre']}! What second did you get it? Comment!"]
    titulo = rng.choice(["Guess the transfer 💰 Only 1% get it in 3 clues", f"Who is this €{f['precio']}M player? 🤔⚽",
                         "Name him before the timer ends ⏱️ Only 1% can", "3 clues, 1 player 🕵️ Can you guess the transfer?"])
    return dict(id=gid, formato="fichaje", cuerpo=cuerpo, clubes=[f["de"], f["a"]], precio=f["precio"] * 1_000_000, anio=f["anio"],
                nombre=f["nombre"], no_son=[rng.choice(recortes(c)) for c in no_son[:3]], voz_lineas=lineas), titulo, \
        f"It was {f['nombre']}: {CLUB[f['de']]} → {CLUB[f['a']]}, {precio_txt(f['precio'])} in {f['anio']} 💰 What second did you get it? 👇", [f["nombre"]]


# ------------------------------------------------------------------ 2 · WHO COST MORE?
def _jugador(f, rng):
    return dict(ref=rng.choice(recortes(f["clave"])), nombre=f["nombre"], precio=f["precio"], txt=precio_txt(f["precio"]),
                detalle=f"{CLUB[f['de']]} → {CLUB[f['a']]} · {f['anio']}", clave=f["clave"], id=f["id"])


def costo(gid, rng, V):
    pares = V.grupos.setdefault("q20_pares", set())
    pool = [f for f in DATOS["fichajes"] if recortes(f["clave"])]
    for intento in range(400):
        en_video, rondas = set(), []
        for r in range(3):
            fin = r == 2
            ok = None
            for _ in range(200):
                a, b = rng.sample(pool, 2)
                if fin and not (a["clave"] in ESTRELLAS or b["clave"] in ESTRELLAS):
                    continue
                if a["clave"] == b["clave"] or {a["clave"], b["clave"]} & en_video:
                    continue
                hi, lo = max(a["precio"], b["precio"]), min(a["precio"], b["precio"])
                if hi == lo or (lo and hi / lo < 1.25):
                    continue
                k = tuple(sorted((a["id"], b["id"])))
                if k in pares or (intento < 300 and not (_libre(V, a["clave"], 3) and _libre(V, b["clave"], 3))):
                    continue
                ok = (a, b); break
            if not ok:
                break
            en_video |= {ok[0]["clave"], ok[1]["clave"]}; rondas.append(ok)
        if len(rondas) == 3:
            break
    else:
        raise RuntimeError("sin pares nuevos para WHO COST MORE")
    for a, b in rondas:
        pares.add(tuple(sorted((a["id"], b["id"]))))
    _marcar(V, *[x["clave"] for p in rondas for x in p])
    R = [[_jugador(a, rng), _jugador(b, rng)] for a, b in rondas]
    if R[2][1]["clave"] not in ESTRELLAS:                                       # la estrella de la final, a la derecha (cuadro 0)
        R[2] = R[2][::-1]

    def gana(p):
        return p[0] if p[0]["precio"] > p[1]["precio"] else p[1]

    def remate(p):
        w, l = gana(p), (p[1] if gana(p) is p[0] else p[0])
        if l["precio"] == 0:
            return f"{w['nombre']}! The other one was free!"
        return f"{w['nombre']}! More than double!" if w["precio"] >= 2 * l["precio"] else f"{w['nombre']}! {w['precio']} million!"
    lineas = ["Who cost more? Round one!", f"{R[0][0]['nombre']} or {R[0][1]['nombre']}?", remate(R[0]),
              f"Round two. Almost nobody gets this one. {R[1][0]['nombre']} or {R[1][1]['nombre']}?", remate(R[1]),
              f"Final round. {R[2][0]['nombre']} or {R[2][1]['nombre']}? Comment your answer before you see it!"]
    f0, f1 = R[2]
    titulo = rng.choice([f"Who cost more? 💰 {f0['nombre']} or {f1['nombre']}", "Who was more expensive? 💸 3 rounds, no Google",
                         f"Who cost more: {f0['nombre']} or {f1['nombre']}? 🤯", "Only 1% get all 3 right 💰 Who cost more?"])
    w = gana(R[2])
    fijado = f"Answer: {w['nombre']} ({w['txt']}, {w['detalle']}) 💰 Did you get all 3? 👇"
    return dict(id=gid, formato="costo", rondas=[[{k: v for k, v in j.items() if k not in ("clave", "id")} for j in r] for r in R],
                voz_lineas=lineas), titulo, fijado, [j["nombre"] for r in R for j in r]


# ------------------------------------------------------------------ 3 · BUILD YOUR BALLON D'OR PLAYER
def balon(gid, rng, V):
    hechos = V.grupos.setdefault("q20_balon", set())
    zur = [c for c in ZURDOS if recortes(c, "cuerpos")]; dies = [c for c in DIESTROS if recortes(c, "cuerpos")]
    acad = [a for a in ACADEMIAS if escudo_ok(a[0])]
    for intento in range(300):
        z = rng.choice([c for c in zur if _libre(V, c, 4)] or zur); d = rng.choice([c for c in dies if _libre(V, c, 4)] or dies)
        ac = rng.sample(acad, 6)
        socios = [c for c in list(ESTRELLAS) + ["erling_haaland", "jude_bellingham", "harry_kane", "pedri", "raphinha", "bukayo_saka",
                                                 "cole_palmer", "mohamed_salah", "rodrygo", "ronaldinho"] if c not in (z, d) and recortes(c)]
        so = rng.sample(socios, 6)
        clave = (z, d, tuple(sorted(a[0] for a in ac)), tuple(sorted(so)))
        if clave not in hechos:
            hechos.add(clave); break
    _marcar(V, z, d)
    ac = [list(a) for a in ac]; ac.insert(rng.randint(2, 5), ["x", "YOU LOSE"])
    pies = [[rng.choice(recortes(z, "cuerpos")), f"{ZURDOS[z]}'S LEFT FOOT"], [rng.choice(recortes(d, "cuerpos")), f"{DIESTROS[d]}'S RIGHT FOOT"]]
    rng.shuffle(pies)
    nz, nd = ZURDOS[z].title(), DIESTROS[d].title()
    a_, b_ = (nz, nd) if "LEFT" in pies[0][1] else (nd, nz)
    pa = "left foot" if "LEFT" in pies[0][1] else "right foot"; pb = "right foot" if pa == "left foot" else "left foot"
    lineas = ["You have three picks to win the Ballon d'Or!", f"Pick fast! {a_}'s {pa}, or {b_}'s {pb}? Three, two, one!",
              "Pause to pick your academy. If you land on this one, you lose!", "Now pause on your strike partner!",
              "Did you win it? Comment your three picks!"]
    gancho = [rng.choice(recortes(c)) for c in rng.sample([c for c in ("lionel_messi", "cristiano_ronaldo", "kylian_mbapp", "neymar") if recortes(c)], 2)]
    titulo = rng.choice(["Build your player to win the Ballon d'Or 🏆 Pause to pick!", "Pause 3 times to win the Ballon d'Or 🏆⚽",
                         "Can you build a Ballon d'Or winner? 🏆 Pause to pick", f"{a_}'s foot or {b_}'s? 🏆 Build your Ballon d'Or player"])
    return dict(id=gid, formato="balon", pies=pies, academias=ac, socios=[[rng.choice(recortes(c)), nombre(c)] for c in so],
                gancho=gancho, voz_lineas=lineas), titulo, "Comment your 3 picks 👇 Did you win the Ballon d'Or? 🏆", [nz, nd]


TIPOS = {"q20fichaje": fichaje, "q20costo": costo, "q20balon": balon}


if __name__ == "__main__":                                                    # prueba: 4 de cada uno sin guardar la memoria
    import sys
    sys.path.insert(0, str(ROOT))
    from variedad import Variedad
    V = Variedad.cargar(); rng = random.Random(7)
    for t, fn in TIPOS.items():
        for i in range(4):
            g, tit, fij, ns = fn(f"t_{t}_{i}", rng, V)
            print(t, "|", tit, "|", " / ".join(g["voz_lineas"][1:3]))
