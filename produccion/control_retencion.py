#!/usr/bin/env python3
"""
Control de retención: revisa un short ANTES de subirlo contra las reglas medibles de reports/24_reglas_de_retencion.md.
Los umbrales salen de comparar 11 virales con nuestros 7 shorts y su "se quedó a mirar" real (reports/24).

Uso: python3 produccion/control_retencion.py salida/runner_01/short.mp4 [otro.mp4 ...]
"""
import sys
from pathlib import Path

import cv2

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research"))
from medir_gancho import MODELO, W, H, medir  # noqa: E402

# (clave, cómo se lee, función que da True si pasa, por qué importa)
REGLAS = [
    ("f0_brillo", "brillo del cuadro 0 ≥ 130", lambda v: v >= 130,
     "virales: mediana 150; nuestros oscuros (52-71) son los que más se descartan"),
    ("cara_max_pct_0s", "cara más grande ≥ 3 % de la pantalla en el cuadro 0", lambda v: v >= 3,
     "virales: mediana 2,7 % y hasta 13 %; nuestras carreras 0,2-0,3 %"),
    ("mov_0_1s", "movimiento en el primer segundo ≥ 4", lambda v: v >= 4,
     "virales: mediana 5,2; nuestras carreras arrancan quietas (0,0)"),
    ("audio_primer_sonido_s", "suena algo desde el cuadro 0 (≤ 0,3 s)", lambda v: v is not None and v <= 0.3,
     "ningún viral arranca en silencio"),
    ("seg_sin_evento_max", "nunca más de 4 s sin un cambio grande en pantalla", lambda v: v <= 4,
     "rematch: 50 s sin cambios grandes, cae al final del 32 % al 8 %"),
    ("audio_silencio_max_s", "sin silencios de más de 0,8 s", lambda v: v <= 0.8,
     "el silencio es un permiso para deslizar"),
    ("duracion_s", "duración ≤ 25 s (FIND 12-18 s)", lambda v: v <= 25,
     "nuestro mejor % visto: FIND de 18 s (76,6 %)"),
]


def main():
    det = cv2.FaceDetectorYN.create(str(MODELO), "", (W, H), 0.6)
    for ruta in sys.argv[1:]:
        r = medir(dict(id=Path(ruta).parent.name, ruta=ruta, grupo="revision"), det)
        if not r:
            print(ruta, "no se pudo leer")
            continue
        fallas = 0
        print(f"\n== {ruta}")
        for clave, texto, ok, porque in REGLAS:
            v = r.get(clave)
            pasa = v is not None and ok(v)
            fallas += not pasa
            print(f"  {'OK   ' if pasa else 'FALLA'} {texto:52} (medido: {v})" + ("" if pasa else f"\n        → {porque}"))
        print(f"  RESULTADO: {'PASA' if not fallas else f'NO PASA ({fallas} reglas)'}")
        print("  Revisar a mano: pregunta/desafío visible en el cuadro 0, recompensa antes de 1,5 s, final sin cierre y que empalme con el inicio.")


if __name__ == "__main__":
    main()
