#!/usr/bin/env python3
"""
FORMATOS DE 20-24 s (ideas de la IA de YouTube Studio, 11/11), con las reglas de edición que pidió:
- corte cada 2,5-3 s con punch-in alternado (1,00x ↔ 1,12x) + whoosh y golpe: nunca una imagen fija más de 3 s;
- subtítulos palabra por palabra en el tercio medio (amarillo la palabra que suena, blanco el resto);
- sonido en capas: beat constante que BAJA cuando habla la voz (ducking) + un efecto en cada aparición;
- barra de tiempo arriba que se vacía (urgencia) y gancho de ego en el segundo 0.

Formatos (guion["formato"]):
  fichaje  · HIDDEN TRANSFER: 3 pistas (clubes → precio → silueta) y se revela el jugador.
  costo    · WHO COST MORE?: 3 rondas de fichajes reales; la final queda sin respuesta (va en el comentario fijado).
  balon    · BUILD YOUR BALLON D'OR PLAYER: 3 decisiones que se eligen PAUSANDO (pierna, academia, compañero).
Voz: edge-tts generada en GitHub (assets/voz_edge, workflow voz.yml) a partir de guiones/<id>.json "voz_lineas".
Uso: python3 produccion/render_q20.py guion.json
"""
import json
import math
import subprocess
import sys
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import motor as M
import render_plinko as P

ROOT = Path(__file__).resolve().parent
REC = ROOT / "assets" / "recortes"
ESC = ROOT / "assets" / "escudos"
W, H, FPS = 1080, 1920, 30
AMA, BLA, ROJ, VER = (255, 222, 0), (255, 255, 255), (235, 40, 50), (40, 220, 90)


# ------------------------------------------------------------------ voz (edge-tts) + palabras
def voz(linea):
    """(señal, duración). Si la locución todavía no está generada, silencio con la duración estimada."""
    idx = ROOT / "assets" / "voz_edge" / "indice.json"
    ind = json.loads(idx.read_text()) if idx.exists() else {}
    if linea in ind:
        x = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", str(ROOT / "assets" / "voz_edge" / ind[linea]["archivo"]),
                            "-af", "silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse",
                            "-ac", "1", "-ar", str(M.SR), "-f", "f32le", "-"], capture_output=True, check=True).stdout
        s = np.frombuffer(x, np.float32).copy()
        return s / max(1e-6, np.abs(s).max()) * 0.95, len(s) / M.SR
    d = 0.33 * len(linea.split()) + 0.3
    return np.zeros(int(d * M.SR), np.float32), d


def tiempos_palabras(linea, t0, dur):
    """Reparte la duración de la frase entre sus palabras (por cantidad de letras): [(palabra, desde, hasta)]."""
    ps = linea.split(); pesos = [len(p.strip(".,!?'")) + 2 for p in ps]; tot = sum(pesos); out = []; t = t0
    for p, w in zip(ps, pesos):
        d = dur * w / tot; out.append((p, t, t + d)); t += d
    return out


# ------------------------------------------------------------------ dibujo
@lru_cache(maxsize=64)
def recorte(ref, alto):
    im = Image.open(REC / f"{ref}.png").convert("RGBA")
    im = im.crop(im.getbbox()); k = alto / im.height
    return im.resize((max(1, int(im.width * k)), alto), Image.LANCZOS)


@lru_cache(maxsize=64)
def escudo(nombre, lado):
    im = Image.open(ESC / f"{nombre}.png").convert("RGBA"); im = im.crop(im.getbbox()); k = lado / max(im.size)
    return im.resize((max(1, int(im.width * k)), max(1, int(im.height * k))), Image.LANCZOS)


@lru_cache(maxsize=8)
def fondo(c1, c2):
    yy = np.linspace(0, 1, H)[:, None, None]
    arr = np.array(c1) * (1 - yy) + np.array(c2) * yy
    im = Image.fromarray(np.broadcast_to(arr, (H, W, 3)).astype(np.uint8)).convert("RGBA")
    viñeta = Image.new("L", (W, H), 0); ImageDraw.Draw(viñeta).ellipse((-300, -200, W + 300, H + 200), fill=255)
    oscuro = Image.new("RGBA", (W, H), (0, 0, 0, 170)); oscuro.putalpha(Image.eval(viñeta.filter(ImageFilter.GaussianBlur(160)), lambda v: 170 - v * 170 // 255))
    im.alpha_composite(oscuro)
    return im


def rayos(im, t, cx=W / 2, cy=H * 0.45, color=(255, 255, 255), alfa=26, n=16):
    """Rayos de luz que giran despacio (fondo vivo: nunca quieto)."""
    capa = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(capa)
    for k in range(n):
        a = k * 2 * math.pi / n + t * 0.35
        d.polygon([(cx, cy), (cx + 2400 * math.cos(a), cy + 2400 * math.sin(a)), (cx + 2400 * math.cos(a + 0.11), cy + 2400 * math.sin(a + 0.11))],
                  fill=color + (alfa,))
    im.alpha_composite(capa)


@lru_cache(maxsize=4)
def balon_dorado(alto=760):
    """Trofeo propio (sin fotos de stock): pelota dorada con brillo metálico y costuras, sobre una base de mármol negro."""
    r = int(alto * 0.36); w = int(alto * 0.8); im = Image.new("RGBA", (w, alto), (0, 0, 0, 0))
    yy, xx = np.mgrid[-r:r, -r:r].astype(np.float32) / r
    z2 = 1 - xx ** 2 - yy ** 2; m = z2 > 0; z = np.sqrt(np.clip(z2, 0, 1))
    luz = np.clip(0.25 + 0.75 * (-0.45 * xx - 0.55 * yy + 0.7 * z), 0, 1)
    esp = np.clip((-0.4 * xx - 0.5 * yy + 0.77 * z), 0, 1) ** 28
    oro = np.stack([150 + 105 * luz, 95 + 125 * luz, 15 + 70 * luz], -1) + 255 * esp[..., None]
    a = np.dstack([np.clip(oro, 0, 255), m * 255]).astype(np.uint8)
    bola = Image.fromarray(a, "RGBA"); d = ImageDraw.Draw(bola)
    cx0, cy0 = r * 1.04, r * 1.06                                               # pelota clásica: pentágono central + costuras
    pent = [(cx0 + r * 0.24 * math.cos(j * 2 * math.pi / 5 - math.pi / 2), cy0 + r * 0.24 * math.sin(j * 2 * math.pi / 5 - math.pi / 2)) for j in range(5)]
    d.polygon(pent, fill=(150, 100, 15, 120))
    for j, (px, py) in enumerate(pent):
        a = j * 2 * math.pi / 5 - math.pi / 2
        qx, qy = cx0 + r * 0.52 * math.cos(a), cy0 + r * 0.52 * math.sin(a)
        d.line([(px, py), (qx, qy)], fill=(130, 85, 10, 120), width=max(2, r // 60))
        for s_ in (-1, 1):
            b = a + s_ * 0.55
            d.line([(qx, qy), (cx0 + r * 0.8 * math.cos(b), cy0 + r * 0.8 * math.sin(b))], fill=(130, 85, 10, 110), width=max(2, r // 60))
    bola.putalpha(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2)))
    db = ImageDraw.Draw(im)
    by = 2 * r - 10
    db.polygon([(w / 2 - r * 0.35, by), (w / 2 + r * 0.35, by), (w / 2 + r * 0.6, alto * 0.82), (w / 2 - r * 0.6, alto * 0.82)], fill=(30, 28, 34))
    db.rounded_rectangle((w / 2 - r * 0.85, alto * 0.8, w / 2 + r * 0.85, alto - 4), 18, fill=(18, 16, 22), outline=(200, 160, 50), width=6)
    db.rectangle((w / 2 - r * 0.5, alto * 0.86, w / 2 + r * 0.5, alto * 0.93), fill=(215, 175, 60))
    im.alpha_composite(bola, (int(w / 2 - r), 0))
    return im


def silueta(im_rgba, color=(8, 8, 14)):
    a = np.asarray(im_rgba).copy(); a[..., :3] = color
    return Image.fromarray(a)


_NEON = {}


def neon(im_rgba, color, grosor=10, brillo=1.0):
    """Contorno de neón alrededor de un recorte (con memoria por imagen: se dibuja en cada cuadro)."""
    k = (id(im_rgba), color, grosor, brillo)
    if k not in _NEON:
        _NEON[k] = _neon(im_rgba, color, grosor, brillo)
    return _NEON[k]


def _neon(im_rgba, color, grosor=10, brillo=1.0):
    al = im_rgba.split()[3]
    borde = al.filter(ImageFilter.MaxFilter(grosor * 2 + 1))
    glow = Image.new("RGBA", im_rgba.size, color + (0,)); glow.putalpha(borde.point(lambda v: int(v * brillo)))
    out = Image.new("RGBA", im_rgba.size, (0, 0, 0, 0))
    out.alpha_composite(glow.filter(ImageFilter.GaussianBlur(grosor * 1.5))); out.alpha_composite(glow)
    return out


def pegar(im, src, cx, cy, s=1.0):
    if s != 1.0:
        src = src.resize((max(1, int(src.width * s)), max(1, int(src.height * s))), Image.BICUBIC)
    im.alpha_composite(src, (int(cx - src.width / 2), int(cy - src.height / 2)))


def rebote(e, k=9, f=20, amp=0.35):
    """Escala de entrada con rebote (golpe visual): 1+amp → 1."""
    return 1.0 if e < 0 else 1 + amp * math.exp(-e * k) * math.cos(e * f)


def cartel(d, xy, txt, tam, fill=AMA, caja=(14, 14, 20, 225), pad=26, ancho_max=1000):
    while tam > 30 and P.fuente(tam).getlength(txt) > ancho_max - 2 * pad:
        tam -= 3
    w = P.fuente(tam).getlength(txt); x, y = xy
    d.rounded_rectangle((x - w / 2 - pad, y - tam * 0.62 - pad / 2, x + w / 2 + pad, y + tam * 0.62 + pad / 2), 26, fill=caja)
    claro = sum(caja[:3]) > 450
    d.text((x, y), txt, font=P.fuente(tam), fill=fill, anchor="mm", stroke_width=0 if claro else 6, stroke_fill=(20, 20, 30))


def tarjeta(im, cx, cy, w, h, borde=AMA, glow=0.0, fondo_c=(20, 22, 40, 235)):
    capa = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(capa)
    if glow > 0:
        g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(g).rounded_rectangle(
            (cx - w / 2 - 18, cy - h / 2 - 18, cx + w / 2 + 18, cy + h / 2 + 18), 46, fill=borde + (int(200 * glow),))
        capa.alpha_composite(g.filter(ImageFilter.GaussianBlur(22)))
    d.rounded_rectangle((cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2), 36, fill=fondo_c, outline=borde, width=8)
    im.alpha_composite(capa)


def subtitulos(im, palabras, t, y=1300, caja=True, ancho=980, cx=W / 2):
    """Frase actual palabra por palabra: la que suena en amarillo y un poco más grande; las demás en blanco."""
    act = [p for p in palabras if p[1] - 0.05 <= t]
    if not act or t > palabras[-1][2] + 0.6:
        return
    i = len(act) - 1
    grupos, cur = [], []                                                      # de a 4 palabras como máximo, cortando en . ! ?
    for k, p in enumerate(palabras):
        cur.append(k)
        if len(cur) == 4 or p[0][-1] in ".!?" or (k + 1 < len(palabras) and palabras[k + 1][1] - p[2] > 0.25):
            grupos.append(cur); cur = []
    if cur:
        grupos.append(cur)
    gi = next(gr for gr in grupos if i in gr); ini = gi[0]; grupo = [palabras[k] for k in gi]
    d = ImageDraw.Draw(im); tam = 84
    txts = [g[0].upper() for g in grupo]
    while tam > 46 and sum(P.fuente(tam).getlength(x + " ") for x in txts) > ancho:
        tam -= 4
    tot = sum(P.fuente(tam).getlength(x + " ") for x in txts); x = max(50, cx - tot / 2)
    if caja:                                                                   # franja oscura detrás: siempre legible
        d.rounded_rectangle((x - 30, y - tam * 0.75, x + tot + 10, y + tam * 0.75), 28, fill=(10, 10, 16, 200))
    for k, (p, a, b) in enumerate(grupo):
        s = p.upper(); w = P.fuente(tam).getlength(s + " ")
        if a - 0.05 > t:
            x += w; continue
        actual = ini + k == i
        tt = int(tam * (1.12 if actual else 1.0))
        d.text((x + w / 2 - P.fuente(tam).getlength(" ") / 2, y), s, font=P.fuente(tt), fill=AMA if actual else BLA, anchor="mm",
               stroke_width=9, stroke_fill=(10, 10, 16))
        x += w


def barra_tiempo(d, u, txt=None):
    """Barra de arriba que se vacía (urgencia). u = 1 → llena, 0 → vacía."""
    d.rounded_rectangle((40, 40, W - 40, 78), 19, fill=(15, 15, 22, 230))
    c = AMA if u > 0.33 else ROJ
    if u > 0:
        d.rounded_rectangle((46, 46, 46 + (W - 92) * u, 72), 13, fill=c)
    if txt:
        P.texto(d, (W / 2, 59), txt, 26, (15, 15, 22), 0)


def camara(im, t, cortes, shake=0.0):
    """Punch-in alternado en cada corte (1,00x ↔ 1,12x, con golpe de 0,12 s) + temblor opcional."""
    cortes = sorted(cortes)
    k = sum(1 for c in cortes if c <= t)
    z = 1.12 if k % 2 else 1.0
    if t < 0.4:                                                                # gancho: entra con zoom que se abre
        z = 1.0 + 0.25 * (1 - t / 0.4) ** 2
    if cortes and k:
        e = t - cortes[k - 1]
        if e < 0.12:
            z += 0.06 * (1 - e / 0.12)
    dx = dy = 0
    if shake:
        dx = shake * math.sin(t * 91) * 14; dy = shake * math.cos(t * 77) * 14
    if z == 1.0 and not shake:
        return im
    w, h = W / z, H / z
    x0 = (W - w) / 2 + dx; y0 = (H - h) / 2 + dy
    return im.crop((int(x0), int(y0), int(x0 + w), int(y0 + h))).resize((W, H), Image.BILINEAR)


def destello(im, e, color=(255, 255, 255), dur=0.15, alfa=200):
    if 0 <= e < dur:
        im.alpha_composite(Image.new("RGBA", (W, H), color + (int(alfa * (1 - e / dur)),)))


# ------------------------------------------------------------------ sonidos extra
def sirena(d=0.9):
    t = np.arange(int(d * M.SR)) / M.SR
    f = 700 + 350 * np.sin(2 * np.pi * 3.2 * t)
    return np.sign(np.sin(2 * np.pi * np.cumsum(f) / M.SR)) * np.exp(-t * 1.2) * 0.12


def latido(d=0.5):
    t = np.arange(int(d * M.SR)) / M.SR
    a = np.sin(2 * np.pi * 52 * t) * np.exp(-t * 22); b = np.sin(2 * np.pi * 48 * (t - 0.16)) * np.exp(-np.clip(t - 0.16, 0, None) * 22) * (t > 0.16)
    return (a + 0.8 * b) * 0.9


def tic(d=0.05, f=2400):
    t = np.arange(int(d * M.SR)) / M.SR
    return np.sin(2 * np.pi * f * t) * np.exp(-t * 90) * 0.35


def caja(d=0.6):
    t = np.arange(int(d * M.SR)) / M.SR
    return (np.sin(2 * np.pi * 2093 * t) + np.sin(2 * np.pi * 2637 * t)) * np.exp(-t * 7) * 0.18 + M.golpe(0.12).sum() * 0


def obturador(d=0.06, semilla=3):
    nz = np.random.default_rng(semilla).standard_normal(int(d * M.SR)); t = np.arange(len(nz)) / M.SR
    return nz * np.exp(-t * 80) * 0.25


def suspenso(d=6.0):
    t = np.arange(int(d * M.SR)) / M.SR
    f = 110 * 2 ** (t / d * 1.5)
    return np.sin(2 * np.pi * np.cumsum(f) / M.SR) * (0.05 + 0.18 * t / d) + np.sin(2 * np.pi * np.cumsum(f * 1.5) / M.SR) * 0.06 * t / d


def zumbido(d, f=55.0, pulso=2.0):
    """Zumbido grave de tensión: dos senos (fundamental + quinta) con un pulso lento de volumen y un sub que respira."""
    t = np.arange(int(d * M.SR)) / M.SR
    env = np.minimum(t / 0.4, 1) * np.minimum((d - t) / 0.15, 1)
    lfo = 0.6 + 0.4 * np.sin(2 * np.pi * pulso * t) ** 2
    x = np.sin(2 * np.pi * f * t) + 0.5 * np.sin(2 * np.pi * f * 1.5 * t) + 0.3 * np.sin(2 * np.pi * f * 0.5 * t)
    return (x * lfo * env * 0.22).astype(np.float32)


def subida(d=1.6):
    """Riser antes de cada respuesta: tono que sube + ruido que se abre, y corta seco (el golpe lo da el stinger)."""
    t = np.arange(int(d * M.SR)) / M.SR; u = t / d
    f = 90 * 2 ** (u * 2.2)
    tono = np.sin(2 * np.pi * np.cumsum(f) / M.SR) + 0.4 * np.sin(2 * np.pi * np.cumsum(f * 2) / M.SR)
    nz = np.random.default_rng(5).standard_normal(len(t))
    ruido = np.convolve(nz, np.ones(9) / 9, mode="same") * u ** 2
    return ((tono * 0.16 + ruido * 0.35) * u ** 1.5).astype(np.float32)


def stinger(d=1.2):
    """Golpe de revelación: bombo grave + platillo suave."""
    t = np.arange(int(d * M.SR)) / M.SR
    bombo = np.sin(2 * np.pi * (40 + 90 * np.exp(-14 * t)) * t) * np.exp(-3.2 * t)
    nz = np.random.default_rng(9).standard_normal(len(t)) * np.exp(-5 * t)
    return (bombo * 0.9 + np.convolve(nz, np.ones(4) / 4, mode="same") * 0.12).astype(np.float32)


def reloj(d, paso=0.5):
    """Tic-tac grave (madera), no agudo."""
    out = np.zeros(int(d * M.SR), np.float32); k = 0
    while k * paso < d:
        s_ = tic(0.06, 900 if k % 2 else 700) * 1.2; a = int(k * paso * M.SR); out[a:a + len(s_)] += s_[: len(out) - a]; k += 1
    return out


def arranque_consola(d=0.9):
    out = np.zeros(int(d * M.SR), np.float32)
    for i, f in enumerate((523, 659, 784, 1046)):
        s = M.pluck(f, 0.35, 0.3); a = int(i * 0.09 * M.SR); out[a:a + len(s)] += s[: len(out) - a]
    return out


def bip(d=0.12, f=1000):
    t = np.arange(int(d * M.SR)) / M.SR
    return np.sign(np.sin(2 * np.pi * f * t)) * np.exp(-t * 18) * 0.14


def aplausos(d=2.5):
    return M.tribuna(d, 7) * 0.7


def meme(nombre, vol=1.0):
    try:
        import render_runner as RR
        return RR.sfx(nombre, vol=vol)
    except Exception:
        return np.zeros(1, np.float32)


# ------------------------------------------------------------------ armado general
class Video:
    def __init__(self, g, escenas):
        """escenas: [(nombre, duración_mínima, índice_de_línea_de_voz_o_None)] → arma la línea de tiempo según la voz."""
        self.g = g; self.ini = {}; self.voces = []; self.palabras = []; t = 0.0
        for nombre, dmin, iv in escenas:
            self.ini[nombre] = t; d = dmin
            if iv is not None:
                s, dv = voz(g["voz_lineas"][iv]); tv = t + 0.12
                self.voces.append((tv, s)); self.palabras += tiempos_palabras(g["voz_lineas"][iv], tv, dv)
                d = max(dmin, dv + 0.45)
            t += d
        self.dur = t; self.cortes = []; self.mix = M.Mezcla(t); self.y_sub = 1300; self.sub_ancho = 980

    def fin(self, nombre):
        ks = list(self.ini); i = ks.index(nombre)
        return self.ini[ks[i + 1]] if i + 1 < len(ks) else self.dur

    def render(self, cuadro, beat_vol=0.42, cortar_final=False):
        g = self.g
        out = ROOT / "salida" / g["id"]; out.mkdir(parents=True, exist_ok=True)
        mudo = out / "mudo.mp4"
        p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                              "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", str(mudo)], stdin=subprocess.PIPE)
        for f in range(int(round(self.dur * FPS))):
            t = f / FPS
            im, shake = cuadro(t)
            im = camara(im, t, self.cortes, shake)
            subtitulos(im, self.palabras, t, self.y_sub(t) if callable(self.y_sub) else self.y_sub, ancho=self.sub_ancho, cx=W / 2 - (W - 40 - self.sub_ancho) / 2 + 20 if self.sub_ancho < 980 else W / 2)
            p.stdin.write(np.asarray(im.convert("RGB"), np.uint8).tobytes())
        p.stdin.close(); p.wait()
        n = int(self.dur * M.SR)
        vz = np.zeros(n + M.SR, np.float32)
        for tv, s in self.voces:
            i = int(tv * M.SR); j = min(len(vz), i + len(s)); vz[i:j] += s[: j - i]
        vz = vz[:n]
        for c in self.cortes:                                                  # cada corte: whoosh + golpe
            self.mix.add(c - 0.08, M.whoosh(0.3), 0.55); self.mix.add(c, M.golpe(0.12), 0.7)
        efectos = self.mix.x[:n]
        beat = M.beat_pista(self.dur, bpm=g.get("bpm", 132))[:n]
        env = np.convolve(np.abs(vz), np.ones(2205) / 2205, mode="same")
        duck = 1 - 0.6 * np.clip(env * 10, 0, 1)                              # la música baja cuando habla la voz
        if cortar_final:                                                       # corte seco al final (suspenso sin resolver)
            k = int(0.12 * M.SR); beat[-k:] = 0; efectos[-k:] = 0
        con = beat * beat_vol * duck + efectos * 0.8 + vz * 1.05
        solo = efectos * 0.8 + vz * 1.05
        M.mezclar(out, mudo, {"short.mp4": np.tanh(con * 1.1) * 0.92, "short_sin_musica.mp4": np.tanh(solo * 1.1) * 0.85})
        print(out / "short.mp4", round(self.dur, 2), "s")


# ================================================================== 1 · HIDDEN TRANSFER
def fichaje(g):
    V = Video(g, [("gancho", 3.0, 0), ("clubes", 4.6, 1), ("precio", 4.6, 2), ("silueta", 4.8, 3), ("revela", 3.2, 4)]); V.y_sub = 1560
    I = V.ini; V.cortes = [I["clubes"], I["precio"], I["silueta"], I["revela"]] + [I["clubes"] + 2.4, I["precio"] + 2.5, I["silueta"] + 2.6]
    base = fondo((150, 0, 30), (20, 0, 90))
    cuerpo = recorte(g["cuerpo"], 860)
    sil = silueta(cuerpo); neo = neon(cuerpo, (60, 220, 255), 9)
    escs = [escudo(c, 330) for c in g["clubes"]]
    estrellas = [recorte(r, 250) for r in g.get("no_son", ["torsos/cristiano_ronaldo_0", "torsos/lionel_messi_0", "torsos/kylian_mbapp_0"])]
    T_FIN = I["revela"]                                                       # la barra se vacía justo antes de la respuesta
    mx = V.mix
    mx.add(0.0, sirena(1.0), 0.9); mx.add(0.0, M.silbato(), 0.8)
    for k in range(3):
        mx.add(0.35 + k * 0.3, M.golpe(0.12), 1.0); mx.add(0.35 + k * 0.3, M.boom(0.4), 0.5)       # cada X
    mx.add(I["clubes"], zumbido(I["revela"] - I["clubes"], 49, 1.6), 1.0)                       # tensión de fondo hasta la respuesta
    mx.add(I["revela"] - 1.6, subida(1.6), 1.0); mx.add(I["revela"], stinger(), 1.0)
    for k in range(len(escs)):
        mx.add(I["clubes"] + 0.35 + k * 0.7, M.boom(0.5), 0.6); mx.add(I["clubes"] + 0.35 + k * 0.7, M.golpe(), 0.8)
    for k in range(18):                                                       # contador de plata acelerado
        mx.add(I["precio"] + 0.3 + 0.9 * (k / 18) ** 1.6, tic(0.04, 1800 + 40 * k), 0.8)
    mx.add(I["precio"] + 1.25, caja(), 1.0); mx.add(I["precio"] + 1.25, meme("caja_registradora_0", 0.7), 0.8)
    mx.add(I["precio"] + 1.9, M.golpe(), 0.9)
    k = 0; tl = I["silueta"] + 0.1
    while tl < I["revela"] - 0.1:                                             # latido que se acelera y sube
        u = (tl - I["silueta"]) / (I["revela"] - I["silueta"]); mx.add(tl, latido(), 0.5 + 0.7 * u); tl += 0.62 - 0.3 * u
    mx.add(I["revela"], M.boom(1.0), 1.0); mx.add(I["revela"], meme("explosion_0", 0.6), 0.7); mx.add(I["revela"] + 0.15, M.silbato(), 0.9)
    mx.add(I["revela"] + 0.2, M.tribuna(2.4), 0.6)

    def cuadro(t):
        im = base.copy(); d = ImageDraw.Draw(im); shake = 0.0
        rayos(im, t, color=(255, 70, 70) if t < I["clubes"] else (90, 200, 255), alfa=34)
        d = ImageDraw.Draw(im)
        barra_tiempo(d, max(0.0, 1 - t / T_FIN))
        pista = sum(1 for k in ("clubes", "precio", "silueta") if t >= I[k])
        for k in range(3):                                                    # 3 pistas: se van encendiendo
            x = W / 2 - 150 + k * 150
            d.ellipse((x - 30, 112, x + 30, 172), fill=AMA if k < pista else (50, 50, 64), outline=(15, 15, 22), width=5)
            P.texto(d, (x, 142), str(k + 1), 36, (15, 15, 22) if k < pista else (140, 140, 150), 0)
        if t < I["clubes"]:                                                   # GANCHO: ego + alerta roja
            pulso = 0.5 + 0.5 * math.sin(t * 2 * math.pi * 2.2)
            im.alpha_composite(Image.new("RGBA", (W, H), (255, 20, 30, int(50 * pulso))))
            d = ImageDraw.Draw(im)
            for k, es in enumerate(estrellas):                                 # NO es Ronaldo, NO es Messi, NO es Mbappé…
                x = W / 2 + (k - 1) * 330
                pegar(im, es, x, 700, rebote(t - k * 0.12, 9, 18, 0.25))
                if t > 0.35 + k * 0.3:
                    d = ImageDraw.Draw(im); r_ = 105; ex = rebote(t - 0.35 - k * 0.3, 10, 20, 0.3)
                    d.line((x - r_ * ex, 640 - r_ * ex, x + r_ * ex, 640 + r_ * ex), fill=ROJ, width=24)
                    d.line((x - r_ * ex, 640 + r_ * ex, x + r_ * ex, 640 - r_ * ex), fill=ROJ, width=24)
            pegar(im, neon(cuerpo, ROJ, 9), W / 2, 1180, 0.72 * rebote(t, 6, 14, 0.15))
            pegar(im, silueta(cuerpo), W / 2, 1180, 0.72 * rebote(t, 6, 14, 0.15))
            d = ImageDraw.Draw(im)
            P.texto(d, (W / 2, 1180), "?", int(280 * (1 + 0.08 * math.sin(t * 14))), AMA, 16)
            cartel(d, (W / 2, 290), "WHO IS HE? ONLY 1% KNOW", 86, AMA)
            cartel(d, (W / 2, 410), "GUESS BEFORE THE TIMER ENDS", 56, BLA)
        elif t < I["precio"]:                                                 # PISTA 1: clubes
            e = t - I["clubes"]
            cartel(d, (W / 2, 300), "CLUE 1 · HIS CLUBS", 70, AMA)
            n = len(escs); xs = [W / 2 + (k - (n - 1) / 2) * 470 for k in range(n)]
            for k, es in enumerate(escs):
                ek = e - 0.35 - k * 0.7
                if ek >= 0:
                    pegar(im, es, xs[k], 820, rebote(ek))
            if n == 2 and e > 1.05:
                P.texto(ImageDraw.Draw(im), (W / 2, 820), "+", 170, AMA, 12)
        elif t < I["silueta"]:                                                # PISTA 2: precio
            e = t - I["precio"]; shake = 0.5 if e < 1.4 else 0.15
            cartel(d, (W / 2, 300), "CLUE 2 · HIS PRICE", 70, AMA)
            u = min(1.0, e / 1.25); u = 1 - (1 - u) ** 3
            val = int(g["precio"] * u)
            col = VER if e >= 1.25 else BLA
            tam = int(150 * rebote(e - 1.25, 8, 18, 0.25)) if e >= 1.25 else 150
            P.texto(ImageDraw.Draw(im), (W / 2, 800), f"€{val:,}".replace(",", "."), tam, col, 14)
            if e >= 1.9:
                cartel(ImageDraw.Draw(im), (W / 2, 1010), f"IN {g['anio']}", int(90 * rebote(e - 1.9)), (15, 15, 22), caja=AMA + (255,))
        elif t < I["revela"]:                                                 # PISTA 3: silueta con neón
            e = t - I["silueta"]; u = e / (I["revela"] - I["silueta"])
            cartel(d, (W / 2, 300), "CLUE 3 · HIS CELEBRATION", 64, AMA)
            parpadeo = 0.55 + 0.45 * abs(math.sin(e * (6 + 10 * u)))
            pegar(im, neon(cuerpo, (60, 220, 255), 9, round(parpadeo, 1)), W / 2, 1000, 1 + 0.05 * u)
            pegar(im, sil, W / 2, 1000, 1 + 0.05 * u)
            seg = max(1, math.ceil((I["revela"] - t) / ((I["revela"] - I["silueta"]) / 3)))
            if e > 1.2:
                P.texto(ImageDraw.Draw(im), (W - 140, 560), str(seg), int(170 * (1 + 0.15 * abs(math.sin(e * 6)))), ROJ, 14)
            shake = 0.1 + 0.3 * u
        else:                                                                 # REVELACIÓN
            e = t - I["revela"]
            rayos(im, t * 3, color=AMA, alfa=40)
            pegar(im, cuerpo, W / 2, 1000, rebote(e, 7, 16, 0.2))
            d = ImageDraw.Draw(im)
            tn = 160
            while P.fuente(tn).getlength(g["nombre"].upper() + "!") > 860:
                tn -= 6
            P.texto(d, (W / 2, 340), g["nombre"].upper() + "!", int(tn * rebote(e, 8, 18, 0.3)), AMA, 16)
            if e > 0.9:
                cartel(d, (W / 2, 1400), "WHAT SECOND DID YOU GET IT?", 58, (15, 15, 22), caja=AMA + (255,))
            destello(im, e)
        return im, shake

    V.render(cuadro)


# ================================================================== 2 · WHO COST MORE?
def costo(g):
    R = g["rondas"]
    V = Video(g, [("gancho", 2.6, 0), ("r1", 3.4, 1), ("r1b", 1.8, 2), ("r2", 4.2, 3), ("r2b", 1.8, 4), ("final", 6.4, 5)])
    I = V.ini; V.cortes = [I["r1"], I["r1b"], I["r2"], I["r2b"], I["final"], I["final"] + 3.0]; V.y_sub = lambda t: 1660 if t < I["r1"] else 990; V.sub_ancho = 820
    base = fondo((0, 150, 70), (0, 30, 110))
    caras = {r[k]["ref"]: recorte(r[k]["ref"], 560) for r in R for k in (0, 1)}
    billetes = [(np.random.default_rng(i).uniform(0, W), np.random.default_rng(i + 50).uniform(-H, 0), np.random.default_rng(i + 99).uniform(-0.6, 0.6),
                 np.random.default_rng(i + 7).uniform(500, 900)) for i in range(26)]
    mx = V.mix
    mx.add(0.0, meme("caja_registradora_0", 0.8), 0.9); mx.add(0.0, M.silbato(), 0.8); mx.add(0.0, M.boom(0.6), 0.7)
    for nombre, rev in (("r1", "r1b"), ("r2", "r2b")):                       # tensión en cada ronda: zumbido + subida + golpe
        mx.add(I[nombre], zumbido(I[rev] - I[nombre], 52, 2.2), 1.0)
        mx.add(I[rev] - 1.3, subida(1.3), 0.9); mx.add(I[rev], stinger(), 0.9)
    mx.add(I["final"], zumbido(V.dur - I["final"], 46, 3.0), 1.2); mx.add(I["final"], reloj(V.dur - I["final"], 0.42), 0.9)
    for k in range(14):
        mx.add(0.05 + k * 0.11, obturador(0.05, k), 0.8)
    for nombre, rev in (("r1", "r1b"), ("r2", "r2b")):
        for s in range(3):
            mx.add(I[nombre] + 0.6 + s * 0.6, bip(0.1, 880), 1.0)
        mx.add(I[rev], M.ding(), 1.2); mx.add(I[rev], M.boom(0.6), 0.6)
    tl = I["r2"]
    while tl < I["r2b"]:
        mx.add(tl, tic(0.05, 2600 if int((tl - I["r2"]) / 0.25) % 2 else 1900), 0.9); tl += 0.25
    mx.add(I["final"], suspenso(V.dur - I["final"]), 1.0)

    def billetera(im, t, cuantos=26, alfa=255):
        d = ImageDraw.Draw(im)
        for x, y0, giro, vel in billetes[:cuantos]:
            y = (y0 + vel * t) % (H + 200) - 100
            w, h = 150, 70; a = giro + t * 1.5
            pts = [(x + c * w / 2 * math.cos(a) - s * h / 2 * math.sin(a), y + c * w / 2 * math.sin(a) + s * h / 2 * math.cos(a)) for c, s in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
            d.polygon(pts, fill=(60, 170, 80, alfa), outline=(20, 90, 40, alfa))
            P.texto(d, (x, y), "€", 40, (230, 255, 230), 0)

    def duelo(im, t, r, e, revela, total_r, cuenta=None):
        """Pantalla dividida arriba/abajo: dos jugadores; al medio la franja de subtítulos y el VS (con la cuenta 3-2-1)."""
        def tl(d, xy, txt, tam, fill, sw=8):
            d.text(xy, txt, font=P.fuente(tam), fill=fill, anchor="lm", stroke_width=sw, stroke_fill=(10, 10, 16))
        for k, cy in ((0, 560), (1, 1420)):
            j = r[k]
            gana = revela and j["precio"] >= r[1 - k]["precio"]
            tarjeta(im, W / 2, cy, 1000, 500, borde=(VER if gana else ROJ) if revela else AMA, glow=0.9 if gana else 0.0)
            c = caras[j["ref"]].crop((0, 0, caras[j["ref"]].width, 470))
            im.alpha_composite(c, (int(W - 60 - c.width), int(cy - 240)))
            d = ImageDraw.Draw(im)
            tl(d, (80, cy - 150), j["nombre"].upper(), 76, BLA)
            if revela:
                tl(d, (80, cy + 5), j["txt"], int(120 * rebote(e - revela, 8, 18, 0.3)), VER if gana else ROJ, 10)
            else:
                tl(d, (80, cy + 5), "€ ???", 120, AMA, 10)
            tl(d, (80, cy + 150), j["detalle"], 31, (205, 205, 215), 5)
        d = ImageDraw.Draw(im)
        d.ellipse((W - 190, 990 - 80, W - 30, 990 + 80), fill=ROJ, outline=BLA, width=7)
        if cuenta:
            P.texto(d, (W - 110, 990), str(cuenta), int(110 * rebote(e % 0.6, 10, 20, 0.3)), BLA, 6)
        else:
            P.texto(d, (W - 110, 990), "VS", 64, BLA, 6)

    def cuadro(t):
        im = base.copy(); shake = 0.0
        rayos(im, t, color=(170, 255, 120), alfa=32)
        if t < I["r1"]:
            billetera(im, t)
            d = ImageDraw.Draw(im)
            f = R[2]                                                          # cuadro 0: las superestrellas de la final
            for k, xx in ((0, 280), (1, W - 280)):
                pegar(im, neon(caras[f[k]["ref"]], AMA, 7), xx, 1060, 1.25 * rebote(t - k * 0.1, 8, 16, 0.2))
                pegar(im, caras[f[k]["ref"]], xx, 1060, 1.25 * rebote(t - k * 0.1, 8, 16, 0.2))
            d = ImageDraw.Draw(im)
            for k, xx in ((0, 280), (1, W - 280)):
                cartel(d, (xx, 1480), "€ ???", int(96 * (1 + 0.06 * math.sin(t * 12 + k))), (15, 15, 22), caja=AMA + (255,))
            d.ellipse((W / 2 - 90, 1060 - 90, W / 2 + 90, 1060 + 90), fill=ROJ, outline=BLA, width=8)
            P.texto(d, (W / 2, 1060), "VS", 76, BLA, 6)
            cartel(d, (W / 2, 330), "WHO COST MORE?", int(120 * rebote(t, 6, 16, 0.2)), AMA)
            cartel(d, (W / 2, 470), "3 ROUNDS · NO GOOGLE", 60, BLA)
        elif t < I["r2"]:
            ronda = R[0]; e = t - I["r1"]; rv = I["r1b"] - I["r1"]
            n = 3 - int((e - 0.5) / 0.6) if (t < I["r1b"] and e > 0.5) else 0
            duelo(im, t, ronda, e, rv if t >= I["r1b"] else 0, 3, n if n >= 1 else None)
            d = ImageDraw.Draw(im)
            cartel(d, (W / 2, 190), "ROUND 1", 64, AMA)
            destello(im, t - I["r1b"], VER, 0.18, 120)
        elif t < I["final"]:
            ronda = R[1]; e = t - I["r2"]; rv = I["r2b"] - I["r2"]
            duelo(im, t, ronda, e, rv if t >= I["r2b"] else 0, 3)
            d = ImageDraw.Draw(im)
            cartel(d, (W / 2, 190), "ROUND 2 · ALMOST NOBODY GETS IT", 54, AMA)
            barra_tiempo(d, max(0.0, 1 - e / max(0.1, rv)) if t < I["r2b"] else 0.0)
            if t >= I["r2b"]:                                                  # fuego del ganador: chispas naranjas
                ee = t - I["r2b"]; gana = 0 if ronda[0]["precio"] > ronda[1]["precio"] else 1
                cy = 560 if gana == 0 else 1420
                rng = np.random.default_rng(int(t * 30))
                for _ in range(40):
                    x = rng.uniform(80, W - 80); y = cy + 300 - rng.uniform(0, 640) * min(1, ee * 2)
                    r_ = rng.uniform(6, 16); d.ellipse((x - r_, y - r_, x + r_, y + r_), fill=(255, int(rng.uniform(90, 200)), 20, 220))
            destello(im, t - I["r2b"], (255, 140, 20), 0.2, 130)
        else:
            ronda = R[2]; e = t - I["final"]
            duelo(im, t, ronda, e, 0, 3)
            d = ImageDraw.Draw(im)
            cartel(d, (W / 2, 190), "FINAL ROUND", 74, ROJ)
            if e > 2.6:
                pul = 1 + 0.08 * math.sin(e * 9)
                cartel(d, (W / 2, 1755), "COMMENT BEFORE THE ANSWER", int(62 * pul), (15, 15, 22), caja=AMA + (255,))
            shake = 0.08 + 0.25 * (e / (V.dur - I["final"]))
        return im, shake

    V.render(cuadro, cortar_final=True)


# ================================================================== 3 · BUILD YOUR BALLON D'OR PLAYER
def balon(g):
    V = Video(g, [("gancho", 3.0, 0), ("pie", 5.6, 1), ("academia", 5.4, 2), ("socio", 4.6, 3), ("final", 3.6, 4)])
    I = V.ini; V.cortes = [I["pie"], I["academia"], I["socio"], I["final"], I["pie"] + 2.8, I["academia"] + 2.7, I["socio"] + 2.3]; V.y_sub = 1430
    base = fondo((190, 110, 0), (70, 0, 140))
    pies = [(recorte(r, 820), n) for r, n in g["pies"]]
    acad = [(escudo(c, 380) if c != "x" else None, n) for c, n in g["academias"]]
    socios = [(recorte(r, 620), n) for r, n in g["socios"]]
    caras_gancho = [recorte(r, 700) for r in g.get("gancho", ["torsos/lionel_messi_0", "torsos/cristiano_ronaldo_0"])]
    trofeo = balon_dorado(760)
    mx = V.mix
    mx.add(0.0, arranque_consola(), 1.0); mx.add(0.05, M.silbato(), 0.8); mx.add(0.0, M.boom(0.6), 0.7)
    for nombre in ("pie", "academia", "socio"):                              # cada decisión: zumbido grave y subida al final
        mx.add(I[nombre], zumbido(V.fin(nombre) - I[nombre], 50 + 4 * ["pie", "academia", "socio"].index(nombre), 2.4), 1.0)
        mx.add(V.fin(nombre) - 1.2, subida(1.2), 0.8)
    mx.add(I["final"], stinger(), 1.0)
    for s in range(3):
        mx.add(I["pie"] + 2.6 + s * 0.65, bip(0.12, 1000 if s < 2 else 1500), 1.0)
    tl = I["pie"] + 0.2
    while tl < I["academia"] - 0.1:
        mx.add(tl, tic(0.04, 1400), 0.6); tl += 0.32
    for nombre, vel in (("academia", 0.16), ("socio", 0.14)):
        tl = I[nombre] + 0.3
        while tl < V.fin(nombre) - 0.05:
            mx.add(tl, obturador(0.05, int(tl * 100)), 1.0); tl += vel
    mx.add(I["final"], M.boom(0.8), 0.8); mx.add(I["final"], aplausos(3.4), 1.0); mx.add(I["final"] + 0.1, M.ding(), 1.0)

    def girar(lista, t0, t, vel):
        return lista[int((t - t0) / vel) % len(lista)], ((t - t0) / vel) % 1

    def cuadro(t):
        im = base.copy(); shake = 0.0
        rayos(im, t, color=(255, 240, 120), alfa=34)
        d = ImageDraw.Draw(im)
        paso = sum(1 for k in ("pie", "academia", "socio") if t >= I[k])
        for k in range(3):                                                     # 3 decisiones (estilo videojuego)
            x = W / 2 - 170 + k * 170
            d.rounded_rectangle((x - 70, 110, x + 70, 170), 18, fill=AMA if k < paso else (50, 50, 64))
            P.texto(d, (x, 140), f"PICK {k + 1}", 30, (15, 15, 22) if k < paso else (150, 150, 160), 0)
        if t < I["pie"]:
            e = t
            for k, img in enumerate(caras_gancho):                           # cuadro 0: Messi y Ronaldo grandes, el trofeo al medio
                xx = 250 if k == 0 else W - 250
                pegar(im, neon(img, AMA, 8), xx, 1050, rebote(e - k * 0.1, 8, 16, 0.2))
                pegar(im, img, xx, 1050, rebote(e - k * 0.1, 8, 16, 0.2))
            if trofeo is not None:
                pegar(im, trofeo, W / 2, 1180, 0.62 * rebote(e - 0.2, 6, 14, 0.25))
            d = ImageDraw.Draw(im)
            cartel(d, (W / 2, 300), "BUILD YOUR PLAYER", int(100 * rebote(e, 6, 16, 0.2)), AMA)
            cartel(d, (W / 2, 430), "TO WIN THE BALLON D'OR", 66, BLA)
            pu = 1 + 0.1 * math.sin(e * 10)                                     # botón de pausa: la tarea, sin leer nada
            cx_, cy_ = W / 2, 1610
            d.rounded_rectangle((cx_ - 250 * pu, cy_ - 70 * pu, cx_ + 250 * pu, cy_ + 70 * pu), 40, fill=AMA)
            d.rectangle((cx_ - 200 * pu, cy_ - 36 * pu, cx_ - 182 * pu, cy_ + 36 * pu), fill=(15, 15, 22))
            d.rectangle((cx_ - 165 * pu, cy_ - 36 * pu, cx_ - 147 * pu, cy_ + 36 * pu), fill=(15, 15, 22))
            d.text((cx_ + 30 * pu, cy_), "PAUSE TO PICK", font=P.fuente(int(56 * pu)), fill=(15, 15, 22), anchor="mm")
        elif t < I["academia"]:
            e = t - I["pie"]
            sel = int(e / 0.32) % 2                                            # la luz salta entre las dos opciones (pausá)
            cartel(d, (W / 2, 280), "PICK 1 · YOUR STRONG FOOT", 64, AMA)
            for k, (img, nom) in enumerate(pies):
                cy = 610 if k == 0 else 1110
                on = k == sel
                tarjeta(im, W / 2, cy, 980, 440, borde=AMA if on else (90, 90, 110), glow=1.0 if on else 0.0,
                        fondo_c=(40, 34, 10, 240) if on else (20, 22, 40, 235))
                pierna = img.crop((0, int(img.height * 0.5), img.width, img.height)); pierna = pierna.resize((int(pierna.width * 0.95), int(pierna.height * 0.95)))
                pegar(im, pierna, W - 90 - pierna.width / 2, cy)
                d = ImageDraw.Draw(im)
                for r_, linea in enumerate(nom.split("'S ")):
                    d.text((80, cy - 45 + r_ * 95), linea + ("'S" if r_ == 0 and "'S " in nom else ""), font=P.fuente(84 if on else 72),
                           fill=AMA if on else BLA, anchor="lm", stroke_width=8, stroke_fill=(10, 10, 16))
            if e > 2.5:
                n = 3 - int((e - 2.5) / 0.65)
                if n >= 1:
                    d = ImageDraw.Draw(im)
                    d.ellipse((W / 2 - 75, 860 - 75, W / 2 + 75, 860 + 75), fill=ROJ, outline=BLA, width=7)
                    P.texto(d, (W / 2, 860), str(n), int(110 * rebote((e - 2.5) % 0.65, 10, 20, 0.3)), BLA, 6)
        elif t < I["socio"]:
            e = t - I["academia"]
            cartel(d, (W / 2, 280), "PICK 2 · PAUSE ON YOUR ACADEMY", 58, AMA)
            (img, nom), u = girar(acad, I["academia"], t, 0.16)
            tarjeta(im, W / 2, 900, 760, 760, borde=ROJ if nom == "YOU LOSE" else AMA, glow=0.7)
            if nom == "YOU LOSE":
                P.texto(ImageDraw.Draw(im), (W / 2, 860), "💀" if False else "X", 360, ROJ, 16)
            else:
                pegar(im, img, W / 2, 860, 1 + 0.06 * (1 - u))
            P.texto(ImageDraw.Draw(im), (W / 2, 1180), nom, 70, ROJ if nom == "YOU LOSE" else BLA, 8)
            cartel(ImageDraw.Draw(im), (W / 2, 1640), "PAUSE NOW!", int(84 * (1 + 0.1 * math.sin(e * 12))), (15, 15, 22), caja=AMA + (255,))
            shake = 0.1
        elif t < I["final"]:
            e = t - I["socio"]
            cartel(d, (W / 2, 280), "PICK 3 · YOUR STRIKE PARTNER", 60, AMA)
            (img, nom), u = girar(socios, I["socio"], t, 0.14)
            tarjeta(im, W / 2, 900, 760, 760, borde=AMA, glow=0.7)
            pegar(im, img, W / 2, 900, 1 + 0.05 * (1 - u))
            P.texto(ImageDraw.Draw(im), (W / 2, 1200), nom.upper(), 76, BLA, 8)
            cartel(ImageDraw.Draw(im), (W / 2, 1640), "PAUSE NOW!", int(84 * (1 + 0.1 * math.sin(e * 12))), (15, 15, 22), caja=AMA + (255,))
            shake = 0.12
        else:
            e = t - I["final"]
            rayos(im, t * 4, color=AMA, alfa=46)
            if trofeo is not None:
                pegar(im, trofeo, W / 2, 1000, rebote(e, 7, 16, 0.25))
            d = ImageDraw.Draw(im)
            cartel(d, (W / 2, 320), "DID YOU WIN IT?", int(110 * rebote(e, 8, 18, 0.3)), AMA)
            if e > 0.8:
                cartel(d, (W / 2, 1640), "COMMENT YOUR 3 PICKS", 66, (15, 15, 22), caja=AMA + (255,))
            rng = np.random.default_rng(int(t * 30))                           # confeti
            for _ in range(60):
                x = rng.uniform(0, W); y = (rng.uniform(0, H) + e * 900) % H; c = [AMA, BLA, ROJ, VER][int(rng.integers(4))]
                d.rectangle((x, y, x + 14, y + 24), fill=c)
            destello(im, e)
        return im, shake

    V.render(cuadro)


if __name__ == "__main__":
    g = json.loads(Path(sys.argv[1]).read_text())
    {"fichaje": fichaje, "costo": costo, "balon": balon}[g["formato"]](g)
