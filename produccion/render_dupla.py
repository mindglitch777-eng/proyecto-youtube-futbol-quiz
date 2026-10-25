#!/usr/bin/env python3
"""
DUPLA · AGE EVOLUTION: dos jugadores con vínculo (compañeros, rivales) envejecen lado a lado, año a año, con morph.
Patrón de la competencia (Frox / Icon Stories: duplas de 1-2,5 M): edades y año en pantalla, sin voz, loop.
Uso: python3 render_dupla.py guiones/dupla_01.json  -> salida/<id>/short.mp4 y short_sin_musica.mp4
"""
import json
import subprocess
import sys
import wave
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw

from fusion import Fusion
from render_evolucion import EP, NACIDO, NACION, bandera, corto, fondo, fotos_de, ruta
from render_find_the_real import BLANCO, FPS, H, LED, SR, W, ROOT, ajustar, texto
from render_fusion import beat, efectos

LADO = 500
PYD = 600
XS = (26, W - 26 - LADO)


def panel(bgr):
    im = Image.fromarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)).resize((LADO, LADO), Image.LANCZOS)
    m = Image.new("L", (LADO, LADO), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, LADO - 1, LADO - 1), 36, fill=255)
    im.putalpha(m)
    return im


def main(guion_path):
    g = json.loads(Path(guion_path).read_text())
    ds = [fotos_de(j, g.get("max_puntaje", 120), g.get("min_cara", 90)) for j in g["jugadores"]]
    fil = [list(d.itertuples()) for d in ds]
    inicio = max(f[0].anio for f in fil)
    anios = sorted({x.anio for f in fil for x in f if x.anio >= inicio})
    # foto vigente de cada jugador en cada año (la última con fecha <= año)
    def vigente(f, a):
        return [x for x in f if x.anio <= a][-1]
    pasos = [[vigente(f, a) for f in fil] for a in anios]
    ref = [f[0].asimetria for f in fil]
    esp = lambda x, i: bool(x.asimetria * ref[i] < 0 and abs(x.asimetria) > 0.05)
    T_HOLD, T_MORPH, T_INTRO, T_FIN = 1.0, 0.8, 0.6, 3.0
    t_juego = (len(anios) - 1) * (T_HOLD + T_MORPH)
    dur = T_INTRO + t_juego + T_HOLD + T_FIN
    t_rev = T_INTRO + t_juego + T_HOLD
    nf = int(dur * FPS)
    out = ROOT / "salida" / g["id"]; out.mkdir(parents=True, exist_ok=True)
    fus = {}
    def fusion(i, a, b):
        k = (i, a.foto, b.foto)
        if k not in fus:
            fus[k] = Fusion(ruta(a), ruta(b), esp(a, i), esp(b, i), json.loads(a.cara), json.loads(b.cara))
        return fus[k]
    base = fondo()
    sonidos = [("whoosh", T_INTRO - 0.2)] + [("whoosh", T_INTRO + k * (T_HOLD + T_MORPH) + T_HOLD) for k in range(len(anios) - 1)]
    sonidos += [("riser", t_rev - 0.9), ("boom", t_rev), ("ding", t_rev + 0.05)]
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "19",
                           str(out / "mudo.mp4")], stdin=subprocess.PIPE)
    cache = {}
    nombres = [corto(j) for j in g["jugadores"]]
    for f in range(nf):
        tv = f / FPS
        tj = min(max(tv - T_INTRO, 0), t_juego)
        k = min(int(tj // (T_HOLD + T_MORPH)), len(anios) - 2) if len(anios) > 1 else 0
        u = min(max((tj - k * (T_HOLD + T_MORPH) - T_HOLD) / T_MORPH, 0), 1)
        u = 0.5 - 0.5 * np.cos(np.pi * u)
        anio = int(round(anios[k] + (anios[min(k + 1, len(anios) - 1)] - anios[k]) * u))
        im = base.copy(); dr = ImageDraw.Draw(im, "RGBA")
        texto(dr, (W / 2, 100), g["titulo"], ajustar(g["titulo"], 92, W - 60), LED, 10)
        texto(dr, (W / 2, 200), "AGE EVOLUTION", 70, BLANCO, 8)
        texto(dr, (W / 2, 370), str(anio), 170, BLANCO, 13)
        for i in range(2):
            a, b = pasos[k][i], pasos[min(k + 1, len(pasos) - 1)][i]
            uu = u if a.foto != b.foto else 0
            clave = (i, a.foto, b.foto, round(uu, 3))
            if clave not in cache:
                img = fusion(i, a, b).cuadro(uu) if a.foto != b.foto else fusion(i, a, a).cuadro(0)
                cache[clave] = panel(img)
                if len(cache) > 8:
                    cache.pop(next(iter(cache)))
            im.paste(cache[clave], (XS[i], PYD), cache[clave])
            dr.rounded_rectangle((XS[i] - 5, PYD - 5, XS[i] + LADO + 5, PYD + LADO + 5), 40,
                                 outline=LED if tv < t_rev else (61, 214, 128), width=8)
            cx = XS[i] + LADO / 2
            texto(dr, (cx, PYD + LADO + 70), nombres[i], ajustar(nombres[i], 80, LADO), BLANCO, 9)
            nac = NACIDO.get(g["jugadores"][i])
            if nac:
                texto(dr, (cx, PYD + LADO + 160), f"AGE {anio - nac}", 66, LED, 8)
            pais = NACION.get(g["jugadores"][i])
            if pais:
                fl = bandera(pais, 80); im.paste(fl, (int(cx - 40), PYD + LADO + 215), fl)
        if tv >= t_rev:
            fl_u = max(0, 1 - (tv - t_rev) / 0.18)
            if fl_u > 0:
                dr.rectangle((0, 0, W, H), fill=(255, 255, 255, int(230 * fl_u)))
            texto(dr, (W / 2, H - 470), g["cierre"], ajustar(g["cierre"], 100, W - 80), (61, 214, 128), 12)
        ff.stdin.write(np.asarray(im, np.uint8).tobytes())
    ff.stdin.close(); ff.wait()
    mix = np.zeros(int(dur * SR), np.float32); fx = efectos(4)
    for n_, s in sonidos:
        i = int(s * SR); sig = fx[n_]; j = min(len(mix), i + len(sig))
        if 0 <= i < len(mix):
            mix[i:j] += (0.7 if n_ == "whoosh" else 1.0) * sig[: j - i]
    con_beat = mix + beat(dur)[: len(mix)] * 0.7
    for nombre_v, pista in (("short.mp4", np.tanh(con_beat * 1.3) * 0.9), ("short_sin_musica.mp4", np.tanh(mix * 1.1) * 0.6)):
        with wave.open(str(out / "audio.wav"), "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
            w.writeframes((np.clip(pista, -1, 1) * 32767).astype(np.int16).tobytes())
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(out / "mudo.mp4"), "-i", str(out / "audio.wav"),
                        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", str(out / nombre_v)], check=True)
    (out / "mudo.mp4").unlink()
    cred = json.loads((EP / "creditos_epoca.json").read_text())
    usadas = sorted({x.foto for p in pasos for x in p})
    (out / "creditos.json").write_text(json.dumps({k: cred[k] for k in usadas}, ensure_ascii=False, indent=1))
    print("listo", out / "short.mp4", f"{dur:.1f}s", anios)


if __name__ == "__main__":
    main(sys.argv[1])
