#!/usr/bin/env python3
"""
SUBIR.txt para los formatos nuevos (carrera, evolucion, prime_now, find_the_real): títulos, descripción con créditos
de fotos (CC), hashtags, comentario para fijar y pasos. Uso: python3 paquete_nuevos.py guiones/carrera_01.json [...]
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CRED = json.loads((ROOT / "assets/fotos/creditos.json").read_text())
MEJOR = json.loads((ROOT / "assets/mejor_foto.json").read_text())


def linea(c):
    return (f"- {c.get('jugador') or 'World Cup ball ' + str(c.get('anio'))}: \"{c['archivo'].removeprefix('File:')}\" by {c['autor'] or 'unknown'}, "
            f"{c['licencia']} ({c['pagina']}). Edited.")


def hashtag(s):
    s = re.sub(r"[^a-z0-9]", "", s.lower().replace("é", "e").replace("í", "i").replace("ñ", "n").replace("á", "a"))
    return "#" + s


def paquete(g):
    out = ROOT / "salida" / g["id"]
    f = g["formato"]
    creditos, twemoji = [], False
    if f == "carrera":
        for c in g["competidores"]:
            if c["tipo"] == "jugador":
                creditos.append(linea(CRED[MEJOR[c["nombre"]]["foto"]]))
            twemoji |= c["tipo"] == "pais"
        ev = g["evento"].title().replace("'S", "'s").replace("D'Or", "d'Or")
        titulos = g.get("titulos") or [f"{g['evento']} RACE 🏁 Who wins? Pick one!",
                                       f"Only ONE can win… {g['gancho'].title()} 😳", f"{ev} marble race 🏆 PICK NOW"]
        gan = g["gancho"].capitalize() + ("" if g["gancho"].endswith("?") else ".")
        desc = f"{gan} Pick yours BEFORE the race starts 👇 Who did you pick?"
        tags = ["#football", "#soccer", "#marblerace", "#shorts", hashtag(g["evento"])] + \
               [hashtag(c["nombre"]) for c in g["competidores"][:3]]
        fijar = "Who did you pick… and did they win? 👇"
        archivo = ('short.mp4" (con relator: nuestro toque) o "short_sin_voz.mp4" + un sonido en tendencia desde el editor '
                   '(remix acelerado, cumbia o funk, como la competencia). Alterná para comparar')
    elif f in ("evolucion", "prime_now", "objeto"):
        cred = json.loads((out / "creditos.json").read_text())
        creditos = [linea(c) for c in cred.values()]
        twemoji = f == "evolucion"
        if f == "objeto":
            tags = ["#football", "#soccer", "#worldcup", "#shorts", "#evolution", "#nostalgia"]
        titulos = g["titulos"]
        desc = g["descripcion"]
        tags = ["#football", "#soccer", "#shorts", "#evolution" if f in ("evolucion", "objeto") else "#thenvsnow", "#nostalgia"]
        fijar = g["comentario_fijado"]
        archivo = ('short_sin_musica.mp4" + un sonido en tendencia desde el editor de Shorts (canción nostálgica o remix '
                   'acelerado: así lo hacen los que pegan). Si no encontrás uno bueno, subí "short.mp4')
    else:   # find_the_real
        creditos = [linea(CRED[r["foto"]]) for r in g["rondas"]]
        titulos = g["titulos"]
        desc = "Can you find the REAL one every round? The last one is only for the 1% 🧠"
        tags = ["#football", "#soccer", "#findthereal", "#shorts"] + [hashtag(r["nombre"]) for r in g["rondas"]]
        fijar = "Be honest… how many did you find? 0/1/2/3 👇"
        archivo = "short_con_beat.mp4 (o short_solo_efectos.mp4 + sonido de tendencia)"
    cred_txt = "\n".join(creditos)
    txt = "=== TÍTULO (elegí uno) ===\n" + "\n".join(f"{'ABC'[i]}) {t}" for i, t in enumerate(titulos[:3])) + f"""

=== DESCRIPCIÓN ===
{desc}

{' '.join(tags)}
""" + (f"""
Photo credits (Wikimedia Commons). Images were modified; the modified images are shared under CC BY-SA 4.0:
{cred_txt}
""" if creditos else "") + ("Flag icons: Twemoji (https://github.com/jdecked/twemoji), CC BY 4.0.\n" if twemoji else "") + f"""
=== COMENTARIO PARA FIJAR ===
{fijar}

=== CÓMO SUBIR (desde el celular) ===
1. Subí "{archivo}".
2. Pegá título, descripción y hashtags. Audiencia: "No es para niños".
3. Publicá en el horario del calendario (10:00 o 23:00, hora Argentina).
4. Fijá el comentario y respondé los primeros 5 comentarios en la primera hora.
5. A las 48 h anotá en produccion/registro.csv: vistas, % vieron vs. deslizaron, retención media y comentarios.
"""
    (out / "SUBIR.txt").write_text(txt, encoding="utf-8")
    return titulos[0]


if __name__ == "__main__":
    for p in sys.argv[1:]:
        print(p, "->", paquete(json.loads(Path(p).read_text())))
