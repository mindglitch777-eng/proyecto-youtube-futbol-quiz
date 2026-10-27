#!/usr/bin/env python3
"""
Renderiza y valida todos los videos V2 (copas, ring escape, trophy race, carreras v5).
Chequea por video: terminó sin error, 1080x1920, 60 fps, tiene audio, duración en rango, ganador = el del guion,
y peso. Deja salida/prueba_v2.json con el resultado de cada uno.

Uso: python3 probar_todo.py [--solo-validar] [filtro]
"""
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TRABAJOS = (
    [("render_copa_v2.py", f"copa_0{i}", f"copa_0{i}_v2", (40, 62)) for i in (1, 2, 3)]
    + [("render_ring_escape.py", f"ring_0{i}", f"ring_0{i}", (18, 40)) for i in (1, 2, 3)]
    + [("render_trophy_race.py", "trofeos_01", "trofeos_01", (25, 45))]
    + [("render_carrera_v5.py", c, c + "_v5", (16, 48)) for c in
       ("carrera_02", "carrera_03", "carrera_04", "carrera_05", "carrera_07",
        "carrera_08", "carrera_09", "carrera_10", "carrera_11")]
)


def ganador_esperado(g):
    if g.get("ganador"):
        return g["ganador"]
    ruta = g.get("ruta", {})
    return next((k for k, v in ruta.items() if v == "F"), None)


def probe(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,width,height,r_frame_rate:format=duration",
                        "-of", "json", str(p)], capture_output=True, text=True)
    return json.loads(r.stdout)


def validar(script, gid, carpeta, rango, log):
    g = json.loads((ROOT / "guiones" / f"{gid}.json").read_text())
    out = ROOT / "salida" / carpeta
    errores = []
    principal = out / "short.mp4"
    if not principal.exists():
        return dict(id=gid, ok=False, errores=["no se generó short.mp4", log[-400:]])
    info = probe(principal)
    v = next(s for s in info["streams"] if s["codec_type"] == "video")
    if (v["width"], v["height"]) != (1080, 1920):
        errores.append(f"resolución {v['width']}x{v['height']}")
    if v["r_frame_rate"] != "60/1":
        errores.append(f"fps {v['r_frame_rate']}")
    if not any(s["codec_type"] == "audio" for s in info["streams"]):
        errores.append("sin audio")
    dur = float(info["format"]["duration"])
    if not rango[0] <= dur <= rango[1]:
        errores.append(f"duración {dur:.1f}s fuera de {rango}")
    res = json.loads((out / "resultado.json").read_text())
    gan = res.get("ganador") or res.get("campeon") or max(res.get("total", {"": 0}), key=res.get("total", {"": 0}).get)
    esp = ganador_esperado(g)
    if esp and gan != esp:
        errores.append(f"ganó {gan}, el guion pedía {esp}")
    mb = principal.stat().st_size / 1e6
    return dict(id=gid, carpeta=carpeta, ok=not errores, errores=errores, dur=round(dur, 1), mb=round(mb, 1), ganador=gan)


def correr(t):
    script, gid, carpeta, rango = t
    if "--solo-validar" not in sys.argv:
        r = subprocess.run([sys.executable, script, f"guiones/{gid}.json"], cwd=ROOT, capture_output=True, text=True)
        log = r.stdout + r.stderr
        if r.returncode != 0:
            return dict(id=gid, ok=False, errores=[f"exit {r.returncode}", log[-600:]])
    else:
        log = ""
    res = validar(script, gid, carpeta, rango, log)
    print(("OK  " if res["ok"] else "FALLA ") + gid, res.get("dur"), res.get("mb"), res.get("ganador"), res["errores"], flush=True)
    return res


if __name__ == "__main__":
    filtro = next((a for a in sys.argv[1:] if not a.startswith("--")), "")
    trabajos = [t for t in TRABAJOS if filtro in t[1]]
    with ThreadPoolExecutor(2) as ex:
        resultados = list(ex.map(correr, trabajos))
    (ROOT / "salida" / "prueba_v2.json").write_text(json.dumps(resultados, ensure_ascii=False, indent=1))
    malos = [r for r in resultados if not r["ok"]]
    print(f"\n{len(resultados) - len(malos)}/{len(resultados)} OK")
    sys.exit(1 if malos else 0)
