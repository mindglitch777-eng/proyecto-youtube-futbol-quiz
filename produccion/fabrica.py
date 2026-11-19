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
import math
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
           "hoyo": "BALL TO THE HOLE", "dress": "DRESS UP", "torre": "BALL TOWER", "rueda": "WHEEL STOP", "piernas": "LEGS WHEEL", "favorito": "STOP ON YOUR FAVORITE", "escape": "STOP TO ESCAPE", "goles": "GOALS BY AGE", "cinta": "CONVEYOR STOP", "vs": "VS STOP", "cano": "SKILL STOP", "slot": "HEAD SLOT", "siuu": "SIUUU 67",
           "penal": "PENALTY 100", "balon": "BALLON D'OR 100%", "cabezas": "HEAD FIT", "fitall": "FIT ALL", "pared": "WALL BALANCE",
           "circulo": "GOAT CIRCLE", "trayectoria": "GUESS BY CAREER", "tridente": "TRIDENT €150M",
           "q20fichaje": "HIDDEN TRANSFER", "q20costo": "WHO COST MORE", "q20balon": "BALLON D'OR PICKS"}
SCRIPT = {"stop": "render_stop.py", "find": "render_find_v2.py", "look": "render_look.py", "cabeza": "render_cabeza.py",
          "plinko": "render_plinko.py", "rueda": "render_rueda.py", "piernas": "render_piernas.py", "favorito": "render_favorito.py", "escape": "render_escape.py", "goles": "render_goles.py", "cinta": "render_cinta.py", "vs": "render_vs.py", "cano": "render_cano.py", "slot": "render_slot.py", "siuu": "render_siuu.py",
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


NOMBRE = {"ronaldo_nazario": "R9", "kak": "Kaká", "ousmane_demb_l": "Dembélé", "son_heung_min": "Son", "arda_g_ler": "Güler", "vin_cius_j_nior": "Vinícius",
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
# REGLA DEL CEO (15/11): en TODOS los videos solo jugadores MUY famosos: las 6 superestrellas de hoy + 5 leyendas. Nunca secundarios
# (con secundarios rendíamos 3 veces menos). Fotos de leyendas revisadas a ojo el 15/11 (afuera: Beckham sin camiseta, Henry con
# aro y texto, Zidane de traje con la copa; Kaká y Ronaldo Nazário tienen fotos de otra persona).
LEYENDAS = ["ronaldinho", "zinedine_zidane", "david_beckham", "thierry_henry", "zlatan_ibrahimovi"]
FAMOSOS = SUPERESTRELLAS + LEYENDAS
TORSOS_LEYENDA = ["david_beckham_0", "david_beckham_2", "david_beckham_3", "ronaldinho_0", "ronaldinho_1", "ronaldinho_2", "ronaldinho_3",
                  "thierry_henry_0", "thierry_henry_1", "thierry_henry_3", "zinedine_zidane_0", "zinedine_zidane_3",
                  "zlatan_ibrahimovi_0", "zlatan_ibrahimovi_1", "zlatan_ibrahimovi_2", "zlatan_ibrahimovi_3"]
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
    est = estrellas_nombres()                                                  # 13/11: solo superestrellas en el título
    ns = sorted(ns, key=lambda n: n not in est)                                # (con "Cole/Gavi/Pedri" rendía 1.841 vs 5.714)
    n_est = sum(1 for n in ns if n in est)
    while len(ns) < 3:
        ns.append(rng.choice(["Messi", "Ronaldo", "Mbappé", "Yamal", "Neymar"]))
    pool = VARIANTES.get(tipo, [])
    if n_est < 2:                                                              # una sola estrella en el video: variantes con un nombre
        pool = [x for x in pool if "{b}" not in x and "{c}" not in x] or pool
    elif n_est < 3:
        pool = [x for x in pool if "{c}" not in x] or pool
    mejor = (2.0, base)                                                        # si nada queda bajo el umbral: la MENOS parecida (nunca la repetida)
    for _ in range(200):
        if not pool:
            break
        resto = [n for n in ns[1:] if n in est] if n_est >= 3 else ns[1:]
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
    nombres = sorted(nombres, key=lambda n: n not in estrellas_nombres())       # 13/11: superestrellas primero (título y hashtags)
    base = (V.titulo("stop_formula", TIT_STOP_FORMULA, rng) if V else rng.choice(TIT_STOP_FORMULA)).format(a=nombres[0], b=nombres[1])
    if nivel and False:                                                        # el nivel queda en pantalla, no en el título
        base += f" · Level {nivel}"
    for n in nombres[:3]:                                                      # hashtags de jugadores (los del top los tenían)
        if len(base) + len(tag(n)) + 1 <= 100:
            base += " " + tag(n)
    return base


def _cuatro_hashtags(desc):
    """Deja como máximo 3 hashtags de jugadores/tema + #shorts (la IA de YouTube: saturar de etiquetas no suma)."""
    tags = _re.findall(r"#\w+", desc)
    quedan = [t for t in tags if t.lower() not in ("#shorts",)][:3] + ["#shorts"]
    limpio = _re.sub(r"[ \t]*#\w+", "", desc).rstrip()
    return limpio + "\n" + " ".join(dict.fromkeys(quedan))


def estrellas_nombres():
    """Nombres de las superestrellas (los que se reconocen en 0,4 s). Solo estos van en los títulos."""
    return {nombre_de(c) for c in SUPERESTRELLAS} | {"Messi", "Ronaldo", "Cristiano Ronaldo", "Mbappé", "Yamal", "Lamine Yamal",
                                                     "Neymar", "Vinícius", "Vinícius Jr."}


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
TIT_RUEDA = ["{n} vs {a} or {b} stop challenge 🔥🛑", "{n} vs {a} or {b} stop challenge 😱🔥",
             "Find {n}'s real body 🛑🔥 {a} or {b}?",                                 # 15.641: también funciona
             # 19/11 (originalidad: títulos 66 % parecidos): estructuras nuevas, siempre con la superestrella al inicio
             "{n}'s body is hiding here 🛑 {a} or {b}?", "{n}, {a} or {b}? Only one body fits 😱",
             "{n} body swap with {a} and {b} 🤯 Stop it right"]


def guion_rueda(gid, rng, V, fecha):
    usados = V.grupos.setdefault("rueda", set())
    ult = V.contadores.setdefault("rueda_ult", [])                            # rota el dueño del cuerpo (antes: Mbappé 6 de 8)
    cuerpo = min(sorted(CUERPOS_RUEDA), key=lambda c: (c == (ult[-1] if ult else None), ult[-6:].count(c), rng.random()))
    ult.append(cuerpo); del ult[:-12]
    for _ in range(300):
        base = cuerpo.rsplit("_", 1)[0]
        pool = [t for t in TORSOS_RUEDA if t.rsplit("_", 1)[0] != base]
        estrellas = [t for t in pool if t.rsplit("_", 1)[0] in SUPERESTRELLAS]
        ley = [t for t in TORSOS_LEYENDA if t.rsplit("_", 1)[0] != base]
        ley = rng.sample(ley, len(ley))
        ley = [t for i, t in enumerate(ley) if t.rsplit("_", 1)[0] not in {x.rsplit("_", 1)[0] for x in ley[:i]}][:4]   # 4 leyendas distintas
        claves = rng.sample(sorted({t.rsplit("_", 1)[0] for t in estrellas}), 3)   # 17/11: 3 estrellas DISTINTAS (antes 2 fotos del mismo: "Vinícius or Vinícius")
        torsos = [rng.choice([t for t in estrellas if t.rsplit("_", 1)[0] == k]) for k in claves] + ley   # 15/11 CEO: solo famosos (3 estrellas + 4 leyendas)
        rng.shuffle(torsos)
        clave = (cuerpo,) + tuple(sorted(torsos))
        if clave not in usados:
            usados.add(clave); break
    nombre = CUERPOS_RUEDA[cuerpo]
    otros = [nombre_de(t.rsplit("_", 1)[0]) for t in torsos if t.rsplit("_", 1)[0] in SUPERESTRELLAS]
    return dict(id=gid, cuerpo=cuerpo, nombre=nombre, torsos=torsos, dur=6.6, vueltas=4, t_encaje=0.45, sentido=rng.choice([1, -1]),
                musica=f"rueda_original_{rng.randint(0, 2)}", fondo="estadio_0", pos_correcto=rng.randint(2, 6), otros=otros)


# LEGS WHEEL (13/11): WHEEL al revés. Torso de superestrella fijo arriba (cara en el cuadro 0) y rueda de piernas abajo.
TIT_PIERNAS = ["Find {n}'s real legs 🦵🛑 {a} or {b}?", "{n} vs {a} or {b} legs challenge 🦵🔥", "Give {n} his legs back 🦵🛑 Only 1% can",
               "Stop on {n}'s REAL legs 🦵😱 {a} or {b}?"]


def guion_piernas(gid, rng, V, fecha):
    usados = V.grupos.setdefault("piernas", set())
    ult = V.contadores.setdefault("piernas_ult", [])
    cuerpo = min(sorted(CUERPOS_RUEDA), key=lambda c: (c == (ult[-1] if ult else None), ult[-6:].count(c), rng.random()))
    ult.append(cuerpo); del ult[:-12]
    base = cuerpo.rsplit("_", 1)[0]
    pool = sorted(p.stem for p in (ROOT / "assets" / "recortes" / "cuerpos").glob("*.png") if not p.stem.startswith(base))
    nombre = CUERPOS_RUEDA[cuerpo]
    est = {c.rsplit("_", 1)[0]: n for c, n in CUERPOS_RUEDA.items() if c != cuerpo and not c.startswith(base)}
    for _ in range(100):                                                       # 2 de las piernas son de otras superestrellas (las del título)
        dos = rng.sample(sorted(est), 2)
        de_est = [rng.choice([x for x in pool if x.startswith(k)]) for k in dos]
        piernas = de_est + rng.sample([x for x in pool if x.startswith(tuple(LEYENDAS))], 3)   # 15/11 CEO: solo famosos (leyendas)
        rng.shuffle(piernas)
        clave = (cuerpo,) + tuple(sorted(piernas))
        if clave not in usados:
            usados.add(clave); break
    return dict(id=gid, cuerpo=cuerpo, nombre=nombre, piernas=piernas, dur=6.6, vueltas=3, t_encaje=0.45, sentido=rng.choice([1, -1]),
                musica=f"rueda_original_{rng.randint(0, 2)}", fondo="estadio_0", pos_correcto=rng.randint(1, 5), otros=[est[k] for k in dos])


# CONVEYOR STOP y HEAD SLOT (13/11): variantes de WHEEL y HEAD FIT con otro objeto que se mueve y otra recompensa.
# SOLO superestrellas en la cinta / el rodillo (lección del 13/11: los secundarios rinden 3 veces menos). La variedad sale de
# qué estrella es el dueño, el orden y el gancho, no de nombres nuevos.
TORSOS_ESTRELLA = {"cristiano_ronaldo": ["cristiano_ronaldo_0"], "lionel_messi": ["lionel_messi_0"], "kylian_mbapp": ["kylian_mbapp_0"],
                   "lamine_yamal": ["lamine_yamal_0"], "neymar": ["neymar_2"], "vin_cius_j_nior": ["vin_cius_j_nior_0", "vin_cius_j_nior_3"]}
TIT_CINTA = ["{n} vs {a} or {b} stop challenge 🛑🔥", "{n} vs {a} or {b} conveyor challenge 😱🛑", "Stop {n}'s body on the belt 🛑 {a} or {b}?",
             "Find {n}'s real body 🛑🔥 {a} or {b}?",
             "{n}'s body is on the belt 🛑 {a} or {b}?", "{n} on the conveyor 😱 Only one body fits: {a} or {b}?"]   # 19/11: más estructuras
TIT_SLOT = ["{n} vs {a} or {b} head slot 🎰🛑", "Hit the {n} JACKPOT 🎰 {a} or {b}?", "Fit {n}'s head 🎰 Only 1% hit the jackpot",
            "{n} head fit slot machine 😱🎰 {a} or {b}?"]


def _dueno(V, clave_ult, opciones, rng):
    ult = V.contadores.setdefault(clave_ult, [])
    c = min(sorted(opciones), key=lambda c: (c == (ult[-1] if ult else None), ult[-6:].count(c), rng.random()))
    ult.append(c); del ult[:-12]
    return c


def _dueno_jugador(V, clave_ult, opciones, rng):
    """18/11: rota por JUGADOR (no por foto) y la memoria la comparten HEAD FIT y HEAD SLOT: antes Mbappé (2 cuerpos de 6) salía
    en los dos el mismo día ("Fit Mbappé's head" 19/11 y 2 veces el 20/11)."""
    ult = V.contadores.setdefault(clave_ult, [])
    c = min(sorted(opciones), key=lambda c: (opciones[c] in ult[-2:], ult[-6:].count(opciones[c]), rng.random()))
    ult.append(opciones[c]); del ult[:-12]
    return c


def guion_cinta(gid, rng, V, fecha):
    usados = V.grupos.setdefault("cinta", set())
    cuerpo = _dueno(V, "cinta_ult", CUERPOS_RUEDA, rng)
    base = cuerpo.rsplit("_", 1)[0]
    for _ in range(100):
        torsos = [rng.choice(v) for k, v in sorted(TORSOS_ESTRELLA.items()) if k != base]
        rng.shuffle(torsos)
        k = rng.randint(1, 5)
        clave = (cuerpo, str(k)) + tuple(torsos)
        if clave not in usados:
            usados.add(clave); break
    otros = [nombre_de(t.rsplit("_", 1)[0]) for t in torsos]
    return dict(id=gid, cuerpo=cuerpo, nombre=CUERPOS_RUEDA[cuerpo], torsos=torsos, dur=6.6, vueltas=2, t_encaje=0.45,
                sentido=rng.choice([1, -1]), musica=f"rueda_original_{rng.randint(0, 2)}", fondo="estadio_0", pos_correcto=k, otros=otros)


def guion_slot(gid, rng, V, fecha):
    usados = V.grupos.setdefault("slot", set())
    cuerpo = _dueno_jugador(V, "fit_ult", CUERPOS_FIT, rng); clave = CUERPOS_FIT[cuerpo]
    est = [c for c in SUPERESTRELLAS if c != clave and c in FOTOS]
    for _ in range(100):
        cab = list(est); rng.shuffle(cab)
        k = rng.randint(1, 5)
        cl = (cuerpo, str(k)) + tuple(cab)
        if cl not in usados:
            usados.add(cl); break
    return dict(id=gid, cuerpo=cuerpo, clave=clave, nombre=nombre_de(clave), cabezas=cab, dur=6.4, vueltas=2, t_encaje=0.45,
                musica=f"rueda_original_{rng.randint(0, 2)}", fondo=fondo_variado(V, "slot", rng), pos_correcto=k, otros=[nombre_de(c) for c in cab])


# STOP ON YOUR FAVORITE (15/11, aprobado por el CEO): 6 cartas de superestrellas, la pelota salta y hay que pausar en tu favorito.
TIT_FAVORITO = ["Stop the ball on your favorite player ⚽🛑 {a}, {b} or {c}?", "Can you stop on your GOAT? 🐐⚽ {a} or {b}?",
                "Who's your favorite? Stop the ball! ⚽🛑 {a}, {b}, {c}", "Pause on your idol ⚽😱 {a} or {b}?"]


def guion_favorito(gid, rng, V, fecha, leyendas=True):
    """15/11 (CEO): 3 estrellas de hoy + 3 leyendas, caras grandes. La del cuadro 0 (donde arranca la pelota) es una estrella de hoy."""
    hoy = ["lionel_messi", "cristiano_ronaldo", "kylian_mbapp", "lamine_yamal", "neymar", "vin_cius_j_nior"]
    leyendas_ = ["ronaldinho", "zinedine_zidane", "david_beckham", "thierry_henry", "zlatan_ibrahimovi"]   # Kaká: foto equivocada, afuera
    ult = V.contadores.setdefault("favorito_ult", [])
    primero = min(hoy, key=lambda c: (ult[-5:].count(c), rng.random()))                  # rota la estrella del cuadro 0
    ult.append(primero); del ult[:-12]
    otros = (rng.sample([c for c in hoy if c != primero], 2) + rng.sample(leyendas_, 3) if leyendas
             else [c for c in hoy if c != primero])                                        # C2: prueba A/B con o sin leyendas
    rng.shuffle(otros)
    jug = [primero] + otros
    sal = [0]
    while len(sal) < 26:
        c = rng.randrange(6)
        if c != sal[-1] and (len(sal) < 25 or c != 0):
            sal.append(c)
    import render_favorito as RF
    nombres = [RF.NOMBRE[c].title().replace("Mbappé", "Mbappé") for c in jug]
    return dict(id=gid, jugadores=jug, saltos=sal, dur=7.0, musica=f"rueda_original_{rng.randint(0, 2)}", fondo="estadio_0",
                nombres=nombres)


# VS STOP (16/11): dos superestrellas cara a cara y un medidor de duelo; pausás con la pelota en la zona dorada de tu estrella.
# Duelos que pide el público (Studio 15/11): Ronaldo vs Messi, Yamal vs Mbappé / Vinícius. Solo superestrellas.
DUELOS = [("cristiano_ronaldo_14", "lionel_messi_3"), ("lamine_yamal_10", "kylian_mbapp_12"), ("lamine_yamal_10", "vin_cius_j_nior_14"),
          ("cristiano_ronaldo_14", "kylian_mbapp_12"), ("lionel_messi_3", "lamine_yamal_10"), ("neymar_1", "vin_cius_j_nior_14"),
          ("lionel_messi_3", "kylian_mbapp_12"), ("cristiano_ronaldo_14", "neymar_1")]
COLOR_VS = {"cristiano_ronaldo": (220, 30, 40), "lionel_messi": (80, 165, 235), "lamine_yamal": (205, 25, 45), "kylian_mbapp": (40, 70, 190),
            "vin_cius_j_nior": (40, 170, 70), "neymar": (250, 210, 0)}
TIT_VS = ["{a} vs {b} 🛑 Stop on your GOAT", "{a} or {b}? 👑 Pause it in the gold zone", "{a} vs {b} stop challenge 👑🔥",
          "Who wins? {a} vs {b} 🛑 Only 1% stop it"]


# 19/11 (originalidad 57; BALLON D'OR/PENALTY/HEAD SLOT con huellas a distancia 0-6): fondo al azar entre los estadios SIN marca
# de agua (0, 1, 5, 6), con espejo y tono de color. La huella (dHash en grises) cambia sobre todo con el fondo y el espejo.
# 19/11 Gerente: estadio_1 y estadio_5 (Freepik premium) TIENEN marca de agua "Magnific" repetida en el cielo: fuera. Solo los revisados a ojo.
FONDOS_LIMPIOS = ["estadio_0", "estadio_6"]


def fondo_variado(V, tipo, rng):
    ult = V.contadores.setdefault(f"{tipo}_fondo", [])
    opciones = [f + e + c for f in FONDOS_LIMPIOS for e in ("", "~espejo") for c in ("", "~calido", "~frio")]
    usados = {x.split("~")[0] + ("~espejo" if "espejo" in x else "") for x in ult[-4:]}
    cand = [o for o in opciones if o.split("~")[0] + ("~espejo" if "espejo" in o else "") not in usados] or opciones
    f = rng.choice(cand); ult.append(f); del ult[:-12]
    return f


# SKILL STOP · NUTMEG (19/11, pedido del CEO): defensor superestrella con las piernas abiertas (recortes con hueco medido) y
# la cara del atacante (estrella o leyenda); pausar con la pelota entre los pies. Solo famosos.
DEFENSORES_CANO = {"kylian_mbapp_13": "kylian_mbapp", "lamine_yamal_3": "lamine_yamal"}   # 19/11 (CEO aprobó #15): solo piernas MUY abiertas = pelota grande
# (fuera: Messi_3 manos en la cintura, Vinícius_10 piernas juntas, Neymar_1 cara tapada por el aro, Zlatan_1 trae su propia pelota)
TIT_CANO = ["{a} vs {b} skills 🛑 Stop the nutmeg", "Can {a} nutmeg {b}? 🛑 Only 1% stop it", "{a} nutmegs {b}? 😱 Pause it between the legs",
            "{a} skills vs {b} 🛑 Stop it between the legs"]


def guion_cano(gid, rng, V, fecha):
    ult = V.contadores.setdefault("cano_ult", [])
    defe = min(sorted(DEFENSORES_CANO), key=lambda c: (ult[-6:].count(c), rng.random()))
    ult.append(defe); del ult[:-12]
    clave_def = DEFENSORES_CANO[defe]
    ult_a = V.contadores.setdefault("cano_atq", [])                           # el atacante también rota (no 3 veces el mismo)
    pool = [c for c in SUPERESTRELLAS if c != clave_def and c in FOTOS] * 2 + [c for c in LEYENDAS if c in FOTOS]
    atq = rng.choice([c for c in pool if c not in ult_a[-3:]] or pool)
    ult_a.append(atq); del ult_a[:-12]
    a, b = nombre_de(atq), nombre_de(clave_def)
    tx = dict(gancho=rng.choice([f"NUTMEG {b.upper()}", "STOP THE NUTMEG", f"{a.upper()} VS {b.upper()}"]),
              apuesta=rng.choice(["ONLY 1% STOP IT", "BETWEEN THE LEGS = WIN", "IMPOSSIBLE SPEED"]),
              cta="HOW MANY TRIES? COMMENT NOW")
    return dict(id=gid, defensor=defe, nombre_def=b, atacante=atq, nombre_atq=a, dur=7.5, pasadas=4, lento=4.0,
                t0=round(rng.uniform(0.0, 0.4), 2), musica=f"rueda_original_{rng.randint(0, 2)}", fondo=fondo_variado(V, "cano", rng), textos=tx)


def guion_vs(gid, rng, V, fecha):
    ult = V.contadores.setdefault("vs_ult", [])
    duelo = min(DUELOS, key=lambda d: (ult[-6:].count("|".join(d)), DUELOS.index(d) > 2, rng.random()))   # primero los 3 más pedidos
    ult.append("|".join(duelo)); del ult[:-12]
    duelo = list(duelo)
    if rng.random() < 0.5:
        duelo.reverse()
    nombres = [CUERPOS_RUEDA[c] for c in duelo]
    cols = [COLOR_VS[c.rsplit("_", 1)[0]] for c in duelo]
    a, b = [n.upper() for n in nombres]
    tx = dict(gancho=rng.choice([f"{a} OR {b}?", "STOP ON YOUR GOAT", f"{a} VS {b}"]),
              apuesta=rng.choice(["IMPOSSIBLE SPEED", "TINY GOLD ZONE · 1% CAN", "ONLY 1% STOP IT IN TIME"]),
              cta="HOW MANY TRIES? WHO WON?")
    return dict(id=gid, cuerpos=duelo, nombres=nombres, colores=cols, dur=7.0, fase=rng.choice([0.0, math.pi]),
                idas=4, umbral=0.94,                                           # 18/11 CEO: "más difícil, más rápido" (antes 2 idas y 0,88)
                musica=f"rueda_original_{rng.randint(0, 2)}", fondo=fondo_variado(V, "vs", rng), textos=tx)


# STOP TO ESCAPE (18/11, pedido del CEO: formatos nuevos ya, más difíciles): 3 estrellas en jaulas, una llave rápida;
# pausás cuando la llave está en la cerradura de tu estrella y escapa.
TIT_ESCAPE = ["Free {a}, {b} or {c}? 🔑 Stop the key in the lock", "Who escapes? 🔑 {a}, {b} or {c}",
              "{a} vs {b} vs {c}: free your GOAT 🔑🛑", "Stop the key to free {a} 🔑 Only 1% can"]


# GOALS BY AGE (19/11, CEO): carrera de goles REALES por edad; sistema dinámico (goles_catalogo.py): grupos × estadísticas ×
# escenarios, nunca el mismo escenario hasta agotar el catálogo; varía paleta, música y ritmo.
GOLES_CARA = {"messi": "lionel_messi", "ronaldo": "cristiano_ronaldo", "mbappe": "kylian_mbapp", "yamal": "lamine_yamal", "neymar": "neymar",
              "vinicius": "vin_cius_j_nior", "ronaldinho": "ronaldinho", "zidane": "zinedine_zidane", "beckham": "david_beckham",
              "henry": "thierry_henry", "zlatan": "zlatan_ibrahimovi", "lewandowski": "robert_lewandowski", "benzema": "karim_benzema",
              "kane": "harry_kane", "rooney": "wayne_rooney", "haaland": "erling_haaland", "r9": "ronaldo_nazario"}
TIT_GOLES = ["{s}: {y} 🐐 Who's the GOAT?", "{s} — {y} ⚽ Who wins?", "Who had more? {s} {y} 📊", "{y}: {s} 👀 Wait for the end",
             "{s} {y} ⚽ The answer will surprise you"]


def guion_goles(gid, rng, V, fecha):
    import goles_catalogo as GC
    usados = V.contadores.setdefault("goles_usados", [])
    e = GC.elegir(rng, usados)
    usados.append(e["clave"]); del usados[:-80]
    pal = V.contadores.setdefault("goles_paleta", [])
    paleta = min(range(6), key=lambda k: (pal[-4:].count(k), rng.random())); pal.append(paleta); del pal[:-12]
    return dict(id=gid, jugadores=e["jugadores"], estadistica=e["estadistica"], desde=e["desde"], **({"hasta": e["hasta"]} if e.get("hasta") else {}),
                seg_por_edad=round(rng.uniform(2.25, 2.55), 2), semilla=rng.randint(0, 999), paleta=paleta,
                titulo=e["titulo"], subtitulo=e["subtitulo"], yt=e["yt"], clave=e["clave"])


def guion_escape(gid, rng, V, fecha):
    ult = V.contadores.setdefault("escape_ult", [])
    hoy = sorted(TORSOS_ESTRELLA)
    dos = sorted(hoy, key=lambda c: (ult[-6:].count(c), rng.random()))[:2]
    ult.extend(dos); del ult[:-12]
    ley = rng.choice(TORSOS_LEYENDA)
    presos = [rng.choice(TORSOS_ESTRELLA[dos[0]]), ley, rng.choice(TORSOS_ESTRELLA[dos[1]])]
    if rng.random() < 0.5:
        presos[0], presos[2] = presos[2], presos[0]
    nombres = [nombre_de(c.rsplit("_", 1)[0]) for c in presos]
    a, b, c = [n.upper() for n in nombres]
    tx = dict(gancho=rng.choice(["FREE YOUR GOAT", "WHO ESCAPES?", "STOP THE KEY"]),
              apuesta=rng.choice(["TINY KEYHOLE · 1% CAN", "IMPOSSIBLE SPEED", "ONLY 1% FREE HIM"]),
              cta="HOW MANY TRIES? WHO ESCAPED?")
    return dict(id=gid, presos=presos, nombres=nombres, dur=7.5, idas=3, zona=26, fase=round(rng.uniform(0, 6.28), 2),
                musica=f"rueda_original_{rng.randint(0, 2)}", fondo="estadio_0", textos=tx)


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
    return dict(id=gid, pateador=c, nombre=n, dur=6.0, vueltas=5, musica=V.musica(rng), arquero=(rng.choice(lista) if lista else "arquero_0"),
                fondo=fondo_variado(V, "penal", rng))


def guion_balon(gid, rng, V, fecha):
    cuerpo = rng.choice(sorted(CUERPOS_RUEDA))
    lista, _ = extra_mejor("trofeo_bo", None)
    return dict(id=gid, cuerpo=cuerpo, nombre=CUERPOS_RUEDA[cuerpo], trofeo=(rng.choice(lista) if lista else "trofeo_bo_1"),
                dur=6.0, vueltas=5, musica=V.musica(rng), fondo=fondo_variado(V, "balon", rng))


# Tendencias de la semana del 04/11 (radar + Gemini): FIT challenge 6,6 M · balance at the wall 6,9 M · "who is the best" 6 M
CUERPOS_FIT = {"kylian_mbapp_13": "kylian_mbapp", "kylian_mbapp_12": "kylian_mbapp", "lionel_messi_3": "lionel_messi",
               "cristiano_ronaldo_14": "cristiano_ronaldo", "lamine_yamal_10": "lamine_yamal", "neymar_3": "neymar"}
CUERPOS_PARED = ["lionel_messi_3", "kylian_mbapp_10", "cristiano_ronaldo_14", "bukayo_saka_3", "ousmane_demb_l_3",
                 "lautaro_mart_nez_3", "kylian_mbapp_11"]                          # (sin mohamed_salah_1: tiene marca de agua)
TIT_CABEZAS = ["99.9% WILL FAIL the FIT challenge 💀 {n} edition", "Fit {n}'s head 🛑 Only 1% can", "{n} head fit challenge 😱 Pause it!",
               "{n} lost his head 😱 Stop on the right one", "{n} without a head?! 🛑 Only 1% fit it",          # 19/11: estructuras nuevas
               "{n}'s head is spinning 💀 Pause it on the real one"]
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
    cuerpo = _dueno_jugador(V, "fit_ult", CUERPOS_FIT, rng); clave = CUERPOS_FIT[cuerpo]
    otras = [c for c in FOTOS if c != clave]
    est = [c for c in SUPERESTRELLAS if c != clave and c in FOTOS]
    ley = [c for c in LEYENDAS if c in FOTOS and c != clave]
    cab = rng.sample(est, min(3, len(est))) + rng.sample(ley, min(4, len(ley))); rng.shuffle(cab)   # 15/11 CEO: solo famosos
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
    resto = rng.sample([c for c in LEYENDAS if c in FOTOS], 3)                 # 15/11 CEO: solo famosos (leyendas)
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
    estrellas = [j for j in JUGADORES if j[1] in SUPERESTRELLAS]              # 16/11: solo superestrellas (regla del 13/11 para títulos)
    grupo = con_estrella(V.grupo("dress", 2, rng, estrellas, fecha), rng, estrellas)
    # 16/11: sin tonos amarillos (se perdían contra el fondo amarillo)
    malos = [{"n": "payaso", "ok": False}, {"n": "pelo_azul~" + str(rng.choice([220, 280, 30, 0])), "ok": False},
             {"n": "peluca_rosa~" + str(rng.choice([320, 190, 280])), "ok": False}]
    rng.shuffle(malos)
    pelo = {"n": "pelo_verde" + rng.choice(["", "~0", "~270", "~200"]), "ok": True}
    medio = [{"n": "cadena", "ok": True}] + malos[:1]                         # 16/11: 4 accesorios (antes 5) y más rápidos
    rng.shuffle(medio)                                                        # → 6,8 s en vez de 11,4 s (Issue #4: 108 % visto)
    return dict(id=gid, jugadores=[c for _, c, _ in grupo], nombres=[n for n, _, _ in grupo], musica=V.musica(rng),
                items=[{"n": "anteojos", "ok": True}] + medio + [pelo], t_item=1.55, t_cae=0.95, cola=0.6)


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
        elif tipo == "escape":
            g = guion_escape(gid, rng, V, sl["fecha"])
            a, b, c3 = g["nombres"]
            titulo = V.titulo("escape", TIT_ESCAPE, rng).format(a=a, b=b, c=c3) + " " + " ".join(tag(x) for x in (a, b, c3))
            desc = ("Stop the key in the lock to free your GOAT 🔑🛑 How many tries did it take you? 👇\n"
                    + " ".join(tag(x) for x in g["nombres"]) + " #football #shorts")
            fijado = ""; fotos = []; nombres = g["nombres"]
        elif tipo == "goles":
            g = guion_goles(gid, rng, V, sl["fecha"])
            ns = [nombre_de(GOLES_CARA[k]) for k in g["jugadores"]]
            sub = g["subtitulo"].title() if " vs " not in g["subtitulo"].lower() and "·" not in g["subtitulo"] else " vs ".join(ns)
            titulo = V.titulo("goles", TIT_GOLES, rng).format(s=sub, y=g["yt"])
            titulo = titulo[:95] + " " + " ".join(tag(x) for x in ns[:2])
            desc = (f"{g['yt'][0].upper() + g['yt'][1:]}: " + " vs ".join(ns) + ". Official goals (club + country), season by season.\n"
                    "Who's the GOAT? Comment 👇\n" + " ".join(tag(x) for x in ns) + " #football #soccer #goals #shorts")
            fijado = "Who's the GOAT for you? 👇"; fotos = []; nombres = ns
        elif tipo == "favorito":
            g = guion_favorito(gid, rng, V, sl["fecha"], leyendas=sl.get("leyendas", True))
            a, b, c3 = g["nombres"][:3]
            titulo = V.titulo("favorito", TIT_FAVORITO, rng).format(a=a, b=b, c=c3) + " " + " ".join(tag(x) for x in (a, b, c3))
            desc = ("Stop the ball on your favorite player ⚽🛑 It gets faster every jump. Who did you get? Comment 👇\n"
                    + " ".join(tag(x) for x in g["nombres"]) + " #football #soccer #stopchallenge #shorts")
            fijado = ""; fotos = []; nombres = g["nombres"][:3]
        elif tipo == "piernas":
            g = guion_piernas(gid, rng, V, sl["fecha"])
            a, b = g["otros"]
            titulo = V.titulo("piernas", TIT_PIERNAS, rng).format(n=g["nombre"], a=a, b=b) + " " + " ".join(tag(x) for x in (g["nombre"], a, b))
            desc = (f"Stop the wheel when {g['nombre']}'s REAL legs are on top 🦵🛑 Only 1% get it first try. How many tries did it take you? 👇\n"
                    + " ".join(tag(x) for x in (g["nombre"], a, b)) + " #football #soccer #stopchallenge #shorts")
            fijado = ""; fotos = []; nombres = [g["nombre"], a, b]
        elif tipo == "cano":
            g = guion_cano(gid, rng, V, sl["fecha"])
            a, b = g["nombre_atq"], g["nombre_def"]
            titulo = V.titulo("cano", TIT_CANO, rng).format(a=a, b=b)
            for x in (a, b):
                if len(titulo) + len(tag(x)) + 1 <= 100:
                    titulo += " " + tag(x)
            desc = (f"Pause when the ball is between {b}'s legs 🛑 Only 1% nutmeg him. How many tries? Comment 👇\n"
                    + " ".join(tag(x) for x in (a, b)) + " #football #skills #shorts")
            fijado = ""; fotos = []; nombres = [a, b]
        elif tipo == "vs":
            g = guion_vs(gid, rng, V, sl["fecha"])
            a, b = g["nombres"]
            titulo = V.titulo("vs", TIT_VS, rng).format(a=a, b=b)
            for x in (a, b):
                if len(titulo) + len(tag(x)) + 1 <= 100:
                    titulo += " " + tag(x)
            desc = (f"Pause when the ball is in YOUR player's gold zone 👑 {a} or {b}? Who did you make win? Comment 👇\n"
                    + " ".join(tag(x) for x in (a, b)) + " #football #stopchallenge #shorts")
            fijado = ""; fotos = []; nombres = [a, b]
        elif tipo in ("cinta", "slot"):
            g = (guion_cinta if tipo == "cinta" else guion_slot)(gid, rng, V, sl["fecha"])
            a, b = rng.sample(g["otros"], 2)
            titulo = V.titulo(tipo, TIT_CINTA if tipo == "cinta" else TIT_SLOT, rng).format(n=g["nombre"], a=a, b=b)
            for x in (g["nombre"], a, b):
                if len(titulo) + len(tag(x)) + 1 <= 100:
                    titulo += " " + tag(x)
            meta = (f"Stop the belt when {g['nombre']}'s REAL body is on top of the legs 🛑" if tipo == "cinta"
                    else f"Stop the slot when {g['nombre']}'s head fits PERFECTLY 🎰🛑")
            desc = (f"{meta} Only 1% get it first try. How many tries did it take you? 👇\n"
                    + " ".join(tag(x) for x in (g["nombre"], a, b)) + " #football #soccer #stopchallenge #shorts")
            fijado = ""; fotos = []; nombres = [g["nombre"], a, b]
        elif tipo == "rueda":
            g = guion_rueda(gid, rng, V, sl["fecha"])
            otros_ = [nombre_de(t.rsplit("_", 1)[0]) for t in g["torsos"]]               # cualquiera de la rueda (varía el título)
            est_ = [o for o in g["otros"]] + [o for o in otros_ if o not in g["otros"]]
            est_ = [o for o in est_ if o in estrellas_nombres()] or est_        # 13/11: en el título solo superestrellas de la rueda
            a, b = rng.sample(est_, 2) if len(est_) >= 2 else (est_ + ["Ronaldo", "Mbappé"])[:2]
            pool_t = TIT_RUEDA                                                  # C2 (15/11): prueba A/B del estilo de título
            if sl.get("titulo_estilo") == "find":
                pool_t = [t for t in TIT_RUEDA if t.startswith("Find")]
            elif sl.get("titulo_estilo") == "vs":
                pool_t = [t for t in TIT_RUEDA if " vs " in t]
            titulo = (rng.choice(pool_t) if sl.get("titulo_estilo") else V.titulo("rueda", TIT_RUEDA, rng)).format(n=g["nombre"], a=a, b=b) \
                + " " + " ".join(tag(x) for x in (g["nombre"], a, b))
            desc = (f"Stop the wheel when {g['nombre']}'s body is PERFECT 🛑 Only 1% get it first try. How many tries did it take you? 👇\n"
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
            desc = f"{meta}\nHow many tries did it take you? 👇 Follow for part 2 🔥\n" + " ".join(tag(x) for x in ns4) + " #football #soccer #challenge #shorts"
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
            desc = (f"8 heads of {n}… only ONE is real 🎯 Pause when the REAL head fits!\nHow many tries did it take you? 👇 Follow for part 2 🔥\n"
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
            desc = f"{meta}\nHow many tries did it take you? 👇 Follow for part 2 🔥\n{etiquetas_} #football #soccer #stopchallenge #shorts"
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
        if sl.get("dur"):                                                       # 15/11: prueba A/B de duración (IA de YouTube: 7-9 s es lo óptimo)
            g["dur"] = sl["dur"]
        desc = _cuatro_hashtags(desc)                                          # 15/11 (IA de YouTube): 3-4 hashtags, no más
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
                               **({"variante": g["arranque"]} if g.get("arranque") else {}),
                               **({"exp": sl["exp"]} if sl.get("exp") else {})))      # Fase 2: prueba A/B del cerebro (se mide sola)
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
