#!/usr/bin/env python3
"""
Guarda en el repo el estado del pipeline (pipeline/datos/*.json) SIN conflictos aunque otra corrida haya escrito en paralelo
(la fábrica y la publicación tocan estado.json a la vez: con `git pull --rebase` quedaba el archivo roto y no se guardaba nada).

Cómo: copia lo que cambió esta corrida, trae lo último del repo y COMBINA por archivo:
- estado.json: por etapa, gana la que tiene el "inicio" más nuevo (cada corrida actualiza sus etapas).
- publicados.json: unión de los registros (id + momento de subida), nada se pierde.
- analytics_historia.json: unión de días.
- el resto: gana la versión de esta corrida (la que acaba de calcularlo).
Reintenta hasta 5 veces si alguien empuja justo en el medio.
Uso: python pipeline/guardar_avance.py "Mensaje"
"""
import json
import subprocess
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
DATOS = RAIZ / "pipeline" / "datos"


def sh(*a, ok=False):
    r = subprocess.run(list(a), cwd=RAIZ, capture_output=True, text=True)
    if r.returncode and not ok:
        raise RuntimeError(f"{' '.join(a)}: {r.stderr[-400:]}")
    return r.stdout


def combinar(nombre, mio, suyo):
    if nombre == "estado.json":
        out = dict(suyo); et = dict(suyo.get("etapas", {}))
        for k, v in mio.get("etapas", {}).items():
            if k not in et or (v.get("inicio") or "") >= (et[k].get("inicio") or ""):
                et[k] = v
        out.update({k: v for k, v in mio.items() if k != "etapas"}); out["etapas"] = et
        return out
    if nombre == "publicados.json":
        por = {}
        for x in suyo:
            por[(x.get("id"), x.get("subido"), x.get("video_id"))] = x
        for x in mio:                                                          # lo de esta corrida gana (ej. marca "reemplazado")
            k = (x.get("id"), x.get("subido"), x.get("video_id"))
            por[k] = {**por.get(k, {}), **x}
        return sorted(por.values(), key=lambda x: x.get("subido") or "")
    if nombre == "analytics_historia.json":
        return {**suyo, **mio}
    return mio


def main():
    msg = sys.argv[1] if len(sys.argv) > 1 else "Pipeline"
    if not __import__("os").environ.get("GITHUB_ACTIONS"):                    # usa reset --hard: solo en las corridas de GitHub
        raise SystemExit("guardar_avance.py es solo para GitHub Actions")
    sh("git", "config", "user.name", "github-actions[bot]")
    sh("git", "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com")
    rama = sh("git", "rev-parse", "--abbrev-ref", "HEAD").strip()
    rama = __import__("os").environ.get("GITHUB_REF_NAME", rama)
    cambiados = [l[3:] for l in sh("git", "status", "--porcelain", "pipeline/datos").splitlines() if l[3:].endswith(".json")]
    if not cambiados:
        print("sin cambios"); return
    mios = {}
    for c in cambiados:
        try:
            mios[c] = json.loads((RAIZ / c).read_text())
        except Exception as e:
            print("no se puede leer", c, e)
    for intento in range(5):
        sh("git", "fetch", "-q", "origin", rama)
        sh("git", "reset", "-q", "--hard", f"origin/{rama}")                   # partimos de lo último del repo…
        for c, mio in mios.items():                                            # …y le sumamos lo de esta corrida
            p = RAIZ / c
            try:
                suyo = json.loads(p.read_text()) if p.exists() else (mio.__class__())
            except Exception:
                suyo = mio.__class__()
            p.write_text(json.dumps(combinar(p.name, mio, suyo), ensure_ascii=False, indent=1))
        sh("git", "add", *mios.keys())
        if not sh("git", "status", "--porcelain", "pipeline/datos").strip():
            print("sin cambios"); return
        sh("git", "commit", "-q", "-m", f"{msg}: estado")
        if subprocess.run(["git", "push", "-q", "origin", f"HEAD:{rama}"], cwd=RAIZ).returncode == 0:
            print("guardado:", ", ".join(Path(c).name for c in mios)); return
        time.sleep(5 * (intento + 1))
    raise SystemExit("no pude guardar el avance después de 5 intentos")


if __name__ == "__main__":
    main()
