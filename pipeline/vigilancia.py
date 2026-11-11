#!/usr/bin/env python3
"""
VIGILANCIA Y AUTORREPARACIÓN (máquina sin IA · Fase 1, 11/11). Corre cada 2 h en GitHub (vigilancia.yml).

Revisa:
1. Automatizaciones clave (fábrica, publicación, investigación, prototipos): si la última corrida FALLÓ, la relanza UNA vez
   (receta de reparación) y lo anota; si vuelve a fallar, avisa.
2. Que hayan corrido: publicación sin éxito hace más de 8 h o fábrica hace más de 30 h → aviso.
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
CLAVE = {"fabrica_diaria.yml": 30, "publicar_diario.yml": 8, "investigar.yml": 60, "prototipo.yml": None}   # horas máximas sin éxito


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
    mem.update(ultimo=dict(hora=datetime.now(ART).isoformat(timespec="minutes"), problemas=problemas, acciones=acciones))
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
    print("problemas:", problemas or "ninguno"); print("acciones:", acciones or "ninguna")


if __name__ == "__main__":
    main()
