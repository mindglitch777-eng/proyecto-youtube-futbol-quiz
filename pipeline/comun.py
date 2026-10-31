"""
Piezas comunes del pipeline semanal (FÁBRICA): configuración, estado visible en el tablero, YouTube Data API y Gemini.
Las claves NUNCA van en el repo: se leen de variables de entorno (secretos de GitHub Actions).
"""
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

RAIZ = Path(__file__).resolve().parents[1]
PIPE = RAIZ / "pipeline"
DATOS = PIPE / "datos"
CONFIG = json.loads((PIPE / "config.json").read_text())
ESTADO = DATOS / "estado.json"

ETAPAS = [
    ("radar", "Radar de virales", "Busca los shorts de fútbol que más explotaron en los últimos 7 días y los canales nuevos que pegaron"),
    ("analisis", "Análisis con Gemini", "Mira cada viral segundo a segundo: gancho, mecánica, sonido, formato; y las grabaciones cuadro a cuadro"),
    ("rendimiento", "Nuestro rendimiento", "Mide cómo rindió cada formato en nuestro canal (vistas según la edad del video)"),
    ("plan", "Plan de la semana", "Reparte los 28 lugares entre formatos según lo que rinde y lo que está de moda"),
    ("produccion", "Producción", "La fábrica genera los videos con dopamina máxima, sin repetir combinaciones"),
    ("control", "Control de calidad", "Cada video pasa las reglas de retención; si falla, se rehace"),
    ("publicacion", "Publicación diaria", "Cada día sube por API los 4 videos del día, programados a su hora"),
]


def ahora():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def leer_estado():
    if ESTADO.exists():
        return json.loads(ESTADO.read_text())
    return {"semana": None, "etapas": {k: {"estado": "pendiente"} for k, *_ in ETAPAS}, "publicados": [], "historial": []}


def guardar_estado(e):
    DATOS.mkdir(parents=True, exist_ok=True)
    e["actualizado"] = ahora()
    ESTADO.write_text(json.dumps(e, ensure_ascii=False, indent=1))


def etapa(nombre, estado, **resumen):
    """Marca una etapa (pendiente / en_curso / ok / error) con su resumen visible en el tablero."""
    e = leer_estado()
    et = e["etapas"].setdefault(nombre, {})
    et["estado"] = estado
    if estado == "en_curso":
        et["inicio"] = ahora(); et.pop("fin", None)
    if estado in ("ok", "error"):
        et["fin"] = ahora()
    if resumen:
        et["resumen"] = resumen
    guardar_estado(e)
    print(f"[{nombre}] {estado} {json.dumps(resumen, ensure_ascii=False)[:300]}", flush=True)


def guardar(nombre, obj):
    DATOS.mkdir(parents=True, exist_ok=True)
    (DATOS / nombre).write_text(json.dumps(obj, ensure_ascii=False, indent=1))


def cargar(nombre, defecto=None):
    p = DATOS / nombre
    return json.loads(p.read_text()) if p.exists() else defecto


# ------------------------------------------------------------------ YouTube Data API (lectura, con clave)
def yt(endpoint, **params):
    r = requests.get(f"https://www.googleapis.com/youtube/v3/{endpoint}", params={**params, "key": os.environ["YOUTUBE_API_KEY"]}, timeout=60)
    r.raise_for_status()
    return r.json()


def yt_videos(ids):
    out = []
    for k in range(0, len(ids), 50):
        out += yt("videos", part="snippet,statistics,contentDetails", id=",".join(ids[k:k + 50]))["items"]
    return out


# ------------------------------------------------------------------ Gemini
MODELOS = ["gemini-3.5-flash", "gemini-3.6-flash", "gemini-flash-latest", "gemini-3.5-flash-lite"]


def gemini(partes, json_out=True, intentos=3):
    """partes: lista de dicts de 'parts' (texto, file_data con link de YouTube o archivo subido)."""
    key = os.environ["GEMINI_API_KEY"]
    for vuelta in range(intentos):
        for m in MODELOS:
            r = requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={key}",
                              json={"contents": [{"parts": partes}],
                                    "generationConfig": {"responseMimeType": "application/json"} if json_out else {}}, timeout=600)
            if r.status_code == 200:
                try:
                    t = r.json()["candidates"][0]["content"]["parts"][0]["text"]
                    return json.loads(t) if json_out else t
                except (KeyError, IndexError, json.JSONDecodeError):
                    continue
            time.sleep(2)
        time.sleep(20 * (vuelta + 1))
    return None


def gemini_subir(ruta, mime="video/mp4"):
    """Sube un archivo local (grabación de pantalla) a la Files API de Gemini y espera a que esté listo."""
    key = os.environ["GEMINI_API_KEY"]
    datos = Path(ruta).read_bytes()
    ini = requests.post(f"https://generativelanguage.googleapis.com/upload/v1beta/files?key={key}",
                        headers={"X-Goog-Upload-Protocol": "resumable", "X-Goog-Upload-Command": "start",
                                 "X-Goog-Upload-Header-Content-Length": str(len(datos)), "X-Goog-Upload-Header-Content-Type": mime,
                                 "Content-Type": "application/json"}, json={"file": {"display_name": Path(ruta).name}}, timeout=60)
    url = ini.headers["X-Goog-Upload-URL"]
    f = requests.post(url, headers={"X-Goog-Upload-Command": "upload, finalize", "X-Goog-Upload-Offset": "0"}, data=datos, timeout=600).json()["file"]
    for _ in range(60):
        if f.get("state") == "ACTIVE":
            return f["uri"]
        time.sleep(5)
        f = requests.get(f"https://generativelanguage.googleapis.com/v1beta/{f['name']}?key={key}", timeout=60).json()
    return None


# ------------------------------------------------------------------ OAuth del canal (subida y estadísticas)
def token_canal():
    """Access token a partir del refresh token guardado como secreto (YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN)."""
    if not all(os.environ.get(k) for k in ("YT_CLIENT_ID", "YT_CLIENT_SECRET", "YT_REFRESH_TOKEN")):
        return None
    r = requests.post("https://oauth2.googleapis.com/token", data=dict(client_id=os.environ["YT_CLIENT_ID"], client_secret=os.environ["YT_CLIENT_SECRET"],
                                                                     refresh_token=os.environ["YT_REFRESH_TOKEN"], grant_type="refresh_token"), timeout=60)
    r.raise_for_status()
    return r.json()["access_token"]
