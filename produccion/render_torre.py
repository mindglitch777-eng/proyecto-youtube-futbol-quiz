#!/usr/bin/env python3
"""
BALL TOWER (satisfying 3D + adivinanza): llueven pelotas, se ordenan en una torre con los colores de una bandera.
Arriba, 3 jugadores: "WHOSE COUNTRY?". Al terminar la torre se revela: bandera + ✅ al correcto, ❌ a los otros.
La torre explota y vuelve a empezar (loop). Escena 3D: runner/escena_torre.html.

Uso: python3 produccion/render_torre.py produccion/guiones/torre_01.json
guion: {"id": "torre_01", "opciones": ["lionel_messi", "cristiano_ronaldo", "neymar"], "correcta": 0, "musica": "chipi_chapa_0"}
"""
import json
import math
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

import cartas
import motor as M
import render_plinko as P

ROOT = P.ROOT
W, H, FPS = 1080, 1920, 30
# franjas (de arriba a abajo, o de izquierda a derecha si vertical)
BANDERAS = {
    "AR": (["#74ACDF", "#FFFFFF", "#74ACDF"], False), "PT": (["#046A38", "#DA291C", "#DA291C"], True),
    "BR": (["#009C3B", "#FFDF00", "#002776", "#FFDF00", "#009C3B"], False), "FR": (["#0055A4", "#FFFFFF", "#EF4135"], True),
    "ES": (["#AA151B", "#F1BF00", "#F1BF00", "#AA151B"], False), "DE": (["#111111", "#DD0000", "#FFCE00"], False),
    "NO": (["#BA0C2F", "#FFFFFF", "#00205B", "#FFFFFF", "#BA0C2F"], False), "BE": (["#111111", "#FAE042", "#ED2939"], True),
    "IT": (["#009246", "#FFFFFF", "#CE2B37"], True), "EG": (["#CE1126", "#FFFFFF", "#111111"], False),
    "ENG": (["#FFFFFF", "#CE1124", "#FFFFFF"], False), "NL": (["#AE1C28", "#FFFFFF", "#21468B"], False),
    "HR": (["#FF0000", "#FFFFFF", "#171796"], False), "SE": (["#006AA7", "#FECC02", "#006AA7"], False),
}
T_LLUVIA, T_JUNTA0, T_JUNTA, T_OLA, D_OLA, T_REVELA, T_DERRUMBE, DUR = 1.6, 1.9, 2.4, 4.9, 1.2, 6.3, 8.4, 9.8


def pais(clave):
    return cartas.datos(clave)[2]


def capa(g, t):
    im = Image.new("RGBA", (W, H)); d = ImageDraw.Draw(im)
    ops = g["opciones"]; ok = g["correcta"]
    P.texto(d, (W / 2, 100), "WHOSE COUNTRY", 96, (255, 255, 255), 12)
    P.texto(d, (W / 2 - 40, 200), "IS THIS?", 96, (255, 235, 40), 12)
    P.RR.pegar_emoji(im, "👇", int(W / 2 + 200), 200, 90)
    for i, k in enumerate(ops):
        cx, cy = 182 + i * 358, 450
        tam = 350
        pulso = 1 + 0.06 * math.sin(t * 6 + i)                                 # respiran (movimiento)
        if t >= T_REVELA:
            e = t - T_REVELA
            pulso = 1 + (0.25 * math.exp(-e * 5) if i == ok else 0) ; tam = 365 if i == ok else 290
        tt = int(tam * pulso)
        cara = P.cara(k, tt)
        if t >= T_REVELA and i != ok:
            cara = Image.blend(cara, cara.convert("LA").convert("RGBA"), 0.85)
        im.alpha_composite(P.con_aro(cara, (60, 220, 90) if (t >= T_REVELA and i == ok) else (255, 255, 255), 10), (int(cx - tt / 2 - 10), int(cy - tt / 2 - 10)))
        d = ImageDraw.Draw(im)
        P.texto(d, (cx, cy + 215), P.nombre_corto(k).upper(), 50, (255, 255, 255), 8)
        if t >= T_REVELA:
            P.RR.pegar_emoji(im, "✅" if i == ok else "❌", int(cx + 100), int(cy - 110), 110)
            d = ImageDraw.Draw(im)
    if T_REVELA <= t < T_DERRUMBE:
        e = t - T_REVELA
        if e < 0.15:
            im.alpha_composite(Image.new("RGBA", (W, H), (255, 255, 255, int(200 * (1 - e / 0.15)))))
        try:
            import banderas as B
            fl = Image.open(B.png(pais(ops[ok]), 320)).convert("RGBA")
        except Exception:
            fl = None
        if fl is not None:
            s = min(1.0, e / 0.15) * 1.0
            fl = fl.resize((int(260 * s) + 1, int(260 * s) + 1), Image.LANCZOS)
            im.alpha_composite(fl, (int(W / 2 - fl.width / 2), 1560 - fl.height // 2))
        d = ImageDraw.Draw(im)
        P.texto(d, (W / 2, 1760), P.nombre_corto(ops[ok]).upper() + "!", 110, (255, 235, 40), 13)
    elif T_OLA <= t < T_REVELA:
        P.texto(d, (W / 2, 1720), "LOOK AT THE COLORS...", 76, (255, 255, 255), 12)
    elif t < T_OLA and t > T_JUNTA0 + 1.0:
        P.texto(d, (W / 2, 1720), "WAIT FOR IT...", 90, (255, 255, 255), 12)
    return im


def audio(g, dur):
    sr = M.SR; n = int(dur * sr); fx = np.zeros(n, np.float32)
    rng = np.random.default_rng(g.get("semilla", 1))

    def add(t0, sig, v=1.0):
        if sig is None:
            return
        a = int(t0 * sr)
        if a < 0 or a >= n:
            return
        b = min(n, a + len(sig)); fx[a:b] += sig[: b - a] * v
    tt = np.arange(int(0.05 * sr)) / sr
    for _ in range(170):                                                       # lluvia: toc-toc de pelotas
        t0 = rng.uniform(0.5, T_LLUVIA + 1.2); f = rng.uniform(500, 900)
        add(t0, np.sin(2 * np.pi * f * tt) * np.exp(-tt * 70) * 0.18)
    for j in range(140):                                                       # armado: clicks cada vez más agudos
        u = j / 140; t0 = T_JUNTA0 + 0.5 + u * T_JUNTA + rng.uniform(0, 0.1); f = 600 + 900 * u
        add(t0, np.sin(2 * np.pi * f * tt) * np.exp(-tt * 60) * 0.2)
    add(T_JUNTA0, M.whoosh(1.0), 0.5)
    for j in range(24):                                                        # ola de color: barrido que sube
        add(T_OLA + j * D_OLA / 24, np.sin(2 * np.pi * (400 + 60 * j) * tt) * np.exp(-tt * 40) * 0.25)
    add(T_REVELA, M.boom(0.8), 0.7); add(T_REVELA, M.ding(0.9), 0.6); add(T_REVELA + 0.05, P.cargar("crowd_cheer_0", 0.5))
    for s in P.SONIDO_JUGADOR.get(g["opciones"][g["correcta"]], ["goat_0"])[:1]:
        add(T_REVELA + 0.25, P.cargar(s, 0.9))
    add(T_DERRUMBE, M.whoosh(0.8), 0.7); add(T_DERRUMBE, M.golpe(0.2), 0.6)
    mu = P.musica(g, dur)
    return np.tanh((mu * 0.7 + fx) * 1.1) * 0.9, np.tanh(fx * 1.1) * 0.85


def main(guion):
    g = json.loads(Path(guion).read_text())
    out = ROOT / "salida" / g["id"]; out.mkdir(parents=True, exist_ok=True)
    franjas, vertical = BANDERAS[pais(g["opciones"][g["correcta"]])]
    cfg = dict(escena="escena_torre.html", fps=FPS, duracion=DUR, n=420, por_anillo=20, r=0.5, franjas=franjas, vertical=vertical,
               semilla=g.get("semilla", 1), t_lluvia=T_LLUVIA, t_junta0=T_JUNTA0, t_junta=T_JUNTA, t_derrumbe=T_DERRUMBE, t_ola=T_OLA, d_ola=D_OLA,
               fondo=g.get("fondo", "#2fb59a"), piso=g.get("piso", "#1f8f78"))
    (out / "cfg3d.json").write_text(json.dumps(cfg))
    tres = out / "tres.mp4"
    muestra = sys.argv[2:]
    subprocess.run(["node", str(ROOT / "runner" / "render_runner.js"), str(out / "cfg3d.json"), str(tres)] + (["--muestra", muestra[0]] if muestra else []),
                   check=True, cwd=ROOT / "runner")
    if muestra:
        return
    lee = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-i", str(tres), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    mudo = out / "mudo.mp4"
    esc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                            "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", str(mudo)], stdin=subprocess.PIPE)
    inicio = None
    import gancho as G
    tx = G.textos_de(g, "torre", con_gancho=False)
    for f in range(int(round(DUR * FPS))):
        crudo = lee.stdout.read(W * H * 3)
        if len(crudo) < W * H * 3:
            break
        t = f / FPS
        base = Image.frombytes("RGB", (W, H), crudo).convert("RGBA"); base.alpha_composite(capa(g, t))
        im = G.capa(base, t, DUR, tx, 1850).convert("RGB")
        if inicio is None:
            inicio = im
        if t > DUR - 0.35:
            im = Image.blend(im, inicio, (t - (DUR - 0.35)) / 0.35)
        esc.stdin.write(np.asarray(im, np.uint8).tobytes())
    esc.stdin.close(); esc.wait(); lee.wait(); tres.unlink()
    con, solo = audio(g, DUR)
    M.mezclar(out, mudo, G.con_pito({"short.mp4": con, "short_solo_efectos.mp4": solo}))
    print(out / "short.mp4", DUR, "s")


if __name__ == "__main__":
    main(sys.argv[1])
