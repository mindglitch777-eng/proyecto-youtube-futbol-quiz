#!/usr/bin/env python3
"""
"WHO WINS THE RACE?" v2: carrera de canicas con física real (pymunk), temática y circuito armado por módulos.

Emociones: elegí uno en el cuadro 0, adelantamientos ("TAKES THE LEAD!"), eliminación del último en cada control,
aceleradores, último tramo con latido, PHOTO FINISH en cámara lenta, ganador con confeti, loop al cuadro 0.
Competidores: jugadores (cara), países (bandera Twemoji) o clubes (colores + nombre, sin escudos).

Uso: python3 render_carrera.py guiones/carrera_01.json
Salida: salida/<id>/short.mp4
"""
import json
import math
import random
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np
import pymunk
from PIL import Image, ImageDraw, ImageFilter

from banderas import png as bandera_png
from render_find_the_real import BLANCO, FPS, H, SR, W, ROOT, ajustar, fuente, texto
from render_fusion import beat, efectos, leer_wav, voces_edge

SUB = 4                                   # estados de física guardados por cuadro (para cámara lenta)
DT = 1 / (FPS * SUB * 2)
PALETAS = {
    "oro": dict(fondo=(18, 14, 8), fondo2=(52, 40, 12), pista=(205, 170, 80), clavo=(240, 210, 130), acento=(255, 210, 63)),
    "noche": dict(fondo=(10, 14, 30), fondo2=(26, 40, 84), pista=(110, 140, 210), clavo=(170, 190, 240), acento=(80, 220, 255)),
    "cancha": dict(fondo=(8, 30, 20), fondo2=(20, 84, 52), pista=(180, 230, 190), clavo=(230, 255, 235), acento=(255, 230, 80)),
    "fuego": dict(fondo=(28, 8, 8), fondo2=(90, 22, 14), pista=(255, 140, 70), clavo=(255, 200, 150), acento=(255, 220, 90)),
    "violeta": dict(fondo=(18, 8, 30), fondo2=(60, 22, 96), pista=(190, 140, 255), clavo=(225, 200, 255), acento=(120, 255, 200)),
}
ROJO = (240, 70, 70)


# ------------------------------------------------------------------ competidores
def _circular(rgb, d):
    im = rgb.convert("RGBA").resize((d, d), Image.LANCZOS)
    m = Image.new("L", (d * 3, d * 3), 0); ImageDraw.Draw(m).ellipse((0, 0, d * 3 - 1, d * 3 - 1), fill=255)
    im.putalpha(m.resize((d, d), Image.LANCZOS))
    return im


def cara_jugador(nombre, d):
    import csv
    sel = json.loads((ROOT / "assets" / "mejor_foto.json").read_text()).get(nombre)
    filas = [f for f in csv.DictReader(open(ROOT / "assets" / "poses.csv")) if f["jugador"] == nombre]
    f = next((f for f in filas if sel and f["foto"] == sel["foto"]), None) or max(filas, key=lambda f: float(f["puntaje"]))
    img = cv2.imread(str(next((ROOT / "assets" / "fotos").glob(f["foto"] + ".*"))))
    x, y, w, h = json.loads(f["cara"])[:4]
    cx, cy, s = x + w / 2, y + h * 0.48, max(w, h) * 1.45
    hh, ww = img.shape[:2]
    s = min(s, hh, ww)
    x0 = int(np.clip(cx - s / 2, 0, ww - s)); y0 = int(np.clip(cy - s / 2, 0, hh - s))
    crop = img[y0:y0 + int(s), x0:x0 + int(s)]
    return _circular(Image.fromarray(cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)), d)


def bola_bandera(pais, d):
    fl = Image.open(bandera_png(pais, 320)).convert("RGBA")
    bb = fl.getbbox(); fl = fl.crop(bb)
    w, h = fl.size; s = min(w, h)
    fl = fl.crop(((w - s) // 2, (h - s) // 2, (w + s) // 2, (h + s) // 2))
    base = Image.new("RGBA", fl.size, (255, 255, 255, 255)); base.alpha_composite(fl)
    return _circular(base, d)


def bola_club(colores, estilo, corto, d):
    k = 4
    im = Image.new("RGB", (d * k, d * k), tuple(colores[0])); dr = ImageDraw.Draw(im)
    c2 = tuple(colores[1]) if len(colores) > 1 else tuple(colores[0])
    D = d * k
    if estilo == "rayas":
        for i in range(0, 7, 2):
            dr.rectangle((i * D / 7, 0, (i + 1) * D / 7, D), fill=c2)
    elif estilo == "mitades":
        dr.rectangle((D / 2, 0, D, D), fill=c2)
    elif estilo == "banda":
        dr.polygon([(D * 0.62, 0), (D * 0.9, 0), (D * 0.38, D), (D * 0.1, D)], fill=c2)
    elif estilo == "franja":
        dr.rectangle((0, D * 0.38, D, D * 0.62), fill=c2)
    tam = ajustar(corto, int(D * 0.30), D * 0.84)
    dr.text((D / 2, D / 2), corto, font=fuente(tam), fill=(255, 255, 255), stroke_width=int(D * 0.035),
            stroke_fill=(0, 0, 0), anchor="mm")
    return _circular(im, d)


def competidores(g, d):
    out = []
    for c in g["competidores"]:
        if c["tipo"] == "jugador":
            img = cara_jugador(c["nombre"], d)
        elif c["tipo"] == "pais":
            img = bola_bandera(c["pais"], d)
        else:
            img = bola_club(c["colores"], c.get("estilo", "liso"), c["corto"], d)
        out.append(dict(c, img=img, color=tuple(c.get("anillo", c.get("colores", [[255, 255, 255]])[0]))))
    return out


# ------------------------------------------------------------------ pista por módulos
class Pista:
    def __init__(self, space, modulos, rnd):
        self.space, self.rnd = space, rnd
        self.segs, self.clavos, self.giros, self.rebot, self.boost, self.controles, self.marcas = [], [], [], [], [], [], []
        y = 380
        self.seg((40, -600), (40, 99999)); self.seg((W - 40, -600), (W - 40, 99999))
        for m in modulos:
            self.marcas.append((y, m))
            y = getattr(self, "m_" + m)(y)
            self.controles.append(y)
        self.meta = y + 360
        self.seg((40, y), (W / 2 - 150, self.meta - 40)); self.seg((W - 40, y), (W / 2 + 150, self.meta - 40))
        self.seg((40, self.meta + 260), (W - 40, self.meta + 260))
        self.controles = self.controles[:-1]

    def seg(self, a, b, g=10, el=0.45, body=None):
        s = pymunk.Segment(body or self.space.static_body, a, b, g); s.elasticity = el; s.friction = 0.6
        self.space.add(s)
        if body is None:
            self.segs.append((a, b, g))
        return s

    def clavo(self, x, y, r=17, el=0.55):
        c = pymunk.Circle(self.space.static_body, r, (x, y)); c.elasticity = el; c.friction = 0.4
        self.space.add(c); self.clavos.append((x, y, r))

    # cada módulo recibe la y de arriba y devuelve la y de abajo
    def m_clavos(self, y, filas=6):
        for k in range(filas):
            xs = np.linspace(220, 860, 4) if k % 2 == 0 else np.linspace(220, 860, 4)[:-1] + 107
            for x in xs:
                self.clavo(x + self.rnd.uniform(-12, 12), y + 120 + k * 200)
        return y + filas * 200 + 120

    def m_zigzag(self, y, n=4):
        for k in range(n):
            if k % 2 == 0:
                self.seg((40, y + k * 400), (W - 340, y + k * 400 + 170))
            else:
                self.seg((W - 40, y + k * 400), (340, y + k * 400 + 170))
        return y + n * 400 + 120

    def _giro(self, x, y, largo, w, brazos=2):
        b = pymunk.Body(body_type=pymunk.Body.KINEMATIC); b.position = (x, y); b.angular_velocity = w
        self.space.add(b)
        for k in range(brazos):
            a = math.pi * k / brazos
            c, s = math.cos(a) * largo, math.sin(a) * largo
            self.seg((-c, -s), (c, s), 12, 0.5, body=b)
        self.giros.append((b, largo, brazos))

    def m_aspas(self, y):
        self._giro(W / 2, y + 360, 300, self.rnd.choice([-1, 1]) * 2.2)
        return y + 760

    def m_molinos(self, y):
        s = self.rnd.choice([-1, 1])
        self._giro(W * 0.31, y + 260, 150, 3.0 * s, 3); self._giro(W * 0.69, y + 260, 150, -3.0 * s, 3)
        self._giro(W * 0.5, y + 620, 150, 3.0 * s, 3)
        return y + 880

    def m_rebotadores(self, y):
        for x, dy in ((W * 0.28, 200), (W * 0.72, 200), (W * 0.5, 450), (W * 0.22, 700), (W * 0.78, 700)):
            c = pymunk.Circle(self.space.static_body, 58, (x, y + dy)); c.elasticity = 1.25; c.friction = 0.2
            self.space.add(c); self.rebot.append((x, y + dy))
        return y + 880

    def m_acelerador(self, y):
        self.seg((40, y + 40), (W - 300, y + 300)); self.seg((W - 40, y + 420), (300, y + 680))
        self.boost.append((y + 120, y + 330, 1)); self.boost.append((y + 500, y + 710, -1))
        return y + 780

    def m_embudo(self, y):
        self.seg((40, y), (W / 2 - 170, y + 330)); self.seg((W - 40, y), (W / 2 + 170, y + 330))
        self.clavo(W / 2, y + 470, 30, 0.8)
        return y + 620


def simular(n, modulos, semilla, eliminar):
    rnd = random.Random(semilla)
    space = pymunk.Space(); space.gravity = (0, 2300)
    pista = Pista(space, modulos, random.Random(1000 + semilla))
    R = 62 if n <= 6 else 54
    bolas = []
    xs = np.linspace(180, W - 180, n)
    orden_ini = rnd.sample(range(n), n)
    for k, i in enumerate(orden_ini):
        b = pymunk.Body(1, pymunk.moment_for_circle(1, 0, R))
        b.position = (xs[k] + rnd.uniform(-20, 20), 150 + rnd.uniform(-30, 30))
        b.velocity = (rnd.uniform(-60, 60), 0)
        c = pymunk.Circle(b, R); c.elasticity = 0.6; c.friction = 0.7
        space.add(b, c); bolas.append([i, b, c])
    bolas.sort(key=lambda x: x[0])
    estados, llegada, fuera, eventos = [], {}, {}, []
    ctrl = list(pista.controles[-eliminar:]) if eliminar else []
    t, vprev = 0.0, [0.0] * n
    lider_prev = None
    while len(llegada) + len(fuera) < n and t < 40:
        for _ in range(2):
            space.step(DT); t += DT
            for i, b, c in bolas:
                if i in fuera or i in llegada:
                    continue
                for y0, y1, sentido in pista.boost:
                    if y0 < b.position.y < y1:
                        b.velocity = (b.velocity.x + sentido * 40, b.velocity.y + 25)
        vivos = [(i, b) for i, b, c in bolas if i not in fuera]
        for i, b in vivos:
            if i not in llegada and b.position.y > pista.meta:
                llegada[i] = t
                eventos.append(("llega", t, i))
            dv = abs(b.velocity.length - vprev[i]); vprev[i] = b.velocity.length
            if dv > 500:
                eventos.append(("golpe", t, i))
            for y0, y1, _ in pista.boost:
                if y0 < b.position.y < y0 + 30:
                    eventos.append(("boost", t, i))
        en_carrera = [(i, b) for i, b in vivos if i not in llegada]
        if ctrl and en_carrera and len(en_carrera) > 2:
            lider_y = max(b.position.y for _, b in vivos)
            if lider_y > ctrl[0]:
                ctrl.pop(0)
                ult, bu = min(en_carrera, key=lambda x: x[1].position.y)
                fuera[ult] = t; eventos.append(("fuera", t, ult))
                space.remove(*[x for x in bolas[ult][1:]])
        if vivos:
            lider = max(vivos, key=lambda x: x[1].position.y + (1e6 - llegada[x[0]] * 1e3 if x[0] in llegada else 0))[0]
            if lider != lider_prev and lider_prev is not None and not llegada:
                eventos.append(("lider", t, lider))
            lider_prev = lider
        estados.append([(b.position.x, b.position.y, b.angle) for _, b, _ in bolas])
    orden = sorted(llegada, key=llegada.get)
    return dict(estados=estados, llegada=llegada, fuera=fuera, orden=orden, eventos=eventos, pista=pista, R=R,
                dt_estado=2 * DT, t_fin=t)


def drama(sim, n, eliminar):
    ll = sorted(sim["llegada"].values())
    if len(sim["llegada"]) + len(sim["fuera"]) < n or len(ll) < 2:
        return -99
    lideres = sum(1 for e in sim["eventos"] if e[0] == "lider")
    gap = ll[1] - ll[0]
    dur = ll[0]
    # el favorito del cuadro 0 (el primero en la lista) no debe ganar siempre: lo decide la física
    return min(lideres, 8) * 1.0 - 5 * gap + (4 if gap < 0.35 else 0) - (0 if 11 < dur < 22 else 25)


# ------------------------------------------------------------------ render
def fondo_img(pal):
    y = np.linspace(0, 1, H)[:, None, None]
    a = np.array(pal["fondo"], np.float32); b = np.array(pal["fondo2"], np.float32)
    img = (a + (b - a) * (0.5 - 0.5 * np.cos(np.pi * y))).repeat(W, 1)
    return Image.fromarray(img.astype(np.uint8), "RGB")


def main(guion_path):
    g = json.loads(Path(guion_path).read_text())
    pal = PALETAS[g.get("paleta", "noche")]
    comp = competidores(g, 2 * (62 if len(g["competidores"]) <= 6 else 54))
    n = len(comp)
    especiales = {"Vinícius Júnior": "VINÍCIUS", "Zinedine Zidane": "ZIDANE", "Kylian Mbappé": "MBAPPÉ"}
    nombres = [c.get("corto_hud") or (especiales.get(c["nombre"], c["nombre"].split()[-1].upper()) if c["tipo"] == "jugador"
               else c.get("corto", c["nombre"]).upper()) for c in comp]
    eliminar = g.get("eliminar", 0)
    mods = g["circuito"]
    mejor = max(range(g.get("intentos", 50)), key=lambda s: drama(simular(n, mods, s, eliminar), n, eliminar))
    sim = simular(n, mods, mejor, eliminar)
    R = sim["R"]; P = sim["pista"]
    ganador = sim["orden"][0]
    t_gan = sim["llegada"][ganador]
    gap = sim["llegada"][sim["orden"][1]] - t_gan
    foto_final = gap < 0.6
    print(f"semilla {mejor} gana {nombres[ganador]} en {t_gan:.1f}s, gap {gap:.2f}s, fuera {[nombres[i] for i in sim['fuera']]}")

    # línea de tiempo: cuadro de video -> tiempo de simulación (cámara lenta en el photo finish)
    T_INTRO, T_FIN = 1.7, 3.2
    tiempos = [0.0] * int(T_INTRO * FPS)
    ts = 0.0
    while ts < t_gan + 0.35:
        lento = foto_final and t_gan - 0.9 < ts < t_gan + 0.3
        ts += (0.3 if lento else 1.0) / FPS
        tiempos.append(ts)
    t_video_gan = next(k for k, x in enumerate(tiempos) if x >= t_gan) / FPS
    tiempos += [min(ts + (k + 1) / FPS, sim["t_fin"]) for k in range(int(T_FIN * FPS))]
    nf = len(tiempos)

    out = ROOT / "salida" / g["id"]; out.mkdir(parents=True, exist_ok=True)
    fondo = fondo_img(pal)
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "19",
                           str(out / "mudo.mp4")], stdin=subprocess.PIPE)

    def t_video(t_sim):
        return next((k for k, x in enumerate(tiempos) if x >= t_sim), nf - 1) / FPS

    popups = []          # (t_video, texto, color)
    sonidos = [("whoosh", T_INTRO - 0.25)]
    voz = [(0.15, g["voz_intro"])]
    ult_voz = 0.0
    for tipo, t, i in sim["eventos"]:
        tv = t_video(t)
        if tipo == "lider" and t < t_gan - 1.2:
            popups.append((tv, f"{nombres[i]} TAKES THE LEAD!", comp[i]["color"]))
            if tv - ult_voz > 2.2:
                voz.append((tv, f"{comp[i]['voz']} takes the lead!")); ult_voz = tv
            sonidos.append(("tick2", tv))
        elif tipo == "fuera":
            popups.append((tv, f"{nombres[i]} IS OUT!", ROJO)); sonidos.append(("boom", tv))
            if tv - ult_voz > 1.2:
                voz.append((tv, f"{comp[i]['voz']} is out!")); ult_voz = tv
        elif tipo == "golpe":
            sonidos.append(("tick", tv))
        elif tipo == "boost":
            sonidos.append(("whoosh", tv))
    voz = [v for v in voz if v[0] < t_video_gan - 1.6]
    if foto_final:
        voz.append((t_video_gan - 1.5, "Photo finish!"))
    voz.append((t_video_gan + 0.15, f"{comp[ganador]['voz']} wins it!"))
    voz.append((t_video_gan + 1.7, "Did your pick win?"))
    sonidos += [("riser", t_video_gan - 1.0), ("boom", t_video_gan), ("ding", t_video_gan + 0.05)]
    rng = np.random.default_rng(3)
    confeti = [(rng.uniform(0, W), rng.uniform(-400, 0), rng.uniform(250, 700), rng.uniform(-80, 80),
                tuple(int(x) for x in rng.choice([[255, 210, 63], [255, 255, 255], [240, 84, 76], [61, 214, 128], [80, 180, 255]])))
               for _ in range(140)]

    cam = 0.0
    cam_obj = 0.0
    for f in range(nf):
        tv = f / FPS
        ts = tiempos[f]
        k = min(int(ts / sim["dt_estado"]), len(sim["estados"]) - 1)
        est = sim["estados"][k]
        vivos = [i for i in range(n) if not (i in sim["fuera"] and sim["fuera"][i] <= ts)]
        llegados = [i for i in vivos if i in sim["llegada"] and sim["llegada"][i] <= ts]
        corriendo = [i for i in vivos if i not in llegados]
        if corriendo:
            cam_obj = min(max(est[i][1] for i in corriendo) - 900, P.meta - H + 520)
        if f == 0:
            cam = cam_obj = -300
        cam += (max(cam_obj, -300) - cam) * (0.10 if tv > T_INTRO else 1)
        sacud = 0
        if any(abs(tv - s) < 0.12 for n_, s in sonidos if n_ == "boom"):
            sacud = 10
        cy = cam + rng.uniform(-sacud, sacud)
        im = fondo.copy(); dr = ImageDraw.Draw(im, "RGBA")
        # marcas de tramo (texto tenue de fondo)
        for y0, m in P.marcas:
            if -200 < y0 - cy < H:
                pass
        for y0 in P.controles[-eliminar:] if eliminar else []:
            yy = y0 - cy
            if -40 < yy < H:
                dr.line((40, yy, W - 40, yy), fill=(240, 70, 70, 120), width=6)
                texto(dr, (W - 70, yy - 26), "ELIMINATION", 30, ROJO, 5, anchor="rm")
        for a, b, gr in P.segs:
            if max(a[1], b[1]) - cy > -50 and min(a[1], b[1]) - cy < H + 50:
                dr.line((a[0], a[1] - cy, b[0], b[1] - cy), fill=pal["pista"], width=2 * gr)
        for x, y, r in P.clavos:
            if -40 < y - cy < H + 40:
                dr.ellipse((x - r, y - cy - r, x + r, y - cy + r), fill=pal["clavo"])
        for x, y in P.rebot:
            if -80 < y - cy < H + 80:
                cerca = any(math.hypot(est[i][0] - x, est[i][1] - y) < R + 70 for i in vivos)
                col = pal["acento"] if cerca else pal["clavo"]
                dr.ellipse((x - 58, y - cy - 58, x + 58, y - cy + 58), fill=col, outline=(255, 255, 255), width=6)
        for y0, y1, s in P.boost:
            if -60 < y0 - cy < H + 60:
                for j in range(4):
                    yy = y0 + 20 + j * 45 - cy
                    xc = W / 2 + s * 120
                    fase = (tv * 3 + j * 0.25) % 1
                    dr.polygon([(xc - 60, yy), (xc, yy + 34), (xc + 60, yy), (xc + 60, yy + 16), (xc, yy + 50), (xc - 60, yy + 16)],
                               fill=pal["acento"] + (int(90 + 160 * fase),))
        for b, largo, brazos in P.giros:
            ang = b.angular_velocity * ts
            px, py = b.position
            if -largo < py - cy < H + largo:
                for j in range(brazos):
                    a = ang + math.pi * j / brazos
                    c, s = math.cos(a) * largo, math.sin(a) * largo
                    dr.line((px - c, py - s - cy, px + c, py + s - cy), fill=pal["acento"], width=24)
                dr.ellipse((px - 18, py - cy - 18, px + 18, py - cy + 18), fill=(255, 255, 255))
        my = P.meta - cy
        for x in range(40, W - 40, 40):
            for fila in range(2):
                dr.rectangle((x, my + fila * 20, x + 20, my + 20 + fila * 20),
                             fill=BLANCO if ((x // 40) + fila) % 2 else (0, 0, 0))
        for i in vivos:
            x, y, a = est[i]
            if -R * 2 < y - cy < H + R * 2:
                img = comp[i]["img"] if comp[i]["tipo"] == "pais" else comp[i]["img"].rotate(-math.degrees(a) * 0.35, resample=Image.BICUBIC)
                im.paste(img, (int(x - R), int(y - cy - R)), img)
                dr.ellipse((x - R, y - cy - R, x + R, y - cy + R), outline=comp[i]["color"], width=7)
                texto(dr, (x, y - cy + R + 24), nombres[i], 34, comp[i]["color"], 6)
        # eliminados: "OUT" durante 1 s donde quedaron
        for i, tf in sim["fuera"].items():
            if 0 <= ts - tf < 1.0:
                ke = min(int(tf / sim["dt_estado"]), len(sim["estados"]) - 1)
                x, y, _ = sim["estados"][ke][i]
                u = (ts - tf) / 1.0
                dr.ellipse((x - R * (1 + u), y - cy - R * (1 + u), x + R * (1 + u), y - cy + R * (1 + u)),
                           outline=ROJO + (int(255 * (1 - u)),), width=10)
                texto(dr, (x, y - cy), "OUT", 60, ROJO, 8)
        # HUD
        dr.rectangle((0, 0, W, 330), fill=(0, 0, 0, 165))
        texto(dr, (W / 2, 62), g["evento"], ajustar(g["evento"], 54, W - 120), pal["acento"], 6)
        texto(dr, (W / 2, 140), g["titulo"], ajustar(g["titulo"], 88, W - 80), BLANCO, 9)
        def clave(i):
            if i in sim["llegada"] and sim["llegada"][i] <= ts:
                return -1e9 + sim["llegada"][i]
            if i in sim["fuera"] and sim["fuera"][i] <= ts:
                return 1e9 - sim["fuera"][i]
            return -est[i][1]
        orden = sorted(range(n), key=clave)
        paso = (W - 120) / n
        for pos, i in enumerate(orden):
            x0 = 60 + paso * pos + paso / 2
            mini = comp[i]["img"].resize((int(min(paso - 14, 96)),) * 2)
            out_ = i in sim["fuera"] and sim["fuera"][i] <= ts
            if out_:
                mini = Image.fromarray(np.asarray(mini.convert("LA").convert("RGBA")))
            im.paste(mini, (int(x0 - mini.width / 2), 196), mini)
            texto(dr, (x0, 312), "OUT" if out_ else f"{pos + 1}", 30, ROJO if out_ else BLANCO, 5)
        # cuadro 0 / intro: elegí uno
        if tv < T_INTRO + 0.3:
            dr.rectangle((0, H * 0.53 - 170, W, H * 0.53 + 170), fill=(0, 0, 0, 175))
            texto(dr, (W / 2, H * 0.53 - 75), g["gancho"], ajustar(g["gancho"], 104, W - 80), BLANCO, 12)
            texto(dr, (W / 2, H * 0.53 + 60), "PICK ONE NOW 👇".replace(" 👇", ""), 92, pal["acento"], 10)
        # pop-ups
        for t0, s, col in popups:
            if 0 <= tv - t0 < 1.1 and tv < t_video_gan - 0.2:
                u = min((tv - t0) / 0.15, 1)
                tam = int(ajustar(s, 84, W - 100) * (0.6 + 0.4 * u))
                texto(dr, (W / 2, H * 0.80), s, tam, col, 10)
                break
        # último tramo: viñeta roja + latido
        if foto_final and t_video_gan - 2.2 < tv < t_video_gan:
            dr.rectangle((0, 0, W, H), outline=(240, 40, 40, 150), width=24)
            if tv > t_video_gan - 1.6:
                texto(dr, (W / 2, H * 0.80), "PHOTO FINISH!", 100, ROJO, 12)
        # ganador
        if tv >= t_video_gan:
            u = min((tv - t_video_gan) / 0.25, 1)
            dr.rectangle((0, H * 0.5 - 330, W, H * 0.5 + 330), fill=(0, 0, 0, int(210 * u)))
            d = int(360 * (0.7 + 0.3 * u))
            big = comp[ganador]["img"].resize((d, d), Image.LANCZOS)
            im.paste(big, (W // 2 - d // 2, int(H * 0.5 - 300)), big)
            dr.ellipse((W / 2 - d / 2, H * 0.5 - 300, W / 2 + d / 2, H * 0.5 - 300 + d), outline=pal["acento"], width=12)
            s = f"{nombres[ganador]} WINS!"
            texto(dr, (W / 2, H * 0.5 + 150), s, ajustar(s, 130, W - 80), pal["acento"], 12)
            texto(dr, (W / 2, H * 0.5 + 265), g.get("cierre", "DID YOUR PICK WIN?"), ajustar(g.get("cierre", "DID YOUR PICK WIN?"), 70, W - 100), BLANCO, 8)
            for x, y, v, vx, col in confeti:
                tt = tv - t_video_gan
                yy = y + v * tt; xx = x + vx * tt + 20 * math.sin(tt * 6 + x)
                if 0 < yy < H:
                    dr.rectangle((xx, yy, xx + 14, yy + 22), fill=col)
        ff.stdin.write(np.asarray(im, np.uint8).tobytes())
    ff.stdin.close(); ff.wait()

    # audio: beat + efectos + relator (edge-tts)
    dur = nf / FPS
    mix = beat(dur) * 0.8
    fx = efectos(n)
    def add(s, sig, vol=1.0):
        i = int(s * SR); j = min(len(mix), i + len(sig))
        if 0 <= i < len(mix):
            mix[i:j] += vol * sig[: j - i]
    ult = {}
    for nombre_fx, s in sorted(sonidos, key=lambda x: x[1]):
        if nombre_fx in ("tick", "whoosh") and s - ult.get(nombre_fx, -9) < (0.09 if nombre_fx == "tick" else 0.5):
            continue
        ult[nombre_fx] = s
        add(s, fx[nombre_fx], 0.55 if nombre_fx == "tick" else 1.0)
    if foto_final:
        for k in range(6):
            add(t_video_gan - 2.0 + k * 0.38, fx["latido"], 1.0)
    # público: ruido filtrado que crece al final
    nz = np.convolve(rng.standard_normal(int(2.4 * SR)).astype(np.float32), np.ones(40) / 40, mode="same")
    env = np.concatenate([np.linspace(0.2, 1, int(0.4 * SR)), np.ones(int(1.0 * SR)), np.linspace(1, 0, int(1.0 * SR))])[: len(nz)]
    add(t_video_gan - 0.05, nz * env, 2.2)
    lineas = [l for _, l in voz]
    rutas = voces_edge(lineas, out)
    dv = np.ones_like(mix)
    for (s, _), r in zip(voz, rutas):
        x = leer_wav(r)
        i = int(s * SR); j = min(len(mix), i + len(x))
        if i < len(mix):
            dv[i:j] = np.minimum(dv[i:j], 0.45)
            mix[i:j] += 1.05 * x[: j - i]
    mix = np.tanh(mix * dv * 1.3) * 0.9
    import wave
    with wave.open(str(out / "audio.wav"), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(mix, -1, 1) * 32767).astype(np.int16).tobytes())
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(out / "mudo.mp4"), "-i", str(out / "audio.wav"),
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", str(out / "short.mp4")], check=True)
    (out / "mudo.mp4").unlink()
    json.dump({"semilla": mejor, "ganador": comp[ganador]["nombre"], "orden": [comp[i]["nombre"] for i in sim["orden"]],
               "eliminados": [comp[i]["nombre"] for i in sim["fuera"]], "dur": round(dur, 1)},
              open(out / "resultado.json", "w"), ensure_ascii=False, indent=1)
    print("listo", out / "short.mp4", f"{dur:.1f}s")


def lineas_voz(g):
    """Todas las frases posibles del relator (se generan antes en GitHub Actions)."""
    ls = [g["voz_intro"], "Photo finish!", "Did your pick win?"]
    for c in g["competidores"]:
        ls += [f"{c['voz']} takes the lead!", f"{c['voz']} is out!", f"{c['voz']} wins it!"]
    return ls


if __name__ == "__main__":
    main(sys.argv[1])
