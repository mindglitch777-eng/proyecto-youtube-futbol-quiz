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
          "henry": "Henry", "ronaldinho": "Ronaldinho", "vinicius": "Vinícius", "zidane": "Zidane", "beckham": "Beckham",
          "lewandowski": "Lewandowski", "benzema": "Benzema", "kane": "Kane", "rooney": "Rooney", "haaland": "Haaland", "r9": "Ronaldo R9"}
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
                n = 1
                if "|" in c and re.match(r'^\s*(rowspan|colspan|style|align|scope)[^|]*\|', c):
                    attr, c = c.split("|", 1); c = c.strip()
                    m = re.search(r'colspan\s*=\s*"?(\d+)', attr)
                    n = int(m.group(1)) if m else 1
                celdas += [c] * n
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
        # grupos del encabezado (para separar liga / copas / continental / otros / total)
        grupos = []
        for linea in tb.split("\n"):
            if linea.startswith("|") and not linea.startswith(("|-", "|+", "|}", "{|")):
                break                                                          # empezaron las filas de datos
            if linea.startswith("!") and "colspan" in linea:
                for h in re.split(r"!!|\|\|", linea[1:]):
                    m = re.search(r'colspan\s*=\s*"?(\d+)"?\s*\|\s*(.*)', h)
                    if m:
                        grupos.append((m.group(2).strip().lower(), int(m.group(1))))
                    elif "rowspan" in h:
                        pass
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
            comp = {}
            if not es_sel and grupos:
                resto = c[idx + 1:]
                pos = 0
                for nom, ancho in grupos:
                    celda = resto[pos + ancho - 1] if pos + ancho - 1 < len(resto) else ""
                    v = int(celda.replace(",", "")) if re.fullmatch(r"\d[\d,]*", celda or "") else 0
                    clave = ("liga" if nom.startswith("league") and ancho == 3 else "continental" if ("continental" in nom or "europe" in nom)
                             else "total" if nom.startswith("total") else "copas" if "cup" in nom or "state" in nom else "otros")
                    comp[clave] = comp.get(clave, 0) + v
                    pos += ancho
            if RESERVA.search(actual) or (es_sel and re.search(r"under|U-?\d\d|Olympic", actual, re.I)):
                continue
            m = re.fullmatch(r"(\d{4})(?:[–-](\d{2,4}))?", c[idx])
            if m.group(2) and not es_sel:
                fin = int(m.group(1)) + 1
                d_fin = date(fin, 6, 30)
            else:
                d_fin = date(int(m.group(1)), 12, 31)
            e = edad(nac, min(d_fin, HOY))
            filas_out.append(dict(tipo="club" if not es_sel else "seleccion", equipo=actual, temporada=c[idx], goles=goles, edad=e, **comp))
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
    # series acumuladas por estadística (19/11: el sistema de GOALS BY AGE cambia de tema para no repetirse)
    NO_EUROPA = re.compile(r"Inter Miami|Al-|Santos|Galaxy|Chicago|Cruzeiro|Corinthians|Flamengo|Grêmio|Red Bulls|Querétaro|Mineiro|Fluminense|São Paulo|Botafogo", re.I)
    def serie(filtro, campo="goles"):
        out_, s_ = {}, 0
        for e_ in range(e0, edad_hoy + 1):
            s_ += sum(f.get(campo, 0) or 0 for f in filas_out if f["edad"] == e_ and filtro(f))
            out_[e_] = s_
        return out_
    series = dict(total=None, club=serie(lambda f: f["tipo"] == "club"), seleccion=serie(lambda f: f["tipo"] == "seleccion"),
                  liga=serie(lambda f: f["tipo"] == "club", "liga"),
                  europa=serie(lambda f: f["tipo"] == "club" and not NO_EUROPA.search(f["equipo"]), "continental"))
    retiro = max(f["edad"] for f in filas_out)
    activo = any(f["edad"] == edad_hoy for f in filas_out)
    if not activo:
        acum = {e: v for e, v in acum.items() if e <= retiro}
    for k_, v_ in list(series.items()):
        if v_ is not None and not activo:
            series[k_] = {e: x for e, x in v_.items() if e <= retiro}
    series["total"] = acum
    chequeo = {k_: (v_[max(v_)] if v_ else 0) for k_, v_ in series.items()}
    return dict(series=series, chequeo=chequeo, nombre=NOMBRE[k], nacimiento=nac.isoformat(), edad_hoy=edad_hoy, activo=activo, total=s if activo else acum[retiro],
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
