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
MODELOS = os.environ.get("GEMINI_TTS_MODELS", "gemini-2.5-flash-preview-tts,gemini-3.8-flash-tts,gemini-3.8-flash-lite-tts").split(",")
MODELO_TRANSCRIBE = os.environ.get("GEMINI_STT_MODEL", "gemini-3.1-flash-lite")
URL = "https://generativelanguage.googleapis.com/v1beta/models/{}:generateContent"
TEMPO = 1.1


def _post(model, body):
    return requests.post(URL.format(model), headers={"x-goog-api-key": os.environ["GEMINI_API_KEY"]}, json=body, timeout=120)


def _normal(s):
    import unicodedata
    s = unicodedata.normalize("NFKD", s.lower()).encode("ascii", "ignore").decode()
    s = s.replace("one percent", "1%").replace("1%", "one percent").replace("-", " ")
    return re.sub(r"[^a-z0-9 ]", "", s).split()


def _parecido(a, b):
    """Proporción de palabras de b que aparecen en orden en a (tolerante a nombres mal transcriptos)."""
    import difflib
    sm = difflib.SequenceMatcher(None, a, b)
    return sum(m.size for m in sm.get_matching_blocks()) / max(len(b), 1)


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


def _segmentos(x, sr, lineas):
    """Elige los cortes entre frases: entre todos los micro-silencios, los que dejan cada tramo
    con la duración más parecida a la esperada (proporcional a las letras de la frase)."""
    n = len(lineas)
    win = int(0.02 * sr)
    env = np.convolve(np.abs(x), np.ones(win) / win, mode="same")
    activo = env > 0.015
    idx = np.where(activo)[0]
    if not len(idx):
        return None
    ini, fin = idx[0], idx[-1]
    # huecos candidatos (>= 0.08 s de silencio)
    huecos = []
    i = ini
    while i < fin:
        if not activo[i]:
            j = i
            while j < fin and not activo[j]:
                j += 1
            if (j - i) / sr >= 0.08:
                huecos.append(((i + j) // 2, (j - i) / sr, i, j))
            i = j
        else:
            i += 1
    if len(huecos) < n - 1:
        return None
    letras = np.array([len(l) for l in lineas], float)
    total = (fin - ini) / sr - sum(h[1] for h in huecos) * 0.5
    esperado = total * letras / letras.sum()
    pos = [ini] + [h[0] for h in huecos] + [fin]
    largo_hueco = [0] + [h[1] for h in huecos] + [0]
    m = len(pos)
    INF = 1e18
    # dp[k][j]: mejor costo usando k frases terminando en el corte j
    dp = np.full((n + 1, m), INF); prev = np.zeros((n + 1, m), int); dp[0][0] = 0
    for k in range(1, n + 1):
        for j in range(1, m):
            if k == n and j != m - 1:
                continue
            for i0 in range(j):
                if dp[k - 1][i0] >= INF:
                    continue
                d = (pos[j] - pos[i0]) / sr
                c = dp[k - 1][i0] + ((d - esperado[k - 1]) / max(esperado[k - 1], 0.4)) ** 2 - 0.8 * min(largo_hueco[j], 0.6)
                if c < dp[k][j]:
                    dp[k][j] = c; prev[k][j] = i0
    if dp[n][m - 1] >= INF:
        return None
    cortes = [m - 1]
    for k in range(n, 0, -1):
        cortes.append(prev[k][cortes[-1]])
    cortes = cortes[::-1]
    segs = []
    for k in range(n):
        a_, b_ = pos[cortes[k]], pos[cortes[k + 1]]
        # recortar silencio en los bordes del tramo
        sub = np.where(activo[a_:b_])[0]
        segs.append((a_ + sub[0], a_ + sub[-1]) if len(sub) else (a_, b_))
    return segs


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
            (CACHE / "_ultimo_crudo.raw").write_bytes(pcm)      # para depurar cortes sin gastar otro pedido
            segs = _segmentos(x, sr, lineas)
            if not segs:
                ultimo = f"{m}: no pude cortar en {len(lineas)} frases"; print("  " + ultimo); continue
            # control: cada tramo no puede ser mucho más largo que su frase
            malos = [i for i, (a, b) in enumerate(segs) if (b - a) / sr > 0.5 * len(lineas[i].split()) + 1.3]
            trans = _transcribe((x[segs[0][0]:segs[-1][1]] * 32767).astype(np.int16).tobytes())
            if malos or (trans and _parecido(_normal(trans), sum((_normal(l) for l in lineas), [])) < 0.85):
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
