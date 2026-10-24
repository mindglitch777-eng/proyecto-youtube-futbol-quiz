#!/usr/bin/env python3
"""
Renderiza un short "FIND THE REAL ___" (1080x1920, 30 fps) con Pillow + FFmpeg.

Diseño (sale de la investigación, reportes 03 y 10):
- gancho escrito en el cuadro 0 (la grilla ya está en pantalla: el primer cuadro decide)
- 4 rondas de dificultad creciente; la última "ONLY 1%" con distorsiones sutiles
- 3 s para pensar con barra que se vacía y tic-tac que acelera; revelación con anillo + "ding"
- cierre "HOW MANY DID YOU FIND?" y corte seco al cuadro inicial (loop)
- audio 100% propio (sintetizado): beat + efectos. Se puede sumar un sonido de tendencia desde la app al subir.

Uso: python3 produccion/render_find_the_real.py produccion/guiones/find_the_real_01.json
"""
import json
import math
import random
import subprocess
import sys
import wave
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent
FOTOS = ROOT / "assets" / "fotos"
FUENTE = str(ROOT / "assets" / "fuentes" / "Anton-Regular.ttf")
FUENTE2 = str(ROOT / "assets" / "fuentes" / "ArchivoBlack-Regular.ttf")
W, H, FPS, SR = 1080, 1920, 30, 44100
LED, VERDE, ROJO, BLANCO = (255, 210, 63), (61, 214, 128), (240, 84, 76), (255, 255, 255)

# grilla 4x4 dentro de la zona segura (los botones de Shorts tapan el borde derecho y el pie)
COLS, ROWS, TILE, GAP = 4, 4, 206, 12
GX = (W - (COLS * TILE + (COLS - 1) * GAP)) // 2 - 38
GY = 610
T_POP, T_THINK, T_REVEAL = 0.3, 3.0, 1.0
T_ROUND = T_POP + T_THINK + T_REVEAL
T_END = 1.4


# ------------------------------------------------------------------ imágenes
_cascada = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")


def recorte_cara(path, lado=512):
    img = cv2.imread(str(path))
    gris = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    caras = _cascada.detectMultiScale(gris, 1.1, 5, minSize=(60, 60))
    h, w = img.shape[:2]
    if len(caras):
        x, y, fw, fh = max(caras, key=lambda c: c[2] * c[3])
        cx, cy, s = x + fw / 2, y + fh * 0.55, fw * 2.0
    else:
        cx, cy, s = w / 2, h * 0.35, min(w, h) * 0.7
    s = min(s, w, h)
    x0 = int(np.clip(cx - s / 2, 0, w - s)); y0 = int(np.clip(cy - s / 2, 0, h - s))
    crop = img[y0:y0 + int(s), x0:x0 + int(s)]
    return cv2.resize(crop, (lado, lado), interpolation=cv2.INTER_AREA)


def _remap(img, fx):
    n = img.shape[0]
    yy, xx = np.indices((n, n), dtype=np.float32)
    cx = cy = (n - 1) / 2
    mx, my = fx(xx - cx, yy - cy)
    return cv2.remap(img, mx + cx, my + cy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


def bulge(img, k, cx=0.0, cy=0.0, radio=0.45):
    """k<1 agranda (lupa), k>1 achica. cx, cy: centro relativo al medio del recorte."""
    n = img.shape[0]; R = n * radio
    def f(x, y):
        x2, y2 = x - cx * n, y - cy * n
        r = np.sqrt(x2 ** 2 + y2 ** 2) / R
        fac = np.where(r < 1, np.power(np.clip(r, 1e-6, 1), k - 1) * 1.0, 1.0)
        fac = np.where(r < 1, fac * (1 - r) + r, 1.0) if k < 1 else fac   # borde suave
        return x2 * fac + cx * n, y2 * fac + cy * n
    return _remap(img, f)


def swirl(img, ang):
    n = img.shape[0]; R = n * 0.5
    def f(x, y):
        r = np.sqrt(x ** 2 + y ** 2); t = np.arctan2(y, x) + ang * np.clip(1 - r / R, 0, 1) ** 2
        return r * np.cos(t), r * np.sin(t)
    return _remap(img, f)


def estirar(img, sx, sy):
    return _remap(img, lambda x, y: (x / sx, y / sy))


def mitad_inferior(img, k):
    """Estira (k>1) o aplasta (k<1) la parte de abajo de la cara: mentón largo / cara chata."""
    n = img.shape[0]
    def f(x, y):
        yr = y / n
        return x, np.where(yr > 0, y / (1 + (k - 1) * np.clip(yr * 2, 0, 1)), y)
    return _remap(img, f)


# posiciones típicas en el recorte (cara centrada): ojos, nariz, boca
OJO_I, OJO_D, NARIZ, BOCA = (-0.085, -0.075), (0.085, -0.075), (0.0, 0.02), (0.0, 0.11)


def distorsion(img, intensidad, rnd):
    """Deformaciones graciosas pero reconocibles. intensidad 1 = obvia, 0.2 = sutil."""
    i = intensidad
    ops = {
        "ojos_gigantes": lambda m: bulge(bulge(m, 1 - 0.75 * i, *OJO_I, radio=0.09 + 0.05 * i), 1 - 0.75 * i, *OJO_D, radio=0.09 + 0.05 * i),
        "ojos_chicos": lambda m: bulge(bulge(m, 1 + 1.6 * i, *OJO_I, radio=0.1), 1 + 1.6 * i, *OJO_D, radio=0.1),
        "un_ojo": lambda m: bulge(m, 1 - 0.8 * i, *rnd.choice([OJO_I, OJO_D]), radio=0.11 + 0.05 * i),
        "nariz": lambda m: bulge(m, 1 - 0.7 * i, *NARIZ, radio=0.1 + 0.06 * i),
        "boca": lambda m: bulge(m, 1 - 0.7 * i, *BOCA, radio=0.1 + 0.06 * i),
        "menton": lambda m: mitad_inferior(m, 1 + 0.55 * i),
        "chata": lambda m: mitad_inferior(m, 1 - 0.35 * i),
        "ancha": lambda m: estirar(m, 1 + 0.4 * i, 1),
        "flaca": lambda m: estirar(m, 1 - 0.28 * i, 1),
        "remolino": lambda m: swirl(m, rnd.choice([-1, 1]) * 1.6 * i),
        "espejo": lambda m: m[:, ::-1].copy(),
    }
    nombres = list(ops)
    if i >= 0.3:
        nombres.remove("espejo")
    k = 1 if i < 0.3 else rnd.randint(1, 2)
    out = img
    for nm in rnd.sample(nombres, k):
        out = ops[nm](out)
    if i < 0.3 and rnd.random() < 0.5:   # ronda difícil: además un leve cambio de brillo
        out = cv2.convertScaleAbs(out, alpha=rnd.uniform(0.9, 1.1), beta=rnd.uniform(-12, 12))
    return out


def a_tile(bgr, lado=TILE, radio=26):
    im = Image.fromarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)).resize((lado, lado), Image.LANCZOS).convert("RGBA")
    m = Image.new("L", (lado, lado), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, lado - 1, lado - 1), radio, fill=255)
    im.putalpha(m)
    return im


# ------------------------------------------------------------------ dibujo
def fuente(tam, cual=FUENTE):
    return ImageFont.truetype(cual, tam)


def fondo():
    y, x = np.indices((H, W), dtype=np.float32)
    d = np.sqrt(((x - W / 2) / W) ** 2 + ((y - H * 0.55) / H) ** 2)
    base = np.array([10, 32, 26], np.float32); luz = np.array([22, 78, 58], np.float32)
    t = np.clip(1 - d * 1.9, 0, 1)[..., None]
    img = (base + (luz - base) * t).astype(np.uint8)
    im = Image.fromarray(img, "RGB")
    dr = ImageDraw.Draw(im, "RGBA")
    # líneas de cancha muy tenues
    dr.ellipse((W / 2 - 330, GY + 430 - 330, W / 2 + 330, GY + 430 + 330), outline=(255, 255, 255, 14), width=6)
    dr.line((0, GY + 430, W, GY + 430), fill=(255, 255, 255, 14), width=6)
    dr.rectangle((W / 2 - 300, H - 260, W / 2 + 300, H + 40), outline=(255, 255, 255, 12), width=6)
    return im


def texto(dr, xy, s, tam, color=BLANCO, borde=10, anchor="mm", cual=FUENTE):
    dr.text(xy, s, font=fuente(tam, cual), fill=color, stroke_width=borde, stroke_fill=(0, 0, 0), anchor=anchor)


def ajustar(s, tam_max, ancho, cual=FUENTE):
    t = tam_max
    while fuente(t, cual).getlength(s) > ancho and t > 40:
        t -= 4
    return t


def ease_out(t):
    return 1 - (1 - min(max(t, 0), 1)) ** 3


def pos_tile(i):
    c, r = i % COLS, i // COLS
    return GX + c * (TILE + GAP), GY + r * (TILE + GAP)


# ------------------------------------------------------------------ audio
def sintetizar(dur, eventos, beat=True):
    n = int(dur * SR); t = np.arange(n) / SR
    mix = np.zeros(n, np.float32)

    def add(start, sig, vol):
        i = int(start * SR); j = min(n, i + len(sig))
        if i < n:
            mix[i:j] += vol * sig[: j - i]

    def env(d, a=0.002, k=8.0):
        tt = np.arange(int(d * SR)) / SR
        return np.minimum(tt / a, 1) * np.exp(-k * tt), tt

    if beat:  # beat original tipo phonk, 140 bpm
        bpm = 140; paso = 60 / bpm / 2
        e, tt = env(0.35, k=9)
        kick = np.sin(2 * np.pi * (45 + 90 * np.exp(-25 * tt)) * tt) * e
        e2, tt2 = env(0.22, k=14)
        bell = (np.sign(np.sin(2 * np.pi * 560 * tt2)) * 0.5 + np.sign(np.sin(2 * np.pi * 845 * tt2)) * 0.5) * e2
        bell = np.convolve(bell, np.ones(6) / 6, mode="same")
        hat = np.random.default_rng(1).standard_normal(int(0.04 * SR)) * env(0.04, k=60)[0]
        patron_bell = [0, 3, 6, 8, 11, 14]
        for i in range(int(dur / paso)):
            s = i * paso
            if i % 4 == 0: add(s, kick, 0.55)
            if i % 16 in patron_bell: add(s, bell, 0.13)
            if i % 2 == 1: add(s, hat, 0.05)
    for tipo, s in eventos:
        if tipo == "tick":
            e, tt = env(0.03, k=120); add(s, np.sin(2 * np.pi * 1900 * tt) * e, 0.35)
        elif tipo == "tick2":
            e, tt = env(0.03, k=120); add(s, np.sin(2 * np.pi * 2400 * tt) * e, 0.42)
        elif tipo == "ding":
            e, tt = env(0.9, k=4.5)
            add(s, (np.sin(2 * np.pi * 1318 * tt) + 0.6 * np.sin(2 * np.pi * 1976 * tt) + 0.3 * np.sin(2 * np.pi * 2637 * tt)) * e, 0.32)
        elif tipo == "whoosh":
            d = 0.35; nz = np.random.default_rng(2).standard_normal(int(d * SR)).astype(np.float32)
            tt = np.arange(len(nz)) / SR; e = np.sin(np.pi * tt / d) ** 2
            k = np.exp(-np.linspace(4, 0.5, len(nz)))
            sig = np.convolve(nz, np.ones(18) / 18, mode="same") * e * k
            add(s, sig, 0.9)
        elif tipo == "boom":
            e, tt = env(0.8, k=5); add(s, np.sin(2 * np.pi * (38 + 60 * np.exp(-12 * tt)) * tt) * e, 0.8)
    mix = np.tanh(mix * 1.4) * 0.85
    return np.stack([mix, mix], 1)


def guardar_wav(path, audio):
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(audio, -1, 1) * 32767).astype(np.int16).tobytes())


# ------------------------------------------------------------------ principal
def main(guion_path):
    g = json.loads(Path(guion_path).read_text())
    rnd = random.Random(g.get("semilla", 7))
    out_dir = ROOT / "salida" / g["id"]; out_dir.mkdir(parents=True, exist_ok=True)
    base_bg = fondo()

    rondas = []
    usados = set()
    for r in g["rondas"]:
        cara = recorte_cara(FOTOS / f"{r['foto']}.jpg")
        real = rnd.choice([i for i in range(COLS * ROWS) if i % COLS != COLS - 1 and i not in usados])  # nunca bajo los botones
        usados.add(real)
        tiles = []
        for i in range(COLS * ROWS):
            tiles.append(a_tile(cara if i == real else distorsion(cara, r["intensidad"], rnd)))
        rondas.append({**r, "real": real, "tiles": tiles})

    dur = len(rondas) * T_ROUND + T_END
    eventos = []
    for k in range(len(rondas)):
        t0 = k * T_ROUND
        eventos.append(("whoosh", t0))
        tt = T_POP
        while tt < T_POP + T_THINK - 0.05:
            restante = T_POP + T_THINK - tt
            eventos.append(("tick2" if restante < 1.0 else "tick", t0 + tt))
            tt += 0.25 if restante < 1.0 else 0.5
        eventos.append(("ding", t0 + T_POP + T_THINK))
    eventos.append(("boom", len(rondas) * T_ROUND))
    guardar_wav(out_dir / "audio_con_beat.wav", sintetizar(dur, eventos, beat=True))
    guardar_wav(out_dir / "audio_solo_efectos.wav", sintetizar(dur, eventos, beat=False))

    nframes = int(round(dur * FPS))
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                           "-pix_fmt", "yuv420p", str(out_dir / "video_mudo.mp4")], stdin=subprocess.PIPE)

    def cuadro(t):
        im = base_bg.copy()
        dr = ImageDraw.Draw(im, "RGBA")
        k = min(int(t // T_ROUND), len(rondas) - 1)
        final = t >= len(rondas) * T_ROUND
        if final and t >= dur - 0.34:      # loop: los últimos cuadros son el primero
            return cuadro(0.0)
        tr = t - k * T_ROUND if not final else T_ROUND
        r = rondas[k]
        # cabecera
        etiqueta = r["etiqueta"]
        col_et = {"EASY": VERDE, "MEDIUM": LED, "HARD": (255, 150, 60)}.get(etiqueta, ROJO)
        f_et = fuente(44, FUENTE2); wet = f_et.getlength(etiqueta) + 50
        dr.rounded_rectangle((W / 2 - wet / 2, 150, W / 2 + wet / 2, 218), 34, fill=col_et)
        dr.text((W / 2, 184), etiqueta, font=f_et, fill=(12, 20, 16), anchor="mm")
        texto(dr, (W / 2, 300), "FIND THE REAL", 104, BLANCO, 9)
        nombre = r["nombre"].upper()
        tam = ajustar(nombre, 200, W - 120)
        pop = 1 + 0.12 * (1 - ease_out(tr / 0.25)) if tr < 0.25 and not final and k > 0 else 1
        texto(dr, (W / 2, 450), nombre, int(tam * pop), LED, 12)
        # contador de ronda
        for i in range(len(rondas)):
            cx = W / 2 + (i - (len(rondas) - 1) / 2) * 44
            dr.ellipse((cx - 11, 548, cx + 11, 570), fill=LED if i <= k else (255, 255, 255, 70))
        # grilla
        revel = tr >= T_POP + T_THINK
        p_rev = ease_out((tr - T_POP - T_THINK) / 0.35) if revel else 0
        for i, tile in enumerate(r["tiles"]):
            x, y = pos_tile(i)
            aparicion = 1 if (final or k == 0) else ease_out((tr - 0.015 * i) / 0.22)
            if aparicion <= 0:
                continue
            esc = 0.85 + 0.15 * aparicion
            es_real = i == r["real"]
            if revel and es_real:
                esc *= 1 + 0.12 * p_rev
            tl = tile if esc == 1 else tile.resize((int(TILE * esc), int(TILE * esc)), Image.LANCZOS)
            if revel and not es_real:
                a = tl.getchannel("A").point(lambda v: int(v * (1 - 0.72 * p_rev)))
                tl = tl.copy(); tl.putalpha(a)
            ox = x + (TILE - tl.width) // 2; oy = y + (TILE - tl.height) // 2
            sombra = Image.new("RGBA", tl.size, (0, 0, 0, 0)); sombra.putalpha(tl.getchannel("A").point(lambda v: v // 3))
            im.paste(sombra, (ox + 6, oy + 8), sombra)
            im.paste(tl, (ox, oy), tl)
            dr.rounded_rectangle((ox, oy, ox + tl.width - 1, oy + tl.height - 1), 26,
                                 outline=(255, 255, 255, int(120 * aparicion * (1 - 0.7 * p_rev * (not es_real)))), width=3)
        if revel:
            x, y = pos_tile(r["real"]); c = (x + TILE / 2, y + TILE / 2); rad = TILE * 0.62 + 30 * (1 - p_rev)
            dr.ellipse((c[0] - rad, c[1] - rad, c[0] + rad, c[1] + rad), outline=VERDE + (255,), width=12)
            # check
            bx, by = x + TILE - 18, y + 18
            dr.ellipse((bx - 34, by - 34, bx + 34, by + 34), fill=VERDE)
            dr.line((bx - 16, by, bx - 4, by + 13, bx + 18, by - 13), fill=(10, 30, 20), width=9, joint="curve")
        # barra de tiempo
        bx0, bx1, by0 = GX, GX + COLS * TILE + (COLS - 1) * GAP, GY + ROWS * (TILE + GAP) + 26
        dr.rounded_rectangle((bx0, by0, bx1, by0 + 26), 13, fill=(255, 255, 255, 40))
        if not final:
            frac = 1 - min(max((tr - T_POP) / T_THINK, 0), 1)
            col = LED if frac > 0.34 else ROJO
            if frac > 0:
                dr.rounded_rectangle((bx0, by0, bx0 + (bx1 - bx0) * frac, by0 + 26), 13, fill=col)
            if not revel:
                seg = math.ceil(frac * T_THINK) if tr >= T_POP else int(T_THINK)
                texto(dr, (bx1 + 52, by0 + 12), str(max(seg, 1)), 64, col, 7)
                leyenda = f"CAN YOU GET {len(rondas)}/{len(rondas)}?" if k == 0 else f"ROUND {k + 1}/{len(rondas)}"
                texto(dr, ((bx0 + bx1) / 2, by0 + 90), leyenda, 62, BLANCO, 7)
            else:
                texto(dr, ((bx0 + bx1) / 2, by0 + 90), "FOUND HIM?", 70, VERDE, 8)
        # cierre
        if final:
            te = t - len(rondas) * T_ROUND
            a = ease_out(te / 0.25)
            dr.rectangle((0, 0, W, H), fill=(4, 12, 9, int(170 * a)))
            texto(dr, (W / 2, 760), "HOW MANY", int(150 * (0.9 + 0.1 * a)), BLANCO, 12)
            texto(dr, (W / 2, 920), "DID YOU FIND?", int(132 * (0.9 + 0.1 * a)), LED, 12)
            texto(dr, (W / 2, 1110), "COMMENT YOUR SCORE /4", 64, BLANCO, 7)
            # flecha hacia comentarios
            ax, ay = W / 2, 1230 + 14 * math.sin(te * 9)
            dr.polygon([(ax - 46, ay), (ax + 46, ay), (ax, ay + 60)], fill=LED)
            dr.rectangle((ax - 16, ay - 70, ax + 16, ay + 2), fill=LED)
        return im

    for f in range(nframes):
        ff.stdin.write(cuadro(f / FPS).tobytes())
        if f % 60 == 0:
            print(f"cuadro {f}/{nframes}", file=sys.stderr)
    ff.stdin.close(); ff.wait()

    for nombre, wav in [("short_con_beat.mp4", "audio_con_beat.wav"), ("short_solo_efectos.mp4", "audio_solo_efectos.wav")]:
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(out_dir / "video_mudo.mp4"), "-i", str(out_dir / wav),
                        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", str(out_dir / nombre)], check=True)
    cuadro(0.0).save(out_dir / "portada.jpg", quality=90)
    cuadro(T_POP + T_THINK + 0.6).save(out_dir / "revelacion.jpg", quality=90)
    cuadro(len(rondas) * T_ROUND + 0.6).save(out_dir / "cierre.jpg", quality=90)
    print(f"listo: {out_dir} ({dur:.1f} s)")


if __name__ == "__main__":
    main(sys.argv[1])
