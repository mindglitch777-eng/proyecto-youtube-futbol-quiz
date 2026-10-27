#!/usr/bin/env python3
"""
CIRCLE CUP: torneo de 8 (jugadores, países o clubes) donde cada partido se juega en un ANILLO QUE GIRA con DOS ARCOS
y una pelota con física real. Como en el fútbol, cada uno defiende su arco: si la pelota entra en el arco de A,
es gol de B.

Por qué así (reporte 16): el círculo solo pega como TORNEO (Footrix: 3,9 M y 2,6 M con cuadro y 59 s);
las simulaciones que explotan suenan en cada rebote, escalan (la pelota acelera) y hacen loop.

Cuartos: primer gol. Semis: a 2. Final: a 3, con el gol decisivo en cámara lenta.
Uso: python3 render_copa.py guiones/copa_01.json  -> salida/<id>/short.mp4 (beat + efectos) y short_sin_musica.mp4
"""
import json
import math
import random
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np
import pymunk
from PIL import Image, ImageDraw, ImageFilter

from render_carrera import competidores
from render_find_the_real import BLANCO, FPS, H, SR, W, ROOT, ajustar, fuente, texto
from render_fusion import beat, efectos

CX, CY, R = W / 2, 1075, 385          # arena
GAP = 0.66                             # ancho angular de cada arco (rad)
BALL = 36
DT = 1 / 240
PAL = {"fondo": (8, 12, 24), "fondo2": (22, 30, 64), "aro": (120, 160, 255), "acento": (255, 210, 63)}
REGLAS = {"QF": 1, "SF": 2, "F": 3}
NOMBRE_RONDA = {"QF": "QUARTER-FINAL", "SF": "SEMI-FINAL", "F": "FINAL"}


# ------------------------------------------------------------------ física de un partido
def partido(goles_para_ganar, semilla, rot=1.25):
    rnd = random.Random(semilla)
    space = pymunk.Space(); space.gravity = (0, 950)
    aro = pymunk.Body(body_type=pymunk.Body.KINEMATIC); aro.position = (CX, CY)
    aro.angular_velocity = rot * rnd.choice([-1, 1]); aro.angle = rnd.uniform(0, 2 * math.pi)
    space.add(aro)
    n = 96
    for k in range(n):
        a0, a1 = 2 * math.pi * k / n, 2 * math.pi * (k + 1) / n
        am = (a0 + a1) / 2
        # dos arcos: centrados en 0 (equipo A) y en pi (equipo B)
        if min(abs((am + math.pi) % (2 * math.pi) - math.pi), abs(am - math.pi)) < GAP / 2:
            continue
        s = pymunk.Segment(aro, (R * math.cos(a0), R * math.sin(a0)), (R * math.cos(a1), R * math.sin(a1)), 7)
        s.elasticity = 1.0; s.friction = 0.2
        space.add(s)
    b = pymunk.Body(1, pymunk.moment_for_circle(1, 0, BALL))
    c = pymunk.Circle(b, BALL); c.elasticity = 0.98; c.friction = 0.3
    space.add(b, c)

    def saque():
        b.position = (CX + rnd.uniform(-40, 40), CY - 60)
        ang = rnd.uniform(0, 2 * math.pi); v = rnd.uniform(500, 750)
        b.velocity = (v * math.cos(ang), v * math.sin(ang)); b.angular_velocity = rnd.uniform(-8, 8)
    saque()
    goles = [0, 0]; t = 0.0; estados = []; eventos = []; pausa = 0.0; vprev = b.velocity
    golpes = 0
    while max(goles) < goles_para_ganar and t < 40:
        for _ in range(8):
            if pausa > 0:
                pausa -= DT; t += DT
                if pausa <= 0:
                    saque(); eventos.append(("saque", t))
                continue
            space.step(DT); t += DT
            # la pelota escala: cada rebote la acelera un poco (tensión creciente)
            dv = (b.velocity - vprev).length
            if dv > 300:
                golpes += 1
                eventos.append(("rebote", t, golpes))
                vel = b.velocity.length
                nueva = min(vel * 1.02 + 6, 1650) * (1 + rnd.uniform(-0.04, 0.04))
                b.velocity = b.velocity.normalized() * nueva
            vprev = b.velocity
            d = (b.position - aro.position)
            if d.length > R + BALL + 12:
                ang = (math.atan2(d.y, d.x) - aro.angle) % (2 * math.pi)
                quien = 0 if min(ang, 2 * math.pi - ang) < math.pi / 2 else 1
                goles[1 - quien] += 1                         # gol en el arco de A = gol de B
                eventos.append(("gol", t, 1 - quien, tuple(goles)))
                pausa = 0.75
                b.position = (CX, -500); b.velocity = (0, 0)   # fuera de cuadro durante el festejo
                break
        estados.append((b.position.x, b.position.y, b.angle, aro.angle))
    return dict(estados=estados, eventos=eventos, goles=goles, ganador=0 if goles[0] > goles[1] else 1, dur=t)


def elegir(goles, quiere, dmin, dmax, base, max_intentos=400):
    """Busca una semilla donde gana `quiere` (0/1), con duración dentro de rango y el partido más parejo."""
    mejor = None
    for s in range(base, base + max_intentos):
        p = partido(goles, s)
        if p["ganador"] != quiere or not (dmin <= p["dur"] <= dmax) or max(p["goles"]) != goles:
            continue
        diff = abs(p["goles"][0] - p["goles"][1])
        punt = -diff * 3 + sum(1 for e in p["eventos"] if e[0] == "rebote") * 0.01
        if mejor is None or punt > mejor[0]:
            mejor = (punt, s, p)
            if diff == 1 and goles > 1:
                break
            if goles == 1:
                break
    if mejor is None:
        raise SystemExit(f"sin semilla para goles={goles} dur={dmin}-{dmax}")
    return mejor[2]


# ------------------------------------------------------------------ torneo
def armar_torneo(g):
    n = len(g["competidores"])
    assert n == 8
    gan = {c["nombre"]: i for i, c in enumerate(g["competidores"])}
    ruta = g.get("ruta", {})                       # nombre -> hasta qué ronda gana ("QF","SF","F")
    orden_rondas = ["QF", "SF", "F"]

    def gana_en(i, ronda):
        hasta = ruta.get(g["competidores"][i]["nombre"])
        return hasta is not None and orden_rondas.index(hasta) >= orden_rondas.index(ronda)
    rondas = []
    vivos = list(range(8))
    base = g.get("semilla", 0) * 1000
    for ronda in orden_rondas:
        partidos = []
        sig = []
        for k in range(0, len(vivos), 2):
            a, b = vivos[k], vivos[k + 1]
            quiere = 0 if gana_en(a, ronda) and not gana_en(b, ronda) else 1 if gana_en(b, ronda) and not gana_en(a, ronda) else random.Random(base + k).randint(0, 1)
            goles = REGLAS[ronda]
            dmin, dmax = {"QF": (2.8, 6.5), "SF": (5.5, 10.5), "F": (10, 17)}[ronda]
            p = elegir(goles, quiere, dmin, dmax, base + len(rondas) * 100 + k * 10)
            partidos.append(dict(ronda=ronda, a=a, b=b, sim=p))
            sig.append(a if p["ganador"] == 0 else b)
            print(ronda, g["competidores"][a]["nombre"], p["goles"], g["competidores"][b]["nombre"], f"{p['dur']:.1f}s")
        rondas.append(partidos)
        vivos = sig
    return rondas, vivos[0]


# ------------------------------------------------------------------ audio propio
NOTAS = [261.6, 293.7, 329.6, 392.0, 440.0, 523.3, 587.3, 659.3, 784.0, 880.0, 1046.5]   # pentatónica


def pluck(f, d=0.22):
    t = np.arange(int(d * SR)) / SR
    e = np.exp(-t * 18)
    return (np.sin(2 * np.pi * f * t) + 0.4 * np.sin(4 * np.pi * f * t) + 0.15 * np.sin(6 * np.pi * f * t)) * e * 0.28


def silbato(d=0.5):
    t = np.arange(int(d * SR)) / SR
    return np.sin(2 * np.pi * (2900 + 120 * np.sin(2 * np.pi * 38 * t)) * t) * np.minimum(t / 0.02, 1) * np.exp(-t * 2) * 0.22


def bocina(d=0.9):
    t = np.arange(int(d * SR)) / SR
    s = sum(np.sign(np.sin(2 * np.pi * f * t)) for f in (220, 277, 330)) / 3
    s = np.convolve(s, np.ones(30) / 30, mode="same")
    return s * np.minimum(t / 0.03, 1) * np.exp(-t * 2.2) * 0.35


def tribuna(d=1.6, rng=np.random.default_rng(4)):
    nz = np.convolve(rng.standard_normal(int(d * SR)), np.ones(50) / 50, mode="same")
    t = np.arange(len(nz)) / SR
    return nz * np.minimum(t / 0.15, 1) * np.exp(-t * 1.5) * 2.6


# ------------------------------------------------------------------ dibujo
def fondo():
    y, x = np.indices((H, W), dtype=np.float32)
    d = np.sqrt(((x - CX) / W) ** 2 + ((y - CY) / H) ** 2)
    a = np.array(PAL["fondo"], np.float32); b = np.array(PAL["fondo2"], np.float32)
    t = np.clip(1 - d * 2.2, 0, 1)[..., None]
    im = Image.fromarray((a + (b - a) * t).astype(np.uint8), "RGB")
    # césped dentro del anillo: franjas, círculo central y punto
    cesped = Image.new("RGB", (2 * R, 2 * R), (24, 110, 58)); dc = ImageDraw.Draw(cesped)
    for k in range(0, 2 * R, 70):
        if (k // 70) % 2:
            dc.rectangle((0, k, 2 * R, k + 70), fill=(30, 124, 66))
    dc.line((0, R, 2 * R, R), fill=(220, 240, 225), width=5)
    dc.ellipse((R - 95, R - 95, R + 95, R + 95), outline=(220, 240, 225), width=5)
    dc.ellipse((R - 9, R - 9, R + 9, R + 9), fill=(220, 240, 225))
    m = Image.new("L", (2 * R, 2 * R), 0); ImageDraw.Draw(m).ellipse((0, 0, 2 * R - 1, 2 * R - 1), fill=255)
    sombra = Image.new("L", (2 * R, 2 * R), 0); ImageDraw.Draw(sombra).ellipse((30, 30, 2 * R - 30, 2 * R - 30), fill=255)
    oscuro = Image.composite(cesped, Image.blend(cesped, Image.new("RGB", cesped.size, (0, 0, 0)), 0.35), sombra.filter(ImageFilter.GaussianBlur(40)))
    im.paste(oscuro, (int(CX - R), int(CY - R)), m)
    return im


def pelota_img(d=2 * BALL):
    from marca.perfil import pelota
    return pelota(d)


def main(guion_path):
    g = json.loads(Path(guion_path).read_text())
    comp = competidores(g, 150)
    caras = {i: c["img"] for i, c in enumerate(comp)}
    chicas = {i: c["img"].resize((62, 62), Image.LANCZOS) for i, c in enumerate(comp)}
    esp = {"Vinícius Júnior": "VINÍCIUS", "Kylian Mbappé": "MBAPPÉ"}
    nombres = [c.get("corto_hud") or (esp.get(c["nombre"], c["nombre"].split()[-1].upper()) if c["tipo"] == "jugador"
               else c.get("corto", c["nombre"]).upper()) for c in comp]
    rondas, campeon = armar_torneo(g)
    out = ROOT / "salida" / g["id"]; out.mkdir(parents=True, exist_ok=True)
    bola = pelota_img()
    base = fondo()

    # línea de tiempo: intro, partidos (con cartel de ronda), festejo final
    T_INTRO, T_CARTEL, T_FIN = 1.6, 0.7, 3.4
    plan = []           # (t0, tipo, datos)
    t = T_INTRO
    for r_i, partidos in enumerate(rondas):
        plan.append((t, "cartel", partidos[0]["ronda"])); t += T_CARTEL
        for m_i, p in enumerate(partidos):
            plan.append((t, "partido", (r_i, m_i, p)))
            lento = p["ronda"] == "F"
            t += p["sim"]["dur"] / (1 if not lento else 1) + 0.5 + (0.9 if lento else 0)
    t_fin = t
    dur = t_fin + T_FIN
    nf = int(dur * FPS)

    # quién sigue vivo en cada momento (para el cuadro)
    def resultado_hasta(tv):
        res = {}
        for t0, tipo, d in plan:
            if tipo == "partido" and tv >= t0 + d[2]["sim"]["dur"] + 0.2:
                p = d[2]; res[(d[0], d[1])] = p["a"] if p["sim"]["ganador"] == 0 else p["b"]
        return res

    sonidos = [("silbato", 0.0)]
    for t0, tipo, d in plan:
        if tipo == "cartel":
            sonidos.append(("whoosh", t0))
        elif tipo == "partido":
            p = d[2]
            sonidos.append(("silbato", t0))
            for e in p["sim"]["eventos"]:
                if e[0] == "rebote":
                    sonidos.append(("nota", t0 + e[1], e[2]))
                elif e[0] == "gol":
                    sonidos += [("bocina", t0 + e[1]), ("tribuna", t0 + e[1])]
            sonidos.append(("silbato", t0 + p["sim"]["dur"] + 0.1))
    sonidos += [("boom", t_fin), ("tribuna", t_fin), ("ding", t_fin + 0.1)]

    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
                           str(out / "mudo.mp4")], stdin=subprocess.PIPE)
    rng = np.random.default_rng(7)
    confeti = [(rng.uniform(0, W), rng.uniform(-500, 0), rng.uniform(260, 720), rng.uniform(-90, 90),
                tuple(int(x) for x in rng.choice([[255, 210, 63], [255, 255, 255], [240, 84, 76], [61, 214, 128], [80, 180, 255]])))
               for _ in range(170)]
    estela = []
    for f in range(nf):
        tv = f / FPS
        im = base.copy(); dr = ImageDraw.Draw(im, "RGBA")
        actual = None
        for t0, tipo, d in plan:
            if tv >= t0:
                actual = (t0, tipo, d)
        res = resultado_hasta(tv)
        # ---------- cabecera: evento + cuadro compacto
        texto(dr, (W / 2, 70), g["evento"], ajustar(g["evento"], 70, W - 80), PAL["acento"], 8)
        filas = [list(range(8)), [res.get((0, k)) for k in range(4)], [res.get((1, k)) for k in range(2)], [res.get((2, 0))]]
        for fi, fila in enumerate(filas):
            y = 150 + fi * 56
            paso = (W - 160) / len(fila)
            for k, i in enumerate(fila):
                x = 80 + paso * k + paso / 2
                if i is None:
                    dr.ellipse((x - 27, y - 27, x + 27, y + 27), outline=(255, 255, 255, 110), width=3)
                    texto(dr, (x, y), "?", 32, (200, 200, 220), 3)
                else:
                    elim = fi < 3 and any(res.get((fi, m)) not in (None, i) and i in (rondas[fi][m]["a"], rondas[fi][m]["b"]) for m in range(len(rondas[fi])))
                    img = chicas[i] if not elim else Image.fromarray(np.asarray(chicas[i].convert("LA").convert("RGBA")))
                    im.paste(img.resize((56, 56)), (int(x - 28), int(y - 28)), img.resize((56, 56)))
                    if fi == 3:
                        dr.ellipse((x - 30, y - 30, x + 30, y + 30), outline=PAL["acento"], width=5)
        if actual is None or tv < T_INTRO:
            # intro: los 8 y la pregunta
            texto(dr, (W / 2, 520), g["titulo"], ajustar(g["titulo"], 96, W - 80), BLANCO, 10)
            for k in range(8):
                ang = 2 * math.pi * k / 8 + tv * 0.8
                x, y = CX + 270 * math.cos(ang), CY + 270 * math.sin(ang)
                im.paste(caras[k].resize((120, 120)), (int(x - 60), int(y - 60)), caras[k].resize((120, 120)))
            texto(dr, (CX, CY), "PICK ONE", 96, PAL["acento"], 10)
        elif actual[1] == "cartel":
            ronda = actual[2]
            u = min((tv - actual[0]) / 0.25, 1)
            texto(dr, (W / 2, CY - 40), NOMBRE_RONDA[ronda], int(ajustar(NOMBRE_RONDA[ronda], 130, W - 80) * (0.7 + 0.3 * u)), PAL["acento"], 12)
            texto(dr, (W / 2, CY + 90), f"FIRST TO {REGLAS[ronda]} GOAL{'S' if REGLAS[ronda] > 1 else ''}", 62, BLANCO, 8)
        elif actual[1] == "partido":
            r_i, m_i, p = actual[2]
            sim = p["sim"]; ts = tv - actual[0]
            final = p["ronda"] == "F"
            # cámara lenta del gol decisivo en la final
            t_ult = [e[1] for e in sim["eventos"] if e[0] == "gol"][-1]
            if final and ts > t_ult - 0.9:
                ts_sim = t_ult - 0.9 + (ts - (t_ult - 0.9)) * 0.35 if ts < t_ult - 0.9 + 0.9 / 0.35 else t_ult + (ts - (t_ult - 0.9) - 0.9 / 0.35)
            else:
                ts_sim = ts
            k = min(int(ts_sim * FPS), len(sim["estados"]) - 1)
            bx, by, bang, aang = sim["estados"][k]
            goles = [0, 0]
            for e in sim["eventos"]:
                if e[0] == "gol" and e[1] <= ts_sim:
                    goles = list(e[3])
            # marcador
            for lado, i in enumerate((p["a"], p["b"])):
                x = W / 2 + (-1 if lado == 0 else 1) * 300
                im.paste(caras[i].resize((130, 130)), (int(x - 65), 410), caras[i].resize((130, 130)))
                dr.ellipse((x - 67, 408, x + 67, 542), outline=comp[i]["color"], width=6)
                texto(dr, (x, 575), nombres[i], ajustar(nombres[i], 44, 260), comp[i]["color"], 6)
            texto(dr, (W / 2, 480), f"{goles[0]} - {goles[1]}", 110, BLANCO, 10)
            texto(dr, (W / 2, 385), NOMBRE_RONDA[p["ronda"]], 40, PAL["acento"], 5)
            # anillo girando con dos arcos (cada arco con la cara de su dueño)
            n = 120
            for kk in range(n):
                a0 = 2 * math.pi * kk / n + aang; a1 = a0 + 2 * math.pi / n
                am = (2 * math.pi * (kk + 0.5) / n)
                if min(abs((am + math.pi) % (2 * math.pi) - math.pi), abs(am - math.pi)) < GAP / 2:
                    continue
                da = min(abs(am), 2 * math.pi - am); db = abs(am - math.pi)
                dueno = comp[p["a"]]["color"] if da < db else comp[p["b"]]["color"]
                mezcla = max(0.0, 1 - min(da, db) / 1.2)
                brillo = 0.8 + 0.2 * math.sin(am * 3 + tv * 4)
                col = tuple(int((c1 * (1 - mezcla) + c2 * mezcla) * brillo) for c1, c2 in zip(PAL["aro"], dueno))
                dr.line((CX + R * math.cos(a0), CY + R * math.sin(a0), CX + R * math.cos(a1), CY + R * math.sin(a1)), fill=col, width=24)
            for lado, i in enumerate((p["a"], p["b"])):
                am = aang + (0 if lado == 0 else math.pi)
                # postes del arco
                for s in (-1, 1):
                    a = am + s * GAP / 2
                    dr.ellipse((CX + R * math.cos(a) - 13, CY + R * math.sin(a) - 13, CX + R * math.cos(a) + 13, CY + R * math.sin(a) + 13),
                               fill=comp[i]["color"])
                # red: arcos concéntricos detrás de la abertura
                poli = [(CX + R * math.cos(am + GAP / 2 * x / 8), CY + R * math.sin(am + GAP / 2 * x / 8)) for x in range(-8, 9)]
                poli += [(CX + (R + 58) * math.cos(am + GAP / 2 * x / 8 * 0.85), CY + (R + 58) * math.sin(am + GAP / 2 * x / 8 * 0.85)) for x in range(8, -9, -1)]
                dr.polygon(poli, fill=comp[i]["color"] + (70,))
                for rr in (R + 16, R + 32, R + 48):
                    pts = [(CX + rr * math.cos(am + GAP / 2 * x / 8 * 0.9), CY + rr * math.sin(am + GAP / 2 * x / 8 * 0.9)) for x in range(-8, 9)]
                    dr.line(pts, fill=(255, 255, 255, 120), width=2)
                for x in range(-8, 9, 2):
                    a = am + GAP / 2 * x / 8 * 0.9
                    dr.line((CX + R * math.cos(a), CY + R * math.sin(a), CX + (R + 58) * math.cos(a), CY + (R + 58) * math.sin(a)), fill=(255, 255, 255, 110), width=2)
                xx, yy = CX + (R + 125) * math.cos(am), CY + (R + 125) * math.sin(am)
                im.paste(chicas[i].resize((110, 110)), (int(xx - 55), int(yy - 55)), chicas[i].resize((110, 110)))
                dr.ellipse((xx - 57, yy - 57, xx + 57, yy + 57), outline=comp[i]["color"], width=6)
            # pelota con estela
            if by > 0:
                estela.append((bx, by)); estela[:] = estela[-14:]
                for j, (ex, ey) in enumerate(estela[:-1]):
                    a = int(120 * j / len(estela)); rr = BALL * (0.4 + 0.6 * j / len(estela))
                    dr.ellipse((ex - rr, ey - rr, ex + rr, ey + rr), fill=PAL["acento"] + (a,))
                dr.ellipse((bx - BALL * 1.5, by - BALL * 1.5, bx + BALL * 1.5, by + BALL * 1.5), fill=(255, 230, 120, 45))
                dr.ellipse((bx - BALL + 8, by - BALL + 14, bx + BALL + 8, by + BALL + 14), fill=(0, 0, 0, 70))
                bi = bola.rotate(-math.degrees(bang), resample=Image.BICUBIC)
                im.paste(bi, (int(bx - BALL), int(by - BALL)), bi)
            else:
                estela.clear()
            # festejo de gol
            for e in sim["eventos"]:
                if e[0] == "gol" and 0 <= ts_sim - e[1] < 0.75:
                    u = (ts_sim - e[1]) / 0.75
                    quien = (p["a"], p["b"])[e[2]]
                    dr.ellipse((CX - R * (1 + u * 0.3), CY - R * (1 + u * 0.3), CX + R * (1 + u * 0.3), CY + R * (1 + u * 0.3)),
                               outline=comp[quien]["color"] + (int(255 * (1 - u)),), width=14)
                    texto(dr, (CX, CY), "GOAL!", int(150 * (0.7 + 0.3 * min(u * 4, 1))), PAL["acento"], 12)
                    texto(dr, (CX, CY + 120), nombres[quien], 70, comp[quien]["color"], 8)
            if final and t_ult - 0.9 < ts_sim < t_ult:
                dr.rectangle((0, 0, W, H), outline=(240, 60, 60, 160), width=22)
                texto(dr, (CX, 1560), "MATCH POINT", 80, (255, 90, 90), 9)
            elif not final:
                texto(dr, (CX, 1560), f"FIRST TO {REGLAS[p['ronda']]}", 64, (210, 215, 235), 7)
        if tv >= t_fin:
            u = min((tv - t_fin) / 0.3, 1)
            dr.rectangle((0, 330, W, H), fill=(0, 0, 0, int(200 * u)))
            d = int(380 * (0.7 + 0.3 * u))
            big = caras[campeon].resize((d, d), Image.LANCZOS)
            im.paste(big, (W // 2 - d // 2, 640), big)
            dr.ellipse((W / 2 - d / 2 - 6, 634, W / 2 + d / 2 + 6, 646 + d), outline=PAL["acento"], width=12)
            texto(dr, (W / 2, 560), "CHAMPION", 110, PAL["acento"], 12)
            texto(dr, (W / 2, 1130), nombres[campeon], ajustar(nombres[campeon], 140, W - 80), BLANCO, 12)
            texto(dr, (W / 2, 1270), g.get("cierre", "WHO WAS YOUR PICK?"), ajustar(g.get("cierre", "WHO WAS YOUR PICK?"), 76, W - 80), BLANCO, 8)
            for x, y, v, vx, col in confeti:
                tt = tv - t_fin; yy = y + v * tt; xx = x + vx * tt + 22 * math.sin(tt * 6 + x)
                if 0 < yy < H:
                    dr.rectangle((xx, yy, xx + 14, yy + 22), fill=col)
        if actual is not None and actual[1] == "partido":
            for e in actual[2][2]["sim"]["eventos"]:
                if e[0] == "gol" and 0 <= tv - actual[0] - e[1] < 0.25:
                    k_ = 14 * (1 - (tv - actual[0] - e[1]) / 0.25)
                    im = Image.fromarray(np.roll(np.asarray(im), (int(rng.uniform(-k_, k_)), int(rng.uniform(-k_, k_))), (0, 1)))
        ff.stdin.write(np.asarray(im, np.uint8).tobytes())
    ff.stdin.close(); ff.wait()

    # ---------- audio
    mix = np.zeros(int(dur * SR) + SR, np.float32)
    fx = efectos(4)

    def add(s, sig, vol=1.0):
        i = int(s * SR); j = min(len(mix), i + len(sig))
        if 0 <= i < len(mix):
            mix[i:j] += vol * sig[: j - i]
    ult = -1
    for s in sonidos:
        tipo, t0 = s[0], s[1]
        if tipo == "nota":
            if t0 - ult < 0.06:
                continue
            ult = t0
            add(t0, pluck(NOTAS[min(s[2] // 3, len(NOTAS) - 1)]))
        elif tipo == "silbato":
            add(t0, silbato())
        elif tipo == "bocina":
            add(t0, bocina())
        elif tipo == "tribuna":
            add(t0, tribuna())
        else:
            add(t0, fx[tipo])
    solo = mix[: int(dur * SR)].copy()
    con = solo + beat(dur)[: len(solo)] * 0.55
    for nombre_v, pista in (("short.mp4", np.tanh(con * 1.2) * 0.9), ("short_sin_musica.mp4", np.tanh(solo * 1.1) * 0.7)):
        with wave.open(str(out / "audio.wav"), "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
            w.writeframes((np.clip(pista, -1, 1) * 32767).astype(np.int16).tobytes())
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(out / "mudo.mp4"), "-i", str(out / "audio.wav"),
                        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", str(out / nombre_v)], check=True)
    (out / "mudo.mp4").unlink()
    json.dump({"campeon": comp[campeon]["nombre"], "dur": round(dur, 1),
               "partidos": [[comp[p["a"]]["nombre"], p["sim"]["goles"], comp[p["b"]]["nombre"]] for r in rondas for p in r]},
              open(out / "resultado.json", "w"), ensure_ascii=False, indent=1)
    print("listo", out / "short.mp4", f"{dur:.1f}s", "campeón", comp[campeon]["nombre"])


if __name__ == "__main__":
    main(sys.argv[1])
