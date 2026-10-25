#!/usr/bin/env python3
"""
EVOLUTION de objetos (pelotas del Mundial, etc.) con fotos libres de Commons.
Patrón de la competencia (Kickoff to Immortality: botines 26 M, camisetas 19,7 M, pelotas 10 M): año grande en cada foto,
~1,6 s por objeto, música de tendencia sin voz, ~30 s. Nuestro toque: transición con zoom, línea de tiempo y pregunta final.
Uso: python3 render_objetos.py guiones/objeto_01.json
"""
import json
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from render_find_the_real import BLANCO, FPS, H, LED, SR, W, ROOT, ajustar, texto
from render_fusion import beat, efectos

P = 940


def cargar(path):
    im = Image.open(path).convert("RGB")
    w, h = im.size; s = min(w, h)
    cuad = im.crop(((w - s) // 2, (h - s) // 2, (w + s) // 2, (h + s) // 2)).resize((P, P), Image.LANCZOS)
    fondo = im.resize((W, int(W * h / w)) if w < h else (int(H * w / h), H)).crop((0, 0, W, H)).filter(ImageFilter.GaussianBlur(40))
    fondo = Image.blend(fondo, Image.new("RGB", (W, H), (8, 8, 14)), 0.55)
    m = Image.new("L", (P, P), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, P - 1, P - 1), 50, fill=255)
    cuad = cuad.convert("RGBA"); cuad.putalpha(m)
    return cuad, fondo


def main(guion_path):
    g = json.loads(Path(guion_path).read_text())
    d = ROOT / "assets" / "objetos" / g["serie"]
    items = [(int(a), cargar(d / f"{a}_{k}.jpg")) for a, k in g["fotos"]]
    T_ITEM, T_TR, T_FIN = g.get("t_item", 1.55), 0.35, 2.6
    dur = len(items) * T_ITEM + T_FIN
    nf = int(dur * FPS)
    out = ROOT / "salida" / g["id"]; out.mkdir(parents=True, exist_ok=True)
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "19",
                           str(out / "mudo.mp4")], stdin=subprocess.PIPE)
    y0 = 430
    for f in range(nf):
        t = f / FPS
        k = min(int(t // T_ITEM), len(items) - 1)
        tt = t - k * T_ITEM
        anio, (cuad, fondo) = items[k]
        im = fondo.copy()
        z = 1.0 + 0.05 * min(tt / T_ITEM, 1)                       # zoom lento (Ken Burns)
        if tt < T_TR and k > 0:                                    # entrada con zoom desde 0.85
            z *= 0.85 + 0.15 * (1 - (1 - tt / T_TR) ** 3)
        c = cuad.resize((int(P * z), int(P * z)), Image.LANCZOS)
        im.paste(c, ((W - c.width) // 2, y0 + (P - c.height) // 2), c)
        dr = ImageDraw.Draw(im, "RGBA")
        texto(dr, (W / 2, 110), g["titulo"], ajustar(g["titulo"], 96, W - 60), BLANCO, 10)
        texto(dr, (W / 2, 220), g["subtitulo"], ajustar(g["subtitulo"], 64, W - 80), LED, 7)
        pop = 1 + 0.25 * max(0, 1 - tt / 0.2)
        texto(dr, (W / 2, y0 + P + 110), str(anio), int(150 * pop), LED, 14)
        nombre = g.get("nombres", {}).get(str(anio))
        if nombre:
            texto(dr, (W / 2, y0 + P + 220), nombre, ajustar(nombre, 64, W - 120), BLANCO, 7)
        # línea de tiempo
        x0, x1, yb = 80, W - 80, 330
        dr.line((x0, yb, x1, yb), fill=(255, 255, 255, 90), width=6)
        for i in range(len(items)):
            x = x0 + (x1 - x0) * i / max(len(items) - 1, 1)
            dr.ellipse((x - 9, yb - 9, x + 9, yb + 9), fill=LED if i <= k else (120, 120, 120))
        if t >= len(items) * T_ITEM:
            u = min((t - len(items) * T_ITEM) / 0.3, 1)
            dr.rectangle((0, 0, W, H), fill=(0, 0, 0, int(170 * u)))
            texto(dr, (W / 2, H * 0.45), g["cierre"], ajustar(g["cierre"], 110, W - 80), LED, 12)
            texto(dr, (W / 2, H * 0.45 + 130), "COMMENT THE YEAR", 72, BLANCO, 8)
        ff.stdin.write(np.asarray(im, np.uint8).tobytes())
    ff.stdin.close(); ff.wait()
    mix = np.zeros(int(dur * SR), np.float32); fx = efectos(4)
    for i in range(len(items)):
        s_ = i * T_ITEM; sig = fx["whoosh"]; a = int(s_ * SR); b = min(len(mix), a + len(sig)); mix[a:b] += 0.6 * sig[: b - a]
    s_ = len(items) * T_ITEM; sig = fx["boom"]; a = int(s_ * SR); b = min(len(mix), a + len(sig)); mix[a:b] += sig[: b - a]
    con_beat = mix + beat(dur)[: len(mix)] * 0.7
    for nombre_v, pista in (("short.mp4", np.tanh(con_beat * 1.3) * 0.9), ("short_sin_musica.mp4", np.tanh(mix * 1.1) * 0.6)):
        with wave.open(str(out / "audio.wav"), "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
            w.writeframes((np.clip(pista, -1, 1) * 32767).astype(np.int16).tobytes())
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(out / "mudo.mp4"), "-i", str(out / "audio.wav"),
                        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", str(out / nombre_v)], check=True)
    (out / "mudo.mp4").unlink()
    cred = json.loads((d / "creditos.json").read_text())
    (out / "creditos.json").write_text(json.dumps({f"{a}_{k}": cred[f"{a}_{k}"] for a, k in g["fotos"]}, ensure_ascii=False, indent=1))
    print("listo", out / "short.mp4", f"{dur:.1f}s")


if __name__ == "__main__":
    main(sys.argv[1])
