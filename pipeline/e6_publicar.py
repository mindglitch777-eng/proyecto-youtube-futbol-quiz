#!/usr/bin/env python3
"""
Etapa 7 · PUBLICACIÓN DIARIA: sube por la API de YouTube los videos del día, programados a su hora (publishAt).
Cada subida gasta 1.600 de las 10.000 unidades diarias: 4 por día entran sobrado.
Los videos los baja del Release de la semana (los deja ahí la fábrica del domingo).
Sin el permiso del canal (secretos YT_CLIENT_ID / YT_CLIENT_SECRET / YT_REFRESH_TOKEN) no sube nada y lo avisa en el tablero.

Uso: python3 pipeline/e6_publicar.py [carpeta_con_videos] [AAAA-MM-DD]
"""
import json
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import requests

from comun import CONFIG, cargar, etapa, guardar, token_canal

ART = timezone(timedelta(hours=-3))


def subir(tok, ruta, m):
    cuando = datetime.fromisoformat(f"{m['fecha']}T{m['hora']}:00").replace(tzinfo=ART)
    status = {"privacyStatus": "private", "selfDeclaredMadeForKids": False, "containsSyntheticMedia": False}
    if cuando > datetime.now(timezone.utc) + timedelta(minutes=15):
        status["publishAt"] = cuando.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    else:
        status["privacyStatus"] = "public"                                    # ya pasó la hora: sale ahora
    cuerpo = {"snippet": {"title": m["titulo"][:100], "description": m["descripcion"][:4900], "tags": m.get("tags", [])[:15],
                          "categoryId": CONFIG["subida"]["categoria"], "defaultLanguage": CONFIG["subida"]["idioma"],
                          "defaultAudioLanguage": CONFIG["subida"]["idioma"]}, "status": status}
    datos = Path(ruta).read_bytes()
    ini = requests.post("https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
                        headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json; charset=UTF-8",
                                 "X-Upload-Content-Type": "video/mp4", "X-Upload-Content-Length": str(len(datos))}, json=cuerpo, timeout=60)
    if ini.status_code >= 300:
        return None, f"{ini.status_code} {ini.text[:300]}"
    r = requests.put(ini.headers["Location"], headers={"Authorization": f"Bearer {tok}", "Content-Type": "video/mp4"}, data=datos, timeout=900)
    if r.status_code >= 300:
        return None, f"{r.status_code} {r.text[:300]}"
    return r.json()["id"], None


def main():
    carpeta = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    hoy = date.fromisoformat(sys.argv[2]) if len(sys.argv) > 2 else datetime.now(ART).date()
    videos = json.loads((carpeta / "videos.json").read_text())
    publicados = cargar("publicados.json", [])
    hechos = {p["id"] for p in publicados if p.get("video_id")}
    del_dia = [m for m in videos if m["fecha"] == hoy.isoformat() and m["id"] not in hechos]
    tok = token_canal()
    if not tok:
        etapa("publicacion", "pendiente", aviso="Falta el permiso del canal (secretos YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN). "
                                                "Mientras tanto, los videos del día se programan a mano desde el tablero.", hoy=hoy.isoformat(),
               del_dia=len(del_dia))
        return
    etapa("publicacion", "en_curso", hoy=hoy.isoformat(), del_dia=len(del_dia))
    subidos, errores = 0, []
    for m in del_dia:
        ruta = carpeta / m["archivo"]
        if not ruta.exists():
            errores.append(f"{m['id']}: no está el archivo"); continue
        vid, err = subir(tok, ruta, m)
        publicados.append(dict(id=m["id"], tipo=m["tipo"], fecha=m["fecha"], hora=m["hora"], titulo=m["titulo"], video_id=vid, error=err,
                               subido=datetime.now(timezone.utc).isoformat(timespec="seconds")))
        guardar("publicados.json", publicados)
        if vid:
            subidos += 1
            print("subido", m["id"], vid, flush=True)
        else:
            errores.append(f"{m['id']}: {err}")
            if "quota" in (err or "").lower() or "uploadLimitExceeded" in (err or ""):
                break                                                         # límite de YouTube: mañana sigue
    etapa("publicacion", "ok" if not errores else "error", hoy=hoy.isoformat(), subidos=subidos, errores=errores[:4],
          total_publicados=sum(1 for p in publicados if p.get("video_id")))


if __name__ == "__main__":
    main()
