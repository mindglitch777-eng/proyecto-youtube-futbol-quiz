#!/usr/bin/env python3
"""
RING ESCAPE: réplica futbolera del formato de bouncyball ("Will the ball escape 5 million rings?", 86,2 M).
Dos (o más) pelotas con cara/escudo rebotan dentro de anillos concéntricos que giran, cada uno con un hueco.
El que atraviesa un anillo lo ROMPE y suma un punto. Gana el que rompe más anillos (cantidad impar, sin empates).

Qué tomamos de la receta (reporte 17): cada rebote es una nota de una melodía (acá "Glory Glory", himno de
cancha de dominio público), estela luminosa, anillos de colores, cierre al romperse el último anillo.
Qué sumamos: marcador en vivo (remontadas), escudos/caras reales, ganador = el pick popular (física real,
se elige la semilla), cámara fija.

Uso: python3 render_ring_escape.py guiones/ring_01.json -> salida/<id>/short.mp4 y short_sin_musica.mp4
"""
import json
import math
import random
import sys
from pathlib import Path

import numpy as np
import pymunk
from PIL import ImageDraw

import motor as M
from motor import W, H, FPS
from render_carrera import competidores

CX, CY = W / 2, 1090
DT = 1 / 240
SUB = 4
BALL = 24
R0, PASO = 110, 62
HUECO = 160                       # largo del hueco en px (igual en todos los anillos)

# Glory Glory (Battle Hymn of the Republic, dominio público): una nota por rebote
_N = {"C4": 261.6, "D4": 293.7, "E4": 329.6, "F4": 349.2, "G4": 392.0, "A4": 440.0, "B4": 493.9, "C5": 523.3, "D5": 587.3,
      "E5": 659.3, "G3": 196.0, "A3": 220.0, "B3": 246.9}
MELODIA = [_N[n] for n in ("G4 G4 G4 G4 F4 E4 F4 G4 C5 D5 E5 E5 D5 C5 B4 A4 G4 G4 G4 G4 G4 F4 E4 F4 G4 C5 C5 B4 A4 B4 C5 "
                           "G4 G4 G4 G4 F4 E4 F4 G4 C5 D5 E5 E5 D5 C5 B4 A4 G4 A4 B4 C5 C5 B4 A4 B4 C5").split()]

PALETA = [(255, 64, 96), (255, 140, 40), (255, 214, 60), (90, 230, 110), (40, 210, 220), (70, 140, 255),
          (150, 100, 255), (230, 80, 230), (255, 90, 150), (255, 170, 60), (120, 240, 160), (80, 200, 255), (200, 120, 255)]


def configurar(n_bolas):
    """1 contra 1: pelotas grandes (caras/escudos bien visibles) y 5 anillos; 3-4 jugadores: 7 anillos."""
    global BALL, R0, PASO, HUECO
    if n_bolas <= 2:
        BALL, R0, PASO, HUECO = 34, 118, 84, 155
    else:
        BALL, R0, PASO, HUECO = 26, 110, 64, 140
    return 5 if n_bolas <= 2 else 7


def radio(k):
    return R0 + PASO * k


def simular(n_bolas, n_anillos, semilla, tmax=48):
    rnd = random.Random(semilla)
    space = pymunk.Space(); space.gravity = (0, 900)
    anillos = []
    for k in range(n_anillos):
        r = radio(k)
        b = pymunk.Body(body_type=pymunk.Body.KINEMATIC); b.position = (CX, CY)
        b.angle = rnd.uniform(0, 2 * math.pi)
        b.angular_velocity = (0.9 + 0.11 * k + rnd.uniform(-0.15, 0.15)) * (1 if k % 2 == 0 else -1)
        hueco = HUECO / r
        n = max(40, int(r / 7))
        formas = []
        for j in range(n):
            a0 = hueco / 2 + (2 * math.pi - hueco) * j / n
            a1 = hueco / 2 + (2 * math.pi - hueco) * (j + 1) / n
            s = pymunk.Segment(b, (r * math.cos(a0), r * math.sin(a0)), (r * math.cos(a1), r * math.sin(a1)), 4)
            s.elasticity = 1.0; s.friction = 0.0
            formas.append(s)
        space.add(b, *formas)
        anillos.append(dict(body=b, formas=formas, r=r, hueco=hueco, roto=None))
    bolas = []
    for i in range(n_bolas):
        b = pymunk.Body(1, pymunk.moment_for_circle(1, 0, BALL))
        b.position = (CX + (i - (n_bolas - 1) / 2) * 70, CY - 20)
        a = rnd.uniform(0, 2 * math.pi); v = rnd.uniform(500, 800)
        b.velocity = (v * math.cos(a), v * math.sin(a)); b.angular_velocity = rnd.uniform(-6, 6)
        c = pymunk.Circle(b, BALL); c.elasticity = 1.0; c.friction = 0.4
        space.add(b, c); bolas.append(b)
    puntos = [0] * n_bolas
    estados, eventos = [], []
    vprev = [b.velocity for b in bolas]
    t = 0.0; fin = None
    while t < tmax and fin is None:
        for _ in range(SUB):
            space.step(DT); t += DT
            for i, b in enumerate(bolas):
                if (b.velocity - vprev[i]).length > 260:
                    eventos.append(("rebote", t, i))
                sp = b.velocity.length
                if sp < 520:
                    b.velocity = b.velocity.normalized() * 520 if sp > 1 else (0, -520)
                elif sp > 1500:
                    b.velocity = b.velocity.normalized() * 1500
                vprev[i] = b.velocity
                d = (b.position - (CX, CY)).length
                for k, an in enumerate(anillos):
                    if an["roto"] is None and d > an["r"] + BALL + 3:
                        an["roto"] = (i, t)
                        space.remove(*an["formas"])
                        puntos[i] += 1
                        eventos.append(("rompe", t, i, k, tuple(puntos), an["body"].angle))
                        # empujoncito hacia afuera para que no quede pegado
                        b.velocity = b.velocity * 1.04
            if all(an["roto"] for an in anillos):
                fin = t
                break
        estados.append(([(b.position.x, b.position.y, b.angle) for b in bolas], [an["body"].angle for an in anillos]))
    if fin is None:
        return None
    ganador = int(np.argmax(puntos))
    # cambios de líder
    lider, cambios = None, 0
    for e in eventos:
        if e[0] == "rompe":
            p = e[4]; m = max(p)
            l = p.index(m) if p.count(m) == 1 else lider
            if l != lider and lider is not None:
                cambios += 1
            lider = l
    return dict(estados=estados, eventos=eventos, puntos=puntos, ganador=ganador, dur=fin, cambios=cambios,
                rotos=[an["roto"] for an in anillos])


def elegir(n_bolas, n_anillos, quiere, dmin, dmax, base, intentos=300):
    mejor = None
    for s in range(base, base + intentos):
        sim = simular(n_bolas, n_anillos, s)
        if sim is None or sim["ganador"] != quiere or not (dmin <= sim["dur"] <= dmax):
            continue
        orden = sorted(sim["puntos"], reverse=True)
        if orden[0] == orden[1]:
            continue
        # ritmo parejo: que no se rompan todos de golpe al final ni al principio
        ts = sorted(r[1] for r in sim["rotos"])
        huecos = max(b - a for a, b in zip([0] + ts, ts))
        punt = sim["cambios"] * 2 - (orden[0] - orden[1]) * 1.5 - max(0, huecos - 6) * 0.5
        if mejor is None or punt > mejor[0]:
            mejor = (punt, s, sim)
            if sim["cambios"] >= 2 and orden[0] - orden[1] == 1 and huecos < 6:
                break
    if mejor is None:
        raise SystemExit(f"sin semilla: bolas={n_bolas} anillos={n_anillos} quiere={quiere}")
    print("semilla", mejor[1], "puntos", mejor[2]["puntos"], "cambios", mejor[2]["cambios"], f"{mejor[2]['dur']:.1f}s")
    return mejor[2]


def main(guion_path):
    g = json.loads(Path(guion_path).read_text())
    comp = competidores(g, 300)
    n = len(comp); n_an = g.get("anillos", configurar(n))
    nombres = [c.get("corto_hud") or (c["nombre"].split()[-1].upper() if c["tipo"] == "jugador" else c.get("corto", c["nombre"]).upper())
               for c in comp]
    quiere = [c["nombre"] for c in comp].index(g["ganador"])
    sim = elegir(n, n_an, quiere, *g.get("duracion", [16, 30]), g.get("semilla", 0) * 1000)
    out = M.ROOT / "salida" / g["id"]; out.mkdir(parents=True, exist_ok=True)
    tema = dict(f1=(4, 4, 12), f2=(26, 18, 52), acento=(255, 214, 80))
    base = M.superficie_fondo(tema["f1"], tema["f2"], cy=CY / H)
    T_INI, T_FIN = 0.0, 3.4
    t_juego = sim["dur"]
    dur = T_INI + t_juego + 0.9 + T_FIN
    nf = int(dur * FPS)
    bola_sup = [M.pil_a_cairo(c["img"].resize((2 * BALL + 2, 2 * BALL + 2), M.Image.LANCZOS)) for c in comp]
    marc_sup = [M.pil_a_cairo(c["img"].resize((116, 116), M.Image.LANCZOS)) for c in comp]
    gris_sup = [M.pil_a_cairo(M.gris(c["img"].resize((116, 116), M.Image.LANCZOS), 0.55)) for c in comp]
    gran_sup = M.pil_a_cairo(comp[sim["ganador"]]["img"].resize((380, 380), M.Image.LANCZOS))

    # sonido: una nota de la melodía por rebote (máx. 1 cada 70 ms), crujido al romper, festejo al final
    mez = M.Mezcla(dur); part = M.Particulas(9)
    notas = [M.pluck(f * 2, 0.32, 0.3) for f in MELODIA]
    idx, ult = 0, -1
    for e in sim["eventos"]:
        te = T_INI + e[1]
        if e[0] == "rebote" and te - ult > 0.07:
            mez.add(te, notas[idx % len(notas)]); idx += 1; ult = te
        elif e[0] == "rompe":
            mez.add(te, M.golpe(), 1.0); mez.add(te, M.whoosh(0.3, e[3]), 0.5)
            k = e[3]; r = radio(k)
            for q in range(24):                                   # el anillo estalla en pedazos de su color
                a = 2 * math.pi * q / 24
                part.chispas(te, CX + r * math.cos(a), CY + r * math.sin(a), PALETA[k % len(PALETA)], 2,
                             v=(120, 380), ang=a, abertura=0.8, vida=0.8)
    t_fin = T_INI + t_juego
    mez.add(t_fin, M.bocina()); mez.add(t_fin, M.tribuna()); mez.add(t_fin + 0.9, M.boom(), 0.8); mez.add(t_fin + 0.95, M.ding())
    part.confeti(t_fin + 0.9)

    vid = M.Video(out / "mudo.mp4")
    for f in range(nf):
        tv = f / FPS; ts = tv - T_INI
        L = M.Lienzo(base); c = L.c; textos = []
        k = max(0, min(int(ts * FPS), len(sim["estados"]) - 1))
        bolas, angs = sim["estados"][k]
        puntos = [0] * n; rotos_ahora = set(); ult_rompe = {}
        for e in sim["eventos"]:
            if e[0] == "rompe" and e[1] <= ts:
                puntos = list(e[4]); rotos_ahora.add(e[3]); ult_rompe[e[2]] = e[1]
        # ---------- cabecera
        textos.append(((W / 2, 92), g["titulo"], M.ajustar(g["titulo"], 84, W - 70), (255, 255, 255), 8))
        sub = g.get("subtitulo", f"BREAK THE MOST RINGS TO WIN")
        textos.append(((W / 2, 178), sub, M.ajustar(sub, 46, W - 90), tema["acento"], 5))
        # marcador en vivo
        xs = [250, 830] if n == 2 else [140 + i * (W - 280) / (n - 1) for i in range(n)]
        lider = puntos.index(max(puntos)) if puntos.count(max(puntos)) == 1 and max(puntos) > 0 else None
        for i in range(n):
            x, y = xs[i], 330
            pulso = max(0.0, 1 - (ts - ult_rompe.get(i, -9)) / 0.4)
            apagado = ts > t_juego and i != sim["ganador"]
            L.brillo(x, y, 100 + 30 * pulso, comp[i]["color"], 0.25 + 0.35 * pulso)
            M.imagen(L, gris_sup[i] if apagado else marc_sup[i], x, y, escala=1 + 0.08 * pulso)
            L.circulo(x, y, 58 * (1 + 0.08 * pulso), None, borde=comp[i]["color"], ancho=6)
            if i == lider:
                M.trofeo(L, x, y - 92, 40)
            textos.append(((x, y + 92), nombres[i], M.ajustar(nombres[i], 42, 300 if n <= 2 else 200), comp[i]["color"], 5))
            if n == 2:
                textos.append(((W / 2 + (-85 if i == 0 else 85), y), str(puntos[i]), int(120 * (1 + 0.15 * pulso)), (255, 255, 255), 8))
            else:
                textos.append(((x, y + 160), str(puntos[i]), int(84 * (1 + 0.15 * pulso)), (255, 255, 255), 7))
        if n == 2:
            textos.append(((W / 2, 322), "-", 90, (200, 200, 215), 6))
        # ---------- anillos
        for kk in range(n_an):
            if kk in rotos_ahora:
                continue
            r = radio(kk); col = PALETA[kk % len(PALETA)]; hu = HUECO / r
            a0 = angs[kk] + hu / 2; a1 = angs[kk] + 2 * math.pi - hu / 2
            L.arco(CX, CY, r, a0, a1, col, 20, 0.12)
            L.arco(CX, CY, r, a0, a1, col, 8, 1.0)
        # ---------- pelotas con estela
        for i in range(n):
            if ts > t_juego + 0.05:
                break
            for j in range(9, 0, -1):
                kk = k - j
                if kk < 0:
                    continue
                ex, ey, _ = sim["estados"][kk][0][i]
                L.circulo(ex, ey, BALL * (1 - j / 11), comp[i]["color"], 0.22 * (1 - j / 10))
        for i in range(n):
            bx, by, ba = bolas[i]
            if ts > t_juego + 0.05:
                break
            L.brillo(bx, by, BALL * 2.1, comp[i]["color"], 0.3)
            M.imagen(L, bola_sup[i], bx, by, ang=ba)
            L.circulo(bx, by, BALL, None, borde=comp[i]["color"], ancho=4)
        part.dibujar(L, tv)
        # ---------- abajo
        quedan = n_an - len(rotos_ahora)
        if ts <= t_juego:
            txt = "LAST RING!" if quedan == 1 else f"{quedan} RINGS LEFT"
            textos.append(((W / 2, 1720), txt, 78 if quedan > 1 else 92, (255, 255, 255) if quedan > 1 else (255, 90, 90), 8))
            if ts < 2.4:
                textos.append(((W / 2, 1815), "PICK ONE BEFORE IT ENDS", 48, tema["acento"], 5))
        # ---------- final
        if ts > t_juego:
            ga = sim["ganador"]
            u = M.suave((ts - t_juego - 0.9) / 0.35)
            if ts < t_juego + 0.9:
                txt = f"{nombres[ga]} WINS {puntos[ga]}-{sorted(puntos)[-2]}"
                textos.append(((W / 2, 1720), txt, M.ajustar(txt, 86, W - 80), comp[ga]["color"], 8))
            else:
                c.new_path(); c.rectangle(0, 0, W, H); L.rgba((0, 0, 0), 0.78 * u); c.fill()
                for j in range(14):
                    a = j * 2 * math.pi / 14 + (ts - t_juego) * 0.35
                    c.new_path(); c.move_to(W / 2, 880); c.arc(W / 2, 880, 720, a, a + 0.11); c.close_path()
                    L.rgba(tema["acento"], 0.07 * u); c.fill()
                L.brillo(W / 2, 880, 320, comp[ga]["color"], 0.45 * u)
                M.imagen(L, gran_sup, W / 2, 880, escala=0.75 + 0.25 * u)
                L.circulo(W / 2, 880, 190 * (0.75 + 0.25 * u), None, borde=tema["acento"], ancho=12, borde_a=u)
                M.trofeo(L, W / 2, 585, 140 * u + 1, u)
                part.dibujar(L, tv)
                textos.append(((W / 2, 1150), "WINNER", 104, tema["acento"], 10))
                textos.append(((W / 2, 1275), nombres[ga], M.ajustar(nombres[ga], 130, W - 80), (255, 255, 255), 10))
                res = " - ".join(f"{nombres[i]} {puntos[i]}" for i in sorted(range(n), key=lambda i: -puntos[i]))
                textos.append(((W / 2, 1385), res, M.ajustar(res, 54, W - 80), (220, 225, 240), 5))
                ci = g.get("cierre", "WHO WAS YOUR PICK?")
                textos.append(((W / 2, 1500), ci, M.ajustar(ci, 74, W - 80), (255, 255, 255), 7))
        im = L.a_pil(); dr = ImageDraw.Draw(im)
        for xy, s, tam, col, borde in textos:
            M.texto(dr, xy, s, tam, col, borde)
        vid.cuadro(im)
    vid.cerrar()
    M.mezclar(out, out / "mudo.mp4", mez.versiones(beat_vol=0.35))
    res = {"ganador": comp[sim["ganador"]]["nombre"], "puntos": dict(zip([c["nombre"] for c in comp], sim["puntos"])),
           "dur": round(dur, 1), "cambios_de_lider": sim["cambios"]}
    json.dump(res, open(out / "resultado.json", "w"), ensure_ascii=False, indent=1)
    print("listo", out / "short.mp4", f"{dur:.1f}s", res)
    return res


if __name__ == "__main__":
    main(sys.argv[1])
