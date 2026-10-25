#!/usr/bin/env python3
"""
Formato "2 PLAYERS, 1 FACE": dos jugadores fusionados en una cara; hay que nombrar a los dos.

Retención (reporte 11):
- cuadro 0 ya muestra la fusión + gancho escrito; la voz arranca en el cuadro 0
- la cara "respira" entre los dos jugadores mientras pensás (sensación de "casi lo tengo")
- latido + crescendo el último segundo; destello + sacudida + golpe de bajo al revelar
- revelación: la cara se separa en dos que se deslizan y vuelven a ser cada jugador
- locución con Gemini TTS + subtítulos grandes; beat propio que baja cuando habla la voz
- puntaje /8 (dos nombres por ronda) y cierre que pide el puntaje; corte seco al inicio (loop)

Uso: GEMINI_API_KEY=... python3 produccion/render_fusion.py produccion/guiones/fusion_01.json
"""
import json
import math
import random
import subprocess
import sys
import wave
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fusion import Fusion  # noqa: E402
from render_find_the_real import (BLANCO, FPS, FUENTE2, H, LED, ROJO, SR, VERDE, W, ajustar, ease_out,  # noqa: E402
                                  fondo, fuente, texto)
from voz_gemini import voces_guion  # noqa: E402

ROOT = Path(__file__).resolve().parent
FOTOS = ROOT / "assets" / "fotos"
CX, CY, DIAM = 505, 1010, 720          # círculo central (corrido a la izquierda por los botones de Shorts)
DIAM_S = 470                            # círculos de la revelación
T_SPLIT = 0.55
ESTILO = "Say this in an excited, fast, high-energy sports hype announcer voice, like a viral YouTube Short"


# ---------------------------------------------------------------- audio
def voces_edge(lineas, out):
    """Usa las locuciones de edge-tts generadas en GitHub Actions (assets/voz_edge). Las pasa a wav sin silencios."""
    indice = json.loads((ROOT / "assets/voz_edge/indice.json").read_text())
    faltan = [l for l in lineas if l not in indice]
    if faltan:
        raise SystemExit(f"faltan voces edge para: {faltan[:3]} (correr el workflow 'Generar voces')")
    rutas = []
    for i, l in enumerate(lineas):
        dst = out / f"voz_{i:02d}.wav"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(ROOT / "assets/voz_edge" / indice[l]["archivo"]),
                        "-af", "silenceremove=start_periods=1:start_threshold=-45dB,areverse,"
                               "silenceremove=start_periods=1:start_threshold=-45dB,areverse",
                        "-ar", "24000", "-ac", "1", str(dst)], check=True)
        rutas.append(dst)
    return rutas



def leer_wav(path):
    with wave.open(str(path)) as w:
        sr, n = w.getframerate(), w.getnframes()
        x = np.frombuffer(w.readframes(n), np.int16).astype(np.float32) / 32768
        if w.getnchannels() == 2:
            x = x.reshape(-1, 2).mean(1)
    if sr != SR:
        x = np.interp(np.linspace(0, len(x) - 1, int(len(x) * SR / sr)), np.arange(len(x)), x).astype(np.float32)
    return x


def dur_wav(path):
    with wave.open(str(path)) as w:
        return w.getnframes() / w.getframerate()


def efectos(n):
    rng = np.random.default_rng(5)
    def env(d, a=0.002, k=8.0):
        tt = np.arange(int(d * SR)) / SR
        return np.minimum(tt / a, 1) * np.exp(-k * tt), tt
    fx = {}
    e, tt = env(0.03, k=120); fx["tick"] = np.sin(2 * np.pi * 1900 * tt) * e * 0.3
    e, tt = env(0.03, k=120); fx["tick2"] = np.sin(2 * np.pi * 2400 * tt) * e * 0.38
    e, tt = env(0.9, k=4.5)
    fx["ding"] = (np.sin(2 * np.pi * 1318 * tt) + 0.6 * np.sin(2 * np.pi * 1976 * tt) + 0.3 * np.sin(2 * np.pi * 2637 * tt)) * e * 0.22
    e, tt = env(0.25, k=14); fx["pista"] = (np.sin(2 * np.pi * 880 * tt) + np.sin(2 * np.pi * 1320 * tt)) * e * 0.18
    e, tt = env(1.0, k=4); fx["boom"] = np.sin(2 * np.pi * (36 + 70 * np.exp(-10 * tt)) * tt) * e * 0.9
    e, tt = env(0.28, k=9); fx["latido"] = np.sin(2 * np.pi * (50 + 30 * np.exp(-30 * tt)) * tt) * e * 0.55
    d = 0.9; nz = rng.standard_normal(int(d * SR)).astype(np.float32); tt = np.arange(len(nz)) / SR
    riser = np.convolve(nz, np.ones(12) / 12, mode="same") * (tt / d) ** 2.2
    riser += 0.35 * np.sin(2 * np.pi * (200 + 900 * (tt / d) ** 2) * tt) * (tt / d) ** 2
    fx["riser"] = riser * 0.35
    d = 0.35; nz = rng.standard_normal(int(d * SR)).astype(np.float32); tt = np.arange(len(nz)) / SR
    fx["whoosh"] = np.convolve(nz, np.ones(18) / 18, mode="same") * np.sin(np.pi * tt / d) ** 2 * 0.8
    return fx


def beat(dur):
    n = int(dur * SR); mix = np.zeros(n, np.float32); paso = 60 / 140 / 2
    def env(d, k):
        tt = np.arange(int(d * SR)) / SR; return np.minimum(tt / 0.002, 1) * np.exp(-k * tt), tt
    e, tt = env(0.35, 9); kick = np.sin(2 * np.pi * (45 + 90 * np.exp(-25 * tt)) * tt) * e
    e2, tt2 = env(0.22, 14)
    bell = (np.sign(np.sin(2 * np.pi * 560 * tt2)) * 0.5 + np.sign(np.sin(2 * np.pi * 845 * tt2)) * 0.5) * e2
    bell = np.convolve(bell, np.ones(6) / 6, mode="same")
    hat = np.random.default_rng(1).standard_normal(int(0.04 * SR)) * env(0.04, 60)[0]
    for i in range(int(dur / paso)):
        s = int(i * paso * SR)
        for sig, cond, vol in ((kick, i % 4 == 0, .5), (bell, i % 16 in (0, 3, 6, 8, 11, 14), .12), (hat, i % 2 == 1, .05)):
            if cond:
                j = min(n, s + len(sig)); mix[s:j] += vol * sig[: j - s]
    return mix


# ---------------------------------------------------------------- dibujo
def circulo(img_bgr, diam, borde=LED, grosor=10):
    im = Image.fromarray(cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)).resize((diam, diam), Image.LANCZOS).convert("RGBA")
    m = Image.new("L", (diam * 2, diam * 2), 0); ImageDraw.Draw(m).ellipse((0, 0, diam * 2 - 1, diam * 2 - 1), fill=255)
    im.putalpha(m.resize((diam, diam), Image.LANCZOS))
    capa = Image.new("RGBA", (diam + 2 * grosor, diam + 2 * grosor), (0, 0, 0, 0))
    ImageDraw.Draw(capa).ellipse((0, 0, capa.width - 1, capa.height - 1), fill=borde + (255,))
    capa.paste(im, (grosor, grosor), im)
    return capa


def pegar_centro(base, capa, cx, cy):
    base.paste(capa, (int(cx - capa.width / 2), int(cy - capa.height / 2)), capa)


def subtitulo(dr, s, prog, y):
    """Subtítulo grande que se escribe palabra por palabra (prog 0..1). Si no entra, va en dos líneas."""
    palabras = s.upper().split()
    k = max(1, math.ceil(len(palabras) * min(prog * 1.15, 1)))
    if fuente(76).getlength(" ".join(palabras)) <= 900:
        texto(dr, (CX + 35, y), " ".join(palabras[:k]), 76, BLANCO, 8)
        return
    # dos líneas balanceadas
    corte = min(range(1, len(palabras)), key=lambda i: abs(fuente(70).getlength(" ".join(palabras[:i]))
                                                          - fuente(70).getlength(" ".join(palabras[i:]))))
    l1, l2 = palabras[:corte], palabras[corte:]
    tam = min(ajustar(" ".join(l1), 70, 900), ajustar(" ".join(l2), 70, 900))
    texto(dr, (CX + 35, y - 38), " ".join(l1[:k]), tam, BLANCO, 8)
    if k > corte:
        texto(dr, (CX + 35, y + 42), " ".join(l2[:k - corte]), tam, BLANCO, 8)


# ---------------------------------------------------------------- principal
def main(guion_path):
    g = json.loads(Path(guion_path).read_text())
    out = ROOT / "salida" / g["id"]; out.mkdir(parents=True, exist_ok=True)
    estilo = g.get("estilo_voz", ESTILO); vname = g.get("voz", "Puck")
    bg = fondo()

    # voces y tiempos
    lineas = [x for r in g["rondas"] for x in (r["voz_pregunta"], r["voz_revela"])] + [g["voz_cierre"]]
    wavs = voces_edge(lineas, out) if g.get("motor_voz", "edge") == "edge" else voces_guion(lineas, estilo, vname)
    rondas, t = [], 0.0
    for i, r in enumerate(g["rondas"]):
        vq, vr = wavs[2 * i], wavs[2 * i + 1]
        dq, dr_ = dur_wav(vq), dur_wav(vr)
        think = max(r.get("pensar", g.get("pensar", 4.5)), dq + 1.5)
        reveal = max(1.7, dr_ + 0.45)
        fus = Fusion(FOTOS / f"{r['a']}.jpg", FOTOS / f"{r['b']}.jpg", r.get("espejar_a", False), r.get("espejar_b", False),
                     r.get("cara_a"), r.get("cara_b"))
        rondas.append({**r, "t0": t, "think": think, "reveal": reveal, "vq": vq, "vr": vr, "dq": dq, "dr": dr_, "fus": fus})
        t += think + reveal
    v_end = wavs[-1]; d_end = dur_wav(v_end)
    t_end0 = t; dur = t + max(1.8, d_end + 0.5)
    print(f"duración {dur:.1f} s", file=sys.stderr)

    # audio
    n = int(dur * SR) + SR
    voces = np.zeros(n, np.float32); sfx = np.zeros(n, np.float32)
    fx = efectos(n)
    def add(buf, s, sig, vol=1.0):
        i = int(s * SR); j = min(len(buf), i + len(sig)); buf[i:j] += vol * sig[: j - i]
    for r in rondas:
        add(voces, r["t0"] + 0.05, leer_wav(r["vq"]), 1.0)
        tr = r["t0"] + r["think"]
        add(voces, tr + 0.25, leer_wav(r["vr"]), 1.0)
        add(sfx, r["t0"], fx["whoosh"])
        s = r["t0"] + 0.5
        while s < tr - 0.05:
            rest = tr - s
            add(sfx, s, fx["tick2"] if rest < 1.0 else fx["tick"])
            s += 0.25 if rest < 1.0 else 0.5
        add(sfx, r["t0"] + r["think"] * 0.55, fx["pista"])
        for k in range(3):
            add(sfx, tr - 1.0 + k * 0.33, fx["latido"])
        add(sfx, tr - 0.9, fx["riser"])
        add(sfx, tr, fx["boom"]); add(sfx, tr + 0.05, fx["ding"])
    add(voces, t_end0 + 0.15, leer_wav(v_end), 1.0); add(sfx, t_end0, fx["boom"], 0.6)
    env_voz = np.convolve(np.abs(voces), np.ones(2205) / 2205, mode="same")
    duck = 1 - 0.65 * np.clip(env_voz * 12, 0, 1)
    b = np.zeros(n, np.float32); bb = beat(dur); b[: len(bb)] = bb
    for nombre, con_beat in (("audio_con_beat.wav", True), ("audio_sin_beat.wav", False)):
        mix = voces * 1.0 + sfx + (b * 0.55 * duck if con_beat else 0)
        mix = np.tanh(mix[: int(dur * SR)] * 1.3) * 0.9
        with wave.open(str(out / nombre), "wb") as w:
            w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
            w.writeframes((np.repeat(mix[:, None], 2, 1) * 32767).astype(np.int16).tobytes())

    # video
    nf = int(round(dur * FPS))
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                           "-pix_fmt", "yuv420p", str(out / "video_mudo.mp4")], stdin=subprocess.PIPE)
    total = len(rondas) * 2

    def cuadro(t):
        if t >= dur - 0.3:
            return cuadro(0.0)        # loop
        im = bg.copy(); dr = ImageDraw.Draw(im, "RGBA")
        final = t >= t_end0
        r = rondas[-1] if final else next(x for x in rondas if t < x["t0"] + x["think"] + x["reveal"])
        k = rondas.index(r); tr = t - r["t0"]
        revel = final or tr >= r["think"]
        trv = (t - (r["t0"] + r["think"])) if revel else 0
        # sacudida
        sx = sy = 0
        if revel and not final and trv < 0.35:
            amp = 16 * (1 - trv / 0.35); sx, sy = amp * math.sin(trv * 90), amp * math.cos(trv * 70)
        # cabecera
        et = r["etiqueta"]; col = {"EASY": VERDE, "MEDIUM": LED, "HARD": (255, 150, 60)}.get(et, ROJO)
        f_et = fuente(44, FUENTE2); wet = f_et.getlength(et) + 50
        dr.rounded_rectangle((W / 2 - wet / 2, 140, W / 2 + wet / 2, 208), 34, fill=col)
        dr.text((W / 2, 174), et, font=f_et, fill=(12, 20, 16), anchor="mm")
        texto(dr, (W / 2, 290), "2 PLAYERS", 112, BLANCO, 9)
        pop = 1 + 0.1 * (1 - ease_out(tr / 0.25)) if (tr < 0.25 and k > 0 and not final) else 1
        texto(dr, (W / 2, 420), "1 FACE", int(150 * pop), LED, 12)
        for i in range(len(rondas)):
            cx = W / 2 + (i - (len(rondas) - 1) / 2) * 44
            dr.ellipse((cx - 11, 512, cx + 11, 534), fill=LED if i <= k else (255, 255, 255, 70))
        # cara
        if not revel:
            amp = r.get("respira", 0.1)
            tt = 0.5 + amp * math.sin(2 * math.pi * 0.55 * tr)
            cara = r["fus"].cuadro(tt)
            zoom = 1 + 0.06 * min(tr / r["think"], 1)
            rest = r["think"] - tr
            if rest < 1.0:   # latido
                zoom *= 1 + 0.035 * abs(math.sin(math.pi * (1 - rest) * 3))
            capa = circulo(cara, int(DIAM * zoom), LED if rest > 1.0 else ROJO)
            pegar_centro(im, capa, CX + sx, CY + sy)
            # barra y número
            frac = max(0.0, rest / r["think"]); bx0, bx1, by = 90, 920, 1440
            dr.rounded_rectangle((bx0, by, bx1, by + 24), 12, fill=(255, 255, 255, 40))
            if frac > 0:
                dr.rounded_rectangle((bx0, by, bx0 + (bx1 - bx0) * frac, by + 24), 12, fill=LED if rest > 1 else ROJO)
            texto(dr, (bx1 + 52, by + 11), str(max(1, math.ceil(rest))), 64, LED if rest > 1 else ROJO, 7)
            # subtítulo de la pregunta
            t_pista = r["think"] * 0.55
            if tr < r["dq"] + 0.4:
                subtitulo(dr, r["voz_pregunta"], 1.0 if k == 0 else (tr - 0.05) / max(r["dq"], .1), 1540)
            elif tr < t_pista:
                texto(dr, (CX + 35, 1540), "NAME BOTH!", 70, BLANCO, 8)
            else:
                ini = lambda n: n[0].upper() + "•" * (len(n.replace(" ", "")) - 1)
                q = ease_out((tr - t_pista) / 0.2)
                texto(dr, (CX + 35, 1540), f"HINT:  {ini(r['nombre_a'])}  +  {ini(r['nombre_b'])}", int(66 * (0.85 + 0.15 * q)), LED, 8)
        else:
            p = ease_out(min(trv / T_SPLIT, 1)) if not final else 1
            diam = int(DIAM + (DIAM_S - DIAM) * p)
            xa, xb = CX - 0 * p - 250 * p, CX + 250 * p
            ya = yb = CY - 40 * p
            ta, tb = 0.5 - 0.5 * p, 0.5 + 0.5 * p
            ca, cb = r["fus"].cuadro(ta), r["fus"].cuadro(tb)
            pegar_centro(im, circulo(ca, diam, VERDE), xa + sx, ya + sy)
            pegar_centro(im, circulo(cb, diam, VERDE), xb + sx, yb + sy)
            if p > 0.6:
                q = ease_out((trv - T_SPLIT * 0.6) / 0.25) if not final else 1
                for nombre, x in ((r["nombre_a"], xa), (r["nombre_b"], xb)):
                    tam = ajustar(nombre.upper(), int(84 * (0.8 + 0.2 * q)), 440)
                    texto(dr, (x, CY + DIAM_S / 2 + 40), nombre.upper(), tam, LED, 9)
            if not final:
                subtitulo(dr, r["voz_revela"], (trv - 0.25) / max(r["dr"], .1), 1540)
            # destello
            if not final and trv < 0.12:
                dr.rectangle((0, 0, W, H), fill=(255, 255, 255, int(150 * (1 - trv / 0.12))))
        # puntaje
        texto(dr, (W / 2, 572), f"SCORE  ? / {total}", 44, (255, 255, 255, 200), 5)
        if final:
            te = t - t_end0; a = ease_out(te / 0.25)
            dr.rectangle((0, 0, W, H), fill=(4, 12, 9, int(175 * a)))
            texto(dr, (W / 2, 760), "WHAT'S YOUR", 140, BLANCO, 12)
            texto(dr, (W / 2, 920), f"SCORE /{total}?", 150, LED, 12)
            texto(dr, (W / 2, 1100), "BE HONEST IN THE COMMENTS", 58, BLANCO, 7)
            ax, ay = W / 2, 1220 + 14 * math.sin(te * 9)
            dr.polygon([(ax - 46, ay), (ax + 46, ay), (ax, ay + 60)], fill=LED); dr.rectangle((ax - 16, ay - 70, ax + 16, ay + 2), fill=LED)
        return im

    for f in range(nf):
        ff.stdin.write(cuadro(f / FPS).convert("RGB").tobytes())
        if f % 90 == 0:
            print(f"cuadro {f}/{nf}", file=sys.stderr)
    ff.stdin.close(); ff.wait()
    for nombre, wav in (("short_con_beat.mp4", "audio_con_beat.wav"), ("short_sin_beat.mp4", "audio_sin_beat.wav")):
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(out / "video_mudo.mp4"), "-i", str(out / wav),
                        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", str(out / nombre)], check=True)
    for nombre, tt in (("portada.jpg", 0.0), ("pensando.jpg", rondas[0]["think"] - 0.6),
                       ("revelacion.jpg", rondas[0]["think"] + 0.9), ("cierre.jpg", t_end0 + 0.6)):
        cuadro(tt).convert("RGB").save(out / nombre, quality=90)
    print(f"listo: {out} ({dur:.1f} s)")


if __name__ == "__main__":
    main(sys.argv[1])
