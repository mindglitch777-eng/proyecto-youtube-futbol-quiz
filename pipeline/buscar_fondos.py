#!/usr/bin/env python3
"""Baja fondos de estadio/cancha en alta resolución (DuckDuckGo Imágenes) para los formatos con recortes.
Guarda produccion/assets/fondos/estadio_<k>.jpg (verticales o recortables a 9:16) + indice.json. Corre en GitHub Actions."""
import io, json, time
from pathlib import Path
import requests
from PIL import Image
RAIZ = Path(__file__).resolve().parents[1]; OUT = RAIZ / "produccion" / "assets" / "fondos"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124 Safari/537.36"}
QS = ["empty football stadium", "empty soccer stadium pitch wide angle", "stadium interior empty seats green pitch",
      "Camp Nou empty stadium", "Santiago Bernabeu empty stadium", "Wembley stadium empty pitch", "empty stadium night lights football",
      "football stadium pitch from center circle empty"]
import cv2, numpy as np
_det = cv2.FaceDetectorYN.create(str(RAIZ / "produccion" / "assets" / "modelos" / "face_detection_yunet_2023mar.onnx"), "", (320, 320), 0.6)


def hay_gente(im):
    a = cv2.cvtColor(np.asarray(im.resize((im.width // 2, im.height // 2))), cv2.COLOR_RGB2BGR)
    _det.setInputSize((a.shape[1], a.shape[0])); _, f = _det.detect(a)
    return f is not None and len(f) > 0


def tiene_cancha(im):
    """Verde de pasto en la mitad de abajo (descarta pelotas, fútbol americano en primer plano, etc.)."""
    a = np.asarray(im.resize((90, 160)))[80:].astype(int)
    verde = (a[..., 1] > a[..., 0] + 15) & (a[..., 1] > a[..., 2] + 10)
    return verde.mean() > 0.35
def main():
    from ddgs import DDGS
    OUT.mkdir(parents=True, exist_ok=True); idx = {}; k = 0
    for v in OUT.glob("estadio_*.jpg"): v.unlink()
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
            if min(im.size) < 1000 or hay_gente(im) or not tiene_cancha(im): continue
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
