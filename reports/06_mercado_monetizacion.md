# 06 · Mercado, idioma y monetización

**Conclusión:**
1. Los Shorts **pagan muy poco**: 10 M de vistas en LATAM dan **~200 a 600 USD, una sola vez**. Para vivir de esto hacen falta **25 a 50 M de vistas por mes**, o sumar otras fuentes de ingreso.
2. **El umbral se duplica el 1-feb-2027** (20 M de vistas en 90 días). Si se arranca ya, la ventana para calificar con 10 M es de unos 100 días.
3. **El inglés** paga hasta ~8 veces más por vista y tiene más volumen, pero está más concentrado. **El español LATAM** tiene menos competencia en varios formatos (ver reporte 02). Recomendación: **arrancar en español neutro** y probar inglés en paralelo con los mismos templates. La decisión es tuya (punto de control).

## Reglas del Programa de Socios (YPP) para Shorts

| | Hoy | Desde 1-feb-2027 (canales nuevos) |
|---|---|---|
| Ingresos por anuncios | 1.000 subs + **10 M de vistas de Shorts en 90 días** (o 4.000 h en 12 meses) | 1.000 subs + **20 M en 90 días** (o 8.000 h) |
| Nivel inicial (fan funding, sin anuncios) | 500 subs + 3 subidas en 90 días + 3 M de vistas de Shorts en 90 días (o 3.000 h) | — |
| Canales ya admitidos | — | Conservan el YPP, pero para seguir cobrando Shorts necesitan mantener 10 M de vistas en 90 días |

- **Cómo se cuentan las vistas:** desde el 31-mar-2025, la vista pública de un Short cuenta apenas empieza o se repite. Para cobrar y para calificar se usan las **"vistas con interacción"** (engaged views), que son menos. El número de Studio no es el que vale para el YPP.
- **Reparto:** los ingresos de anuncios de Shorts van a un fondo común por país y se reparten según la participación de cada canal en las vistas con interacción. **El creador se lleva el 45%**, use música o no.
- **Las vistas anteriores a entrar al YPP no se cobran.**

Fuentes: [TechCrunch 10-ago-2026](https://techcrunch.com/2026/08/10/youtube-now-requires-creators-to-have-twice-as-many-watch-hours-to-start-earning-money/), [AIR: requisitos 2026](https://air.io/en/monetization/youtube-partner-program-requirements-2026-the-complete-guide), [MediaPost: cambio de conteo](https://www.mediapost.com/publications/article/404562/youtube-changes-how-it-counts-shorts-views.html), [política oficial de Shorts](https://support.google.com/youtube/answer/12504220) (no la pude abrir desde acá; el reparto del 45% sale de la cobertura que la cita).

## Cuánto es la plata (estimación)

**Fórmula:** ingreso = vistas con interacción / 1000 × RPM. El RPM es un **placeholder configurable**. Para referencia, AIR (datos de sus canales socios) da: México 0,040; Brasil 0,045; EE.UU. 0,328 USD cada 1.000 vistas ([AIR](https://air.io/en/monetization/what-rpm-can-you-expect-from-shorts-in-2026)).

| RPM (USD/1000) | 10 M de vistas | Vistas por mes para 500 USD | Vistas por mes para 1.000 USD |
|---|---|---|---|
| 0,01 | 100 USD | 50 M | 100 M |
| 0,02 | 200 USD | 25 M | 50 M |
| 0,04 (≈ México) | 400 USD | 12,5 M | 25 M |
| 0,06 | 600 USD | 8,3 M | 16,7 M |
| 0,33 (≈ EE.UU., inglés) | 3.300 USD | 1,5 M | 3 M |

Con 3 shorts por día son ~90 por mes. Para 25 M de vistas por mes hacen falta **~280 mil de promedio por short**. Hoy, el canal quiz joven típico hace una mediana de 15 a 60 mil (`data/processed/crecimiento.csv`). El modelo realista es que **pocos videos virales cargan casi todo**.

## Comparación de mercados (datos)

Búsqueda de shorts quiz del último año por país, top 50 por vistas (`data/raw/search_hits.json`, entradas con `region`):

| Mercado | Mediana de vistas del top 50 | Videos de 1 M o más | Canales distintos | % de vistas en los 3 principales |
|---|---|---|---|---|
| Inglés, Reino Unido | 1,41 M | 31 | 21 | 66% |
| Inglés, EE.UU. | 1,17 M | 27 | 23 | 68% |
| Español, Argentina | 1,04 M | 26 | 22 | 60% |
| Español, México | 0,99 M | 25 | 22 | 60% |
| Español, España | 0,56 M | 19 | 23 | 45% |
| Portugués, Brasil | 0,42 M | 18 | 32 | 43% |

- **Argentina y México dan casi idéntico:** el algoritmo trata el español LATAM como un solo mercado. Hacer contenido **rioplatense** no abre un mercado aparte, solo achica el público. Conviene **español neutro**, con rioplatense solo en temas locales (Boca–River, Liga Argentina).
- **El inglés** tiene un techo más alto y paga mucho más por vista, pero 3 canales se llevan dos tercios de las vistas.
- **España y Brasil** están menos concentrados (más fácil hacerse un lugar) pero son más chicos.

Reparto por idioma de los canales medidos (`data/processed/canales.csv`):

| Idioma | Quiz puro | Quiz mixto | No quiz |
|---|---|---|---|
| Español | 44 | 37 | 69 |
| Inglés | 43 | 41 | 34 |
| Portugués | 19 | 9 | 6 |

## Qué tan realista es

- **Muestra sin sesgo:** de 65 canales jóvenes (menos de 12 meses) que estaban subiendo quizzes de fútbol el 24-oct, **3 (≈5%) llegaron a 10 M de vistas en total** y **12 (18%) a 1.000 subs**. La mediana es de 359 subs y 117 mil vistas (`data/raw/fresh_channels.json`). Muestra chica: tomalo como orden de magnitud.
- **Los que lo lograron** (`crecimiento.csv`): casi siempre fue con **1 a 3 videos que explotaron temprano**, no por acumulación lenta. Ver reporte 04.
- **Traducción:** es una apuesta tipo lotería con chances que se pueden mejorar (formato, volumen, iteración). No es un sueldo garantizado. El plan de 30 días (reporte 09) está diseñado para saber rápido si hay tracción.
