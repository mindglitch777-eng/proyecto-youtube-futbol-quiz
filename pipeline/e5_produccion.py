#!/usr/bin/env python3
"""
Etapas 5 y 6 · PRODUCCIÓN + CONTROL: la fábrica genera un video por lugar del plan y cada uno pasa el control
de retención (reglas medibles del reporte 24). El que falla se vuelve a generar con otra combinación (hasta 2 veces).
Salida: produccion/semana_<inicio>/ (videos + videos.json) y el resumen en el estado.
"""
import json
import random
import sys
from pathlib import Path

from comun import RAIZ, cargar, etapa

sys.path.insert(0, str(RAIZ / "produccion"))
sys.path.insert(0, str(RAIZ / "research"))


def controlar(ruta, det):
    from control_retencion import REGLAS
    from medir_gancho import medir
    r = medir(dict(id=Path(ruta).stem, ruta=str(ruta), grupo="control"), det)
    fallas = [txt for clave, txt, ok, _ in REGLAS if r is None or r.get(clave) is None or not ok(r.get(clave))]
    return fallas, r


def main():
    import cv2
    import fabrica
    from medir_gancho import MODELO, W, H
    plan = cargar("plan.json")
    sem = RAIZ / "produccion" / f"semana_{plan['inicio']}"
    etapa("produccion", "en_curso", videos=len(plan["slots"]))
    rng = random.Random(plan["inicio"])
    manifiesto, errores = fabrica.fabricar(plan["slots"], sem, rng, prefijo="s" + plan["inicio"].replace("-", "")[4:], procesos=4)
    etapa("produccion", "ok" if not errores else "error", videos=sum(m["listo"] for m in manifiesto), errores=len(errores))

    etapa("control", "en_curso")
    det = cv2.FaceDetectorYN.create(str(MODELO), "", (W, H), 0.6)
    rehechos = 0
    for m in manifiesto:
        for intento in range(3):
            ruta = sem / m["archivo"]
            fallas, medida = controlar(ruta, det) if ruta.exists() else (["no se generó"], None)
            m["control"] = "PASA" if not fallas else "NO PASA: " + "; ".join(fallas)
            if not fallas or intento == 2:
                break
            rehechos += 1                                                      # rehacer ese lugar con otra combinación
            nuevo, _ = fabrica.fabricar([dict(fecha=m["fecha"], hora=m["hora"], tipo=m["tipo"], dificil=True)], sem,
                                        random.Random(f"{m['id']}-{intento}"), prefijo=m["id"].rsplit("_", 3)[0] + f"r{intento}")
            n = nuevo[0]
            if (sem / n["archivo"]).exists():
                (sem / n["archivo"]).replace(ruta)
            for resto in sem.glob(f"{Path(n['archivo']).stem}*"):              # restos del reintento
                resto.unlink()
            for k in ("titulo", "descripcion", "fijado", "jugadores", "tags", "soluciones"):
                if k in n:
                    m[k] = n[k]
    (sem / "videos.json").write_text(json.dumps(manifiesto, ensure_ascii=False, indent=1))
    (sem / "CALENDARIO.md").write_text("# Calendario de la semana\n\n| # | Día | Hora (ARG) | Formato | Título | Control |\n|---|---|---|---|---|---|\n" +
                                       "\n".join(f"| {m['n']} | {m['fecha']} | {m['hora']} | {m['formato']} | {m['titulo']} | {m['control']} |" for m in manifiesto) + "\n")
    (RAIZ / "pipeline" / "datos" / "semana_actual.json").write_text(json.dumps(dict(inicio=plan["inicio"], videos=manifiesto), ensure_ascii=False, indent=1))
    pasan = sum(m["control"] == "PASA" for m in manifiesto)
    etapa("control", "ok", pasan=f"{pasan} de {len(manifiesto)}", rehechos=rehechos)
    e = json.loads((RAIZ / "pipeline" / "datos" / "estado.json").read_text())
    e["semana"] = plan["inicio"]
    (RAIZ / "pipeline" / "datos" / "estado.json").write_text(json.dumps(e, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
