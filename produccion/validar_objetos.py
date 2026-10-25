#!/usr/bin/env python3
"""
Gemini mira cada foto candidata y confirma si es la pelota OFICIAL de ese Mundial (por el texto impreso, el diseño y el
nombre del archivo de Commons), si la pelota es la protagonista, si está entera y nítida.
Uso: GEMINI_API_KEY=... python3 validar_objetos.py balones_v2   -> assets/objetos/<serie>/validacion.json
"""
import base64
import io
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests
from PIL import Image

ROOT = Path(__file__).resolve().parent
KEY = os.environ.get("GEMINI_API_KEY")
MODELS = ["gemini-3.5-flash", "gemini-3.6-flash", "gemini-flash-latest", "gemini-3.5-flash-lite"]
URL = "https://generativelanguage.googleapis.com/v1beta/models/{}:generateContent"
OFICIAL = {1930: "Tiento (first half) / T-Model (second half), leather", 1934: "Federale 102", 1938: "Allen",
           1950: "Duplo T / Super Duplo T", 1954: "Swiss World Champion", 1958: "Top Star", 1962: "Crack (Señor Zamora)",
           1966: "Slazenger Challenge 4-Star (orange or yellow leather)", 1970: "adidas Telstar (Telstar Durlast)",
           1974: "adidas Telstar Durlast / Chile Durlast", 1978: "adidas Tango Durlast (Tango Argentina)",
           1982: "adidas Tango España", 1986: "adidas Azteca", 1990: "adidas Etrusco Unico", 1994: "adidas Questra (USA 94)",
           1998: "adidas Tricolore", 2002: "adidas Fevernova", 2006: "adidas +Teamgeist", 2010: "adidas Jabulani",
           2014: "adidas Brazuca", 2018: "adidas Telstar 18", 2022: "adidas Al Rihla", 2026: "adidas Trionda"}
PROMPT = """You are verifying photos for a "World Cup ball evolution" video. Year: {anio}. Official ball: {oficial}.
Commons file name: "{archivo}".
Look at the image (read any printed text on the ball) and answer ONLY JSON:
{{"es_la_pelota_oficial": true/false (is this the official {anio} World Cup ball model or its official match/final version, NOT a replica of another tournament like a Euro/Olympics/club ball, NOT a different year),
 "confianza": 0.0-1.0,
 "pelota_protagonista": true/false (the ball is the main subject, large and fully visible, not tiny, not cut off),
 "nitida": true/false,
 "texto_visible": "text you can read on the ball",
 "motivo": "short reason"}}"""


def b64(path):
    im = Image.open(path).convert("RGB"); im.thumbnail((768, 768))
    buf = io.BytesIO(); im.save(buf, "JPEG", quality=88)
    return base64.b64encode(buf.getvalue()).decode()


def uno(args):
    clave, info, d = args
    body = {"contents": [{"parts": [{"inline_data": {"mime_type": "image/jpeg", "data": b64(d / f"{clave}.jpg")}},
                                    {"text": PROMPT.format(anio=info["anio"], oficial=OFICIAL.get(info["anio"], "?"),
                                                           archivo=info["archivo"])}]}],
            "generationConfig": {"temperature": 0, "responseMimeType": "application/json"}}
    for ronda in range(4):
        for m in MODELS:
            try:
                r = requests.post(URL.format(m), headers={"x-goog-api-key": KEY}, json=body, timeout=120)
            except requests.RequestException:
                continue
            if r.status_code == 200:
                try:
                    a = json.loads("".join(p.get("text", "") for p in r.json()["candidates"][0]["content"]["parts"]))
                    a = a[0] if isinstance(a, list) else a
                    return clave, a
                except Exception:
                    continue
        time.sleep(8 * (ronda + 1))
    return clave, None


def main(serie):
    d = ROOT / "assets" / "objetos" / serie
    cred = json.loads((d / "creditos.json").read_text())
    val_p = d / "validacion.json"
    val = json.loads(val_p.read_text()) if val_p.exists() else {}
    pend = []
    for k, v in cred.items():
        if k in val:
            continue
        try:
            Image.open(d / f"{k}.jpg").verify()
        except Exception:
            continue
        pend.append((k, v, d))
    with ThreadPoolExecutor(4) as ex:
        for clave, a in ex.map(uno, pend):
            if a:
                val[clave] = a
                print(clave, a.get("es_la_pelota_oficial"), a.get("confianza"), a.get("pelota_protagonista"), str(a.get("texto_visible") or "")[:50], flush=True)
    val_p.write_text(json.dumps(val, ensure_ascii=False, indent=1))
    # mejor foto por año: oficial + protagonista + nítida, mayor confianza
    elegidas = {}
    for k, a in val.items():
        if a.get("es_la_pelota_oficial") and a.get("pelota_protagonista") and a.get("nitida") and a.get("confianza", 0) >= 0.7:
            anio = cred[k]["anio"]
            if anio not in elegidas or a["confianza"] > val[elegidas[anio]]["confianza"]:
                elegidas[anio] = k
    print("elegidas:", dict(sorted(elegidas.items())))
    print("sin foto confirmada:", sorted(set(OFICIAL) - set(elegidas)))
    (d / "elegidas.json").write_text(json.dumps(dict(sorted(elegidas.items())), indent=1))


if __name__ == "__main__":
    main(sys.argv[1])
