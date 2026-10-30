#!/usr/bin/env python3
"""
FIND v2 (reporte 24, reglas de retención): grilla 5x5 numerada de caras graciosas, una sola es la real.

- Cuadro 0: fondo claro (cielo + pasto), "FIND <JUGADOR>" grande y una cara deformada GIGANTE que se achica hasta su
  casillero mientras aparece la grilla (movimiento + cara grande desde el primer cuadro).
- 3 rondas: fácil (caras exageradas), media, "ONLY 1%" (casi iguales). 3 s para buscar con barra y tic-tac que acelera;
  cada segundo una cara falsa "salta" para despistar.
- Revelación: se apagan las falsas, círculo rojo a mano sobre la real y "#N". Pedido de comentario fijo: el número.
- Termina justo en la última revelación (sin cierre) para que el loop vuelva a la cara gigante.

Uso: python3 produccion/render_find_v2.py produccion/guiones/find_v2_01.json
"""
import json
import math
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

import caras_find as CF
import motor as M
import render_runner as RR

ROOT = Path(__file__).resolve().parent
W, H, FPS = 1080, 1920, 30
F_TIT = str(ROOT / "assets" / "fuentes" / "ArchivoBlack-Regular.ttf")
F_NUM = str(ROOT / "assets" / "fuentes" / "Anton-Regular.ttf")
N, TILE, GAP, PAD = 5, 194, 8, 14
PX, PY = (W - (N * TILE + (N - 1) * GAP + 2 * PAD)) // 2, 330
T_INTRO, T_POP, T_BUSCAR, T_REVELA = 0.95, 0.35, 3.0, 0.9
T_QUIETA, T_FLASH = 0.45, 0.3              # la cara gigante se queda quieta con la frase; el flash se apaga en 0,3 s
FRASE = "99% FAIL THIS"
NIVEL = {"facil": ("EASY", (61, 200, 110)), "medio": ("MEDIUM", (255, 176, 32)), "dificil": ("ONLY 1%", (235, 64, 52))}


def fuente(f, t):
    return ImageFont.truetype(f, t)


def ease_out(x):
    x = min(max(x, 0.0), 1.0)
    return 1 - (1 - x) ** 3


def resorte(x):
    """0→1 con rebote (pop)."""
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    return 1 + math.sin(x * math.pi * 1.5) * math.exp(-x * 4) * 0.35 - (1 - x) ** 3


def fondo():
    im = Image.new("RGB", (W, H))
    a = np.zeros((H, W, 3), np.float32)
    y = np.linspace(0, 1, 1440)[:, None]
    a[:1440] = (np.array([46, 160, 255]) * (1 - y) + np.array([196, 238, 255]) * y)[:, None, :]
    for i in range(1440, H):
        k = (i - 1440) / (H - 1440)
        base = np.array([92, 200, 74]) if ((i - 1440) // 70) % 2 == 0 else np.array([78, 184, 62])
        a[i] = base * (1 - 0.35 * k)
    im = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    nubes = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(nubes)
    for cx, cy, s in [(150, 250, 1.0), (880, 200, 1.3), (520, 1420, 1.6), (90, 1400, 1.1), (1000, 1380, 1.2)]:
        for dx, dy, r in [(-60, 10, 60), (0, -15, 80), (70, 5, 65), (130, 20, 45)]:
            d.ellipse([cx + dx * s - r * s, cy + dy * s - r * s, cx + dx * s + r * s, cy + dy * s + r * s], fill=(255, 255, 255, 200))
    im.paste(nubes.filter(ImageFilter.GaussianBlur(6)), (0, 0), nubes.filter(ImageFilter.GaussianBlur(6)))
    # panel blanco de la grilla con sombra
    lado = N * TILE + (N - 1) * GAP + 2 * PAD
    sombra = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sombra).rounded_rectangle([PX + 6, PY + 14, PX + lado + 6, PY + lado + 14], 30, fill=(10, 40, 80, 110))
    im.paste(sombra.filter(ImageFilter.GaussianBlur(14)), (0, 0), sombra.filter(ImageFilter.GaussianBlur(14)))
    ImageDraw.Draw(im).rounded_rectangle([PX, PY, PX + lado, PY + lado], 30, fill=(255, 255, 255))
    return im


def pos(i):
    r, c = divmod(i, N)
    return PX + PAD + c * (TILE + GAP), PY + PAD + r * (TILE + GAP)


def tile_img(bgr, num):
    im = Image.fromarray(bgr[..., ::-1]).resize((TILE, TILE), Image.LANCZOS)
    m = Image.new("L", (TILE, TILE), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, TILE - 1, TILE - 1], 18, fill=255)
    out = Image.new("RGBA", (TILE, TILE), (0, 0, 0, 0)); out.paste(im, (0, 0), m)
    d = ImageDraw.Draw(out)
    d.rounded_rectangle([6, 6, 54, 46], 10, fill=(255, 255, 255, 235))
    d.text((30, 26), str(num), font=fuente(F_NUM, 32), fill=(20, 20, 30), anchor="mm")
    return out


def texto(d, xy, s, tam, fill, stroke=10, sc=(16, 32, 72), f=F_TIT):
    d.text(xy, s, font=fuente(f, tam), fill=fill, anchor="mm", stroke_width=stroke, stroke_fill=sc)


def titulo(nombre, nivel, escala, ang):
    capa = Image.new("RGBA", (W, 300), (0, 0, 0, 0)); d = ImageDraw.Draw(capa)
    tam = 150
    while d.textlength(f"FIND {nombre}", font=fuente(F_TIT, tam)) + 2 * 14 > W - 50:
        tam -= 4
    texto(d, (W // 2 + 6, 196), f"FIND {nombre}", tam, (16, 32, 72), 14)               # sombra
    texto(d, (W // 2, 188), f"FIND {nombre}", tam, (255, 214, 30), 14)
    et, col = NIVEL[nivel]
    w = 60 + 26 * len(et)
    d.rounded_rectangle([W // 2 - w // 2, 40, W // 2 + w // 2, 96], 28, fill=col, outline=(16, 32, 72), width=5)
    d.text((W // 2, 68), et, font=fuente(F_TIT, 34), fill=(255, 255, 255), anchor="mm")
    if escala != 1 or ang:
        capa = capa.rotate(ang, resample=Image.BICUBIC, center=(W // 2, 188))
        cw, ch = int(W * escala), int(300 * escala)
        capa = capa.resize((cw, ch), Image.BICUBIC)
        out = Image.new("RGBA", (W, 300), (0, 0, 0, 0)); out.paste(capa, ((W - cw) // 2, int(188 - 188 * escala)), capa)
        return out
    return capa


def circulo_mano(d, cx, cy, r, prog, ancho=12):
    pts = []
    for k in range(int(80 * prog) + 1):
        a = -math.pi * 0.65 + 2.25 * math.pi * k / 80
        rr = r * (1 + 0.06 * math.sin(a * 3) + 0.05 * (k / 80))
        pts.append((cx + rr * math.cos(a) * 1.05, cy + rr * math.sin(a)))
    if len(pts) > 1:
        d.line(pts, fill=(235, 30, 30), width=ancho, joint="curve")


def armar(g):
    rondas, t = [], 0.0
    for k, r in enumerate(g["rondas"]):
        img, p = CF.base(r["foto"])
        rng = np.random.default_rng(g["semilla"] + k)
        evitar = {4, 9, 14, 19, 24, 12} if k == 0 else {4, 9, 14, 19, 24}           # columna de botones y casillero de la intro
        real = int(rng.choice([i for i in range(N * N) if i not in evitar]))
        falsas = CF.variantes(img, p, N * N - 1, r["nivel"], g["semilla"] * 10 + k)
        if k == 0:                                                          # la cara del gancho: la más graciosa
            heroe = img
            for nom, fz in (("cachetes", 0.9), ("ojos_gigantes", 1.0), ("lengua", 1.0)):
                heroe = CF.efecto(heroe, p, nom, fz)
            falsas[12 if real > 12 else 11] = heroe
        caras, j = [], 0
        for i in range(N * N):
            if i == real:
                caras.append(img)
            else:
                caras.append(falsas[j]); j += 1
        t0 = t
        dur = (T_INTRO if k == 0 else T_POP) + T_BUSCAR + T_REVELA
        rondas.append(dict(nombre=r["nombre"].upper(), nivel=r["nivel"], real=real, t0=t0, t_busca=t0 + (T_INTRO if k == 0 else T_POP),
                           t_rev=t0 + dur - T_REVELA, t1=t0 + dur, tiles=[tile_img(c, i + 1) for i, c in enumerate(caras)],
                           heroe=Image.fromarray(caras[12][..., ::-1]), saltos=[int(x) for x in rng.choice([i for i in range(25) if i != real], 3, replace=False)]))
        t += dur
    return rondas, t


def cuadro(fnd, R, t, k):
    im = fnd.copy(); d = ImageDraw.Draw(im)
    lt = t - R["t0"]
    # título: entra con golpe en cada ronda (en la 1ª ya está en el cuadro 0) y respira con el beat
    if k == 0:
        esc = 1 + 0.03 * math.sin(t * 2 * math.pi * 128 / 60 / 2)
    else:
        esc = 0.4 + 0.6 * resorte(lt / 0.35)
    tit = titulo(R["nombre"], R["nivel"], esc, 2.5 * math.sin(t * 3.1))
    im.paste(tit, (0, 0), tit)
    revelando = t >= R["t_rev"]
    pr = (t - R["t_rev"]) / T_REVELA
    for i, tl in enumerate(R["tiles"]):
        x, y = pos(i)
        if k == 0:
            a = ease_out((lt - 0.02 - 0.012 * i) / 0.3) if i != 12 else 1.0
        else:
            a = resorte((lt - 0.012 * i) / 0.3)
        if a <= 0:
            continue
        if k == 0 and i == 12 and lt < T_INTRO:
            continue                                                            # lo dibuja la intro
        s = a
        for j, ts in enumerate(R["saltos"]):                                   # cara falsa que "salta" para despistar
            tj = R["t_busca"] + 0.6 + j * 0.9
            if i == ts and tj <= t < tj + 0.3:
                s *= 1 + 0.16 * math.sin((t - tj) / 0.3 * math.pi)
        if revelando and i == R["real"]:
            s *= 1 + 0.22 * ease_out(pr / 0.3)
        tt = tl if s == 1 else tl.resize((max(1, int(TILE * s)), max(1, int(TILE * s))), Image.BICUBIC)
        if revelando and i != R["real"]:
            osc = Image.new("RGBA", tt.size, (255, 255, 255, int(150 * ease_out(pr / 0.2))))
            tt = tt.copy(); tt.alpha_composite(Image.composite(osc, Image.new("RGBA", tt.size, (0, 0, 0, 0)), tt.split()[3]))
        im.paste(tt, (x + (TILE - tt.width) // 2, y + (TILE - tt.height) // 2), tt)
    if revelando:                                                              # la real arriba de todo + círculo
        x, y = pos(R["real"]); s = 1 + 0.22 * ease_out(pr / 0.3)
        tt = R["tiles"][R["real"]].resize((int(TILE * s), int(TILE * s)), Image.BICUBIC)
        im.paste(tt, (x + (TILE - tt.width) // 2, y + (TILE - tt.height) // 2), tt)
        circulo_mano(d, x + TILE / 2, y + TILE / 2, TILE * 0.68, ease_out(pr / 0.3))
    # intro: cara gigante que se achica hasta su casillero
    if k == 0 and lt < T_INTRO:
        e = ease_out((lt - T_QUIETA) / (T_INTRO - T_QUIETA))
        x1, y1 = pos(12)
        golpe = 1 + 0.14 * math.exp(-lt * 14) * math.cos(lt * 40)                # zoom de impacto al arrancar
        lado = int(700 * golpe * (1 - e) + TILE * e)
        cx = W / 2 * (1 - e) + (x1 + TILE / 2) * e; cy = 860 * (1 - e) + (y1 + TILE / 2) * e
        h = R["heroe"].resize((lado, lado), Image.BICUBIC)
        m = Image.new("L", (lado, lado), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, lado - 1, lado - 1], int(18 + 40 * (1 - e)), fill=255)
        bor = Image.new("RGB", (lado + 16, lado + 16), (255, 255, 255))
        im.paste(bor, (int(cx - lado / 2 - 8), int(cy - lado / 2 - 8)))
        im.paste(h, (int(cx - lado / 2), int(cy - lado / 2)), m)
        if lt < T_QUIETA + 0.12:                                               # frase fuerte arriba de la cara
            z = 0.8 + 0.2 * resorte(lt / 0.22) if lt < 0.22 else 1.0
            fade = 1 - max(0, (lt - T_QUIETA) / 0.12)
            capa = Image.new("RGBA", (W, 260), (0, 0, 0, 0)); dc = ImageDraw.Draw(capa)
            fr = R.get("frase", FRASE); tf = 108
            while dc.textlength(fr, font=fuente(F_TIT, tf)) > W - 140:
                tf -= 4
            texto(dc, (W // 2, 130), fr, tf, (255, 40, 40), 16, (255, 255, 255))
            capa = capa.rotate(6, resample=Image.BICUBIC)
            cw, ch = int(W * z), int(260 * z)
            capa = capa.resize((cw, ch), Image.BICUBIC)
            if fade < 1:
                capa.putalpha(capa.split()[3].point(lambda v: int(v * fade)))
            im.paste(capa, ((W - cw) // 2, int(1180 - ch / 2)), capa)
    if t < T_FLASH:                                                            # flash blanco que se apaga
        a = 0.45 * (1 - t / T_FLASH) ** 2
        im = Image.blend(im.convert("RGB"), Image.new("RGB", (W, H), (255, 255, 255)), a)
        d = ImageDraw.Draw(im)
    # barra de tiempo + cuenta
    bx0, bx1, by = 70, W - 70, 1392
    d.rounded_rectangle([bx0, by, bx1, by + 38], 19, fill=(16, 32, 72))
    resto = 1 - min(max((t - R["t_busca"]) / T_BUSCAR, 0), 1)
    if t < R["t_busca"]:
        resto = 1.0
    col = (61, 214, 110) if resto > 0.55 else (255, 196, 30) if resto > 0.25 else (240, 60, 50)
    if resto > 0:
        d.rounded_rectangle([bx0 + 5, by + 5, bx0 + 5 + (bx1 - bx0 - 10) * resto, by + 33], 14, fill=col)
    if revelando:
        z = resorte(pr / 0.35)
        texto(d, (W // 2, 1520), f"#{R['real'] + 1}", int(40 + 110 * z), (61, 214, 110), 12)
    else:
        texto(d, (W // 2, 1500), "WHICH NUMBER?", 64, (255, 255, 255), 9)
        texto(d, (W // 2, 1575), "COMMENT IT BELOW", 40, (255, 214, 30), 7)
    return im


def audio(rondas, dur):
    mez = M.Mezcla(dur)
    tic = np.sin(2 * np.pi * 1900 * np.arange(int(0.035 * M.SR)) / M.SR) * np.exp(-np.arange(int(0.035 * M.SR)) / M.SR * 90) * 0.35
    drama = RR.sfx("dramatic_0", 0, 1.6, 0.55)
    wow = RR.sfx("wow_0", 0, 1.4, 0.5)
    n = int(0.09 * M.SR); ruido = np.random.default_rng(9).standard_normal(n).astype(np.float32)
    obturador = np.diff(ruido, prepend=0) * np.exp(-np.arange(n) / M.SR * 45) * 0.5          # "clic" de cámara (ruido agudo)
    tt = np.arange(int(0.6 * M.SR)) / M.SR
    zumbido = np.sin(2 * np.pi * 3200 * tt) * np.exp(-tt * 7) * 0.12                          # pitido del flash
    mez.add(0.0, obturador); mez.add(0.0, zumbido)
    mez.add(0.0, RR.sfx("vine_boom_0", 0, 1.2, 0.9))
    mez.add(T_QUIETA - 0.05, M.whoosh(0.45), 0.6)
    for k, R in enumerate(rondas):
        if k:
            mez.add(R["t0"] - 0.05, M.whoosh(0.4), 0.5)
        if R["nivel"] == "dificil":
            mez.add(R["t0"] + 0.05, drama)
        tt = R["t_busca"]
        while tt < R["t_rev"] - 0.05:                                          # tic-tac que acelera
            mez.add(tt, tic)
            frac = (tt - R["t_busca"]) / T_BUSCAR
            tt += 0.5 if frac < 0.5 else 0.33 if frac < 0.8 else 0.2
        for j in range(3):
            mez.add(R["t_busca"] + 0.6 + j * 0.9, M.pluck(M.NOTAS[6 + j], 0.2, 0.2))
        mez.add(R["t_rev"], M.ding(), 0.9)
        mez.add(R["t_rev"] + 0.05, M.tribuna(1.0), 0.45)
        if k == len(rondas) - 1:
            mez.add(R["t_rev"] + 0.15, wow)
    solo = mez.x[: int(dur * M.SR)]
    import render_stop as RS
    musica = RS.musica_67(dur)[: len(solo)]
    return {"short.mp4": np.tanh((solo + musica * 0.55) * 1.05) * 0.92, "short_sin_musica.mp4": np.tanh(solo * 1.05) * 0.85}


def main(guion):
    g = json.loads(Path(guion).read_text())
    out = ROOT / "salida" / g["id"]; out.mkdir(parents=True, exist_ok=True)
    rondas, dur = armar(g)
    rondas[0]["frase"] = g.get("frase", FRASE)
    fnd = fondo()
    mudo = out / "mudo.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", str(mudo)], stdin=subprocess.PIPE)
    nf = int(round(dur * FPS))
    for f in range(nf):
        t = f / FPS
        k = max(i for i, R in enumerate(rondas) if t >= R["t0"])
        im = cuadro(fnd, rondas[k], t, k)
        p.stdin.write(np.asarray(im.convert("RGB"), np.uint8).tobytes())
        if f in (0, int(0.25 * FPS), int((rondas[0]["t_rev"] + 0.4) * FPS), int((rondas[2]["t0"] + 1.5) * FPS)):
            im.convert("RGB").save(out / f"muestra_{f:03d}.jpg", quality=85)
    p.stdin.close(); p.wait()
    M.mezclar(out, mudo, audio(rondas, dur))
    json.dump(dict(duracion=dur, rondas=[dict(nombre=R["nombre"], real=R["real"] + 1, nivel=R["nivel"]) for R in rondas]),
              open(out / "resultado.json", "w"), indent=1)
    print(out / "short.mp4", round(dur, 2), "s", [R["real"] + 1 for R in rondas])


if __name__ == "__main__":
    main(sys.argv[1])
