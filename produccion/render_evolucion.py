#!/usr/bin/env python3
"""
Dos formatos con las fotos CON FECHA (assets/fotos_epoca, verificadas en assets/poses_epoca.csv):

- "evolucion"  WHO IS HE? · AGE EVOLUTION: la cara de un jugador envejece año a año con morph. Adiviná antes de hoy.
               Pistas: bandera (55%) e iniciales (80%). Cierre: "WHAT YEAR DID YOU GET IT?"
- "prime_now"  PRIME vs NOW: plantel de un año (p. ej. BARCELONA 2015) -> cada jugador se transforma en su cara de hoy.
               Cierre: "WHO AGED THE BEST?"

Uso: python3 render_evolucion.py guiones/evo_01.json
"""
import json
import subprocess
import sys
import wave
from pathlib import Path

import cv2
import numpy as np
import pandas as pd
from PIL import Image, ImageDraw

from banderas import png as bandera_png
from fusion import Fusion
from render_find_the_real import BLANCO, FPS, H, LED, SR, W, ROOT, ajustar, ease_out, texto
from render_fusion import beat, efectos, leer_wav, voces_edge

EP = ROOT / "assets" / "fotos_epoca"
PANEL = 880
PY = 470
NACION = {
    "Lionel Messi": "AR", "Cristiano Ronaldo": "PT", "Neymar": "BR", "Luka Modrić": "HR", "Zlatan Ibrahimović": "SE",
    "Sergio Ramos": "ES", "Toni Kroos": "DE", "Robert Lewandowski": "PL", "Mohamed Salah": "EG", "Kevin De Bruyne": "BE",
    "Harry Kane": "ENG", "Ángel Di María": "AR", "Karim Benzema": "FR", "Antoine Griezmann": "FR", "Kylian Mbappé": "FR",
    "Luis Suárez": "UY", "Andrés Iniesta": "ES", "Wayne Rooney": "ENG", "Gareth Bale": "WAL", "Thomas Müller": "DE",
    "Casemiro": "BR", "Raphaël Varane": "FR", "Keylor Navas": "CR", "Dani Carvajal": "ES", "Isco": "ES",
    "Sergio Busquets": "ES", "Gerard Piqué": "ES", "Dani Alves": "BR", "Javier Mascherano": "AR", "Ivan Rakitić": "HR",
    "Marc-André ter Stegen": "DE", "Jordi Alba": "ES", "Manuel Neuer": "DE", "Mesut Özil": "DE", "Philipp Lahm": "DE",
    "Bastian Schweinsteiger": "DE", "Mats Hummels": "DE", "Miroslav Klose": "DE", "Paul Pogba": "FR", "N'Golo Kanté": "FR",
    "Hugo Lloris": "FR", "Olivier Giroud": "FR", "Vinícius Júnior": "BR", "Jude Bellingham": "ENG", "Lamine Yamal": "ES",
}
CORTO = {"Marc-André ter Stegen": "TER STEGEN", "Ángel Di María": "DI MARÍA", "Kevin De Bruyne": "DE BRUYNE",
         "N'Golo Kanté": "KANTÉ", "Vinícius Júnior": "VINÍCIUS", "Zlatan Ibrahimović": "ZLATAN", "Dani Alves": "DANI ALVES",
         "Jordi Alba": "JORDI ALBA", "Keylor Navas": "NAVAS"}


def corto(n):
    return CORTO.get(n, n.split()[-1].upper())


# ------------------------------------------------------------------ fotos
def fotos_de(jugador, max_puntaje=45):
    df = pd.read_csv(ROOT / "assets" / "poses_epoca.csv")
    bloq = set(json.loads((ROOT / "assets" / "fotos_bloqueadas.json").read_text()))
    d = df[(df.jugador == jugador) & (df.puntaje <= max_puntaje) & (df.cara_px >= 110) & ~df.foto.isin(bloq)]
    return d.sort_values("puntaje").groupby("anio").head(1).sort_values("anio")


def elegir_anios(d, n=8, sep=2):
    filas = list(d.itertuples())
    if not filas:
        return []
    out = [filas[0]]
    for f in filas[1:-1]:
        if f.anio - out[-1].anio >= sep:
            out.append(f)
    if filas[-1].anio - out[-1].anio >= 1:
        out.append(filas[-1])
    while len(out) > n:            # sacamos los intermedios más pegados
        k = min(range(1, len(out) - 1), key=lambda i: out[i + 1].anio - out[i - 1].anio)
        out.pop(k)
    return out


def ruta(f):
    return EP / f"{f.foto}.jpg"


def espejos(filas):
    ref = filas[0].asimetria
    return [bool(f.asimetria * ref < 0 and abs(f.asimetria) > 0.05) for f in filas]


# ------------------------------------------------------------------ dibujo
def fondo():
    y = np.linspace(0, 1, H)[:, None, None]
    a = np.array([10, 12, 20], np.float32); b = np.array([30, 26, 52], np.float32)
    return Image.fromarray((a + (b - a) * y).repeat(W, 1).astype(np.uint8), "RGB")


def panel(bgr):
    im = Image.fromarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)).resize((PANEL, PANEL), Image.LANCZOS)
    m = Image.new("L", (PANEL, PANEL), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, PANEL - 1, PANEL - 1), 48, fill=255)
    im.putalpha(m)
    return im


def bandera(pais, lado=150):
    return Image.open(bandera_png(pais, 160)).convert("RGBA").resize((lado, lado), Image.LANCZOS)


# ------------------------------------------------------------------ líneas de tiempo
def tramos_evolucion(g):
    filas = elegir_anios(fotos_de(g["jugador"]), g.get("max_fotos", 8))
    esp = espejos(filas)
    T_HOLD, T_MORPH = g.get("hold", 1.15), g.get("morph", 0.85)
    tramos, t = [], 0.0
    for k in range(len(filas) - 1):
        tramos.append(dict(t0=t, t1=t + T_HOLD + T_MORPH, a=filas[k], b=filas[k + 1], ea=esp[k], eb=esp[k + 1],
                           hold=T_HOLD, morph=T_MORPH, nombre=g["jugador"]))
        t += T_HOLD + T_MORPH
    return filas, tramos, t


def tramos_prime(g):
    tramos, t, usados = [], 0.0, []
    for jug in g["jugadores"]:
        d = fotos_de(jug, 60)
        if d.empty:
            continue
        antes = d.iloc[(d.anio - g["anio"]).abs().argsort()[:1]].iloc[0]
        ahora = d.iloc[-1]
        if ahora.anio - antes.anio < g.get("min_gap", 5) or abs(antes.anio - g["anio"]) > 2:
            print("salteo", jug, antes.anio, ahora.anio); continue
        a = next(d.loc[[antes.name]].itertuples()); b = next(d.loc[[ahora.name]].itertuples())
        eb = bool(a.asimetria * b.asimetria < 0 and abs(b.asimetria) > 0.05)
        tramos.append(dict(t0=t, t1=t + 2.5, a=a, b=b, ea=False, eb=eb, hold=0.8, morph=1.0, nombre=jug))
        usados += [a, b]
        t += 2.5
    return usados, tramos, t


# ------------------------------------------------------------------ principal
def main(guion_path):
    g = json.loads(Path(guion_path).read_text())
    evo = g["formato"] == "evolucion"
    filas, tramos, t_juego = tramos_evolucion(g) if evo else tramos_prime(g)
    if not tramos:
        raise SystemExit("sin fotos suficientes")
    out = ROOT / "salida" / g["id"]; out.mkdir(parents=True, exist_ok=True)
    T_INTRO = 0.9
    T_REVEAL = 3.4 if evo else 2.8
    dur = T_INTRO + t_juego + (tramos[-1]["hold"] if evo else 0) + T_REVEAL
    nf = int(dur * FPS)
    fus = [Fusion(ruta(tr["a"]), ruta(tr["b"]), tr["ea"], tr["eb"], json.loads(tr["a"].cara), json.loads(tr["b"].cara))
           for tr in tramos]
    base = fondo()
    t_rev = T_INTRO + t_juego + (tramos[-1]["hold"] if evo else 0)
    sonidos = [("whoosh", T_INTRO - 0.2)]
    for tr in tramos:
        sonidos.append(("whoosh", T_INTRO + tr["t0"] + tr["hold"]))
        if not evo:
            sonidos.append(("tick2", T_INTRO + tr["t0"]))
    if evo:
        pais = NACION.get(g["jugador"])
        t_h1, t_h2 = T_INTRO + t_juego * 0.55, T_INTRO + t_juego * 0.8
        sonidos += [("ding", t_h1), ("ding", t_h2), ("riser", t_rev - 0.9), ("boom", t_rev), ("ding", t_rev + 0.05)]
        ini = ". ".join(p[0] for p in g["jugador"].replace("-", " ").split()[:2]) + "."
        voz = [(0.1, g["voz_intro"]), (t_rev + 0.1, g["voz_revela"])]
    else:
        sonidos += [("boom", t_rev), ("ding", t_rev + 0.05)]
        voz = [(0.1, g["voz_intro"]), (t_rev + 0.1, g["voz_cierre"])]
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "19",
                           str(out / "mudo.mp4")], stdin=subprocess.PIPE)
    cache = {}
    for f in range(nf):
        tv = f / FPS
        tj = max(tv - T_INTRO, 0)
        k = next((i for i, tr in enumerate(tramos) if tr["t0"] <= tj < tr["t1"]), len(tramos) - 1)
        tr = tramos[k]
        u = min(max((tj - tr["t0"] - tr["hold"]) / tr["morph"], 0), 1)
        u = 0.5 - 0.5 * np.cos(np.pi * u)
        clave_c = (k, round(u, 3))
        if clave_c not in cache:
            cache = {clave_c: panel(fus[k].cuadro(u))}
        im = base.copy(); dr = ImageDraw.Draw(im, "RGBA")
        im.paste(cache[clave_c], ((W - PANEL) // 2, PY), cache[clave_c])
        dr.rounded_rectangle(((W - PANEL) // 2 - 6, PY - 6, (W + PANEL) // 2 + 6, PY + PANEL + 6), 52,
                             outline=LED if tv < t_rev else (61, 214, 128), width=10)
        anio = int(round(tr["a"].anio + (tr["b"].anio - tr["a"].anio) * u))
        if evo:
            texto(dr, (W / 2, 120), g["gancho"], ajustar(g["gancho"], 86, W - 80), BLANCO, 10)
            texto(dr, (W / 2, 330), str(anio), 190, LED, 14)
            if tv < t_rev:
                texto(dr, (W / 2, PY + PANEL + 110), "WHO IS HE?", 110, BLANCO, 12)
                if tv >= t_h1 and pais:
                    fl = bandera(pais, 130); im.paste(fl, (W // 2 - 300, PY + PANEL + 190), fl)
                    texto(dr, (W / 2 - 140, PY + PANEL + 255), "HINT", 54, LED, 7, anchor="lm")
                if tv >= t_h2:
                    texto(dr, (W / 2 + 140, PY + PANEL + 255), ini, 70, BLANCO, 8)
        else:
            texto(dr, (W / 2, 110), g["titulo"], ajustar(g["titulo"], 96, W - 80), LED, 10)
            texto(dr, (W / 2, 215), "THEN vs NOW", 78, BLANCO, 9)
            if tv < t_rev:
                texto(dr, (W / 2, 350), str(anio), 140, LED if u < 0.5 else (120, 220, 255), 12)
                texto(dr, (W / 2, PY + PANEL + 110), corto(tr["nombre"]), ajustar(corto(tr["nombre"]), 120, W - 100), BLANCO, 12)
                texto(dr, (W / 2, PY + PANEL + 225), f"{k + 1}/{len(tramos)}", 56, (200, 200, 220), 7)
        if tv >= t_rev:
            fl_u = max(0, 1 - (tv - t_rev) / 0.18)
            if fl_u > 0:
                dr.rectangle((0, 0, W, H), fill=(255, 255, 255, int(230 * fl_u)))
            if evo:
                nom = g["jugador"].upper()
                texto(dr, (W / 2, PY + PANEL + 110), nom, ajustar(nom, 120, W - 80), (61, 214, 128), 12)
                texto(dr, (W / 2, PY + PANEL + 235), g["cierre"], ajustar(g["cierre"], 76, W - 80), BLANCO, 9)
            else:
                texto(dr, (W / 2, PY + PANEL + 140), g["cierre"], ajustar(g["cierre"], 110, W - 80), (61, 214, 128), 12)
        ff.stdin.write(np.asarray(im, np.uint8).tobytes())
    ff.stdin.close(); ff.wait()

    mix = beat(dur) * 0.7
    fx = efectos(4)
    def add(s, sig, vol=1.0):
        i = int(s * SR); j = min(len(mix), i + len(sig))
        if 0 <= i < len(mix):
            mix[i:j] += vol * sig[: j - i]
    for n_, s in sonidos:
        add(s, fx[n_], 0.7 if n_ == "whoosh" else 1.0)
    rutas = voces_edge([l for _, l in voz], out)
    dv = np.ones_like(mix)
    for (s, _), r in zip(voz, rutas):
        x = leer_wav(r); i = int(s * SR); j = min(len(mix), i + len(x))
        dv[i:j] = np.minimum(dv[i:j], 0.45); mix[i:j] += 1.05 * x[: j - i]
    mix = np.tanh(mix * dv * 1.3) * 0.9
    with wave.open(str(out / "audio.wav"), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(mix, -1, 1) * 32767).astype(np.int16).tobytes())
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(out / "mudo.mp4"), "-i", str(out / "audio.wav"),
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", str(out / "short.mp4")], check=True)
    (out / "mudo.mp4").unlink()
    cred = json.loads((EP / "creditos_epoca.json").read_text())
    usadas = sorted({tr["a"].foto for tr in tramos} | {tr["b"].foto for tr in tramos})
    (out / "creditos.json").write_text(json.dumps({k: cred[k] for k in usadas}, ensure_ascii=False, indent=1))
    print("listo", out / "short.mp4", f"{dur:.1f}s", [(tr["a"].anio, tr["b"].anio) for tr in tramos])


if __name__ == "__main__":
    main(sys.argv[1])
