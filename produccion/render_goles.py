#!/usr/bin/env python3
"""
GOALS BY AGE v2 (19/11, devolución del CEO: "más lento, más profesional, mejores jugadores, otra música").
Carrera de barras con el motor profesional (cairo: antialias, degradés, sombras, 60 fps):
- Una edad cada ~2,3 s con curva suave: los goles suben de a uno y se FRENAN en cada cumpleaños (se ve cada avance).
- Las barras cambian de lugar DESLIZÁNDOSE (resorte), la escala se agranda suave; color y escudo del CLUB de esa edad,
  bandera, cara grande con aro; "+N" goles del año; línea de tiempo abajo.
- Cambio de líder: cartel que entra deslizando + golpe de música. Final: "WHO'S THE GOAT?".
- Música original por código (musica_epica.py), distinta por semilla. DATOS REALES: assets/goles/goles_edad.json (Wikipedia).
Uso: python3 produccion/render_goles.py guion.json
guion: {"id", "jugadores": ["ronaldo", "messi", "lewandowski", "zlatan"], "desde": 17, "seg_por_edad": 2.3, "semilla": 0,
        "titulo": "GOALS BY AGE", "subtitulo": "..."}
"""
import json
import math
import sys
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import motor as M
import musica_epica as ME
import render_plinko as P

ROOT = Path(__file__).resolve().parent
W, H, FPS = M.W, M.H, M.FPS
DATOS = ROOT / "assets" / "goles" / "goles_edad.json"
CARA = {"messi": "lionel_messi", "ronaldo": "cristiano_ronaldo", "mbappe": "kylian_mbapp", "yamal": "lamine_yamal", "neymar": "neymar",
        "vinicius": "vin_cius_j_nior", "ronaldinho": "ronaldinho", "zidane": "zinedine_zidane", "beckham": "david_beckham",
        "henry": "thierry_henry", "zlatan": "zlatan_ibrahimovi", "lewandowski": "robert_lewandowski", "benzema": "karim_benzema",
        "kane": "harry_kane", "rooney": "wayne_rooney", "haaland": "erling_haaland"}
ACENTO = {"messi": (108, 180, 238), "ronaldo": (230, 40, 55), "mbappe": (60, 110, 230), "neymar": (250, 210, 40), "lewandowski": (230, 40, 70),
          "zlatan": (250, 210, 0), "henry": (60, 110, 230), "ronaldinho": (250, 210, 40), "benzema": (60, 110, 230), "kane": (240, 240, 245),
          "rooney": (240, 240, 245), "haaland": (120, 200, 255), "zidane": (60, 110, 230), "beckham": (240, 240, 245), "vinicius": (250, 210, 40)}
PAIS = {"messi": "AR", "ronaldo": "PT", "mbappe": "FR", "yamal": "ES", "neymar": "BR", "vinicius": "BR", "ronaldinho": "BR", "zidane": "FR",
        "beckham": "ENG", "henry": "FR", "zlatan": "SE", "lewandowski": "PL", "benzema": "FR", "kane": "ENG", "rooney": "ENG", "haaland": "NO"}
# club -> (escudo, color 1, color 2)
CLUB = {"Barcelona": ("barcelona", (165, 0, 68), (0, 77, 152)), "Paris Saint-Germain": ("psg", (0, 58, 112), (218, 41, 28)),
        "Inter Miami": ("inter_miami", (240, 150, 190), (35, 31, 32)), "Sporting CP": ("sporting", (0, 128, 87), (240, 240, 240)),
        "Manchester United": ("man_united", (200, 16, 30), (255, 210, 0)), "Real Madrid": ("real_madrid", (236, 236, 240), (254, 190, 16)),
        "Juventus": ("juventus", (36, 36, 40), (236, 236, 240)), "Al-Nassr": ("al_nassr", (250, 205, 0), (0, 52, 120)),
        "Monaco": ("monaco", (226, 6, 19), (240, 240, 240)), "Santos": ("santos", (236, 236, 240), (30, 30, 30)),
        "Al-Hilal": ("al_hilal", (0, 92, 185), (240, 240, 240)), "AC Milan": ("milan", (190, 16, 40), (30, 30, 30)),
        "Inter Milan": ("inter", (0, 82, 160), (30, 30, 30)), "Ajax": ("ajax", (210, 18, 46), (240, 240, 240)),
        "LA Galaxy": ("la_galaxy", (0, 36, 93), (255, 210, 0)), "Arsenal": ("arsenal", (220, 1, 7), (240, 240, 240)),
        "Bayern Munich": ("bayern", (220, 5, 45), (0, 102, 178)), "Borussia Dortmund": ("dortmund", (253, 225, 0), (30, 30, 30)),
        "Tottenham Hotspur": ("tottenham", (240, 240, 245), (19, 34, 87)), "Manchester City": ("man_city", (108, 171, 221), (28, 44, 91)),
        "Lyon": ("lyon", (0, 61, 145), (218, 41, 28)), "Everton": ("", (0, 51, 153), (240, 240, 240)),
        "Lech Poznań": ("", (0, 82, 160), (240, 240, 240)), "Znicz Pruszków": ("", (220, 30, 40), (240, 240, 240)),
        "Malmö FF": ("", (100, 170, 230), (240, 240, 240)), "Red Bull Salzburg": ("salzburg", (210, 20, 50), (240, 240, 240)),
        "Molde": ("", (0, 70, 150), (240, 240, 240)), "Bryne": ("", (220, 30, 40), (240, 240, 240)),
        "Al-Ittihad": ("", (250, 205, 0), (30, 30, 30)), "Chicago Fire": ("", (200, 16, 46), (0, 40, 85)), "Paris Saint-Germain (loan)": ("psg", (0, 58, 112), (218, 41, 28)),
        "Real Madrid (loan)": ("real_madrid", (236, 236, 240), (254, 190, 16))}

X0, Y0, FILA, GROSOR, D_CARA = 60, 700, 228, 132, 156
ANCHO = W - X0 - 190
INTRO, OUTRO = 1.6, 4.5
CREMA, ORO, GRIS = (245, 246, 250), (255, 200, 40), (150, 162, 185)


def mix(c, k):
    return tuple(int(max(0, min(255, v * k))) for v in c)


@lru_cache(maxsize=64)
def sup_cara(k):
    im = P.cara(CARA[k], D_CARA)
    aro = Image.new("RGBA", (D_CARA + 16, D_CARA + 16), (0, 0, 0, 0)); dr = ImageDraw.Draw(aro)
    dr.ellipse((0, 0, D_CARA + 15, D_CARA + 15), fill=(255, 255, 255, 255)); aro.alpha_composite(im, (8, 8))
    som = Image.new("RGBA", (aro.width + 40, aro.height + 40), (0, 0, 0, 0))
    som.paste((0, 0, 0, 150), (20, 26), aro.split()[3]); som = som.filter(ImageFilter.GaussianBlur(9)); som.alpha_composite(aro, (20, 20))
    return M.pil_a_cairo(som)


@lru_cache(maxsize=64)
def sup_escudo(club):
    arch = CLUB.get(club, ("",))[0]
    f = ROOT / "assets" / "escudos" / f"{arch}.png"
    return M.pil_a_cairo(M.escudo_en_disco(str(f), 64)) if arch and f.exists() else None


@lru_cache(maxsize=32)
def sup_bandera(k):
    f = ROOT / "assets" / "banderas" / f"{PAIS.get(k, '')}_160.png"
    if not f.exists():
        return None
    b = Image.open(f).convert("RGBA"); b = b.resize((60, int(60 * b.height / b.width)), Image.LANCZOS)
    m = Image.new("L", b.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, b.width - 1, b.height - 1), 7, fill=255)
    b.putalpha(m)
    return M.pil_a_cairo(b)


def cargar(g):
    d = json.loads(DATOS.read_text())
    js = []
    for k in g["jugadores"]:
        x = d["jugadores"][k]
        acum = {int(e): v for e, v in x["acumulado_por_edad"].items()}
        js.append(dict(k=k, nombre=x["nombre"], acum=acum, e0=min(acum), edad_max=max(acum), activo=x.get("activo", False),
                       club={int(e): c for e, c in x.get("club_por_edad", {}).items()}))
    return js


def goles(j, e):
    """Goles acumulados a una edad fraccionaria: dentro de cada año sube con curva suave (arranca y frena en el cumpleaños)."""
    e = min(e, j["edad_max"])
    a = math.floor(e)
    prev = j["acum"].get(a, 0 if a < j["e0"] else j["acum"][max(k for k in j["acum"] if k <= a)])
    nxt = j["acum"].get(a + 1, prev)
    return prev + (nxt - prev) * M.suave(e - a)


def club_de(j, e):
    ks = sorted(j["club"])
    if not ks:
        return None
    a = min(max(int(e) + (1 if e - int(e) > 0.5 else 0), ks[0]), ks[-1])
    return j["club"].get(a) or j["club"][max(k for k in ks if k <= a)]


class Video:
    def __init__(self, g):
        self.g = g
        self.js = cargar(g)
        self.desde = g.get("desde", min(j["e0"] for j in self.js))
        self.hasta = max(j["edad_max"] for j in self.js)
        self.spe = g.get("seg_por_edad", 2.3)
        self.dur = round(INTRO + (self.hasta - self.desde + 1) * self.spe + OUTRO, 2)
        self.fondo = self.armar_fondo()
        self.res = [M.Resorte(Y0 + i * FILA, 7.0) for i in range(len(self.js))]
        self.escala = M.Resorte(80.0, 2.5)
        self.cambios = self.lideres()

    def edad(self, t):
        return min(self.hasta + 1, self.desde + max(0.0, t - INTRO) / self.spe)

    def lideres(self):
        out, prev, e = [], None, self.desde
        while e <= self.hasta + 1:
            v = [goles(j, e) for j in self.js]
            lid = int(np.argmax(v)) if max(v) > 0 else None
            if lid is not None and prev is not None and lid != prev and v[lid] - v[prev] >= 1:
                out.append((INTRO + (e - self.desde) * self.spe, lid)); prev = lid
            elif prev is None and lid is not None and v[lid] >= 1:
                prev = lid
            e += 0.01
        return out

    def armar_fondo(self):
        s = M.superficie_fondo((6, 9, 20), (24, 36, 74), cy=0.42)
        L = M.Lienzo(s)
        for i in range(9):                                                     # rayos de luz diagonales, muy suaves
            x = -300 + i * 230
            L.c.new_path(); L.c.move_to(x, 0); L.c.line_to(x + 120, 0); L.c.line_to(x + 620, H); L.c.line_to(x + 500, H); L.c.close_path()
            L.rgba((255, 255, 255), 0.018); L.c.fill()
        L.rect_redondo(36, 640, W - 72, 985, 34, (255, 255, 255), 0.035, borde=(255, 255, 255), ancho=2)   # panel del gráfico
        return L.s

    def cuadro(self, t, dt):
        L = M.Lienzo(self.fondo); c = L.c
        e = self.edad(t)
        vals = [goles(j, e) for j in self.js]
        tope = self.escala.paso(max(60.0, max(vals) * 1.15), dt)
        orden = sorted(range(len(self.js)), key=lambda i: -vals[i])
        ys = [0] * len(self.js)
        for r, i in enumerate(orden):
            ys[i] = self.res[i].paso(Y0 + r * FILA, dt)
        # líneas guía de la escala
        paso = next(p for p in (20, 50, 100, 200, 250, 500) if tope / p <= 5)
        guias = []
        for k in range(1, int(tope / paso) + 1):
            x = X0 + ANCHO * k * paso / tope
            L.linea(x, 670, x, 1600, (255, 255, 255), 2, 0.07); guias.append((x, k * paso))
        textos = []
        for i in sorted(range(len(self.js)), key=lambda i: ys[i]):
            j = self.js[i]; y = ys[i] + 40
            club = club_de(j, e)
            c1, c2 = (CLUB[club][1], CLUB[club][2]) if club in CLUB else (ACENTO.get(j["k"], (200, 200, 200)), (240, 240, 240))
            largo = max(150, ANCHO * vals[i] / tope)
            for k_, a_ in ((10, 0.10), (6, 0.14), (3, 0.18)):                  # sombra suave
                L.rect_redondo(X0 + 4, y + k_, largo, GROSOR, 30, (0, 0, 0), a_)
            gr = M.cairo.LinearGradient(0, y, 0, y + GROSOR)
            for pos, k_ in ((0, 1.18), (0.45, 1.0), (1, 0.62)):
                cc = mix(c1, k_); gr.add_color_stop_rgb(pos, *[v / 255 for v in cc])
            M.Lienzo.rect_redondo(L, X0, y, largo, GROSOR, 30, None)
            c.set_source(gr); c.fill()
            L.rect_redondo(X0 + 16, y + GROSOR - 26, largo - 32, 10, 5, c2, 0.9)  # franja con el 2.º color del club
            gl = M.cairo.LinearGradient(0, y, 0, y + GROSOR * 0.45)            # brillo de arriba
            gl.add_color_stop_rgba(0, 1, 1, 1, 0.30); gl.add_color_stop_rgba(1, 1, 1, 1, 0.0)
            M.Lienzo.rect_redondo(L, X0 + 4, y + 4, largo - 8, GROSOR * 0.45, 26, None); c.set_source(gl); c.fill()
            L.rect_redondo(X0, y, largo, GROSOR, 30, None, borde=(255, 255, 255), ancho=2)
            b = sup_bandera(j["k"])
            if b is not None:
                M.imagen(L, b, X0 + 52, y + GROSOR / 2 - 6)
            fx = X0 + largo + 10
            M.imagen(L, sup_cara(j["k"]), fx, y + GROSOR / 2 + 4)
            esc = sup_escudo(club) if club else None
            if esc is not None:
                M.imagen(L, esc, fx + 58, y + GROSOR / 2 + 58)
            claro = sum(c1) / 3 > 170
            num = f"{int(round(vals[i]))}"
            textos.append(("num", num, X0 + largo - 78, y + GROSOR / 2 - 4, (25, 25, 32) if claro else CREMA, largo))
            sub = club.replace(" (loan)", "").upper() if club else ""
            textos.append(("nom", j["nombre"].upper(), X0 + 6, y - 32, sub))
            ent = math.floor(e)
            if self.desde < ent <= j["edad_max"] and e - ent < 1.2:
                gan = j["acum"].get(ent, 0) - j["acum"].get(ent - 1, 0)
                if gan > 0:
                    textos.append(("mas", f"+{gan}", W - 70, y - 30, min(1, (1.2 - (e - ent)) * 3)))
            if j["activo"] and e >= j["edad_max"] + 0.6:
                textos.append(("now", "TODAY", X0 + 6, y - 32, j["nombre"].upper()))
        # línea de tiempo
        ty = 1672
        L.linea(90, ty, W - 90, ty, (255, 255, 255), 8, 0.15)
        prog = (min(e, self.hasta + 1) - self.desde) / (self.hasta + 1 - self.desde)
        L.linea(90, ty, 90 + (W - 180) * prog, ty, ORO, 8, 0.95)
        L.circulo(90 + (W - 180) * prog, ty, 15, ORO, borde=(255, 255, 255), ancho=4)
        marcas = [a for a in range(self.desde, self.hasta + 2) if a % 5 == 0]
        for a in marcas:
            x = 90 + (W - 180) * (a - self.desde) / (self.hasta + 1 - self.desde)
            L.circulo(x, ty, 5, (255, 255, 255), 0.6)
        # cartel de cambio de líder (entra desde abajo)
        cartel = None
        for tc, li in self.cambios:
            u = t - tc
            if -0.05 <= u < 2.4:
                cartel = (li, u)
        if cartel:
            li, u = cartel
            k_ = M.suave(min(1, u / 0.35)) * (1 - M.suave(max(0, (u - 2.0) / 0.4)))
            club = club_de(self.js[li], e); col = CLUB.get(club, (0, ACENTO.get(self.js[li]["k"], ORO)))[1]
            yb = 1880 - 60 * k_
            L.rect_redondo(80, yb - 56, W - 160, 104, 52, (10, 14, 28), 0.92 * k_, borde=ORO, ancho=4)
            if u < 0.25:
                L.brillo(W / 2, 1180, 900, ORO, 0.22 * (1 - u / 0.25))
        im = L.a_pil()
        d = ImageDraw.Draw(im)
        # encabezado
        M.texto(d, (W / 2, 205), self.g.get("titulo", "GOALS BY AGE"), M.ajustar(self.g.get("titulo", "GOALS BY AGE"), 150, W - 120), CREMA, 0)
        d.rounded_rectangle((W / 2 - 300, 268, W / 2 + 300, 276), 4, fill=ORO)
        sub = self.g.get("subtitulo") or "  ·  ".join(j["nombre"].upper() for j in self.js)
        M.texto(d, (W / 2, 330), sub, M.ajustar(sub, 46, W - 140, M.ARCHIVO), GRIS, 0, cual=M.ARCHIVO)
        # edad (late un poco en cada cumpleaños)
        ent = min(math.floor(e), self.hasta)
        pop = 1 + 0.10 * max(0.0, 1 - (e - math.floor(e)) * 5) if e < self.hasta + 1 else 1
        M.texto(d, (W / 2, 445), "AGE", 46, GRIS, 0, cual=M.ARCHIVO)
        M.texto(d, (W / 2, 548), f"{ent}", int(150 * pop), ORO, 0)
        for x, v in guias:
            M.texto(d, (x, 660), f"{v}", 26, (150, 160, 180), 0, cual=M.ARCHIVO)
        for tx in textos:
            if tx[0] == "num":
                _, s, x, y, col, largo = tx
                tam = 70
                if largo < M.fuente(tam).getlength(s) + 150:
                    x = X0 + largo + 10 + D_CARA / 2 + 30 + M.fuente(tam).getlength(s) / 2; col = CREMA
                else:
                    x = x - M.fuente(tam).getlength(s) / 2
                M.texto(d, (x, y), s, tam, col, 0)
            elif tx[0] == "nom":
                _, s, x, y, sub_ = tx
                M.texto(d, (x, y), s, 48, CREMA, 0, anchor="lm")
                if sub_:
                    M.texto(d, (x + M.fuente(48).getlength(s) + 18, y + 4), sub_, 26, GRIS, 0, anchor="lm", cual=M.ARCHIVO)
            elif tx[0] == "mas":
                _, s, x, y, a_ = tx
                col = tuple(int(v * a_ + 20 * (1 - a_)) for v in (90, 235, 130))
                M.texto(d, (x, y), s, 44, col, 0, anchor="rm")
        for a in marcas:
            x = 90 + (W - 180) * (a - self.desde) / (self.hasta + 1 - self.desde)
            M.texto(d, (x, 1708), f"{a}", 26, GRIS, 0, cual=M.ARCHIVO)
        if cartel:
            li, u = cartel
            k_ = M.suave(min(1, u / 0.35)) * (1 - M.suave(max(0, (u - 2.0) / 0.4)))
            if k_ > 0.05:
                s = f"{self.js[li]['nombre'].upper()} TAKES THE LEAD!"
                M.texto(d, (W / 2, 1880 - 60 * k_ - 6), s, M.ajustar(s, 64, W - 230), tuple(int(v * k_) for v in ORO), 0)
        if t >= self.dur - OUTRO + 0.6:
            a_ = min(1, (t - (self.dur - OUTRO + 0.6)) / 0.4)
            capa = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dc = ImageDraw.Draw(capa)
            dc.rounded_rectangle((80, 1768, W - 80, 1880), 56, fill=(10, 14, 28, int(235 * a_)), outline=ORO + (int(255 * a_),), width=4)
            im = im.convert("RGBA"); im.alpha_composite(capa); d = ImageDraw.Draw(im)
            M.texto(d, (W / 2, 1810), "WHO'S THE GOAT?", 62, tuple(int(v * a_) for v in ORO), 0)
            M.texto(d, (W / 2, 1853), "COMMENT BELOW", 26, tuple(int(v * a_) for v in CREMA), 0, cual=M.ARCHIVO)
            im = im.convert("RGB")
        return im

    def audio(self):
        dur = self.dur; sr = M.SR; n = int(dur * sr)
        mu = ME.pista(dur, self.g.get("semilla", 0), golpes=[tc for tc, _ in self.cambios])
        fx = np.zeros(n, np.float32)
        for a in range(self.desde + 1, self.hasta + 2):                         # tic suave en cada cumpleaños
            i = int((INTRO + (a - self.desde) * self.spe) * sr)
            if i < n:
                s = M.pluck(1760, 0.12, 0.12); fx[i:i + len(s)] += s[: n - i]
        con = np.tanh((mu * 0.9 + fx) * 1.05) * 0.92
        return con, np.tanh(fx * 1.1) * 0.8


def main(guion):
    g = json.loads(Path(guion).read_text())
    out = ROOT / "salida" / g["id"]; out.mkdir(parents=True, exist_ok=True)
    V = Video(g)
    mudo = out / "mudo.mp4"
    vid = M.Video(mudo)
    dt = 1 / FPS
    for f in range(int(round(V.dur * FPS))):
        vid.cuadro(V.cuadro(f / FPS, dt))
    vid.cerrar()
    con, solo = V.audio()
    M.mezclar(out, mudo, {"short.mp4": con, "short_solo_efectos.mp4": solo})
    print(out / "short.mp4", V.dur, "s", "cambios de líder", [(round(tc, 1), V.js[i]["nombre"]) for tc, i in V.cambios])


if __name__ == "__main__":
    main(sys.argv[1])
