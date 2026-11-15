#!/usr/bin/env python3
"""
VIGILANCIA Y AUTORREPARACIÓN (máquina sin IA · Fase 1, 11/11). Corre cada 2 h en GitHub (vigilancia.yml).

Revisa:
1. Automatizaciones clave (fábrica, publicación, investigación, prototipos): si la última corrida FALLÓ, la relanza UNA vez
   (receta de reparación) y lo anota; si vuelve a fallar, avisa.
2. Que hayan corrido: publicación sin éxito hace más de 12 h (de noche hay 8 h sin corridas) o fábrica hace más de 30 h → aviso.
3. Datos: cada datos/*.json tiene que poder leerse. Si uno está roto, lo restaura desde la última versión buena del repo.
4. Cobertura: videos subidos para hoy y mañana (≥6 por día) y stock de la reserva.
Avisos: un Issue con la etiqueta "alerta-sistema" (llega al celular por la app de GitHub). Si todo vuelve a estar sano, lo cierra.
Memoria: datos/vigilancia.json (relanzamientos hechos, último parte).
"""
import json
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
DATOS = RAIZ / "pipeline" / "datos"
ART = timezone(timedelta(hours=-3))
REPO = "mindglitch777-eng/proyecto-youtube-futbol-quiz"
CLAVE = {"fabrica_diaria.yml": 30, "publicar_diario.yml": 12, "investigar.yml": 60, "prototipo.yml": None}   # horas máximas sin éxito


def gh(*a, ok=True):
    r = subprocess.run(["gh", *a], capture_output=True, text=True, cwd=RAIZ, timeout=120)
    if r.returncode and not ok:
        raise RuntimeError(r.stderr[-300:])
    return r.stdout


def corridas(wf, n=10):
    try:
        return json.loads(gh("api", f"repos/{REPO}/actions/workflows/{wf}/runs?per_page={n}")).get("workflow_runs", [])
    except Exception:
        return []


def main():
    ahora = datetime.now(timezone.utc)
    mem_p = DATOS / "vigilancia.json"
    mem = json.loads(mem_p.read_text()) if mem_p.exists() else {"relanzados": []}
    problemas, acciones = [], []
    # 1-2. automatizaciones
    for wf, horas in CLAVE.items():
        rs = [r for r in corridas(wf) if r.get("status") == "completed"]
        if not rs:
            continue
        ult = rs[0]
        if ult["conclusion"] == "failure":
            if ult["id"] not in mem["relanzados"]:
                gh("api", "-X", "POST", f"repos/{REPO}/actions/runs/{ult['id']}/rerun-failed-jobs")
                mem["relanzados"] = (mem["relanzados"] + [ult["id"]])[-50:]
                acciones.append(f"relancé {wf} (falló: {ult['html_url']})")
            else:
                problemas.append(f"{wf} falló de nuevo después de relanzarlo: {ult['html_url']}")
        if horas:
            ok = [r for r in rs if r["conclusion"] == "success"]
            if ok:
                hace = (ahora - datetime.fromisoformat(ok[0]["updated_at"].replace("Z", "+00:00"))).total_seconds() / 3600
                if hace > horas:
                    problemas.append(f"{wf} no termina bien hace {hace:.0f} h (máximo {horas} h)")
    # 2a. (15/11) PERMISO DE GOOGLE: lo único que puede frenar el canal sin que las máquinas lo arreglen
    import os
    if all(os.environ.get(k) for k in ("YT_CLIENT_ID", "YT_CLIENT_SECRET", "YT_REFRESH_TOKEN")):
        try:
            import requests
            v = {k: os.environ[k].strip().strip('"').strip("'").strip() for k in ("YT_CLIENT_ID", "YT_CLIENT_SECRET", "YT_REFRESH_TOKEN")}
            r = requests.post("https://oauth2.googleapis.com/token", data=dict(client_id=v["YT_CLIENT_ID"].removeprefix("https://").rstrip("/"),
                              client_secret=v["YT_CLIENT_SECRET"], refresh_token=v["YT_REFRESH_TOKEN"], grant_type="refresh_token"), timeout=60)
            mem["permiso_google"] = dict(hora=datetime.now(ART).isoformat(timespec="minutes"), ok=r.status_code == 200)
            if r.status_code != 200:
                problemas.append("🔑 GOOGLE RECHAZÓ EL PERMISO DEL CANAL: no se pueden subir videos ni medir. Qué hacer (10 minutos): "
                                 "1) seguí pipeline/README.md, sección 3 (paso 3.5), para generar un refresh token nuevo con tu cuenta del canal; "
                                 "2) en GitHub → Settings → Secrets and variables → Actions, reemplazá YT_REFRESH_TOKEN; "
                                 "3) listo: la próxima publicación sube lo atrasado sola (hay videos con 2-3 días de margen y la reserva). "
                                 f"Detalle técnico: {r.status_code} {r.text[:120]}")
        except Exception as e:
            print("no pude probar el permiso de Google:", e)
    else:
        problemas.append("faltan los secretos del canal en la vigilancia (YT_CLIENT_ID / YT_CLIENT_SECRET / YT_REFRESH_TOKEN)")
    # 2b. (auditoría A3, 15/11) FALLAS SILENCIOSAS: pasos que fallaron dentro de una corrida que siguió de largo
    for wf in ("fabrica_diaria.yml", "publicar_diario.yml"):
        rs = [r for r in corridas(wf, 3) if r.get("status") == "completed"]
        if rs:
            try:
                jobs = json.loads(gh("api", f"repos/{REPO}/actions/runs/{rs[0]['id']}/jobs")).get("jobs", [])
            except Exception:
                jobs = []
            malos = [st_["name"] for j in jobs for st_ in j.get("steps", []) if st_.get("conclusion") == "failure"]
            if malos and rs[0]["id"] not in mem.setdefault("pasos_avisados", []):
                problemas.append(f"{wf}: falló el paso «{', '.join(malos)}» ({rs[0]['html_url']})")
                mem["pasos_avisados"] = (mem["pasos_avisados"] + [rs[0]["id"]])[-30:]
    # 2c. ¿cada robot corrió las veces que tiene que correr? (GitHub se saltea tareas programadas)
    MINIMO_24H = {"medir_vivo.yml": 10, "publicar_diario.yml": 4, "vigilancia.yml": 5, "fabrica_diaria.yml": 1}
    for wf, mn in (MINIMO_24H.items() if datetime.now(ART).date().isoformat() >= "2026-11-17" else []):   # recién con 24 h de horarios nuevos
        n = sum(1 for r in corridas(wf, 40) if (ahora - datetime.fromisoformat(r["created_at"].replace("Z", "+00:00"))).total_seconds() < 86400)
        if n < mn:
            problemas.append(f"{wf} corrió {n} veces en 24 h (mínimo {mn}): GitHub está salteando sus horarios")
    # 2d. medición fresca (la base de todas las decisiones)
    try:
        f_vivo = json.loads(gh("api", f"repos/{REPO}/commits/datos-vivos"))["commit"]["committer"]["date"]
        h_vivo = (ahora - datetime.fromisoformat(f_vivo.replace("Z", "+00:00"))).total_seconds() / 3600
        if h_vivo > 3:
            problemas.append(f"la medición en vivo tiene {h_vivo:.1f} h (máximo 3 h)")
    except Exception:
        pass
    # 2e. ¿los agentes con IA hicieron y GUARDARON su trabajo? (el 12/11 corrieron sin acceso y nadie se enteró)
    art = datetime.now(ART)
    if art.hour >= 17:
        ger = json.loads((DATOS / "gerente.json").read_text()) if (DATOS / "gerente.json").exists() else {}
        if (ger.get("parte") or {}).get("fecha") != art.date().isoformat():
            problemas.append("el Gerente IA no dejó su parte de hoy en GitHub (¿corrió? ¿pudo guardar?)")
        if art.weekday() in (0, 3):
            bit = (RAIZ / "reports" / "gerente" / "bitacora.md").read_text() if (RAIZ / "reports" / "gerente" / "bitacora.md").exists() else ""
            if f"{art.date().isoformat()}" not in bit or "Ingeniero" not in bit.split(art.date().isoformat(), 1)[-1]:
                problemas.append("el Ingeniero no anotó su turno de hoy en la bitácora (¿corrió? ¿pudo guardar?)")
    # 2f. cambios automáticos que el CEO tiene que saber (podas y promociones)
    poda = json.loads((DATOS / "poda.json").read_text()) if (DATOS / "poda.json").exists() else {}
    vistos = mem.setdefault("cambios_avisados", 0)
    nuevos = poda.get("historial", [])[vistos:] if len(poda.get("historial", [])) >= vistos else poda.get("historial", [])
    avisos = [f"{c['formato']}: {c['cambio']} ({c['motivo']})" for c in nuevos]
    mem["cambios_avisados"] = len(poda.get("historial", []))
    # 3. datos legibles (si uno se rompió, vuelve a la última versión buena)
    for p in sorted(DATOS.glob("*.json")):
        try:
            json.loads(p.read_text())
        except Exception:
            rel = str(p.relative_to(RAIZ))
            for k in range(1, 30):
                r = subprocess.run(["git", "show", f"HEAD~{k}:{rel}"], capture_output=True, text=True, cwd=RAIZ)
                try:
                    json.loads(r.stdout); p.write_text(r.stdout); acciones.append(f"restauré {p.name} (estaba roto) desde HEAD~{k}"); break
                except Exception:
                    continue
            else:
                problemas.append(f"{p.name} está roto y no encontré una versión buena")
    # 4. cobertura y reserva
    pub = json.loads((DATOS / "publicados.json").read_text()) if (DATOS / "publicados.json").exists() else []
    hoy = datetime.now(ART).date()
    for d in (0, 1):
        f = (hoy + timedelta(days=d)).isoformat()
        n = sum(1 for x in pub if x["fecha"] == f and x.get("video_id") and not x.get("reemplazado"))
        if n < 6 and (d == 0 or datetime.now(ART).hour >= 20):
            problemas.append(f"{f}: {n} videos subidos de 6")
    res = json.loads((DATOS / "reserva.json").read_text()) if (DATOS / "reserva.json").exists() else {"videos": []}
    libres = sum(1 for v in res["videos"] if not v.get("usado"))
    if libres < 4:
        problemas.append(f"reserva con {libres} videos (mínimo 4): la fábrica la repone en su próxima corrida")
    mem.update(ultimo=dict(hora=datetime.now(ART).isoformat(timespec="minutes"), problemas=problemas, acciones=acciones, avisos=avisos))
    mem_p.write_text(json.dumps(mem, ensure_ascii=False, indent=1))
    # aviso por Issue
    abiertos = json.loads(gh("api", f"repos/{REPO}/issues?labels=alerta-sistema&state=open") or "[]")
    if problemas:
        cuerpo = "**La vigilancia encontró problemas que no pudo resolver sola:**\n\n" + "\n".join(f"- {x}" for x in problemas)
        if acciones:
            cuerpo += "\n\n**Lo que ya hice:**\n" + "\n".join(f"- {x}" for x in acciones)
        cuerpo += "\n\n_Vigilancia automática (sin IA). El Gerente IA lo revisa en su próximo parte._\n\n---\n_Generated by [Claude Code](https://claude.ai/code)_"
        if abiertos:
            gh("api", "-X", "POST", f"repos/{REPO}/issues/{abiertos[0]['number']}/comments", "-f", f"body={cuerpo}")
        else:
            gh("api", "-X", "POST", f"repos/{REPO}/issues", "-f", "title=ALERTA del sistema: hay algo que revisar", "-f", f"body={cuerpo}",
               "-f", "labels[]=alerta-sistema")
    else:
        for i in abiertos:
            gh("api", "-X", "POST", f"repos/{REPO}/issues/{i['number']}/comments", "-f",
               "body=Todo volvió a estar sano ✅ (vigilancia automática).\n\n---\n_Generated by [Claude Code](https://claude.ai/code)_")
            gh("api", "-X", "PATCH", f"repos/{REPO}/issues/{i['number']}", "-f", "state=closed")
    if avisos:                                                                 # aviso informativo (no es una alarma)
        try:
            ab = json.loads(gh("api", f"repos/{REPO}/issues?labels=aviso&state=open") or "[]")
            cuerpo = ("**Cambios automáticos del sistema** (no hace falta que hagas nada; si no estás de acuerdo, comentá acá):\n\n"
                      + "\n".join(f"- {x}" for x in avisos) + "\n\n---\n_Generated by [Claude Code](https://claude.ai/code)_")
            if ab:
                gh("api", "-X", "POST", f"repos/{REPO}/issues/{ab[0]['number']}/comments", "-f", f"body={cuerpo}")
            else:
                gh("api", "-X", "POST", f"repos/{REPO}/issues", "-f", "title=Cambios automáticos del sistema (podas y promociones)",
                   "-f", f"body={cuerpo}", "-f", "labels[]=aviso")
        except Exception as e:
            print("no pude avisar:", e)
    print("problemas:", problemas or "ninguno"); print("acciones:", acciones or "ninguna"); print("avisos:", avisos or "ninguno")


if __name__ == "__main__":
    main()
