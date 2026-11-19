#!/usr/bin/env python3
"""
Convierte el texto crudo de Wikipedia (assets/goles/<clave>.txt, de goles_wiki.py) en goles oficiales ACUMULADOS por edad.
- Cuenta: club PRIMER equipo (temporada por temporada, columna Total) + selección MAYOR (año por año, columna Total).
  Sin equipos B/C/reserva/juveniles ni selecciones juveniles (lo habitual al hablar de "goles en su carrera").
- Edad de cada fila = la edad que tenía al TERMINAR esa temporada (30/6 del 2.º año; temporadas de un año calendario y los
  años de selección terminan el 31/12). La temporada en curso cuenta en su edad de hoy.
- Guarda también el club de cada edad (para pintar la barra con sus colores) y verifica contra el total de la tabla.
Salida: assets/goles/goles_edad.json
"""
import json
import re
from datetime import date
from pathlib import Path

DIR = Path(__file__).resolve().parent / "assets" / "goles"
NOMBRE = {"messi": "Messi", "ronaldo": "Ronaldo", "mbappe": "Mbappé", "yamal": "Yamal", "neymar": "Neymar", "zlatan": "Zlatan",
          "henry": "Henry", "ronaldinho": "Ronaldinho", "vinicius": "Vinícius", "zidane": "Zidane", "beckham": "Beckham"}
RESERVA = re.compile(r"\b(B|C|II|III|Castilla|Atlètic|Atletic|Reserves?|Youth|Juniors?|U-?\d\d|under-\d\d|Under-\d\d|Academy|Promesas)\b|Barcelona Atl", re.I)
HOY = date.today()


def limpiar(t):
    t = re.sub(r"<ref[^>/]*/>", "", t)
    t = re.sub(r"<ref[^>]*>.*?</ref>", "", t, flags=re.S)
    t = re.sub(r"<!--.*?-->", "", t, flags=re.S)
    for _ in range(12):                                                        # plantillas de adentro hacia afuera
        nuevo = re.sub(r"\{\{\s*(nowrap|nobr)\s*\|([^{}]*)\}\}", r"\2", t, flags=re.I)
        nuevo = re.sub(r"\{\{[^{}]*\}\}", "", nuevo)
        if nuevo == t:
            break
        t = nuevo
    t = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r"\1", t)
    return t


def filas(tabla):
    out = []
    for f in tabla.split("\n|-")[1:]:
        celdas = []
        for linea in f.strip("\n").split("\n"):
            if not linea.startswith("|") or linea.startswith(("|+", "|}")):
                continue
            for c in linea[1:].split("||"):
                c = c.strip()
                if "|" in c and re.match(r'^\s*(rowspan|colspan|style|align|scope)[^|]*\|', c):
                    c = c.split("|", 1)[1].strip()
                celdas.append(c)
        if celdas:
            out.append(celdas)
    return out


def enteros(celdas):
    return [int(c.replace(",", "")) for c in celdas if re.fullmatch(r"\d[\d,]*", c)]


def nacimiento(texto):
    m = re.search(r"birth[ _]date(?: and age)?\s*\|(?:[^|}]*=[^|}]*\|)*\s*(\d{4})\s*\|\s*(\d{1,2})\s*\|\s*(\d{1,2})", texto, re.I)
    return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))


def edad(nac, d):
    return d.year - nac.year - ((d.month, d.day) < (nac.month, nac.day))


def procesar(k):
    crudo = (DIR / f"{k}.txt").read_text()
    nac = nacimiento(crudo)
    bloque = crudo.split("#### SECCION")[1]                                     # solo la sección "Career statistics" completa
    tablas = re.findall(r"\{\|.*?\n\|\}", limpiar(bloque), flags=re.S)
    filas_out, club_total, selec_total = [], 0, 0
    for tb in tablas:
        es_club = "by club" in tb.split("\n", 3)[1].lower()
        cap = tb.split("\n", 3)[1].lower()
        es_sel = "national team" in cap or ("by year" in cap and "club" not in cap)
        if not (es_club or es_sel):
            continue
        actual = None
        for c in filas(tb):
            idx = next((i for i, x in enumerate(c) if re.fullmatch(r"(\d{4})(?:[–-](\d{2,4}))?", x)), None)
            if idx is None:
                continue
            if idx >= 1:
                actual = c[0]
            ns = enteros(c[idx + 1:])
            if not ns or actual is None:
                continue
            goles = ns[-1]
            if RESERVA.search(actual) or (es_sel and re.search(r"under|U-?\d\d|Olympic", actual, re.I)):
                continue
            m = re.fullmatch(r"(\d{4})(?:[–-](\d{2,4}))?", c[idx])
            if m.group(2) and not es_sel:
                fin = int(m.group(1)) + 1
                d_fin = date(fin, 6, 30)
            else:
                d_fin = date(int(m.group(1)), 12, 31)
            e = edad(nac, min(d_fin, HOY))
            filas_out.append(dict(tipo="club" if not es_sel else "seleccion", equipo=actual, temporada=c[idx], goles=goles, edad=e))
            if es_sel:
                selec_total += goles
            else:
                club_total += goles
    edad_hoy = edad(nac, HOY)
    # una vuelta suelta después de años sin jugar (ej. Ronaldinho a los 46, 0 goles) no cuenta como carrera activa
    eds = sorted({f["edad"] for f in filas_out if f["tipo"] == "club"})
    for a, b in zip(eds, eds[1:]):
        if b - a > 2:
            filas_out = [f for f in filas_out if f["edad"] <= a]
            break
    acum, clubes, s = {}, {}, 0
    e0 = min(f["edad"] for f in filas_out)
    for e in range(e0, edad_hoy + 1):
        s += sum(f["goles"] for f in filas_out if f["edad"] == e)
        acum[e] = s
        cl = [f for f in filas_out if f["edad"] == e and f["tipo"] == "club"]
        if cl:
            clubes[e] = max(cl, key=lambda f: f["goles"])["equipo"]
    retiro = max(f["edad"] for f in filas_out)
    activo = any(f["edad"] == edad_hoy for f in filas_out)
    if not activo:
        acum = {e: v for e, v in acum.items() if e <= retiro}
    return dict(nombre=NOMBRE[k], nacimiento=nac.isoformat(), edad_hoy=edad_hoy, activo=activo, total=s if activo else acum[retiro],
                club=club_total, seleccion=selec_total, acumulado_por_edad=acum, club_por_edad=clubes, filas=filas_out)


def main():
    out = dict(fuente="Wikipedia (en), Career statistics: club primer equipo + selección mayor, goles oficiales", fecha=HOY.isoformat(),
               jugadores={})
    for f in sorted(DIR.glob("*.txt")):
        try:
            out["jugadores"][f.stem] = j = procesar(f.stem)
            print(f"{j['nombre']:10} nac {j['nacimiento']} edad {j['edad_hoy']} activo {j['activo']} total {j['total']} "
                  f"(club {j['club']} + selección {j['seleccion']})")
        except Exception as e:
            print(f.stem, "ERROR", repr(e))
    (DIR / "goles_edad.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
