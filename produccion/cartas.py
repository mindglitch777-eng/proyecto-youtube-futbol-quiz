#!/usr/bin/env python3
"""
Carta estilo FUT (oro "rare"), dibujada por nosotros (sin arte de EA): oro metálico con brillo, jugador recortado sin
fondo, media, posición, bandera, escudo del club, nombre y 6 estadísticas. carta(clave, ovr, brillo=0..1).

Uso de prueba: python3 produccion/cartas.py cristiano_ronaldo 99  → salida/carta_prueba.png
"""
import json
import sys
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent
ANTON = str(ROOT / "assets" / "fuentes" / "Anton-Regular.ttf")
ARCH = str(ROOT / "assets" / "fuentes" / "ArchivoBlack-Regular.ttf")
FRONT = json.loads((ROOT / "assets" / "fotos" / "frontales.json").read_text())
CW, CH = 600, 860

# nombre en la carta, posición, país, club, estadísticas base (PAC SHO PAS DRI DEF PHY)
DATOS = {
    "cristiano_ronaldo": ("RONALDO", "ST", "PT", "al_nassr", (77, 88, 75, 78, 34, 75)),
    "lionel_messi": ("MESSI", "RW", "AR", "inter_miami", (80, 87, 90, 92, 33, 64)),
    "neymar": ("NEYMAR JR", "LW", "BR", "santos", (79, 82, 84, 87, 37, 60)),
    "lamine_yamal": ("YAMAL", "RW", "ES", "barcelona", (88, 80, 84, 90, 32, 61)),
    "kylian_mbapp": ("MBAPPÉ", "ST", "FR", "real_madrid", (97, 90, 80, 92, 36, 78)),
    "erling_haaland": ("HAALAND", "ST", "NO", "man_city", (86, 92, 70, 80, 45, 88)),
    "vin_cius_j_nior": ("VINI JR.", "LW", "BR", "real_madrid", (95, 84, 81, 91, 29, 69)),
    "jude_bellingham": ("BELLINGHAM", "CAM", "ENG", "real_madrid", (80, 86, 84, 87, 78, 83)),
    "mohamed_salah": ("SALAH", "RW", "EG", "liverpool", (89, 87, 82, 88, 45, 76)),
    "harry_kane": ("KANE", "ST", "ENG", "bayern", (68, 93, 84, 82, 49, 83)),
    "pedri": ("PEDRI", "CM", "ES", "barcelona", (78, 72, 88, 89, 68, 70)),
    "ronaldinho": ("RONALDINHO", "CAM", "BR", "barcelona", (91, 89, 90, 96, 37, 81)),
    "zlatan_ibrahimovi": ("IBRAHIMOVIĆ", "ST", "SE", "milan", (80, 92, 81, 88, 37, 89)),
    "kevin_de_bruyne": ("DE BRUYNE", "CM", "BE", "napoli", (70, 86, 93, 85, 64, 75)),
    "zinedine_zidane": ("ZIDANE", "CAM", "FR", "real_madrid", (80, 87, 94, 94, 70, 84)),
    "thierry_henry": ("HENRY", "ST", "FR", "arsenal", (93, 91, 83, 89, 45, 81)),
    "sergio_ramos": ("RAMOS", "CB", "ES", "real_madrid", (72, 63, 74, 72, 88, 84)),
    "luka_modric": ("MODRIĆ", "CM", "HR", "milan", (72, 76, 89, 88, 72, 66)),
}


def datos(clave):
    return DATOS.get(clave, (clave.split("_")[0].upper(), "ST", None, None, (80, 80, 80, 80, 50, 75)))


def f(tam, cual=ANTON):
    return ImageFont.truetype(cual, tam)


def forma(w, h):
    """Contorno de la carta: puntas de arriba recortadas en curva, base en pico suave."""
    return [(w * 0.13, 0), (w * 0.87, 0), (w * 0.93, h * 0.035), (w, h * 0.05), (w, h * 0.80), (w * 0.82, h * 0.93),
            (w * 0.5, h), (w * 0.18, h * 0.93), (0, h * 0.80), (0, h * 0.05), (w * 0.07, h * 0.035)]


@lru_cache(maxsize=32)
def recorte_jugador(clave):
    """Cabeza + hombros sin fondo (GrabCut sembrado con los 68 puntos)."""
    import render_cabeza as RC
    im, corte, cx, A = RC.recorte(FRONT.get(clave, clave + "_0"))
    bb = im.getbbox()
    return im.crop(bb) if bb else im


def oro(w, h, tono=(1.0, 1.0, 1.0)):
    y = np.linspace(0, 1, h)[:, None]; x = np.linspace(0, 1, w)[None, :]
    base = np.array([248, 226, 140]) * (1 - y[..., None]) + np.array([196, 150, 50]) * y[..., None]
    base = np.broadcast_to(base, (h, w, 3)).copy()
    banda = np.exp(-((x * 0.8 + y * 0.6 - 0.55) ** 2) / 0.012)[..., None]     # reflejo diagonal
    base = base + banda * np.array([60, 55, 40])
    vet = (np.sin((x * 1.2 - y) * 90) * 0.5 + 0.5)[..., None] * 10            # vetas finas
    base = (base + vet) * np.array(tono)
    return Image.fromarray(np.clip(base, 0, 255).astype(np.uint8)).convert("RGBA")


def carta(clave, ovr=None, brillo=None):
    nombre, pos, pais, club, st = datos(clave)
    if ovr is None:
        ovr = int(round(np.mean(sorted(st)[2:]) + 4))
    stats = st if ovr < 95 else tuple(min(99, s + (99 - max(st))) for s in st)
    if ovr >= 99:
        stats = (99,) * 4 + stats[4:]
    w, h = CW, CH
    mask = Image.new("L", (w * 2, h * 2), 0)
    ImageDraw.Draw(mask).polygon([(x * 2, y * 2) for x, y in forma(w, h)], fill=255)
    mask = mask.resize((w, h), Image.LANCZOS)
    c = oro(w, h)
    d = ImageDraw.Draw(c)
    # marco interior en relieve
    d.line([(x * 0.94 + w * 0.03, y * 0.95 + h * 0.022) for x, y in forma(w, h)] + [(forma(w, h)[0][0] * 0.94 + w * 0.03, h * 0.022)],
           fill=(255, 246, 200, 255), width=5)
    d.line([(x * 0.94 + w * 0.03, y * 0.95 + h * 0.022 + 5) for x, y in forma(w, h)], fill=(160, 115, 30, 160), width=3)
    # jugador: recortado, abajo se funde con la carta
    jug = recorte_jugador(clave)
    s = 430 / jug.width
    jug = jug.resize((430, int(jug.height * s)), Image.LANCZOS)
    if jug.height > 470:
        jug = jug.crop((0, 0, 430, 470))
    a = np.asarray(jug.split()[3]).astype(np.float32)
    fade = np.clip((jug.height - np.arange(jug.height)) / 70, 0, 1)[:, None]
    jug.putalpha(Image.fromarray((a * fade).astype(np.uint8)))
    sombra = Image.new("RGBA", jug.size, (90, 60, 0, 0)); sombra.putalpha(jug.split()[3].point(lambda v: v // 3))
    c.alpha_composite(sombra.filter(ImageFilter.GaussianBlur(8)), (w - 430 - 4, 70))
    c.alpha_composite(jug, (w - 430 - 18, 60))
    d = ImageDraw.Draw(c)
    # media, posición, bandera, escudo
    oscuro = (62, 42, 6)
    d.text((112, 150), str(ovr), font=f(150), fill=oscuro, anchor="mm")
    d.text((112, 250), pos, font=f(58), fill=oscuro, anchor="mm")
    d.line((70, 292, 154, 292), fill=(150, 110, 30), width=3)
    if pais:
        try:
            import banderas as B
            fl = Image.open(B.png(pais, 160)).convert("RGBA").resize((86, 86), Image.LANCZOS)
            c.alpha_composite(fl, (69, 305))
        except Exception:
            pass
    if club and (ROOT / "assets" / "escudos" / f"{club}.png").exists():
        es = Image.open(ROOT / "assets" / "escudos" / f"{club}.png").convert("RGBA")
        es.thumbnail((86, 86), Image.LANCZOS)
        c.alpha_composite(es, (112 - es.width // 2, 410))
    d = ImageDraw.Draw(c)
    # nombre
    tam = 74
    while f(tam).getlength(nombre) > w - 110 and tam > 36:
        tam -= 3
    d.text((w / 2, 578), nombre, font=f(tam), fill=oscuro, anchor="mm")
    d.line((95, 625, w - 95, 625), fill=(150, 110, 30), width=3)
    etiquetas = ["PAC", "SHO", "PAS", "DRI", "DEF", "PHY"]
    for k in range(6):
        col, fila = k // 3, k % 3
        x = 150 + col * 225; y = 668 + fila * 52
        d.text((x - 8, y), str(stats[k]), font=f(50), fill=oscuro, anchor="rm")
        d.text((x + 6, y), etiquetas[k], font=f(44), fill=(95, 68, 15), anchor="lm")
    d.line((w / 2, 645, w / 2, 790), fill=(150, 110, 30), width=3)
    # brillo que barre la carta (animable)
    if brillo is not None:
        sh = Image.new("RGBA", (w, h)); ds = ImageDraw.Draw(sh)
        x0 = -300 + brillo * (w + 600)
        ds.polygon([(x0, 0), (x0 + 120, 0), (x0 - 200, h), (x0 - 320, h)], fill=(255, 255, 255, 120))
        c.alpha_composite(sh.filter(ImageFilter.GaussianBlur(14)))
    c.putalpha(mask)
    # borde exterior + resplandor
    out = Image.new("RGBA", (w + 60, h + 60))
    glow = Image.new("L", (w + 60, h + 60), 0); glow.paste(mask, (30, 30))
    halo = Image.new("RGBA", (w + 60, h + 60), (255, 220, 90, 0)); halo.putalpha(glow.filter(ImageFilter.GaussianBlur(16)).point(lambda v: int(v * 0.8)))
    out.alpha_composite(halo); out.alpha_composite(c, (30, 30))
    return out


def misterio(ovr=99, brillo=None):
    """Carta dorada tapada: media visible, jugador en '?' (para el gancho del cuadro 0)."""
    w, h = CW, CH
    mask = Image.new("L", (w * 2, h * 2), 0)
    ImageDraw.Draw(mask).polygon([(x * 2, y * 2) for x, y in forma(w, h)], fill=255)
    mask = mask.resize((w, h), Image.LANCZOS)
    c = oro(w, h); d = ImageDraw.Draw(c)
    d.line([(x * 0.94 + w * 0.03, y * 0.95 + h * 0.022) for x, y in forma(w, h)], fill=(255, 246, 200, 255), width=5)
    d.text((112, 150), str(ovr), font=f(150), fill=(62, 42, 6), anchor="mm")
    d.ellipse((230, 110, 520, 400), fill=(70, 48, 8, 255))
    d.rounded_rectangle((180, 360, 570, 560), 120, fill=(70, 48, 8, 255))
    d.text((375, 300), "?", font=f(230), fill=(255, 225, 120), anchor="mm")
    d.text((w / 2, 620), "???", font=f(80), fill=(62, 42, 6), anchor="mm")
    if brillo is not None:
        sh = Image.new("RGBA", (w, h)); ds = ImageDraw.Draw(sh)
        x0 = -300 + brillo * (w + 600)
        ds.polygon([(x0, 0), (x0 + 120, 0), (x0 - 200, h), (x0 - 320, h)], fill=(255, 255, 255, 140))
        c.alpha_composite(sh.filter(ImageFilter.GaussianBlur(14)))
    c.putalpha(mask)
    out = Image.new("RGBA", (w + 60, h + 60))
    glow = Image.new("L", (w + 60, h + 60), 0); glow.paste(mask, (30, 30))
    halo = Image.new("RGBA", (w + 60, h + 60), (255, 220, 90, 0)); halo.putalpha(glow.filter(ImageFilter.GaussianBlur(16)))
    out.alpha_composite(halo); out.alpha_composite(c, (30, 30))
    return out


if __name__ == "__main__":
    k = sys.argv[1] if len(sys.argv) > 1 else "cristiano_ronaldo"
    o = int(sys.argv[2]) if len(sys.argv) > 2 else None
    (ROOT / "salida").mkdir(exist_ok=True)
    carta(k, o, 0.4).save(ROOT / "salida" / "carta_prueba.png")
    print(ROOT / "salida" / "carta_prueba.png")
