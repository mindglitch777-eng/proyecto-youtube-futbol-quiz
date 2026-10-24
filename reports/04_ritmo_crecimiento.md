# 04 · Ritmo y crecimiento

**Conclusión:**
1. Los canales quiz jóvenes que llegaron a 10 M lo hicieron por **1 a 3 videos que explotaron**, casi siempre **dentro de los primeros 50 videos**.
2. **Subir más no rinde más:** los que suben ~3 por día tienen las medianas más bajas; los que explotaron suben **~1 por día**.
3. Propuesta: **2 por día de calidad**, mejor que 3 de relleno. El tercero solo si es una variante de un formato que ya pegó.
4. El **horario** casi no importa. No hay una franja que rinda claramente más.

Datos: historial completo de los **90 canales quiz jóvenes** (creados desde abr-2025) con 3 M de vistas o más; 72 de ellos pasaron los 10 M. Están en `data/processed/crecimiento.csv` y salen de `research/crecimiento.py`.

> ⚠️ **Estimación:** la API no da historial de vistas ni de subs. "Días hasta 10 M" = primer día en que la suma de las vistas **actuales** de lo ya publicado supera 10 M. Es una cota **optimista** (los videos viejos siguieron sumando después). Además estos canales son **los que tuvieron éxito**: para la tasa real ver reporte 06 (≈5%).

## Cuánto tardaron (90 canales quiz jóvenes; los tiempos a 10 M, sobre los 72 que llegaron)

| | Mínimo | 25% | Mediana | 75% |
|---|---|---|---|---|
| Días hasta 10 M (estimación) | 0 | 18 | **46** | 99 |
| Videos hasta 10 M | 1 | 11 | **36** | 99 |
| Videos por día | 0,08 | 0,48 | **0,82** | 1,33 |
| % de videos con 10× la mediana del canal | 0 | 5% | **9%** | 14% |
| % de las vistas del canal en su mejor video | 1% | 11% | **19%** | 34% |

## Casos para estudiar (sin cara, recientes)

| Canal | Creado | Videos | Vistas | Días / videos hasta 10 M | Ritmo por día | Formato |
|---|---|---|---|---|---|---|
| [MStriker](https://youtube.com/channel/UCSY6No0ec_0BP_Z9Bm0C0Vg) | ago-2026 | 77 | 146 M | 5 d / 6 videos | 0,97 | imagen oculta |
| [Muzam](https://youtube.com/channel/UC5_bl5EXSUXplvOj67NOQgg) | sep-2026 | 22 | 55 M | 7 d / 9 videos | 1,05 | duelo |
| [SpotVerse](https://youtube.com/channel/UCFa04zYV0EUB9NSr2-WD-LQ) | sep-2026 | 37 | 43 M | 21 d / 17 videos | 0,95 | impostor |
| [SRD Game](https://youtube.com/channel/UCuk5pDlj8SG7BTLQlqEMvBg) | ago-2026 | 39 | 22 M | 3 d / 4 videos | 0,97 | impostor |
| [Funny Sharpener](https://youtube.com/channel/UChr7usZtWvWet3w4vRUPQNw) | mar-2026 | 254 | 421 M | 3 d / 3 videos | 1,09 | duelo |
| [Goatline Theory](https://youtube.com/channel/UCOLow8szhPZjhDrQZmqz55A) (ES) | jun-2026 | 199 | 29 M | 75 d / 98 videos | 1,66 | imagen oculta |
| [TrendPick](https://youtube.com/channel/UCGpWgn2950kTRmsD7Gkz-UA) | jul-2026 | 37 | 17 M | 11 d / 13 videos | 0,60 | tier list |

## Ritmo de publicación: ¿3 por día canibaliza?

- **Entre canales:** correlación **−0,16** entre videos por día y mediana de vistas. Los 6 canales que suben 2,5 o más por día tienen una mediana de **15 mil** vistas por video; los 28 que suben ~1 por día (0,7 a 1,3), **74 mil**. Los que explotaron (MStriker, Muzam, AYAYAY, Minuto De Juego) suben **0,5 a 1 por día** con medianas de 0,5 a 1,8 M.
- **Dentro de cada canal:** en las semanas con más subidas la mediana **no cae** (correlación de rangos, mediana +0,20). Subir más no destruye lo anterior, pero tampoco lo multiplica. Probablemente suben más cuando les está yendo bien.
- **Lectura:** el volumen ayuda a encontrar el viral, pero **la calidad por video es lo que separa**. Con un solo operador y celular, **2 por día bien hechos** es el punto óptimo. El tercero entra en la semana 3 si el pipeline lo permite sin bajar la calidad.

## ¿Qué proporción "pega"?

- Mediana de los canales: **9% de los videos supera 10× la mediana del canal**, o sea ~1 de cada 11 videos.
- Con 2 por día, eso sería **~1 viral por semana** si el canal está bien encaminado.

## Horario (hora Argentina)

Mediana de vistas relativa a la mediana del canal, según la hora de subida (`data/processed/horarios.csv`, ~18.000 videos de 90 canales):

- Casi todas las franjas quedan entre **0,9× y 1,2×**. **No hay una hora mágica.** Lo más flojo: 4 h (0,67×) y 16–17 h (0,72–0,80×). Lo mejor: 21 h, 23 h y 0 h (1,19–1,24×).
- Los canales en inglés suben más entre las 11 y las 13 h ART (mañana en EE.UU. y mediodía en Europa).
- **Recomendación:** fijar 2 horarios y sostenerlos, por ejemplo **12:00 y 21:00 ART**, y evitar las 16–17 h. Que la constancia pese más que la hora exacta.
