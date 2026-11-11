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
    """Sube TODO lo que dejó e6_bajar.py (hoy + próximos días), cada uno programado a su hora. Al final deja el parte de la
    vigía en datos/alerta.json: si algo que sale en las próximas 12 h no quedó en YouTube, es una ALERTA."""
    carpeta = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    ahora = datetime.now(timezone.utc)
    videos = json.loads((carpeta / "videos.json").read_text()) if (carpeta / "videos.json").exists() else []
    vencidos = json.loads((carpeta / "vencidos.json").read_text()) if (carpeta / "vencidos.json").exists() else []
    publicados = cargar("publicados.json", [])
    hechos = {p["id"] for p in publicados if (p.get("video_id") and not p.get("reemplazado")) or p.get("manual")}
    cola = [m for m in videos if m["id"] not in hechos]
    problemas = [f"Se pasó la hora y NO se subió: {v}" for v in vencidos]

    def urgente(m):
        return datetime.fromisoformat(f"{m['fecha']}T{m['hora']}:00").replace(tzinfo=ART) < ahora + timedelta(hours=12)

    try:
        tok = token_canal()
    except Exception as e:
        tok = None; problemas.append(f"Google rechazó el permiso del canal: {e}")
    if not tok:
        problemas.append("Sin permiso del canal (secretos YT_CLIENT_ID / YT_CLIENT_SECRET / YT_REFRESH_TOKEN).")
        etapa("publicacion", "error", errores=problemas[:4])
        return vigia(problemas, cola, 0)
    etapa("publicacion", "en_curso", en_cola=len(cola))
    subidos, errores, freno = 0, [], None
    import auditor
    previos = [p["titulo"] for p in publicados if p.get("video_id") and p.get("titulo")][-60:]
    for m in cola:
        ruta = carpeta / m["archivo"]
        m, avisos = auditor.auditar(m, previos, carpeta)                      # última revisión antes de subir (no se edita después)
        for a in avisos:
            print("AUDITOR", a, flush=True)
        if m.get("_roto"):
            errores.append(avisos[-1]); continue
        previos.append(m["titulo"])
        try:
            vid, err = subir(tok, ruta, m)
        except Exception as e:                                                # corte de red, etc.: se reintenta en la próxima corrida
            vid, err = None, f"excepción: {e}"
        publicados.append(dict(id=m["id"], tipo=m["tipo"], variante=m.get("variante"), exp=m.get("exp"), fecha=m["fecha"], hora=m["hora"], titulo=m["titulo"], video_id=vid, error=err,
                               subido=datetime.now(timezone.utc).isoformat(timespec="seconds")))
        guardar("publicados.json", publicados)
        if vid:
            subidos += 1; print("subido", m["fecha"], m["hora"], m["id"], vid, flush=True)
            if m.get("fijado"):
                try:
                    c = requests.post("https://www.googleapis.com/youtube/v3/commentThreads?part=snippet",
                                      headers={"Authorization": f"Bearer {tok}"}, timeout=60,
                                      json={"snippet": {"videoId": vid, "topLevelComment": {"snippet": {"textOriginal": m["fijado"]}}}})
                    print("  comentario", "ok" if c.ok else f"no ({c.status_code}: falta permiso youtube.force-ssl?)", flush=True)
                except Exception as e:
                    print("  comentario falló", e)
        else:
            errores.append(f"{m['id']}: {err}")
            if "quota" in (err or "").lower() or "uploadLimitExceeded" in (err or ""):
                freno = "límite diario de YouTube"; break                    # normal: la próxima corrida sigue
    hechos = {p["id"] for p in publicados if p.get("video_id") or p.get("manual")}
    faltan = [m for m in cola if m["id"] not in hechos]
    for m in faltan:
        if urgente(m):
            problemas.append(f"{m['fecha']} {m['hora']} {m['id']} no quedó programado" + (f" ({freno})" if freno else ""))
    problemas += [e for e in errores if "quota" not in e.lower() and "uploadLimitExceeded" not in e]
    etapa("publicacion", "ok" if not problemas else "error", subidos=subidos, en_cola=len(faltan), freno=freno, errores=problemas[:4],
          total_publicados=sum(1 for p in publicados if p.get("video_id")))
    return vigia(problemas, faltan, subidos)


def vigia(problemas, faltan, subidos):
    """Parte para el aviso: datos/alerta.json (el workflow abre un Issue 'ALERTA subida' si hay problemas y lo cierra si no)."""
    problemas = list(dict.fromkeys(problemas))
    guardar("alerta.json", dict(hora=datetime.now(ART).isoformat(timespec="minutes"), ok=not problemas, problemas=problemas,
                                subidos_ahora=subidos, en_cola=[m["id"] for m in faltan]))
    print("VIGÍA:", "todo en orden" if not problemas else "PROBLEMAS:\n- " + "\n- ".join(problemas), flush=True)


if __name__ == "__main__":
    main()
