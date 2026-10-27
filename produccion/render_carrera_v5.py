#!/usr/bin/env python3
"""
CARRERAS V5: misma física y circuitos que render_carrera (v4), dibujado con el motor V2.

Cambios de calidad pedidos ("nada de movimientos raros"):
- 60 fps con interpolación entre estados de física (también en la cámara lenta del photo finish).
- Cámara con resorte críticamente amortiguado: sigue al líder sin saltos ni sacudones (se sacó el temblor).
- Antialias en toda la pista, sombras y brillo suaves, escudos reales en clubes.
Uso: python3 render_carrera_v5.py guiones/carrera_02.json -> salida/<id>_v5/short.mp4 y short_sin_voz.mp4
"""
import json
import math
import sys
from pathlib import Path

import cairocffi as cairo
import numpy as np
from PIL import ImageDraw

import motor as M
import render_carrera as RCar
from motor import W, H, FPS, SR
from render_carrera import PALETAS, ROJO, competidores, drama, simular
from render_fusion import beat, efectos, leer_wav, voces_edge


def elegir_carrera(g, n):
    objetivo = next((i for i, c in enumerate(g["competidores"]) if c["nombre"] == g.get("ganador")), None)
    RCar.DUR_MIN, RCar.DUR_MAX = g.get("duracion", [11, 22])
    puntajes = []
    for s in range(g.get("intentos", 220 if objetivo is not None else 50)):
        sim_s = simular(n, g["circuito"], s, g.get("eliminar", 0))
        if objetivo is not None and (not sim_s["orden"] or sim_s["orden"][0] != objetivo):
            continue
        puntajes.append((drama(sim_s, n, g.get("eliminar", 0)), s))
        if objetivo is not None and len(puntajes) >= 12:
            break
    if not puntajes:
        raise SystemExit(f"ninguna carrera la gana {g.get('ganador')}: subí 'intentos'")
    mejor = max(puntajes)[1]
    return mejor, simular(n, g["circuito"], mejor, g.get("eliminar", 0))


def estado(sim, ts):
    """Posiciones interpoladas en el tiempo de simulación ts (sin cuadros repetidos)."""
    q = ts / sim["dt_estado"]
    k = min(int(q), len(sim["estados"]) - 1); k1 = min(k + 1, len(sim["estados"]) - 1); u = q - int(q) if k1 > k else 0
    a, b = sim["estados"][k], sim["estados"][k1]
    return [(x0 + (x1 - x0) * u, y0 + (y1 - y0) * u, r0 + (r1 - r0) * u) for (x0, y0, r0), (x1, y1, r1) in zip(a, b)], k


def fondo(pal):
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); c = cairo.Context(s)
    g = cairo.LinearGradient(0, 0, 0, H)
    g.add_color_stop_rgb(0, *(v / 255 for v in pal["fondo"])); g.add_color_stop_rgb(0.5, *(v / 255 for v in pal["fondo2"]))
    g.add_color_stop_rgb(1, *(v / 255 for v in pal["fondo"]))
    c.set_source(g); c.paint()
    return s


def main(guion_path, sufijo="_v5"):
    g = json.loads(Path(guion_path).read_text())
    pal = PALETAS[g.get("paleta", "noche")]
    n = len(g["competidores"])
    semilla, sim = elegir_carrera(g, n)
    R = sim["R"]; P = sim["pista"]
    comp = competidores(g, 2 * R)
    esp = {"Vinícius Júnior": "VINÍCIUS", "Zinedine Zidane": "ZIDANE", "Kylian Mbappé": "MBAPPÉ"}
    nombres = [c.get("corto_hud") or (esp.get(c["nombre"], c["nombre"].split()[-1].upper()) if c["tipo"] == "jugador"
               else c.get("corto", c["nombre"]).upper()) for c in comp]
    ganador = sim["orden"][0]; t_gan = sim["llegada"][ganador]
    gap = sim["llegada"][sim["orden"][1]] - t_gan
    foto_final = gap < 0.6
    print(f"semilla {semilla} gana {nombres[ganador]} en {t_gan:.1f}s, gap {gap:.2f}s")

    T_INTRO, T_FIN = 1.7, 3.4
    tiempos = [0.0] * int(T_INTRO * FPS); ts = 0.0
    while ts < t_gan + 0.35:
        lento = foto_final and t_gan - 0.9 < ts < t_gan + 0.3
        ts += (0.3 if lento else 1.0) / FPS; tiempos.append(ts)
    f_gan = next(k for k, x in enumerate(tiempos) if x >= t_gan); t_video_gan = f_gan / FPS
    tiempos += [min(ts + (k + 1) / FPS, sim["t_fin"]) for k in range(int(T_FIN * FPS))]
    nf = len(tiempos)
    tarr = np.array(tiempos)

    def t_video(t_sim):
        k = int(np.searchsorted(tarr, t_sim)); return min(k, nf - 1) / FPS

    popups, sonidos, voz, ult_voz = [], [("whoosh", T_INTRO - 0.25)], [(0.15, g["voz_intro"])], 0.0
    for tipo, t, i in sim["eventos"]:
        tv = t_video(t)
        if tipo == "lider" and t < t_gan - 1.2:
            popups.append((tv, f"{nombres[i]} TAKES THE LEAD!", comp[i]["color"])); sonidos.append(("tick2", tv))
            if tv - ult_voz > 2.2:
                voz.append((tv, f"{comp[i]['voz']} takes the lead!")); ult_voz = tv
        elif tipo == "fuera":
            popups.append((tv, f"{nombres[i]} IS OUT!", ROJO)); sonidos.append(("boom", tv))
            if tv - ult_voz > 1.2:
                voz.append((tv, f"{comp[i]['voz']} is out!")); ult_voz = tv
        elif tipo == "golpe":
            sonidos.append(("tick", tv))
        elif tipo == "boost":
            sonidos.append(("whoosh", tv))
        elif tipo == "portal":
            popups.append((tv, f"{nombres[i]} SENT BACK!", (190, 110, 255))); sonidos += [("whoosh", tv), ("boom", tv + 0.05)]
    voz = [v for v in voz if v[0] < t_video_gan - 1.6]
    if foto_final:
        voz.append((t_video_gan - 1.5, "Photo finish!"))
    voz.append((t_video_gan + 0.15, f"{comp[ganador]['voz']} wins it!"))
    voz.append((t_video_gan + 1.7, "Did your pick win?"))
    sonidos += [("riser", t_video_gan - 1.0), ("boom", t_video_gan), ("ding", t_video_gan + 0.05)]

    out = M.ROOT / "salida" / (g["id"] + sufijo); out.mkdir(parents=True, exist_ok=True)
    base = fondo(pal)
    bola = [M.pil_a_cairo(c["img"]) for c in comp]
    mini = [M.pil_a_cairo(c["img"].resize((int(min((W - 120) / n - 14, 96)),) * 2, M.Image.LANCZOS)) for c in comp]
    mini_g = [M.pil_a_cairo(M.gris(c["img"].resize((int(min((W - 120) / n - 14, 96)),) * 2, M.Image.LANCZOS), 0.5)) for c in comp]
    gran = M.pil_a_cairo(comp[ganador]["img"].resize((360, 360), M.Image.LANCZOS))
    part = M.Particulas(8); part.confeti(t_video_gan + 0.05)
    cam = M.Resorte(-300, 3.2)
    vid = M.Video(out / "mudo.mp4")
    for f in range(nf):
        tv = f / FPS; ts = tiempos[f]
        est, k = estado(sim, ts)
        vivos = [i for i in range(n) if not (i in sim["fuera"] and sim["fuera"][i] <= ts)]
        llegados = [i for i in vivos if i in sim["llegada"] and sim["llegada"][i] <= ts]
        corriendo = [i for i in vivos if i not in llegados]
        obj = min(max(est[i][1] for i in corriendo) - 900, P.meta - H + 520) if corriendo else P.meta - H + 520
        cy = cam.paso(max(obj, -300), 1 / FPS) if tv > T_INTRO else cam.paso(-300, 1 / FPS)
        L = M.Lienzo(base); c = L.c; textos = []
        # líneas de fondo con paralaje suave (sensación de velocidad sin mover nada raro)
        for yy in range(-int(cy * 0.4) % 160 - 160, H, 160):
            L.linea(0, yy, W, yy, (255, 255, 255), 2, 0.035)
        # eliminación
        for y0 in (P.controles[-g.get("eliminar", 0):] if g.get("eliminar", 0) else []):
            yy = y0 - cy
            if -40 < yy < H:
                L.linea(50, yy, W - 50, yy, ROJO, 6, 0.55)
                textos.append(((W - 70, yy - 26), "ELIMINATION", 30, ROJO, 5, "rm"))
        # pista
        for a, b, gr in P.segs:
            if max(a[1], b[1]) - cy > -60 and min(a[1], b[1]) - cy < H + 60:
                L.linea(a[0], a[1] - cy, b[0], b[1] - cy, pal["pista"], 2 * gr + 16, 0.16)
                L.linea(a[0], a[1] - cy, b[0], b[1] - cy, pal["pista"], 2 * gr, 1.0)
        for x, y, r in P.clavos:
            if -40 < y - cy < H + 40:
                L.circulo(x + 3, y - cy + 5, r, (0, 0, 0), 0.25)
                L.circulo(x, y - cy, r, pal["clavo"])
                L.circulo(x - r * 0.3, y - cy - r * 0.3, r * 0.35, (255, 255, 255), 0.5)
        for px, py, pr, _ in P.portales:
            if -120 < py - cy < H + 120:
                L.brillo(px, py - cy, pr * 1.3, (190, 110, 255), 0.35)
                for j in range(5):
                    rr = pr * (1 - j * 0.17); a0 = math.radians(tv * 220 + j * 40)
                    L.arco(px, py - cy, rr, a0, a0 + 4.3, (190, 110, 255), 8, 0.9 - j * 0.14)
                textos.append(((px, py - cy + pr + 26), "BACK -700", 26, (210, 160, 255), 4, "mm"))
        for a, b in P.tramp:
            if max(a[1], b[1]) - cy > -50 and min(a[1], b[1]) - cy < H + 50:
                L.linea(a[0], a[1] - cy, b[0], b[1] - cy, (80, 255, 170), 30, 0.25)
                L.linea(a[0], a[1] - cy, b[0], b[1] - cy, (80, 255, 170), 22)
                L.linea(a[0], a[1] - cy, b[0], b[1] - cy, (225, 255, 238), 7)
        for pb, A, w, fase in P.pendulos:
            ang = A * math.sin(w * ts + fase); px, py = pb.position
            if -300 < py - cy < H + 300:
                ex, ey = px - 250 * math.sin(ang), py + 250 * math.cos(ang)
                L.linea(px, py - cy, ex, ey - cy, pal["acento"], 24)
                L.circulo(ex + 4, ey - cy + 6, 34, (0, 0, 0), 0.25)
                L.circulo(ex, ey - cy, 34, (255, 90, 90), borde=(255, 255, 255), ancho=5)
                L.circulo(px, py - cy, 14, (255, 255, 255))
        for x, y in P.rebot:
            if -80 < y - cy < H + 80:
                cerca = any(math.hypot(est[i][0] - x, est[i][1] - y) < R + 70 for i in vivos)
                if cerca:
                    L.brillo(x, y - cy, 110, pal["acento"], 0.5)
                L.circulo(x, y - cy, 58, pal["acento"] if cerca else pal["clavo"], borde=(255, 255, 255), ancho=6)
                L.circulo(x, y - cy, 30, (255, 255, 255), 0.25)
        for y0, y1, s in P.boost:
            if -60 < y0 - cy < H + 60:
                for j in range(4):
                    yy = y0 + 20 + j * 45 - cy; xc = W / 2 + s * 120
                    fz = (tv * 3 + j * 0.25) % 1
                    c.new_path()
                    for px_, py_ in ((xc - 60, yy), (xc, yy + 34), (xc + 60, yy), (xc + 60, yy + 16), (xc, yy + 50), (xc - 60, yy + 16)):
                        c.line_to(px_, py_)
                    c.close_path(); L.rgba(pal["acento"], 0.35 + 0.6 * fz); c.fill()
        for b, largo, brazos in P.giros:
            ang = b.angular_velocity * ts; px, py = b.position
            if -largo < py - cy < H + largo:
                for j in range(brazos):
                    a = ang + math.pi * j / brazos
                    cc, ss = math.cos(a) * largo, math.sin(a) * largo
                    L.linea(px - cc, py - ss - cy, px + cc, py + ss - cy, pal["acento"], 24)
                L.circulo(px, py - cy, 18, (255, 255, 255))
        my = P.meta - cy
        if -60 < my < H + 60:
            for x in range(40, W - 40, 40):
                for fila in range(2):
                    c.rectangle(x, my + fila * 20, 20, 20); L.rgba((255, 255, 255) if ((x // 40) + fila) % 2 else (10, 10, 10)); c.fill()
            textos.append(((W - 60, my - 34), "FINISH", 44, (255, 255, 255), 6, "rm"))
        # estelas y pelotas
        lider_i = max(corriendo, key=lambda i: est[i][1]) if corriendo else None
        for i in vivos:
            for j in range(1, 7):
                kk = max(k - j * 2, 0)
                ex, ey, _ = sim["estados"][kk][i]
                if -R * 2 < ey - cy < H + R * 2:
                    L.circulo(ex, ey - cy, R * (1 - j / 8), comp[i]["color"], 0.16 * (1 - j / 7))
        for i in vivos:
            x, y, a = est[i]
            if -R * 2 < y - cy < H + R * 2:
                L.circulo(x + R * 0.12, y - cy + R * 0.22, R, (0, 0, 0), 0.3)
                M.imagen(L, bola[i], x, y - cy, ang=0 if comp[i]["tipo"] == "pais" else a * 0.35)
                L.circulo(x, y - cy, R, None, borde=comp[i]["color"], ancho=7)
                if i == lider_i:
                    cx_, cy_ = x, y - cy - R - 30
                    c.new_path()
                    for px_, py_ in ((cx_ - 34, cy_ + 14), (cx_ - 34, cy_ - 16), (cx_ - 17, cy_), (cx_, cy_ - 22), (cx_ + 17, cy_), (cx_ + 34, cy_ - 16), (cx_ + 34, cy_ + 14)):
                        c.line_to(px_, py_)
                    c.close_path(); L.rgba((255, 210, 63)); c.fill_preserve(); L.rgba((120, 80, 0)); c.set_line_width(3); c.stroke()
                textos.append(((x, y - cy + R + 24), nombres[i], 34, comp[i]["color"], 6, "mm"))
        for i, tf in sim["fuera"].items():
            if 0 <= ts - tf < 1.0:
                ke = min(int(tf / sim["dt_estado"]), len(sim["estados"]) - 1)
                x, y, _ = sim["estados"][ke][i]; u = (ts - tf) / 1.0
                L.circulo(x, y - cy, R * (1 + u), None, borde=ROJO, ancho=10, borde_a=1 - u)
                textos.append(((x, y - cy), "OUT", 60, ROJO, 8, "mm"))
        n_mundo = len(textos)
        # HUD superior
        L.rect_redondo(16, 14, W - 32, 320, 30, (5, 7, 16), 0.86)
        textos.append(((W / 2, 64), g["evento"], M.ajustar(g["evento"], 52, W - 120), pal["acento"], 6, "mm"))
        textos.append(((W / 2, 138), g["titulo"], M.ajustar(g["titulo"], 84, W - 90), (255, 255, 255), 9, "mm"))

        def clave(i):
            if i in sim["llegada"] and sim["llegada"][i] <= ts:
                return -1e9 + sim["llegada"][i]
            if i in sim["fuera"] and sim["fuera"][i] <= ts:
                return 1e9 - sim["fuera"][i]
            return -est[i][1]
        orden = sorted(range(n), key=clave); paso = (W - 120) / n
        for pos, i in enumerate(orden):
            x0 = 60 + paso * pos + paso / 2
            out_ = i in sim["fuera"] and sim["fuera"][i] <= ts
            M.imagen(L, mini_g[i] if out_ else mini[i], x0, 240)
            textos.append(((x0, 310), "OUT" if out_ else f"{pos + 1}", 30, ROJO if out_ else (255, 255, 255), 5, "mm"))
        if tv < T_INTRO + 0.3:
            L.rect_redondo(30, H * 0.53 - 170, W - 60, 340, 36, (0, 0, 0), 0.62)
            textos.append(((W / 2, H * 0.53 - 75), g["gancho"], M.ajustar(g["gancho"], 104, W - 100), (255, 255, 255), 12, "mm"))
            textos.append(((W / 2, H * 0.53 + 60), "PICK ONE NOW", 92, pal["acento"], 10, "mm"))
        for t0, s, col in popups:
            if 0 <= tv - t0 < 1.1 and tv < t_video_gan - 0.2:
                u = M.suave((tv - t0) / 0.15)
                textos.append(((W / 2, H * 0.80), s, int(M.ajustar(s, 84, W - 100) * (0.75 + 0.25 * u)), col, 10, "mm"))
                break
        if foto_final and t_video_gan - 2.2 < tv < t_video_gan:
            c.new_path(); c.rectangle(0, 0, W, H); L.rgba((240, 40, 40), 0.55); c.set_line_width(24); c.stroke()
            if tv > t_video_gan - 1.6:
                textos.append(((W / 2, H * 0.80), "PHOTO FINISH!", 100, ROJO, 12, "mm"))
        if tv >= t_video_gan:
            u = M.suave((tv - t_video_gan) / 0.3)
            L.rect_redondo(30, H * 0.5 - 340, W - 60, 680, 40, (0, 0, 0), 0.75 * u)
            L.brillo(W / 2, H * 0.5 - 120, 260, comp[ganador]["color"], 0.4 * u)
            M.imagen(L, gran, W / 2, H * 0.5 - 120, escala=0.75 + 0.25 * u)
            L.circulo(W / 2, H * 0.5 - 120, 180 * (0.75 + 0.25 * u), None, borde=pal["acento"], ancho=12, borde_a=u)
            part.dibujar(L, tv)
            s = f"{nombres[ganador]} WINS!"
            textos.append(((W / 2, H * 0.5 + 150), s, M.ajustar(s, 130, W - 100), pal["acento"], 12, "mm"))
            ci = g.get("cierre", "DID YOUR PICK WIN?")
            textos.append(((W / 2, H * 0.5 + 265), ci, M.ajustar(ci, 70, W - 120), (255, 255, 255), 8, "mm"))
        if tv >= t_video_gan:                    # nada del mundo por encima de la tarjeta del ganador
            textos = [t_ for k_, t_ in enumerate(textos) if k_ >= n_mundo or not (H * 0.5 - 360 < t_[0][1] < H * 0.5 + 360)]
        im = L.a_pil(); dr = ImageDraw.Draw(im)
        for xy, s, tam, col, borde, anc in textos:
            M.texto(dr, xy, s, tam, col, borde, anchor=anc)
        vid.cuadro(im)
    vid.cerrar()

    # audio: mismos efectos y relator que v4 (voces ya generadas), con dos versiones
    dur = nf / FPS
    rng = np.random.default_rng(3)
    mix = np.zeros(int(dur * SR), np.float32); fx = efectos(n)

    def add(s, sig, vol=1.0):
        i = int(s * SR); j = min(len(mix), i + len(sig))
        if 0 <= i < len(mix):
            mix[i:j] += vol * sig[: j - i]
    ult = {}
    for nombre_fx, s in sorted(sonidos, key=lambda x: x[1]):
        if nombre_fx in ("tick", "whoosh") and s - ult.get(nombre_fx, -9) < (0.09 if nombre_fx == "tick" else 0.5):
            continue
        ult[nombre_fx] = s
        add(s, fx[nombre_fx], 0.55 if nombre_fx == "tick" else 1.0)
    if foto_final:
        for kk in range(6):
            add(t_video_gan - 2.0 + kk * 0.38, fx["latido"], 1.0)
    nz = np.convolve(rng.standard_normal(int(2.4 * SR)).astype(np.float32), np.ones(40) / 40, mode="same")
    env = np.concatenate([np.linspace(0.2, 1, int(0.4 * SR)), np.ones(int(1.0 * SR)), np.linspace(1, 0, int(1.0 * SR))])[: len(nz)]
    add(t_video_gan - 0.05, nz * env, 2.2)
    solo_fx = mix.copy()
    mix = mix + beat(dur)[: len(mix)] * 0.8
    rutas = voces_edge([l for _, l in voz], out)
    dv = np.ones_like(mix)
    for (s, _), r in zip(voz, rutas):
        x = leer_wav(r); i = int(s * SR); j = min(len(mix), i + len(x))
        if i < len(mix):
            dv[i:j] = np.minimum(dv[i:j], 0.45); mix[i:j] += 1.05 * x[: j - i]
    M.mezclar(out, out / "mudo.mp4", {"short.mp4": np.tanh(mix * dv * 1.3) * 0.9, "short_sin_voz.mp4": np.tanh(solo_fx * 1.1) * 0.6})
    res = {"semilla": semilla, "ganador": comp[ganador]["nombre"], "orden": [comp[i]["nombre"] for i in sim["orden"]],
           "eliminados": [comp[i]["nombre"] for i in sim["fuera"]], "dur": round(dur, 1), "photo_finish": foto_final}
    json.dump(res, open(out / "resultado.json", "w"), ensure_ascii=False, indent=1)
    print("listo", out / "short.mp4", f"{dur:.1f}s", res["ganador"])
    return res


if __name__ == "__main__":
    main(sys.argv[1])
