#!/usr/bin/env python3
"""
Mide shorts de forma exacta: baja el video en baja calidad a una carpeta temporal,
saca métricas con ffmpeg y BORRA el video. Al repo solo van las métricas y una
hoja de contacto (1 cuadro por segundo, chiquita) para mirar el estilo.

Ojo: descargar videos de YouTube va contra sus Términos de Servicio. Es para
análisis interno, nunca para resubir nada. Si YouTube bloquea la descarga
("Sign in to confirm you're not a bot"), el video queda marcado y se sigue.

Por video guarda en data/raw/medicion/<id>.json:
  - duracion_s, fps, resolución
  - cortes_s: segundos donde cambia la escena (ffmpeg scene > UMBRAL)
  - volumen_por_segundo_db: volumen medio de cada segundo (para ver silencios/subidas)
  - silencios: tramos sin audio
y en data/raw/medicion/<id>.jpg la hoja de contacto.

Uso: python3 research/medir_video.py ID [ID ...]  |  --lista archivo.json
Requiere: yt-dlp, ffmpeg.
"""
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "raw" / "medicion"
OUT.mkdir(parents=True, exist_ok=True)
UMBRAL = 0.3


def sh(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def medir(vid):
    dest = OUT / f"{vid}.json"
    if dest.exists() and "error" not in json.loads(dest.read_text()):
        return
    with tempfile.TemporaryDirectory() as tmp:
        f = Path(tmp) / "v.mp4"
        r = sh(["yt-dlp", "-q", "-f", "best[height<=480][ext=mp4]/best[height<=480]/worst", "-o", str(f),
                f"https://www.youtube.com/shorts/{vid}"])
        if r.returncode or not f.exists():
            dest.write_text(json.dumps({"video_id": vid, "error": r.stderr[-400:]}, ensure_ascii=False))
            print(f"{vid}: no se pudo bajar: {r.stderr.strip()[-150:]}", file=sys.stderr)
            return
        info = json.loads(sh(["ffprobe", "-v", "quiet", "-print_format", "json", "-show_streams", "-show_format", str(f)]).stdout)
        dur = float(info["format"]["duration"])
        vs = next(s for s in info["streams"] if s["codec_type"] == "video")
        # cortes de escena
        r = sh(["ffmpeg", "-i", str(f), "-vf", f"select='gt(scene,{UMBRAL})',showinfo", "-an", "-f", "null", "-"])
        cortes = [round(float(t), 2) for t in re.findall(r"pts_time:([\d.]+)", r.stderr)]
        # volumen por segundo
        r = sh(["ffmpeg", "-i", str(f), "-af", "asetnsamples=n=44100,astats=metadata=1:reset=1,"
                "ametadata=print:key=lavfi.astats.Overall.RMS_level", "-vn", "-f", "null", "-"])
        vol = [None if v in ("-inf", "inf") else round(float(v), 1)
               for v in re.findall(r"RMS_level=([-\w.]+)", r.stderr)]
        r = sh(["ffmpeg", "-i", str(f), "-af", "silencedetect=n=-40dB:d=0.4", "-vn", "-f", "null", "-"])
        ini = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", r.stderr)]
        fin = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", r.stderr)]
        # hoja de contacto: 1 cuadro/s, 10 columnas, 108 px de ancho
        filas = max(1, int(dur) // 10 + 1)
        sh(["ffmpeg", "-y", "-i", str(f), "-vf", f"fps=1,scale=108:-1,tile=10x{filas}", "-frames:v", "1",
            "-q:v", "6", str(OUT / f"{vid}.jpg")])
    res = {"video_id": vid, "duracion_s": round(dur, 2), "fps": vs.get("r_frame_rate"),
           "resolucion": f"{vs.get('width')}x{vs.get('height')}", "umbral_escena": UMBRAL,
           "cortes_s": cortes, "n_cortes": len(cortes),
           "cortes_por_10s": round(10 * len(cortes) / dur, 2) if dur else None,
           "volumen_por_segundo_db": vol,
           "silencios": [[round(a, 2), round(b, 2)] for a, b in zip(ini, fin)]}
    dest.write_text(json.dumps(res, ensure_ascii=False, indent=1))
    print(f"{vid}: {dur:.1f}s, {len(cortes)} cortes", file=sys.stderr)


if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "--lista":
        a = json.loads(Path(a[1]).read_text())
    for vid in a:
        medir(vid)
