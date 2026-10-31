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
T_ITEM, T_CAE = 1.45, 0.32
EMOJI = {"anteojos": "sunglasses_3d", "lentes": "glasses_3d", "antiparras": "goggles_3d", "corona": "crown_3d", "gorra": "billed_cap_3d",
         "galera": "top_hat_3d", "birrete": "graduation_cap_3d", "casco": "military_helmet_3d", "sombrero": "womans_hat_3d",
         "moño": "ribbon_3d", "medalla": "sports_medal_3d", "diamante": "gem_stone_3d"}
NOMBRE = {"anteojos": "SHADES", "lentes": "GLASSES", "antiparras": "GOGGLES", "corona": "CROWN", "gorra": "CAP", "galera": "TOP HAT",
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
    bs, dxs, geos, piezas = A
    items = g["items"]; n = len(items)
    im = Image.new("RGBA", (W, H), FONDO + (255,))
    d = ImageDraw.Draw(im)
    off = int(t * 320) % 120                                                  # rayas diagonales que se mueven (movimiento constante)
    for k in range(-30, 30):
        x = k * 120 + off
        d.polygon([(x, 0), (x + 50, 0), (x + 50 - H * 0.4, H), (x - H * 0.4, H)], fill=(255, 245, 120, 255))
    t_fin = n * T_ITEM
    final = t >= t_fin
    # busto pelado (o con pelo original en el cierre)
    for i, b in enumerate(bs):
        base = b["img"] if (final and t > t_fin + 1.2) else b["pelado"]
        im.alpha_composite(base, (int(dxs[i]), Y_BUSTO))
    k_act = min(n - 1, int(t // T_ITEM)); lt = t - k_act * T_ITEM
    quedan = [j for j in range(n) if items[j]["ok"] and (j < k_act or (j == k_act and lt > T_CAE + 0.45) or final)]
    # orden de capas: pelo → gorros/corona → anteojos → cadena/medalla
    orden = lambda j: 0 if items[j]["n"].startswith("pelo") else (1 if items[j]["n"] in ("corona", "gorra", "galera", "birrete", "casco", "sombrero", "moño") else 2)
    activos = sorted(quedan + ([k_act] if not final and k_act not in quedan else []), key=orden)
    for j in activos:
        for i in range(2):
            img, (x, y) = piezas[j][i]
            if j == k_act and not final:
                if lt < T_CAE:                                                # cae con rebote
                    u = lt / T_CAE
                    y += -900 * (1 - u) ** 2 + 40 * math.sin(u * math.pi) * (1 - u)
                elif not items[j]["ok"] and lt > T_CAE + 0.35:                # ✗: tiembla y se cae
                    e = lt - T_CAE - 0.35
                    if e < 0.25:
                        x += 18 * math.sin(e * 80)
                    else:
                        y += 2600 * (e - 0.25) ** 2; x += (i * 2 - 1) * 300 * (e - 0.25)
                        img = img.rotate((i * 2 - 1) * -140 * (e - 0.25), expand=True, resample=Image.BICUBIC)
            im.alpha_composite(img, (int(x), int(y)))
    d = ImageDraw.Draw(im)
    # lista 1-4 con los accesorios que quedaron
    oks = [j for j in range(n) if items[j]["ok"]]
    for r in range(4):
        y = 300 + r * 115
        P.texto(d, (75, y), f"{r + 1}.", 82, (255, 255, 255), 9)
        if r < len(oks) and oks[r] in quedan:
            j = oks[r]; nm = items[j]["n"]
            ic = piezas[j][0][0].copy(); ic.thumbnail((120, 95), Image.LANCZOS)
            im.alpha_composite(ic, (130, int(y - ic.height / 2)))
            d = ImageDraw.Draw(im)
            P.texto(d, (300, y), NOMBRE.get(nm.split(":")[0], nm.upper()), 46, (40, 200, 70), 7, (20, 20, 30))
    P.texto(d, (W / 2 + 120, 110), g.get("titulo", "DRIP CHALLENGE"), 84, (255, 255, 255), 11, (20, 20, 30))
    P.texto(d, (W / 2 + 120, 200), " VS ".join(P.nombre_corto(k).upper() for k in g["jugadores"]), 56, (230, 40, 60), 8, (255, 255, 255))
    # ✓ / ✗
    if not final and lt >= T_CAE + 0.3:
        e = lt - T_CAE - 0.3
        if e < 0.6:
            esc = min(1.0, e / 0.08)
            if e < 0.15:                                                      # golpe de color en toda la pantalla
                col = (60, 230, 90) if items[k_act]["ok"] else (255, 40, 40)
                im.alpha_composite(Image.new("RGBA", (W, H), col + (int(110 * (1 - e / 0.15)),)))
            P.RR.pegar_emoji(im, "✅" if items[k_act]["ok"] else "❌", W // 2 + 250, 420, int(260 * esc) + 1)
            d = ImageDraw.Draw(im)
    if final:
        e = t - t_fin
        if e < 0.15:
            im.alpha_composite(Image.new("RGBA", (W, H), (255, 255, 255, int(220 * (1 - e / 0.15)))))
        d = ImageDraw.Draw(im)
        if e < 1.2:
            P.texto(d, (W / 2 + 150, 560), "DRIP 100%", int(130 * min(1, e / 0.1 + 0.3)), (255, 255, 255), 15, (230, 40, 60))
            for q in range(10):
                em = "🔥💎😎🥶💯"[q % 5]
                P.RR.pegar_emoji(im, em, int((q * 211 + 70) % W), int((e * 900 + q * 300) % (H + 200) - 100), 90)
        else:
            P.texto(d, (W / 2, 590), "WHO WORE IT BETTER?", 78, (255, 255, 255), 12, (20, 20, 30))
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
    nope, bruh, boing, wow = P.cargar("nope_0", 0.7), P.cargar("bruh_0", 0.7), P.cargar("boing_0", 0.6), P.cargar("wow_0", 0.6)
    for k, it in enumerate(g["items"]):
        t0 = k * T_ITEM
        add(t0, M.whoosh(0.35), 0.6); add(t0 + T_CAE, M.golpe(0.12), 0.8)
        if it["ok"]:
            add(t0 + T_CAE + 0.3, M.ding(0.6), 0.7); add(t0 + T_CAE + 0.3, P.cargar("moneda_0", 0.5))
        else:
            add(t0 + T_CAE + 0.3, nope if k % 2 else bruh); add(t0 + T_CAE + 0.6, boing)
    tf = len(g["items"]) * T_ITEM
    add(tf, M.boom(0.8), 0.7); add(tf, P.cargar("airhorn_0", 0.5)); add(tf + 0.2, P.cargar("rizz_0", 0.7))
    add(tf + 1.2, wow)
    mu = P.musica(g, dur)
    return np.tanh((mu * 0.7 + fx) * 1.1) * 0.9, np.tanh(fx * 1.1) * 0.85


def main(guion):
    g = json.loads(Path(guion).read_text())
    out = ROOT / "salida" / g["id"]; out.mkdir(parents=True, exist_ok=True)
    A = armar(g)
    dur = len(g["items"]) * T_ITEM + 2.4
    mudo = out / "mudo.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", str(mudo)], stdin=subprocess.PIPE)
    inicio = cuadro(g, A, 0.0, dur)
    for f in range(int(round(dur * FPS))):
        t = f / FPS; im = cuadro(g, A, t, dur)
        if t > dur - 0.3:
            im = Image.blend(im, inicio, (t - (dur - 0.3)) / 0.3)
        p.stdin.write(np.asarray(im, np.uint8).tobytes())
    p.stdin.close(); p.wait()
    con, solo = audio(g, dur)
    M.mezclar(out, mudo, {"short.mp4": con, "short_solo_efectos.mp4": solo})
    print(out / "short.mp4", round(dur, 2), "s")


if __name__ == "__main__":
    main(sys.argv[1])
