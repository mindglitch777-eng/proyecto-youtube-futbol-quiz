# 00 · Resumen ejecutivo

**Qué tan realista es la meta:** posible, pero es una apuesta.
- De 65 canales quiz jóvenes tomados al azar, solo **~5% llegó a 10 M de vistas** (reporte 06).
- Los que lo lograron lo hicieron con **1 a 3 videos virales tempranos**, en una mediana de **47 días y 55 videos** (reporte 04).
- **⚠️ Fecha límite:** desde el **1-feb-2027** los canales nuevos necesitan **20 M de vistas en 90 días** (hoy son 10 M).
- **💸 La plata es poca:** 10 M de vistas en LATAM ≈ **200–600 USD**. Vivir de esto pide 25–50 M de vistas por mes, o pasar al inglés, que paga ~8 veces más.

## Qué funciona (datos)

1. **Formatos sin cara que rinden más que el promedio de su canal:** carrera del jugador (1,46×), imagen oculta/silueta (1,39×), impostor/encontrá al real (1,38×), nombrá jugadores (1,37×), armá tu equipo (1,36×), escudo (1,35×). Con cara también rinde verdadero o falso (1,43×). → reporte 02.
2. **Plantilla ganadora sin cara:**
   - 15–30 s, 3–4 rondas;
   - gancho escrito gigante en el segundo 0–1;
   - 3 s para pensar con cuenta regresiva visible;
   - sonido de acierto, música de tendencia, sin voz, loop al inicio.
   → reporte 03.
3. **Casos copiables:** MStriker (77 videos, 146 M), SpotVerse (37 videos, 43 M), Muzam (22 videos, 55 M), TIER (52 videos, 113 M). Todos nacieron en 2026 y suben **~1 por día**. → reportes 01 y 04.
4. **Hueco en español:** imagen oculta (en inglés 49 videos de 1 M+, en español 8), ordená de mayor a menor (95 contra 10), tier list y carrera. → reporte 02.

## Qué no funciona o es riesgoso

- **Emojis:** 0,92× y ningún outlier. Saturado y flojo.
- **Subir 3 por día de relleno:** los canales de ~3 por día tienen medianas de 1 a 70 mil. Los que explotaron suben 1 por día.
- **Clips de partidos:** el 54% de los sin cara exitosos los usa, pero es **riesgo de Content ID y strikes**. No los usamos. → reporte 07.
- **El horario:** no hay una hora mágica (0,9–1,2×).
- **Contenido rioplatense:** Argentina y México dan igual en las búsquedas. Conviene español neutro.

## Qué hacer primero

1. **Vos elegís** los 4 formatos y el idioma (punto de control). Mi propuesta: **impostor (grilla), silueta, verdadero o falso y carrera**, en **español neutro**, más una prueba chica en inglés.
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
- 29.442 videos (26.798 shorts) de 434 canales, en 63 búsquedas, con 7.597 unidades de cuota de YouTube el 24-oct-2026.
- ~26.800 shorts clasificados por formato con Gemini y ~150 shorts "mirados" por Gemini.
- Todo lo crudo está en `data/raw/`; lo limpio en `data/processed/`.
