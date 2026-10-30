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
FORMATO = {"stop": "STOP", "find": "FIND", "look": "¿CUÁL LOOK?", "cabeza": "CATCH THE RIGHT HEAD"}
SCRIPT = {"stop": "render_stop.py", "find": "render_find_v2.py", "look": "render_look.py", "cabeza": "render_cabeza.py"}
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


def guion_stop(gid, rng, usados, dificil):
    grupo = elegir(rng, 4, usados)
    pcts = [f"{rng.choice([1, 1, 2, 3])}%", f"{rng.randint(5, 29)}%", f"{rng.randint(33, 61)}%", f"{rng.choice([67, 67, 69, 88, 99])}%"]
    vueltas = [5, 4, 3, 4] if dificil else [4, 3, 3, 2]
    giros = [1, 1, 1, 2] if dificil else [1, 1, 2, 2]
    colores = rng.sample(COLORES, 4); formas = [rng.choice(FORMAS) for _ in range(4)]
    cuads = []
    for k, (n, clave, _) in enumerate(grupo):
        cuads.append(dict(nombre=n, foto=FOTOS[clave], color=colores[k], pct=pcts[k], forma=formas[k], rasgo=rng.choice(RASGOS),
                          vueltas=vueltas[k], giros=giros[k], encaje_bueno=rng.randint(0, 3), fase=round(rng.uniform(0, 6.28), 2),
                          tam=rng.choice([60, 64, 68])))
    return dict(id=gid, duracion=6.0, hiper=True, musica="67", cuadrantes=cuads)


def guion_look(gid, rng, usados_look):
    while True:
        n, clave, _ = rng.choices(JUGADORES, [w for *_, w in JUGADORES])[0]
        looks = rng.sample(LOOKS, 4)
        if n not in usados_look:                                              # un jugador distinto cada día
            usados_look.add(n); break
    return dict(id=gid, foto=FOTOS[clave], nombre=n, looks=looks, color0=rng.randint(0, 5), titulo_pantalla=rng.choice(PANT_LOOK))


def guion_find(gid, rng, usados):
    grupo = elegir(rng, 3, usados)
    rondas = [dict(nombre=n, foto=FOTOS[c], nivel=nv) for (n, c, _), nv in zip(grupo, ["facil", "medio", "dificil"])]
    return dict(id=gid, semilla=rng.randint(1, 999), frase=rng.choice(FRASES), rondas=rondas)


def guion_cabeza(gid, rng, usados_cab):
    while True:
        grupo = elegir(rng, 3, set())
        if grupo[0][0] not in usados_cab:
            usados_cab.add(grupo[0][0]); break
    real = grupo[0]; opciones = [FOTOS[c] for _, c, _ in grupo[1:]]
    opciones.insert(rng.choice([1, 2]), FOTOS[real[1]])                       # la correcta nunca es la primera
    return dict(id=gid, nombre=real[0], foto=FOTOS[real[1]], opciones=opciones, color=rng.choice(COLORES_CABEZA))


def creditos(claves):
    return "\n".join(f'- {CRED[k]["jugador"]}: "{CRED[k]["archivo"].replace("File:", "")}" by {CRED[k]["autor"]}, {CRED[k]["licencia"]} '
                     f'({CRED[k]["pagina"]}). Edited.' for k in claves if k in CRED)


def tag(n):
    return "#" + n.lower().replace("é", "e").replace("í", "i").replace("á", "a")


def render(args):
    tipo, ruta = args
    r = subprocess.run([sys.executable, str(ROOT / SCRIPT[tipo]), str(ruta)], capture_output=True, text=True, cwd=ROOT)
    return ruta, r.returncode, r.stderr[-400:]


def main():
    inicio = date.fromisoformat(sys.argv[1]); dias = int(sys.argv[2]); rng = random.Random(int(sys.argv[3]) if len(sys.argv) > 3 else 67)
    sem = ROOT / f"semana_{inicio.isoformat()}"; (sem / "guiones").mkdir(parents=True, exist_ok=True)
    usados, usados_look, usados_cab, trabajos, filas = set(), set(), set(), [], []
    n = 0
    for d in range(dias):
        dia = inicio + timedelta(days=d); et = f"{DIAS[dia.weekday()]}{dia.day:02d}"
        for slot in ("stopA", "find", "look", "noche"):
            n += 1
            tipo = {"stopA": "stop", "find": "find", "look": "look", "noche": "cabeza" if d % 2 == 0 else "stop"}[slot]
            gid = f"s1_{n:02d}_{et}_{HORAS[slot].replace(':', '')}_{tipo}"
            if tipo == "find":
                g = guion_find(gid, rng, usados)
                titulo = "FIND " + " ".join(r["nombre"].upper() for r in g["rondas"])
                desc = "Find the REAL one in every round 🔎 Round 3 is only for the 1%\nComment the numbers 👇\n" + " ".join(tag(r["nombre"]) for r in g["rondas"])
                fijado = "Answers in the video 👀 Which round did you get wrong? 1, 2 or 3?"
                fotos = [r["foto"] for r in g["rondas"]]
            elif tipo == "cabeza":
                g = guion_cabeza(gid, rng, usados_cab)
                titulo = rng.choice(TIT_CABEZA).format(n=g["nombre"])
                desc = f"Only one head fits {g['nombre']} 🤯 Did you guess it before the end? 1, 2 or 3 👇\n{tag(g['nombre'])} #football #shorts"
                fijado = "Be honest… did you get it before it landed? 👀"
                fotos = g["opciones"]
            elif tipo == "look":
                g = guion_look(gid, rng, usados_look)
                titulo = rng.choice(TIT_LOOK).format(n=g["nombre"])
                desc = f"Which one fits {g['nombre']} best? Comment 1, 2, 3 or 4 👇\n{tag(g['nombre'])} #football #shorts"
                fijado = f"I'm going with number {rng.randint(1, 4)} 😂 what about you?"
                fotos = [g["foto"]]
            else:
                g = guion_stop(gid, rng, usados, dificil=(slot == "stopA"))
                titulo = rng.choice(TIT_STOP)
                desc = "It only fits ONCE per loop 🛑 Pause at the perfect moment. Which one did you get?\n" + " ".join(tag(q["nombre"]) for q in g["cuadrantes"])
                q0 = g["cuadrantes"][0]
                fijado = f"{q0['nombre']} {q0['pct']} only fits ONE time... did you get it? 😤"
                fotos = [q["foto"] for q in g["cuadrantes"]]
            ruta = sem / "guiones" / f"{gid}.json"
            ruta.write_text(json.dumps(g, ensure_ascii=False, indent=1))
            (sem / f"{gid}.txt").write_text(
                f"=== PROGRAMAR ===\n{dia.isoformat()} a las {HORAS[slot]} (hora de Argentina)\n\n=== TÍTULO ===\n{titulo}\n\n=== DESCRIPCIÓN ===\n{desc}\n\n"
                f"Photo credits (Wikimedia Commons). Images were modified; the modified images are shared under CC BY-SA 4.0:\n{creditos(fotos)}\n\n"
                f"=== COMENTARIO PARA FIJAR ===\n{fijado}\n\n=== AL SUBIR ===\n- Idioma del video: Inglés. Solo hashtags en inglés.\n"
                f"- Si podés, usá el archivo _solo_efectos y agregá desde la app el sonido '6 7' en tendencia.\n")
            trabajos.append((tipo, ruta))
            filas.append(f"| {n} | {dia.isoformat()} ({DIAS[dia.weekday()]}) | {HORAS[slot]} | {FORMATO[tipo]} | {titulo} | `{gid}` |")
    with ProcessPoolExecutor(3) as ex:
        for ruta, rc, err in ex.map(render, trabajos):
            print("ok" if rc == 0 else "ERROR", ruta.stem, "" if rc == 0 else err, flush=True)
    for tipo, ruta in trabajos:                                               # mover los videos a la carpeta de la semana
        sal = ROOT / "salida" / ruta.stem
        for f, suf in (("short.mp4", ""), ("short_solo_efectos.mp4", "_solo_efectos"), ("short_sin_musica.mp4", "_solo_efectos")):
            if (sal / f).exists():
                (sal / f).replace(sem / f"{ruta.stem}{suf}.mp4")
        if tipo == "find" and (sal / "resultado.json").exists():               # soluciones del FIND al .txt
            res = json.loads((sal / "resultado.json").read_text())
            sol = " · ".join(f'{x["nombre"].title()} #{x["real"]}' for x in res["rondas"])
            with open(sem / f"{ruta.stem}.txt", "a") as fh:
                fh.write(f"\n=== SOLUCIONES (para vos) ===\n{sol}\n")
    (sem / "CALENDARIO.md").write_text("# Calendario de la semana\n\n| # | Día | Hora (ARG) | Formato | Título | Archivo |\n|---|---|---|---|---|---|\n" + "\n".join(filas) + "\n")
    print(sem)


if __name__ == "__main__":
    main()
