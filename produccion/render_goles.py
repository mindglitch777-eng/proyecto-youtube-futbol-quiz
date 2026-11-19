#!/usr/bin/env python3
"""
GOALS BY AGE (19/11, pedido del CEO, idea de la investigación 2.0: un video así hizo 6,45 M y 1.870 comentarios).
Carrera de barras: goles oficiales ACUMULADOS (club + selección) de 4 superestrellas/leyendas, edad por edad. Arriba, un contador
grande de EDAD; cada barra lleva la cara del jugador y su número. Cuando cambia el líder: destello + "{NOMBRE} TAKES THE LEAD!".
Los que todavía juegan se frenan en su edad de hoy ("NOW"). Final: ranking + "WHO'S THE GOAT? COMMENT 👇".
DATOS REALES: assets/goles/goles_edad.json (goles_edad.py, desde Wikipedia). Nunca se inventa un número.
Uso: python3 produccion/render_goles.py guion.json
guion: {"id", "jugadores": ["messi", "ronaldo", "mbappe", "yamal"], "desde": 17, "seg_por_edad": 1.15, "musica", "fondo", "textos"}
"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

import gancho as G
import motor as M
import render_plinko as P
import render_rueda as R

ROOT = Path(__file__).resolve().parent
W, H, FPS = R.W, R.H, R.FPS
DATOS = ROOT / "assets" / "goles" / "goles_edad.json"
CARA = {"messi": "lionel_messi", "ronaldo": "cristiano_ronaldo", "mbappe": "kylian_mbapp", "yamal": "lamine_yamal", "neymar": "neymar",
        "vinicius": "vin_cius_j_nior", "ronaldinho": "ronaldinho", "zidane": "zinedine_zidane", "beckham": "david_beckham",
        "henry": "thierry_henry", "zlatan": "zlatan_ibrahimovi"}
COLOR = {"messi": (108, 180, 238), "ronaldo": (230, 40, 55), "mbappe": (40, 80, 200), "yamal": (250, 190, 30), "neymar": (30, 170, 80),
         "vinicius": (240, 240, 245), "ronaldinho": (255, 220, 40), "zidane": (30, 50, 140), "beckham": (200, 30, 40), "henry": (200, 30, 60),
         "zlatan": (250, 210, 0)}
# 19/11 (grabación del CEO): la barra toma los colores del CLUB de esa edad, con escudo y bandera; "+N" goles del año
CLUB = {"Barcelona": ("barcelona", (165, 0, 68), (0, 77, 152)), "Paris Saint-Germain": ("psg", (0, 65, 112), (218, 41, 28)),
        "Inter Miami": ("inter_miami", (247, 181, 205), (35, 31, 32)), "Sporting CP": ("sporting", (0, 128, 87), (255, 255, 255)),
        "Manchester United": ("man_united", (218, 41, 28), (255, 229, 0)), "Real Madrid": ("real_madrid", (245, 245, 245), (254, 190, 16)),
        "Juventus": ("juventus", (30, 30, 30), (245, 245, 245)), "Al-Nassr": ("al_nassr", (255, 220, 0), (0, 52, 120)),
        "Monaco": ("monaco", (226, 6, 19), (245, 245, 245)), "Santos": ("santos", (245, 245, 245), (30, 30, 30)),
        "Al-Hilal": ("al_hilal", (0, 92, 185), (245, 245, 245)), "AC Milan": ("milan", (200, 16, 46), (30, 30, 30)),
        "Inter Milan": ("inter", (0, 82, 160), (30, 30, 30)), "Ajax": ("ajax", (210, 18, 46), (245, 245, 245)),
        "LA Galaxy": ("la_galaxy", (0, 36, 93), (255, 210, 0)), "Arsenal": ("arsenal", (239, 1, 7), (245, 245, 245)),
        "Flamengo": ("flamengo", (200, 16, 46), (30, 30, 30))}
PAIS = {"messi": "AR", "ronaldo": "PT", "mbappe": "FR", "yamal": "ES", "neymar": "BR", "vinicius": "BR", "ronaldinho": "BR",
        "zidane": "FR", "beckham": "ENG", "henry": "FR", "zlatan": "SE"}
BAR_X0, BAR_Y0, BAR_H, BAR_GAP = 150, 700, 185, 95
D_CARA = 175
INTRO, OUTRO = 1.2, 3.0


def cargar(g):
    d = json.loads(DATOS.read_text())
    js = []
    for k in g["jugadores"]:
        x = d["jugadores"][k]
        acum = {int(e): v for e, v in x["acumulado_por_edad"].items()}
        js.append(dict(k=k, nombre=x["nombre"], acum=acum, edad_max=max(acum), activo=x.get("activo", False),
                       club={int(e): c.replace(" (loan)", "") for e, c in x.get("club_por_edad", {}).items()}))
    desde = g.get("desde", 17)
    hasta = max(j["edad_max"] for j in js)
    return js, desde, hasta


def valor(j, edad_f):
    """Goles acumulados a una edad fraccionaria (interpola entre cumpleaños; se frena en su edad de hoy)."""
    e = min(edad_f, j["edad_max"])
    a = int(e); b = min(a + 1, j["edad_max"])
    va, vb = j["acum"].get(a, 0 if a < min(j["acum"]) else j["acum"][max(k for k in j["acum"] if k <= a)]), j["acum"].get(b, 0)
    if b not in j["acum"]:
        vb = va
    return va + (vb - va) * (e - a)


def lideres(js, desde, hasta):
    """Momentos (edad) en que cambia el líder: para el cartel y el sonido."""
    out, prev = [], None
    paso = 0.02
    e = desde
    while e <= hasta + 1e-6:
        vals = [valor(j, e) for j in js]
        lid = int(np.argmax(vals)) if max(vals) > 0 else None
        if lid is not None and prev is not None and lid != prev and vals[lid] - vals[prev] >= 0.5:
            out.append((e, lid))
        if lid is not None:
            prev = lid
        e += paso
    return out


def armar(g):
    js, desde, hasta = cargar(g)
    spe = g.get("seg_por_edad", 1.15)
    dur = round(INTRO + (hasta - desde) * spe + OUTRO, 2)
    caras = {j["k"]: P.con_aro(P.cara(CARA[j["k"]], D_CARA), COLOR[j["k"]], 8) for j in js}
    escudos, banderas = {}, {}
    for c, (arch, _, _) in CLUB.items():
        f = ROOT / "assets" / "escudos" / f"{arch}.png"
        if f.exists():
            e = Image.open(f).convert("RGBA"); e.thumbnail((74, 74), Image.LANCZOS); escudos[c] = e
    for j in js:
        f = ROOT / "assets" / "banderas" / f"{PAIS[j['k']]}_160.png"
        if f.exists():
            b = Image.open(f).convert("RGBA"); b.thumbnail((96, 64), Image.LANCZOS); banderas[j["k"]] = b
    return dict(escudos=escudos, banderas=banderas, js=js, desde=desde, hasta=hasta, spe=spe, dur=dur, caras=caras, fondo=R.fondo(g.get("fondo", "estadio_0")).copy(),
                cambios=lideres(js, desde, hasta))


def edad_en(A, t):
    return min(A["hasta"], A["desde"] + max(0.0, t - INTRO) / A["spe"])


def cuadro(g, A, t):
    im = A["fondo"].copy()
    im.alpha_composite(Image.new("RGBA", (W, H), (8, 12, 22, 150)))
    d = ImageDraw.Draw(im, "RGBA")
    e = edad_en(A, t)
    js = A["js"]
    vals = [valor(j, e) for j in js]
    tope = max(60.0, max(vals) * 1.08)
    orden = sorted(range(len(js)), key=lambda i: -vals[i])
    pos = {i: r for r, i in enumerate(orden)}
    # contador de edad
    # título fijo (como el original: se lee siempre qué se compara)
    P.texto(d, (W / 2, 210), A["textos"]["gancho"], 118, (255, 230, 40), 13)
    sub = A["textos"]["apuesta"]; ts = 50
    while ts > 30 and P.fuente(ts).getlength(sub) > W - 90:
        ts -= 2
    d.rounded_rectangle([40, 285, W - 40, 355], 35, fill=(15, 20, 35, 220), outline=(255, 230, 40, 255), width=4)
    P.texto(d, (W / 2, 320), sub, ts, (255, 255, 255), 5)
    P.texto(d, (W / 2, 500), f"{int(e)} YEARS OLD", 110, (255, 255, 255), 12)
    ancho = W - BAR_X0 - 70 - D_CARA
    for i, j in enumerate(js):
        y = BAR_Y0 + pos[i] * (BAR_H + BAR_GAP)
        largo = max(8, ancho * vals[i] / tope)
        ea = max(min(j["club"] or [0]), min(int(e), max(j["club"] or [0])))
        club = j["club"].get(ea) or j["club"].get(max([k_ for k_ in j["club"] if k_ <= ea] or [ea]))
        c1, c2 = (CLUB[club][1], CLUB[club][2]) if club in CLUB else (COLOR[j["k"]], (255, 255, 255))
        d.rounded_rectangle([BAR_X0, y, BAR_X0 + largo, y + BAR_H], 24, fill=c1 + (240,), outline=(255, 255, 255, 210), width=4)
        if largo > 60:
            d.rectangle([BAR_X0 + 14, y + BAR_H - 34, BAR_X0 + largo - 14, y + BAR_H - 16], fill=c2 + (230,))
        if j["k"] in A["banderas"]:
            b = A["banderas"][j["k"]]; im.alpha_composite(b, (int(BAR_X0 - b.width - 22), int(y + BAR_H / 2 - b.height / 2)))
        cara = A["caras"][j["k"]]
        cx = int(BAR_X0 + largo - cara.width / 2 + 40)
        im.alpha_composite(cara, (cx, int(y + BAR_H / 2 - cara.height / 2)))
        if club in A["escudos"]:
            es = A["escudos"][club]; im.alpha_composite(es, (cx + cara.width - es.width + 6, int(y + BAR_H / 2 + cara.height / 2 - es.height + 6)))
        d = ImageDraw.Draw(im, "RGBA")
        # "+N" goles del último año (aparece al cumplir años y se apaga)
        ent = int(e)
        if ent > A["desde"] and e < j["edad_max"] + 0.999 and ent <= j["edad_max"]:
            gan = j["acum"].get(ent, 0) - j["acum"].get(ent - 1, 0)
            fr = e - ent
            if gan > 0 and fr < 0.8:
                P.texto(d, (W - 90, y - 30), f"+{gan}", 50, (90, 240, 120), 7)
        P.texto(d, (BAR_X0 + 20 + P.fuente(52).getlength(j["nombre"].upper()) / 2, y - 30), j["nombre"].upper(), 52, (255, 255, 255), 7)
        num = f"{int(round(vals[i]))}"
        tn = P.fuente(70).getlength(num)
        if largo > tn + 90:                                                    # el número dentro de la barra (como el original), si entra
            P.texto(d, (BAR_X0 + largo - 60 - tn / 2, y + BAR_H / 2 - 8), num, 70, (255, 255, 255), 8)
        else:
            P.texto(d, (BAR_X0 + largo + cara.width + 50 + tn / 2, y + BAR_H / 2), num, 70, (255, 255, 255), 8)
        if j["activo"] and e >= j["edad_max"] + 0.5 and largo > tn + 230:
            P.texto(d, (BAR_X0 + 75, y + BAR_H / 2 - 8), "NOW", 40, (255, 255, 255), 6)
    # cambio de líder
    for ec, li in A["cambios"]:
        tc = INTRO + (ec - A["desde"]) * A["spe"]
        if 0 <= t - tc < 1.1:
            if t - tc < 0.15:
                im.alpha_composite(Image.new("RGBA", (W, H), COLOR[js[li]["k"]] + (60,))); d = ImageDraw.Draw(im, "RGBA")
            txt = f"{js[li]['nombre'].upper()} TAKES THE LEAD!"
            tam = 78
            while tam > 44 and P.fuente(tam).getlength(txt) > W - 80:
                tam -= 4
            P.texto(d, (W / 2, 1850), txt, tam, (255, 230, 40), 10)
    if t >= A["dur"] - OUTRO + 0.4:
        P.texto(d, (W / 2, 1790), "WHO'S THE GOAT?", 84, (255, 230, 40), 10)
        P.texto(d, (W / 2, 1862), "COMMENT NOW", 56, (255, 255, 255), 8)
    return im.convert("RGB")


def audio(g, A):
    dur = A["dur"]; sr = M.SR; n = int(dur * sr); fx = np.zeros(n, np.float32)

    def add(t0, sig, v=1.0):
        a = int(t0 * sr)
        if a >= n:
            return
        b = min(n, a + len(sig)); fx[a:b] += sig[: b - a] * v
    for k in range(A["hasta"] - A["desde"] + 1):
        add(INTRO + k * A["spe"], M.ding(0.25), 0.18)                       # tic de cada cumpleaños
    for ec, _ in A["cambios"]:
        add(INTRO + (ec - A["desde"]) * A["spe"], M.boom(0.6), 0.35); add(INTRO + (ec - A["desde"]) * A["spe"], M.ding(0.8), 0.5)
    add(0, G.silbato(sr), 1.0)
    mu = P.musica(g, dur)
    return np.tanh((mu * 0.75 + fx) * 1.1) * 0.9, np.tanh(fx * 1.1) * 0.85


def main(guion):
    g = json.loads(Path(guion).read_text())
    out = ROOT / "salida" / g["id"]; out.mkdir(parents=True, exist_ok=True)
    A = armar(g)
    A["textos"] = g.get("textos") or dict(gancho="GOALS BY AGE", apuesta=" vs ".join(j["nombre"].upper() for j in A["js"]))
    mudo = out / "mudo.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", str(mudo)], stdin=subprocess.PIPE)
    for f in range(int(round(A["dur"] * FPS))):
        p.stdin.write(np.asarray(cuadro(g, A, f / FPS), np.uint8).tobytes())
    p.stdin.close(); p.wait()
    con, solo = audio(g, A)
    M.mezclar(out, mudo, {"short.mp4": con, "short_solo_efectos.mp4": solo})
    print(out / "short.mp4", A["dur"], "s", "cambios de líder", [(round(e, 1), A["js"][i]["nombre"]) for e, i in A["cambios"]])


if __name__ == "__main__":
    main(sys.argv[1])
