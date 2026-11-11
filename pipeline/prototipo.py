#!/usr/bin/env python3
"""
FÁBRICA DE PROTOTIPOS (máquina, sin IA · 11/11): cada propuesta del Gerente IA llega al CEO con una PRUEBA VISUAL.

El Gerente (o el Ingeniero) escribe pipeline/propuestas/<id>.json y hace push; el workflow prototipo.yml corre esto:
  {"id": "p001", "issue": 12, "titulo": "Bajar STOP a 1 por día", "que_mostrar": "texto corto",
   "slots": [{"tipo": "q20costo"}, {"tipo": "rueda"}],          # videos de muestra a renderizar (formatos existentes o nuevos con listo:false)
   "grilla": {"antes": ["09:00 rueda", ...], "despues": ["09:00 rueda", ...]}}   # opcional: cómo cambia el día
Hace: renderiza las muestras (sin gastar la memoria anti-repetición del canal), arma una hoja con 4 cuadros de cada video
(+ la grilla antes/después si viene), deja todo en reports/propuestas/<id>/ y escribe propuestas/<id>.json con
"prototipo": {...}. El workflow sube los videos a un Release "propuesta-<id>" y comenta en el Issue con la imagen y los links.
Uso: python3 pipeline/prototipo.py  (procesa las propuestas que todavía no tienen prototipo)
"""
import json
import random
import shutil
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
PROP = RAIZ / "pipeline" / "propuestas"
DATOS = RAIZ / "pipeline" / "datos"


def cuadros(mp4, n=4, alto=480):
    from PIL import Image
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(mp4)],
                               capture_output=True, text=True).stdout.strip() or 6)
    ims = []
    for k, u in enumerate((0.0, 0.25, 0.55, 0.85)[:n]):
        out = mp4.with_suffix(f".c{k}.png")
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", f"{u * dur:.2f}", "-i", str(mp4), "-frames:v", "1",
                        "-vf", f"scale=-2:{alto}", str(out)], check=True)
        ims.append(Image.open(out).convert("RGB")); out.unlink()
    return ims, dur


def hoja(filas, grilla, titulo, destino):
    from PIL import Image, ImageDraw, ImageFont
    try:
        f_t = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 34)
        f_s = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
    except Exception:
        f_t = f_s = ImageFont.load_default()
    ancho = max([sum(i.width for i in ims) + 20 * (len(ims) + 1) for _, ims, _ in filas] + [1400])
    alto = 90 + sum(ims[0].height + 70 for _, ims, _ in filas) + (60 + 34 * max(len(grilla.get("antes", [])), len(grilla.get("despues", []))) if grilla else 0)
    im = Image.new("RGB", (ancho, alto), (16, 20, 28)); d = ImageDraw.Draw(im)
    d.text((20, 24), titulo, font=f_t, fill=(255, 222, 0)); y = 90
    for nombre, ims, dur in filas:
        d.text((20, y), f"{nombre} · {dur:.1f} s · cuadros al 0 %, 25 %, 55 % y 85 %", font=f_s, fill=(230, 230, 230)); y += 40
        x = 20
        for c in ims:
            im.paste(c, (x, y)); x += c.width + 20
        y += ims[0].height + 30
    if grilla:
        d.text((20, y), "Grilla del día · ANTES", font=f_s, fill=(255, 120, 120)); d.text((ancho // 2, y), "DESPUÉS", font=f_s, fill=(120, 255, 140)); y += 40
        for k in range(max(len(grilla.get("antes", [])), len(grilla.get("despues", [])))):
            a = grilla.get("antes", [])[k] if k < len(grilla.get("antes", [])) else ""
            b = grilla.get("despues", [])[k] if k < len(grilla.get("despues", [])) else ""
            d.text((20, y), a, font=f_s, fill=(230, 230, 230)); d.text((ancho // 2, y), b, font=f_s, fill=(230, 230, 230)); y += 34
    im.save(destino, quality=88)


def procesar(p):
    pr = json.loads(p.read_text())
    if pr.get("prototipo"):
        return None
    pid = pr["id"]; dest = RAIZ / "reports" / "propuestas" / pid; dest.mkdir(parents=True, exist_ok=True)
    sem = RAIZ / "produccion" / "prototipos" / pid; sem.mkdir(parents=True, exist_ok=True)
    resguardo = {n: (DATOS / n).read_bytes() for n in ("variedad.json", "huellas.json") if (DATOS / n).exists()}
    filas, videos = [], []
    try:
        if pr.get("slots"):
            sys.path.insert(0, str(RAIZ / "produccion"))
            import fabrica
            dia = (date.today() + timedelta(days=30)).isoformat()
            slots = [dict(fecha=s.get("fecha", dia), hora=s.get("hora", f"{12 + i:02d}:00"), tipo=s["tipo"], **{k: v for k, v in s.items() if k not in ("fecha", "hora", "tipo")})
                     for i, s in enumerate(pr["slots"])]
            man, err = fabrica.fabricar(slots, sem, random.Random(pid), prefijo=pid, procesos=3)
            for m in man:
                mp4 = sem / m["archivo"]
                if mp4.exists():
                    ims, dur = cuadros(mp4)
                    filas.append((f"{m['formato']} · \"{m['titulo'][:60]}\"", ims, dur)); videos.append(str(mp4.relative_to(RAIZ)))
    finally:
        for n, b in resguardo.items():                                         # el prototipo no gasta la memoria anti-repetición
            (DATOS / n).write_bytes(b)
    hoja(filas, pr.get("grilla"), f"Propuesta {pid}: {pr.get('titulo', '')}"[:90], dest / "hoja.jpg")
    for f in sem.glob("*_solo_efectos.mp4"):
        f.unlink()
    pr["prototipo"] = dict(hoja=f"reports/propuestas/{pid}/hoja.jpg", videos=videos, release=f"propuesta-{pid}")
    p.write_text(json.dumps(pr, ensure_ascii=False, indent=1))
    return pr


def main():
    import os
    hechos = [x for x in (procesar(p) for p in sorted(PROP.glob("*.json"))) if x]
    salida = Path(os.environ.get("PROTO_SALIDA", RAIZ / "_prototipos.jsonl"))       # resultado aparte (la fábrica imprime otras cosas)
    salida.write_text("".join(json.dumps(dict(id=pr["id"], issue=pr.get("issue"), videos=pr["prototipo"]["videos"],
                                               hoja=pr["prototipo"]["hoja"]), ensure_ascii=False) + "\n" for pr in hechos))
    print(f"prototipos hechos: {len(hechos)}")


if __name__ == "__main__":
    main()
