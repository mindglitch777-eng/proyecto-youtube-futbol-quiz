#!/usr/bin/env python3
"""
FOOTBALL STOP CHALLENGE (réplica de Eddy Kicks, reporte 26): 4 cuadrantes de colores, cada jugador con un hueco
negro con forma (triángulo, corazón, estrella, círculo) sobre un rasgo de la cara. El pedazo que falta orbita y pasa
por el hueco; el espectador intenta PAUSAR justo cuando encaja. Porcentaje fijo en cada cuadrante (1 %, 17 %, 69 %, 99 %).

- Loop perfecto: cada pieza da 1, 2 o 3 vueltas exactas en la duración del video y el audio es cíclico.
- Al encajar, destello en ese cuadrante + "tic": premia al que mira y le enseña cuándo pausar.
- Música propia tipo phonk (808 + cowbell) a 120 BPM, en loop.

Uso: python3 produccion/render_stop.py produccion/guiones/stop_01.json
"""
import json
import math
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

import caras_find as CF
import motor as M

ROOT = Path(__file__).resolve().parent
W, H, FPS = 1080, 1920, 30
QW, QH = W // 2, H // 2
F_TIT = str(ROOT / "assets" / "fuentes" / "ArchivoBlack-Regular.ttf")
COLORES = {"rojo": (232, 48, 48), "verde": (40, 190, 80), "amarillo": (250, 205, 30), "azul": (40, 140, 240), "violeta": (150, 70, 220)}
LADO = 480           # recorte de la cara dentro de cada cuadrante
RADIO = 105          # radio de la órbita


def forma(nombre, r):
    """Máscara L de lado 2r con la forma."""
    m = Image.new("L", (2 * r, 2 * r), 0); d = ImageDraw.Draw(m)
    if nombre == "circulo":
        d.ellipse([0, 0, 2 * r - 1, 2 * r - 1], fill=255)
    elif nombre == "triangulo":
        d.polygon([(r, 0), (2 * r - 1, 2 * r - 1), (0, 2 * r - 1)], fill=255)
    elif nombre == "estrella":
        pts = [(r + (r if k % 2 == 0 else r * 0.45) * math.sin(k * math.pi / 5), r - (r if k % 2 == 0 else r * 0.45) * math.cos(k * math.pi / 5)) for k in range(10)]
        d.polygon(pts, fill=255)
    elif nombre == "corazon":
        d.ellipse([0, 0, r * 1.1, r * 1.1], fill=255); d.ellipse([r * 0.9, 0, 2 * r - 1, r * 1.1], fill=255)
        d.polygon([(r * 0.05, r * 0.75), (2 * r - r * 0.05, r * 0.75), (r, 2 * r - 1)], fill=255)
    elif nombre == "rombo":
        d.polygon([(r, 0), (2 * r - 1, r), (r, 2 * r - 1), (0, r)], fill=255)
    return m


def borde(mask, ancho, color):
    """Contorno de una máscara como imagen RGBA."""
    a = np.asarray(mask.filter(ImageFilter.MaxFilter(ancho * 2 + 1))).astype(np.int16) - np.asarray(mask).astype(np.int16)
    out = Image.new("RGBA", mask.size, color + (0,)); out.putalpha(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)))
    return out


def texto(d, xy, s, tam, fill, stroke=10, sc=(255, 255, 255)):
    d.text(xy, s, font=ImageFont.truetype(F_TIT, tam), fill=fill, anchor="mm", stroke_width=stroke, stroke_fill=sc)


def armar(g):
    cuads = []
    for k, q in enumerate(g["cuadrantes"]):
        img, p = CF.base(q["foto"], q.get("zoom", 1.35))
        P = CF.partes(p)
        rasgo = {"ojo_izq": P["oi"], "ojo_der": P["od"], "boca": P["boca"], "nariz": P["nariz"]}[q["rasgo"]] * LADO / CF.LADO
        cara = Image.fromarray(img[..., ::-1]).resize((LADO, LADO), Image.LANCZOS).convert("RGBA")
        r = int(q.get("tam", 70))
        m = forma(q["forma"], r)
        cx, cy = int(rasgo[0]), int(rasgo[1])
        pieza = cara.crop((cx - r, cy - r, cx + r, cy + r)); pieza.putalpha(m)
        pieza.alpha_composite(borde(m, 5, (0, 0, 0)))
        hueco = Image.new("RGBA", (2 * r, 2 * r), (12, 12, 12, 255)); hueco.putalpha(m)
        cara.alpha_composite(hueco, (cx - r, cy - r))
        cara.alpha_composite(borde(m, 4, (255, 255, 255)), (cx - r, cy - r))
        x0, y0 = (k % 2) * QW, (k // 2) * QH
        abajo = k >= 2                                                       # abajo: el % arriba, lejos de la interfaz de YouTube
        fx, fy = x0 + (QW - LADO) // 2, y0 + (190 if abajo else 120)
        lado_orbita = 1 if cx < LADO / 2 else -1                             # la órbita gira hacia el centro de la foto
        cuads.append(dict(encajes=[], q=q, cara=cara, pieza=pieza, r=r, hueco=(fx + cx, fy + cy), pos=(fx, fy), x0=x0, y0=y0, abajo=abajo, dir=lado_orbita,
                          vueltas=q["vueltas"], fase=q.get("fase", 0.0), col=COLORES[q["color"]]))
    return cuads


def pieza_en(c, t, dur):
    """Posición del centro de la pieza: órbita que pasa por el hueco en el ángulo pi."""
    th = 2 * math.pi * c["vueltas"] * t / dur + c["fase"]
    hx, hy = c["hueco"]
    return hx + c["dir"] * (RADIO + RADIO * math.cos(th)), hy + RADIO * 0.75 * math.sin(th), th


def alineado(c, t, dur):
    x, y, _ = pieza_en(c, t, dur)
    return math.hypot(x - c["hueco"][0], y - c["hueco"][1])


def fondo(cuads):
    im = Image.new("RGB", (W, H)); d = ImageDraw.Draw(im)
    for c in cuads:
        d.rectangle([c["x0"], c["y0"], c["x0"] + QW, c["y0"] + QH], fill=c["col"])
        x, y = c["pos"]
        sombra = Image.new("RGBA", (LADO + 40, LADO + 40), (0, 0, 0, 0))
        ImageDraw.Draw(sombra).rounded_rectangle([20, 26, LADO + 20, LADO + 26], 28, fill=(0, 0, 0, 90))
        sombra = sombra.filter(ImageFilter.GaussianBlur(10))
        im.paste(sombra, (x - 20, y - 20), sombra)
        mk = Image.new("L", (LADO, LADO), 0); ImageDraw.Draw(mk).rounded_rectangle([0, 0, LADO - 1, LADO - 1], 28, fill=255)
        im.paste(c["cara"], (x, y), Image.fromarray(np.minimum(np.asarray(mk), np.asarray(c["cara"].split()[3]))))
        ImageDraw.Draw(im).rounded_rectangle([x - 4, y - 4, x + LADO + 3, y + LADO + 3], 30, outline=(255, 255, 255), width=8)
        y_nom, y_pct = (c["y0"] + 730, c["y0"] + 100) if c["abajo"] else (c["y0"] + 62, c["y0"] + 735)
        texto(d, (c["x0"] + QW // 2, y_nom), c["q"]["nombre"].upper(), 50, (255, 255, 255), 8, (20, 20, 30))
        texto(d, (c["x0"] + QW // 2, y_pct), c["q"]["pct"], 118, (255, 255, 255), 12, (20, 20, 30))
    d.line([(QW, 0), (QW, H)], fill=(20, 20, 30), width=10); d.line([(0, QH), (W, QH)], fill=(20, 20, 30), width=10)
    return im


def encajes(c, dur):
    """Momentos (s) en que la pieza pasa justo por el hueco."""
    pasos = np.linspace(0, dur, int(dur * 200), endpoint=False)
    ds = [alineado(c, s, dur) for s in pasos]
    return [float(pasos[j]) for j in range(len(ds)) if ds[j] < ds[j - 1] and ds[j] <= ds[(j + 1) % len(ds)] and ds[j] < 26]


DOPA = False      # modo "más dopamina": estela, chispas, PERFECT!, % que salta, temblor y fondo que late con el bajo


def desde_encaje(c, t, dur):
    """Segundos desde el último encaje de esta pieza (cíclico), o None si pasó más de 0,6 s."""
    mejor = None
    for te in c["encajes"]:
        dt = (t - te) % dur
        if dt < 0.6 and (mejor is None or dt < mejor):
            mejor = dt
    return mejor


def cuadro(fnd, cuads, t, dur):
    im = fnd.copy().convert("RGBA")
    if DOPA:                                                                  # el fondo late con cada negra
        b = (t % 0.5) / 0.5
        im.alpha_composite(Image.new("RGBA", (W, H), (255, 255, 255, int(28 * (1 - b) ** 3))))
    for c in cuads:
        if DOPA:                                                              # estela de la pieza
            for k, a in ((3, 50), (2, 85), (1, 130)):
                gx, gy, _ = pieza_en(c, t - k * 0.03, dur)
                fant = c["pieza"].copy(); fant.putalpha(c["pieza"].split()[3].point(lambda v, a=a: v * a // 255))
                capa = Image.new("RGBA", (LADO, LADO), (0, 0, 0, 0))
                capa.alpha_composite(fant, (int(gx - c["r"] - c["pos"][0]), int(gy - c["r"] - c["pos"][1])))
                im.alpha_composite(capa, c["pos"])
        x, y, _ = pieza_en(c, t, dur)
        capa = Image.new("RGBA", (LADO, LADO), (0, 0, 0, 0))                     # la pieza no sale de su foto
        capa.alpha_composite(c["pieza"], (int(x - c["r"] - c["pos"][0]), int(y - c["r"] - c["pos"][1])))
        im.alpha_composite(capa, c["pos"])
        dist = alineado(c, t, dur)
        if dist < 26:                                                         # encajó: destello en el cuadrante
            a = int(110 * (1 - dist / 26))
            capa = Image.new("RGBA", (QW, QH), (255, 255, 255, a)); im.alpha_composite(capa, (c["x0"], c["y0"]))
    d = ImageDraw.Draw(im)
    temblor = 0
    if DOPA:
        for c in cuads:
            de = desde_encaje(c, t, dur)
            if de is None:
                continue
            p = de / 0.6
            hx, hy = c["hueco"]
            rng = np.random.default_rng(int(c["x0"] + c["y0"]))
            for j in range(16):                                               # chispas
                ang = j * 2 * math.pi / 16 + rng.uniform(-0.2, 0.2)
                rr = 30 + 230 * (1 - (1 - p) ** 2) * rng.uniform(0.7, 1.1)
                sx, sy = hx + rr * math.cos(ang), hy + rr * math.sin(ang)
                tam = 14 * (1 - p) + 2
                col = (255, 230, 60, int(255 * (1 - p))) if j % 2 else (255, 255, 255, int(255 * (1 - p)))
                d.ellipse([sx - tam, sy - tam, sx + tam, sy + tam], fill=col)
            z = 0.6 + 0.5 * min(1, p / 0.25) - 0.1 * max(0, p - 0.25)
            texto(d, (c["x0"] + QW // 2, c["pos"][1] + LADO // 2 + 150), "PERFECT!", int(78 * z), (255, 230, 40), 10, (20, 20, 30))
            y_pct = c["y0"] + (100 if c["abajo"] else 735)                     # el % salta
            texto(d, (c["x0"] + QW // 2, y_pct), c["q"]["pct"], int(118 * (1 + 0.35 * (1 - p))), (255, 230, 40), 12, (20, 20, 30))
            if de < 0.1:
                temblor = 9
    pulso = 1 + 0.06 * max(0, math.cos(2 * math.pi * t * 2))                  # late con la negra (120 BPM)
    r = int(110 * pulso)
    d.ellipse([W // 2 - r, H // 2 - r, W // 2 + r, H // 2 + r], fill=(255, 255, 255), outline=(20, 20, 30), width=10)
    texto(d, (W // 2, H // 2 - 18), "STOP", int(62 * pulso), (230, 30, 30), 0)
    texto(d, (W // 2, H // 2 + 42), "AT 100%", int(26 * pulso), (20, 20, 30), 0)
    im = im.convert("RGB")
    if temblor:
        dx, dy = (temblor, -temblor // 2) if int(t * 30) % 2 else (-temblor, temblor // 2)
        im = im.transform(im.size, Image.AFFINE, (1, 0, -dx, 0, 1, -dy), fillcolor=(20, 20, 30))
    return im


def audio(cuads, dur):
    sr = M.SR; n = int(dur * sr); x = np.zeros(n, np.float32)
    def add(t0, sig, vol=1.0):                                                # cíclico: lo que sobra vuelve al principio
        i = int(t0 * sr) % n
        for j in range(0, len(sig), n):
            part = sig[j:j + n] * vol
            fin = min(n, i + len(part)); x[i:fin] += part[: fin - i]
            if i + len(part) > n:
                x[: i + len(part) - n] += part[fin - i:]
    tt = np.arange(int(0.6 * sr)) / sr
    bombo = np.sin(2 * np.pi * (45 + 90 * np.exp(-25 * tt)) * tt) * np.exp(-4.5 * tt) * 0.75                 # 808
    tc = np.arange(int(0.18 * sr)) / sr
    def cowbell(f):
        s = np.sign(np.sin(2 * np.pi * f * tc)) * 0.6 + np.sign(np.sin(2 * np.pi * f * 1.48 * tc)) * 0.4
        return np.convolve(s, np.ones(5) / 5, "same") * np.exp(-tc * 18) * 0.13
    nz = np.random.default_rng(2).standard_normal(int(0.05 * sr)).astype(np.float32)
    hat = np.diff(nz, prepend=0) * np.exp(-np.arange(len(nz)) / sr * 70) * 0.08
    clap = np.convolve(np.random.default_rng(3).standard_normal(int(0.15 * sr)), np.ones(4) / 4, "same") * np.exp(-np.arange(int(0.15 * sr)) / sr * 25) * 0.2
    negra = 0.5; mel = [740, 740, 880, 740, 660, 660, 587, 660, 740, 740, 988, 880, 740, 660, 587, 554]
    k = 0; t = 0.0
    while t < dur - 1e-6:
        if k % 4 in (0, 3) or k % 8 == 6:
            add(t, bombo)
        if k % 4 == 2:
            add(t, clap)
        add(t, hat); add(t + negra / 2, hat)
        add(t, cowbell(mel[k % len(mel)])); add(t + negra / 2, cowbell(mel[(k * 3 + 1) % len(mel)]), 0.7)
        t += negra; k += 1
    tic = np.sin(2 * np.pi * 1600 * np.arange(int(0.06 * sr)) / sr) * np.exp(-np.arange(int(0.06 * sr)) / sr * 50) * 0.3
    pasos = np.linspace(0, dur, int(dur * 200), endpoint=False)
    for c in cuads:                                                           # "tic" cada vez que una pieza encaja
        ds = [alineado(c, s, dur) for s in pasos]
        for j in range(len(ds)):
            if ds[j] < ds[j - 1] and ds[j] <= ds[(j + 1) % len(ds)] and ds[j] < 26:
                add(pasos[j], tic)
                if DOPA:
                    add(pasos[j], M.ding(0.5), 0.35)
                    add(pasos[j], M.boom(0.4), 0.25)
    return np.tanh(x * 1.2) * 0.9


def main(guion):
    g = json.loads(Path(guion).read_text())
    out = ROOT / "salida" / g["id"]; out.mkdir(parents=True, exist_ok=True)
    dur = g.get("duracion", 6.0)
    global DOPA
    DOPA = bool(g.get("dopamina"))
    cuads = armar(g); fnd = fondo(cuads)
    for c in cuads:
        c["encajes"] = encajes(c, dur)
    mudo = out / "mudo.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", str(mudo)], stdin=subprocess.PIPE)
    for f in range(int(round(dur * FPS))):
        im = cuadro(fnd, cuads, f / FPS, dur)
        p.stdin.write(np.asarray(im, np.uint8).tobytes())
        if f in (0, 45):
            im.save(out / f"muestra_{f:03d}.jpg", quality=85)
    p.stdin.close(); p.wait()
    M.mezclar(out, mudo, {"short.mp4": audio(cuads, dur)})
    print(out / "short.mp4", dur, "s")


if __name__ == "__main__":
    main(sys.argv[1])
