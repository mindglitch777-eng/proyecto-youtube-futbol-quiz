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
           "hoyo": "BALL TO THE HOLE", "dress": "DRESS UP", "torre": "BALL TOWER"}
SCRIPT = {"stop": "render_stop.py", "find": "render_find_v2.py", "look": "render_look.py", "cabeza": "render_cabeza.py",
          "plinko": "render_plinko.py", "hoyo": "render_hoyo.py", "dress": "render_dress.py", "torre": "render_torre.py"}
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


def nombre_de(clave):
    for n, c, _ in JUGADORES:
        if c == clave:
            return n
    return NOMBRE.get(clave, clave.split("_")[0].title())


def guion_stop(gid, rng, usados, dificil, V=None, fecha=None):
    """STOP en serie (#nivel), con tema rotativo (B1) y cada 3er nivel HARD: más vueltas, giro doble y 5 s (B2)."""
    tema = nivel = None
    if V is not None:
        tema = V.titulo("stop_tema", list(TEMAS_STOP), rng)
        nivel = V.siguiente("stop_nivel", 13)
        pool = [(nombre_de(c), FOTOS.get(c) and c, 3) for c in TEMAS_STOP[tema] if c in FOTOS]
        grupo = V.grupo("stop_" + tema, 4, rng, pool, fecha)
        dificil = nivel % 3 == 0
    else:
        grupo = elegir(rng, 4, usados)
    pcts = [f"{rng.choice([1, 1, 2, 3])}%", f"{rng.randint(5, 29)}%", f"{rng.randint(33, 61)}%", f"{rng.choice([67, 67, 69, 88, 99])}%"]
    vueltas = ([6, 5, 5, 6] if nivel and nivel % 3 == 0 else [5, 4, 3, 4]) if dificil else [4, 3, 3, 2]
    giros = ([2, 2, 1, 2] if nivel and nivel % 3 == 0 else [1, 1, 1, 2]) if dificil else [1, 1, 2, 2]
    colores = rng.sample(COLORES, 4); formas = [rng.choice(FORMAS) for _ in range(4)]
    cuads = []
    for k, (n, clave, _) in enumerate(grupo):
        cuads.append(dict(nombre=n, foto=FOTOS[clave], color=colores[k], pct=pcts[k], forma=formas[k], rasgo=rng.choice(RASGOS),
                          vueltas=vueltas[k], giros=giros[k], encaje_bueno=rng.randint(0, 3), fase=round(rng.uniform(0, 6.28), 2),
                          tam=rng.choice([60, 64, 68])))
    g = dict(id=gid, duracion=5.0 if (nivel and nivel % 3 == 0) else 6.0, hiper=True, musica="67", cuadrantes=cuads)
    if nivel:
        g.update(tema=(tema + " · HARD") if nivel % 3 == 0 else tema, nivel=nivel, pregunta="WHICH ONE DID YOU STOP? 1-4", tema_base=tema)
    return g


def guion_look(gid, rng, usados_look, V=None):
    hechos = V.grupos.setdefault("look", set()) if V else set()
    for intento in range(500):
        n, clave, _ = rng.choices(JUGADORES, [w for *_, w in JUGADORES])[0]
        looks = rng.sample(LOOKS, 4)
        combo = tuple([n] + sorted(looks))
        if (n not in usados_look or intento > 300) and combo not in hechos:   # un jugador distinto cada día; combo nunca repetido
            usados_look.add(n); hechos.add(combo); break
    return dict(id=gid, foto=FOTOS[clave], nombre=n, looks=looks, color0=rng.randint(0, 5), titulo_pantalla=rng.choice(PANT_LOOK))


def guion_find(gid, rng, usados, V=None):
    grupo = elegir(rng, 3, usados)
    rondas = [dict(nombre=n, foto=FOTOS[c], nivel=nv) for (n, c, _), nv in zip(grupo, ["facil", "medio", "dificil"])]
    return dict(id=gid, semilla=V.semilla(rng) if V else rng.randint(1, 999), frase=rng.choice(FRASES), rondas=rondas)


def guion_cabeza(gid, rng, usados_cab, V=None):
    hechos = V.grupos.setdefault("cabeza", set()) if V else set()
    for intento in range(500):
        grupo = elegir(rng, 3, set())
        combo = tuple([grupo[0][0]] + sorted(n for n, *_ in grupo[1:]))
        if (grupo[0][0] not in usados_cab or intento > 300) and combo not in hechos:
            usados_cab.add(grupo[0][0]); hechos.add(combo); break
    real = grupo[0]; opciones = [FOTOS[c] for _, c, _ in grupo[1:]]
    opciones.insert(rng.choice([1, 2]), FOTOS[real[1]])                       # la correcta nunca es la primera
    return dict(id=gid, nombre=real[0], foto=FOTOS[real[1]], opciones=opciones, color=rng.choice(COLORES_CABEZA))


def guion_plinko(gid, rng, V, fecha):
    grupo = V.grupo("plinko", 4, rng, JUGADORES, fecha)
    return dict(id=gid, jugadores=[c for _, c, _ in grupo], nombres=[n for n, _, _ in grupo], semilla=V.semilla(rng) * 5000,
                titulo=V.titulo("plinko_pantalla", PANT_PLINKO, rng), musica=V.musica(rng))


def guion_dress(gid, rng, V, fecha):
    grupo = V.grupo("dress", 2, rng, JUGADORES, fecha)
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
        if len({cartas.datos(c)[2] for _, c, _ in grupo}) == 3:
            break
    nombres = [n for n, _, _ in grupo]
    fondo, piso = rng.choice(FONDOS_TORRE)
    return dict(id=gid, opciones=[c for _, c, _ in grupo], nombres=nombres, correcta=V.ganador(nombres, rng), semilla=V.semilla(rng),
                musica=V.musica(rng), fondo=fondo, piso=piso)


def guion_hoyo(gid, rng, V, fecha):
    grupo = V.grupo("hoyo", 4, rng, JUGADORES, fecha)
    nombres = [n for n, _, _ in grupo]
    return dict(id=gid, jugadores=[c for _, c, _ in grupo], nombres=nombres, ganador=V.ganador(nombres, rng), semilla=V.semilla(rng),
                titulo=V.titulo("hoyo_pantalla", PANT_HOYO, rng), musica=V.musica(rng))


def creditos(claves):
    return "\n".join(f'- {CRED[k]["jugador"]}: "{CRED[k]["archivo"].replace("File:", "")}" by {CRED[k]["autor"]}, {CRED[k]["licencia"]} '
                     f'({CRED[k]["pagina"]}). Edited.' for k in claves if k in CRED)


def tag(n):
    return "#" + n.lower().replace("é", "e").replace("í", "i").replace("á", "a")


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


def fabricar(slots, sem, rng, prefijo="s1", procesos=3):
    """Genera, renderiza y deja en `sem` un video por slot (dict fecha, hora, tipo, dificil) + su .txt + videos.json."""
    (sem / "guiones").mkdir(parents=True, exist_ok=True)
    from variedad import Variedad
    V = Variedad.cargar()                                                     # memoria permanente: nada se repite entre semanas
    usados = V.grupos.setdefault("stop_find", set())
    usados_look, usados_cab, trabajos, filas, manifiesto = set(), set(), [], [], []
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
            g = guion_stop(gid, rng, usados, dificil=sl.get("dificil", True), V=V, fecha=sl["fecha"])
            titulo = V.titulo("stop_serie", TIT_STOP_SERIE, rng).format(n=g["nivel"], tema=TEMA_TITULO.get(g["tema_base"], g["tema_base"].title()))
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
        manifiesto.append(dict(id=gid, n=n, fecha=dia.isoformat(), hora=hora, tipo=tipo, formato=FORMATO[tipo], titulo=titulo,
                               descripcion=desc_completa, fijado=fijado, jugadores=nombres,
                               tags=["football", "soccer", "shorts"] + [x.lower() for x in nombres], archivo=f"{gid}.mp4"))
        trabajos.append((tipo, ruta))
        filas.append(f"| {n} | {dia.isoformat()} ({DIAS[dia.weekday()]}) | {hora} | {FORMATO[tipo]} | {titulo} | `{gid}` |")
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
