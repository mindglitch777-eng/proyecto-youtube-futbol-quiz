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


def silueta(im_rgba, color=(8, 8, 14)):
    a = np.asarray(im_rgba).copy(); a[..., :3] = color
    return Image.fromarray(a)


@lru_cache(maxsize=64)
def neon(im_rgba, color, grosor=10, brillo=1.0):
    """Contorno de neón alrededor de un recorte."""
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
    ini = (i // 4) * 4; grupo = palabras[ini:ini + 4]                          # de a 4 palabras (se lee de un vistazo)
    d = ImageDraw.Draw(im); tam = 84
    txts = [g[0].upper() for g in grupo]
    while tam > 46 and sum(P.fuente(tam).getlength(x + " ") for x in txts) > ancho:
        tam -= 4
    tot = sum(P.fuente(tam).getlength(x + " ") for x in txts); x = cx - tot / 2
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
            subtitulos(im, self.palabras, t, self.y_sub, ancho=self.sub_ancho, cx=W / 2 - (W - 40 - self.sub_ancho) / 2 + 20 if self.sub_ancho < 980 else W / 2)
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
    base = fondo((26, 8, 12), (8, 6, 22))
    cuerpo = recorte(g["cuerpo"], 860)
    sil = silueta(cuerpo); neo = neon(cuerpo, (60, 220, 255), 9)
    escs = [escudo(c, 330) for c in g["clubes"]]
    T_FIN = I["revela"]                                                       # la barra se vacía justo antes de la respuesta
    mx = V.mix
    mx.add(0.0, sirena(1.0), 0.9); mx.add(0.0, M.silbato(), 0.8)
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
        rayos(im, t, color=(255, 60, 60) if t < I["clubes"] else (255, 255, 255), alfa=20)
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
            pegar(im, sil, W / 2, 1000, 0.95 * rebote(t, 6, 14, 0.15))
            pegar(im, neon(cuerpo, ROJ, 9), W / 2, 1000, 0.95 * rebote(t, 6, 14, 0.15))
            pegar(im, sil, W / 2, 1000, 0.95 * rebote(t, 6, 14, 0.15))
            d = ImageDraw.Draw(im)
            P.texto(d, (W / 2, 1000), "?", 300, AMA, 16)
            cartel(d, (W / 2, 330), "ONLY 1% GUESS", 112, AMA)
            cartel(d, (W / 2, 470), "THIS TRANSFER", 112, BLA)
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
            P.texto(d, (W / 2, 330), g["nombre"].upper() + "!", int(170 * rebote(e, 8, 18, 0.3)), AMA, 16)
            if e > 0.9:
                cartel(d, (W / 2, 1450), "WHAT SECOND DID YOU GET IT?", 60, (15, 15, 22), caja=AMA + (255,))
            destello(im, e)
        return im, shake

    V.render(cuadro)


# ================================================================== 2 · WHO COST MORE?
def costo(g):
    R = g["rondas"]
    V = Video(g, [("gancho", 2.6, 0), ("r1", 3.4, 1), ("r1b", 1.8, 2), ("r2", 4.2, 3), ("r2b", 1.8, 4), ("final", 6.4, 5)])
    I = V.ini; V.cortes = [I["r1"], I["r1b"], I["r2"], I["r2b"], I["final"], I["final"] + 3.0]; V.y_sub = 990; V.sub_ancho = 820
    base = fondo((6, 40, 22), (6, 10, 26))
    caras = {r[k]["ref"]: recorte(r[k]["ref"], 560) for r in R for k in (0, 1)}
    billetes = [(np.random.default_rng(i).uniform(0, W), np.random.default_rng(i + 50).uniform(-H, 0), np.random.default_rng(i + 99).uniform(-0.6, 0.6),
                 np.random.default_rng(i + 7).uniform(500, 900)) for i in range(26)]
    mx = V.mix
    mx.add(0.0, meme("caja_registradora_0", 0.8), 0.9); mx.add(0.0, M.silbato(), 0.8)
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
            tl(d, (80, cy + 150), j["detalle"], 38, (205, 205, 215), 5)
        d = ImageDraw.Draw(im)
        d.ellipse((W - 190, 990 - 80, W - 30, 990 + 80), fill=ROJ, outline=BLA, width=7)
        if cuenta:
            P.texto(d, (W - 110, 990), str(cuenta), int(110 * rebote(e % 0.6, 10, 20, 0.3)), BLA, 6)
        else:
            P.texto(d, (W - 110, 990), "VS", 64, BLA, 6)

    def cuadro(t):
        im = base.copy(); shake = 0.0
        rayos(im, t, color=(120, 255, 150), alfa=16)
        if t < I["r1"]:
            billetera(im, t)
            d = ImageDraw.Draw(im)
            f = R[2]                                                          # cuadro 0: las superestrellas de la final
            pegar(im, caras[f[0]["ref"]], 290, 1250, 0.8); pegar(im, caras[f[1]["ref"]], W - 290, 1250, 0.8)
            d = ImageDraw.Draw(im)
            cartel(d, (W / 2, 420), "WHO COST MORE?", int(120 * rebote(t, 6, 16, 0.2)), AMA)
            cartel(d, (W / 2, 580), "3 ROUNDS · NO GOOGLE", 64, BLA)
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
    base = fondo((40, 26, 4), (10, 8, 30))
    pies = [(recorte(r, 820), n) for r, n in g["pies"]]
    acad = [(escudo(c, 380) if c != "x" else None, n) for c, n in g["academias"]]
    socios = [(recorte(r, 620), n) for r, n in g["socios"]]
    trofeo = recorte(g.get("trofeo", "extras/trofeo_bo_1"), 760) if (REC / f"{g.get('trofeo', 'extras/trofeo_bo_1')}.png").exists() else None
    mx = V.mix
    mx.add(0.0, arranque_consola(), 1.0); mx.add(0.05, M.silbato(), 0.8)
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
        rayos(im, t, color=AMA, alfa=18)
        d = ImageDraw.Draw(im)
        paso = sum(1 for k in ("pie", "academia", "socio") if t >= I[k])
        for k in range(3):                                                     # 3 decisiones (estilo videojuego)
            x = W / 2 - 170 + k * 170
            d.rounded_rectangle((x - 70, 110, x + 70, 170), 18, fill=AMA if k < paso else (50, 50, 64))
            P.texto(d, (x, 140), f"PICK {k + 1}", 30, (15, 15, 22) if k < paso else (150, 150, 160), 0)
        if t < I["pie"]:
            e = t
            if trofeo is not None:
                pegar(im, trofeo, W / 2, 1050, 0.85 * rebote(e, 6, 14, 0.2))
            for k, (img, _) in enumerate(pies[:2]):                          # cuadro 0: Messi y Ronaldo a los costados
                pegar(im, img.resize((img.width * 6 // 10, img.height * 6 // 10)), 170 + k * (W - 340), 1180)
            d = ImageDraw.Draw(im)
            cartel(d, (W / 2, 330), "BUILD YOUR PLAYER", int(100 * rebote(e, 6, 16, 0.2)), AMA)
            cartel(d, (W / 2, 470), "TO WIN THE BALLON D'OR", 70, BLA)
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
