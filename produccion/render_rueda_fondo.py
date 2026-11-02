"""Fondo de reserva para WHEEL STOP (cielo + tribunas + cancha), si no hay foto de estadio bajada."""
import numpy as np
from PIL import Image, ImageDraw

W, H = 1080, 1920


def dibujado():
    y = np.linspace(0, 1, H)[:, None]
    cielo = np.array([70, 150, 230]) * (1 - y) + np.array([190, 225, 250]) * y
    im = Image.fromarray(np.repeat(cielo[:, None, :], W, 1).astype(np.uint8)).convert("RGBA"); d = ImageDraw.Draw(im)
    d.rectangle((0, 900, W, 1180), fill=(70, 80, 95, 255))
    rng = np.random.default_rng(3)
    for _ in range(5000):
        x, yy = rng.uniform(0, W), rng.uniform(910, 1170)
        d.rectangle((x, yy, x + 3, yy + 4), fill=tuple(int(v) for v in rng.choice([[230, 60, 60], [240, 240, 240], [60, 120, 230], [250, 210, 60]])) + (200,))
    d.rectangle((0, 1180, W, H), fill=(60, 150, 60, 255))
    for k in range(12):
        if k % 2:
            d.rectangle((0, 1180 + k * 70, W, 1250 + k * 70), fill=(75, 168, 70, 255))
    return im
