#!/usr/bin/env python3
"""
PELOTAS AL HOYO 3D (réplica mejorada de "ball drop race", 14,6 M).
Escena 3D (three.js, runner/escena_hoyo.html): cancha de estadio, hoyo con aro dorado y bandera GOAT, 4 pelotas reales
con la cara de cada jugador flotando arriba. Arriba (Python): presentación con las 4 caras gigantes + carta 99 tapada,
después la cabecera con las caras. Una pelota hace "lip out" (da la vuelta al borde y sale → SO CLOSE!), dos pasan de
largo, y la del ganador llega en cámara lenta, gira en el borde y entra → flash, CARTA FUT real, hinchada, su sonido.
Loop: los últimos 0,35 s funden con el cuadro 0.

Uso: python3 produccion/render_hoyo.py produccion/guiones/hoyo_01.json
guion: {"id": "hoyo_01", "jugadores": [...4 claves...], "ganador": 2, "semilla": 3, "musica": "bombardiro_0"}
"""
import json
import math
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

import cartas
import motor as M
import render_plinko as P

ROOT = P.ROOT
W, H, FPS = P.W, P.H, 30
HOYO = (0.0, -30.0)
R_HOYO, R_BOLA = 1.25, 0.7
T_INTRO, T_VUELO = 1.2, 0.85
T_GANA = 3.4                                   # (tiempo de física) el ganador cae al hoyo
LENTO, T_LENTO = 0.4, 0.75
FIESTA, FADE = 2.4, 0.35


def bezier(p0, c, p1, u):
    return ((1 - u) ** 2 * p0[0] + 2 * (1 - u) * u * c[0] + u * u * p1[0], (1 - u) ** 2 * p0[1] + 2 * (1 - u) * u * c[1] + u * u * p1[1])


def plan(g):
    rng = np.random.default_rng(g.get("semilla", 1))
    n = len(g["jugadores"]); gan = g["ganador"] % n
    otros = [i for i in range(n) if i != gan]
    casi = otros[int(rng.integers(len(otros)))]
    hx, hz = HOYO
    bs = []
    for i in range(n):
        x0 = -3.3 + i * 2.2
        if i == gan:
            lado = 1 if x0 < 0 else -1
            borde = (hx - lado * R_HOYO * 0.95, hz + 0.25)
            bs.append(dict(tipo="gana", x0=x0, fin=borde, t1=T_GANA - 0.55, c=(x0 * 0.3 + rng.uniform(-3, 3), -16), lado=lado))
        elif i == casi:
            lado = -1 if x0 < 0 else 1
            borde = (hx + lado * R_HOYO * 0.9, hz + R_HOYO * 0.45)
            bs.append(dict(tipo="casi", x0=x0, fin=borde, t1=1.9, c=(x0 * 0.4 + rng.uniform(-2, 2), -14), lado=lado))
        else:
            lado = -1 if x0 < 0 else 1
            fin = (hx + lado * rng.uniform(3.2, 5.0), hz - rng.uniform(1, 5))
            bs.append(dict(tipo="pasa", x0=x0, fin=fin, t1=rng.uniform(2.1, 2.6), c=(x0 + rng.uniform(-2.5, 2.5), -15), lado=lado))
    return bs, gan


def pos(b, tp):
    """(x, y, z, visible) de la pelota en tiempo de física tp (0 = patada)."""
    hx, hz = HOYO
    if tp <= 0:
        return b["x0"], R_BOLA, 0.0, 1.0
    if tp <= b["t1"]:
        tau = tp / b["t1"]; u = 1 - (1 - tau) ** 1.7                             # frena de a poco
        x, z = bezier((b["x0"], 0.0), b["c"], b["fin"], u)
        return x, R_BOLA, z, 1.0
    e = tp - b["t1"]
    a0 = math.atan2(b["fin"][1] - hz, b["fin"][0] - hx)
    if b["tipo"] == "casi":                                                       # lip out: media vuelta por el borde y sale
        giro = min(e / 0.55, 1.0) * math.pi * 1.15
        if e <= 0.55:
            a = a0 - b["lado"] * giro
            return hx + math.cos(a) * R_HOYO, R_BOLA * 0.82, hz + math.sin(a) * R_HOYO, 1.0
        a = a0 - b["lado"] * math.pi * 1.15
        k = 1 - math.exp(-(e - 0.55) * 2.5)
        tx, tz = -math.sin(a) * b["lado"], math.cos(a) * b["lado"]
        return hx + math.cos(a) * R_HOYO + tx * 3.2 * k, R_BOLA, hz + math.sin(a) * R_HOYO + tz * 3.2 * k, 1.0
    if b["tipo"] == "pasa":
        k = 1 - math.exp(-e * 2.2)
        return b["fin"][0] + b["lado"] * 1.2 * k, R_BOLA, b["fin"][1] - 2.0 * k, 1.0
    # gana: gira 3/4 de vuelta por el borde cerrándose y cae
    if e <= 0.55:
        u = e / 0.55; a = a0 + b["lado"] * u * math.pi * 1.5; rr = R_HOYO * (0.95 - 0.55 * u)
        return hx + math.cos(a) * rr, R_BOLA * (1 - 0.3 * u), hz + math.sin(a) * rr, 1.0
    k = min(1.0, (e - 0.55) / 0.3)
    return hx, R_BOLA * 0.7 - 2.6 * k * k, hz, 1.0 if k < 1 else 0.0


def reloj():
    s0 = T_GANA - T_LENTO; largo = T_LENTO / LENTO

    def v2p(tv):
        tp = tv - T_INTRO
        if tp <= s0:
            return tp
        if tp <= s0 + largo:
            return s0 + (tp - s0) * LENTO
        return T_GANA + (tp - s0 - largo)

    def p2v(tp):
        if tp <= s0:
            return tp + T_INTRO
        if tp <= T_GANA:
            return T_INTRO + s0 + (tp - s0) / LENTO
        return T_INTRO + s0 + largo + (tp - T_GANA)
    return v2p, p2v


def camara(bs, gan, tp):
    """Cámara: alta atrás en la presentación → sigue a las pelotas → baja al hoyo en la cámara lenta → sube al festejo."""
    hx, hz = HOYO
    zs = [pos(b, max(0, tp))[2] for b in bs]
    zm = min(0.0, sum(zs) / len(zs))
    seguir = (0.0, 8.5, zm + 15.0, 0.0, 0.0, zm - 10.0)
    cerca = (hx + 2.6, 2.2, hz + 6.0, hx, 0.0, hz - 0.5)
    if tp <= T_GANA - T_LENTO - 0.5:
        return seguir
    if tp <= T_GANA:
        u = M.suave((tp - (T_GANA - T_LENTO - 0.5)) / (T_LENTO + 0.5))
        return tuple(a + (b - a) * u for a, b in zip(seguir, cerca))
    e = tp - T_GANA
    ang = e * 0.5
    return (hx + 6.0 * math.sin(ang), 2.2 + e * 1.5, hz + 6.0 * math.cos(ang), hx, 0.0, hz)


# ------------------------------------------------------------------ capa 2D (encima del 3D)
def capa(g, bs, gan, tv, tp):
    js = g["jugadores"]; n = len(js)
    im = Image.new("RGBA", (W, H)); d = ImageDraw.Draw(im)
    titulo = g.get("titulo", "WHO WINS?")
    if tv < T_INTRO:                                                              # presentación sobre fondo limpio
        a = 255 if tv < T_VUELO else int(255 * (1 - (tv - T_VUELO) / (T_INTRO - T_VUELO)))
        im.alpha_composite(P.fondo_limpio().copy().resize((W, H)) if a == 255 else Image.blend(Image.new("RGBA", (W, H)), P.fondo_limpio(), a / 255))
        d = ImageDraw.Draw(im)
    P.texto(d, (W / 2, 105), titulo, 104, (255, 235, 40), 13)
    P.RR.pegar_emoji(im, "👇", int(W / 2 + P.fuente(104).getlength(titulo) / 2 + 60), 105, 90)
    for i, j in enumerate(js):
        if tv < T_INTRO:
            x, y, tam = P.cara_intro(i, j, tv)
        else:
            x, y, tam = 140 + i * 267, 330, 236
            b = bs[i]
            if b["tipo"] == "casi" and 0 <= tp - b["t1"] < 0.9:
                y += 12 * math.sin((tp - b["t1"]) * 50)
        grosor = max(9, tam // 30)
        im.alpha_composite(P.con_aro(P.cara(j, tam), P.COLORES[i], grosor), (int(x - tam / 2 - grosor), int(y - tam / 2 - grosor)))
        d = ImageDraw.Draw(im)
        if tv < T_VUELO:
            P.texto(d, (x, y + tam / 2 + 40), P.nombre_corto(j).upper(), 64, P.COLORES[i], 9)
        elif tv >= T_INTRO:
            P.texto(d, (x, y + 155), P.nombre_corto(j).upper(), 40, P.COLORES[i], 7)
    if tv < T_VUELO + 0.15:
        mi = cartas.misterio(99, (tv * 1.4) % 1.2)
        esc = 0.5 * (1 + 0.05 * math.sin(tv * 14)) * (1 - max(0, tv - T_VUELO) / 0.15)
        if esc > 0.02:
            mi = mi.rotate(6 * math.sin(tv * 9), expand=True, resample=Image.BICUBIC)
            mi = mi.resize((max(1, int(mi.width * esc)), max(1, int(mi.height * esc))), Image.LANCZOS)
            im.alpha_composite(mi, (int(W / 2 - mi.width / 2), int(1000 - mi.height / 2)))
    d = ImageDraw.Draw(im)
    if T_INTRO <= tv and tp < 0.35:
        P.texto(d, (W / 2, 1000), "GO!", int(200 + 200 * max(0, 0.35 - tp)), (255, 255, 255), 16, (255, 60, 60))
    for b in bs:
        e = tp - b["t1"]
        if b["tipo"] == "casi" and 0.2 <= e and tp < T_GANA - T_LENTO:
            P.texto(d, (W / 2, 1720), "SO CLOSE!", int(130 * min(1, (e - 0.2) / 0.1)) + 1, (255, 70, 70), 14)
            P.RR.pegar_emoji(im, "😭", int(W / 2 + 350), 1720, 110)
    if T_GANA - T_LENTO <= tp < T_GANA:
        P.texto(d, (W / 2, 1720), "WAIT...", 130, (255, 255, 255), 14)
    if tp >= T_GANA:
        e = tp - T_GANA
        if e < 0.2:
            im.alpha_composite(Image.new("RGBA", (W, H), (255, 240, 170, int(250 * (1 - e / 0.2)))))
        im.alpha_composite(Image.new("RGBA", (W, H), (10, 5, 30, int(min(160, e * 650)))))
        rayos = Image.new("RGBA", (W, H)); dr = ImageDraw.Draw(rayos)
        for k in range(16):
            a0 = e * 1.3 + k * 2 * math.pi / 16
            dr.polygon([(W / 2, 1000), (W / 2 + 2200 * math.cos(a0), 1000 + 2200 * math.sin(a0)),
                        (W / 2 + 2200 * math.cos(a0 + 0.13), 1000 + 2200 * math.sin(a0 + 0.13))], fill=(255, 210, 60, 60))
        im.alpha_composite(rayos)
        cr = cartas.carta(js[gan], 99, min(1.2, e / 0.9))
        giro = abs(math.cos(min(1.0, e / 0.45) * math.pi * 2)) if e < 0.45 else 1.0
        esc = min(1.0, 0.3 + e / 0.3) * 1.18 * (1 + 0.03 * math.sin(e * 12))
        cw, ch = max(2, int(cr.width * esc * max(0.04, giro))), int(cr.height * esc)
        im.alpha_composite(cr.resize((cw, ch), Image.LANCZOS), (int(W / 2 - cw / 2), int(1040 - ch / 2)))
        d = ImageDraw.Draw(im)
        P.texto(d, (W / 2, 1640), "WINNER!", 150, (255, 230, 40), 15)
        for k in range(14):
            em = "🔥🏆⚽🐐💰⭐"[k % 6]
            x = (k * 173 + 60) % W; y = (e * 900 + k * 260) % (H + 200) - 100
            P.RR.pegar_emoji(im, em, int(x), int(y), 80)
    return im


def audio(g, bs, gan, dur, p2v):
    sr = M.SR; n = int(dur * sr); fx = np.zeros(n, np.float32)

    def add(t0, sig, v=1.0, video=False):
        if sig is None:
            return
        a = int((t0 if video else p2v(t0)) * sr)
        if a < 0 or a >= n:
            return
        b = min(n, a + len(sig)); fx[a:b] += sig[: b - a] * v
    pop = P.cargar("pop_0", 0.8)
    add(0, M.boom(0.6), 0.7, True); add(0, M.whoosh(0.6), 0.6, True)
    for i in range(len(bs)):
        add(i * 0.16, pop if pop is not None else M.golpe(0.1), 0.9, True)
    add(T_VUELO, M.whoosh(0.5), 0.7, True)
    for i in range(len(bs)):
        add(0.0 + i * 0.03, M.golpe(0.12), 0.8)
    add(0.0, P.cargar("airhorn_0", 0.35))
    rod = np.convolve(np.random.default_rng(3).standard_normal(int(3.0 * sr)).astype(np.float32), np.ones(60) / 60, "same")
    add(0.0, rod * np.linspace(0.9, 0.2, len(rod)), 0.6)
    for b in bs:
        if b["tipo"] == "casi":
            for k in range(6):
                add(b["t1"] + k * 0.09, M.golpe(0.05), 0.35)
            add(b["t1"] + 0.6, P.cargar("nope_0", 0.75)); add(b["t1"] + 0.6, P.cargar("emotional_damage_0", 0.5))
        elif b["tipo"] == "pasa":
            add(b["t1"], M.whoosh(0.3), 0.3)
    add(T_GANA - T_LENTO, M.whoosh(1.4), 0.5)
    k = T_GANA - 0.55
    while k < T_GANA:                                                             # vueltas en el borde
        add(k, M.golpe(0.05), 0.45); k += 0.07
    add(T_GANA, pop, 1.0); add(T_GANA, M.boom(1.0), 0.8); add(T_GANA, M.ding(0.9), 0.6)
    add(T_GANA + 0.05, P.cargar("crowd_cheer_0", 0.55)); add(T_GANA + 0.1, P.cargar("pack_opening_0", 0.5))
    for s in P.SONIDO_JUGADOR.get(g["jugadores"][gan], ["goat_0"])[:1]:
        add(T_GANA + 0.3, P.cargar(s, 0.95))
    add(dur - FADE, M.whoosh(0.4), 0.5, True)
    mu = P.musica(g, dur)
    return np.tanh((mu * 0.72 + fx) * 1.1) * 0.9, np.tanh(fx * 1.1) * 0.85


def main(guion):
    g = json.loads(Path(guion).read_text())
    out = ROOT / "salida" / g["id"]; out.mkdir(parents=True, exist_ok=True)
    bs, gan = plan(g)
    v2p, p2v = reloj()
    dur = p2v(T_GANA) + FIESTA + FADE
    nf = int(round(dur * FPS))
    (out / "caras").mkdir(exist_ok=True)
    jug = []
    for i, j in enumerate(g["jugadores"]):
        P.cara(j, 512).save(out / "caras" / f"{j}.png")
        jug.append(dict(cara=f"../salida/{g['id']}/caras/{j}.png", color="#%02x%02x%02x" % P.COLORES[i]))
    cuadros = []
    for f in range(nf):
        tp = v2p(f / FPS)
        cuadros.append(dict(cam=[round(v, 3) for v in camara(bs, gan, tp)],
                            bolas=[[round(v, 3) for v in pos(b, tp)] for b in bs]))
    cfg = dict(escena="escena_hoyo.html", fps=FPS, duracion=dur, hoyo=list(HOYO), r_hoyo=R_HOYO, r_bola=R_BOLA, jugadores=jug, cuadros=cuadros)
    (out / "cfg3d.json").write_text(json.dumps(cfg))
    muestra = sys.argv[2:] if len(sys.argv) > 2 else None
    tres = out / "tres.mp4"
    cmd = ["node", str(ROOT / "runner" / "render_runner.js"), str(out / "cfg3d.json"), str(tres)] + (["--muestra", muestra[0]] if muestra else [])
    subprocess.run(cmd, check=True, cwd=ROOT / "runner")
    if muestra:
        return
    lee = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-i", str(tres), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    mudo = out / "mudo.mp4"
    esc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                            "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", str(mudo)], stdin=subprocess.PIPE)
    inicio = None
    for f in range(nf):
        crudo = lee.stdout.read(W * H * 3)
        if len(crudo) < W * H * 3:
            break
        tv = f / FPS; tp = v2p(tv)
        base = Image.frombytes("RGB", (W, H), crudo).convert("RGBA")
        base.alpha_composite(capa(g, bs, gan, tv, tp))
        im = base.convert("RGB")
        if tp >= T_GANA and tp - T_GANA < 0.35:
            k = (1 - (tp - T_GANA) / 0.35) * 26
            im = im.transform(im.size, Image.AFFINE, (1, 0, k * math.sin(tv * 90), 0, 1, k * math.cos(tv * 77)), fillcolor=(255, 240, 170))
        if inicio is None:
            inicio = im
        if tv > dur - FADE:
            im = Image.blend(im, inicio, (tv - (dur - FADE)) / FADE)
        esc.stdin.write(np.asarray(im, np.uint8).tobytes())
    esc.stdin.close(); esc.wait(); lee.wait()
    tres.unlink()
    con, solo = audio(g, bs, gan, dur, p2v)
    M.mezclar(out, mudo, {"short.mp4": con, "short_solo_efectos.mp4": solo})
    (out / "resultado.json").write_text(json.dumps(dict(ganador=g["jugadores"][gan], dur=dur), ensure_ascii=False))
    print(out / "short.mp4", round(dur, 2), "s")


if __name__ == "__main__":
    main(sys.argv[1])
