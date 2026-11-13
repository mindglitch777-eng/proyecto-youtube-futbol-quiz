# Bitácora del Gerente IA · Futbol Edition

Cada día el Gerente anota acá lo que vio, lo que decidió (y por qué, con números) y qué tiene que revisar después.
Antes de decidir, lee las últimas entradas: así no repite decisiones, sigue lo que dejó pendiente y mide si sus cambios funcionaron.

Formato de cada entrada:
## AAAA-MM-DD
- **Vi:** (3-5 hechos con números; aclarar la confianza de cada uno y las ADVERTENCIAS del día)
- **Decidí e hice:** (cambio · motivo · las 6 preguntas del manual: n datos / dato sano / otra explicación / peor caso y cómo se deshace / cómo se mide / mío o del CEO)
- **No toqué (a propósito):** (lo que esperé por falta de datos o porque un cambio anterior todavía está en evaluación)
- **Revisar el AAAA-MM-DD:** (qué y con qué número se confirma o se revierte)
- **Para el CEO:** (solo lo que necesita su decisión; si no hay nada, "nada")

## 2026-11-11 (entrada inicial, armada con el CEO)
- **Vi:** canal +85 % en la mediana a las 48 h (1.938 → 3.590). HEAD FIT y WHEEL son las estrellas (5,1x y 3,4x el canal; WHEEL +140 %).
  STOP cae (-33 %, 0,8x). FIT ALL: 1.088-2.541 vistas en sus 3 primeros (WHEEL/HEAD FIT 15-23k los mismos días).
- **Decidí e hice:** FIT ALL deja de ser promovido (vuelve a prueba). Extras de los 3 formatos de 20 s: mié 11, jue 12 y vie 13 a las 18:30.
  Vigía: se corrigió la falsa alarma de "no subidos" en horarios ya cubiertos por videos viejos.
- **Revisar el 2026-11-14:** FIT ALL con ≥4 videos medidos (si < 0,5x del STOP, la poda lo saca). Los 3 de 20 s a las 48 h: ¿superan 3.000?
  STOP: si sigue < 0,7x del canal una semana más, proponer al CEO bajar de 2 a 1 por día y darle el lugar a WHEEL/HEAD FIT.
- **Para el CEO:** nada.

## 2026-11-11 (tarde) · primera propuesta con prototipo
- **Vi:** la fábrica de prototipos funciona de punta a punta (Issue #3, hoja en reports/propuestas/p001/hoja.jpg).
  En las muestras se ven 2 defectos visuales de formatos viejos: DRESS UP tiene un rectángulo negro sobre el pecho del
  jugador de la izquierda, y BALLON D'OR 100 % deja un hueco transparente en las manos del jugador antes de que llegue el trofeo.
- **Decidí e hice:** nada en la grilla (la propuesta espera al CEO).
- **Revisar el 2026-11-12:** pedirle al Ingeniero (jueves) que arregle esos 2 defectos antes de que DRESS o BALLON D'OR vuelvan a salir.
- **Para el CEO:** Issue #3 (bajar el STOP a 1 por día) con su prueba visual.

## 2026-11-13 · Ingeniero
- **Ingeniero:** 2 formatos de prueba nuevos con `"listo": false`: **CONVEYOR STOP** (`cinta`, variante de WHEEL: torsos de 6 superestrellas
  colgados de una cinta aérea sobre las piernas de una estrella) y **HEAD SLOT** (`slot`, variante de HEAD FIT: tragamonedas de cabezas de
  6 superestrellas que desemboca en el cuello; JACKPOT + monedas). Solo superestrellas, con una estrella en el cuadro 0. Avanzan a saltos y
  el PERFECT!/JACKPOT! se ve solo mientras la pieza correcta está calzada. Propuesta p002 con 3 muestras de cada uno (Issue #7).
  La prueba de humo con --render dio TODO OK. No toqué render_balon.py ni DRESS: los tiene la sesión principal.
- **Para el CEO:** Issue #7 (aprobar o no CONVEYOR STOP y HEAD SLOT; si entran, que alternen con WHEEL/HEAD FIT, sin sumarse como extras).

## 2026-11-13 · Gerente IA (turno diario)
- **Vi:** 821 suscriptores; 699 K de 10 M vistas de Shorts en 90 días (7 %). Últimas 24 h ~58 K vistas y ~48 subs (11-12/11: ~45 K y ~30; confianza baja, 1 día).
  Mediana del canal a las 48 h esta semana 2.490 (antes 6.044, -59 %): efecto de los 9-15 videos por día. WHEEL 8.117 (alta) pero cansado (últimos 4 = 36 % de los anteriores).
  HEAD FIT 15.207 (3 medidos, baja). Originalidad 86, inspector 0 defectos, sin advertencias, todos los workflows OK. 14/11: 7 videos con HEAD FIT 2 veces (subidos antes del arreglo).
- **Decidí e hice:** (1) CEO aprobó #6 y #7 → `piernas`, `cinta`, `slot` con `listo: true` (máx. 3/semana) + freno nuevo en e4_plan.py: máx. 1 variante de WHEEL/HEAD FIT por día.
  6 preguntas: n = 0 videos propios (son pruebas, no promoción) / dato sano, sin advertencias / la aprobación es del CEO; el freno sale de la lección del 13/11 / peor caso: 3 formatos flojos ocupan lugares de prueba → la poda los saca, o se vuelve a `listo: false` / se mide con 4 videos de cada uno a las 48 h / del CEO (aprobado), el freno es mío.
  (2) Respondí la consulta #4 (DRESS UP): sigue pausado; arreglar + acortar; 2 pruebas con propuesta; si < 120 % visto, se saca. Le pedí el arreglo al Ingeniero.
  (3) Cerré #3 según la decisión del CEO (STOP 2 por día).
- **No toqué (a propósito):** WHEEL 1 por día (cambio del 13/11 en evaluación); el doble HEAD FIT del 14/11 (ya subido; borrar/editar es del CEO); FIT ALL (el cerebro ya casi no lo elige); A/B del arranque del STOP (sin ganador: 44/56 %).
- **Revisar el 2026-11-16:** WHEEL a 1 por día: ¿vuelve a pasar 5 K a las 48 h? ¿Vistas diarias vuelven a ~70 K? Primeras variantes nuevas en la grilla.
- **Revisar el 2026-11-18:** 2.º STOP del día contra el 1.º (hoy ~2.350 vs ~10.500): si sigue igual, volver a presentar 1 por día.
- **Revisar el 2026-11-24:** piernas/cinta/slot con 4 videos: poda o sigue.
- **Para el CEO:** respuesta de DRESS UP en el Issue #4.
