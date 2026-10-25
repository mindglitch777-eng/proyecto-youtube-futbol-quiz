#!/usr/bin/env python3
"""
Calendario maestro: 2 shorts por día (10:00 y 23:00 hora Argentina) mezclando todos los formatos.
Regla: cada día mezcla formatos (carrera, evolución, prime vs now, find the real, fusión) para comparar en la
primera semana y clonar el que gane (reportes 14 y 15).
Salida: produccion/salida/CALENDARIO_MAESTRO.md
"""
import json
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DIAS = ["lun", "mar", "mié", "jue", "vie", "sáb", "dom"]

# (id, motivo) en orden; las dos primeras van hoy y mañana por los eventos
PLAN = [
    (None, None), ("carrera_06", "Noche del Clásico (rivalidad del día)"),
    ("find_the_real_02", "Ola FIND de FULYON (23 M y creciendo)"), ("carrera_01", "Balón de Oro: predicción el día de la ceremonia (verificá la fecha)"),
    ("evo_01", "Evolución: Messi desde 2005"), ("carrera_08", "Trío con Ronaldo (fórmula DriveLabs)"),
    ("prime_01", "Prime vs now: Barcelona 2015 (nostalgia)"), ("lote1_02", "Fusión: Argentina vs Brasil"),
    ("evo_02", "Evolución: Neymar"), ("carrera_04", "Debate GOAT (gana Ronaldo)"),
    ("find_the_real_03", "Ola FIND"), ("carrera_02", "Campeones del mundo (gana Argentina)"),
    ("prime_02", "Prime vs now: Alemania 2014"), ("carrera_03", "Libertadores (gana Boca)"),
    ("evo_03", "Evolución: Beckham (público UK/EE.UU.)"), ("carrera_09", "Trío con Ronaldo"),
    ("lote1_04", "Fusión: Premier League"), ("carrera_05", "Premier Big 6 (gana United)"),
    ("evo_04", "Evolución: Salah"), ("carrera_07", "Leyendas vs nueva generación (gana Ronaldinho)"),
    ("prime_03", "Prime vs now: España 2010"), ("find_the_real_04", "FIND"),
    ("evo_05", "Evolución: Zlatan"), ("lote1_06", "Fusión: jóvenes estrellas"),
    ("prime_04", "Prime vs now: Francia 2018"), ("find_the_real_05", "FIND"),
    ("evo_06", "Evolución: Modrić"), ("lote1_10", "Fusión: Messi o Ronaldo"),
    ("evo_07", "Evolución: Kane (público UK)"), ("lote1_14", "Fusión: modo imposible"),
]


def titulo(vid):
    p = ROOT / "salida" / vid / "SUBIR.txt"
    if not p.exists():
        return "—"
    for l in p.read_text().splitlines():
        if l.startswith("A) "):
            return l[3:]
    return "—"


def main():
    inicio = date(2026, 10, 25)
    filas = []
    for k, (vid, motivo) in enumerate(PLAN):
        if vid is None:
            continue
        if not (ROOT / "salida" / vid).exists():
            continue
        d = inicio + timedelta(days=k // 2)
        hora = "10:00" if k % 2 == 0 else "23:00"
        filas.append(f"| {DIAS[d.weekday()]} {d.day:02d}-{d.month:02d} {hora} | `{vid}` | {motivo} | {titulo(vid)} |")
    txt = """# Calendario maestro (2 shorts por día)

**Horarios: 10:00 y 23:00, hora Argentina**, siempre los mismos (el algoritmo y tu audiencia se acostumbran).
Cada carpeta `produccion/salida/<id>/` tiene el video y `SUBIR.txt` (título, descripción con créditos y comentario para fijar).

| Cuándo | Video | Por qué ese día | Título A |
|---|---|---|---|
""" + "\n".join(filas) + """

## Reglas de la semana
1. **Día 1 a 4: probar todos los formatos** (carreras, evolución, prime vs now, fusión, find the real).
2. **A las 48–72 h de cada video**, anotá en `produccion/registro.csv` vistas, % vieron vs. deslizaron y retención.
3. **El jueves**: el formato que pase **10 veces la mediana del canal** se **clona 3–5 veces** la semana siguiente
   (mismo formato, título casi igual, otro tema). El que quede abajo de la mediana sale del calendario.
4. **Eventos en vivo** (finales, clásicos, Balón de Oro, fechas FIFA): una carrera o evolución del tema ese mismo día.
5. Respondé los primeros 5 comentarios de cada video en la primera hora.
"""
    (ROOT / "salida" / "CALENDARIO_MAESTRO.md").write_text(txt, encoding="utf-8")
    print(txt)


if __name__ == "__main__":
    main()
