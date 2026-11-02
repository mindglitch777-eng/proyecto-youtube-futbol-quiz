#!/usr/bin/env python3
"""
Busca en internet (DuckDuckGo Imágenes, filtro "transparent") PNGs de jugadores DE FRENTE y sin fondo, los descarga y se
queda solo con los buenos: 1 cara grande y de frente, transparencia real, alta resolución y cuerpo debajo de la cara.
Guarda:  produccion/assets/recortes/torsos/<clave>_<k>.png  (de la cabeza a la cintura)
         produccion/assets/recortes/cuerpos/<clave>_<k>.png (cuerpo entero, si la imagen llega a los pies)
         produccion/assets/recortes/hoja.jpg (hoja de control) + indice.json (origen de cada imagen)
Corre en GitHub Actions (desde la nube de Claude no se llega a los sitios de imágenes).
Pedido: pipeline/pedido_recortes.json {"jugadores": {"cristiano_ronaldo": "Cristiano Ronaldo", ...}, "por_jugador": 4}
"""
import io
import json
import sys
import time
from pathlib import Path

import cv2
import numpy as np
import requests
from PIL import Image

RAIZ = Path(__file__).resolve().parents[1]
OUT = RAIZ / "produccion" / "assets" / "recortes"
MODELO = RAIZ / "produccion" / "assets" / "modelos" / "face_detection_yunet_2023mar.onnx"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36"}
CONSULTAS = ["{n} png", "{n} png transparent", "{n} jersey png", "{n} full body png", "{n} 2025 png"]


def buscar(q, n=60):
    from ddgs import DDGS
    for intento in range(4):
        try:
            res = DDGS().images(q, max_results=n, type_image="transparent", size="Large")
            return [r.get("image") for r in res if r.get("image")]
        except Exception as e:
            print("  búsqueda falló", q, e, flush=True); time.sleep(8 * (intento + 1))
    return []


def bajar(url):
    try:
        r = requests.get(url, headers=UA, timeout=25)
        if r.status_code != 200 or len(r.content) < 30_000:
            return None
        im = Image.open(io.BytesIO(r.content))
        if im.mode not in ("RGBA", "LA", "P"):
            return None
        im = im.convert("RGBA")
        a = np.asarray(im)[..., 3]
        if (a < 10).mean() < 0.15 or (a > 245).mean() < 0.15:                 # tiene que tener fondo transparente de verdad
            return None
        return im
    except Exception:
        return None


def evaluar(im, det):
    """Puntaje (o None): cara de frente, grande, arriba, con cuerpo debajo."""
    rgba = np.asarray(im)
    a = rgba[..., 3]
    ys, xs = np.nonzero(a > 30)
    if len(ys) < 1000:
        return None
    bgr = cv2.cvtColor(rgba[..., :3], cv2.COLOR_RGB2BGR)
    bgr[a < 30] = 255
    h, w = bgr.shape[:2]
    det.setInputSize((w, h))
    _, f = det.detect(bgr)
    if f is None or len(f) != 1:
        return None
    x, y, fw, fh = f[0][:4]
    ojo_d, ojo_i, nariz = f[0][4:6], f[0][6:8], f[0][8:10]
    simetria = abs((nariz[0] - ojo_d[0]) - (ojo_i[0] - nariz[0])) / max(fw, 1)      # 0 = de frente
    if fh < 90 or simetria > 0.18:
        return None
    abajo = (ys.max() - (y + fh)) / fh                                          # cuántas caras de cuerpo hay debajo
    if abajo < 2.2:
        return None
    return dict(score=float(fh * (1 - simetria) + min(abajo, 6) * 20), cara=[float(x), float(y), float(fw), float(fh)],
                abajo=float(abajo), simetria=float(simetria))


def main():
    pedido = json.loads((RAIZ / "pipeline" / "pedido_recortes.json").read_text())
    global CONSULTAS
    solo_cuerpos = pedido.get("solo_cuerpos", False)
    if solo_cuerpos:                                                          # piernas: cuerpo entero, parado y de frente
        CONSULTAS = ["{n} full body png", "{n} standing full body png transparent", "{n} png full body front",
                     "{n} posing full body png", "{n} render png full body"]
    n_max = pedido.get("por_jugador", 4)
    (OUT / "torsos").mkdir(parents=True, exist_ok=True); (OUT / "cuerpos").mkdir(parents=True, exist_ok=True)
    det = cv2.FaceDetectorYN.create(str(MODELO), "", (320, 320), 0.7)
    idx_path = OUT / "indice.json"
    indice = json.loads(idx_path.read_text()) if idx_path.exists() else {}
    for clave, nombre in pedido["jugadores"].items():
        if not solo_cuerpos and len([k for k in indice if k.startswith(clave + "_")]) >= n_max:
            continue
        vistos, cand = set(), []
        for q in CONSULTAS:
            for url in buscar(q.format(n=nombre)):
                if url in vistos:
                    continue
                vistos.add(url)
                im = bajar(url)
                if im is None:
                    continue
                ev = evaluar(im, det)
                if ev and solo_cuerpos and ev["abajo"] < 6.3:
                    ev = None
                if ev:
                    cand.append((ev["score"], url, im, ev))
            time.sleep(2)
            if len(cand) >= n_max * 3:
                break
        cand.sort(key=lambda c: -c[0])
        k = 10 if solo_cuerpos else 0                                          # los cuerpos nuevos van como _10, _11...
        for score, url, im, ev in cand[:n_max]:
            x, y, fw, fh = ev["cara"]
            bb = im.getbbox()
            torso = im.crop((bb[0], bb[1], bb[2], int(min(bb[3], y + fh * 4.2))))
            torso.save(OUT / "torsos" / f"{clave}_{k}.png")
            if ev["abajo"] >= 6.0:
                im.crop(bb).save(OUT / "cuerpos" / f"{clave}_{k}.png")
            indice[f"{clave}_{k}"] = dict(jugador=nombre, url=url, score=round(score, 1), abajo=round(ev["abajo"], 1),
                                          cuerpo_entero=ev["abajo"] >= 6.0)
            k += 1
        print(clave, "candidatos:", len(cand), "guardados:", k, flush=True)
        idx_path.write_text(json.dumps(indice, ensure_ascii=False, indent=1))
    hoja()


def hoja():
    """Hoja de control: todos los torsos guardados, en filas, para elegir a ojo."""
    fs = sorted((OUT / "torsos").glob("*.png"))
    if not fs:
        return
    th = 300; filas, fila, ancho = [], [], 0
    for f in fs:
        im = Image.open(f).convert("RGBA"); im.thumbnail((240, th))
        tile = Image.new("RGBA", (250, th + 30), (255, 230, 0, 255)); tile.alpha_composite(im, ((250 - im.width) // 2, 0))
        from PIL import ImageDraw
        ImageDraw.Draw(tile).text((5, th + 8), f.stem, fill=(0, 0, 0))
        fila.append(tile)
        if len(fila) == 8:
            filas.append(fila); fila = []
    if fila:
        filas.append(fila)
    hoja_im = Image.new("RGB", (250 * 8, (th + 30) * len(filas)), (40, 40, 40))
    for r, fl in enumerate(filas):
        for c, t in enumerate(fl):
            hoja_im.paste(t.convert("RGB"), (c * 250, r * (th + 30)))
    hoja_im.save(OUT / "hoja.jpg", quality=80)


if __name__ == "__main__":
    main()
