#!/usr/bin/env python3
"""
REGLA 10 (09/11, pedido del dueño): UNA OLA QUE FUNCIONA AHORA SE SUBE AHORA.
La fábrica diaria produce para dentro de 2 días; eso sirve para la grilla, pero una ola caliente no espera.
Cada vez que corre la fábrica diaria, este paso:
1. Busca la ola caliente: un formato nuestro listo cuya mecánica está "naciente" o "subiendo" en el detector (olas.json),
   o el formato que la poda marcó como promovido por una ola (poda.json, el que no tiene lugar fijo).
2. Para HOY (si quedan ≥3 h antes de las 22:15) y MAÑANA: si ese día todavía no tiene ese formato, fabrica uno EXTRA
   a las 22:15 (la noche rinde 4-7 veces más) que se suma a la grilla (no reemplaza a nadie).
3. Lo deja en produccion/semana_ola_<hoy>/ (videos.json con "extra": true); el workflow lo publica como Release
   "semana-ola-<hoy>" y la publicación lo sube en la próxima corrida (6 por día de YouTube aparte, hasta 10 en 24 h).
Imprime la carpeta (o "nada").
"""
import json
import random
import sys
from datetime import datetime, timedelta, timezone

from comun import CONFIG, RAIZ, cargar

ART = timezone(timedelta(hours=-3))
HORA_EXTRA = "22:15"
OLA_A_FORMATO = {"stop": ["stop", "siuu", "penal", "balon"], "wheel": ["rueda"], "fit": ["fitall", "cabezas"], "find": ["find"],
                 "dress": ["dress"], "quiz": ["trayectoria", "tridente", "q20fichaje", "q20costo"], "goat": ["circulo"]}


def ola_caliente():
    poda = cargar("poda.json", {"podadas": {}, "promovidas": {}})
    listos = [k for k, v in CONFIG["pruebas"].items() if v.get("listo") and k not in poda["podadas"]]
    fijos = {"rueda", "cabezas"}
    for k in poda["promovidas"]:                                               # promovido por ola (no los de lugar fijo)
        if k in listos and k not in fijos:
            return k, "promovido por ola"
    est = cargar("olas.json", {}).get("estado", {})
    calientes = sorted(((f, e) for f, e in est.items() if e["estado"] in ("naciente", "subiendo")), key=lambda x: -(x[1].get("vph") or 0))
    for fam, e in calientes:
        for k in OLA_A_FORMATO.get(fam, []):
            if k in listos:
                return k, f"ola {fam} {e['estado']}"
    return None, None


def tiene(fecha, tipo, todos):
    if any(m["fecha"] == fecha and m["tipo"] == tipo for m, _ in todos.values()):
        return True
    return any(p["fecha"] == fecha and p.get("tipo") == tipo and p.get("video_id") for p in cargar("publicados.json", []))


def main():
    import os
    if os.environ.get("EXTRA_SLOTS", "").strip():                              # pedido a mano: videos extra ya mismo (regla 3)
        slots = json.loads(os.environ["EXTRA_SLOTS"]); return fabricar_extra(slots, "pedido a mano")
    tipo, por = ola_caliente()
    if not tipo:
        print("sin ola caliente", file=sys.stderr); print("nada"); return
    import e6_bajar
    todos = e6_bajar.manifiestos()
    ahora = datetime.now(ART); hoy = ahora.date()
    dias = []
    limite_hoy = datetime.fromisoformat(f"{hoy.isoformat()}T{HORA_EXTRA}:00").replace(tzinfo=ART) - timedelta(hours=3)
    if ahora < limite_hoy:
        dias.append(hoy)
    dias.append(hoy + timedelta(days=1))
    slots = [dict(fecha=d.isoformat(), hora=HORA_EXTRA, tipo=tipo) for d in dias if not tiene(d.isoformat(), tipo, todos)]
    if not slots:
        print(f"{tipo} ({por}) ya está hoy y mañana", file=sys.stderr); print("nada"); return
    return fabricar_extra(slots, f"{tipo} ({por})")


def fabricar_extra(slots, por):
    sys.path.insert(0, str(RAIZ / "produccion"))
    import fabrica
    ahora = datetime.now(ART); hoy = ahora.date()
    sem = RAIZ / "produccion" / f"semana_ola_{hoy.isoformat()}_{ahora.strftime('%H%M')}"
    man, errores = fabrica.fabricar(slots, sem, random.Random(f"ola-{ahora.isoformat()}"), prefijo=f"o{ahora.strftime('%m%d%H%M')}", procesos=3)
    for m in man:
        m["extra"] = True
    (sem / "videos.json").write_text(json.dumps([m for m in man if (sem / m["archivo"]).exists()], ensure_ascii=False, indent=1))
    for f in sem.glob("*_solo_efectos.mp4"):
        f.unlink()
    print(f"extra: {por} → " + ", ".join(f"{s['fecha']} {s['hora']} {s['tipo']}" for s in slots), file=sys.stderr)
    print(sem.name)


if __name__ == "__main__":
    main()
