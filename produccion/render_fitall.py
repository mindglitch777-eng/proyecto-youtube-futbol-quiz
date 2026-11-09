#!/usr/bin/env python3
"""
FIT ALL (ola del 09/11: "Can Anyone Solve This? FitAll Neymar Jr Stars" 4,6 M en 3 días en un canal de 21k; 18 videos +1 M en 7 días).
Lo que hacen los virales: anillo de 8 cabezas del MISMO jugador girando arriba, cuerpo sin cabeza abajo, 3 s, loop, audio pegadizo.
Nuestra versión (más difícil = más intentos = más loops): las 8 cabezas son de la misma superestrella, pero SOLO UNA es la de esa foto
(las otras 7 son fotos distintas del mismo jugador: otro peinado, otra cara, otro ángulo). Hay que pausar cuando la cabeza REAL
encaja en el cuello. El encaje cae en el corte del loop (t_encaje 0,45 s), como en WHEEL y HEAD FIT.

Recortes: assets/recortes/cuerpos/*.png (cuerpo + cabeza correcta) y torsos/*.png + cuerpos/*.png (cabezas señuelo).
Uso: python3 produccion/render_fitall.py guion.json
guion: {"id", "cuerpo": "cristiano_ronaldo_14", "senuelos": ["cristiano_ronaldo_0", ...7] (opcional: "carpeta/nombre[:espejo]"),
        "nombre": "Ronaldo", "dur": 4.0, "vueltas": 3, "t_encaje": 0.45, "sentido": 1, "musica": "suuu_remix_0", "fondo": "estadio_0",
        "pos_correcto": 3}
"""
import json
import math
import subprocess
import sys
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps

import motor as M
import render_plinko as P
import render_rueda as RR

ROOT = Path(__file__).resolve().parent
REC = ROOT / "assets" / "recortes"
W, H, FPS = 1080, 1920, 30
CARA = 128                    # alto de cara (px) de todas las cabezas y del cuerpo: quedan parejas
K_PELO = 0.75                 # cuánto pelo entra arriba de la cara (en caras)
K_CUELLO = 1.06               # corte justo debajo del mentón: el cuello de la camiseta queda en el cuerpo (no delata)
K_ANCHO = 1.05                # media anchura de la cabeza recortada (en caras): sin hombros ni camiseta (no delata)
HUECO = 165                   # radio del agujero del centro del anillo (abierto: las 8 caras se ven grandes)
T_ZOOM, ZOOM = 0.35, 2.3        # arranque con zoom a las cabezas (regla: cara grande en el cuadro 0)
PIE_Y = 1990                  # los botines quedan apenas fuera de cuadro: más lugar para el anillo


def _abrir(ref):
    """ref = 'torsos/cristiano_ronaldo_0' o 'cuerpos/x_3', con ':espejo' opcional."""
    nom, _, esp = ref.partition(":")
    carpeta, n = nom.split("/") if "/" in nom else ("torsos", nom)
    im = Image.open(REC / carpeta / f"{n}.png").convert("RGBA")
    return ImageOps.mirror(im) if esp else im


@lru_cache(maxsize=32)
def cabeza(ref):
    """Cabeza + cuello (sin hombros), con la cara de CARA px. Devuelve la imagen centrada en la cara."""
    im = _abrir(ref)
    x, y, fw, fh = RR.cara(im)
    s = CARA / fh
    im = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)
    x, y, fw, fh = x * s, y * s, fw * s, fh * s
    cx = x + fw / 2
    caja = (int(cx - K_ANCHO * fh), int(max(0, y - K_PELO * fh)), int(cx + K_ANCHO * fh), int(y + K_CUELLO * fh))
    c = Image.new("RGBA", (caja[2] - caja[0], caja[3] - caja[1]))
    c.alpha_composite(im.crop(caja))
    # máscara ovalada (cara + pelo + cuello): afuera hombros, manos y pedazos de camiseta que delatan cuál es la real
    hh, ww = c.height, c.width
    yy, xx = np.mgrid[0:hh, 0:ww].astype(np.float32)
    cyo = hh * 0.44; ry = hh * 0.47; rx = ww * 0.41
    dist = ((xx - ww / 2) / rx) ** 2 + ((yy - cyo) / ry) ** 2
    m = np.clip((1.0 - dist) / 0.12, 0, 1)
    cuello = (yy > hh * 0.8) & (np.abs(xx - ww / 2) < fh * 0.3)                # el cuello llega entero al corte (encaja en el cuerpo)
    m = np.maximum(m, cuello * np.clip((fh * 0.3 - np.abs(xx - ww / 2)) / 8, 0, 1))
    a = np.asarray(c).copy()
    a[..., 3] = (a[..., 3] * m).astype(np.uint8)
    return Image.fromarray(a)


@lru_cache(maxsize=8)
def cuerpo(nombre):
    """Cuerpo sin cabeza (desde el corte del cuello hasta los pies) y la x del cuello."""
    im = Image.open(REC / "cuerpos" / f"{nombre}.png").convert("RGBA")
    x, y, fw, fh = RR.cara(im)
    s = CARA / fh
    im = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
    x, y, fw, fh = x * s, y * s, fw * s, fh * s
    corte = int(y + K_CUELLO * fh)
    p = im.crop((0, corte, im.width, im.height))
    bb = p.getbbox()
    return p.crop((bb[0], 0, bb[2], bb[3])), (x + fw / 2) - bb[0]


MALAS = {"vin_cius_j_nior_12", "vin_cius_j_nior_10", "cristiano_ronaldo_3"}        # revisadas a ojo: dedo en la cara, cabeza para arriba, color raro
CUERPOS = {"cristiano_ronaldo": ["cristiano_ronaldo_14", "cristiano_ronaldo_12", "cristiano_ronaldo_10", "cristiano_ronaldo_1"],
           "vin_cius_j_nior": ["vin_cius_j_nior_14", "vin_cius_j_nior_11", "vin_cius_j_nior_13"],
           "kylian_mbapp": ["kylian_mbapp_12", "kylian_mbapp_13", "kylian_mbapp_10"],
           "lamine_yamal": ["lamine_yamal_10"], "neymar": ["neymar_1", "neymar_3"], "lionel_messi": ["lionel_messi_3", "lionel_messi_2"]}
LISTAS = ["cristiano_ronaldo", "vin_cius_j_nior", "kylian_mbapp"]   # con ≥7 cabezas distintas (Messi/Neymar/Yamal: faltan fotos)
NOMBRES = {"cristiano_ronaldo": "Ronaldo", "vin_cius_j_nior": "Vinícius", "kylian_mbapp": "Mbappé", "lamine_yamal": "Yamal",
           "neymar": "Neymar", "lionel_messi": "Messi"}


def _huella(img):
    a = np.asarray(img.convert("RGBA").resize((24, 24)), np.float32)
    return a[..., :3] * (a[..., 3:] / 255)


def parecidas(a, b):
    return float(np.abs(_huella(a) - _huella(b)).mean()) < 14


def senuelos(cuerpo_, rng, n=7):
    """7 cabezas del MISMO jugador, todas distintas entre sí y distintas de la real (sin fotos repetidas).
    Si faltan fotos, entran espejadas (nunca la real espejada: sería demasiado parecida)."""
    est = cuerpo_.rsplit("_", 1)[0]
    real = cabeza("cuerpos/" + cuerpo_)
    refs = [f"{c}/{p.stem}" for c in ("cuerpos", "torsos") for p in sorted((REC / c).glob(est + "_*.png")) if p.stem not in MALAS]
    rng.shuffle(refs)
    elegidas, imgs = [], [real]
    for r in refs:
        try:
            im = cabeza(r)
        except Exception:
            continue
        if not any(parecidas(im, x) for x in imgs):
            elegidas.append(r); imgs.append(im)
    base = list(elegidas)
    for r in base:
        if len(elegidas) >= n:
            break
        elegidas.append(r + ":espejo")
    return elegidas[:n]


def armar(g):
    ref_ok = "cuerpos/" + g["cuerpo"]
    pz = [cabeza(r if "/" in r else "torsos/" + r) for r in g["senuelos"]]
    k = g.get("pos_correcto", 3)
    pz.insert(k, cabeza(ref_ok))
    body, cuello_x = cuerpo(g["cuerpo"])
    alto = max(p.height for p in pz)
    r = HUECO + alto / 2
    cuello_y = PIE_Y - body.height
    cy = cuello_y - pz[k].height / 2 - r
    sobra = (cy - r - alto / 2) - 230                                          # lugar libre bajo el cartel de arriba: el anillo lo usa
    if sobra > 0:
        r += sobra / 2; cy -= sobra / 2
    return dict(piezas=pz, correcto=k, cuerpo=body, cuello_x=cuello_x, r=r, centro=(W / 2, cy), cuello_y=cuello_y,
                fondo=RR.fondo(g.get("fondo")))


def angulo(g, A, t):
    n = len(A["piezas"]); paso = 360 / n
    vel = g.get("sentido", 1) * 360.0 * g.get("vueltas", 3) / g["dur"]
    return 90 - A["correcto"] * paso - vel * g.get("t_encaje", 0.45) + vel * t


def encajes(g, A):
    n = len(A["piezas"]); paso = 360 / n; out = []
    for f in range(int(round(g["dur"] * FPS))):
        t = f / FPS
        a = (angulo(g, A, t) + A["correcto"] * paso - 90) % 360
        if min(a, 360 - a) < 360 * g.get("vueltas", 3) / g["dur"] / FPS / 1.9 and (not out or t - out[-1] > 0.6):
            out.append(t)
    return out


@lru_cache(maxsize=2)
def aro(r):
    """Aro dorado detrás de las cabezas (como los virales): marca el camino y da brillo."""
    im = Image.new("RGBA", (W, W)); d = ImageDraw.Draw(im)
    c = W / 2
    for gr, al in ((26, 40), (16, 90), (7, 230)):
        d.ellipse((c - r - gr, c - r - gr, c + r + gr, c + r + gr), outline=(255, 205, 60, al), width=gr)
    return im.filter(ImageFilter.GaussianBlur(3))


def cuadro(g, A, t, enc):
    im = A["fondo"].copy()
    cx, cy = A["centro"]
    im.alpha_composite(aro(int(A["r"])), (int(cx - W / 2), int(cy - W / 2)))
    im.alpha_composite(A["cuerpo"], (int(cx - A["cuello_x"]), int(A["cuello_y"])))
    n = len(A["piezas"]); paso = 360 / n; a0 = angulo(g, A, t)
    capas = []
    for k, img in enumerate(A["piezas"]):
        th = a0 + k * paso; rad = math.radians(th)
        px, py = cx + A["r"] * math.cos(rad), cy + A["r"] * math.sin(rad)
        rot = img.rotate(90 - th, expand=True, resample=Image.BICUBIC)
        capas.append((math.sin(rad), rot, px, py))
    for _, rot, px, py in sorted(capas, key=lambda c: c[0]):
        im.alpha_composite(rot, (int(px - rot.width / 2), int(py - rot.height / 2)))
    d = ImageDraw.Draw(im)
    # flecha que señala el cuello vacío (en los virales: guía la vista al lugar del encaje)
    fy = A["cuello_y"] + 40
    d.polygon([(cx + 150, fy - 34), (cx + 150, fy + 34), (cx + 95, fy)], fill=(255, 255, 255, 235))
    d.rectangle((cx + 150, fy - 12, cx + 230, fy + 12), fill=(255, 255, 255, 235))
    num = int(((a0 - angulo(g, A, 0)) % 360) // paso) % n + 1
    P.texto(d, (110, 300), f"{num}.", 150, (255, 255, 255), 13, (230, 30, 30))
    for te in enc:
        e = t - te
        if -0.05 <= e < 0.5:
            if e < 0.15:
                im.alpha_composite(Image.new("RGBA", (W, H), (60, 230, 90, int(60 * (1 - max(e, 0) / 0.15)))))
                d = ImageDraw.Draw(im)
            P.texto(d, (W / 2, H - 70), "PERFECT!", int(110 * min(1, (e + 0.05) / 0.1)) + 1, (255, 230, 40), 12)
    if t < T_ZOOM:                                                             # arranque: zoom a las cabezas (caras grandes en el cuadro 0)
        u = t / T_ZOOM; z = 1 + (ZOOM - 1) * (1 - u) ** 2
        fx, fy = cx, A["cuello_y"] - A["r"] * 0.55
        w, h = W / z, H / z
        x0 = min(max(0, fx - w / 2), W - w); y0 = min(max(0, fy - h / 2), H - h)
        im = im.crop((int(x0), int(y0), int(x0 + w), int(y0 + h))).resize((W, H), Image.BICUBIC)
    import gancho as G
    G.capa(im, t, g["dur"], A["textos"], 95, ancho_max=1000, tam=78)
    return im.convert("RGB")


def audio(g, A, enc, dur):
    sr = M.SR; n = int(dur * sr); fx = np.zeros(n, np.float32)

    def add(t0, sig, v=1.0):
        a = int(t0 * sr) % n; b = min(n, a + len(sig)); fx[a:b] += sig[: b - a] * v
    paso = 360 / len(A["piezas"]); vel = 360 * g.get("vueltas", 3) / g["dur"]
    k = 0.0
    while k < dur:                                                             # tic por cada cabeza que pasa por el cuello
        add(k, M.golpe(0.04), 0.3); k += paso / vel
    for te in enc:
        add(te, M.ding(0.6), 0.6); add(te, M.boom(0.5), 0.45)
    import gancho as G
    add(0, G.silbato(sr), 1.0)
    mu = P.musica(g, dur)
    return np.tanh((mu * 0.8 + fx) * 1.1) * 0.9, np.tanh(fx * 1.1) * 0.85


def main(guion):
    g = json.loads(Path(guion).read_text())
    out = ROOT / "salida" / g["id"]; out.mkdir(parents=True, exist_ok=True)
    A = armar(g); dur = g["dur"]; enc = encajes(g, A)
    import gancho as G
    A["textos"] = g.get("textos") or G.elegir("fitall", g["id"], g.get("nombre", ""))
    mudo = out / "mudo.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", str(mudo)], stdin=subprocess.PIPE)
    for f in range(int(round(dur * FPS))):
        p.stdin.write(np.asarray(cuadro(g, A, f / FPS, enc), np.uint8).tobytes())
    p.stdin.close(); p.wait()
    con, solo = audio(g, A, enc, dur)
    M.mezclar(out, mudo, {"short.mp4": con, "short_solo_efectos.mp4": solo})
    print(out / "short.mp4", dur, "s", "encajes", [round(x, 2) for x in enc])


if __name__ == "__main__":
    main(sys.argv[1])
