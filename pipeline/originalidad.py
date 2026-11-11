#!/usr/bin/env python3
"""
AUDITOR DE ORIGINALIDAD (sin IA, 11/11): mide qué tan "plantilla" se ve el canal, porque la política de YouTube de
contenido inauténtico (producido en masa, repetitivo, de plantilla con poca variación) es el mayor riesgo para monetizar.

Qué mide (todo determinista):
1. Huella visual de cada video que produce la fábrica (hash perceptual de 3 cuadros: 0,5 s, mitad y final). Dos videos con
   huella casi igual = "casi idénticos" para un revisor.
2. Concentración de plantilla: qué % de las subidas de los últimos 7 días es el mismo formato.
3. Títulos: parecido promedio de cada título con el más parecido de los últimos 7 días.
4. Música: cuántas pistas distintas se usaron en los últimos 30 videos.
Salida: datos/huellas.json (memoria de huellas) y datos/originalidad.json (el índice que leen el Gerente y el tablero).
Uso: fabrica.py llama registrar() al terminar cada video; gerente.py llama reporte().
"""
import difflib
import json
import re
import subprocess
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
DATOS = RAIZ / "pipeline" / "datos"
ART = timezone(timedelta(hours=-3))
UMBRAL_CASI_IGUAL = 10                    # bits distintos (de 192) por debajo de los cuales dos videos se ven casi iguales


def _cargar(n, d):
    p = DATOS / n
    try:
        return json.loads(p.read_text()) if p.exists() else d
    except Exception:
        return d


def _dhash(png_bytes):
    from io import BytesIO
    from PIL import Image
    im = Image.open(BytesIO(png_bytes)).convert("L").resize((9, 8))
    px = list(im.getdata())
    return "".join("1" if px[r * 9 + c] > px[r * 9 + c + 1] else "0" for r in range(8) for c in range(8))


def huella(ruta):
    """3 cuadros → 192 bits (como texto de 0/1). None si no se puede leer el video."""
    try:
        dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(ruta)],
                                   capture_output=True, text=True, timeout=60).stdout.strip())
        bits = ""
        for t in (0.5, dur / 2, max(0.5, dur - 0.5)):
            png = subprocess.run(["ffmpeg", "-loglevel", "error", "-ss", f"{t:.2f}", "-i", str(ruta), "-frames:v", "1", "-f", "image2pipe",
                                  "-vcodec", "png", "-"], capture_output=True, timeout=60).stdout
            bits += _dhash(png)
        return bits
    except Exception:
        return None


def distancia(a, b):
    return sum(x != y for x, y in zip(a, b))


def registrar(vid, ruta, tipo, fecha, musica=None):
    h = huella(ruta)
    if not h:
        return None
    hs = _cargar("huellas.json", [])
    hs = [x for x in hs if x["id"] != vid]
    previos = hs[-80:]
    cerca = min(((distancia(h, x["h"]), x["id"]) for x in previos), default=(999, None))
    hs.append(dict(id=vid, tipo=tipo, fecha=fecha, h=h, musica=musica, mas_cercano=cerca[1], distancia=cerca[0]))
    (DATOS / "huellas.json").write_text(json.dumps(hs[-400:], ensure_ascii=False))
    return cerca


def _norm(t):
    t = re.sub(r"#\w+", "", t.lower())
    return re.sub(r"[^a-z0-9áéíóúñü%' ]+", " ", t).split()


def reporte():
    hoy = datetime.now(ART).date()
    pub = [p for p in _cargar("publicados.json", []) if p.get("video_id") and not p.get("reemplazado")]
    sem = [p for p in pub if hoy - timedelta(days=7) <= date.fromisoformat(p["fecha"]) <= hoy]
    tipos = {}
    for p in sem:
        tipos[p.get("tipo")] = tipos.get(p.get("tipo"), 0) + 1
    top = max(tipos.items(), key=lambda kv: kv[1]) if tipos else (None, 0)
    conc = top[1] / max(1, len(sem))
    tits = [p.get("titulo", "") for p in sem]
    sims = []
    for i, t in enumerate(tits):
        otros = tits[:i] + tits[i + 1:]
        if otros:
            sims.append(max(difflib.SequenceMatcher(None, _norm(t), _norm(o)).ratio() for o in otros))
    sim_tit = sum(sims) / len(sims) if sims else 0
    hs = _cargar("huellas.json", [])[-60:]
    casi = [x for x in hs if x.get("distancia", 999) <= UMBRAL_CASI_IGUAL]
    musicas = [x.get("musica") for x in hs[-30:] if x.get("musica")]
    # índice 0-100 (100 = muy variado): penaliza concentración de plantilla, títulos parecidos y videos casi idénticos
    indice = 100
    indice -= max(0, conc - 0.30) * 150                                        # que un solo formato pase el 30 % de la semana
    indice -= max(0, sim_tit - 0.55) * 150                                     # títulos que se parecen más de 55 % en promedio
    indice -= (len(casi) / max(1, len(hs))) * 100                              # videos casi idénticos a otro
    indice = max(0, round(indice))
    alertas = []
    if conc > 0.40:
        alertas.append(f"{top[0]} es el {conc:.0%} de las subidas de la semana: demasiado de la misma plantilla.")
    if sim_tit > 0.65:
        alertas.append(f"Los títulos se parecen {sim_tit:.0%} en promedio: falta variedad de frases.")
    if hs and len(casi) / len(hs) > 0.15:
        alertas.append(f"{len(casi)} de los últimos {len(hs)} videos son casi idénticos a otro (misma imagen en los mismos momentos).")
    if musicas and len(set(musicas)) < 5:
        alertas.append(f"Solo {len(set(musicas))} pistas de música distintas en los últimos {len(musicas)} videos.")
    out = dict(fecha=hoy.isoformat(), indice=indice, subidas_semana=len(sem), formato_mas_usado=top[0], concentracion=round(conc, 2),
               parecido_titulos=round(sim_tit, 2), casi_identicos=len(casi), medidos=len(hs), musicas_distintas=len(set(musicas)),
               reparto_semana=tipos, alertas=alertas,
               lectura=("BIEN: variado" if indice >= 75 else "OJO: se empieza a ver repetitivo" if indice >= 55 else "RIESGO: parece producción en masa"))
    (DATOS / "originalidad.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
    return out


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "registrar":                    # originalidad.py registrar <id> <ruta> <tipo> <fecha>
        print(registrar(*sys.argv[2:6]))
    else:
        print(json.dumps(reporte(), ensure_ascii=False, indent=1))
