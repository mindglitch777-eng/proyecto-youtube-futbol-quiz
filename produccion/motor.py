#!/usr/bin/env python3
"""
Motor gráfico V2: dibujo vectorial con antialias (cairo) + imágenes y textos con Pillow, salida a 60 fps.
Lo usan la Circle Cup V2, Ring Escape y las carreras V2.

- Lienzo: cairo ARGB32 1080x1920 -> numpy -> Pillow (caras, escudos, texto) -> ffmpeg.
- Skins de pelota: clasica, dorada, champions, neon, mundial (dibujadas por código, rotan con la física).
- Skins de arco: red blanca, neón, dorada.
- Cámara: resorte críticamente amortiguado (sin sacudones ni saltos).
- Audio: sintetizado propio (notas por rebote, silbato, bocina, tribuna), sin derechos de terceros.
"""
import math
import subprocess
import wave
from functools import lru_cache
from pathlib import Path

import cairocffi as cairo
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
W, H, FPS, SR = 1080, 1920, 60, 44100
ANTON = str(ROOT / "assets/fuentes/Anton-Regular.ttf")
ARCHIVO = str(ROOT / "assets/fuentes/ArchivoBlack-Regular.ttf")


# ------------------------------------------------------------------ lienzo
class Lienzo:
    def __init__(self, fondo=None):
        self.s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
        self.c = cairo.Context(self.s)
        self.c.set_antialias(cairo.ANTIALIAS_BEST)
        if fondo is not None:
            self.c.set_source_surface(fondo, 0, 0); self.c.paint()

    def rgba(self, col, a=1.0):
        r, g, b = [x / 255 for x in col[:3]]
        self.c.set_source_rgba(r, g, b, a if len(col) < 4 else col[3] / 255 * a)

    def circulo(self, x, y, r, col, a=1.0, borde=None, ancho=0, borde_a=1.0):
        self.c.new_path(); self.c.arc(x, y, r, 0, 2 * math.pi)
        if col is not None:
            self.rgba(col, a); self.c.fill_preserve() if borde else self.c.fill()
        if borde:
            self.rgba(borde, borde_a); self.c.set_line_width(ancho); self.c.stroke()

    def brillo(self, x, y, r, col, a=0.5):
        """Halo radial suave."""
        g = cairo.RadialGradient(x, y, 0, x, y, r)
        cr, cg, cb = [v / 255 for v in col[:3]]
        g.add_color_stop_rgba(0, cr, cg, cb, a); g.add_color_stop_rgba(1, cr, cg, cb, 0)
        self.c.set_source(g); self.c.new_path(); self.c.arc(x, y, r, 0, 2 * math.pi); self.c.fill()

    def arco(self, x, y, r, a0, a1, col, ancho, a=1.0, cap=cairo.LINE_CAP_ROUND):
        self.c.new_path(); self.c.arc(x, y, r, a0, a1)
        self.rgba(col, a); self.c.set_line_width(ancho); self.c.set_line_cap(cap); self.c.stroke()

    def linea(self, x0, y0, x1, y1, col, ancho, a=1.0):
        self.c.new_path(); self.c.move_to(x0, y0); self.c.line_to(x1, y1)
        self.rgba(col, a); self.c.set_line_width(ancho); self.c.set_line_cap(cairo.LINE_CAP_ROUND); self.c.stroke()

    def rect_redondo(self, x, y, w, h, r, col, a=1.0, borde=None, ancho=0):
        c = self.c; c.new_path()
        c.arc(x + w - r, y + r, r, -math.pi / 2, 0); c.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
        c.arc(x + r, y + h - r, r, math.pi / 2, math.pi); c.arc(x + r, y + r, r, math.pi, 3 * math.pi / 2); c.close_path()
        if col is not None:
            self.rgba(col, a); c.fill_preserve() if borde else c.fill()
        if borde:
            self.rgba(borde); c.set_line_width(ancho); c.stroke()

    def a_pil(self):
        buf = np.ndarray((H, W, 4), np.uint8, self.s.get_data())
        return Image.fromarray(buf[:, :, [2, 1, 0]].copy(), "RGB")


def superficie_fondo(c1, c2, cy=0.55, cancha=False):
    """Degradé radial de fondo (se calcula una vez y se reutiliza en cada cuadro)."""
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); c = cairo.Context(s)
    g = cairo.RadialGradient(W / 2, H * cy, 50, W / 2, H * cy, H * 0.75)
    g.add_color_stop_rgb(0, *[v / 255 for v in c2]); g.add_color_stop_rgb(1, *[v / 255 for v in c1])
    c.set_source(g); c.paint()
    return s


# ------------------------------------------------------------------ skins de pelota
def _penta(c, x, y, r, rot):
    c.new_path()
    for i in range(5):
        a = rot + i * 2 * math.pi / 5 - math.pi / 2
        (c.move_to if i == 0 else c.line_to)(x + r * math.cos(a), y + r * math.sin(a))
    c.close_path()


SKINS = {
    "clasica": dict(base=(250, 250, 250), panel=(20, 20, 24), estilo="pentagonos"),
    "dorada": dict(base=(250, 214, 92), panel=(120, 78, 10), estilo="pentagonos"),
    "champions": dict(base=(245, 247, 252), panel=(16, 36, 110), estilo="estrellas"),
    "neon": dict(base=(18, 20, 30), panel=(60, 255, 200), estilo="pentagonos"),
    "mundial": dict(base=(250, 250, 250), panel=(220, 40, 60), panel2=(20, 110, 230), panel3=(30, 170, 90), estilo="ondas"),
}


def pelota(L, x, y, r, ang, skin="clasica"):
    """Pelota con sombreado esférico y paneles que rotan con `ang`."""
    k = SKINS[skin]; c = L.c
    L.circulo(x + r * 0.18, y + r * 0.32, r * 1.02, (0, 0, 0), 0.28)            # sombra
    c.save(); c.new_path(); c.arc(x, y, r, 0, 2 * math.pi); c.clip()
    L.circulo(x, y, r, k["base"])
    if k["estilo"] == "pentagonos":
        L.rgba(k["panel"]); _penta(c, x, y, r * 0.36, ang); c.fill()
        for i in range(5):
            a = ang + i * 2 * math.pi / 5 - math.pi / 2
            px, py = x + math.cos(a) * r * 0.92, y + math.sin(a) * r * 0.92
            L.rgba(k["panel"]); _penta(c, px, py, r * 0.32, a + math.pi / 2); c.fill()
            L.linea(x + math.cos(a) * r * 0.36, y + math.sin(a) * r * 0.36, x + math.cos(a) * r * 0.62, y + math.sin(a) * r * 0.62, k["panel"], r * 0.05)
    elif k["estilo"] == "estrellas":
        for i in range(6):
            a = ang + i * math.pi / 3
            px, py = x + math.cos(a) * r * 0.55, y + math.sin(a) * r * 0.55
            c.new_path()
            for j in range(10):
                rr = r * (0.26 if j % 2 == 0 else 0.11); aa = a + j * math.pi / 5
                (c.move_to if j == 0 else c.line_to)(px + rr * math.cos(aa), py + rr * math.sin(aa))
            c.close_path(); L.rgba(k["panel"]); c.fill()
    elif k["estilo"] == "triadas":
        for i in range(3):
            a = ang + i * 2 * math.pi / 3
            px, py = x + math.cos(a) * r * 0.5, y + math.sin(a) * r * 0.5
            L.arco(px, py, r * 0.42, a + 0.6, a + math.pi * 2 - 0.6, k["panel"], r * 0.16, cap=cairo.LINE_CAP_BUTT)
        L.circulo(x, y, r * 0.18, k["panel"])
    elif k["estilo"] == "ondas":
        for i, col in enumerate((k["panel"], k["panel2"], k["panel3"])):
            a = ang + i * 2 * math.pi / 3
            L.arco(x + math.cos(a) * r * 0.45, y + math.sin(a) * r * 0.45, r * 0.55, a + 0.9, a + 2.9, col, r * 0.2, cap=cairo.LINE_CAP_ROUND)
    # sombreado esférico y brillo especular
    g = cairo.RadialGradient(x - r * 0.35, y - r * 0.4, r * 0.05, x, y, r * 1.05)
    g.add_color_stop_rgba(0, 1, 1, 1, 0.55); g.add_color_stop_rgba(0.45, 1, 1, 1, 0.0); g.add_color_stop_rgba(1, 0, 0, 0, 0.38)
    c.set_source(g); c.paint()
    c.restore()
    L.circulo(x, y, r, None, borde=(0, 0, 0), ancho=max(2, r * 0.05), borde_a=0.55)


# ------------------------------------------------------------------ imágenes (caras/escudos/banderas) recortadas en círculo
@lru_cache(maxsize=256)
def disco(path_o_clave, d, fondo=(255, 255, 255)):
    """Imagen cuadrada recortada en círculo con fondo (los escudos con transparencia quedan sobre blanco)."""
    im = Image.open(path_o_clave).convert("RGBA")
    w, h = im.size; s = max(w, h)
    lienzo = Image.new("RGBA", (s, s), fondo + (255,)); lienzo.alpha_composite(im, ((s - w) // 2, (s - h) // 2))
    im = lienzo.resize((d, d), Image.LANCZOS)
    m = Image.new("L", (d * 3, d * 3), 0); ImageDraw.Draw(m).ellipse((0, 0, d * 3 - 1, d * 3 - 1), fill=255)
    im.putalpha(m.resize((d, d), Image.LANCZOS))
    return im


def escudo_en_disco(path, d, margen=0.14):
    """Escudo entero (sin recortar) centrado dentro de un disco blanco."""
    esc = Image.open(path).convert("RGBA")
    lado = int(d * (1 - 2 * margen))
    esc.thumbnail((lado, lado), Image.LANCZOS)
    base = Image.new("RGBA", (d, d), (0, 0, 0, 0))
    m = Image.new("L", (d * 3, d * 3), 0); ImageDraw.Draw(m).ellipse((0, 0, d * 3 - 1, d * 3 - 1), fill=255)
    blanco = Image.new("RGBA", (d, d), (255, 255, 255, 255)); blanco.putalpha(m.resize((d, d), Image.LANCZOS))
    base.alpha_composite(blanco)
    base.alpha_composite(esc, ((d - esc.width) // 2, (d - esc.height) // 2))
    return base


# ------------------------------------------------------------------ texto
@lru_cache(maxsize=64)
def fuente(tam, cual=ANTON):
    return ImageFont.truetype(cual, tam)


def texto(dr, xy, s, tam, color=(255, 255, 255), borde=0, borde_col=(0, 0, 0), anchor="mm", cual=ANTON):
    dr.text(xy, s, font=fuente(tam, cual), fill=color, stroke_width=borde, stroke_fill=borde_col, anchor=anchor)


def ajustar(s, tam, ancho, cual=ANTON):
    while fuente(tam, cual).getlength(s) > ancho and tam > 24:
        tam -= 2
    return tam


# ------------------------------------------------------------------ cámara
class Resorte:
    """Seguimiento críticamente amortiguado: llega suave, sin pasarse ni temblar."""
    def __init__(self, x=0.0, w=4.0):
        self.x, self.v, self.w = x, 0.0, w

    def paso(self, objetivo, dt):
        a = self.w * self.w * (objetivo - self.x) - 2 * self.w * self.v
        self.v += a * dt; self.x += self.v * dt
        return self.x


# ------------------------------------------------------------------ salida
class Video:
    def __init__(self, ruta_mudo):
        self.p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                                   "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "23",
                                   "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(ruta_mudo)], stdin=subprocess.PIPE)

    def cuadro(self, im):
        self.p.stdin.write(np.asarray(im, np.uint8).tobytes())

    def cerrar(self):
        self.p.stdin.close(); self.p.wait()


def mezclar(out, mudo, pistas):
    """pistas: {nombre_mp4: array mono float}. Une audio y video; borra el mudo."""
    for nombre, pista in pistas.items():
        with wave.open(str(out / "audio.wav"), "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
            w.writeframes((np.clip(pista, -1, 1) * 32767).astype(np.int16).tobytes())
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(mudo), "-i", str(out / "audio.wav"),
                        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(out / nombre)], check=True)
    Path(mudo).unlink()
    (out / "audio.wav").unlink()


# ------------------------------------------------------------------ audio propio
NOTAS = [261.6, 293.7, 329.6, 392.0, 440.0, 523.3, 587.3, 659.3, 784.0, 880.0, 1046.5, 1174.7, 1318.5]


def pluck(f, d=0.25, vol=0.26):
    t = np.arange(int(d * SR)) / SR
    return (np.sin(2 * np.pi * f * t) + 0.35 * np.sin(4 * np.pi * f * t) + 0.12 * np.sin(6 * np.pi * f * t)) * np.exp(-t * 16) * vol


def silbato(d=0.45):
    t = np.arange(int(d * SR)) / SR
    return np.sin(2 * np.pi * (2900 + 120 * np.sin(2 * np.pi * 38 * t)) * t) * np.minimum(t / 0.02, 1) * np.exp(-t * 2.5) * 0.18


def bocina(d=0.9):
    t = np.arange(int(d * SR)) / SR
    s = sum(np.sign(np.sin(2 * np.pi * f * t)) for f in (220, 277, 330)) / 3
    return np.convolve(s, np.ones(30) / 30, mode="same") * np.minimum(t / 0.03, 1) * np.exp(-t * 2.4) * 0.3


def tribuna(d=1.8, semilla=4):
    rng = np.random.default_rng(semilla)
    nz = np.convolve(rng.standard_normal(int(d * SR)), np.ones(50) / 50, mode="same")
    t = np.arange(len(nz)) / SR
    return nz * np.minimum(t / 0.15, 1) * np.exp(-t * 1.4) * 2.4


def golpe(d=0.12):
    t = np.arange(int(d * SR)) / SR
    return np.sin(2 * np.pi * (140 + 300 * np.exp(-40 * t)) * t) * np.exp(-t * 35) * 0.35


def whoosh(d=0.4, semilla=2):
    nz = np.random.default_rng(semilla).standard_normal(int(d * SR)).astype(np.float32)
    t = np.arange(len(nz)) / SR
    return np.convolve(nz, np.ones(18) / 18, mode="same") * np.sin(np.pi * t / d) ** 2 * 0.6


def boom(d=1.0):
    t = np.arange(int(d * SR)) / SR
    return np.sin(2 * np.pi * (36 + 70 * np.exp(-10 * t)) * t) * np.exp(-t * 4) * 0.85


def ding(d=0.9):
    t = np.arange(int(d * SR)) / SR
    return (np.sin(2 * np.pi * 1318 * t) + 0.6 * np.sin(2 * np.pi * 1976 * t)) * np.exp(-t * 4.5) * 0.22


def beat_pista(dur, bpm=128):
    n = int(dur * SR); mix = np.zeros(n, np.float32); paso = 60 / bpm / 2
    tt = np.arange(int(0.35 * SR)) / SR
    kick = np.sin(2 * np.pi * (45 + 90 * np.exp(-25 * tt)) * tt) * np.exp(-9 * tt)
    th = np.arange(int(0.05 * SR)) / SR
    hat = np.random.default_rng(1).standard_normal(len(th)) * np.exp(-60 * th)
    tb = np.arange(int(0.3 * SR)) / SR
    bajo = np.sin(2 * np.pi * 55 * tb) * np.exp(-6 * tb)
    for i in range(int(dur / paso)):
        s = int(i * paso * SR)
        for sig, cond, vol in ((kick, i % 4 == 0, .45), (hat, i % 2 == 1, .05), (bajo, i % 8 in (3, 6), .25)):
            if cond:
                j = min(n, s + len(sig)); mix[s:j] += vol * sig[: j - s]
    return mix


class Mezcla:
    def __init__(self, dur):
        self.x = np.zeros(int(dur * SR) + SR, np.float32); self.dur = dur

    def add(self, t, sig, vol=1.0):
        i = int(t * SR); j = min(len(self.x), i + len(sig))
        if 0 <= i < len(self.x):
            self.x[i:j] += vol * sig[: j - i]

    def versiones(self, beat_vol=0.5):
        solo = self.x[: int(self.dur * SR)]
        con = solo + beat_pista(self.dur)[: len(solo)] * beat_vol
        return {"short.mp4": np.tanh(con * 1.15) * 0.9, "short_sin_musica.mp4": np.tanh(solo * 1.1) * 0.75}


# ------------------------------------------------------------------ imágenes PIL dentro de cairo
def pil_a_cairo(im):
    """PIL RGBA -> superficie cairo (alfa premultiplicado), para dibujar todo en el mismo orden de capas."""
    im = im.convert("RGBA")
    a = np.asarray(im, np.float32)
    al = a[:, :, 3:4] / 255.0
    bgra = np.empty_like(a); bgra[:, :, 0] = a[:, :, 2]; bgra[:, :, 1] = a[:, :, 1]; bgra[:, :, 2] = a[:, :, 0]
    bgra[:, :, :3] *= al; bgra[:, :, 3] = a[:, :, 3]
    buf = bytearray(np.ascontiguousarray(bgra.astype(np.uint8)).tobytes())
    return cairo.ImageSurface.create_for_data(buf, cairo.FORMAT_ARGB32, im.width, im.height, im.width * 4)


def gris(im, k=0.75):
    """Versión apagada (eliminados en el cuadro)."""
    g = im.convert("LA").convert("RGBA"); g.putalpha(im.getchannel("A"))
    return Image.blend(g, Image.new("RGBA", im.size, (20, 20, 30, 0)), 1 - k).convert("RGBA") if k < 1 else g


def imagen(L, surf, x, y, ang=0.0, alpha=1.0, escala=1.0):
    c = L.c; c.save(); c.translate(x, y)
    if ang:
        c.rotate(ang)
    if escala != 1.0:
        c.scale(escala, escala)
    c.set_source_surface(surf, -surf.get_width() / 2, -surf.get_height() / 2)
    c.get_source().set_filter(cairo.FILTER_BEST)
    c.paint_with_alpha(alpha) if alpha < 1 else c.paint()
    c.restore()


def suave(u):
    """Curva ease-in-out (smoothstep) para animaciones sin tirones."""
    u = min(max(u, 0.0), 1.0)
    return u * u * (3 - 2 * u)


def trofeo(L, x, y, h, a=1.0):
    """Copa vectorial dorada con degradé metálico."""
    c = L.c; w = h * 0.62
    g = cairo.LinearGradient(x - w / 2, 0, x + w / 2, 0)
    for st, col in ((0, (0.62, 0.43, 0.08)), (0.35, (1, 0.88, 0.45)), (0.55, (1, 0.97, 0.75)), (1, (0.7, 0.5, 0.1))):
        g.add_color_stop_rgba(st, *col, a)
    c.new_path()
    top = y - h * 0.5
    c.move_to(x - w / 2, top); c.line_to(x + w / 2, top)
    c.curve_to(x + w / 2, top + h * 0.42, x + w * 0.18, top + h * 0.55, x + w * 0.08, top + h * 0.6)
    c.line_to(x + w * 0.08, top + h * 0.78); c.line_to(x + w * 0.3, top + h * 0.86); c.line_to(x + w * 0.3, top + h)
    c.line_to(x - w * 0.3, top + h); c.line_to(x - w * 0.3, top + h * 0.86); c.line_to(x - w * 0.08, top + h * 0.78)
    c.line_to(x - w * 0.08, top + h * 0.6)
    c.curve_to(x - w * 0.18, top + h * 0.55, x - w / 2, top + h * 0.42, x - w / 2, top)
    c.close_path(); c.set_source(g); c.fill()
    for s in (-1, 1):                                                        # asas
        c.new_path(); c.arc(x + s * w * 0.5, top + h * 0.2, h * 0.14, -math.pi / 2, math.pi / 2) if s > 0 else \
            c.arc_negative(x + s * w * 0.5, top + h * 0.2, h * 0.14, -math.pi / 2, math.pi / 2)
        c.set_source(g); c.set_line_width(h * 0.05); c.stroke()


class Particulas:
    """Chispas/confeti deterministas: se crean en eventos y se dibujan en función del tiempo (sin estado por cuadro)."""
    def __init__(self, semilla=3):
        self.rng = np.random.default_rng(semilla); self.p = []

    def chispas(self, t0, x, y, col, n=36, v=(380, 900), ang=None, abertura=math.pi * 2, vida=0.9):
        for _ in range(n):
            a = (ang if ang is not None else 0) + self.rng.uniform(-abertura / 2, abertura / 2)
            vv = self.rng.uniform(*v)
            self.p.append(("c", t0, x, y, vv * math.cos(a), vv * math.sin(a), col, self.rng.uniform(3, 7), vida * self.rng.uniform(0.6, 1)))

    def confeti(self, t0, n=180, cols=((255, 210, 63), (255, 255, 255), (240, 84, 76), (61, 214, 128), (80, 180, 255))):
        for _ in range(n):
            self.p.append(("f", t0, self.rng.uniform(0, W), self.rng.uniform(-700, -20), self.rng.uniform(-60, 60),
                           self.rng.uniform(260, 520), cols[self.rng.integers(len(cols))], self.rng.uniform(0, 6.28), 9.0))

    def dibujar(self, L, t):
        for q in self.p:
            k, t0 = q[0], q[1]; u = t - t0
            if u < 0 or u > q[8]:
                continue
            if k == "c":
                x = q[2] + q[4] * u; y = q[3] + q[5] * u + 600 * u * u
                L.circulo(x, y, q[7] * (1 - u / q[8]) + 1, q[6], 1 - u / q[8])
            else:
                x = q[2] + q[4] * u + 26 * math.sin(u * 5 + q[7]); y = q[3] + q[5] * u
                if -30 < y < H + 30:
                    c = L.c; c.save(); c.translate(x, y); c.rotate(q[7] + u * 4); c.scale(1, abs(math.cos(u * 6 + q[7])) + 0.15)
                    L.rgba(q[6]); c.rectangle(-8, -12, 16, 24); c.fill(); c.restore()
