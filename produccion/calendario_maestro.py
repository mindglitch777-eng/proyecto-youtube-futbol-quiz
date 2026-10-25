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
    (None, None), ("carrera_06", "Noche del Clásico (se jugó hoy 21:00 de España)"),
    ("find_the_real_02", "Ola FIND de FULYON (23 M y creciendo)"),
    ("carrera_01", "Balón de Oro (ceremonia 17:00 ART): subí carrera_01 si gana YAMAL o carrera_01b si gana KANE"),
    ("evo_01", "Evolución: Messi desde 2005"), ("carrera_08", "Trío con Ronaldo (fórmula DriveLabs)"),
    ("objeto_01", "Evolución de pelotas del Mundial (el formato de 10–26 M)"), ("dupla_02", "Dupla: Messi y Neymar"),
    ("prime_01", "Prime vs now: Barcelona 2015"), ("carrera_04", "Debate GOAT (gana Ronaldo)"),
    ("find_the_real_03", "FIND"), ("carrera_02", "Campeones del mundo (gana Argentina)"),
    ("evo_02", "Evolución: Neymar"), ("carrera_03", "Libertadores (gana Boca)"),
    ("dupla_01", "Dupla: Lampard y Drogba (público UK)"), ("carrera_09", "Trío con Ronaldo"),
    ("prime_02", "Prime vs now: Alemania 2014"), ("carrera_05", "Premier Big 6 (gana United)"),
    ("carrera_10", "Predicción Champions del martes (gana Barça)"), ("evo_03", "Evolución: Beckham"),
    ("carrera_11", "Predicción Champions del miércoles (gana Madrid)"), ("find_the_real_04", "FIND"),
    ("dupla_03", "Dupla: Casillas y Ramos"), ("carrera_07", "Leyendas vs nueva generación (gana Ronaldinho)"),
    ("evo_04", "Evolución: Salah"), ("lote1_02", "Fusión: Argentina vs Brasil"),
    ("prime_03", "Prime vs now: España 2010"), ("find_the_real_05", "FIND"),
    ("evo_05", "Evolución: Zlatan"), ("dupla_04", "Dupla: Suárez y Messi"),
    ("prime_04", "Prime vs now: Francia 2018"), ("lote1_04", "Fusión: Premier League"),
    ("evo_06", "Evolución: Modrić"), ("lote1_06", "Fusión: jóvenes estrellas"),
    ("evo_07", "Evolución: Kane"), ("lote1_10", "Fusión: Messi o Ronaldo"),
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
