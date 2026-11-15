#!/usr/bin/env python3
"""
STOP ON YOUR FAVORITE (15/11 · idea aprobada por el CEO; mercado: "CAN YOU STOP THE BALL ON YOUR FAVORITE PLAYER?" 1,3 M en 3 días).
6 caras GRANDES (3 estrellas de hoy + 3 leyendas: Ronaldinho, Zidane, Beckham, Henry, Zlatan; 2 columnas x 3 filas). Una pelota salta de carta en carta, cada vez más rápido y después
frena: hay que PAUSAR cuando cae en tu favorito. La carta donde cae se ilumina (aro dorado + destello + "golpe").
No hay respuesta correcta: la gracia es el comentario ("¿en quién la paraste?"). Loop: la pelota vuelve a la carta del cuadro 0.
Superestrella en el cuadro 0 (la pelota arranca sobre ella). Sin datos en pantalla: solo cara y nombre de la carta.
Uso: python3 produccion/render_favorito.py guion.json
guion: {"id", "jugadores": [6 claves de SUPERESTRELLAS], "saltos": [índices de carta en orden], "dur": 7.0, "musica", "fondo"}
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
import render_rueda as RR

ROOT = Path(__file__).resolve().parent
W, H, FPS = RR.W, RR.H, RR.FPS
D_CARA = 350                                      # 15/11 (CEO): caras GRANDES y bien visibles (antes cartas chicas)
COLS = [W / 2 - 262, W / 2 + 262]
FILAS = [545, 1020, 1495]
BALL = 190
NOMBRE = {"lionel_messi": "MESSI", "cristiano_ronaldo": "RONALDO", "kylian_mbapp": "MBAPPÉ", "lamine_yamal": "YAMAL",
          "neymar": "NEYMAR", "vin_cius_j_nior": "VINÍCIUS", "ronaldinho": "RONALDINHO", "zinedine_zidane": "ZIDANE",
          "david_beckham": "BECKHAM", "thierry_henry": "HENRY", "zlatan_ibrahimovi": "ZLATAN"}
LEYENDAS = {"ronaldinho", "zinedine_zidane", "david_beckham", "thierry_henry", "zlatan_ibrahimovi"}


@lru_cache(maxsize=16)
def carta(clave):
    """Cara redonda grande con aro (dorado para las leyendas, blanco para las estrellas de hoy) y el nombre abajo."""
    cara = P.cara(clave, D_CARA)
    col = (255, 205, 40) if clave in LEYENDAS else (255, 255, 255)
    c = P.con_aro(cara, col, 14)
    out = Image.new("RGBA", (c.width, c.height + 70), (0, 0, 0, 0))
    out.alpha_composite(c, (0, 0))
    d = ImageDraw.Draw(out)
    nom = NOMBRE.get(clave, clave.split("_")[0].upper())
    P.texto(d, (out.width / 2, c.height + 22), nom, 58 if len(nom) <= 8 else 46, (255, 255, 255), 9)   # nombres largos: letra más chica
    if clave in LEYENDAS:
        P.texto(d, (out.width / 2, 34), "LEGEND", 34, (255, 215, 40), 6)
    return out


@lru_cache(maxsize=1)
def pelota():
    return Image.open(ROOT / "assets" / "recortes" / "extras" / "pelota_1.png").convert("RGBA").resize((BALL, BALL), Image.LANCZOS)


def centro(i):
    return COLS[i % 2], FILAS[i // 2]


def tiempos(n, dur):
    """Instantes de aterrizaje: arranca lento, acelera (tensión) y frena al final (lo justo para pausar)."""
    u = np.linspace(0, 1, n)
    vel = 0.55 + 1.6 * np.sin(np.pi * u) ** 2                              # saltos por unidad: lento → rápido → lento
    paso = 1 / vel
    t = np.cumsum(paso); t = t / t[-1] * dur
    return [0.0] + list(t[:-1])


def pos_pelota(g, ts, t):
    sal = g["saltos"]
    k = max(i for i, x in enumerate(ts) if x <= t + 1e-9)
    a = sal[k]; b = sal[(k + 1) % len(sal)]
    t0 = ts[k]; t1 = ts[k + 1] if k + 1 < len(ts) else g["dur"]
    u = min(1.0, (t - t0) / max(1e-6, t1 - t0))
    (x0, y0), (x1, y1) = centro(a), centro(b)
    alto = 140 + 0.25 * math.hypot(x1 - x0, y1 - y0)
    x = x0 + (x1 - x0) * u
    y = y0 + (y1 - y0) * u - alto * 4 * u * (1 - u)                        # parábola: salta de carta a carta
    return x, y, a, t - t0


def cuadro(g, A, ts, t):
    im = A["fondo"].copy()
    d = ImageDraw.Draw(im)
    x, y, actual, desde = pos_pelota(g, ts, t)
    for i, c in enumerate(g["jugadores"]):
        cx, cy = centro(i)
        ca = A["cartas"][i]
        if i == actual and desde < 0.35:                                    # la carta donde cayó: aro dorado y un salto chico
            e = desde / 0.35
            s = 1 + 0.08 * math.sin(math.pi * e)
            ca2 = ca.resize((int(ca.width * s), int(ca.height * s)), Image.LANCZOS)
            glow = Image.new("RGBA", (ca2.width + 80, ca2.width + 80), (0, 0, 0, 0))
            ImageDraw.Draw(glow).ellipse((10, 10, glow.width - 10, glow.height - 10), fill=(255, 215, 40, int(240 * (1 - e))))
            glow = glow.filter(ImageFilter.GaussianBlur(14))
            im.alpha_composite(glow, (int(cx - glow.width / 2), int(cy - ca2.width / 2 - 40)))
            im.alpha_composite(ca2, (int(cx - ca2.width / 2), int(cy - ca2.width / 2)))
        else:
            im.alpha_composite(ca, (int(cx - ca.width / 2), int(cy - ca.width / 2)))
    b = pelota().rotate(-t * 720, resample=Image.BICUBIC)
    im.alpha_composite(b, (int(x - BALL / 2), int(y - BALL / 2 + 60)))
    d = ImageDraw.Draw(im)
    if t > g["dur"] - 1.6:
        P.texto(d, (W / 2, 1840), "WHO DID YOU GET?", 74, (255, 230, 40), 11)
    import gancho as G
    G.capa(im, t, g["dur"], A["textos"], 95, ancho_max=1000, tam=80)
    return im.convert("RGB")


def audio(g, ts, dur):
    sr = M.SR; n = int(dur * sr); fx = np.zeros(n, np.float32)

    def add(t0, sig, v=1.0):
        a = int(t0 * sr) % n; b = min(n, a + len(sig)); fx[a:b] += sig[: b - a] * v
    for t in ts:
        add(t, M.golpe(0.07), 0.55)
    import gancho as G
    add(0, G.silbato(sr), 1.0)
    mu = P.musica(g, dur)
    return np.tanh((mu * 0.75 + fx) * 1.1) * 0.9, np.tanh(fx * 1.1) * 0.85


def main(guion):
    g = json.loads(Path(guion).read_text())
    out = ROOT / "salida" / g["id"]; out.mkdir(parents=True, exist_ok=True)
    dur = g["dur"]
    ts = tiempos(len(g["saltos"]), dur)
    import gancho as G
    A = dict(fondo=RR.fondo(g.get("fondo", "estadio_0")), cartas=[carta(c) for c in g["jugadores"]],
             textos=g.get("textos") or G.elegir("favorito", g["id"], ""))
    mudo = out / "mudo.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", str(mudo)], stdin=subprocess.PIPE)
    for f in range(int(round(dur * FPS))):
        p.stdin.write(np.asarray(cuadro(g, A, ts, f / FPS), np.uint8).tobytes())
    p.stdin.close(); p.wait()
    con, solo = audio(g, ts, dur)
    M.mezclar(out, mudo, {"short.mp4": con, "short_solo_efectos.mp4": solo})
    print(out / "short.mp4", dur, "s", len(ts), "saltos")


if __name__ == "__main__":
    main(sys.argv[1])
