#!/usr/bin/env python3
"""
RESERVA DE VIDEOS (Fase 1 · Blindaje, 11/11): el canal nunca se queda sin videos aunque la fábrica falle dos días.

- Stock: 12 videos de formatos FIJOS (WHEEL, HEAD FIT, STOP), ya renderizados y sin fecha, guardados en Releases "reserva-*".
  La fábrica diaria repone hasta 4 por corrida cuando el stock baja de 12 (`python reserva.py producir` → carpeta o "nada").
- Uso: el planificador de subidas (e6_bajar.py) llama huecos() + tomar(): si a un horario de la grilla de las próximas
  30 h le falta video (la fábrica falló), le asigna uno de la reserva (el más viejo) con esa fecha y hora.
Memoria: datos/reserva.json {"videos": [{id, archivo, release, tipo, titulo, descripcion, fijado, tags, jugadores, usado}]}.
"""
import json
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from comun import RAIZ, cargar, guardar

ART = timezone(timedelta(hours=-3))
OBJETIVO = 12
POR_CORRIDA = 4
TIPOS = ["rueda", "cabezas", "stop"]
HORAS = ["09:00", "13:00", "17:00", "20:00", "21:30", "23:00"]        # la grilla del día (misma que e4_plan.GRILLA)


def stock():
    return [v for v in cargar("reserva.json", {"videos": []})["videos"] if not v.get("usado")]


def producir():
    disp = stock()
    falta = min(POR_CORRIDA, OBJETIVO - len(disp))
    if falta <= 0:
        return None
    sys.path.insert(0, str(RAIZ / "produccion"))
    import fabrica
    ahora = datetime.now(ART)
    usados = {}
    for v in disp:
        usados[v["tipo"]] = usados.get(v["tipo"], 0) + 1
    tipos = sorted(TIPOS, key=lambda t: (usados.get(t, 0), random.random()))   # repone lo que menos hay
    slots = [dict(fecha="2099-01-01", hora=f"{10 + k:02d}:00", tipo=tipos[k % len(tipos)], dificil=True) for k in range(falta)]
    sem = RAIZ / "produccion" / f"reserva_{ahora.strftime('%Y%m%d_%H%M')}"
    man, _ = fabrica.fabricar(slots, sem, random.Random(f"reserva-{ahora.isoformat()}"), prefijo=f"r{ahora.strftime('%m%d%H%M')}", procesos=3)
    tag = f"reserva-{ahora.strftime('%Y%m%d-%H%M')}"
    datos = cargar("reserva.json", {"videos": []})
    for m in man:
        if (sem / m["archivo"]).exists():
            datos["videos"].append(dict({k: m[k] for k in ("id", "archivo", "tipo", "titulo", "descripcion", "fijado", "tags", "jugadores", "formato")
                                         if k in m}, release=tag, creado=ahora.isoformat(timespec="minutes"), usado=None))
    for f in sem.glob("*_solo_efectos.mp4"):
        f.unlink()
    guardar("reserva.json", datos)
    return sem.name, tag


def huecos(ocupados, ahora=None):
    """Horarios de la grilla en las próximas 30 h (desde dentro de 1 h) sin ningún video. ocupados = [(fecha, "HH:MM")]."""
    ahora = ahora or datetime.now(ART)
    mins = lambda h: int(h[:2]) * 60 + int(h[3:5])
    out = []
    for d in range(3):
        f = (ahora.date() + timedelta(days=d)).isoformat()
        for h in HORAS:
            t = datetime.fromisoformat(f"{f}T{h}:00").replace(tzinfo=ART)
            if not (ahora + timedelta(hours=1) <= t <= ahora + timedelta(hours=30)):
                continue
            if any(fo == f and abs(mins(ho) - mins(h)) <= 45 for fo, ho in ocupados):
                continue
            out.append((f, h))
    return out


def tomar(fecha, hora):
    """Saca el video más viejo de la reserva y lo deja listo para ese horario (o None si no hay)."""
    datos = cargar("reserva.json", {"videos": []})
    libres = [v for v in datos["videos"] if not v.get("usado")]
    if not libres:
        return None
    v = libres[0]
    v["usado"] = f"{fecha} {hora}"
    guardar("reserva.json", datos)
    m = {k: v[k] for k in v if k not in ("usado", "creado")}
    m.update(fecha=fecha, hora=hora, id=f"{v['id']}__{fecha}_{hora.replace(':', '')}", reserva=True)
    return m


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "producir":
        r = producir()
        print("nada" if not r else f"{r[0]} {r[1]}")
    else:
        print(f"stock de reserva: {len(stock())} / {OBJETIVO}")
