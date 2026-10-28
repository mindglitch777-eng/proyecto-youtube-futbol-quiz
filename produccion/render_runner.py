#!/usr/bin/env python3
"""
RUNNER "ROLLO DE PLATA" (DAY 1 → DAY 999999): réplica del formato de FULYON (13,5 M) y Suuuuu Shorts (4,7 M en su video 1).
Un rollo de billetes 3D baja por una pista nevada y pasa por puertas (+, -, x, ÷, ???). Arriba, la foto del jugador
y "DAY N" cambian en cada puerta. Final: meta a cuadros, lluvia de billetes y cartel 👍 or 😭.

Uso: python3 render_runner.py guiones/runner_01.json [--muestra 1,5,12]
Salida: salida/<id>/short.mp4 (música de juego + efectos) y short_sin_musica.mp4 (para poner el sonido de moda en el editor).
"""
import json
import math
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np

import motor as M

ROOT = Path(__file__).resolve().parent
FPS = 60
PASO = 2.25            # segundos entre puertas
T_PRIMERA = 2.0
VEL = 9.8              # unidades/s de la pista


# ------------------------------------------------------------------ fotos: recorte alrededor de la cara + deformación "meme"
_det = None


def cara(img, puntos=False):
    """Cara más grande (YuNet, el mismo detector que usa poses.py): (x, y, ancho, alto) o None.
    Con puntos=True devuelve también ojos, nariz y boca [(x, y) x5]."""
    global _det
    if _det is None:
        _det = cv2.FaceDetectorYN.create(str(ROOT / "assets/modelos/face_detection_yunet_2023mar.onnx"), "", (320, 320), 0.6)
    h, w = img.shape[:2]
    _det.setInputSize((w, h))
    _, caras = _det.detect(img)
    if caras is None or not len(caras):
        return None
    c = max(caras, key=lambda c: c[2] * c[3])
    caja = tuple(float(v) for v in c[:4])
    return (caja, [(float(c[4 + 2 * k]), float(c[5 + 2 * k])) for k in range(5)]) if puntos else caja


def recortar(ruta, dst, escala=3.2, bw=640, bh=520):
    """Recorte con la proporción del cuadro de foto, la cara centrada a lo ancho y a ~40 % del alto (nunca corta la cabeza)."""
    img = cv2.imread(str(ruta))
    h, w = img.shape[:2]
    c = cara(img)
    cw_, ch_ = (w, w * bh / bw) if w * bh / bw <= h else (h * bw / bh, h)          # el recorte más grande posible
    if c:
        x, y, fw, fh = c
        quiere = fw * escala
        if quiere < cw_:
            cw_, ch_ = quiere, quiere * bh / bw
        cx, cy = x + fw / 2, y + fh / 2
        x0 = np.clip(cx - cw_ / 2, 0, w - cw_); y0 = np.clip(cy - ch_ * 0.40, 0, h - ch_)
    else:
        x0, y0 = (w - cw_) / 2, (h - ch_) / 2
    if c and c[3] > ch_ * 0.62:
        # primer plano muy cerrado: la foto entra entera y el resto se rellena con la misma foto desenfocada
        fondo = cv2.GaussianBlur(cv2.resize(img, (bw, int(bw * h / w)) if w / h < bw / bh else (int(bh * w / h), bh)), (0, 0), 25)
        fy, fx = (fondo.shape[0] - bh) // 2, (fondo.shape[1] - bw) // 2
        lienzo = (fondo[max(fy, 0):max(fy, 0) + bh, max(fx, 0):max(fx, 0) + bw] * 0.6).astype(np.uint8)
        lienzo = cv2.resize(lienzo, (bw, bh))
        r = min(bw / w, bh / h); fw2, fh2 = int(w * r), int(h * r)
        lienzo[(bh - fh2) // 2:(bh - fh2) // 2 + fh2, (bw - fw2) // 2:(bw - fw2) // 2 + fw2] = cv2.resize(img, (fw2, fh2), interpolation=cv2.INTER_AREA)
        cv2.imwrite(str(dst), lienzo, [cv2.IMWRITE_JPEG_QUALITY, 94])
        return True
    crop = img[int(y0):int(y0 + ch_), int(x0):int(x0 + cw_)]
    crop = cv2.resize(crop, (bw, bh), interpolation=cv2.INTER_LANCZOS4 if crop.shape[1] < bw else cv2.INTER_AREA)
    cv2.imwrite(str(dst), crop, [cv2.IMWRITE_JPEG_QUALITY, 94])
    return c is not None


def deformar(dst, fuerza=0.75):
    """Lupa sobre la cara (ojos y nariz gigantes): la foto 'meme' de los días malos, como en el original."""
    img = cv2.imread(str(dst)); h, w = img.shape[:2]
    c = cara(img)
    cx, cy, rad = (w / 2, h * 0.45, min(w, h) * 0.45) if not c else (c[0] + c[2] / 2, c[1] + c[3] * 0.45, max(c[2], c[3]) * 0.95)
    yy, xx = np.indices((h, w), dtype=np.float32)
    dx, dy = xx - cx, yy - cy; d = np.sqrt(dx * dx + dy * dy) / rad
    k = np.where(d < 1, (1 - fuerza * (1 - d) ** 2), 1.0)
    out = cv2.remap(img, (cx + dx * k).astype(np.float32), (cy + dy * k).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    cv2.imwrite(str(dst), out, [cv2.IMWRITE_JPEG_QUALITY, 94])


EMOJI = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"


def pegar_emoji(im, e, x, y, tam):
    """Emoji a color (Noto Color Emoji solo se dibuja a 109 px: se dibuja y se escala)."""
    from PIL import Image, ImageDraw, ImageFont
    capa = Image.new("RGBA", (136, 128), (0, 0, 0, 0))
    ImageDraw.Draw(capa).text((0, 0), e, font=ImageFont.truetype(EMOJI, 109), embedded_color=True)
    capa = capa.crop(capa.getbbox()).resize((tam, tam), Image.LANCZOS)
    im.alpha_composite(capa, (int(x - tam / 2), int(y - tam / 2)))


def meme(dst, tipo):
    """Lógica pura: si la puerta anterior hizo GANAR plata, la foto sale 'épica' (ojos láser, brillo dorado, 🤑📈);
    si hizo PERDER, sale 'triste' (colores fríos, cara deformada, 💀📉)."""
    from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
    img = cv2.imread(str(dst))
    det = cara(img, puntos=True)
    if tipo == "triste":
        if det:
            cv2.imwrite(str(dst), img); deformar(dst, 0.55); img = cv2.imread(str(dst))
        gris = cv2.cvtColor(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), cv2.COLOR_GRAY2BGR)
        frio = cv2.addWeighted(gris, 0.75, np.full_like(img, (140, 70, 20)), 0.25, 0)        # gris azulado
        im = Image.fromarray(cv2.cvtColor(frio, cv2.COLOR_BGR2RGB)).convert("RGBA")
        if det:
            (x, y, cw, ch), pts = det
            for ex, ey in pts[:2]:                                                       # lágrimas
                pegar_emoji(im, "💧", ex, ey + ch * 0.32, int(ch * 0.22))
        pegar_emoji(im, "📉", im.width - 70, 70, 110)
        pegar_emoji(im, "💀", 70, im.height - 70, 110)
    else:
        im = ImageEnhance.Color(Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))).enhance(1.25).convert("RGBA")
        oro = Image.new("RGBA", im.size, (255, 190, 40, 0)); d = ImageDraw.Draw(oro)
        for r in range(0, min(im.size), 6):                                             # viñeta dorada
            a = int(110 * (r / max(im.size)) ** 2)
            d.rectangle((r // 2, r // 2, im.width - r // 2, im.height - r // 2), outline=(255, 190, 40, max(0, 90 - a)))
        im.alpha_composite(oro.filter(ImageFilter.GaussianBlur(18)))
        if det:
            (x, y, cw, ch), pts = det
            rayo = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(rayo)
            largo = im.width * (1.4 if tipo == "epico_max" else 0.9)
            centro = x + cw / 2
            de_frente = abs(pts[0][0] - pts[1][0]) > cw * 0.28                           # de perfil los láser quedan mal
            for ex, ey in (pts[:2] if de_frente else []):                                                       # ojos láser: salen hacia afuera de la cara
                lado = -1 if ex < centro else 1
                fin = (ex + lado * largo * 0.45, ey - largo * 0.10)
                for ancho, alfa in ((int(ch * 0.16), 90), (int(ch * 0.09), 170), (int(ch * 0.035), 255)):
                    d.line((ex, ey, *fin), fill=(255, 40, 30, alfa), width=max(2, ancho))
                    d.ellipse((ex - ancho, ey - ancho, ex + ancho, ey + ancho), fill=(255, 60, 40, alfa))
            im.alpha_composite(rayo.filter(ImageFilter.GaussianBlur(3)))
            im.alpha_composite(rayo)
        pegar_emoji(im, "📈", im.width - 70, 70, 110)
        pegar_emoji(im, "🤑" if tipo == "epico_max" else "🔥", 70, im.height - 70, 110)
    im.convert("RGB").save(str(dst), quality=94)


# ------------------------------------------------------------------ lógica de la plata
def aplicar(m, op, v):
    return {"+": m + v, "-": m - v, "x": m * v, "÷": m / v}[op]


def armar(g, out):
    fotos_dir = out / "fotos"; fotos_dir.mkdir(parents=True, exist_ok=True)
    fotos, etapas = {}, []
    for i, e in enumerate(g["etapas"]):
        dst = fotos_dir / f"e{i:02d}.jpg"
        recortar(ROOT / e["foto"], dst, e.get("escala", 3.2))
        if i > 0 and e.get("meme", True):
            p = g["puertas"][i - 1]; lado = p["lados"][p["elige"]]
            op = lado["revela"][0] if lado["txt"] == "???" else lado["op"]
            meme(dst, "triste" if op in "-÷" else ("epico_max" if p.get("grito") else "epico"))
        fotos[f"e{i}"] = f"/salida/{out.name}/fotos/{dst.name}"
        etapas.append(dict(dia=e["dia"], foto=f"e{i}", color=e.get("color", "#2fe36b")))
    m = g["inicio"]; puertas = []
    for k, p in enumerate(g["puertas"]):
        t = T_PRIMERA + k * PASO
        lado = p["lados"][p["elige"]]
        op, v = (lado["revela"][0], lado["revela"][1]) if lado["txt"] == "???" else (lado["op"], lado["v"])
        antes, m = m, aplicar(m, op, v)
        lados = [dict(txt=l["txt"], tipo="misterio" if l["txt"] == "???" else ("mas" if l["op"] in "+x" else "menos")) for l in p["lados"]]
        if lado["txt"] == "???":
            lados[p["elige"]]["revelado"] = f"{op}{v}"
        puertas.append(dict(t=t, z=-VEL * t, lados=lados, elige=p["elige"], antes=antes, despues=m,
                            efecto="sube" if m > antes else "baja", grito=p.get("grito")))
        etapas[k + 1]["desde"] = t
    etapas[0]["desde"] = 0.0
    t_meta = puertas[-1]["t"] + 1.3
    dur = t_meta + 2.7
    return dict(fps=FPS, vel=VEL, inicio=g["inicio"], puertas=puertas, etapas=etapas, fotos=fotos, tMeta=t_meta,
                zMeta=-VEL * t_meta - 0.5, duracion=dur, largo=VEL * dur + 40)


# ------------------------------------------------------------------ audio: música de juego de celular propia + efectos
def musica_juego(dur, bpm=128):
    """Loop alegre tipo juego móvil: bombo, palmas, bajo y melodía cuadrada en Do mayor. Arranca con golpe en el 0."""
    sr = M.SR; n = int(dur * sr); mix = np.zeros(n, np.float32); negra = 60 / bpm; sem = negra / 2
    def tono(f, d, forma="cuadrada", vol=0.12):
        t = np.arange(int(d * sr)) / sr
        s = np.sign(np.sin(2 * np.pi * f * t)) if forma == "cuadrada" else np.sin(2 * np.pi * f * t)
        return (np.convolve(s, np.ones(6) / 6, mode="same") if forma == "cuadrada" else s) * np.exp(-t * 5) * vol
    def add(t0, sig):
        i = int(t0 * sr); j = min(n, i + len(sig))
        if i < n:
            mix[i:j] += sig[: j - i]
    tt = np.arange(int(0.3 * sr)) / sr
    kick = np.sin(2 * np.pi * (50 + 110 * np.exp(-30 * tt)) * tt) * np.exp(-10 * tt) * 0.55
    nz = np.random.default_rng(3).standard_normal(int(0.12 * sr)).astype(np.float32)
    clap = np.convolve(nz, np.ones(4) / 4, mode="same") * np.exp(-np.arange(len(nz)) / sr * 30) * 0.22
    hat = np.random.default_rng(4).standard_normal(int(0.04 * sr)) * np.exp(-np.arange(int(0.04 * sr)) / sr * 90) * 0.06
    N = {"C4": 261.6, "D4": 293.7, "E4": 329.6, "F4": 349.2, "G4": 392.0, "A4": 440.0, "B4": 493.9, "C5": 523.3, "D5": 587.3, "E5": 659.3, "G5": 784.0}
    mel = "E5 G5 E5 C5 D5 E5 C5 G4 A4 C5 D5 E5 D5 C5 A4 G4 E5 G5 E5 C5 D5 E5 G5 E5 D5 C5 A4 C5 D5 C5 G4 C5".split()
    bajos = [130.8, 130.8, 174.6, 196.0]                # C C F G
    k = 0; t = 0.0
    while t < dur:
        if k % 2 == 0:
            add(t, kick)
        if k % 4 == 2:
            add(t, clap)
        add(t + sem / 2, hat)
        add(t, tono(bajos[(k // 8) % 4], sem * 0.9, "seno", 0.22))
        add(t, tono(N[mel[k % len(mel)]], sem * 0.85, "cuadrada", 0.07))
        t += sem; k += 1
    return mix


def kaching():
    t = np.arange(int(0.5 * M.SR)) / M.SR
    tono = (np.sin(2 * np.pi * 1568 * t) + 0.7 * np.sin(2 * np.pi * 2093 * t)) * np.exp(-t * 7) * 0.22
    nz = np.random.default_rng(5).standard_normal(len(t)) * np.exp(-t * 40) * 0.12
    return tono + nz


def bajon():
    t = np.arange(int(0.6 * M.SR)) / M.SR
    f = 420 * np.exp(-t * 1.6)
    return np.sign(np.sin(2 * np.pi * np.cumsum(f) / M.SR)) * np.exp(-t * 3) * 0.12


def monedas(n=6, semilla=1):
    rng = np.random.default_rng(semilla); out = np.zeros(int((n * 0.07 + 0.2) * M.SR), np.float32)
    for i in range(n):
        s = M.pluck(rng.choice([1760, 1976, 2349, 2637]), 0.12, 0.12); j = int(i * 0.07 * M.SR)
        out[j:j + len(s)] += s[: len(out) - j]
    return out


def bocina_mlg():
    """Airhorn de meme: tres bocinazos de sierras desafinadas (sintetizado, sin derechos)."""
    sr = M.SR; out = []
    for d in (0.16, 0.16, 0.55):
        t = np.arange(int(d * sr)) / sr
        s = sum(2 * ((f * t) % 1) - 1 for f in (466, 470, 554, 698, 932)) / 5
        s = np.convolve(s, np.ones(4) / 4, mode="same") * np.minimum(t / 0.01, 1) * np.minimum((d - t) / 0.03, 1)
        out += [s * 0.38, np.zeros(int(0.04 * sr))]
    return np.concatenate(out).astype(np.float32)


def trombon_triste():
    """'Wah wah wah waaah': cuatro notas que bajan, la última con vibrato (sintetizado)."""
    sr = M.SR; out = []
    for f, d in ((311, 0.32), (294, 0.32), (277, 0.32), (262, 1.0)):
        t = np.arange(int(d * sr)) / sr
        vib = 1 + 0.03 * np.sin(2 * np.pi * 6 * t) * (d > 0.5)
        fase = 2 * np.pi * np.cumsum(f * vib) / sr
        s = sum(np.sin(k * fase) / k ** 0.9 for k in range(1, 9))                     # timbre de bronce
        s *= np.minimum(t / 0.04, 1) * np.minimum((d - t) / 0.06, 1) * (1 + 0.6 * np.sin(np.pi * np.minimum(t / 0.25, 1)))
        out.append(s * 0.09)
    return np.concatenate(out).astype(np.float32)


def vine_boom():
    t = np.arange(int(1.1 * M.SR)) / M.SR
    s = np.sin(2 * np.pi * (42 + 90 * np.exp(-18 * t)) * t) * np.exp(-t * 3.2)
    clic = np.random.default_rng(2).standard_normal(len(t)) * np.exp(-t * 120) * 0.3
    return ((s + clic) * 0.8).astype(np.float32)


def audio(cfg):
    dur = cfg["duracion"]; mez = M.Mezcla(dur)
    for p in cfg["puertas"]:
        if p["efecto"] == "sube":
            mez.add(p["t"], kaching()); mez.add(p["t"] + 0.05, monedas(7 if p["grito"] else 4, int(p["t"] * 10)))
            if p["grito"]:
                mez.add(p["t"] + 0.08, bocina_mlg(), 0.9)
        else:
            mez.add(p["t"], trombon_triste(), 1.0)
            if p["grito"]:
                mez.add(p["t"], vine_boom(), 0.9)
        mez.add(p["t"] - 0.15, M.whoosh(0.3), 0.35)
    mez.add(cfg["tMeta"], M.boom(), 0.6); mez.add(cfg["tMeta"], M.tribuna(2.6), 1.0); mez.add(cfg["tMeta"] + 0.1, bocina_mlg(), 0.9); mez.add(cfg["tMeta"] + 0.05, monedas(14, 9))
    musica = musica_juego(dur)[: int(dur * M.SR)]
    solo = mez.x[: int(dur * M.SR)]
    return {"short.mp4": np.tanh((solo + musica * 0.85) * 1.1) * 0.9, "short_sin_musica.mp4": np.tanh(solo * 1.1) * 0.8}


def main(guion, muestra=None):
    g = json.loads(Path(guion).read_text())
    out = ROOT / "salida" / g["id"]; out.mkdir(parents=True, exist_ok=True)
    cfg = armar(g, out)
    (out / "config.json").write_text(json.dumps(cfg, ensure_ascii=False))
    js = ROOT / "runner" / "render_runner.js"
    if muestra:
        subprocess.run(["node", str(js), str(out / "config.json"), str(out / "muestra"), "--muestra", muestra], check=True)
        return
    subprocess.run(["node", str(js), str(out / "config.json"), str(out / "mudo.mp4")], check=True)
    M.mezclar(out, out / "mudo.mp4", audio(cfg))
    print("listo", out / "short.mp4", f"{cfg['duracion']:.1f}s", "plata final", cfg["puertas"][-1]["despues"])


if __name__ == "__main__":
    a = sys.argv[1:]
    main(a[0], a[2] if len(a) > 2 and a[1] == "--muestra" else None)
