#!/usr/bin/env python3
"""
PLINKO GOAT (formato propio): 4 pelotas con la cara de 4 jugadores caen rebotando por un tablero de clavos.
Cada rebote suena (más agudo cuanto más abajo), suma +1 al OVR del jugador en vivo y hace chispas.
Abajo: casilleros 💀 · 50 · 65 · 75 · 85 · 99 · 85 · 75 · 65 · 50 · 💀. Las que caen al lado del 99 → "SO CLOSE!" + nope;
en 💀 → "BENCH" + bruh. La que cae en el 99 → flash dorado, temblor, CARTA FUT 99 + sonido del jugador + hinchada.
Cierra con un flash blanco que empalma con el flash del cuadro 0 (loop). La física se busca con semillas hasta que
haya exactamente un ganador, al menos un casi-acierto y el ganador caiga último (suspenso hasta el final).

Uso: python3 produccion/render_plinko.py produccion/guiones/plinko_01.json
guion: {"id": "plinko_01", "jugadores": ["cristiano_ronaldo", "lionel_messi", "neymar", "lamine_yamal"], "semilla": 1,
        "titulo": "WHO GETS 99?", "musica": "trallallero_2"}
"""
import json
import math
import subprocess
import sys
from functools import lru_cache
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

import caras_find as CF
import motor as M
import render_runner as RR

ROOT = Path(__file__).resolve().parent
W, H, FPS = 1080, 1920, 30
F_TIT = str(ROOT / "assets" / "fuentes" / "ArchivoBlack-Regular.ttf")
FRONT = json.loads((ROOT / "assets" / "fotos" / "frontales.json").read_text())

# --- tablero
FILAS, Y0, DY, DX = 6, 720, 126, 148
R_PEG, R_BOLA = 12, 56
Y_SLOT0, Y_PISO = Y0 + (FILAS - 1) * DY, Y0 + (FILAS - 1) * DY + 215
VALORES = ["💀", "75", "85", "99", "85", "75", "💀"]
GANA = 3
OVR0 = 40                                                                  # OVR inicial; cada rebote +1 (al pasar por 67 → "six seven")
Y_CARTEL = Y_PISO + 120
COLORES = [(255, 70, 70), (70, 170, 255), (255, 210, 40), (90, 230, 120)]
SONIDO_JUGADOR = {"cristiano_ronaldo": ["siuuu_0", "siu_estadio_0"], "lionel_messi": ["ankara_messi_0", "messi_chant_0"],
                  "neymar": ["neymar_0", "neymar_risa_0"]}


def clavos():
    out = []
    for r in range(FILAS):
        n = r + 3
        for k in range(n):
            out.append((W / 2 + (k - (n - 1) / 2) * DX, Y0 + r * DY, r))
    return out


PEGS = clavos()
PEGS_FILA = [[p for p in PEGS if p[2] == r] for r in range(FILAS)]
ORO = {(p[0], p[1]) for p in PEGS if (p[2], round((p[0] - W / 2) / DX * 2)) in {(1, -1), (2, 2), (3, -3), (4, 0), (2, -2)}}   # clavos dorados: +5
X_DIV = [W / 2 + (k - (FILAS + 1) / 2) * DX for k in range(FILAS + 2)]       # palitos de los casilleros (= clavos de la última fila)


def borde_x(y):
    """Paredes en diagonal siguiendo la pirámide (para que nada se escape por los costados)."""
    filas = max(0.0, (y - Y0) / DY)
    return (filas + 2) / 2 * DX + 20


# ------------------------------------------------------------------ física
def simular(semilla, n=4, demora=0.38, dt=1 / 240, tmax=9.0):
    rng = np.random.default_rng(semilla)
    pos = np.array([[W / 2 + rng.uniform(-30, 30), Y0 - 170] for i in range(n)], float)
    vel = np.array([[rng.uniform(-60, 60), 0.0] for _ in range(n)])
    salida = [i * demora for i in range(n)]
    activo = [False] * n; quieto = [None] * n; casillero = [None] * n
    golpes = []                                                              # (t, bola, x, y, fila)
    tray = [[] for _ in range(n)]
    t = 0.0; ultimo = {}
    while t < tmax:
        for i in range(n):
            if not activo[i] and t >= salida[i]:
                activo[i] = True
            if not activo[i] or quieto[i] is not None:
                continue
            vel[i, 1] += 2500 * dt
            pos[i] += vel[i] * dt
            x, y = pos[i]
            rf = int(round((y - Y0) / DY))
            cerca = PEGS_FILA[rf] if 0 <= rf < FILAS and abs(y - (Y0 + rf * DY)) < R_PEG + R_BOLA + 2 else []
            for (px, py, fila) in cerca:
                dx, dy = x - px, y - py; d = math.hypot(dx, dy)
                if d < R_PEG + R_BOLA:
                    nx, ny = dx / d, dy / d
                    pos[i] = [px + nx * (R_PEG + R_BOLA), py + ny * (R_PEG + R_BOLA)]
                    vn = vel[i, 0] * nx + vel[i, 1] * ny
                    if vn < 0:
                        vel[i, 0] -= 1.55 * vn * nx; vel[i, 1] -= 1.55 * vn * ny
                        vel[i, 0] += rng.uniform(-55, 55)
                        clave = (i, px, py)
                        if t - ultimo.get(clave, -1) > 0.12:
                            golpes.append((t, i, px, py, fila)); ultimo[clave] = t
            x, y = pos[i]
            lim = borde_x(y)
            if abs(x - W / 2) > lim - R_BOLA and y < Y_SLOT0:
                pos[i, 0] = W / 2 + math.copysign(lim - R_BOLA, x - W / 2); vel[i, 0] *= -0.5
            if y > Y_SLOT0:                                                   # dentro de los casilleros: paredes verticales
                for xd in X_DIV:
                    if abs(x - xd) < R_BOLA + 4:
                        pos[i, 0] = xd + math.copysign(R_BOLA + 4, x - xd); vel[i, 0] *= -0.4
            if pos[i, 1] > Y_PISO - R_BOLA:
                pos[i, 1] = Y_PISO - R_BOLA
                if abs(vel[i, 1]) < 260:
                    vel[i] = 0; quieto[i] = t
                    casillero[i] = int(np.clip(np.searchsorted(X_DIV, pos[i, 0]) - 1, 0, len(VALORES) - 1))
                else:
                    vel[i, 1] *= -0.35; vel[i, 0] *= 0.6
        for i in range(n):                                                   # choques entre pelotas
            for j in range(i + 1, n):
                if not (activo[i] and activo[j]):
                    continue
                d = pos[i] - pos[j]; dist = np.linalg.norm(d)
                if 0 < dist < 2 * R_BOLA:
                    nrm = d / dist; sol = 2 * R_BOLA - dist
                    if quieto[i] is None:
                        pos[i] += nrm * sol / 2
                    if quieto[j] is None:
                        pos[j] -= nrm * sol / 2
                    rel = np.dot(vel[i] - vel[j], nrm)
                    if rel < 0:
                        if quieto[i] is None:
                            vel[i] -= rel * nrm * 0.9
                        if quieto[j] is None:
                            vel[j] += rel * nrm * 0.9
        for i in range(n):
            tray[i].append((t, pos[i, 0], pos[i, 1]))
        t += dt
        if all(q is not None for q in quieto):
            break
    return dict(tray=tray, golpes=golpes, quieto=quieto, casillero=casillero, salida=salida)


def buscar(semilla0, n=4):
    """Prueba semillas hasta un resultado con suspenso: un solo 99, casi-acierto, ganador último y todo en < 7,5 s."""
    for s in range(semilla0, semilla0 + 4000):
        r = simular(s, n)
        if any(q is None for q in r["quieto"]):
            continue
        c = r["casillero"]
        if c.count(GANA) != 1 or max(r["quieto"]) > 6.0:
            continue
        g = c.index(GANA)
        otros = max(q for k, q in enumerate(r["quieto"]) if k != g)
        if r["quieto"][g] - otros < 0.9 or not any(x in (GANA - 1, GANA + 1) for x in c):
            continue
        if len(set(c)) < 3:
            continue
        r["semilla"] = s; r["ganador"] = g
        return r
    raise RuntimeError("no encontré una semilla con suspenso")


def puntos(gl):
    return 5 if (gl[2], gl[3]) in ORO else 1


def ovr_en(r, i, t):
    return min(98, OVR0 + sum(puntos(gl) for gl in r["golpes"] if gl[1] == i and gl[0] <= t))


def momento67(r, i):
    """Momento en que el OVR en vivo del jugador i pasa por 67."""
    v = OVR0
    for gl in r["golpes"]:
        if gl[1] != i:
            continue
        v2 = v + puntos(gl)
        if v < 67 <= v2:
            return gl[0] if (r["quieto"][i] is None or gl[0] < r["quieto"][i]) else None
        v = v2
    return None


def posicion(r, i, t):
    tr = r["tray"][i]
    k = min(len(tr) - 1, max(0, int(t * 240)))
    return tr[k][1], tr[k][2]


# ------------------------------------------------------------------ dibujo
def fuente(tam):
    return ImageFont.truetype(F_TIT, tam)


def texto(d, xy, s, tam, fill, stroke=10, sc=(20, 20, 30)):
    d.text(xy, s, font=fuente(tam), fill=fill, anchor="mm", stroke_width=stroke, stroke_fill=sc)


@lru_cache(maxsize=64)
def cara(clave, d):
    img, _ = CF.base(FRONT.get(clave, clave + "_0"), 1.25)
    im = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)).convert("RGBA").resize((d, d), Image.LANCZOS)
    m = Image.new("L", (d * 3, d * 3), 0); ImageDraw.Draw(m).ellipse((0, 0, d * 3 - 1, d * 3 - 1), fill=255)
    im.putalpha(m.resize((d, d), Image.LANCZOS))
    return im


def con_aro(im, col, grosor):
    d = im.width + grosor * 2
    out = Image.new("RGBA", (d, d)); dr = ImageDraw.Draw(out)
    dr.ellipse((0, 0, d - 1, d - 1), fill=col + (255,)); out.alpha_composite(im, (grosor, grosor))
    return out


@lru_cache(maxsize=4)
def fondo_base():
    """Degradé violeta→azul eléctrico, claro (brillo alto en el cuadro 0) + tablero."""
    y = np.linspace(0, 1, H)[:, None]
    a, b = np.array([120, 70, 255]), np.array([40, 200, 255])
    arr = (a * (1 - y) + b * y)[:, None, :].repeat(W, 1).reshape(H, W, 3)
    im = Image.fromarray(arr.astype(np.uint8)).convert("RGBA")
    d = ImageDraw.Draw(im)
    # casilleros
    for j, v in enumerate(VALORES):
        x0, x1 = X_DIV[j], X_DIV[j + 1]
        col = (255, 200, 0) if j == GANA else (60, 60, 70) if v == "💀" else (255, 255, 255)
        d.rounded_rectangle((x0 + 5, Y_SLOT0 + 40, x1 - 5, Y_PISO + 8), 14, fill=col + (110 if j != GANA else 200,))
    for xd in X_DIV:
        d.rounded_rectangle((xd - 5, Y_SLOT0, xd + 5, Y_PISO + 8), 4, fill=(255, 255, 255, 255))
    d.rounded_rectangle((X_DIV[0] - 10, Y_PISO, X_DIV[-1] + 10, Y_PISO + 22), 8, fill=(255, 255, 255, 255))
    return im


def chispas(d, x, y, edad, col):
    for k in range(8):
        a = k * math.pi / 4 + 0.3
        r = 12 + edad * 260
        d.ellipse((x + math.cos(a) * r - 6, y + math.sin(a) * r - 6, x + math.cos(a) * r + 6, y + math.sin(a) * r + 6),
                  fill=col + (int(255 * max(0, 1 - edad / 0.3)),))


def carta(clave, nombre=None, ovr=99, col=None, brillo=None):
    import cartas
    return cartas.carta(clave, ovr, brillo)


def nombre_corto(clave):
    return {"cristiano_ronaldo": "Ronaldo", "lionel_messi": "Messi", "neymar": "Neymar", "lamine_yamal": "Yamal",
            "kylian_mbapp": "Mbappé", "erling_haaland": "Haaland", "vin_cius_j_nior": "Vinicius", "jude_bellingham": "Bellingham",
            "mohamed_salah": "Salah", "ronaldinho": "Ronaldinho", "zlatan_ibrahimovi": "Zlatan", "harry_kane": "Kane",
            "kevin_de_bruyne": "De Bruyne", "pedri": "Pedri", "sergio_ramos": "Ramos"}.get(clave, clave.split("_")[0].title())


T_INTRO = 1.35                                                              # presentación: carta 99 tapada + 4 caras gigantes
T_VUELO = 0.95                                                              # desde acá las caras vuelan a la cabecera
LENTO, T_LENTO = 0.42, 0.6                                                  # cámara lenta los últimos 0,6 s del ganador


def reloj(r):
    """Mapea tiempo de video ↔ tiempo de física (intro + cámara lenta antes de que caiga el ganador)."""
    tl = r["quieto"][r["ganador"]]; s0 = tl - T_LENTO; largo = T_LENTO / LENTO

    def v2p(tv):
        tp = tv - T_INTRO
        if tp <= s0:
            return tp
        if tp <= s0 + largo:
            return s0 + (tp - s0) * LENTO
        return tl + (tp - s0 - largo)

    def p2v(tp):
        if tp <= s0:
            return tp + T_INTRO
        if tp <= tl:
            return T_INTRO + s0 + (tp - s0) / LENTO
        return T_INTRO + s0 + largo + (tp - tl)
    return v2p, p2v


@lru_cache(maxsize=1)
def fondo_limpio():
    y = np.linspace(0, 1, H)[:, None]
    a, b = np.array([120, 70, 255]), np.array([40, 200, 255])
    arr = (a * (1 - y) + b * y)[:, None, :].repeat(W, 1).reshape(H, W, 3)
    return Image.fromarray(arr.astype(np.uint8)).convert("RGBA")


@lru_cache(maxsize=1)
def capa_clavos():
    """Clavos con resplandor (blancos y dorados)."""
    im = Image.new("RGBA", (W, H)); d = ImageDraw.Draw(im)
    for (px, py, fila) in PEGS:
        col = (255, 210, 40) if (px, py) in ORO else (220, 245, 255)
        rr = R_PEG + (5 if (px, py) in ORO else 0)
        d.ellipse((px - rr - 9, py - rr - 9, px + rr + 9, py + rr + 9), fill=col + (150,))
    glow = im.filter(ImageFilter.GaussianBlur(10))
    d = ImageDraw.Draw(glow)
    for (px, py, fila) in PEGS:
        oro = (px, py) in ORO
        rr = R_PEG + (5 if oro else 0)
        d.ellipse((px - rr, py - rr, px + rr, py + rr), fill=(255, 215, 50, 255) if oro else (255, 255, 255, 255))
        if oro:
            d.text((px, py), "+5", font=fuente(15), fill=(120, 60, 0), anchor="mm")
    return glow


def cara_intro(i, j, ti):
    """Posición y tamaño de cada cara en la presentación (2x2 gigante, entra con rebote y vuela a la cabecera)."""
    cx, cy = 140 + i * 267, 395
    bx, by = W / 4 + (i % 2) * W / 2, 640 + (i // 2) * 720
    t_in = i * 0.16                                                           # todas visibles desde el cuadro 0; rebotan de a una
    e = ti - t_in
    pop = 1 + 0.22 * math.exp(-e * 9) * math.sin(e * 30) if 0 <= e < 0.5 else 1.0
    tam = 470 * pop
    if ti > T_VUELO:
        u = M.suave((ti - T_VUELO) / (T_INTRO - T_VUELO))
        bx, by = bx + (cx - bx) * u, by + (cy - by) * u
        tam = tam + (236 - tam) * u
    return bx, by, int(tam)


def cuadro(g, r, tv, dur, reloj_):
    v2p, p2v = reloj_
    ti, t = tv, v2p(tv)
    js = g["jugadores"]; n = len(js); gan = r["ganador"]; t_gana = r["quieto"][gan]
    im = fondo_base().copy()
    rot = ti * 0.6                                                            # rayos girando
    capa = Image.new("RGBA", (W, H)); dc = ImageDraw.Draw(capa)
    for k in range(14):
        a0 = rot + k * 2 * math.pi / 14
        dc.polygon([(W / 2, 1000), (W / 2 + 2200 * math.cos(a0), 1000 + 2200 * math.sin(a0)),
                    (W / 2 + 2200 * math.cos(a0 + 0.12), 1000 + 2200 * math.sin(a0 + 0.12))], fill=(255, 255, 255, 26))
    im.alpha_composite(capa)
    im.alpha_composite(capa_clavos())
    if ti < T_INTRO:                                                          # presentación sobre fondo limpio; el tablero aparece al volar
        limpio = fondo_limpio().copy(); limpio.alpha_composite(capa)
        a_ = 1.0 if ti < T_VUELO else 1 - (ti - T_VUELO) / (T_INTRO - T_VUELO)
        im = Image.blend(im, limpio, a_)
    d = ImageDraw.Draw(im)
    ovr = []
    for i in range(n):
        v = ovr_en(r, i, t)
        if r["quieto"][i] is not None and t >= r["quieto"][i]:
            val = VALORES[r["casillero"][i]]
            v = 0 if val == "💀" else int(val)
        ovr.append(v)
    texto(d, (W / 2, 105), g.get("titulo", "WHO GETS 99?"), 100, (255, 235, 40), 12)
    texto(d, (W / 2 - 30, 200), "COMMENT YOUR PICK", 48, (255, 255, 255), 8)
    RR.pegar_emoji(im, "👇", int(W / 2 - 30 + fuente(48).getlength("COMMENT YOUR PICK") / 2 + 45), 200, 56)
    # ---- presentación
    if ti < T_INTRO:
        for i, j in enumerate(js):
            p = cara_intro(i, j, ti)
            if p is None:
                continue
            x, y, tam = p
            im.alpha_composite(con_aro(cara(j, tam), COLORES[i], max(9, tam // 30)), (int(x - tam / 2 - max(9, tam // 30)), int(y - tam / 2 - max(9, tam // 30))))
            d = ImageDraw.Draw(im)
            if ti < T_VUELO:
                texto(d, (x, y + tam / 2 + 40), nombre_corto(j).upper(), 64, COLORES[i], 9)
        if ti < T_VUELO + 0.15:                                               # carta 99 tapada encima, en el centro
            mi = __import__("cartas").misterio(99, (ti * 1.4) % 1.2)
            esc = 0.5 * (1 + 0.05 * math.sin(ti * 14)) * (1 - max(0, ti - T_VUELO) / 0.15)
            if esc > 0.02:
                mi = mi.rotate(6 * math.sin(ti * 9), expand=True, resample=Image.BICUBIC)
                mi = mi.resize((max(1, int(mi.width * esc)), max(1, int(mi.height * esc))), Image.LANCZOS)
                im.alpha_composite(mi, (int(W / 2 - mi.width / 2), int(1000 - mi.height / 2)))
            d = ImageDraw.Draw(im)
    else:
        lider = max(range(n), key=lambda i: ovr[i]) if len(set(ovr)) > 1 else None
        for i, j in enumerate(js):
            cx = 140 + i * 267; cy = 395
            ult = [gl[0] for gl in r["golpes"] if gl[1] == i and gl[0] <= t]
            pulso = 1.12 if ult and t - ult[-1] < 0.12 else 1.0
            tam = int(236 * pulso)
            im.alpha_composite(con_aro(cara(j, tam), COLORES[i], 9), (int(cx - tam / 2 - 9), int(cy - tam / 2 - 9)))
            d = ImageDraw.Draw(im)
            val = ovr[i]
            muerto = r["quieto"][i] is not None and t >= r["quieto"][i] and VALORES[r["casillero"][i]] == "💀"
            if muerto:
                RR.pegar_emoji(im, "💀", cx, cy + 150, 70)
            else:
                texto(d, (cx, cy + 150), str(val), 66, (255, 230, 40) if val >= 85 else (255, 255, 255), 8)
            texto(d, (cx, cy - 143), nombre_corto(j).upper(), 34, COLORES[i], 6)
            if i == lider and t < t_gana:
                RR.pegar_emoji(im, "👑", cx + 95, cy - 100, 74)
            d = ImageDraw.Draw(im)
    # ---- clavos encendidos + chispas + popups "+1"/"+5"
    for gl in r["golpes"]:
        e = t - gl[0]
        if 0 <= e < 0.25:
            px, py, b = gl[2], gl[3], gl[1]
            rr = R_PEG + 14 * (1 - e / 0.25)
            d.ellipse((px - rr, py - rr, px + rr, py + rr), fill=COLORES[b] + (255,))
            chispas(d, px, py, e, COLORES[b])
        if 0 <= e < 0.5:
            oro = puntos(gl) == 5
            tam = (78 if oro else 40) * min(1, e / 0.06 + 0.3)
            texto(d, (gl[2] + 40, gl[3] - 40 - e * 120), "+5" if oro else "+1", int(tam), (255, 215, 40) if oro else (255, 255, 255), 7)
    # casilleros
    for j, v in enumerate(VALORES if ti >= T_VUELO else []):
        xc = (X_DIV[j] + X_DIV[j + 1]) / 2
        brillo = j == GANA and int(ti * 6) % 2 == 0
        if v == "💀":
            RR.pegar_emoji(im, "💀", int(xc), Y_SLOT0 + 95, 70)
        else:
            texto(d, (xc, Y_SLOT0 + 95), v, 60 if j != GANA else 74, (255, 255, 255) if j != GANA else ((255, 255, 255) if brillo else (130, 70, 0)), 7)
    d = ImageDraw.Draw(im)
    # pelotas con estela
    for i in range(n):
        if t < r["salida"][i]:
            continue
        for k in range(1, 6):
            x, y = posicion(r, i, max(r["salida"][i], t - k * 0.025))
            rr = R_BOLA * (1 - k * 0.13)
            d.ellipse((x - rr, y - rr, x + rr, y + rr), fill=COLORES[i] + (int(120 - k * 20),))
        x, y = posicion(r, i, t)
        bola = con_aro(cara(js[i], 2 * R_BOLA - 10), COLORES[i], 5)
        im.alpha_composite(bola, (int(x - bola.width / 2), int(y - bola.height / 2)))
    d = ImageDraw.Draw(im)
    # carteles al caer (de a uno)
    caidos = [i for i in range(n) if i != gan and r["quieto"][i] is not None and r["quieto"][i] <= t]
    for i in sorted(caidos, key=lambda k: r["quieto"][k])[-1:]:
        e = t - r["quieto"][i]
        if e > (0.6 if len(caidos) == n - 1 else 1.1) or t >= t_gana:
            continue
        c = r["casillero"][i]; esc = min(1.0, e / 0.12)
        if c in (GANA - 1, GANA + 1):
            texto(d, (W / 2, Y_CARTEL), "SO CLOSE!", int(120 * esc) + 1, (255, 70, 70), 13)
            RR.pegar_emoji(im, "😭", int(W / 2 + 340), Y_CARTEL, int(100 * esc) + 1)
        elif VALORES[c] == "💀":
            texto(d, (W / 2, Y_CARTEL), "BENCHED", int(110 * esc) + 1, (210, 210, 220), 13)
            RR.pegar_emoji(im, "💀", int(W / 2 + 330), Y_CARTEL, int(100 * esc) + 1)
        else:
            texto(d, (W / 2, Y_CARTEL), f"{nombre_corto(js[i]).upper()} {VALORES[c]}", int(90 * esc) + 1, (255, 255, 255), 11)
        d = ImageDraw.Draw(im)
    # 6 7
    for i in range(n):
        g67 = momento67(r, i)
        if g67 is not None and 0 <= t - g67 < 0.55:
            e = t - g67
            im.alpha_composite(Image.new("RGBA", (W, H), (255, 60, 200, int(120 * max(0, 1 - e / 0.3)))))
            d = ImageDraw.Draw(im)
            texto(d, (W / 2, 1000), "6 7", int(180 + 120 * min(1, e / 0.08)), (255, 255, 255), 16, (255, 40, 170))
            texto(d, (W / 2, 1180), nombre_corto(js[i]).upper() + " HIT 67", 64, COLORES[i], 9)
    otros = [r["quieto"][i] for i in range(n) if i != gan]
    if max(otros) + 0.6 < t < t_gana:
        texto(d, (W / 2, Y_CARTEL), "LAST ONE...", 100, (255, 235, 40), 13)
    # ---- ganador: carta FUT real que gira y brilla
    if t >= t_gana:
        e = t - t_gana
        if e < 0.2:
            im.alpha_composite(Image.new("RGBA", (W, H), (255, 235, 140, int(240 * (1 - e / 0.2)))))
        im.alpha_composite(Image.new("RGBA", (W, H), (10, 5, 30, int(min(175, e * 700)))))
        rayos = Image.new("RGBA", (W, H)); dr = ImageDraw.Draw(rayos)
        for k in range(16):
            a0 = e * 1.3 + k * 2 * math.pi / 16
            dr.polygon([(W / 2, 1000), (W / 2 + 2200 * math.cos(a0), 1000 + 2200 * math.sin(a0)),
                        (W / 2 + 2200 * math.cos(a0 + 0.13), 1000 + 2200 * math.sin(a0 + 0.13))], fill=(255, 210, 60, 70))
        im.alpha_composite(rayos)
        cr = carta(js[gan], ovr=99, brillo=min(1.2, e / 0.9))
        giro = abs(math.cos(min(1.0, e / 0.45) * math.pi * 2)) if e < 0.45 else 1.0     # da 2 vueltas al aparecer
        esc = min(1.0, 0.3 + e / 0.3) * 1.18 * (1 + 0.03 * math.sin(e * 12))
        cw, ch = max(2, int(cr.width * esc * max(0.04, giro))), int(cr.height * esc)
        cr = cr.resize((cw, ch), Image.LANCZOS)
        im.alpha_composite(cr, (int(W / 2 - cw / 2), int(1050 - ch / 2)))
        d = ImageDraw.Draw(im)
        texto(d, (W / 2, 1640), "GOAT", 160, (255, 230, 40), 15)
        RR.pegar_emoji(im, "🐐", int(W / 2 - 310), 1640, 130)
        RR.pegar_emoji(im, "🐐", int(W / 2 + 310), 1640, 130)
        for k in range(14):
            em = "🔥🏆⚽🐐💰⭐"[k % 6]
            x = (k * 173 + 60) % W; y = (e * 900 + k * 260) % (H + 200) - 100
            RR.pegar_emoji(im, em, int(x), int(y), 80)
    out = im.convert("RGB")
    # cámara: zoom sobre la última pelota en cámara lenta
    if t_gana - T_LENTO < t < t_gana:
        u = M.suave((t - (t_gana - T_LENTO)) / T_LENTO * 2)
        z = 1 + 0.38 * u
        x, y = posicion(r, gan, t)
        cw, ch = W / z, H / z
        x0 = min(max(x - cw / 2, 0), W - cw); y0 = min(max(y - ch * 0.55, 0), H - ch)
        out = out.crop((int(x0), int(y0), int(x0 + cw), int(y0 + ch))).resize((W, H), Image.BICUBIC)
    if t_gana <= t < t_gana + 0.35:
        k = (1 - (t - t_gana) / 0.35) * 28
        out = out.transform(out.size, Image.AFFINE, (1, 0, k * math.sin(t * 90), 0, 1, k * math.cos(t * 77)), fillcolor=(255, 230, 120))
    return out


# ------------------------------------------------------------------ audio
def cargar(nombre, vol=1.0):
    try:
        return RR.sfx(nombre, vol=vol)
    except Exception:
        return None


def musica(g, dur):
    import render_stop as RS
    nom = g.get("musica", "trallallero_2")
    m = cargar(nom if nom[-1].isdigit() else nom + "_0", 0.55)
    if m is None:
        return RS.musica_67(dur)[: int(dur * M.SR)] * 0.8
    n = int(dur * M.SR)
    return np.tile(m, n // len(m) + 1)[:n]


def audio(g, r, dur, reloj_):
    sr = M.SR; n = int(dur * sr); fx = np.zeros(n, np.float32)
    v2p, p2v = reloj_

    def add(t0, sig, v=1.0, video=False):
        if sig is None:
            return
        a = int((t0 if video else p2v(t0)) * sr)
        if a >= n:
            return
        b = min(n, a + len(sig)); fx[a:b] += sig[: b - a] * v
    for (t, i, px, py, fila) in r["golpes"]:                                # tic más agudo cuanto más abajo
        f = 700 * 2 ** (fila / 8)
        tt = np.arange(int(0.07 * sr)) / sr
        add(t, np.sin(2 * np.pi * f * tt) * np.exp(-tt * 45) * 0.32)
        if (px, py) in ORO:
            add(t, cargar("moneda_0", 0.6))
    add(0, M.boom(0.6), 0.7, True); add(0, M.whoosh(0.6), 0.6, True)
    pop = cargar("pop_0", 0.8)
    for i in range(len(g["jugadores"])):                                      # cada cara entra con un "pop"
        add(i * 0.16, pop if pop is not None else M.golpe(0.1), 0.9, True)
    add(T_VUELO, M.whoosh(0.5), 0.7, True)
    voz67 = [cargar("seis_siete_0", 0.9), cargar("67_0", 0.9), cargar("doot_doot_0", 0.9)]
    for i in range(len(g["jugadores"])):
        m67 = momento67(r, i)
        if m67 is not None:
            add(m67, voz67[i % 3])
    gan = r["ganador"]; js = g["jugadores"]
    nope, bruh = cargar("nope_0", 0.6), cargar("bruh_0", 0.7)
    for i in range(len(js)):
        q = r["quieto"][i]; c = r["casillero"][i]
        if i == gan:
            continue
        add(q, M.golpe(0.12), 0.7)
        if c in (GANA - 1, GANA + 1):
            add(q + 0.05, nope)
        elif VALORES[c] == "💀":
            add(q + 0.05, bruh)
        else:
            add(q, M.ding(0.4), 0.3)
    otros = max(r["quieto"][i] for i in range(len(js)) if i != gan)
    tg = r["quieto"][gan]
    if tg - otros > 0.4:                                                     # redoble de suspenso
        k = otros
        while k < tg:
            add(k, M.golpe(0.08), 0.35); k += max(0.06, 0.18 - (k - otros) * 0.08)
    add(tg - T_LENTO, M.whoosh(1.2), 0.5)
    add(tg, M.boom(1.0), 0.8); add(tg, M.ding(0.9), 0.6); add(tg + 0.1, cargar("pack_opening_0", 0.6))
    add(tg, cargar("airhorn_0", 0.5)); add(tg + 0.05, M.tribuna(1.8), 0.5)
    for s in SONIDO_JUGADOR.get(js[gan], ["goat_0"])[:1]:
        add(tg + 0.15, cargar(s, 0.95))
    add(dur - 0.35, M.whoosh(0.4), 0.5, True)
    mu = musica(g, dur)
    return np.tanh((mu * 0.75 + fx) * 1.1) * 0.9, np.tanh(fx * 1.1) * 0.85


def main(guion):
    g = json.loads(Path(guion).read_text())
    out = ROOT / "salida" / g["id"]; out.mkdir(parents=True, exist_ok=True)
    r = buscar(g.get("semilla", 1), len(g["jugadores"]))
    rl = reloj(r)
    dur = rl[1](r["quieto"][r["ganador"]]) + 2.4
    print("semilla", r["semilla"], "casilleros", r["casillero"], "caídas", [round(q, 2) for q in r["quieto"]], "dur", round(dur, 2))
    mudo = out / "mudo.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", str(mudo)], stdin=subprocess.PIPE)
    inicio = cuadro(g, r, 0.0, dur, rl)
    for f in range(int(round(dur * FPS))):
        t = f / FPS; im = cuadro(g, r, t, dur, rl)
        if t > dur - 0.3:                                                      # loop: funde con el cuadro 0
            im = Image.blend(im, inicio, (t - (dur - 0.3)) / 0.3)
        p.stdin.write(np.asarray(im, np.uint8).tobytes())
    p.stdin.close(); p.wait()
    con, solo = audio(g, r, dur, rl)
    M.mezclar(out, mudo, {"short.mp4": con, "short_solo_efectos.mp4": solo})
    (out / "resultado.json").write_text(json.dumps(dict(semilla=r["semilla"], ganador=g["jugadores"][r["ganador"]],
                                                         casilleros=r["casillero"], dur=dur), ensure_ascii=False))
    print(out / "short.mp4", round(dur, 2), "s")


if __name__ == "__main__":
    main(sys.argv[1])
