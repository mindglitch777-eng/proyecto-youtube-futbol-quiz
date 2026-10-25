#!/usr/bin/env python3
"""Fotos de perfil del canal FUTBOL EDITION (800x800). Se ven en un círculo de ~100 px: el monograma tiene que leerse chico."""
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
ANTON = str(ROOT / "assets/fuentes/Anton-Regular.ttf")
ARCHIVO = str(ROOT / "assets/fuentes/ArchivoBlack-Regular.ttf")
N = 800
OUT = Path(__file__).resolve().parent


def radial(c1, c2, cx=0.5, cy=0.42):
    y, x = np.indices((N, N), dtype=np.float32) / N
    d = np.clip(np.sqrt((x - cx) ** 2 + (y - cy) ** 2) / 0.75, 0, 1)[..., None]
    return Image.fromarray((np.array(c1) * (1 - d) + np.array(c2) * d).astype(np.uint8), "RGB")


def pelota(d, fondo=(255, 255, 255), panel=(16, 16, 16)):
    """Pelota clásica: pentágono central + 5 pentágonos cortados por el borde."""
    k = 4; D = d * k
    im = Image.new("RGBA", (D, D), (0, 0, 0, 0)); dr = ImageDraw.Draw(im)
    dr.ellipse((0, 0, D - 1, D - 1), fill=fondo)
    c = D / 2

    def penta(cx, cy, r, rot):
        return [(cx + r * math.cos(rot + i * 2 * math.pi / 5), cy + r * math.sin(rot + i * 2 * math.pi / 5)) for i in range(5)]
    r0 = D * 0.125
    dr.polygon(penta(c, c, r0, -math.pi / 2), fill=panel)
    for i in range(5):
        a = -math.pi / 2 + i * 2 * math.pi / 5
        px, py = c + math.cos(a) * D * 0.43, c + math.sin(a) * D * 0.43
        dr.polygon(penta(px, py, r0 * 0.95, a + math.pi / 2), fill=panel)
        # costuras
        dr.line((c + math.cos(a) * r0, c + math.sin(a) * r0, c + math.cos(a) * D * 0.33, c + math.sin(a) * D * 0.33), fill=panel, width=int(D * 0.014))
    m = Image.new("L", (D, D), 0); ImageDraw.Draw(m).ellipse((0, 0, D - 1, D - 1), fill=255)
    im.putalpha(Image.fromarray(np.minimum(np.array(im.getchannel("A")), np.array(m))))
    sombra = Image.new("RGBA", (D, D), (0, 0, 0, 0)); ImageDraw.Draw(sombra).ellipse((D * 0.12, D * 0.12, D * 1.1, D * 1.1), fill=(0, 0, 0, 28))
    sombra.putalpha(Image.fromarray(np.minimum(np.array(sombra.getchannel("A")), np.array(m))))
    im.alpha_composite(sombra)
    return im.resize((d, d), Image.LANCZOS)


def texto_centrado(dr, xy, s, f, fill, borde=0, borde_col=(0, 0, 0)):
    dr.text(xy, s, font=f, fill=fill, anchor="mm", stroke_width=borde, stroke_fill=borde_col)


def anillo_texto(im, s, r, f, col, inicio=-90):
    """Texto en arco alrededor del centro."""
    dr = ImageDraw.Draw(im)
    total = sum(f.getlength(ch) for ch in s)
    ang = inicio - math.degrees(total / r) / 2
    for ch in s:
        w = f.getlength(ch)
        a = math.radians(ang + math.degrees(w / 2 / r))
        x, y = N / 2 + r * math.cos(a), N / 2 + r * math.sin(a)
        letra = Image.new("RGBA", (int(w * 2 + 20), int(f.size * 2)), (0, 0, 0, 0))
        ImageDraw.Draw(letra).text((letra.width / 2, letra.height / 2), ch, font=f, fill=col, anchor="mm")
        letra = letra.rotate(-math.degrees(a) - 90, resample=Image.BICUBIC, expand=True)
        im.alpha_composite(letra, (int(x - letra.width / 2), int(y - letra.height / 2)))
        ang += math.degrees(w / r)


def opcion_a():
    """Escudo-sello: monograma FE dorado sobre verde cancha, pelota detrás y texto en anillo."""
    im = radial((26, 120, 70), (4, 30, 18)).convert("RGBA")
    dr = ImageDraw.Draw(im)
    for i in range(-2, 12):   # franjas de césped cortado
        if i % 2:
            dr.polygon([(i * 90, 0), (i * 90 + 90, 0), (i * 90 - 210, N), (i * 90 - 300, N)], fill=(255, 255, 255, 14))
    b = pelota(430); im.alpha_composite(b.rotate(18, resample=Image.BICUBIC), (N // 2 - 215, N // 2 - 250))
    velo = Image.new("RGBA", (N, N), (6, 40, 24, 70)); im.alpha_composite(velo)
    dr = ImageDraw.Draw(im)
    texto_centrado(dr, (N / 2, N / 2 - 20), "FE", ImageFont.truetype(ANTON, 420), (255, 205, 60), 14, (10, 20, 12))
    dr.ellipse((38, 38, N - 38, N - 38), outline=(255, 205, 60), width=10)
    anillo_texto(im, "FUTBOL • EDITION", 318, ImageFont.truetype(ARCHIVO, 54), (255, 255, 255), inicio=90 + 180)
    return im


def opcion_b():
    """Pop: amarillo eléctrico, pelota grande y 'FE' en negro con contorno blanco. Lo más llamativo en el feed."""
    im = radial((255, 226, 40), (255, 150, 0)).convert("RGBA")
    dr = ImageDraw.Draw(im)
    for r in range(80, 620, 70):   # ondas de energía
        dr.ellipse((N / 2 - r, N / 2 - r, N / 2 + r, N / 2 + r), outline=(255, 255, 255, 40), width=6)
    b = pelota(250); im.alpha_composite(b.rotate(-20, resample=Image.BICUBIC), (N - 250 - 95, 95))
    dr = ImageDraw.Draw(im)
    texto_centrado(dr, (N / 2 - 20, N / 2 - 15), "FE", ImageFont.truetype(ANTON, 420), (15, 15, 15), 18, (255, 255, 255))
    texto_centrado(dr, (N / 2, N - 150), "FUTBOL EDITION", ImageFont.truetype(ARCHIVO, 50), (15, 15, 15), 6, (255, 255, 255))
    return im


def opcion_c():
    """Noche de estadio: azul profundo con reflectores, pelota-luna y 'FE' blanco con brillo cian."""
    im = radial((30, 50, 120), (4, 6, 22), cy=0.3).convert("RGBA")
    luz = Image.new("RGBA", (N, N), (0, 0, 0, 0)); dl = ImageDraw.Draw(luz)
    for x in (110, N - 110):   # haces de reflectores
        dl.polygon([(x, 0), (x - 160, N), (x + 160, N)], fill=(160, 220, 255, 40))
    im.alpha_composite(luz.filter(ImageFilter.GaussianBlur(30)))
    b = pelota(250); im.alpha_composite(b, (N // 2 - 125, 70))
    brillo = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    ImageDraw.Draw(brillo).text((N / 2, N / 2 + 150), "FE", font=ImageFont.truetype(ANTON, 360), fill=(80, 220, 255, 255), anchor="mm")
    im.alpha_composite(brillo.filter(ImageFilter.GaussianBlur(22)))
    dr = ImageDraw.Draw(im)
    texto_centrado(dr, (N / 2, N / 2 + 150), "FE", ImageFont.truetype(ANTON, 360), (255, 255, 255), 6, (10, 30, 70))
    return im


if __name__ == "__main__":
    vista = Image.new("RGB", (3 * 420, 470), (240, 240, 240)); dv = ImageDraw.Draw(vista)
    for i, (nombre, f) in enumerate((("A_sello_cancha", opcion_a), ("B_amarillo_pop", opcion_b), ("C_estadio_noche", opcion_c))):
        im = f().convert("RGB"); im.save(OUT / f"perfil_{nombre}.png")
        # vista previa en círculo como en YouTube (grande y chico)
        m = Image.new("L", (380, 380), 0); ImageDraw.Draw(m).ellipse((0, 0, 379, 379), fill=255)
        vista.paste(im.resize((380, 380), Image.LANCZOS), (i * 420 + 20, 10), m)
        m2 = Image.new("L", (48, 48), 0); ImageDraw.Draw(m2).ellipse((0, 0, 47, 47), fill=255)
        vista.paste(im.resize((48, 48), Image.LANCZOS), (i * 420 + 186, 405), m2)
        dv.text((i * 420 + 20, 412), nombre[0], font=ImageFont.truetype(ANTON, 36), fill=(30, 30, 30))
    vista.save(OUT / "perfil_opciones.png")
    print("listo")
