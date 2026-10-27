#!/usr/bin/env python3
"""
Calendario V2 (27-oct → 13-nov, 2 por día a las 10:00 y 23:00 ART) para la página de subida.
Mezcla: 1 simulación por día (Circle Cup, Ring Escape, Trophy Race, Carreras V5) + 1 formato pasivo/quiz
(evolución, FIND, prime vs now, dupla, objetos). Los textos de los formatos que no cambiaron se reusan del calendario anterior.

Uso: python3 calendario_v2.py <cal_anterior.json> <salida.json>
"""
import json
import sys
from datetime import date, timedelta
from pathlib import Path

from paquete_nuevos import CRED, MEJOR, hashtag, linea
from render_carrera import ESCUDO

ROOT = Path(__file__).resolve().parent
DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]

# (id, formato, motivo con números)
PLAN = [
    ("copa_02", "copa", "Circle Cup V2: misma receta que Footrix (3,9 M con cuadro de 8). Kane ganó el Balón de Oro y el debate está caliente"),
    ("ring_01", "ring", "Ring Escape: formato de bouncyball (86,2 M), con el debate más grande del fútbol"),
    ("evo_01", "evo", "Evolución: FULYON hizo 13,5 M con la de Ronaldo y su 1er millón llegó en el video 3"),
    ("copa_01", "copa", "Circle Cup GOAT: final Ronaldo vs Messi (el 86 % de las carreras top gana el favorito del público)"),
    ("objeto_01", "objeto", "Evolución de pelotas del Mundial: el formato de objetos hace 10–26 M"),
    ("trofeos_01", "trofeos", "Trophy Race: Rival Stats hizo 4,2 M y su 1er millón llegó en 5 días. Datos verificados: Messi 16, Ronaldo 13"),
    ("find_the_real_03", "find", "FIND: el formato de FULYON (23,4 M), 3 rondas y 15 s"),
    ("evo_02", "evo", "Evolución: Neymar"),
    ("carrera_02", "carrera", "Carrera V5: campeones del mundo (gana Argentina), 60 fps y cámara suave"),
    ("ring_02", "ring", "Ring Escape con escudos reales: Real Madrid vs Barça"),
    ("dupla_02", "dupla", "Dupla: Messi y Neymar"),
    ("carrera_04", "carrera", "Carrera V5: debate GOAT (gana Ronaldo)"),
    ("copa_03", "copa", "Circle Cup de Champions con escudos reales, la víspera de la semana de Champions"),
    ("carrera_10", "carrera", "Predicción del martes de Champions, con escudos reales"),
    ("prime_01", "prime", "Prime vs now: Barcelona 2015"),
    ("carrera_11", "carrera", "Predicción del miércoles de Champions, con escudos reales"),
    ("ring_03", "ring", "Ring Escape de 4 estrellas: Yamal, Mbappé, Kane y Haaland"),
    ("find_the_real_04", "find", "FIND"),
    ("carrera_08", "carrera", "Trío con Ronaldo (fórmula DriveLabs: 24,3 M)"),
    ("evo_03", "evo", "Evolución: Beckham"),
    ("carrera_03", "carrera", "Libertadores con escudos reales (gana Boca)"),
    ("dupla_01", "dupla", "Dupla: Lampard y Drogba (público del Reino Unido)"),
    ("carrera_05", "carrera", "Premier Big 6 con escudos reales (gana United)"),
    ("evo_04", "evo", "Evolución: Salah"),
    ("carrera_07", "carrera", "Leyendas vs nueva generación (gana Ronaldinho)"),
    ("prime_02", "prime", "Prime vs now: Alemania 2014"),
    ("carrera_09", "carrera", "Trío con Ronaldo"),
    ("find_the_real_05", "find", "FIND"),
    ("dupla_03", "dupla", "Dupla: Casillas y Ramos"),
    ("evo_05", "evo", "Evolución: Zlatan"),
    ("prime_03", "prime", "Prime vs now: España 2010"),
    ("dupla_04", "dupla", "Dupla: Suárez y Messi"),
    ("evo_06", "evo", "Evolución: Modrić"),
    ("prime_04", "prime", "Prime vs now: Francia 2018"),
    ("evo_07", "evo", "Evolución: Kane"),
]
SIMS = {"copa": "_v2", "ring": "", "trofeos": "", "carrera": "_v5"}
NOTA_ESCUDOS = "Club crests are trademarks of their respective clubs, shown for identification only."


def slots():
    d, h = date(2026, 10, 27), "23:00"
    while True:
        yield d, h
        d, h = (d, "23:00") if h == "10:00" else (d + timedelta(days=1), "10:00")


def creditos(g):
    lin = [linea(CRED[MEJOR[c["nombre"]]["foto"]]) for c in g["competidores"] if c["tipo"] == "jugador"]
    txt = ""
    if lin:
        txt += "\n\nPhoto credits (Wikimedia Commons). Images were modified; the modified images are shared under CC BY-SA 4.0:\n" + "\n".join(lin)
    if any(c["tipo"] == "club" for c in g["competidores"]):
        for c in g["competidores"]:
            assert c["tipo"] != "club" or c["nombre"] in ESCUDO, c["nombre"]
        txt += "\n\n" + NOTA_ESCUDOS
    if any(c["tipo"] == "pais" for c in g["competidores"]):
        txt += "\nFlag icons: Twemoji (https://github.com/jdecked/twemoji), CC BY 4.0."
    return txt


def version_sim(gid, formato, viejo, archivo):
    g = json.loads((ROOT / "guiones" / f"{gid}.json").read_text())
    tags = {"copa": ["#football", "#soccer", "#simulation", "#shorts"], "ring": ["#football", "#soccer", "#satisfying", "#shorts"],
            "trofeos": ["#football", "#soccer", "#messi", "#ronaldo", "#shorts"],
            "carrera": ["#football", "#soccer", "#marblerace", "#shorts"]}[formato]
    tags += [hashtag(c["nombre"]) for c in g["competidores"][:3] if hashtag(c["nombre"]) not in tags]
    if formato == "carrera" and viejo:                                    # textos ya aprobados del calendario anterior
        v = dict(viejo)
        if any(c["tipo"] == "club" for c in g["competidores"]) and NOTA_ESCUDOS not in v["descripcion"]:
            v["descripcion"] += "\n\n" + NOTA_ESCUDOS
    else:
        desc = g["descripcion"] + "\n\n" + " ".join(tags) + creditos(g)
        if formato == "trofeos":
            desc += ("\n\nData: Ballon d'Or, UEFA Champions League, World Cup, Copa América, Euro, Nations League "
                     "and Finalissima titles, 2006–2025.")
        v = dict(titulos=g["titulos"][:3], descripcion=desc, fijar=g["comentario_fijado"])
    v.update(id=gid, archivo=archivo, ruta=f"v2/{gid}.mp4",
             como="Calidad V2 (60 fps). Ya trae " + ("relator, beat y efectos" if formato == "carrera" else "música propia y un sonido por rebote") +
                  ". Si querés probar un sonido en tendencia, bajale el volumen al original desde el editor de Shorts.")
    return v


def main(viejo_path, salida):
    viejo = {v["id"]: v for it in json.loads(Path(viejo_path).read_text()) for v in it["versiones"]}
    items = []
    for n, ((gid, formato, motivo), (d, h)) in enumerate(zip(PLAN, slots()), 1):
        archivo = f"{n:02d}_{["lun", "mar", "mie", "jue", "vie", "sab", "dom"][d.weekday()]}{d.day:02d}-{d.month:02d}_{h[:2]}h_{gid}.mp4"
        if formato in SIMS:
            v = version_sim(gid, formato, viejo.get(gid), archivo)
        else:
            v = dict(viejo[gid]); v["archivo"] = archivo
        items.append(dict(n=n, fecha=d.isoformat(), dia=f"{DIAS[d.weekday()]} {d.day} {MESES[d.month - 1]}", hora=h,
                          formato=formato, motivo=motivo, versiones=[v]))
    Path(salida).write_text(json.dumps(items, ensure_ascii=False, indent=1))
    print(len(items), "items:", items[0]["dia"], "→", items[-1]["dia"])


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
