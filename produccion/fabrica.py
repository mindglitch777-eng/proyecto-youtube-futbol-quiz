#!/usr/bin/env python3
"""
Fábrica semanal: genera N días de videos listos para programar en YouTube Studio, sin repetir combinaciones.
Por día, 4 formatos distintos: STOP CHALLENGE (hiper + beat 6 7) · FIND v2 · ¿CUÁL LOOK? 1-4 · y a la noche, alternando,
CATCH THE RIGHT HEAD o un STOP medio.
Cada video sale con su .txt (título, descripción con créditos, comentario fijado, día y hora) y un CALENDARIO.md.

Uso: python3 produccion/fabrica.py 2026-10-31 7 [semilla]
Salida: produccion/semana_<fecha>/
"""
import json
import random
import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FOTOS = json.loads((ROOT / "assets" / "fotos" / "frontales.json").read_text())
CRED = json.loads((ROOT / "assets" / "fotos" / "creditos.json").read_text())

# nombre en pantalla, clave de foto, peso (los más buscados salen más)
JUGADORES = [("Ronaldo", "cristiano_ronaldo", 5), ("Messi", "lionel_messi", 5), ("Neymar", "neymar", 4), ("Yamal", "lamine_yamal", 4),
             ("Haaland", "erling_haaland", 3), ("Mbappé", "kylian_mbapp", 3), ("Vinícius", "vin_cius_j_nior", 2),
             ("Bellingham", "jude_bellingham", 2), ("Salah", "mohamed_salah", 2), ("Kane", "harry_kane", 1),
             ("Ronaldinho", "ronaldinho", 2), ("Zlatan", "zlatan_ibrahimovi", 2), ("Lewandowski", "robert_lewandowski", 1),
             ("Zidane", "zinedine_zidane", 1), ("Henry", "thierry_henry", 1)]
FORMAS = ["estrella", "triangulo", "corazon", "rombo"]
RASGOS = ["boca", "nariz", "ojo_izq", "ojo_der"]
COLORES = ["rojo", "verde", "amarillo", "azul", "violeta"]
LOOKS = ["corona", "anteojos", "payaso", "cowboy", "cuernos", "aureola", "cadena", "cabezon", "alien", "bigote"]
DIAS = ["lun", "mar", "mie", "jue", "vie", "sab", "dom"]
HORAS = {"stopA": "09:00", "find": "13:00", "look": "17:00", "noche": "21:00"}   # hora de Argentina
FORMATO = {"stop": "STOP", "find": "FIND", "look": "¿CUÁL LOOK?", "cabeza": "CATCH THE RIGHT HEAD", "plinko": "PLINKO GOAT",
           "hoyo": "BALL TO THE HOLE", "dress": "DRESS UP", "torre": "BALL TOWER", "rueda": "WHEEL STOP", "siuu": "SIUUU 67",
           "penal": "PENALTY 100", "balon": "BALLON D'OR 100%", "cabezas": "HEAD FIT", "fitall": "FIT ALL", "pared": "WALL BALANCE",
           "circulo": "GOAT CIRCLE", "trayectoria": "GUESS BY CAREER", "tridente": "TRIDENT €150M",
           "q20fichaje": "HIDDEN TRANSFER", "q20costo": "WHO COST MORE", "q20balon": "BALLON D'OR PICKS"}
SCRIPT = {"stop": "render_stop.py", "find": "render_find_v2.py", "look": "render_look.py", "cabeza": "render_cabeza.py",
          "plinko": "render_plinko.py", "rueda": "render_rueda.py", "siuu": "render_siuu.py",
          "penal": "render_penal.py", "balon": "render_balon.py", "cabezas": "render_cabezas.py", "fitall": "render_fitall.py",
          "pared": "render_pared.py", "circulo": "render_circulo.py", "trayectoria": "render_trayectoria.py",
          "tridente": "render_tridente.py", "q20fichaje": "render_q20.py", "q20costo": "render_q20.py", "q20balon": "render_q20.py",
          "hoyo": "render_hoyo.py", "dress": "render_dress.py", "torre": "render_torre.py"}
TIT_DRESS = ["Pause when it fits 😂 {a} & {b} drip challenge", "Dress them up 😎 Can you stop at the right time? {a} & {b}",
             "Make {a} and {b} DRIP 🥶 Pause it!", "{a} & {b} bald edition 😂 Pause to dress them", "Stop it when it fits 🛑😂 {a} vs {b}"]
TIT_TORRE = ["Whose country is this? 🏳️ {a}, {b} or {c} 👇", "Guess the flag before it's revealed 😳 {a}, {b} or {c}?",
             "Satisfying ball tower ⚽ whose country? {a}, {b} or {c}", "Only real fans get this 🤯 {a}, {b} or {c}?",
             "Wait for the colors... 👀 {a}, {b} or {c}?"]
FONDOS_TORRE = [("#2fb59a", "#1f8f78"), ("#7b5cff", "#5a3fd6"), ("#ff8a3d", "#d9682a"), ("#3da9ff", "#2a82d1"), ("#ff5c8a", "#d63f6d")]
TIT_PLINKO = ["Who Gets The 99 GOAT Card? 🐐 {a}, {b}, {c} or {d}?", "Only ONE lands on 99 🎯 {a} vs {b} vs {c} vs {d}",
              "Plinko decides the GOAT 🐐 {a}, {b}, {c} or {d}?", "{a}, {b}, {c} or {d}... who gets 99? 👇",
              "4 balls, 1 GOAT card 🐐 Pick yours: {a}, {b}, {c} or {d}"]
PANT_PLINKO = ["WHO GETS 99?", "WHO'S THE GOAT?", "WHO LANDS 99?"]
TIT_HOYO = ["Which ball goes in? ⚽🕳️ {a}, {b}, {c} or {d}", "Only ONE ball goes in 😳 {a}, {b}, {c} or {d}?",
            "{a} vs {b} vs {c} vs {d} ⚽ who gets the hole-in-one?", "Ball to the hole 🕳️ {a}, {b}, {c} or {d}... who wins?",
            "Pick a ball before it rolls 👇 {a}, {b}, {c} or {d}"]
PANT_HOYO = ["WHO WINS?", "WHO GETS IN?", "PICK A BALL"]
FRASES = ["99% FAIL THIS", "YOUR EYES WILL LIE", "ONLY 1% GET 3/3", "IMPOSSIBLE LEVEL"]
TIT_CABEZA = ["Catch the right head 🤯 {n} edition", "Which head is {n}'s? 1, 2 or 3 😳", "Give {n} his head back 💀 1, 2 or 3?"]
COLORES_CABEZA = [[60, 170, 255], [255, 120, 40], [120, 210, 70], [170, 90, 255], [255, 70, 140]]
TIT_STOP = ["Football Stop Challenge ⚽🛑 Can you stop at 100%?", "Football Stop Challenge ⚽🛑 Only 1% can stop it 6️⃣7️⃣",
            "Football Stop Challenge ⚽🛑 Pause at the perfect moment"]
TIT_LOOK = ["Which {n} look is best? 1, 2, 3 or 4 🤔", "{n} new look 😳 Pick one: 1, 2, 3 or 4", "Rate {n}'s looks 👀 1, 2, 3 or 4?"]
PANT_LOOK = ["WHICH LOOK IS BEST?", "PICK HIS NEXT LOOK", "RATE THE LOOK"]


def elegir(rng, k, usados):
    """k jugadores distintos, por peso, evitando repetir el mismo grupo."""
    while True:
        pool = [j for j in JUGADORES]
        grupo = []
        while len(grupo) < k:
            j = rng.choices(pool, [w for *_, w in pool])[0]
            pool.remove(j); grupo.append(j)
        clave = tuple(sorted(n for n, *_ in grupo))
        if clave not in usados:
            usados.add(clave); return grupo


NOMBRE = {"kak": "Kaká", "ousmane_demb_l": "Dembélé", "son_heung_min": "Son", "arda_g_ler": "Güler", "vin_cius_j_nior": "Vinícius",
          "kylian_mbapp": "Mbappé", "zlatan_ibrahimovi": "Zlatan", "federico_valverde": "Valverde", "jamal_musiala": "Musiala",
          "florian_wirtz": "Wirtz", "bukayo_saka": "Saka", "phil_foden": "Foden", "declan_rice": "Rice", "kevin_de_bruyne": "De Bruyne",
          "marcus_rashford": "Rashford", "david_beckham": "Beckham", "toni_kroos": "Kroos", "gareth_bale": "Bale", "karim_benzema": "Benzema",
          "sergio_ramos": "Ramos", "rodrygo": "Rodrygo", "gavi": "Gavi", "pedri": "Pedri", "robert_lewandowski": "Lewandowski"}
TEMAS_STOP = {   # B1: misma mecánica, temas que rotan
    "GOATS": ["lionel_messi", "cristiano_ronaldo", "neymar", "ronaldinho", "zinedine_zidane", "kylian_mbapp"],
    "LEGENDS": ["ronaldinho", "zinedine_zidane", "thierry_henry", "david_beckham", "kak", "zlatan_ibrahimovi", "sergio_ramos", "toni_kroos",
                "gareth_bale", "karim_benzema"],
    "BALLON D'OR": ["lamine_yamal", "kylian_mbapp", "erling_haaland", "vin_cius_j_nior", "jude_bellingham", "mohamed_salah", "harry_kane",
                    "pedri", "ousmane_demb_l"],
    "BARÇA vs MADRID": ["lamine_yamal", "pedri", "robert_lewandowski", "gavi", "kylian_mbapp", "vin_cius_j_nior", "jude_bellingham",
                        "federico_valverde", "rodrygo", "arda_g_ler"],
    "PREMIER LEAGUE": ["erling_haaland", "mohamed_salah", "bukayo_saka", "phil_foden", "declan_rice", "son_heung_min", "kevin_de_bruyne",
                       "marcus_rashford", "florian_wirtz"],
    "YOUNG STARS": ["lamine_yamal", "jude_bellingham", "jamal_musiala", "florian_wirtz", "arda_g_ler", "gavi", "pedri", "bukayo_saka"],
}
TEMA_TITULO = {"GOATS": "GOATs", "LEGENDS": "Legends", "BALLON D'OR": "Ballon d'Or", "BARÇA vs MADRID": "Barça vs Madrid",
               "PREMIER LEAGUE": "Premier League", "YOUNG STARS": "Young Stars"}
TIT_STOP_SERIE = ["Football Stop Challenge #{n} ⚽🛑 {tema} edition", "Stop at 100% ⚽🛑 Level {n}: {tema}",
                  "Football Stop Challenge Level {n} 🛑 {tema} — only 1% can stop it", "Can you stop at 100%? ⚽🛑 #{n} {tema}"]


# REGLA PARA SIEMPRE (pedido del dueño del canal): en el primer cuadro de TODOS los videos aparece una superestrella
# (la cara más conocida frena el scroll: el 49% que hoy desliza decide en <0,4 s). Va en el lugar más visible de cada formato.
SUPERESTRELLAS = ["cristiano_ronaldo", "lionel_messi", "kylian_mbapp", "lamine_yamal", "neymar", "vin_cius_j_nior"]
_uso_estrellas = {}


def con_estrella(grupo, rng, pool=None):
    """Devuelve el grupo con una superestrella en el lugar 0. Si no hay ninguna, entra la menos usada (reemplaza al último)."""
    grupo = list(grupo)
    idx = [i for i, (_, c, _) in enumerate(grupo) if c in SUPERESTRELLAS]
    if idx:
        i = idx[0]
    else:
        cand = [j for j in (pool or JUGADORES) if j[1] in SUPERESTRELLAS and j[1] not in {c for _, c, _ in grupo}]
        cand = cand or [j for j in JUGADORES if j[1] in SUPERESTRELLAS and j[1] not in {c for _, c, _ in grupo}]
        minimo = min(_uso_estrellas.get(j[1], 0) for j in cand)
        grupo[-1] = rng.choice([j for j in cand if _uso_estrellas.get(j[1], 0) == minimo])
        i = len(grupo) - 1
    grupo.insert(0, grupo.pop(i))
    _uso_estrellas[grupo[0][1]] = _uso_estrellas.get(grupo[0][1], 0) + 1
    return grupo


# Fórmula de título de STOP (datos de YouTube Studio: el más visto llevaba nombre de estrella + meta exacta "100";
# el peor, un título genérico sin nombres). Siempre: marca + superestrella + meta numérica + hashtags de los jugadores.
TIT_STOP_FORMULA = ["Football Stop Challenge ⚽🛑 Only 1% can stop it 6️⃣7️⃣",          # 15.800 de mediana (Studio 07/11)
                    "Football Stop Challenge ⚽🛑 Can you stop {a} at 100%?",         # 14.000 ("Pause at the perfect moment": 5.000, afuera)
                    "Football Stop Challenge ⚽🛑 Can you stop at 100%?",
                    "Football Stop Challenge ⚽🛑 Only 1% can stop {a} 6️⃣7️⃣"]


import difflib
import re as _re

EMOJIS_EXTRA = ["🔥", "🛑", "😱", "🤯", "💀", "⚽", "😤", "👀"]


def _norm(t):
    t = _re.sub(r"#\w+", "", t.lower())
    return _re.sub(r"[^a-z0-9áéíóúñü%' ]+", " ", t).split()


def parecido(a, b):
    return difflib.SequenceMatcher(None, _norm(a), _norm(b)).ratio()


# Variantes COMPLETAS y naturales por formato (07/11): cuando un título se parece a otro, se elige otra de estas con otros jugadores.
VARIANTES = {
    "stop": ["Football Stop Challenge ⚽🛑 Only 1% can stop {a} 6️⃣7️⃣", "Football Stop Challenge ⚽🛑 Can you stop {a} at 100%?",
             "Football Stop Challenge ⚽🛑 {a} or {b}: who can you stop?", "Football Stop Challenge ⚽🛑 Stop {a} at 100% if you can",
             "Football Stop Challenge ⚽🛑 Impossible level: {a} vs {b}", "Football Stop Challenge ⚽🛑 Only legends stop {a} 💀",
             "Football Stop Challenge ⚽🛑 {a}, {b} or {c} at 100%?", "Football Stop Challenge ⚽🛑 99% fail with {a} 😤",
             "Football Stop Challenge ⚽🛑 Stop {a} before {b} 6️⃣7️⃣", "Football Stop Challenge ⚽🛑 Can you beat {a}'s level?"],
    "rueda": ["{a} vs {b} or {c} stop challenge 🔥🛑", "{a} vs {b} or {c} stop challenge 😱🔥", "{a} vs {b} or {c} stop challenge 🛑🤯",
              "{a} vs {b} or {c} stop challenge 💀🔥", "Find {a}'s real body 🛑🔥 {b} or {c}?"],
    "fitall": ["Can Anyone Solve This? Fit All {a} Heads 🎯⚽", "Fit {a}'s REAL head 🎯 Only 1 of 8 is real",
               "Can you find {a}'s real head? 🎯⚽ Only 1% can", "8 {a} heads, only 1 fits 😱🎯 Can you solve this?",
               "Only 1 of these {a} heads is real 🎯 Pause it!", "{a} fit all challenge 🎯 Which head is the real one?",
               "Pause on the REAL {a} 😤🎯 7 are fake", "Nobody solves this {a} puzzle 💀🎯", "Which {a} is real? 🎯⚽ Stop it on the right head",
               "IMPOSSIBLE {a} head puzzle 🤯 Can anyone solve this?", "Real or fake {a}? 🎯 Fit the right head", "{a} lost his head 😂🎯 Find the real one"],
    "cabezas": ["99.9% WILL FAIL the FIT challenge 💀 {a} edition", "Fit {a}'s head 🛑 Only 1% can", "{a} head fit challenge 😱 Pause it!",
                "Can you fit {a}'s head perfectly? 🤯", "Only 1% can fit {a}'s face 🎯", "This is almost impossible! Fit {a} 🎯⚽"],
}
EMOJIS_EXTRA = ["🔥", "🛑", "😱", "🤯", "💀", "⚽", "😤", "👀"]


def _norm(t):
    t = _re.sub(r"#\w+", "", t.lower())
    return _re.sub(r"[^a-z0-9áéíóúñü%' ]+", " ", t).split()


def parecido(a, b):
    return difflib.SequenceMatcher(None, _norm(a), _norm(b)).ratio()


def _con_tags(base, tags):
    """Título final sin cortar palabras: los hashtags entran solo si caben en 100 caracteres."""
    out = base.strip()
    for t in dict.fromkeys(x.lower() for x in tags):                           # sin hashtags repetidos (#messi #messi)
        if len(out) + len(t) + 1 <= 100:
            out += " " + t
    return out


def titulo_unico(titulo, previos, rng, nombres=(), umbral=0.7, tipo=None):
    """REGLA (07/11): nunca dos títulos parecidos. Si se parece > umbral a uno ya usado, elige otra variante COMPLETA del
    formato (VARIANTES) con otros jugadores; nunca pega frases sueltas ni corta palabras."""
    tags = [w for w in titulo.split() if w.startswith("#")]
    base = " ".join(w for w in titulo.split() if not w.startswith("#"))
    def ok(t):
        return all(parecido(t, p) < umbral for p in previos)
    if ok(base):
        return _con_tags(base, tags)
    ns = [n for n in nombres if n] or ["Messi", "Ronaldo", "Mbappé"]
    while len(ns) < 3:
        ns.append(rng.choice(["Messi", "Ronaldo", "Mbappé", "Yamal", "Neymar"]))
    pool = VARIANTES.get(tipo, [])
    mejor = (2.0, base)                                                        # si nada queda bajo el umbral: la MENOS parecida (nunca la repetida)
    for _ in range(200):
        if not pool:
            break
        resto = ns[1:]
        if tipo in ("rueda", "cabezas", "stop", "fitall"):                                # el protagonista (la superestrella) SIEMPRE va primero
            a = ns[0]; b, c = (rng.sample(resto, 2) if len(resto) >= 2 else (resto + ns)[:2])
        else:
            a, b, c = rng.sample(ns, 3) if len(set(ns)) >= 3 else (ns[0], ns[1], ns[2])
        t = rng.choice(pool).format(a=a, b=b, c=c)
        if ok(t):
            return _con_tags(t, tags)
        pm = max((parecido(t, p) for p in previos), default=0)
        if pm < mejor[0]:
            mejor = (pm, t)
    for _ in range(100):                                                       # último recurso: mismo título con otro par de emojis
        t = _re.sub(r"[🔥🛑😱🤯💀⚽😤👀]+", "", base).strip() + " " + "".join(rng.sample(EMOJIS_EXTRA, 2))
        if ok(t):
            return _con_tags(t, tags)
    return _con_tags(mejor[1], tags)


def titulo_stop(V, rng, nombres, nivel=None):
    base = (V.titulo("stop_formula", TIT_STOP_FORMULA, rng) if V else rng.choice(TIT_STOP_FORMULA)).format(a=nombres[0], b=nombres[1])
    if nivel and False:                                                        # el nivel queda en pantalla, no en el título
        base += f" · Level {nivel}"
    for n in nombres[:3]:                                                      # hashtags de jugadores (los del top los tenían)
        if len(base) + len(tag(n)) + 1 <= 100:
            base += " " + tag(n)
    return base


def nombre_de(clave):
    for n, c, _ in JUGADORES:
        if c == clave:
            return n
    return NOMBRE.get(clave, clave.split("_")[0].title())


def guion_stop(gid, rng, usados, dificil, V=None, fecha=None, hard_pedido=False):
    """STOP en serie (#nivel), con tema rotativo (B1) y cada 3er nivel HARD: más vueltas, giro doble y 5 s (B2)."""
    tema = nivel = None; hard = False
    if V is not None:
        tema = V.titulo("stop_tema", list(TEMAS_STOP), rng)
        nivel = V.siguiente("stop_nivel", 13)
        pool = [(nombre_de(c), FOTOS.get(c) and c, 3) for c in TEMAS_STOP[tema] if c in FOTOS]
        grupo = V.grupo("stop_" + tema, 4, rng, pool, fecha)
        hard = bool(hard_pedido)                                               # el lugar de las 21:00 es el HARD (grilla nueva)
    else:
        grupo = elegir(rng, 4, usados)
    grupo = con_estrella(grupo, rng)                                           # cuadrante 1 (arriba a la izquierda) = superestrella
    pcts = [f"{rng.choice([1, 1, 2, 3])}%", f"{rng.randint(5, 29)}%", f"{rng.randint(33, 61)}%", f"{rng.choice([67, 67, 69, 88, 99])}%"]
    # MODO IMPOSIBLE (06/11): el viejo HARD es ahora el nivel normal y el HARD es casi imposible. Más difícil = más intentos = más loops.
    vueltas = ([8, 7, 7, 8] if hard else [6, 5, 5, 6]) if dificil else [5, 4, 4, 5]
    giros = ([3, 2, 2, 3] if hard else [2, 2, 1, 2]) if dificil else [2, 1, 1, 2]
    colores = rng.sample(COLORES, 4); formas = [rng.choice(FORMAS) for _ in range(4)]
    cuads = []
    for k, (n, clave, _) in enumerate(grupo):
        cuads.append(dict(nombre=n, foto=FOTOS[clave], color=colores[k], pct=pcts[k], forma=formas[k], rasgo=rng.choice(RASGOS),
                          vueltas=vueltas[k], giros=giros[k], encaje_bueno=rng.randint(0, 3), fase=round(rng.uniform(0, 6.28), 2),
                          tam=rng.choice([54, 58, 62])))
    g = dict(id=gid, duracion=5.0 if hard else 6.0, hiper=True, musica="67", cuadrantes=cuads,
             arranque=rng.choice(["estrella", "grilla"]))                    # prueba A/B: arranque tipo FIND (zoom a la estrella) vs. grilla
    if nivel:
        g.update(tema=(tema + " · HARD") if hard else tema, nivel=nivel, pregunta="WHICH ONE DID YOU STOP? 1-4", tema_base=tema)
    return g


def guion_look(gid, rng, usados_look, V=None):
    hechos = V.grupos.setdefault("look", set()) if V else set()
    for intento in range(500):
        n, clave, _ = rng.choice([j for j in JUGADORES if j[1] in SUPERESTRELLAS])
        looks = rng.sample(LOOKS, 4)
        combo = tuple([n] + sorted(looks))
        if (n not in usados_look or intento > 300) and combo not in hechos:   # un jugador distinto cada día; combo nunca repetido
            usados_look.add(n); hechos.add(combo); break
    return dict(id=gid, foto=FOTOS[clave], nombre=n, looks=looks, color0=rng.randint(0, 5), titulo_pantalla=rng.choice(PANT_LOOK))


def guion_find(gid, rng, usados, V=None):
    grupo = con_estrella(elegir(rng, 3, usados), rng)                          # la ronda 1 (primer cuadro) es una superestrella
    rondas = [dict(nombre=n, foto=FOTOS[c], nivel=nv) for (n, c, _), nv in zip(grupo, ["facil", "medio", "dificil"])]
    return dict(id=gid, semilla=V.semilla(rng) if V else rng.randint(1, 999), frase=rng.choice(FRASES), rondas=rondas)


def guion_cabeza(gid, rng, usados_cab, V=None):
    hechos = V.grupos.setdefault("cabeza", set()) if V else set()
    for intento in range(500):
        grupo = elegir(rng, 3, set())
        combo = tuple([grupo[0][0]] + sorted(n for n, *_ in grupo[1:]))
        if (grupo[0][0] not in usados_cab or intento > 300) and combo not in hechos:
            usados_cab.add(grupo[0][0]); hechos.add(combo); break
    grupo = con_estrella(grupo, rng)                                           # la cabeza a encontrar es de una superestrella
    real = grupo[0]; opciones = [FOTOS[c] for _, c, _ in grupo[1:]]
    opciones.insert(rng.choice([1, 2]), FOTOS[real[1]])                       # la correcta nunca es la primera
    return dict(id=gid, nombre=real[0], foto=FOTOS[real[1]], opciones=opciones, color=rng.choice(COLORES_CABEZA))


# WHEEL STOP: piernas de una superestrella (foto de cuerpo entero de frente) + rueda de 8 torsos. Solo recortes aprobados a ojo.
CUERPOS_RUEDA = {"lionel_messi_3": "Messi", "lamine_yamal_10": "Yamal", "kylian_mbapp_12": "Mbappé",
                 "cristiano_ronaldo_14": "Ronaldo", "neymar_1": "Neymar", "vin_cius_j_nior_14": "Vinícius"}   # 08/11: +3 probados a ojo
TORSOS_RUEDA = ["cristiano_ronaldo_0", "lionel_messi_0", "kylian_mbapp_0", "lamine_yamal_0", "neymar_2", "erling_haaland_1",
                "vin_cius_j_nior_0", "vin_cius_j_nior_3", "jude_bellingham_0", "jude_bellingham_1", "mohamed_salah_0", "harry_kane_1",
                "pedri_2", "ronaldinho_0", "phil_foden_0", "bukayo_saka_2", "cole_palmer_1", "raphinha_0", "lautaro_mart_nez_1"]
# WHEEL: SIEMPRE la fórmula del mercado "X vs Y or Z stop challenge" (07/11: con ella 18-26k vistas; "Stop the wheel on Messi" 3,4k)
TIT_RUEDA = ["{n} vs {a} or {b} stop challenge 🔥🛑", "{n} vs {a} or {b} stop challenge 😱🔥", "{n} vs {a} or {b} stop challenge 🛑🤯",
             "Find {n}'s real body 🛑🔥 {a} or {b}?"]                                 # 15.641: también funciona


def guion_rueda(gid, rng, V, fecha):
    usados = V.grupos.setdefault("rueda", set())
    ult = V.contadores.setdefault("rueda_ult", [])                            # rota el dueño del cuerpo (antes: Mbappé 6 de 8)
    cuerpo = min(sorted(CUERPOS_RUEDA), key=lambda c: (c == (ult[-1] if ult else None), ult[-6:].count(c), rng.random()))
    ult.append(cuerpo); del ult[:-12]
    for _ in range(300):
        base = cuerpo.rsplit("_", 1)[0]
        pool = [t for t in TORSOS_RUEDA if t.rsplit("_", 1)[0] != base]
        estrellas = [t for t in pool if t.rsplit("_", 1)[0] in SUPERESTRELLAS]
        torsos = rng.sample(estrellas, 2) + rng.sample([t for t in pool if t not in estrellas], 5)
        rng.shuffle(torsos)
        clave = (cuerpo,) + tuple(sorted(torsos))
        if clave not in usados:
            usados.add(clave); break
    nombre = CUERPOS_RUEDA[cuerpo]
    otros = [nombre_de(t.rsplit("_", 1)[0]) for t in torsos if t.rsplit("_", 1)[0] in SUPERESTRELLAS]
    return dict(id=gid, cuerpo=cuerpo, nombre=nombre, torsos=torsos, dur=6.6, vueltas=4, t_encaje=0.45, sentido=rng.choice([1, -1]),
                musica=f"rueda_original_{rng.randint(0, 2)}", fondo="estadio_0", pos_correcto=rng.randint(2, 6), otros=otros)


# Formatos nuevos con la mecánica STOP (ideas de la IA de YouTube Studio, 02/11)
TIT_SIUU = ["Pause Ronaldo at 67 😱 SIUUU challenge", "Only 1% stop CR7 at 67 🛑 SIUUU", "Stop at 67 = SIUUU 🔥 Can you do it?",
            "SIUUU at 67 🛑 Pause it at the top!"]
TIT_PENAL = ["Can {n} score at 100%? ⚽🛑 Stop it in the top corner", "Stop the penalty at 100% ⚽ {n} edition",
             "{n} penalty challenge 🛑 Only 1% hit the top corner"]
TIT_BALON = ["Freeze the Ballon d'Or in {n}'s hands 🏆 Stop at 100%", "Give {n} the Ballon d'Or 🏆🛑 Only 1% can",
             "Stop the Ballon d'Or at 100% 🏆 {n} edition"]


def extra_mejor(prefijo, defecto):
    """El primer recorte aprobado de assets/recortes/extras (aprobados.json), o el de respaldo."""
    ap = ROOT / "assets" / "recortes" / "extras" / "aprobados.json"
    lista = json.loads(ap.read_text()).get(prefijo, []) if ap.exists() else []
    return lista, defecto


def guion_siuu(gid, rng, V, fecha):
    lista, defecto = extra_mejor("siuu", "cuerpos/cristiano_ronaldo_11")
    img = rng.choice(["extras/" + x for x in lista] or [defecto])
    return dict(id=gid, imagen=img, dur=6.0, ciclo=round(rng.uniform(0.85, 1.05), 2), musica=V.musica(rng), desfase=round(rng.uniform(0.15, 0.3), 2))


def guion_penal(gid, rng, V, fecha):
    estrellas = [(nombre_de(c), c) for c in SUPERESTRELLAS if c in FOTOS]
    hechos = V.grupos.setdefault("penal", set())
    n, c = min(estrellas, key=lambda e: (sum(1 for x in hechos if x[0] == e[1]), rng.random()))
    hechos.add((c, str(len(hechos))))
    lista, _ = extra_mejor("arquero", None)
    return dict(id=gid, pateador=c, nombre=n, dur=6.0, vueltas=5, musica=V.musica(rng), arquero=(rng.choice(lista) if lista else "arquero_0"))


def guion_balon(gid, rng, V, fecha):
    cuerpo = rng.choice(sorted(CUERPOS_RUEDA))
    lista, _ = extra_mejor("trofeo_bo", None)
    return dict(id=gid, cuerpo=cuerpo, nombre=CUERPOS_RUEDA[cuerpo], trofeo=(rng.choice(lista) if lista else "trofeo_bo_1"),
                dur=6.0, vueltas=5, musica=V.musica(rng))


# Tendencias de la semana del 04/11 (radar + Gemini): FIT challenge 6,6 M · balance at the wall 6,9 M · "who is the best" 6 M
CUERPOS_FIT = {"kylian_mbapp_13": "kylian_mbapp", "kylian_mbapp_12": "kylian_mbapp", "lionel_messi_3": "lionel_messi",
               "cristiano_ronaldo_14": "cristiano_ronaldo", "lamine_yamal_10": "lamine_yamal", "neymar_3": "neymar"}
CUERPOS_PARED = ["lionel_messi_3", "kylian_mbapp_10", "cristiano_ronaldo_14", "bukayo_saka_3", "ousmane_demb_l_3",
                 "lautaro_mart_nez_3", "kylian_mbapp_11"]                          # (sin mohamed_salah_1: tiene marca de agua)
TIT_CABEZAS = ["99.9% WILL FAIL the FIT challenge 💀 {n} edition", "Fit {n}'s head 🛑 Only 1% can", "{n} head fit challenge 😱 Pause it!"]
TIT_PARED = ["Who has the best balance? 👀⚽ {a}, {b}, {c} or {d}", "Who won't fall? 😱 {a} vs {b} vs {c} vs {d}",
             "Only one stays up 🤯 {a}, {b}, {c} or {d}?"]
TIT_CIRCULO = ["Pause on your GOAT 🐐 {a}, {b} or {c}?", "Who is the BEST footballer? 🐐 Pause it!", "Stop the ball on your GOAT 🐐⚽"]


# FIT ALL (ola del 09/11: 18 videos +1 M en 7 días, canales chicos): 8 cabezas de la MISMA estrella, solo una es la real.
TIT_FITALL = ["Can Anyone Solve This? Fit All {n} Heads 🎯⚽", "Fit {n}'s REAL head 🎯 Only 1 of 8 is real",
              "Can you find {n}'s real head? 🎯⚽ Only 1% can", "8 {n} heads, only 1 fits 😱🎯 Can you solve this?",
              "{n} fit all challenge 🎯 Which head is the real one?", "Pause on the REAL {n} 😤🎯 7 are fake",
              "IMPOSSIBLE {n} head puzzle 🤯 Can anyone solve this?", "Real or fake {n}? 🎯 Fit the right head"]
MUSICA_FITALL = {"cristiano_ronaldo": ["suuu_remix_0", "suuu_remix_1", "walkout_0"], "neymar": ["neymar_samba_0", "neymar_samba_1"],
                 "lionel_messi": ["messi_ankara_remix_0", "ankara_messi_0"]}


def guion_fitall(gid, rng, V, fecha):
    import render_fitall as RF
    ult = V.contadores.setdefault("fitall_ult", [])
    cand = [c for c in RF.LISTAS if c in RF.CUERPOS]
    est = min(sorted(cand), key=lambda c: (c == (ult[-1] if ult else None), ult[-6:].count(c), rng.random()))
    ult.append(est); del ult[:-12]
    cuerpo = rng.choice(RF.CUERPOS[est])
    mus = MUSICA_FITALL.get(est) or ["walkout_0", "walkout_1", "parado_bailao_0", "rueda_original_1"]
    return dict(id=gid, cuerpo=cuerpo, senuelos=RF.senuelos(cuerpo, rng), nombre=RF.NOMBRES[est], dur=4.0, vueltas=3, t_encaje=0.45,
                sentido=rng.choice([1, -1]), musica=rng.choice(mus), fondo="estadio_0", pos_correcto=rng.randint(1, 6))


def guion_cabezas(gid, rng, V, fecha):
    cuerpo = rng.choice(sorted(CUERPOS_FIT)); clave = CUERPOS_FIT[cuerpo]
    otras = [c for c in FOTOS if c != clave]
    est = [c for c in SUPERESTRELLAS if c != clave and c in FOTOS]
    cab = rng.sample(est, 3) + rng.sample([c for c in otras if c not in est], 4); rng.shuffle(cab)
    return dict(id=gid, cuerpo=cuerpo, clave=clave, nombre=nombre_de(clave), cabezas=cab, dur=6.4, vueltas=4,
                sentido=rng.choice([1, -1]), pos_correcto=rng.randint(2, 6), musica=f"rueda_original_{rng.randint(0, 2)}")


def guion_pared(gid, rng, V, fecha):
    estrellas = [c for c in CUERPOS_PARED if c.rsplit("_", 1)[0] in SUPERESTRELLAS]
    otros = [c for c in CUERPOS_PARED if c not in estrellas]
    for _ in range(50):
        cs = rng.sample(estrellas, 2) + rng.sample(otros, 2)
        if len({c.rsplit("_", 1)[0] for c in cs}) == 4:
            break
    rng.shuffle(cs)
    nombres = [nombre_de(c.rsplit("_", 1)[0]) for c in cs]
    return dict(id=gid, cuerpos=cs, nombres=nombres, ganador=V.ganador(nombres, rng), dur=7.0, musica=V.musica(rng))


def guion_circulo(gid, rng, V, fecha):
    est = [c for c in SUPERESTRELLAS if c in FOTOS]
    resto = rng.sample([c for c in FOTOS if c not in est], 3)
    cl = est + resto; rng.shuffle(cl)
    return dict(id=gid, claves=cl, nombres=[nombre_de(c) for c in cl], dur=8.0, musica=V.musica(rng))


# Ideas aprobadas el 05/11 (IA de YouTube Studio), en modo imposible
TIT_TRAYECTORIA = ["Guess him in 3 seconds ⏱️ 99% can't", "Who is this player? 🤔 Only real fans know", "Guess the player by his clubs ⏱️"]
TIT_TRIDENTE = ["Build your trident with €150M 💰 99% go bankrupt", "Pause to pick your 3 ⚽ Can you stay under €150M?",
                "€150M budget challenge 💸 Pause it!"]
RODILLOS = [[["vin_cius_j_nior", "Vinícius", 120], ["kylian_mbapp", "Mbappé", 150], ["neymar", "Neymar", 20], ["khvicha_kvaratskhelia", "Kvara", 70],
             ["marcus_rashford", "Rashford", 30], ["rodrygo", "Rodrygo", 60]],
            [["erling_haaland", "Haaland", 150], ["harry_kane", "Kane", 70], ["robert_lewandowski", "Lewandowski", 10],
             ["lautaro_mart_nez", "Lautaro", 80], ["cristiano_ronaldo", "Ronaldo", 10], ["juli_n_lvarez", "Julián", 75]],
            [["lamine_yamal", "Yamal", 160], ["mohamed_salah", "Salah", 40], ["bukayo_saka", "Saka", 100], ["lionel_messi", "Messi", 15],
             ["ousmane_demb_l", "Dembélé", 60], ["phil_foden", "Foden", 80]]]


def guion_trayectoria(gid, rng, V, fecha):
    import render_trayectoria as RT
    hechos = V.grupos.setdefault("trayectoria", set())
    cand = [k for k in RT.CARRERAS if (k,) not in hechos] or list(RT.CARRERAS)
    k = rng.choice(cand); hechos.add((k,))
    n, clubes = RT.CARRERAS[k]
    return dict(id=gid, clave=k, nombre=n, clubes=clubes, dur=5.5, musica=V.musica(rng))


def guion_tridente(gid, rng, V, fecha):
    rod = [rng.sample(r, 5) for r in RODILLOS]
    return dict(id=gid, presupuesto=150, rodillos=rod, dur=7.0, musica=V.musica(rng),
                vueltas=[rng.randint(14, 17), rng.randint(11, 13), rng.randint(15, 18)])


def guion_plinko(gid, rng, V, fecha):
    grupo = con_estrella(V.grupo("plinko", 4, rng, JUGADORES, fecha), rng)
    return dict(id=gid, jugadores=[c for _, c, _ in grupo], nombres=[n for n, _, _ in grupo], semilla=V.semilla(rng) * 5000,
                titulo=V.titulo("plinko_pantalla", PANT_PLINKO, rng), musica=V.musica(rng))


def guion_dress(gid, rng, V, fecha):
    grupo = con_estrella(V.grupo("dress", 2, rng, JUGADORES, fecha), rng)
    malos = [{"n": "payaso", "ok": False}, {"n": "pelo_azul~" + str(rng.choice([220, 280, 30, 0])), "ok": False},
             {"n": "peluca_rosa~" + str(rng.choice([320, 190, 50])), "ok": False}]
    rng.shuffle(malos)
    pelo = {"n": "pelo_verde" + rng.choice(["", "~0", "~45", "~270", "~200"]), "ok": True}
    medio = [{"n": "cadena", "ok": True}] + malos
    rng.shuffle(medio)
    return dict(id=gid, jugadores=[c for _, c, _ in grupo], nombres=[n for n, _, _ in grupo], musica=V.musica(rng),
                items=[{"n": "anteojos", "ok": True}] + medio + [pelo])


def guion_torre(gid, rng, V, fecha):
    import cartas
    import render_torre as RT
    pool = [j for j in JUGADORES if cartas.datos(j[1])[2] in RT.BANDERAS]
    for _ in range(300):
        grupo = V.grupo("torre", 3, rng, pool, fecha)
        grupo = con_estrella(grupo, rng, pool)
        if len({cartas.datos(c)[2] for _, c, _ in grupo}) == 3:
            break
    nombres = [n for n, _, _ in grupo]
    fondo, piso = rng.choice(FONDOS_TORRE)
    return dict(id=gid, opciones=[c for _, c, _ in grupo], nombres=nombres, correcta=V.ganador(nombres, rng), semilla=V.semilla(rng),
                musica=V.musica(rng), fondo=fondo, piso=piso)


def guion_hoyo(gid, rng, V, fecha):
    grupo = con_estrella(V.grupo("hoyo", 4, rng, JUGADORES, fecha), rng)
    nombres = [n for n, _, _ in grupo]
    return dict(id=gid, jugadores=[c for _, c, _ in grupo], nombres=nombres, ganador=V.ganador(nombres, rng), semilla=V.semilla(rng),
                titulo=V.titulo("hoyo_pantalla", PANT_HOYO, rng), musica=V.musica(rng))


def creditos(claves):
    return "\n".join(f'- {CRED[k]["jugador"]}: "{CRED[k]["archivo"].replace("File:", "")}" by {CRED[k]["autor"]}, {CRED[k]["licencia"]} '
                     f'({CRED[k]["pagina"]}). Edited.' for k in claves if k in CRED)


def tag(n):
    import unicodedata
    n = unicodedata.normalize("NFKD", n).encode("ascii", "ignore").decode()
    return "#" + "".join(ch for ch in n.lower() if ch.isalnum())


def render(args):
    tipo, ruta = args
    r = subprocess.run([sys.executable, str(ROOT / SCRIPT[tipo]), str(ruta)], capture_output=True, text=True, cwd=ROOT)
    return ruta, r.returncode, r.stderr[-400:]


def slots_por_defecto(inicio, dias):
    """La grilla fija: 09 STOP difícil · 13 FIND · 17 ¿CUÁL LOOK? · 21 CATCH o STOP medio (alternando)."""
    out = []
    for d in range(dias):
        dia = inicio + timedelta(days=d)
        for slot in ("stopA", "find", "look", "noche"):
            tipo = {"stopA": "stop", "find": "find", "look": "look", "noche": "cabeza" if d % 2 == 0 else "stop"}[slot]
            out.append(dict(fecha=dia.isoformat(), hora=HORAS[slot], tipo=tipo, dificil=slot == "stopA"))
    return out


def fabricar(slots, sem, rng, prefijo="s1", procesos=3, renderizar=True):
    """Genera, renderiza y deja en `sem` un video por slot (dict fecha, hora, tipo, dificil) + su .txt + videos.json."""
    (sem / "guiones").mkdir(parents=True, exist_ok=True)
    from variedad import Variedad
    V = Variedad.cargar()                                                     # memoria permanente: nada se repite entre semanas
    usados = V.grupos.setdefault("stop_find", set())
    usados_look, usados_cab, trabajos, filas, manifiesto = set(), set(), [], [], []
    pub_p = ROOT.parent / "pipeline" / "datos" / "publicados.json"                  # títulos ya usados en el canal (regla: nunca parecidos)
    previos_titulos = [x["titulo"] for x in (json.loads(pub_p.read_text()) if pub_p.exists() else []) if x.get("video_id")][-150:]
    voces_pendientes = []
    for n, sl in enumerate(slots, 1):
        dia = date.fromisoformat(sl["fecha"]); tipo = sl["tipo"]; hora = sl["hora"]
        et = f"{DIAS[dia.weekday()]}{dia.day:02d}"
        gid = f"{prefijo}_{n:02d}_{et}_{hora.replace(':', '')}_{tipo}"
        if tipo == "dress":
            g = guion_dress(gid, rng, V, sl["fecha"])
            ns = g["nombres"]
            titulo = V.titulo("dress", TIT_DRESS, rng).format(a=ns[0], b=ns[1])
            desc = ("Pause when the accessory fits 😂 How many did you get? 1, 2, 3 or 4 👇\n" + " ".join(tag(n) for n in ns)
                    + " #football #soccer #challenge #pausechallenge #shorts")
            fijado = "Be honest… how many did you stop on time? 😂"
            fotos = [FOTOS[c] for c in g["jugadores"]]; nombres = ns
        elif tipo == "torre":
            g = guion_torre(gid, rng, V, sl["fecha"])
            ns = g["nombres"]
            titulo = V.titulo("torre", TIT_TORRE, rng).format(a=ns[0], b=ns[1], c=ns[2])
            desc = ("Watch the balls build the flag 🏳️ Comment your guess BEFORE the colors show 👇\n" + " ".join(tag(n) for n in ns)
                    + " #football #soccer #satisfying #quiz #shorts")
            fijado = "Did you get it before the colors changed? 👀"
            fotos = [FOTOS[c] for c in g["opciones"]]; nombres = ns
        elif tipo in ("plinko", "hoyo"):
            g = (guion_plinko if tipo == "plinko" else guion_hoyo)(gid, rng, V, sl["fecha"])
            ns = g["nombres"]
            titulo = V.titulo(tipo, TIT_PLINKO if tipo == "plinko" else TIT_HOYO, rng).format(a=ns[0], b=ns[1], c=ns[2], d=ns[3])
            if tipo == "plinko":
                desc = "4 balls, 1 card. Only one lands on 99 🎯 Comment your pick BEFORE the end 👇"
                fijado = "Who did you pick? 👀 Be honest 😂"
            else:
                desc = "4 balls, 1 hole. Only one goes in 🕳️ Comment your pick BEFORE they roll 👇"
                fijado = f"I was sure {ns[(g['ganador'] + 1) % 4]} had it 😭 who did you pick?"
            desc += "\n" + " ".join(tag(n) for n in ns) + f" #football #soccer #{'plinko' if tipo == 'plinko' else 'challenge'} #goat #shorts"
            fotos = [FOTOS[c] for c in g["jugadores"]]; nombres = ns
        elif tipo == "rueda":
            g = guion_rueda(gid, rng, V, sl["fecha"])
            otros_ = [nombre_de(t.rsplit("_", 1)[0]) for t in g["torsos"]]               # cualquiera de la rueda (varía el título)
            est_ = [o for o in g["otros"]] + [o for o in otros_ if o not in g["otros"]]
            a, b = rng.sample(est_[:4], 2) if len(est_) >= 2 else (est_ + ["Ronaldo", "Mbappé"])[:2]
            titulo = V.titulo("rueda", TIT_RUEDA, rng).format(n=g["nombre"], a=a, b=b) + " " + " ".join(tag(x) for x in (g["nombre"], a, b))
            desc = (f"Stop the wheel when {g['nombre']}'s body is PERFECT 🛑 Only 1% get it first try. Comment your number 👇\n"
                    + " ".join(tag(x) for x in (g["nombre"], a, b)) + " #football #soccer #stopchallenge #shorts")
            fijado = ""; fotos = []; nombres = [g["nombre"], a, b]
        elif tipo in ("trayectoria", "tridente"):
            g = (guion_trayectoria if tipo == "trayectoria" else guion_tridente)(gid, rng, V, sl["fecha"])
            titulo = V.titulo(tipo, TIT_TRAYECTORIA if tipo == "trayectoria" else TIT_TRIDENTE, rng)
            ns = [g["nombre"]] if tipo == "trayectoria" else [r[0][1] for r in g["rodillos"]]
            titulo += " " + " ".join(tag(x) for x in (["football", "quiz"] if tipo == "trayectoria" else ns))
            meta = ("Guess the player from his career BEFORE the 3 seconds are up ⏱️" if tipo == "trayectoria"
                    else "Pause to build your attacking trident. Stay under €150M or go bankrupt 💸")
            desc = f"{meta}\nComment your answer 👇 Follow for part 2 🔥\n#football #soccer #challenge #shorts"
            fijado = ""; fotos = []; nombres = ns
        elif tipo in ("cabezas", "pared", "circulo"):
            g = {"cabezas": guion_cabezas, "pared": guion_pared, "circulo": guion_circulo}[tipo](gid, rng, V, sl["fecha"])
            ns = [g["nombre"]] if tipo == "cabezas" else g["nombres"]
            ns4 = (ns + ["Messi", "Ronaldo", "Mbappé", "Yamal"])[:4]
            plant = {"cabezas": TIT_CABEZAS, "pared": TIT_PARED, "circulo": TIT_CIRCULO}[tipo]
            titulo = V.titulo(tipo, plant, rng).format(n=ns[0], a=ns4[0], b=ns4[1], c=ns4[2], d=ns4[3])
            for x in ns4[:3]:
                if len(titulo) + len(tag(x)) + 1 <= 100:
                    titulo += " " + tag(x)
            meta = {"cabezas": f"Pause when {ns[0]}'s head fits PERFECTLY 🛑", "pared": "Pick who won't fall BEFORE the countdown ends 👀",
                    "circulo": "Pause when the ball touches YOUR GOAT 🐐"}[tipo]
            desc = f"{meta}\nComment your pick 👇 Follow for part 2 🔥\n" + " ".join(tag(x) for x in ns4) + " #football #soccer #challenge #shorts"
            fijado = ""; fotos = []; nombres = ns4
        elif tipo in ("q20fichaje", "q20costo", "q20balon"):                     # formatos de 20 s con voz (anti-repetición propia)
            import q20_guiones as Q20
            g, titulo, fijado, nombres = Q20.TIPOS[tipo](gid, rng, V)
            titulo += " " + " ".join(tag(x) for x in nombres[:2])
            desc = (f"{g['voz_lineas'][0]}\nComment your answer 👇 Follow for part 2 🔥\n"
                    + " ".join(tag(x) for x in nombres[:4]) + " #football #soccer #quiz #shorts")
            fotos = []
            voces_pendientes += g["voz_lineas"]
        elif tipo == "fitall":
            g = guion_fitall(gid, rng, V, sl["fecha"])
            n = g["nombre"]
            titulo = V.titulo("fitall", TIT_FITALL, rng).format(n=n)
            for x in (tag(n), "#fitchallenge"):
                if len(titulo) + len(x) + 1 <= 100:
                    titulo += " " + x
            desc = (f"8 heads of {n}… only ONE is real 🎯 Pause when the REAL head fits!\nComment your number 👇 Follow for part 2 🔥\n"
                    f"{tag(n)} #fitchallenge #football #soccer #challenge #shorts")
            fijado = ""; fotos = []; nombres = [n]
        elif tipo in ("siuu", "penal", "balon"):
            g = {"siuu": guion_siuu, "penal": guion_penal, "balon": guion_balon}[tipo](gid, rng, V, sl["fecha"])
            n = g.get("nombre", "Ronaldo")
            plant = {"siuu": TIT_SIUU, "penal": TIT_PENAL, "balon": TIT_BALON}[tipo]
            titulo = V.titulo(tipo, plant, rng).format(n=n)
            etiquetas_ = {"siuu": "#ronaldo #cr7 #siuu", "penal": f"{tag(n)} #penalty", "balon": f"{tag(n)} #ballondor"}[tipo]
            if len(titulo) + len(etiquetas_) + 1 <= 100:
                titulo += " " + etiquetas_
            meta = {"siuu": "Pause it EXACTLY at 67 🛑 (Ronaldo at the top = SIUUU)", "penal": "Pause when the target is in the top corner (100%) ⚽",
                    "balon": f"Pause when the Ballon d'Or fits in {n}'s hands (100%) 🏆"}[tipo]
            desc = f"{meta}\nComment your number 👇 Follow for part 2 🔥\n{etiquetas_} #football #soccer #stopchallenge #shorts"
            fijado = ""; fotos = [FOTOS[g["pateador"]]] if tipo == "penal" and g.get("pateador") in FOTOS else []; nombres = [n]
        elif tipo == "find":
            g = guion_find(gid, rng, usados, V)
            titulo = "FIND " + " ".join(r["nombre"].upper() for r in g["rondas"])
            desc = "Find the REAL one in every round 🔎 Round 3 is only for the 1%\nComment the numbers 👇\n" + " ".join(tag(r["nombre"]) for r in g["rondas"])
            fijado = "Answers in the video 👀 Which round did you get wrong? 1, 2 or 3?"
            fotos = [r["foto"] for r in g["rondas"]]; nombres = [r["nombre"] for r in g["rondas"]]
        elif tipo == "cabeza":
            g = guion_cabeza(gid, rng, usados_cab, V)
            titulo = V.titulo("cabeza", TIT_CABEZA, rng).format(n=g["nombre"])
            desc = f"Only one head fits {g['nombre']} 🤯 Did you guess it before the end? 1, 2 or 3 👇\n{tag(g['nombre'])} #football #shorts"
            fijado = "Be honest… did you get it before it landed? 👀"
            fotos = g["opciones"]; nombres = [g["nombre"]]
        elif tipo == "look":
            g = guion_look(gid, rng, usados_look, V)
            titulo = V.titulo("look", TIT_LOOK, rng).format(n=g["nombre"])
            desc = f"Which one fits {g['nombre']} best? Comment 1, 2, 3 or 4 👇\n{tag(g['nombre'])} #football #shorts"
            fijado = f"I'm going with number {rng.randint(1, 4)} 😂 what about you?"
            fotos = [g["foto"]]; nombres = [g["nombre"]]
        else:
            g = guion_stop(gid, rng, usados, dificil=sl.get("dificil", True), V=V, fecha=sl["fecha"], hard_pedido=sl.get("hard", False))
            if sl.get("arranque"):
                g["arranque"] = sl["arranque"]
            titulo = titulo_stop(V, rng, [q["nombre"] for q in g["cuadrantes"]], g["nivel"])
            desc = (f"Level {g['nivel']} 🛑 It only fits ONCE per loop. Pause at 100%!\nWhich one did you stop? Comment 1, 2, 3 or 4 👇\n"
                    f"Follow for Level {g['nivel'] + 1} 🔥\n" + " ".join(tag(q["nombre"]) for q in g["cuadrantes"]) + " #stopchallenge #football #shorts")
            q0 = g["cuadrantes"][0]
            fijado = f"{q0['nombre']} {q0['pct']} only fits ONE time... did you get it? 😤"
            fotos = [q["foto"] for q in g["cuadrantes"]]; nombres = [q["nombre"] for q in g["cuadrantes"]]
        import gancho as G
        fijado = G.FIJADO.get(tipo, fijado)                                    # comentario fijado que invita a responder (guía YouTube)
        ruta = sem / "guiones" / f"{gid}.json"
        ruta.write_text(json.dumps(g, ensure_ascii=False, indent=1))
        desc_completa = (f"{desc}\n\nPhoto credits (Wikimedia Commons). Images were modified; the modified images are shared under CC BY-SA 4.0:\n"
                         f"{creditos(fotos)}")
        (sem / f"{gid}.txt").write_text(
            f"=== PROGRAMAR ===\n{dia.isoformat()} a las {hora} (hora de Argentina)\n\n=== TÍTULO ===\n{titulo}\n\n=== DESCRIPCIÓN ===\n{desc_completa}\n\n"
            f"=== COMENTARIO PARA FIJAR ===\n{fijado}\n\n=== AL SUBIR ===\n- Idioma del video: Inglés. Solo hashtags en inglés.\n")
        titulo = titulo_unico(titulo, previos_titulos, rng, [x for x in nombres if isinstance(x, str)][:4], tipo=tipo)
        previos_titulos.append(titulo)
        manifiesto.append(dict(id=gid, n=n, fecha=dia.isoformat(), hora=hora, tipo=tipo, formato=FORMATO[tipo], titulo=titulo,
                               descripcion=desc_completa, fijado=fijado, jugadores=nombres,
                               tags=["football", "soccer", "shorts"] + [x.lower() for x in nombres], archivo=f"{gid}.mp4",
                               **({"variante": g["arranque"]} if g.get("arranque") else {})))
        trabajos.append((tipo, ruta))
        filas.append(f"| {n} | {dia.isoformat()} ({DIAS[dia.weekday()]}) | {hora} | {FORMATO[tipo]} | {titulo} | `{gid}` |")
    if not renderizar:                                                          # prueba de humo: solo guiones y títulos (sin video ni memoria)
        return manifiesto, []
    if voces_pendientes:                                                        # locución de los formatos de 20 s (edge-tts)
        try:
            import voz_edge
            voz_edge.generar(voces_pendientes)
        except Exception as e:
            print("no pude generar las voces:", e, flush=True)
    errores = []
    with ProcessPoolExecutor(procesos) as ex:
        for ruta, rc, err in ex.map(render, trabajos):
            print("ok" if rc == 0 else "ERROR", ruta.stem, "" if rc == 0 else err, flush=True)
            if rc:
                errores.append(dict(id=ruta.stem, error=err))
    for (tipo, ruta), m in zip(trabajos, manifiesto):                        # mover los videos a la carpeta de la semana
        sal = ROOT / "salida" / ruta.stem
        for f, suf in (("short.mp4", ""), ("short_solo_efectos.mp4", "_solo_efectos"), ("short_sin_musica.mp4", "_solo_efectos")):
            if (sal / f).exists():
                (sal / f).replace(sem / f"{ruta.stem}{suf}.mp4")
        if tipo == "plinko" and (sal / "resultado.json").exists():             # el ganador del PLINKO lo decide la física
            gk = json.loads((sal / "resultado.json").read_text())["ganador"]
            V.anotar_ganador(next(n for n, c, _ in JUGADORES if c == gk))
        if tipo == "find" and (sal / "resultado.json").exists():               # soluciones del FIND
            res = json.loads((sal / "resultado.json").read_text())
            m["soluciones"] = " · ".join(f'{x["nombre"].title()} #{x["real"]}' for x in res["rondas"])
            with open(sem / f"{ruta.stem}.txt", "a") as fh:
                fh.write(f"\n=== SOLUCIONES (para vos) ===\n{m['soluciones']}\n")
        import shutil
        shutil.rmtree(sal, ignore_errors=True)
        try:                                                                   # huella para el auditor de originalidad (sin IA)
            sys.path.insert(0, str(ROOT.parent / "pipeline"))
            import originalidad
            gj = json.loads(ruta.read_text()) if ruta.exists() else {}
            originalidad.registrar(m["id"], sem / m["archivo"], tipo, m["fecha"], gj.get("musica"))
        except Exception as e:
            print("huella no registrada:", m["id"], e, flush=True)
        m["listo"] = (sem / m["archivo"]).exists()
    V.guardar()
    (sem / "videos.json").write_text(json.dumps(manifiesto, ensure_ascii=False, indent=1))
    (sem / "CALENDARIO.md").write_text("# Calendario de la semana\n\n| # | Día | Hora (ARG) | Formato | Título | Archivo |\n|---|---|---|---|---|---|\n" + "\n".join(filas) + "\n")
    return manifiesto, errores


def main():
    inicio = date.fromisoformat(sys.argv[1]); dias = int(sys.argv[2]); rng = random.Random(int(sys.argv[3]) if len(sys.argv) > 3 else 67)
    sem = ROOT / f"semana_{inicio.isoformat()}"
    fabricar(slots_por_defecto(inicio, dias), sem, rng)
    print(sem)


if __name__ == "__main__":
    main()
