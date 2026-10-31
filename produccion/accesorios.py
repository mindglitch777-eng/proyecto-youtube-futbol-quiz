#!/usr/bin/env python3
"""
Accesorios dibujados por código (cairo, con degradés y brillos) ubicados con los 68 puntos de la cara.
capa(nombre, geo, tam) → PIL RGBA del tamaño `tam`, con el accesorio en el lugar justo.
geo: dict(p=68 puntos, A=ancho de cara, cx, cejas, cyk, rx, ry, dy=offset vertical del lienzo)
"""
import math
import random

import cairocffi as cairo
import numpy as np
from PIL import Image

ACCESORIOS = {
    # nombre: (tipo, es_pelo)
    "anteojos": "cara", "anteojos_oro": "cara", "cadena": "pecho", "cadena_doble": "pecho", "corona": "cabeza", "aros": "orejas",
    "pelo_verde": "pelo", "pelo_azul": "pelo", "pelo_rubio": "pelo", "pelo_rojo": "pelo",
    "payaso": "pelo", "peluca_rosa": "pelo", "afro": "pelo", "mohawk": "pelo",
}


def a_pil(surf):
    w, h = surf.get_width(), surf.get_height()
    buf = np.frombuffer(surf.get_data(), np.uint8).reshape(h, surf.get_stride() // 4, 4)[:, :w]
    a = buf[..., 3:4].astype(np.float32)
    rgb = np.where(a > 0, buf[..., 2::-1].astype(np.float32) * 255 / np.maximum(a, 1), 0)   # BGRA premultiplicado → RGB
    return Image.fromarray(np.dstack([np.clip(rgb, 0, 255), a]).astype(np.uint8), "RGBA")


def grad_lineal(x0, y0, x1, y1, paradas):
    g = cairo.LinearGradient(x0, y0, x1, y1)
    for o, c in paradas:
        g.add_color_stop_rgba(o, *[v / 255 for v in c[:3]], (c[3] / 255) if len(c) > 3 else 1)
    return g


def grad_radial(cx, cy, r0, r1, paradas, fx=None, fy=None):
    g = cairo.RadialGradient(fx if fx is not None else cx, fy if fy is not None else cy, r0, cx, cy, r1)
    for o, c in paradas:
        g.add_color_stop_rgba(o, *[v / 255 for v in c[:3]], (c[3] / 255) if len(c) > 3 else 1)
    return g


def oro(ctx, x, y, r):
    return grad_radial(x, y, 0, r, [(0, (255, 248, 190)), (0.45, (250, 200, 60)), (0.8, (205, 140, 20)), (1, (140, 85, 5))], x - r * 0.3, y - r * 0.3)


# ------------------------------------------------------------------ piezas
def anteojos(ctx, g, dorado=False):
    p, A = g["p"], g["A"]
    oi, od = p[36:42].mean(0), p[42:48].mean(0)
    ang = math.atan2(od[1] - oi[1], od[0] - oi[0])
    c = (oi + od) / 2
    ctx.save(); ctx.translate(*c); ctx.rotate(ang)
    sep = np.linalg.norm(od - oi) / 2
    w, h = A * 0.33, A * 0.2
    for s in (-1, 1):
        x = s * sep
        ctx.new_path()
        ctx.move_to(x - w / 2, -h * 0.5); ctx.line_to(x + w / 2, -h * 0.55)
        ctx.curve_to(x + w / 2 + w * 0.05, h * 0.2, x + w * 0.3, h * 0.62, x, h * 0.6)
        ctx.curve_to(x - w * 0.3, h * 0.62, x - w / 2 - w * 0.05, h * 0.2, x - w / 2, -h * 0.5)
        ctx.close_path()
        ctx.set_source(grad_lineal(x, -h / 2, x, h * 0.6, [(0, (60, 60, 70)), (0.5, (15, 15, 20)), (1, (35, 35, 45))]))
        ctx.fill_preserve()
        ctx.set_source(oro(ctx, x, -h * 0.4, w) if dorado else grad_lineal(0, -h, 0, h, [(0, (40, 40, 40)), (1, (5, 5, 5))]))
        ctx.set_line_width(A * 0.035); ctx.stroke()
        ctx.save(); ctx.move_to(x - w * 0.3, -h * 0.35); ctx.line_to(x - w * 0.05, -h * 0.4); ctx.line_to(x - w * 0.32, h * 0.35)   # reflejo
        ctx.line_to(x - w * 0.42, h * 0.3); ctx.close_path(); ctx.set_source_rgba(1, 1, 1, 0.28); ctx.fill(); ctx.restore()
    ctx.set_line_width(A * 0.04); ctx.move_to(-sep + w / 2, -h * 0.45); ctx.curve_to(-w * 0.1, -h * 0.75, w * 0.1, -h * 0.75, sep - w / 2, -h * 0.45)
    ctx.set_source(oro(ctx, 0, -h * 0.6, w) if dorado else grad_lineal(0, -h, 0, h, [(0, (40, 40, 40)), (1, (5, 5, 5))])); ctx.stroke()
    for s in (-1, 1):                                                          # patillas hacia las orejas
        ctx.move_to(s * (sep + w / 2), -h * 0.5); ctx.line_to(s * (sep + w / 2 + A * 0.12), -h * 0.45); ctx.stroke()
    ctx.restore()


def cadena(ctx, g, doble=False):
    p, A, cx = g["p"], g["A"], g["cx"]
    y0 = p[8, 1] + A * 0.42
    for k, (rx, ry, gros) in enumerate([(A * 0.62, A * 0.36, 1.0)] + ([(A * 0.72, A * 0.52, 0.8)] if doble else [])):
        n = 18
        for i in range(n + 1):
            t = math.pi * (0.08 + 0.84 * i / n)
            x, y = cx + rx * math.cos(t), y0 - ry * 0.25 + ry * math.sin(t)
            tang = math.atan2(ry * math.cos(t), -rx * math.sin(t))
            lw, lh = A * 0.14 * gros, A * 0.09 * gros
            ctx.save(); ctx.translate(x, y); ctx.rotate(tang + (0.5 if i % 2 else -0.5))
            ctx.scale(1, lh / lw); ctx.new_path(); ctx.arc(0, 0, lw / 2, 0, 2 * math.pi); ctx.restore()
            ctx.set_source(oro(ctx, x, y, lw * 0.7)); ctx.fill_preserve()
            ctx.set_source_rgba(0.45, 0.28, 0.0, 0.9); ctx.set_line_width(A * 0.008); ctx.stroke()
    # dije
    y = y0 + A * 0.36 * 0.75
    ctx.save(); ctx.translate(cx, y + A * 0.1)
    ctx.new_path(); ctx.move_to(0, -A * 0.12); ctx.line_to(A * 0.1, 0); ctx.line_to(0, A * 0.14); ctx.line_to(-A * 0.1, 0); ctx.close_path()
    ctx.set_source(grad_radial(-A * 0.03, -A * 0.04, 0, A * 0.16, [(0, (255, 255, 255)), (0.4, (170, 230, 255)), (1, (40, 120, 220))])); ctx.fill_preserve()
    ctx.set_source_rgba(1, 1, 1, 0.9); ctx.set_line_width(A * 0.01); ctx.stroke(); ctx.restore()


def corona(ctx, g):
    A, cx, cyk, ry = g["A"], g["cx"], g["cyk"], g["ry"]
    top = cyk - ry * 0.92; w = A * 0.92; h = A * 0.42
    ctx.new_path(); ctx.move_to(cx - w / 2, top + h * 0.3)
    for i, (dx, dy) in enumerate([(-0.5, -0.65), (-0.25, -0.15), (0, -0.85), (0.25, -0.15), (0.5, -0.65)]):
        ctx.line_to(cx + dx * w, top + dy * h)
    ctx.line_to(cx + w / 2, top + h * 0.3); ctx.close_path()
    ctx.set_source(grad_lineal(cx, top - h, cx, top + h * 0.3, [(0, (255, 245, 170)), (0.5, (245, 190, 40)), (1, (170, 105, 10))])); ctx.fill_preserve()
    ctx.set_source_rgba(0.45, 0.27, 0, 1); ctx.set_line_width(A * 0.018); ctx.stroke()
    for j, col in enumerate([(230, 20, 50), (30, 110, 255), (230, 20, 50)]):
        x = cx + (j - 1) * w * 0.3; y = top + h * 0.05
        ctx.new_path(); ctx.arc(x, y, A * 0.045, 0, 2 * math.pi)
        ctx.set_source(grad_radial(x, y, 0, A * 0.05, [(0, (255, 255, 255)), (0.35, col), (1, tuple(v // 2 for v in col))], x - A * 0.015, y - A * 0.015)); ctx.fill()


def aros(ctx, g):
    p, A = g["p"], g["A"]
    for k, s in ((1, -1), (15, 1)):
        x, y = p[k, 0] + s * A * 0.07, p[k, 1] + A * 0.02
        ctx.new_path(); ctx.arc(x, y, A * 0.05, 0, 2 * math.pi)
        ctx.set_source(grad_radial(x, y, 0, A * 0.06, [(0, (255, 255, 255)), (0.5, (190, 235, 255)), (1, (90, 160, 230))], x - A * 0.015, y - A * 0.02)); ctx.fill()
        for a in range(4):                                                     # destello
            t = a * math.pi / 2
            ctx.move_to(x, y); ctx.line_to(x + math.cos(t) * A * 0.09, y + math.sin(t) * A * 0.09)
        ctx.set_source_rgba(1, 1, 1, 0.9); ctx.set_line_width(A * 0.008); ctx.stroke()


def pelo_puntas(ctx, g, col, n=11, largo=1.0, semilla=1):
    """Pelo anime de puntas, cubriendo el cráneo."""
    rng = random.Random(semilla)
    A, cx, cyk, rx, ry = g["A"], g["cx"], g["cyk"], g["rx"], g["ry"]
    claro = tuple(min(255, int(v * 1.35 + 40)) for v in col); oscuro = tuple(int(v * 0.45) for v in col)
    ctx.new_path()
    ctx.move_to(cx - rx * 1.08, cyk + A * 0.05)
    for i in range(n + 1):
        t = math.pi * (1.0 + i / n)
        bx, by = cx + rx * 1.05 * math.cos(t), cyk + ry * 1.0 * math.sin(t)
        out = (A * 0.38 + rng.uniform(-0.06, 0.1) * A) * largo
        ox, oy = math.cos(t) * out, math.sin(t) * out
        if i:
            pt = math.pi * (1.0 + (i - 0.5) / n)
            ctx.line_to(cx + rx * 1.12 * math.cos(pt) + math.cos(pt) * out * 1.25, cyk + ry * 1.1 * math.sin(pt) + math.sin(pt) * out * 1.25)
        ctx.line_to(bx, by)
    ctx.line_to(cx + rx * 1.08, cyk + A * 0.05)
    # flequillo sobre la frente
    for i in range(5):
        x = cx + rx * (0.8 - i * 0.4)
        ctx.line_to(x, cyk + A * (0.1 + 0.08 * (i % 2)))
        ctx.line_to(x - rx * 0.2, cyk - A * 0.05)
    ctx.close_path()
    ctx.set_source(grad_lineal(cx, cyk - ry * 1.6, cx, cyk + A * 0.1, [(0, claro), (0.55, col), (1, oscuro)])); ctx.fill_preserve()
    ctx.set_source_rgba(*[v / 255 for v in oscuro], 1); ctx.set_line_width(A * 0.018); ctx.set_line_join(cairo.LINE_JOIN_ROUND); ctx.stroke()
    ctx.set_source_rgba(1, 1, 1, 0.35); ctx.set_line_width(A * 0.02)               # mechones de brillo
    for i in range(6):
        t = math.pi * (1.15 + i * 0.13)
        ctx.move_to(cx + rx * 0.3 * math.cos(t), cyk - ry * 0.4 + ry * 0.3 * math.sin(t))
        ctx.line_to(cx + rx * 1.1 * math.cos(t), cyk + ry * 1.05 * math.sin(t)); ctx.stroke()


def pompones(ctx, g, colores, radio=0.2, semilla=3, ancho=1.25, alto=1.15):
    """Peluca de rulos/pompones (payaso arcoíris, afro)."""
    rng = random.Random(semilla)
    A, cx, cyk, rx, ry = g["A"], g["cx"], g["cyk"], g["rx"], g["ry"]
    bolas = []
    for i in range(70):
        t = math.pi * rng.uniform(0.92, 2.08); r = rng.uniform(0.55, 1.0)
        x = cx + rx * ancho * r * math.cos(t) * 1.15; y = cyk + A * 0.12 + ry * alto * r * math.sin(t) * 1.05
        if y > cyk + A * 0.35:
            continue
        bolas.append((y, x, colores[int((x - cx + rx * 1.4) / (rx * 2.8) * len(colores)) % len(colores)]))
    for y, x, col in sorted(bolas):
        rr = A * radio * rng.uniform(0.75, 1.1)
        ctx.new_path(); ctx.arc(x, y, rr, 0, 2 * math.pi)
        ctx.set_source(grad_radial(x, y, 0, rr, [(0, tuple(min(255, v + 90) for v in col)), (0.6, col), (1, tuple(v // 2 for v in col))], x - rr * 0.35, y - rr * 0.35)); ctx.fill()


def peluca_rosa(ctx, g):
    A, cx, cyk, rx, ry, p = g["A"], g["cx"], g["cyk"], g["rx"], g["ry"], g["p"]
    col = (255, 105, 190); claro = (255, 190, 230); osc = (190, 40, 120)
    menton = p[8, 1] - A * 0.05
    ctx.new_path()
    ctx.move_to(cx - rx * 1.25, menton)
    ctx.curve_to(cx - rx * 1.45, cyk - ry * 0.3, cx - rx * 1.2, cyk - ry * 1.35, cx, cyk - ry * 1.3)
    ctx.curve_to(cx + rx * 1.2, cyk - ry * 1.35, cx + rx * 1.45, cyk - ry * 0.3, cx + rx * 1.25, menton)
    ctx.line_to(cx + rx * 0.95, menton); ctx.curve_to(cx + rx * 1.0, cyk + A * 0.2, cx + rx * 0.9, cyk + A * 0.05, cx + rx * 0.7, cyk + A * 0.02)
    ctx.line_to(cx - rx * 0.7, cyk + A * 0.02); ctx.curve_to(cx - rx * 0.9, cyk + A * 0.05, cx - rx * 1.0, cyk + A * 0.2, cx - rx * 0.95, menton)
    ctx.close_path()
    ctx.set_source(grad_lineal(cx, cyk - ry * 1.3, cx, menton, [(0, claro), (0.4, col), (1, osc)])); ctx.fill_preserve()
    ctx.set_source_rgba(*[v / 255 for v in osc], 1); ctx.set_line_width(A * 0.015); ctx.stroke()
    ctx.set_source_rgba(1, 1, 1, 0.3); ctx.set_line_width(A * 0.012)
    for i in range(9):
        x = cx - rx * 1.1 + i * rx * 0.27
        ctx.move_to(x, cyk - ry * 1.1 + abs(i - 4) * A * 0.04); ctx.curve_to(x - A * 0.05, cyk, x, menton - A * 0.2, x + A * 0.02, menton - A * 0.05); ctx.stroke()
    for s in (-1, 1):                                                          # moños
        x, y = cx + s * rx * 0.9, cyk - ry * 0.85
        ctx.new_path(); ctx.arc(x, y, A * 0.07, 0, 2 * math.pi); ctx.set_source_rgba(1, 0.92, 0.3, 1); ctx.fill()


def mohawk(ctx, g, col=(30, 30, 35)):
    A, cx, cyk, ry = g["A"], g["cx"], g["cyk"], g["ry"]
    ctx.new_path(); ctx.move_to(cx - A * 0.12, cyk - A * 0.05)
    for i in range(8):
        t = i / 7
        x = cx - A * 0.12 + t * A * 0.24
        ctx.line_to(x - A * 0.04, cyk - ry * (1.0 + 0.6 * math.sin(t * math.pi)) - A * 0.3)
        ctx.line_to(x + A * 0.02, cyk - ry * 0.9)
    ctx.line_to(cx + A * 0.12, cyk - A * 0.05); ctx.close_path()
    ctx.set_source(grad_lineal(cx, cyk - ry * 2, cx, cyk, [(0, (255, 60, 60)), (1, col)])); ctx.fill()


def dibujar(nombre, ctx, g):
    if nombre == "anteojos":
        anteojos(ctx, g)
    elif nombre == "anteojos_oro":
        anteojos(ctx, g, dorado=True)
    elif nombre == "cadena":
        cadena(ctx, g)
    elif nombre == "cadena_doble":
        cadena(ctx, g, doble=True)
    elif nombre == "corona":
        corona(ctx, g)
    elif nombre == "aros":
        aros(ctx, g)
    elif nombre == "pelo_verde":
        pelo_puntas(ctx, g, (70, 200, 50), semilla=2)
    elif nombre == "pelo_azul":
        pelo_puntas(ctx, g, (40, 90, 230), semilla=5, largo=1.2)
    elif nombre == "pelo_rubio":
        pelo_puntas(ctx, g, (250, 220, 90), semilla=7, n=13, largo=0.8)
    elif nombre == "pelo_rojo":
        pelo_puntas(ctx, g, (230, 50, 40), semilla=9, largo=1.1)
    elif nombre == "payaso":
        pompones(ctx, g, [(240, 40, 40), (255, 150, 0), (255, 230, 0), (60, 200, 70), (40, 120, 255), (150, 60, 220)], 0.2, 3, 1.45, 1.2)
    elif nombre == "afro":
        pompones(ctx, g, [(35, 25, 20)], 0.17, 4, 1.35, 1.35)
    elif nombre == "peluca_rosa":
        peluca_rosa(ctx, g)
    elif nombre == "mohawk":
        mohawk(ctx, g)


def capa(nombre, g, tam):
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, int(tam[0]), int(tam[1]))
    ctx = cairo.Context(surf); ctx.translate(0, g.get("dy", 0))
    dibujar(nombre, ctx, g)
    surf.flush()
    return a_pil(surf)
