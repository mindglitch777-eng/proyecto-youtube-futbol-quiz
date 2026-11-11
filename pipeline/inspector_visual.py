#!/usr/bin/env python3
"""
INSPECTOR VISUAL (máquina, sin IA · 11/11): revisa cada video ANTES de que salga, buscando los defectos que un humano ve y
que se nos escaparon (📌 el rectángulo negro del DRESS, el "hueco" del BALLON D'OR, el precio que tocaba el borde).
Mira un cuadro cada 0,25 s y busca:
1. Rectángulo negro: una mancha negra pura, grande y rectangular en el medio de la imagen (un recorte o una foto rota).
2. Pantalla congelada: más de 1,5 s sin ningún cambio (en un Short es una invitación a deslizar).
3. Cuadro vacío: un cuadro casi liso (negro, blanco o de un solo color), que suele ser un error de render.
(El texto cortado se previene al dibujar: los carteles achican la letra hasta que entra.)
Devuelve la lista de defectos (vacía = pasa). La usa el control de la fábrica (e5_produccion.py), que rehace el video con
otra combinación si no pasa, y la fábrica de prototipos. Guarda el historial en datos/inspeccion.json para el Gerente.
Uso: python3 pipeline/inspector_visual.py video.mp4 [tipo]
"""
import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np

RAIZ = Path(__file__).resolve().parents[1]
W, H = 270, 480                      # se analiza achicado (rápido y suficiente para ver defectos grandes)
PASO = 0.25
SIN_TEXTO_AMARILLO = {"dress"}       # su fondo es amarillo: el chequeo de texto no aplica


def cuadros(ruta):
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", str(ruta), "-vf", f"fps={1 / PASO},scale={W}:{H}", "-f", "rawvideo",
                          "-pix_fmt", "rgb24", "-"], capture_output=True, timeout=300).stdout
    n = len(raw) // (W * H * 3)
    return np.frombuffer(raw[: n * W * H * 3], np.uint8).reshape(n, H, W, 3)


def rectangulos_negros(f):
    """Parche oscuro, LISO y rectangular (📌 DRESS: un rectángulo gris oscuro en el pecho, pegado abajo). Los carteles nuestros
    también son oscuros, pero tienen texto adentro (no son lisos) y están arriba: no cuentan."""
    import cv2
    gris = f.astype(np.int16).max(axis=2)
    oscuro = (gris < 55).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(oscuro, 8)
    malos = []
    for k in range(1, n):
        x, y, w, h, a = st[k]
        if a < 0.006 * W * H or y < 0.12 * H or x == 0 or x + w >= W:          # chico, en la franja de arriba o pegado a los costados
            continue
        if a / max(1, w * h) < 0.85 or min(w, h) < 8:                          # no es un rectángulo
            continue
        zona = f[y:y + h, x:x + w][lab[y:y + h, x:x + w] == k]
        if zona.std() < 7:                                                     # liso: no es un cartel con texto ni ropa con detalle
            malos.append((int(x), int(y), int(w), int(h)))
    return malos


def inspeccionar(ruta, tipo=None):
    fr = cuadros(ruta)
    if len(fr) < 4:
        return ["no se pudo leer el video"]
    defectos = []
    rect = [i for i, f in enumerate(fr) if rectangulos_negros(f)]
    if len(rect) >= max(2, len(fr) // 10):
        defectos.append(f"rectángulo negro en {len(rect)} de {len(fr)} cuadros (desde {rect[0] * PASO:.1f} s)")
    dif = np.abs(np.diff(fr.astype(np.int16), axis=0)).mean(axis=(1, 2, 3))
    quieto, peor = 0, 0
    for d in dif:
        quieto = quieto + 1 if d < 0.4 else 0
        peor = max(peor, quieto)
    if peor * PASO > 1.5:
        defectos.append(f"pantalla congelada {peor * PASO:.1f} s")
    vacios = [i for i, f in enumerate(fr) if f.std() < 6]
    if vacios:
        defectos.append(f"{len(vacios)} cuadros casi lisos (desde {vacios[0] * PASO:.1f} s)")
    return defectos


def anotar(vid, tipo, defectos):
    p = RAIZ / "pipeline" / "datos" / "inspeccion.json"
    try:
        hist = json.loads(p.read_text()) if p.exists() else []
    except Exception:
        hist = []
    hist.append(dict(id=vid, tipo=tipo, fecha=datetime.now(timezone(timedelta(hours=-3))).isoformat(timespec="minutes"), defectos=defectos))
    p.write_text(json.dumps(hist[-300:], ensure_ascii=False, indent=1))


if __name__ == "__main__":
    d = inspeccionar(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
    print("PASA" if not d else "DEFECTOS:\n- " + "\n- ".join(d))
