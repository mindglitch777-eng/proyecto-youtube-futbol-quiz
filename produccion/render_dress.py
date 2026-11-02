#!/usr/bin/env python3
"""
DRESS UP (réplica mejorada del "Dressing Challenge", 31 M): dos jugadores PELADOS sobre fondo amarillo, lista 1-2-3-4.
Caen accesorios de a pares (emojis 3D + pelo real de otro jugador recoloreado + cadena de oro):
✓ se queda (ding + check + se anota en la lista) · ✗ tiembla, X roja, "nope" y se cae. Final: "DRIP 100%" y el loop
vuelve a los pelados.

Uso: python3 produccion/render_dress.py produccion/guiones/dress_01.json
guion: {"id": "dress_01", "jugadores": ["cristiano_ronaldo", "lamine_yamal"], "musica": "trallallero_2",
        "items": [{"n": "anteojos", "ok": true}, {"n": "cadena", "ok": true}, {"n": "pelo:ronaldinho:320", "ok": false}, ...]}
"""
import json
import math
import subprocess
import sys
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

import accesorios as AC
import motor as M
import pelado as PE
import render_plinko as P

ROOT = Path(__file__).resolve().parent
W, H, FPS = 1080, 1920, 30
FONDO = (255, 228, 0)
ANCHO_B = 960
Y_BUSTO = 0                                     # se calcula: el busto apoya abajo de la pantalla
T_ITEM, T_CAE = 2.1, 1.25
T_DECIDE = T_CAE + 0.5                          # cuándo sale ✅/❌
# accesorios del video original (assets/dress): ancho en caras (A) y qué fracción de su alto va a la altura de las cejas
PNG = {"anteojos": (1.12, None), "cadena": (1.3, None), "payaso": (1.75, 0.50), "pelo_azul": (1.6, 0.62),
       "peluca_rosa": (1.62, 0.40), "pelo_verde": (1.55, 0.60)}
EMOJI = {"anteojos": "sunglasses_3d", "lentes": "glasses_3d", "antiparras": "goggles_3d", "corona": "crown_3d", "gorra": "billed_cap_3d",
         "galera": "top_hat_3d", "birrete": "graduation_cap_3d", "casco": "military_helmet_3d", "sombrero": "womans_hat_3d",
         "moño": "ribbon_3d", "medalla": "sports_medal_3d", "diamante": "gem_stone_3d"}
NOMBRE = {"pelo_verde": "HAIR", "payaso": "WIG", "pelo_azul": "HAIR", "peluca_rosa": "WIG", "anteojos": "SHADES", "lentes": "GLASSES", "antiparras": "GOGGLES", "corona": "CROWN", "gorra": "CAP", "galera": "TOP HAT",
          "birrete": "GRAD CAP", "casco": "HELMET", "sombrero": "HAT", "moño": "BOW", "medalla": "MEDAL", "diamante": "ICE",
          "cadena": "CHAIN", "pelo": "HAIR"}


@lru_cache(maxsize=64)
def emoji(nombre):
    im = Image.open(ROOT / "assets" / "fluent" / f"{EMOJI[nombre]}.png").convert("RGBA")
    if nombre == "anteojos":                                                  # lentes negros brillantes (no violetas)
        a = np.asarray(im).astype(np.float32)
        gris = a[..., :3].mean(2, keepdims=True) * 0.55
        im = Image.fromarray(np.dstack([np.repeat(gris, 3, 2), a[..., 3:]]).astype(np.uint8))
    return im


def geo(b, dx, dy):
    A = b["A"]
    return dict(p=b["puntos"] + [dx, dy], A=A, cx=b["cx"] + dx, cejas=b["cejas"] + dy, cyk=b["cejas"] + dy + A * 0.08, rx=A * 0.54, ry=A * 0.66)


def pieza(item, b, g):
    """Imagen RGBA del accesorio para ese jugador + su posición final (x, y de la esquina) en pantalla."""
    n = item["n"]; A = g["A"]; p = g["p"]
    if n.split("~")[0] in PNG:
        base_n, _, tono = n.partition("~")
        fw, fy = PNG[base_n]
        im = Image.open(ROOT / "assets" / "dress" / f"{base_n}.png").convert("RGBA")
        if tono:
            im = PE.teñir(im, int(tono), 0.8, 0.15)
        w = A * fw; im = im.resize((int(w), int(im.height * w / im.width)), Image.LANCZOS)
        if base_n == "anteojos":
            oi, od = p[36:42].mean(0), p[42:48].mean(0)
            im = im.rotate(-math.degrees(math.atan2(od[1] - oi[1], od[0] - oi[0])), expand=True, resample=Image.BICUBIC)
            c = (oi + od) / 2
            return im, (c[0] - im.width / 2, c[1] - im.height * 0.45)
        if base_n == "cadena":
            return im, (g["cx"] - im.width / 2, p[8, 1] - A * 0.12)
        return im, (g["cx"] - im.width / 2, g["cejas"] - im.height * fy)
    if n.startswith("pelo:"):
        _, donante, tono = n.split(":")
        h = PE.pelo(donante); s = A / h["A"]
        im = h["img"].resize((max(1, int(h["img"].width * s)), max(1, int(h["img"].height * s))), Image.LANCZOS)
        im = PE.teñir(im, int(tono)) if tono != "x" else im
        return im, (g["cx"] - h["cx"] * s, g["cejas"] - h["cejas"] * s)
    if n in ("cadena", "cadena_doble"):
        lienzo = AC.capa(n, dict(g, dy=0), (W, H))
        bb = lienzo.getbbox()
        return lienzo.crop(bb), (bb[0], bb[1])
    e = emoji(n)
    oi, od = p[36:42].mean(0), p[42:48].mean(0)
    if n in ("anteojos", "lentes", "antiparras"):
        w = A * (1.12 if n != "antiparras" else 1.25); im = e.resize((int(w), int(w)), Image.LANCZOS)
        ang = -math.degrees(math.atan2(od[1] - oi[1], od[0] - oi[0]))
        im = im.rotate(ang, expand=True, resample=Image.BICUBIC)
        c = (oi + od) / 2
        return im, (c[0] - im.width / 2, c[1] - im.height / 2 + A * 0.02)
    if n == "medalla":
        w = A * 0.75; im = e.resize((int(w), int(w)), Image.LANCZOS)
        return im, (g["cx"] - w / 2, p[8, 1] + A * 0.3)
    if n == "diamante":
        w = A * 0.22; im = e.resize((int(w), int(w)), Image.LANCZOS)
        return im, (p[2, 0] - A * 0.16 - w / 2, p[2, 1] - w * 0.2)           # un aro (el otro lo pone `extra`)
    escala = {"corona": 0.95, "gorra": 1.45, "galera": 1.15, "birrete": 1.35, "casco": 1.5, "sombrero": 1.7, "moño": 0.8}[n]
    base = {"corona": 0.9, "gorra": 0.62, "galera": 0.72, "birrete": 0.75, "casco": 0.6, "sombrero": 0.62, "moño": 1.0}[n]
    w = A * escala; im = e.resize((int(w), int(w)), Image.LANCZOS)
    bb = im.getbbox(); im = im.crop(bb)
    y_base = g["cyk"] - g["ry"] * base
    return im, (g["cx"] - im.width / 2, y_base - im.height * 0.78)


def armar(g):
    global Y_BUSTO
    bs = [PE.busto(k, ANCHO_B) for k in g["jugadores"]]
    Y_BUSTO = H - max(b["img"].height for b in bs) + 40
    dxs = [W / 2 - ANCHO_B + 270, W / 2 - 270]
    geos = [geo(b, dx, Y_BUSTO) for b, dx in zip(bs, dxs)]
    piezas = [[pieza(it, b, gg) for b, gg in zip(bs, geos)] for it in g["items"]]
    return bs, dxs, geos, piezas


def ok_hasta(items, k):
    return [i for i in range(k) if items[i]["ok"]]


def cuadro(g, A, t, dur):
    """Como el original: cada accesorio baja despacio; el que va se queda en su lugar, el que no va pasa de largo."""
    bs, dxs, geos, piezas = A
    items = g["items"]; n = len(items)
    im = Image.new("RGBA", (W, H), FONDO + (255,))
    for i, b in enumerate(bs):
        im.alpha_composite(b["pelado"], (int(dxs[i]), Y_BUSTO))
    t_fin = n * T_ITEM
    k_act = min(n - 1, int(t // T_ITEM)); lt = t - k_act * T_ITEM
    if t < t_fin + 0.6:
        quedan = [j for j in range(n) if items[j]["ok"] and (j < k_act or (j == k_act and lt >= T_CAE) or t >= t_fin)]
        cayendo = [k_act] if t < t_fin and not (items[k_act]["ok"] and lt >= T_CAE) else []
        orden = lambda j: 0 if items[j]["n"].split("~")[0] in ("payaso", "pelo_azul", "peluca_rosa", "pelo_verde") or items[j]["n"].startswith("pelo") else (
            1 if items[j]["n"] in ("corona", "gorra", "galera", "birrete", "casco", "sombrero", "moño") else 2)
        for j in sorted(quedan + cayendo, key=orden):
            for i in range(2):
                img, (x, y) = piezas[j][i]
                if j in cayendo:
                    if items[j]["ok"]:                                        # baja y frena justo en su lugar
                        u = lt / T_CAE; e = 1 - (1 - u) ** 2.2
                        y = (-img.height - 40) + (y + img.height + 40) * e
                    else:                                                     # pasa de largo, atravesando la cara
                        u = lt / T_ITEM
                        y = (-img.height - 40) + (H + img.height + 80) * u
                im.alpha_composite(img, (int(x), int(y)))
    d = ImageDraw.Draw(im)
    for r in range(4):
        P.texto(d, (70, 250 + r * 105), f"{r + 1}.", 86, (255, 255, 255), 9)
    return im.convert("RGB")


def audio(g, dur):
    sr = M.SR; n = int(dur * sr); fx = np.zeros(n, np.float32)

    def add(t0, sig, v=1.0):
        if sig is None:
            return
        a = int(t0 * sr)
        if a >= n:
            return
        b = min(n, a + len(sig)); fx[a:b] += sig[: b - a] * v
    for k, it in enumerate(g["items"]):
        t0 = k * T_ITEM
        add(t0, M.whoosh(0.6), 0.5)
        if it["ok"]:
            add(t0 + T_CAE, M.golpe(0.1), 0.6); add(t0 + T_CAE, M.ding(0.5), 0.45)
    tf = len(g["items"]) * T_ITEM
    add(tf + 0.8, M.whoosh(0.4), 0.5)
    mu = P.musica(g, dur)
    return np.tanh((mu * 0.7 + fx) * 1.1) * 0.9, np.tanh(fx * 1.1) * 0.85


def main(guion):
    g = json.loads(Path(guion).read_text())
    out = ROOT / "salida" / g["id"]; out.mkdir(parents=True, exist_ok=True)
    A = armar(g)
    dur = len(g["items"]) * T_ITEM + 0.9
    mudo = out / "mudo.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", str(mudo)], stdin=subprocess.PIPE)
    import gancho as G
    tx = G.textos_de(g, "dress")
    inicio = G.capa(cuadro(g, A, 0.0, dur), 0.0, dur, tx, 110)
    for f in range(int(round(dur * FPS))):
        t = f / FPS; im = G.capa(cuadro(g, A, t, dur), t, dur, tx, 110)
        if t > dur - 0.3:
            im = Image.blend(im, inicio, (t - (dur - 0.3)) / 0.3)
        p.stdin.write(np.asarray(im, np.uint8).tobytes())
    p.stdin.close(); p.wait()
    con, solo = audio(g, dur)
    M.mezclar(out, mudo, G.con_pito({"short.mp4": con, "short_solo_efectos.mp4": solo}))
    print(out / "short.mp4", round(dur, 2), "s")


if __name__ == "__main__":
    main(sys.argv[1])
