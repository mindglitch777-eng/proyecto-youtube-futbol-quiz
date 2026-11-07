#!/usr/bin/env python3
"""
Etapa 7a · Juntar los videos a subir CON MARGEN: los de hoy y los de los próximos DIAS_ADELANTE días que todavía no están en YouTube.
La idea: YouTube los publica solo a su hora (publishAt). Si un día GitHub no corre, no pasa nada: ya están programados allá.

Busca en las semanas guardadas en el repo (produccion/semana_*/videos.json) y en los Releases semana-* (los arma la fábrica).
Deja en _subir/: videos.json (solo los elegidos, en orden de fecha) + los .mp4.
Uso: python3 pipeline/e6_bajar.py [carpeta_destino]
"""
import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
ART = timezone(timedelta(hours=-3))
DIAS_ADELANTE = 3          # margen: con 3 días cargados, aunque GitHub no corra 2 días seguidos no se pierde ninguna subida
MAX_POR_CORRIDA = 6        # 6 x 1.600 = 9.600 unidades (cuota diaria 10.000)


def hechos():
    p = RAIZ / "pipeline" / "datos" / "publicados.json"
    pub = json.loads(p.read_text()) if p.exists() else []
    return {x["id"] for x in pub if (x.get("video_id") and not x.get("reemplazado")) or x.get("manual")}


def dias_con_viejos(ids_actuales):
    """Días que todavía tienen videos subidos de un plan anterior (no reemplazados): ahí no se sube nada nuevo (sin duplicados)."""
    p = RAIZ / "pipeline" / "datos" / "publicados.json"
    pub = json.loads(p.read_text()) if p.exists() else []
    return {x["fecha"] for x in pub if x.get("video_id") and not x.get("reemplazado") and x["id"] not in ids_actuales}


def manifiestos():
    """{id: (video, origen)} de todas las semanas; el repo manda sobre el Release (ahí van los cambios a mano)."""
    out = {}
    try:
        tags = subprocess.run(["gh", "release", "list", "--limit", "30", "--json", "tagName", "-q", ".[].tagName"],
                              capture_output=True, text=True, timeout=120).stdout.split()
    except Exception as e:
        print("no pude listar los Releases:", e); tags = []
    for tag in [t for t in tags if t.startswith("semana-")]:
        tmp = RAIZ / f"_tmp_{tag}"
        subprocess.run(["gh", "release", "download", tag, "-p", "videos.json", "-D", str(tmp), "--clobber"], capture_output=True, timeout=300)
        if (tmp / "videos.json").exists():
            for m in json.loads((tmp / "videos.json").read_text()):
                out[m["id"]] = (m, ("release", tag))
    for vj in sorted((RAIZ / "produccion").glob("semana_*/videos.json")):
        for m in json.loads(vj.read_text()):
            out[m["id"]] = (m, ("repo", vj.parent))
    return out


def main():
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else RAIZ / "_subir"
    dest.mkdir(parents=True, exist_ok=True)
    ahora = datetime.now(ART); hoy = ahora.date()
    limite = (hoy + timedelta(days=DIAS_ADELANTE)).isoformat()
    ya = hechos(); todos = manifiestos()
    viejos = dias_con_viejos(set(todos))
    pend = sorted((m for m, _ in todos.values() if hoy.isoformat() <= m["fecha"] <= limite and m["id"] not in ya and m["fecha"] not in viejos),
                  key=lambda m: (m["fecha"], m["hora"]))
    vencidos = sorted(m["id"] for m, _ in todos.values() if m["fecha"] < hoy.isoformat() and m["id"] not in ya
                      and m["fecha"] >= (hoy - timedelta(days=3)).isoformat())
    elegidos = []
    for m in pend[:MAX_POR_CORRIDA]:
        _, (tipo, lugar) = todos[m["id"]]
        archivo = dest / m["archivo"]
        if tipo == "repo":
            src = lugar / m["archivo"]
            if src.exists():
                archivo.write_bytes(src.read_bytes())
        else:
            subprocess.run(["gh", "release", "download", lugar, "-p", m["archivo"], "-D", str(dest), "--clobber"], capture_output=True, timeout=600)
        print(("ok   " if archivo.exists() else "FALTA"), m["fecha"], m["hora"], m["id"], flush=True)
        elegidos.append(m)
    (dest / "videos.json").write_text(json.dumps(elegidos, ensure_ascii=False, indent=1))
    (dest / "vencidos.json").write_text(json.dumps(vencidos))
    print(f"pendientes en los próximos {DIAS_ADELANTE} días: {len(pend)} · para esta corrida: {len(elegidos)} · vencidos sin subir: {len(vencidos)}")


if __name__ == "__main__":
    main()
