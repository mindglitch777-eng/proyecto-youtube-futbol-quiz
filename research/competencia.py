#!/usr/bin/env python3
"""
Análisis de competencia por formato: historial de cada canal (últimos 50 videos) + Gemini mirando sus
mejores y peores shorts con una guía de "por qué pega" (gancho, desenlace, quién gana, emoción, audio, título).

Uso: YOUTUBE_API_KEY=... GEMINI_API_KEY=... python3 research/competencia.py historial|gemini|resumen
Salida: data/raw/competencia/<canal>.json, data/raw/gemini_competencia/<id>.json, data/processed/competencia.csv
"""
import json
import os
import statistics as st
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
import yt_research as Y  # noqa: E402

RAW = Y.RAW
OUT_H = RAW / "competencia"; OUT_H.mkdir(exist_ok=True)
OUT_G = RAW / "gemini_competencia"; OUT_G.mkdir(exist_ok=True)
GKEY = os.environ.get("GEMINI_API_KEY")
MODELS = ["gemini-3.5-flash", "gemini-3.6-flash", "gemini-3.5-flash-lite", "gemini-flash-latest"]
URL = "https://generativelanguage.googleapis.com/v1beta/models/{}:generateContent"

CANALES = {
    "carrera": {"DriveLabs": "UC-3xq-bcNGEb0obHvSeIROQ", "Fire Rankings": "UC2hGyiVFV1LZvdc1TLLucng",
                "Goal nowa": "UC4p91GYQSlOgBREXK3fdVzQ", "Footypoints": "UCQg42PAMjcOz1-YoVkoJlcg",
                "Rival Stats": "UC8CFPYt0JQ1lPqAKWzd6bKg", "Sphere Stars": "UCybOrEQ3PNWG54esMw_hy3Q"},
    "evolucion": {"Unstoppable Football": "UCHM-YotK7hvUxLSrUsmkflA", "FULYON SHORTS": "UC5PgkslN0-aal256mrdnyxg",
                  "Kickoff to Immortality": "UCdqIgbMD65BzFTB_dTVy7HA", "FootyPivot": "UC2kPVQ_IUHzkiywd_bFcmNw",
                  "Icon Stories": "UCH-4iUlUJR57mC4evjkLhGQ", "Frox": "UCD2CLDW14h82BRSvjxGGRgQ"},
}

PROMPT = """Sos analista de YouTube Shorts virales de fútbol. Mirá y escuchá este short completo.
Este video tuvo {vistas} vistas; la mediana del canal es {mediana} (rinde {lift}x). Quiero entender POR QUÉ rinde así.
No inventes: si algo no se ve o no se oye, poné null. Respondé SOLO JSON válido en español:
{{
 "formato_exacto": "qué es en una frase",
 "duracion_s": 0,
 "primer_segundo": "qué se ve y se oye en el segundo 0-1",
 "gancho_texto": "texto o frase del gancho",
 "protagonistas": ["jugadores/equipos/países que aparecen"],
 "desenlace": "cómo termina; si es carrera/competencia: quién gana y si era el más popular, el favorito del momento o una sorpresa",
 "ganador_popular": true,
 "arco_de_tension": "cómo se construye la tensión (remontada, eliminaciones, final ajustado, cámara lenta, etc.)",
 "momentos_emocion": [{{"t": 0.0, "que": "..."}}],
 "audio": {{"musica": "tipo/tendencia y si se reconoce la canción", "voz": "sí/no y estilo", "efectos": "cuáles"}},
 "visual": "3D/2D/fotos/IA/clips; calidad; colores",
 "texto_en_pantalla": "qué textos y cuándo",
 "ritmo_cortes_por_segundo": 0.0,
 "loop": true,
 "pedido_al_espectador": "qué le pide (elegir, comentar, etc.) o null",
 "polemica_o_debate": "qué debate de internet explota (GOAT, Balón de Oro, rivalidad...) o null",
 "por_que_rinde_asi": "3 razones concretas",
 "que_le_falta": "qué lo haría más viral",
 "riesgo_copyright": "clips de TV, música con derechos, escudos, etc."
}}"""


def historial():
    for fmt, cs in CANALES.items():
        for nombre, cid in cs.items():
            dst = OUT_H / f"{cid}.json"
            if dst.exists():
                continue
            ch = Y.api("channels", part="snippet,statistics,contentDetails", id=cid)["items"][0]
            up = ch["contentDetails"]["relatedPlaylists"]["uploads"]
            ids = [x["contentDetails"]["videoId"] for x in
                   Y.api("playlistItems", part="contentDetails", playlistId=up, maxResults=50).get("items", [])]
            vs = Y.api("videos", part="snippet,statistics,contentDetails", id=",".join(ids)).get("items", [])
            vids = [{"id": v["id"], "titulo": v["snippet"]["title"], "fecha": v["snippet"]["publishedAt"],
                     "vistas": int(v["statistics"].get("viewCount", 0)), "likes": int(v["statistics"].get("likeCount", 0) or 0),
                     "coment": int(v["statistics"].get("commentCount", 0) or 0), "dur": v["contentDetails"]["duration"]}
                    for v in vs]
            dst.write_text(json.dumps({"formato": fmt, "nombre": nombre, "id": cid, "creado": ch["snippet"]["publishedAt"],
                                       "subs": int(ch["statistics"].get("subscriberCount", 0)),
                                       "vistas_total": int(ch["statistics"]["viewCount"]),
                                       "n_videos": int(ch["statistics"]["videoCount"]), "videos": vids}, ensure_ascii=False))
            print(nombre, len(vids), "videos")
    print("cuota", Y.quota())


def objetivos():
    out = []
    for f in OUT_H.glob("*.json"):
        d = json.loads(f.read_text())
        vs = sorted(d["videos"], key=lambda v: -v["vistas"])
        if not vs:
            continue
        med = st.median(v["vistas"] for v in vs)
        sel = vs[:4] + vs[-2:]
        for v in sel:
            out.append((d["formato"], d["nombre"], v, med))
    return out


def gemini():
    def uno(arg):
        fmt, canal, v, med = arg
        dst = OUT_G / f"{v['id']}.json"
        if dst.exists():
            return
        body = {"contents": [{"parts": [{"file_data": {"file_uri": f"https://www.youtube.com/watch?v={v['id']}"}},
                                        {"text": PROMPT.format(vistas=v["vistas"], mediana=int(med), lift=round(v["vistas"] / max(med, 1), 2))}]}],
                "generationConfig": {"temperature": 0.2, "responseMimeType": "application/json"}}
        for ronda in range(4):
            for m in MODELS:
                try:
                    r = requests.post(URL.format(m), headers={"x-goog-api-key": GKEY}, json=body, timeout=300)
                except requests.RequestException:
                    continue
                if r.status_code == 200:
                    try:
                        t = "".join(p.get("text", "") for p in r.json()["candidates"][0]["content"]["parts"])
                        a = json.loads(t)
                    except Exception:
                        continue
                    dst.write_text(json.dumps({"formato": fmt, "canal": canal, "video": v, "mediana": med, "modelo": m,
                                               "analisis": a}, ensure_ascii=False, indent=1))
                    print("ok", canal, v["id"], v["vistas"], flush=True)
                    return
            time.sleep(15 * (ronda + 1))
        print("falló", v["id"])
    with ThreadPoolExecutor(4) as ex:
        list(ex.map(uno, objetivos()))


if __name__ == "__main__":
    {"historial": historial, "gemini": gemini}[sys.argv[1]]()
