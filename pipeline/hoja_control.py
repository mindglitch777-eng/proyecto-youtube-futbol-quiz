#!/usr/bin/env python3
"""
HOJA DE CONTROL DIARIA (auditoría A4, 15/11): el inspector automático solo ve pantallas negras o congeladas; los defectos de
DISEÑO (parche negro de DRESS, medidor que contradice al "PERFECT!", nombre cortado, foto de otro jugador) los ve un ojo.
Arma una imagen con 4 cuadros de cada video del día (0,1 s · 30 % · 60 % · 90 %) con su formato y título. La fábrica la sube
al Release del día como control.jpg y el Gerente IA la mira cada día (gh release download semana-<fecha> -p control.jpg).
Uso: python3 pipeline/hoja_control.py produccion/semana_<fecha> [salida.jpg]
"""
import json
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 216, 384


def cuadro(mp4, t):
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-ss", f"{t:.2f}", "-i", str(mp4), "-frames:v", "1", "-vf", f"scale={W}:{H}",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    return Image.frombytes("RGB", (W, H), raw) if len(raw) == W * H * 3 else Image.new("RGB", (W, H), (60, 0, 0))


def dur(mp4):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(mp4)], capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 6.0


def main(carpeta, salida=None):
    carpeta = Path(carpeta)
    man = json.loads((carpeta / "videos.json").read_text()) if (carpeta / "videos.json").exists() else []
    man = man if isinstance(man, list) else man.get("videos", [])
    filas = [m for m in man if (carpeta / m["archivo"]).exists()]
    if not filas:
        print("sin videos"); return None
    fuente = ImageFont.load_default()
    hoja = Image.new("RGB", (4 * W + 50, len(filas) * (H + 34) + 10), (18, 18, 22))
    d = ImageDraw.Draw(hoja)
    for i, m in enumerate(filas):
        mp4 = carpeta / m["archivo"]; du = dur(mp4); y = 10 + i * (H + 34)
        d.text((10, y), f"{m.get('fecha', '')} {m.get('hora', '')} · {m.get('formato', m.get('tipo'))} · {m.get('titulo', '')[:90]}",
               fill=(255, 230, 120), font=fuente)
        for k, f in enumerate((0.1, 0.3 * du, 0.6 * du, 0.9 * du)):
            hoja.paste(cuadro(mp4, f), (10 + k * (W + 10), y + 20))
    salida = Path(salida or carpeta / "control.jpg")
    hoja.save(salida, quality=80)
    print(salida)
    return salida


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
