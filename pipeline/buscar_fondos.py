#!/usr/bin/env python3
"""Baja fondos de estadio/cancha en alta resolución (DuckDuckGo Imágenes) para los formatos con recortes.
Guarda produccion/assets/fondos/estadio_<k>.jpg (verticales o recortables a 9:16) + indice.json. Corre en GitHub Actions."""
import io, json, time
from pathlib import Path
import requests
from PIL import Image
RAIZ = Path(__file__).resolve().parents[1]; OUT = RAIZ / "produccion" / "assets" / "fondos"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124 Safari/537.36"}
QS = ["football stadium pitch background 4k", "soccer stadium grass wallpaper vertical", "empty football stadium pitch hd",
      "stadium background for editing football", "soccer field stadium lights wallpaper 4k"]
def main():
    from ddgs import DDGS
    OUT.mkdir(parents=True, exist_ok=True); idx = {}; k = 0
    for q in QS:
        try:
            res = DDGS().images(q, max_results=40, size="Wallpaper", type_image="photo")
        except Exception as e:
            print("falló", q, e); time.sleep(10); continue
        for r in res:
            if k >= 16: break
            try:
                b = requests.get(r["image"], headers=UA, timeout=25)
                im = Image.open(io.BytesIO(b.content)).convert("RGB")
            except Exception:
                continue
            if min(im.size) < 1000: continue
            w, h = im.size; nw = min(w, int(h * 9 / 16))                          # recorte 9:16 del centro
            im = im.crop(((w - nw) // 2, 0, (w - nw) // 2 + nw, h)).resize((1080, 1920), Image.LANCZOS)
            im.save(OUT / f"estadio_{k}.jpg", quality=90); idx[f"estadio_{k}"] = r["image"]; k += 1
        time.sleep(3)
    (OUT / "indice.json").write_text(json.dumps(idx, indent=1))
    hoja = Image.new("RGB", (270 * 8, 480 * 2), (30, 30, 30))
    for i in range(min(k, 16)):
        hoja.paste(Image.open(OUT / f"estadio_{i}.jpg").resize((270, 480)), ((i % 8) * 270, (i // 8) * 480))
    hoja.save(OUT / "hoja.jpg", quality=80); print(k, "fondos")
if __name__ == "__main__":
    main()
