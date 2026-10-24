#!/usr/bin/env python3
"""
Locución con Gemini TTS (gratis con GEMINI_API_KEY). Cachea por texto en assets/voz/.

Controles de calidad (el TTS a veces agrega palabras por su cuenta):
1. Pedido estricto: "leé exactamente esta línea y nada más".
2. Duración máxima según la cantidad de palabras; si se pasa, se regenera.
3. Transcripción con Gemini: si no coincide con el texto, se regenera.
Después se recortan los silencios y se acelera un poco (ritmo de Shorts).
"""
import base64
import hashlib
import json
import os
import re
import subprocess
import time
import wave
from pathlib import Path

import numpy as np
import requests

ROOT = Path(__file__).resolve().parent
CACHE = ROOT / "assets" / "voz"
CACHE.mkdir(parents=True, exist_ok=True)
MODELOS = os.environ.get("GEMINI_TTS_MODELS", "gemini-2.5-flash-preview-tts,gemini-3.8-flash-tts").split(",")
MODELO_TRANSCRIBE = os.environ.get("GEMINI_STT_MODEL", "gemini-3.1-flash-lite")
URL = "https://generativelanguage.googleapis.com/v1beta/models/{}:generateContent"
TEMPO = 1.1


def _post(model, body):
    return requests.post(URL.format(model), headers={"x-goog-api-key": os.environ["GEMINI_API_KEY"]}, json=body, timeout=120)


def _normal(s):
    return re.sub(r"[^a-z0-9 ]", "", s.lower().replace("é", "e").replace("one percent", "1%").replace("1%", "one percent")).split()


def _transcribe(pcm):
    import io
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(24000); w.writeframes(pcm)
    body = {"contents": [{"parts": [{"inline_data": {"mime_type": "audio/wav", "data": base64.b64encode(buf.getvalue()).decode()}},
                                    {"text": "Transcribe exactly what is said. Output only the words."}]}]}
    r = _post(MODELO_TRANSCRIBE, body)
    if r.status_code != 200:
        return None
    return "".join(p.get("text", "") for p in r.json()["candidates"][0]["content"]["parts"])


def _recortar(pcm, sr=24000, umbral=0.02):
    x = np.frombuffer(pcm, np.int16).astype(np.float32) / 32768
    env = np.convolve(np.abs(x), np.ones(240) / 240, mode="same")
    idx = np.where(env > umbral)[0]
    if len(idx) == 0:
        return pcm
    a, b = max(0, idx[0] - int(0.03 * sr)), min(len(x), idx[-1] + int(0.08 * sr))
    return (x[a:b] * 32767).astype(np.int16).tobytes()


def voz(texto, estilo, voz_nombre="Puck"):
    h = hashlib.sha1(f"v2|{texto}|{estilo}|{voz_nombre}".encode()).hexdigest()[:14]
    dest = CACHE / f"{h}.wav"
    if dest.exists():
        return dest
    max_dur = 0.45 * len(texto.split()) + 1.2
    prompt = f"{estilo}. Read EXACTLY the following line, word for word, and say nothing else:\n{texto}"
    body = {"contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseModalities": ["AUDIO"],
                                 "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voz_nombre}}}}}
    ultimo = None
    for intento in range(6):
        for m in MODELOS:
            r = _post(m, body)
            if r.status_code != 200:
                ultimo = f"{m} {r.status_code}"
                continue
            pcm = _recortar(base64.b64decode(r.json()["candidates"][0]["content"]["parts"][0]["inlineData"]["data"]))
            dur = len(pcm) / 2 / 24000
            trans = _transcribe(pcm)
            ok_dur = dur <= max_dur
            ok_txt = trans is None or _normal(trans) == _normal(texto)
            if ok_dur and ok_txt:
                tmp = dest.with_suffix(".raw.wav")
                with wave.open(str(tmp), "wb") as w:
                    w.setnchannels(1); w.setsampwidth(2); w.setframerate(24000); w.writeframes(pcm)
                subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(tmp), "-filter:a", f"atempo={TEMPO}", str(dest)], check=True)
                tmp.unlink()
                (CACHE / f"{h}.json").write_text(json.dumps({"texto": texto, "estilo": estilo, "voz": voz_nombre, "modelo": m,
                                                             "transcripcion": trans, "dur_s": round(dur / TEMPO, 2)}))
                return dest
            ultimo = f"{m}: dur {dur:.1f}s (máx {max_dur:.1f}) / transcripción '{trans}'"
            print(f"  voz rechazada ({texto[:30]}): {ultimo}")
        time.sleep(5 * (intento + 1))
    raise RuntimeError(f"TTS falló para '{texto}': {ultimo}")


def _segmentos(x, sr, n_esperado, gap_min=0.32):
    """Corta por silencios; une los huecos más chicos hasta tener n_esperado segmentos."""
    env = np.convolve(np.abs(x), np.ones(int(0.02 * sr)) / int(0.02 * sr), mode="same")
    voz_on = env > 0.02
    idx = np.where(voz_on)[0]
    if not len(idx):
        return None
    # tramos con voz
    cortes = np.where(np.diff(idx) > gap_min * sr)[0]
    inicios = [idx[0]] + [idx[c + 1] for c in cortes]
    fines = [idx[c] for c in cortes] + [idx[-1]]
    segs = list(zip(inicios, fines))
    # descartar ruidos muy cortos (< 0.15 s)
    segs = [s for s in segs if s[1] - s[0] > 0.15 * sr]
    while len(segs) > n_esperado:
        gaps = [segs[i + 1][0] - segs[i][1] for i in range(len(segs) - 1)]
        i = int(np.argmin(gaps)); segs[i:i + 2] = [(segs[i][0], segs[i + 1][1])]
    return segs if len(segs) == n_esperado else None


def voces_guion(lineas, estilo, voz_nombre="Puck"):
    """Una sola locución para todo el guion, cortada por silencios. Devuelve una ruta .wav por línea."""
    h = hashlib.sha1(f"g2|{'|'.join(lineas)}|{estilo}|{voz_nombre}".encode()).hexdigest()[:14]
    rutas = [CACHE / f"{h}_{i:02d}.wav" for i in range(len(lineas))]
    if all(r.exists() for r in rutas):
        return rutas
    prompt = (f"{estilo}. Read the following lines in order, word for word. After each line make a clear one-second pause. "
              f"Do not add anything else, no intro, no outro:\n\n" + "\n\n".join(lineas))
    body = {"contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseModalities": ["AUDIO"],
                                 "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voz_nombre}}}}}
    sr = 24000; ultimo = None
    for intento in range(6):
        for m in MODELOS:
            r = _post(m, body)
            if r.status_code != 200:
                ultimo = f"{m} {r.status_code}"; continue
            pcm = base64.b64decode(r.json()["candidates"][0]["content"]["parts"][0]["inlineData"]["data"])
            x = np.frombuffer(pcm, np.int16).astype(np.float32) / 32768
            segs = _segmentos(x, sr, len(lineas))
            if not segs:
                ultimo = f"{m}: no pude cortar en {len(lineas)} frases"; print("  " + ultimo); continue
            # control: cada tramo no puede ser mucho más largo que su frase
            malos = [i for i, (a, b) in enumerate(segs) if (b - a) / sr > 0.5 * len(lineas[i].split()) + 1.3]
            trans = _transcribe((x[segs[0][0]:segs[-1][1]] * 32767).astype(np.int16).tobytes())
            if malos or (trans and _normal(trans) != sum((_normal(l) for l in lineas), [])):
                ultimo = f"{m}: tramos largos {malos} / transcripción '{trans}'"; print("  voz rechazada: " + ultimo[:200]); continue
            for i, (a, b) in enumerate(segs):
                a = max(0, a - int(0.03 * sr)); b = min(len(x), b + int(0.08 * sr))
                tmp = rutas[i].with_suffix(".raw.wav")
                with wave.open(str(tmp), "wb") as w:
                    w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((x[a:b] * 32767).astype(np.int16).tobytes())
                subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(tmp), "-filter:a", f"atempo={TEMPO}", str(rutas[i])], check=True)
                tmp.unlink()
            (CACHE / f"{h}.json").write_text(json.dumps({"lineas": lineas, "modelo": m, "transcripcion": trans}, ensure_ascii=False))
            return rutas
        time.sleep(20 * (intento + 1))
    raise RuntimeError(f"TTS de guion falló: {ultimo}")
