#!/usr/bin/env python3
"""
Busca PNG sin fondo de OBJETOS para los formatos nuevos (trofeo del Balón de Oro, Cristiano en el SIUUU, arco, arquero, pelota).
Igual que buscar_recortes.py (DuckDuckGo Imágenes, filtro "transparent"), pero sin exigir cara de frente.
Pedido: pipeline/pedido_extras.json {"clave": {"consultas": [...], "n": 6, "min_lado": 500}}
Guarda: produccion/assets/recortes/extras/<clave>_<k>.png + extras/hoja.jpg (para elegir a ojo) + extras/indice.json
Corre en GitHub Actions (desde la nube de Claude no se llega a los sitios de imágenes).
"""
import io
import json
import time
from pathlib import Path

import numpy as np
import requests
from PIL import Image, ImageDraw

RAIZ = Path(__file__).resolve().parents[1]
OUT = RAIZ / "produccion" / "assets" / "recortes" / "extras"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36"}


def buscar(q, n=60):
    from ddgs import DDGS
    for intento in range(4):
        try:
            return [r["image"] for r in DDGS().images(q, max_results=n, type_image="transparent", size="Large") if r.get("image")]
        except Exception as e:
            print("  búsqueda falló", q, e, flush=True); time.sleep(8 * (intento + 1))
    return []


def bajar(url, min_lado):
    try:
        r = requests.get(url, headers=UA, timeout=25)
        if r.status_code != 200 or len(r.content) < 20_000:
            return None
        im = Image.open(io.BytesIO(r.content))
        if im.mode not in ("RGBA", "LA", "P"):
            return None
        im = im.convert("RGBA")
        a = np.asarray(im)[..., 3]
        if (a < 10).mean() < 0.12 or (a > 245).mean() < 0.12:                 # transparencia real
            return None
        im = im.crop(im.getbbox())
        return im if min(im.size) >= min_lado else None
    except Exception:
        return None


def main():
    pedido = json.loads((RAIZ / "pipeline" / "pedido_extras.json").read_text())
    OUT.mkdir(parents=True, exist_ok=True)
    idx_p = OUT / "indice.json"
    indice = json.loads(idx_p.read_text()) if idx_p.exists() else {}
    for clave, cfg in pedido.items():
        if any(k.startswith(clave + "_") for k in indice):
            continue
        vistos, cand = set(), []
        for q in cfg["consultas"]:
            for url in buscar(q):
                if url in vistos:
                    continue
                vistos.add(url)
                im = bajar(url, cfg.get("min_lado", 500))
                if im is not None:
                    cand.append((im.width * im.height, url, im))
            time.sleep(2)
            if len(cand) >= cfg.get("n", 6) * 3:
                break
        cand.sort(key=lambda c: -c[0])
        for k, (_, url, im) in enumerate(cand[:cfg.get("n", 6)]):
            im.thumbnail((1400, 1400))
            im.save(OUT / f"{clave}_{k}.png")
            indice[f"{clave}_{k}"] = dict(url=url, tam=list(im.size))
        print(clave, "candidatos", len(cand), flush=True)
        idx_p.write_text(json.dumps(indice, ensure_ascii=False, indent=1))
    hoja()


def hoja():
    fs = sorted(OUT.glob("*_*.png"))
    if not fs:
        return
    th = 260; cols = 6; filas = (len(fs) + cols - 1) // cols
    out = Image.new("RGB", (250 * cols, (th + 30) * filas), (40, 40, 40))
    for i, f in enumerate(fs):
        im = Image.open(f).convert("RGBA"); im.thumbnail((240, th))
        tile = Image.new("RGBA", (250, th + 30), (255, 230, 0, 255)); tile.alpha_composite(im, ((250 - im.width) // 2, 0))
        ImageDraw.Draw(tile).text((5, th + 8), f.stem, fill=(0, 0, 0))
        out.paste(tile.convert("RGB"), ((i % cols) * 250, (i // cols) * (th + 30)))
    out.save(OUT / "hoja.jpg", quality=80)


if __name__ == "__main__":
    main()
