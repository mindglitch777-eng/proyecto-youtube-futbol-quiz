#!/usr/bin/env python3
"""
TROPHY RACE: réplica de Rival Stats ("Messi vs Ronaldo: Ultimate Trophy Battle", 4,2 M; su primer 1M llegó en 5 días).
Año por año, cada trofeo vuela desde el año hasta la columna del jugador y se apila; contador grande, "takes the lead"
cuando cambia el líder, total final y pregunta de debate.

Solo datos verificados escritos en el guion (campo "trofeos": [[año, quién, tipo], ...]).
Tipos: balon (Ballon d'Or), ucl (Champions League), mundial, copa (Copa América), euro, nations, finalissima.
Uso: python3 render_trophy_race.py guiones/trofeos_01.json -> salida/<id>/short.mp4 y short_sin_musica.mp4
"""
import json
import math
import sys
from pathlib import Path

import cairocffi as cairo
from PIL import ImageDraw

import motor as M
from motor import W, H, FPS
from render_carrera import competidores

ETIQUETA = {"balon": "BALLON D'OR", "ucl": "CHAMPIONS LEAGUE", "mundial": "WORLD CUP", "copa": "COPA AMÉRICA",
            "euro": "EURO", "nations": "NATIONS LEAGUE", "finalissima": "FINALISSIMA"}
ROW = 58
BASE_Y = 1800


def icono(L, tipo, x, y, h, a=1.0):
    """Ícono vectorial del trofeo (sin logos de terceros)."""
    if tipo == "balon":
        M.pelota(L, x, y, h * 0.42, 0.3, "dorada")
    elif tipo == "ucl":                                   # copa plateada de orejas grandes
        c = L.c
        for s in (-1, 1):
            c.new_path(); c.save(); c.translate(x + s * h * 0.28, y - h * 0.08); c.scale(0.55, 1)
            c.arc(0, 0, h * 0.3, 0, 2 * math.pi); c.restore()
            L.rgba((215, 220, 230), a); c.set_line_width(h * 0.08); c.stroke()
        _copa(L, x, y, h, ((0.55, 0.57, 0.62), (0.95, 0.96, 1.0), (0.6, 0.62, 0.68)), a)
    elif tipo == "mundial":
        M.trofeo(L, x, y, h, a)
    else:
        _copa(L, x, y, h * 0.9, ((0.55, 0.57, 0.62), (0.95, 0.96, 1.0), (0.6, 0.62, 0.68)), a)


def _copa(L, x, y, h, cols, a):
    c = L.c; w = h * 0.5
    g = cairo.LinearGradient(x - w / 2, 0, x + w / 2, 0)
    for st, col in zip((0, 0.5, 1), cols):
        g.add_color_stop_rgba(st, *col, a)
    top = y - h * 0.45
    c.new_path(); c.move_to(x - w / 2, top); c.line_to(x + w / 2, top)
    c.curve_to(x + w / 2, top + h * 0.45, x + w * 0.1, top + h * 0.55, x + w * 0.08, top + h * 0.62)
    c.line_to(x + w * 0.3, top + h * 0.9); c.line_to(x - w * 0.3, top + h * 0.9); c.line_to(x - w * 0.08, top + h * 0.62)
    c.curve_to(x - w * 0.1, top + h * 0.55, x - w / 2, top + h * 0.45, x - w / 2, top)
    c.close_path(); c.set_source(g); c.fill()


def main(guion_path):
    g = json.loads(Path(guion_path).read_text())
    comp = competidores(g, 300)
    nombres = [c.get("corto_hud") or c["nombre"].split()[-1].upper() for c in comp]
    idx = {c["nombre"]: i for i, c in enumerate(comp)}
    anios = list(range(g["desde"], g["hasta"] + 1))
    PASO = g.get("segundos_por_anio", 1.45)
    T0 = 1.2
    t_fin = T0 + len(anios) * PASO + 0.4
    dur = t_fin + 3.8
    out = M.ROOT / "salida" / g["id"]; out.mkdir(parents=True, exist_ok=True)
    base = M.superficie_fondo((6, 8, 18), (26, 34, 70), cy=0.5)
    cara = [M.pil_a_cairo(c["img"].resize((150, 150), M.Image.LANCZOS)) for c in comp]
    gran = None
    xs = [W * 0.27, W * 0.73]

    # cada trofeo: (t_aparece, jugador, tipo, año, posición en la pila)
    items, pila = [], [0, 0]
    for k, an in enumerate(anios):
        del_anio = [t for t in g["trofeos"] if t[0] == an]
        for j, (_, quien, tipo) in enumerate(del_anio):
            i = idx[quien]
            items.append(dict(t=T0 + k * PASO + 0.25 + j * 0.32, i=i, tipo=tipo, anio=an, n=pila[i]))
            pila[i] += 1
    total = pila[:]
    ganador = 0 if total[0] > total[1] else 1
    # líder en el tiempo y cambios
    mez = M.Mezcla(dur); part = M.Particulas(4)
    tick = M.pluck(1760, 0.06, 0.12)
    for k in range(len(anios)):
        mez.add(T0 + k * PASO, tick)
    cuenta = [0, 0]; lider = None; avisos = []
    for it in items:
        cuenta[it["i"]] += 1
        mez.add(it["t"] + 0.38, M.golpe(), 0.9); mez.add(it["t"] + 0.38, M.ding(0.5), 0.5)
        nuevo = 0 if cuenta[0] > cuenta[1] else 1 if cuenta[1] > cuenta[0] else None
        if nuevo is not None and nuevo != lider:
            if lider is not None or cuenta[nuevo] >= 2:
                avisos.append((it["t"] + 0.4, nuevo, "TAKES THE LEAD" if lider is not None else "LEADS"))
                mez.add(it["t"] + 0.4, M.whoosh(), 0.6)
            lider = nuevo
        elif nuevo is None and lider is not None:
            avisos.append((it["t"] + 0.4, None, "LEVEL!")); lider = None
        x, y = xs[it["i"]], BASE_Y - it["n"] * ROW
        part.chispas(it["t"] + 0.38, x, y, comp[it["i"]]["color"], 16, v=(150, 420), vida=0.6)
    mez.add(t_fin, M.boom()); mez.add(t_fin, M.tribuna()); mez.add(t_fin + 0.1, M.ding())
    part.confeti(t_fin + 0.1)

    vid = M.Video(out / "mudo.mp4")
    for f in range(int(dur * FPS)):
        tv = f / FPS
        L = M.Lienzo(base); c = L.c; textos = []
        k = int(min(max((tv - T0) / PASO, 0), len(anios) - 1))
        textos.append(((W / 2, 80), g["titulo"], M.ajustar(g["titulo"], 82, W - 70), (255, 255, 255), 8))
        textos.append(((W / 2, 160), g["subtitulo"], M.ajustar(g["subtitulo"], 38, W - 80), (255, 214, 80), 4))
        # año (cambia con un pequeño pop de escala, sin mover cámara)
        ua = M.suave(((tv - T0) - k * PASO) / 0.18) if tv >= T0 else 1
        textos.append(((W / 2, 300), str(anios[k]), int(120 * (0.85 + 0.15 * ua)), (255, 214, 80), 9))
        vis = [x for x in items if x["t"] <= tv]
        cnt = [sum(1 for x in vis if x["i"] == i and tv >= x["t"] + 0.38) for i in (0, 1)]
        for i in (0, 1):
            x = xs[i]
            pulso = max([0.0] + [1 - (tv - x2["t"] - 0.38) / 0.35 for x2 in vis if x2["i"] == i and 0 <= tv - x2["t"] - 0.38 < 0.35])
            L.brillo(x, 470, 130, comp[i]["color"], 0.3 + 0.3 * pulso)
            M.imagen(L, cara[i], x, 470)
            L.circulo(x, 470, 75, None, borde=comp[i]["color"], ancho=7)
            textos.append(((x, 588), nombres[i], M.ajustar(nombres[i], 50, 420), comp[i]["color"], 6))
            textos.append(((x, 690), str(cnt[i]), int(110 * (1 + 0.18 * pulso)), (255, 255, 255), 9))
            # estante
            L.rect_redondo(x - 215, 760, 430, BASE_Y - 760 + 40, 22, (255, 255, 255), 0.04, borde=None)
            L.linea(x - 205, BASE_Y + 34, x + 205, BASE_Y + 34, comp[i]["color"], 5, 0.8)
        for it in vis:
            u = M.suave((tv - it["t"]) / 0.38)
            x1, y1 = xs[it["i"]], BASE_Y - it["n"] * ROW
            x0, y0 = W / 2, 300
            x = x0 + (x1 - x0) * u; y = y0 + (y1 - y0) * u - math.sin(math.pi * u) * 120
            col = comp[it["i"]]["color"]
            if u >= 1 and tv < t_fin:
                L.rect_redondo(x1 - 205, y1 - 25, 410, 50, 14, col, 0.16)
                icono(L, it["tipo"], x1 - 172, y1, 44)
                textos.append(((x1 - 140, y1 + 1), f"{it['anio']}  {ETIQUETA[it['tipo']]}", M.ajustar(f"{it['anio']}  {ETIQUETA[it['tipo']]}", 30, 330), (240, 242, 250), 3, "lm"))
            elif u < 1:
                L.brillo(x, y, 60, col, 0.4)
                icono(L, it["tipo"], x, y, 70 - 26 * u)
        part.dibujar(L, tv)
        for ta, quien, msg in avisos:
            if 0 <= tv - ta < 1.1:
                u = tv - ta
                a = min(1, u / 0.15) * min(1, (1.1 - u) / 0.25)
                s = f"{nombres[quien]} {msg}" if quien is not None else msg
                L.rect_redondo(90, 1040 - 60, W - 180, 120, 30, (0, 0, 0), 0.6 * a)
                textos.append(((W / 2, 1040), s, M.ajustar(s, 80, W - 220), comp[quien]["color"] if quien is not None else (255, 255, 255), 8, "mm", a))
        if tv >= t_fin:
            u = M.suave((tv - t_fin) / 0.35)
            c.new_path(); c.rectangle(0, 0, W, H); L.rgba((4, 6, 14), 0.94 * u); c.fill()
            if gran is None:
                gran = M.pil_a_cairo(comp[ganador]["img"].resize((360, 360), M.Image.LANCZOS))
            L.brillo(W / 2, 760, 300, comp[ganador]["color"], 0.45 * u)
            M.imagen(L, gran, W / 2, 760, escala=0.75 + 0.25 * u)
            L.circulo(W / 2, 760, 180 * (0.75 + 0.25 * u), None, borde=(255, 214, 80), ancho=12, borde_a=u)
            part.dibujar(L, tv)
            textos.append(((W / 2, 1010), f"{nombres[ganador]} {total[ganador]}", 120, (255, 214, 80), 10))
            textos.append(((W / 2, 1130), f"{nombres[1 - ganador]} {total[1 - ganador]}", 80, (230, 232, 245), 8))
            textos.append(((W / 2, 1270), g["cierre"], M.ajustar(g["cierre"], 80, W - 80), (255, 255, 255), 8))
            textos.append(((W / 2, 1370), g.get("nota", ""), M.ajustar(g.get("nota", ""), 36, W - 100), (180, 185, 205), 3))
            textos.append(((W / 2, 1460), "COMMENT YOUR ANSWER", 50, (255, 214, 80), 5))
        im = L.a_pil(); dr = ImageDraw.Draw(im, "RGBA")
        for tx in textos:
            xy, s, tam, col, borde = tx[:5]
            anchor = tx[5] if len(tx) > 5 else "mm"
            alpha = tx[6] if len(tx) > 6 else 1
            M.texto(dr, xy, s, tam, tuple(col[:3]) + (int(255 * alpha),), borde, (0, 0, 0, int(255 * alpha)), anchor)
        vid.cuadro(im)
    vid.cerrar()
    M.mezclar(out, out / "mudo.mp4", mez.versiones(beat_vol=0.55))
    res = {"total": dict(zip([c["nombre"] for c in comp], total)), "dur": round(dur, 1)}
    json.dump(res, open(out / "resultado.json", "w"), ensure_ascii=False, indent=1)
    print("listo", out / "short.mp4", res)
    return res


if __name__ == "__main__":
    main(sys.argv[1])
