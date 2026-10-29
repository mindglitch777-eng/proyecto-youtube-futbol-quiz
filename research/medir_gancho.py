#!/usr/bin/env python3
"""
Mide de forma objetiva el gancho, el ritmo y el sonido de un short (nuestros y grabaciones de virales).
Sirve para comparar contra los virales y para revisar cada video antes de subirlo.

Uso: python3 research/medir_gancho.py lista.json salida.json
lista.json: [{"id": "...", "ruta": "...mp4", "grupo": "viral|nuestro", "recorte": [x0, y0, x1, y1] (opcional, fracciones), "se_quedo": 50.7 (opcional)}]
"""
import json
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np

MODELO = Path(__file__).resolve().parents[1] / "produccion" / "assets" / "modelos" / "face_detection_yunet_2023mar.onnx"
FPS = 10           # cuadros por segundo para el análisis
W, H = 360, 640    # tamaño normalizado
SR = 16000


def cuadros(ruta, recorte):
    cap = cv2.VideoCapture(str(ruta))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    paso = max(1, round(fps / FPS))
    out, n = [], 0
    while True:
        ok, f = cap.read()
        if not ok:
            break
        if n % paso == 0:
            if recorte:
                h, w = f.shape[:2]
                x0, y0, x1, y1 = recorte
                f = f[int(y0 * h):int(y1 * h), int(x0 * w):int(x1 * w)]
            out.append(cv2.resize(f, (W, H)))
        n += 1
    return out


def audio(ruta):
    r = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", str(ruta), "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                       capture_output=True)
    return np.frombuffer(r.stdout, dtype=np.float32)


def cara_max(det, f):
    det.setInputSize((f.shape[1], f.shape[0]))
    _, caras = det.detect(f)
    if caras is None:
        return 0.0
    return float(max(c[2] * c[3] for c in caras) / (f.shape[0] * f.shape[1]))


def colorido(f):
    b, g, r = [c.astype(float) for c in cv2.split(f)]
    rg, yb = r - g, 0.5 * (r + g) - b
    return float(np.hypot(rg.std(), yb.std()) + 0.3 * np.hypot(rg.mean(), yb.mean()))


def medir(item, det):
    fs = cuadros(item["ruta"], item.get("recorte"))
    if not fs:
        return None
    dur = len(fs) / FPS
    gris = [cv2.cvtColor(f, cv2.COLOR_BGR2GRAY).astype(np.int16) for f in fs]
    dif = np.array([np.abs(gris[i] - gris[i - 1]).mean() for i in range(1, len(gris))])
    cortes = np.where(dif > 28)[0]                       # cambio de escena / golpe visual fuerte
    eventos = np.where(dif > 10)[0]                      # algo grande pasa en pantalla
    f0 = fs[0]
    hsv = cv2.cvtColor(f0, cv2.COLOR_BGR2HSV)
    bordes = cv2.Canny(cv2.cvtColor(f0, cv2.COLOR_BGR2GRAY), 80, 160)
    caras = [cara_max(det, fs[min(i, len(fs) - 1)]) for i in (0, 5, 10)]

    a = audio(item["ruta"])
    m = {}
    if len(a):
        hop = SR // 50                                   # ventanas de 20 ms
        rms = np.sqrt(np.convolve(a ** 2, np.ones(hop) / hop, "valid")[::hop] + 1e-12)
        db = 20 * np.log10(rms + 1e-9)
        sonando = db > -35
        primer = float(np.argmax(sonando) / 50) if sonando.any() else None
        # golpes de sonido: subidas bruscas de energía
        flux = np.diff(db)
        golpes = np.where((flux > 9) & (db[1:] > -30))[0]
        golpes = golpes[np.insert(np.diff(golpes) > 5, 0, True)] if len(golpes) else golpes
        silencio, maxsil = 0, 0
        for s in sonando:
            silencio = 0 if s else silencio + 1
            maxsil = max(maxsil, silencio)
        m = dict(audio_primer_sonido_s=primer, audio_db_medio=round(float(db[sonando].mean()) if sonando.any() else -99, 1),
                 audio_golpes_por_s=round(len(golpes) / max(dur, 1), 2),
                 audio_golpes_primeros_3s=int((golpes < 150).sum()),
                 audio_silencio_max_s=round(maxsil / 50, 2))

    return dict(
        id=item["id"], grupo=item["grupo"], se_quedo=item.get("se_quedo"), duracion_s=round(dur, 1),
        f0_brillo=round(float(hsv[..., 2].mean()), 1), f0_saturacion=round(float(hsv[..., 1].mean()), 1),
        f0_colorido=round(colorido(f0), 1), f0_detalle=round(float((bordes > 0).mean() * 100), 1),
        cara_max_pct_0s=round(caras[0] * 100, 1), cara_max_pct_1s=round(max(caras) * 100, 1),
        mov_0_1s=round(float(dif[:FPS].mean()), 1) if len(dif) else 0, mov_medio=round(float(dif.mean()), 1),
        cortes_por_10s=round(len(cortes) / dur * 10, 1), eventos_por_s=round(len(eventos) / dur, 2),
        seg_sin_evento_max=round(float(np.diff(np.concatenate([[0], eventos, [len(dif)]])).max() / FPS), 1),
        loop_dif_final_inicio=round(float(np.abs(gris[-1] - gris[0]).mean()), 1),
        **m)


def main():
    lista = json.loads(Path(sys.argv[1]).read_text())
    det = cv2.FaceDetectorYN.create(str(MODELO), "", (W, H), 0.6)
    res = []
    for it in lista:
        r = medir(it, det)
        if r:
            res.append(r)
            print(json.dumps(r, ensure_ascii=False), flush=True)
    Path(sys.argv[2]).write_text(json.dumps(res, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
