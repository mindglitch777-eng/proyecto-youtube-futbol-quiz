#!/usr/bin/env python3
"""
CIRCLE CUP V2: misma física real que la Circle Cup (render_copa.partido), dibujada con el motor V2:
60 fps, antialias, anillo de neón, cámara fija (sin sacudones), escudos/banderas/caras reales,
skins de pelota y de arco, cuadro de torneo con líneas que se iluminan (receta Footrix, 3,9 M).

Mejoras sobre la receta (reporte 17): arranca en el cuadro 0 sin intro muerta, nota musical por rebote
que sube con la tensión, arco con red que se infla en el gol, chispas del color del que convierte,
match point con borde rojo (sin temblor), gol final en cámara lenta, campeón con copa y confeti.

Uso: python3 render_copa_v2.py guiones/copa_01.json  -> salida/<id>_v2/short.mp4 y short_sin_musica.mp4
Guion: además de los campos de la copa v1 acepta "tema", "pelota" (skin) y "arco" (skin).
"""
import json
import math
import sys
from pathlib import Path

import cairocffi as cairo
from PIL import ImageDraw

import render_copa as RC
import motor as M
from motor import W, H, FPS
from render_carrera import competidores

RC.SUB = 4                                   # estados a 60 fps
RC.DURS = {"QF": (2.6, 5.6), "SF": (5.0, 9.0), "F": (9.0, 14.0)}
CX, CY, R, BALL, GAP = RC.CX, 1150, RC.R, RC.BALL, RC.GAP
DY = CY - RC.CY                              # la física usa CY=1075; se dibuja desplazada
NOMBRE_RONDA = {"QF": "QUARTER-FINAL", "SF": "SEMI-FINAL", "F": "FINAL"}

TEMAS = {
    "oro": dict(f1=(10, 8, 4), f2=(58, 42, 12), aro=(255, 206, 96), acento=(255, 214, 80)),
    "noche": dict(f1=(5, 8, 22), f2=(22, 36, 88), aro=(110, 165, 255), acento=(255, 214, 80)),
    "champions": dict(f1=(3, 6, 26), f2=(18, 30, 100), aro=(140, 190, 255), acento=(235, 240, 255)),
    "cancha": dict(f1=(3, 16, 9), f2=(14, 64, 36), aro=(90, 255, 160), acento=(255, 214, 80)),
}
ARCOS = {   # postes, red
    "blanco": dict(poste=(250, 250, 250), red=(255, 255, 255), glow=None),
    "neon": dict(poste=(80, 255, 220), red=(80, 255, 220), glow=(80, 255, 220)),
    "dorado": dict(poste=(255, 210, 90), red=(255, 230, 150), glow=(255, 200, 80)),
}


def fondo_estatico(tema):
    s = M.superficie_fondo(tema["f1"], tema["f2"], cy=CY / H)
    c = cairo.Context(s); c.set_antialias(cairo.ANTIALIAS_BEST)
    # césped dentro del anillo
    c.save(); c.arc(CX, CY, R - 4, 0, 2 * math.pi); c.clip()
    for k in range(-6, 7):
        c.rectangle(CX - R, CY + k * 62 - 31, 2 * R, 62)
        c.set_source_rgb(*(v / 255 for v in ((26, 112, 60) if k % 2 else (31, 126, 68)))); c.fill()
    c.set_source_rgba(1, 1, 1, 0.75); c.set_line_width(5)
    c.move_to(CX - R, CY); c.line_to(CX + R, CY); c.stroke()
    c.arc(CX, CY, 92, 0, 2 * math.pi); c.stroke()
    c.arc(CX, CY, 9, 0, 2 * math.pi); c.fill()
    g = cairo.RadialGradient(CX, CY, R * 0.55, CX, CY, R)            # viñeta interior
    g.add_color_stop_rgba(0, 0, 0, 0, 0); g.add_color_stop_rgba(1, 0, 0, 0, 0.45)
    c.set_source(g); c.paint(); c.restore()
    return s


def preparar(g):
    comp = competidores(g, 400)
    esp = {"Vinícius Júnior": "VINÍCIUS", "Kylian Mbappé": "MBAPPÉ", "Lamine Yamal": "YAMAL"}
    nombres = [c.get("corto_hud") or (esp.get(c["nombre"], c["nombre"].split()[-1].upper()) if c["tipo"] == "jugador"
               else c.get("corto", c["nombre"]).upper()) for c in comp]
    sup = {}

    def S(i, d, apagado=False):
        k = (i, d, apagado)
        if k not in sup:
            im = comp[i]["img"].resize((d, d), M.Image.LANCZOS)
            sup[k] = M.pil_a_cairo(M.gris(im, 0.55) if apagado else im)
        return sup[k]
    return comp, nombres, S


def construir_plan(rondas):
    """Línea de tiempo: partidos seguidos, sin pantallas muertas. Devuelve plan y duración."""
    plan, t = [], 0.25
    for r_i, partidos in enumerate(rondas):
        for m_i, p in enumerate(partidos):
            final = p["ronda"] == "F"
            extra = (0.9 / 0.35 - 0.9) if final else 0.0                  # cámara lenta del último gol
            post = 1.5 if final else 0.95
            plan.append(dict(t0=t, r=r_i, m=m_i, p=p, final=final, fin_juego=t + p["sim"]["dur"] + extra,
                             fin=t + p["sim"]["dur"] + extra + post))
            t = plan[-1]["fin"]
    return plan, t


def tiempo_sim(it, ts):
    """Tiempo de simulación para el tiempo de pantalla ts (cámara lenta 0.35x en el gol final)."""
    sim = it["p"]["sim"]
    if not it["final"]:
        return ts
    t_ult = [e[1] for e in sim["eventos"] if e[0] == "gol"][-1]
    a = t_ult - 0.9
    if ts <= a:
        return ts
    if ts <= a + 0.9 / 0.35:
        return a + (ts - a) * 0.35
    return t_ult + (ts - a - 0.9 / 0.35)


def main(guion_path, sufijo="_v2"):
    g = json.loads(Path(guion_path).read_text())
    tema = TEMAS[g.get("tema", "noche")]; arco_sk = ARCOS[g.get("arco", "blanco")]; skin = g.get("pelota", "clasica")
    comp, nombres, S = preparar(g)
    rondas, campeon = RC.armar_torneo(g)
    plan, t_fin = construir_plan(rondas)
    T_FIN = 3.6
    dur = t_fin + T_FIN
    nf = int(dur * FPS)
    out = M.ROOT / "salida" / (g["id"] + sufijo); out.mkdir(parents=True, exist_ok=True)
    base = fondo_estatico(tema)

    # ---------------- cuadro del torneo (posiciones)
    QF = [(120 + 120 * k, 168) for k in range(8)]
    SF = [((QF[2 * k][0] + QF[2 * k + 1][0]) / 2, 262) for k in range(4)]
    FI = [((SF[0][0] + SF[1][0]) / 2, 350), ((SF[2][0] + SF[3][0]) / 2, 350)]
    CAMP = (W / 2, 350)
    slots = [QF, SF, FI]

    def ocupante(ronda, k, tv):
        """Quién ocupa el casillero k de la ronda (0=QF,1=SF,2=F,3=campeón) en el tiempo tv, y desde cuándo."""
        if ronda == 0:
            return k, -1
        it = next(x for x in plan if x["r"] == ronda - 1 and x["m"] == k)
        if tv < it["fin_juego"] + 0.15:
            return None, None
        p = it["p"]
        return (p["a"] if p["sim"]["ganador"] == 0 else p["b"]), it["fin_juego"] + 0.15

    # ---------------- sonido
    mez = M.Mezcla(dur)
    sil, boc, tri, who, bm, dg = M.silbato(), M.bocina(), M.tribuna(), M.whoosh(), M.boom(), M.ding()
    notas = {f: M.pluck(f) for f in M.NOTAS}
    part = M.Particulas(5)
    for it in plan:
        t0, sim = it["t0"], it["p"]["sim"]
        mez.add(t0, sil, 0.9)
        ult = -1
        for e in sim["eventos"]:
            te = t0 + (e[1] if not it["final"] else pantalla_de(it, e[1]))
            if e[0] == "rebote" and te - ult > 0.06:
                ult = te; mez.add(te, notas[M.NOTAS[min(e[2] // 3, len(M.NOTAS) - 1)]])
            elif e[0] == "gol":
                mez.add(te, boc); mez.add(te, tri, 0.9)
                quien = (it["p"]["a"], it["p"]["b"])[e[2]]
                # chispas desde el arco donde entró (el del rival)
                st = sim["estados"][min(int(e[1] * FPS), len(sim["estados"]) - 1)]
                ang_arco = st[3] + (math.pi if e[2] == 0 else 0)
                part.chispas(te, CX + R * math.cos(ang_arco), CY + R * math.sin(ang_arco), comp[quien]["color"], 46,
                             ang=ang_arco, abertura=2.4)
        mez.add(it["fin_juego"], sil, 0.7)
        mez.add(it["fin_juego"] + 0.15, who, 0.6)
    mez.add(t_fin, bm); mez.add(t_fin, tri); mez.add(t_fin + 0.1, dg)
    part.confeti(t_fin + 0.1)
    part.chispas(t_fin + 0.1, W / 2, 860, tema["acento"], 90, v=(500, 1300), vida=1.3)

    vid = M.Video(out / "mudo.mp4")
    for f in range(nf):
        tv = f / FPS
        L = M.Lienzo(base); c = L.c
        it = next((x for x in plan if x["t0"] <= tv < x["fin"]), None)
        textos = []                                          # (xy, s, tam, color, borde)

        # ---------- cabecera
        textos.append(((W / 2, 64), g["evento"], M.ajustar(g["evento"], 64, W - 120), tema["acento"], 7))
        # líneas del cuadro (se iluminan con el color del que avanza)
        for ronda in range(3):
            for k in range(len(slots[ronda])):
                x0, y0 = slots[ronda][k]
                dest = slots[ronda + 1][k // 2] if ronda < 2 else CAMP
                i, desde = ocupante(ronda + 1, k // 2, tv) if ronda < 2 else (None, None)
                if ronda == 2:
                    i, desde = (campeon, t_fin - 1.5 + 0.15) if tv >= t_fin - 1.5 + 0.15 else (None, None)
                pasa = i is not None and i == ocupante(ronda, k, tv)[0]
                col = comp[i]["color"] if pasa else (255, 255, 255)
                u = M.suave((tv - desde) / 0.45) if pasa else 0
                a = 0.22 + 0.7 * u
                ym = (y0 + dest[1]) / 2 if ronda < 2 else y0
                if ronda < 2:
                    L.linea(x0, y0 + 30, x0, ym, col, 4, a); L.linea(x0, ym, dest[0], ym, col, 4, a)
                    L.linea(dest[0], ym, dest[0], dest[1] - 30, col, 4, a)
                else:
                    L.linea(x0 + (36 if x0 < CAMP[0] else -36), y0, CAMP[0] + (-46 if x0 < CAMP[0] else 46), y0, col, 4, a)
        # casilleros
        for ronda in range(3):
            d = (72, 66, 66)[ronda]
            for k, (x, y) in enumerate(slots[ronda]):
                i, desde = ocupante(ronda, k, tv)
                if i is None:
                    L.circulo(x, y, d / 2, (255, 255, 255), 0.06, borde=(255, 255, 255), ancho=2.5, borde_a=0.35)
                    textos.append(((x, y + 2), "?", 30, (210, 215, 235), 0))
                    continue
                elim = False
                if ronda < 2 or True:
                    sig = ocupante(ronda + 1, k // 2, tv)[0] if ronda < 2 else (campeon if tv >= t_fin - 1.35 else None)
                    elim = sig is not None and sig != i
                u = M.suave((tv - desde) / 0.35) if desde is not None and desde >= 0 else 1
                M.imagen(L, S(i, d, elim), x, y, escala=0.6 + 0.4 * u)
                L.circulo(x, y, d / 2, None, borde=comp[i]["color"] if not elim else (90, 90, 100), ancho=3.5)
        # casillero del campeón
        if tv >= t_fin - 1.35:
            u = M.suave((tv - (t_fin - 1.35)) / 0.4)
            L.brillo(*CAMP, 80, tema["acento"], 0.5 * u)
            M.imagen(L, S(campeon, 84), *CAMP, escala=0.6 + 0.4 * u)
            L.circulo(*CAMP, 42, None, borde=tema["acento"], ancho=5)
        else:
            L.circulo(*CAMP, 42, (0, 0, 0), 0.25, borde=tema["acento"], ancho=3, borde_a=0.6)
            M.trofeo(L, CAMP[0], CAMP[1], 52, 0.95)

        # ---------- partido
        if it is not None:
            p, sim = it["p"], it["p"]["sim"]
            ts = tv - it["t0"]; tsim = tiempo_sim(it, ts)
            k = max(0, min(int(tsim * FPS), len(sim["estados"]) - 1))
            bx, by, bang, aang = sim["estados"][k]; by += DY
            goles = [0, 0]; ult_rebote = -9
            for e in sim["eventos"]:
                if e[0] == "gol" and e[1] <= tsim:
                    goles = list(e[3])
                if e[0] == "rebote" and e[1] <= tsim:
                    ult_rebote = e[1]
            ganador = (p["a"], p["b"])[sim["ganador"]]
            # marcador
            ronda_txt = NOMBRE_RONDA[p["ronda"]] + ("" if p["ronda"] == "F" else f"  ·  MATCH {it['m'] + 1}/{len(rondas[it['r']])}")
            textos.append(((W / 2, 452), ronda_txt, 38, tema["acento"], 4))
            for lado, i in enumerate((p["a"], p["b"])):
                x = (170, 910)[lado]
                perdio = tv >= it["fin_juego"] and i != ganador
                L.brillo(x, 535, 100, comp[i]["color"], 0.25 if not perdio else 0.0)
                M.imagen(L, S(i, 128, perdio), x, 535)
                L.circulo(x, 535, 64, None, borde=comp[i]["color"] if not perdio else (90, 90, 100), ancho=6)
                textos.append(((x, 632), nombres[i], M.ajustar(nombres[i], 44, 300), comp[i]["color"] if not perdio else (130, 130, 140), 5))
            textos.append(((W / 2, 540), f"{goles[0]}  -  {goles[1]}", 112, (255, 255, 255), 8))

            # anillo: halo + núcleo, cada mitad tiñéndose hacia el color de su arco
            flash = max(0.0, 1 - (tsim - ult_rebote) / 0.18) if tsim >= ult_rebote else 0
            for lado, i in enumerate((p["a"], p["b"])):
                centro = aang + (0 if lado == 0 else math.pi)
                n = 22
                for s in (-1, 1):
                    for j in range(n):
                        a0 = centro + s * (GAP / 2 + (math.pi / 2 - GAP / 2) * j / n)
                        a1 = centro + s * (GAP / 2 + (math.pi / 2 - GAP / 2) * (j + 1) / n)
                        m = 1 - j / n
                        col = tuple(int(c1 * (1 - m * 0.85) + c2 * m * 0.85) for c1, c2 in zip(tema["aro"], comp[i]["color"]))
                        lo, hi = (a0, a1) if a0 < a1 else (a1, a0)
                        L.arco(CX, CY, R, lo, hi + 0.004, col, 46, 0.10 + 0.08 * flash, cairo.LINE_CAP_BUTT)
                        L.arco(CX, CY, R, lo, hi + 0.004, col, 26, 0.22 + 0.15 * flash, cairo.LINE_CAP_BUTT)
                        L.arco(CX, CY, R, lo, hi + 0.004, tuple(min(255, int(v * 1.1 + 40 * flash)) for v in col), 13, 1.0, cairo.LINE_CAP_BUTT)
            # arcos (red + postes) y el dueño detrás
            for lado, i in enumerate((p["a"], p["b"])):
                am = aang + (0 if lado == 0 else math.pi)
                recien = [tsim - e[1] for e in sim["eventos"] if e[0] == "gol" and e[2] != lado and 0 <= tsim - e[1] < 0.6]
                infla = math.sin(math.pi * recien[0] / 0.6) * 18 if recien else 0
                prof = 62 + infla
                c.new_path()
                for q in range(17):
                    a = am - GAP / 2 + GAP * q / 16
                    (c.move_to if q == 0 else c.line_to)(CX + R * math.cos(a), CY + R * math.sin(a))
                for q in range(16, -1, -1):
                    a = am + (-GAP / 2 + GAP * q / 16) * 0.82
                    c.line_to(CX + (R + prof) * math.cos(a), CY + (R + prof) * math.sin(a))
                c.close_path(); L.rgba(comp[i]["color"], 0.22); c.fill_preserve()
                L.rgba(arco_sk["red"], 0.55); c.set_line_width(2.5); c.stroke()
                for q in range(1, 4):
                    rr = R + prof * q / 4
                    L.arco(CX, CY, rr, am - GAP / 2 * (1 - 0.18 * q / 4), am + GAP / 2 * (1 - 0.18 * q / 4), arco_sk["red"], 2, 0.45)
                for q in range(-6, 7, 2):
                    a0 = am + GAP / 2 * q / 6; a1 = am + GAP / 2 * q / 6 * 0.82
                    L.linea(CX + R * math.cos(a0), CY + R * math.sin(a0), CX + (R + prof) * math.cos(a1), CY + (R + prof) * math.sin(a1), arco_sk["red"], 2, 0.45)
                for s in (-1, 1):
                    a = am + s * GAP / 2; px, py = CX + R * math.cos(a), CY + R * math.sin(a)
                    if arco_sk["glow"]:
                        L.brillo(px, py, 34, arco_sk["glow"], 0.6)
                    L.circulo(px, py, 13, arco_sk["poste"], borde=(0, 0, 0), ancho=2.5, borde_a=0.5)
                xx, yy = CX + (R + 116) * math.cos(am), CY + (R + 116) * math.sin(am)
                L.brillo(xx, yy, 85, comp[i]["color"], 0.3)
                M.imagen(L, S(i, 100), xx, yy)
                L.circulo(xx, yy, 50, None, borde=comp[i]["color"], ancho=5)
            # pelota con estela
            if by > 0 and tsim < sim["dur"] + 0.01:
                for j in range(10, 0, -1):
                    kk = k - j
                    if kk < 0:
                        continue
                    ex, ey, _, _ = sim["estados"][kk]; ey += DY
                    if ey < 0 or math.hypot(ex - bx, ey - by) > 260:
                        continue
                    L.circulo(ex, ey, BALL * (1 - j / 12), tema["acento"], 0.20 * (1 - j / 11))
                L.brillo(bx, by, BALL * 2.0, tema["acento"], 0.22)
                M.pelota(L, bx, by, BALL, bang, skin)
            part.dibujar(L, tv)
            # festejo de gol (crece y se desvanece; la cámara no se mueve)
            for e in sim["eventos"]:
                if e[0] == "gol" and 0 <= tsim - e[1] < 0.8:
                    u = (tsim - e[1]) / 0.8
                    quien = (p["a"], p["b"])[e[2]]
                    L.arco(CX, CY, R * (1 + 0.25 * M.suave(u)), 0, 2 * math.pi, comp[quien]["color"], 12, 1 - u)
                    esc = 0.75 + 0.25 * M.suave(min(u * 4, 1))
                    textos.append(((CX, CY - 20), "GOAL!", int(150 * esc), tema["acento"], 10))
                    textos.append(((CX, CY + 105), nombres[quien], M.ajustar(nombres[quien], 72, 2 * R - 80), comp[quien]["color"], 7))
            # textos de abajo: regla, match point, avanza
            reg = RC.REGLAS[p["ronda"]]
            t_ult = [e[1] for e in sim["eventos"] if e[0] == "gol"][-1]
            match_point = max(goles) == reg - 1 and reg > 1 and tsim < t_ult
            if tv >= it["fin_juego"]:
                u = M.suave((tv - it["fin_juego"]) / 0.3)
                txt = f"{nombres[ganador]} {'IS THE CHAMPION' if it['final'] else 'ADVANCES'}"
                textos.append(((W / 2, 1782), txt, int(M.ajustar(txt, 74, W - 80) * (0.8 + 0.2 * u)), comp[ganador]["color"], 7))
            elif tv < 2.2:
                textos.append(((W / 2, 1772), g["titulo"], M.ajustar(g["titulo"], 78, W - 70), (255, 255, 255), 8))
                textos.append(((W / 2, 1858), "PICK YOUR WINNER NOW", 46, tema["acento"], 5))
            elif match_point:
                pul = 0.5 + 0.5 * math.sin(tv * 9)
                c.new_path(); c.rectangle(0, 0, W, H); L.rgba((240, 50, 60), 0.35 + 0.25 * pul); c.set_line_width(26); c.stroke()
                textos.append(((W / 2, 1782), "MATCH POINT", 84, (255, 90, 90), 8))
            else:
                textos.append(((W / 2, 1782), f"FIRST TO {reg} GOAL{'S' if reg > 1 else ''}", 62, (225, 230, 245), 6))
        # ---------- campeón
        if tv >= t_fin:
            u = M.suave((tv - t_fin) / 0.35)
            c.new_path(); c.rectangle(0, 410, W, H - 410); L.rgba((0, 0, 0), 0.78 * u); c.fill()
            for j in range(14):                                     # rayos de luz lentos
                a = j * 2 * math.pi / 14 + (tv - t_fin) * 0.35
                c.new_path(); c.move_to(W / 2, 900)
                c.arc(W / 2, 900, 700, a, a + 0.11); c.close_path(); L.rgba(tema["acento"], 0.07 * u); c.fill()
            L.brillo(W / 2, 900, 330, comp[campeon]["color"], 0.45 * u)
            M.imagen(L, S(campeon, 400), W / 2, 900, escala=0.75 + 0.25 * u)
            L.circulo(W / 2, 900, 200 * (0.75 + 0.25 * u), None, borde=tema["acento"], ancho=12, borde_a=u)
            M.trofeo(L, W / 2, 600, 150 * u + 1, u)
            part.dibujar(L, tv)
            textos.append(((W / 2, 1175), "CHAMPION", 104, tema["acento"], 10))
            textos.append(((W / 2, 1300), nombres[campeon], M.ajustar(nombres[campeon], 132, W - 80), (255, 255, 255), 10))
            ci = g.get("cierre", "WHO WAS YOUR PICK?")
            textos.append(((W / 2, 1440), ci, M.ajustar(ci, 76, W - 80), (255, 255, 255), 7))
            textos.append(((W / 2, 1530), "COMMENT YOUR PICK", 48, tema["acento"], 5))

        im = L.a_pil(); dr = ImageDraw.Draw(im)
        for xy, s, tam, col, borde in textos:
            M.texto(dr, xy, s, tam, col, borde)
        vid.cuadro(im)
    vid.cerrar()
    M.mezclar(out, out / "mudo.mp4", mez.versiones())
    res = {"campeon": comp[campeon]["nombre"], "dur": round(dur, 1),
           "partidos": [[comp[p["a"]]["nombre"], p["sim"]["goles"], comp[p["b"]]["nombre"]] for r in rondas for p in r]}
    json.dump(res, open(out / "resultado.json", "w"), ensure_ascii=False, indent=1)
    print("listo", out / "short.mp4", f"{dur:.1f}s", "campeón", comp[campeon]["nombre"])
    return res


def pantalla_de(it, te):
    """Inversa de tiempo_sim: en qué segundo de pantalla ocurre el evento te de la simulación."""
    sim = it["p"]["sim"]
    t_ult = [e[1] for e in sim["eventos"] if e[0] == "gol"][-1]
    a = t_ult - 0.9
    if te <= a:
        return te
    if te <= t_ult:
        return a + (te - a) / 0.35
    return a + 0.9 / 0.35 + (te - t_ult)


if __name__ == "__main__":
    main(sys.argv[1])
