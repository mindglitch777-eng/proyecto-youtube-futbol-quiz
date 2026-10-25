#!/usr/bin/env python3
"""
Calendario maestro: 2 shorts por día (10:00 y 23:00 hora Argentina) mezclando todos los formatos.
Regla: cada día lleva 1 formato nuevo (carrera / evolución / prime vs now) + 1 de prueba (fusión / find the real),
para comparar formatos en la primera semana y clonar el que gane (reporte 14).
Salida: produccion/salida/CALENDARIO_MAESTRO.md
"""
import json
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DIAS = ["lun", "mar", "mié", "jue", "vie", "sáb", "dom"]

# (id, motivo) en orden; las dos primeras van hoy y mañana por los eventos
PLAN = [
    # dom 25-oct (10:00 ya salió lote1_01)
    (None, None), ("carrera_06", "Noche del Clásico"),
    ("lote1_03", "Balón de Oro (ceremonia: verificá la fecha)"), ("carrera_01", "Balón de Oro: noche de la ceremonia"),
    ("find_the_real_02", "Ola FIND de FULYON"), ("evo_01", "Formato nuevo: evolución"),
    ("lote1_02", "Argentina vs Brasil"), ("carrera_02", "Campeones del mundo (identidad de país)"),
    ("prime_01", "Formato nuevo: prime vs now"), ("carrera_04", "Debate GOAT"),
    ("lote1_04", "Premier League (público que paga más)"), ("carrera_05", "Premier Big 6"),
    ("find_the_real_03", "Ola FIND"), ("carrera_03", "Libertadores (sábado de fútbol sudamericano)"),
    ("evo_02", "Evolución"), ("carrera_07", "Leyendas vs nueva generación"),
    # semana 2: se reemplaza según los números del día 4 (clonar lo que pase 10x la mediana)
    ("prime_02", "Prime vs now"), ("lote1_05", "Inglaterra"),
    ("evo_03", "Evolución"), ("find_the_real_04", "FIND"),
    ("lote1_06", "Jóvenes estrellas"), ("prime_03", "Prime vs now"),
    ("evo_04", "Evolución"), ("lote1_07", "Francia"),
    ("find_the_real_05", "FIND"), ("lote1_08", "Delanteros"),
    ("evo_05", "Evolución"), ("lote1_09", "España vs Alemania"),
    ("evo_06", "Evolución"), ("lote1_10", "Messi o Ronaldo"),
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
