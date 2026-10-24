# 00 · Resumen ejecutivo

**Qué tan realista es la meta:** posible, pero es una apuesta.
- De **158 canales quiz jóvenes** tomados al azar (lo último que se subió, sin sesgo de éxito), **5% llegó a 10 M de vistas** en total. Entre los que lo intentan en serio (30 videos o más): **11% llega a 10 M y 5% a 20 M** (reporte 06).
- Los que lo lograron lo hicieron con **1 a 3 videos virales tempranos**, en una mediana de **46 días y 36 videos** (90 canales con historial completo, reporte 04).
- **⚠️ Fecha límite:** desde el **1-feb-2027** los canales nuevos necesitan **20 M de vistas en 90 días** (hoy son 10 M).
- **💸 La plata es poca:** 10 M de vistas en LATAM ≈ **200–600 USD**. Vivir de esto pide 25–50 M de vistas por mes, o pasar al inglés, que paga ~8 veces más.

## Qué funciona (datos)

1. **Formatos sin cara que rinden más que el promedio de su canal:** nombrá jugadores (1,42×), impostor / encontrá al real (1,35×), armá tu equipo (1,35×), futbolista de chico (1,32×), escudo (1,29×), verdadero o falso (1,27×), carrera (1,25×), silueta / imagen oculta (1,23×). **Entre los mejores la diferencia es chica: pesa más la ejecución.** → reporte 02.
2. **Plantilla ganadora sin cara:**
   - 15–30 s, 3–4 rondas;
   - gancho escrito gigante en el segundo 0–1;
   - 2–3 s para pensar con cuenta regresiva visible;
   - sonido de acierto, música de tendencia, sin voz, loop al inicio.
   → reporte 03.
3. **Casos copiables:** MStriker (77 videos, 146 M), SpotVerse (37 videos, 43 M), Muzam (22 videos, 55 M), TIER (52 videos, 113 M). Todos nacieron en 2026 y suben **~1 por día**. → reportes 01 y 04.
4. **Hueco en español:** imagen oculta (en inglés 73 videos de 1 M+, en español 9), ordená de mayor a menor (116 contra 10), armá tu equipo (97 contra 33). Además, buscando "encontrá al verdadero Messi" en español aparecen solo 12 videos y "adiviná por la sombra" solo 6; en inglés las mismas búsquedas llenan las 50. → reporte 02.

## Qué no funciona o es riesgoso

- **Formatos flojos:** duelo / "¿quién es mejor?" (1,06×), opción múltiple (1,02×), tier list (1,09×), gol/jugada (1,09×, y además usa clips).
- **Subir 3 por día de relleno:** los canales que suben 2,5 o más por día tienen una mediana de **15 mil** vistas por video; los de ~1 por día, **74 mil**.
- **Clips de partidos:** el 63% de los sin cara exitosos los usa, pero es **riesgo de Content ID y strikes**. No los usamos. → reporte 07.
- **El horario:** no hay una hora mágica (0,9–1,2×).
- **Contenido rioplatense:** Argentina y México dan igual en las búsquedas. Conviene español neutro.

## Qué hacer primero

1. **Vos elegís** los 4 formatos y el idioma (punto de control). Mi propuesta: **impostor / encontrá al real (grilla), silueta, nombrá jugadores sin cara y verdadero o falso**, en **español neutro**, más una prueba chica en inglés.
2. Yo armo **un short de ejemplo** con la plantilla (Remotion o FFmpeg + Pillow, fotos de Wikimedia) para validar el diseño visual.
3. Arrancamos el **plan de 30 días** con 2 por día (reporte 09).

## Mapa de reportes

| # | Reporte | Para qué |
|---|---|---|
| 01 | [Canales](01_canales.md) | Quiénes son, cuáles crecen, cuáles copiar |
| 02 | [Formatos](02_formatos.md) | Ranking de formatos, competencia por idioma, ejemplos |
| 03 | [Anatomía](03_anatomia_video.md) | Segundos de gancho, pensar, loop, música, títulos |
| 04 | [Ritmo y crecimiento](04_ritmo_crecimiento.md) | Cuánto tardan, cuántos por día, horarios |
| 05 | [Audiencia](05_audiencia.md) | Qué comentan, qué genera interacción |
| 06 | [Mercado y monetización](06_mercado_monetizacion.md) | Reglas del YPP, plata, idiomas |
| 07 | [Riesgos](07_riesgos.md) | Copyright, contenido inauténtico, reclamos |
| 08 | [Calendario](08_calendario.md) | Fechas futboleras y quizzes para cada una |
| 09 | [Plan de 30 días](09_plan_30_dias.md) | Borrador operativo |

**Base de datos:**
- 41.692 videos (37.921 shorts) de 560 canales, en 80 búsquedas, con 9.893 unidades de cuota de YouTube el 24-oct-2026.
- ~38.000 shorts clasificados por formato con Gemini, 150 shorts "mirados" por Gemini y comentarios de 118 shorts.
- Todo lo crudo está en `data/raw/`; lo limpio en `data/processed/`.
