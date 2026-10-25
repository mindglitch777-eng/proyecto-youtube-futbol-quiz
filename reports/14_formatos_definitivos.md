# 14 · Formatos definitivos: qué pega más rápido y qué podemos crear nosotros

**Base de datos** (25-oct-2026):
- **14.257 shorts etiquetados por Gemini** según lo que **recibe** el espectador: la recompensa psicológica, qué se le pide comentar y si es serie (`data/raw/gemini_recompensas.json`).
- Cruzados con la **velocidad real** de 6.781 shorts de 14 días o menos, medidos dos veces (vistas por hora).
- Más la **oferta en fútbol** (muestra al azar) y **25 búsquedas nuevas** de validación.
- Tablas: `data/processed/patrones_recompensa.csv` y `patrones_mecanica_velocidad.csv`.

## 1. El patrón: qué "recibe" el espectador

| Recompensa | Vistas/hora (mediana, ≤14 días) | % que pasa 10 mil vistas/hora | Mediana en fútbol | % de la oferta de fútbol |
|---|---|---|---|---|
| **Suspenso / competencia** (ver quién gana) | **139** | 5,4% | **1,64 M** | 6,6% |
| **Curiosidad / revelación** (quedarse a ver qué pasa) | 113 | 5,7% | 1,39 M | 8,0% |
| Humor | 98 | 6,0% | 1,11 M | 8,4% |
| Espectáculo / habilidad | 66 | 3,0% | 1,16 M | 12,9% |
| **Transformación** (antes/después, morph) | 49 | **9,6%** (el más alto) | 1,23 M | **1,1%** |
| **Nostalgia** | 47 | 0% | 0,26 M (4,5 M en otros nichos) | **1,5%** |
| **Logro / acierto** (quiz clásico, "ponete a prueba") | **48** | 2,0% | **0,21 M** | **32,9%** |

**Conclusión clave:**
- **El quiz clásico es lo más saturado de fútbol** (1 de cada 3 shorts) y de lo más lento. Pegan más rápido los videos donde el espectador **recibe una resolución sin esfuerzo**: ver quién gana, ver qué pasa, ver el cambio.
- La participación que mejor funciona es **liviana**: "elegí uno antes de que empiece". No es "contá cuántas acertaste".
- **Lo que se pide comentar:**
  - los videos que piden **puntaje** tienen una mediana de **31 vistas por hora y 40–70 mil vistas totales**: lo peor de la tabla;
  - los que no piden nada o piden opinión rinden 2 o 3 veces más.
  - Ojo: puede ser porque "puntaje" va casi siempre con quiz clásico. Es una correlación, no una prueba.
- Las **series numeradas** no rinden más por sí mismas: rinden cuando se clona algo que ya pegó.

## 2. Validación de formatos candidatos (búsquedas de hoy, último año, shorts)

| Formato | Mediana | Con 1 M+ | Quién lo hace | Lectura |
|---|---|---|---|---|
| **Prime vs. now (equipo o jugador)** | **4,45 M** | **50/50** | 37 canales, casi todo **con clips de TV** | Demanda enorme, pero con riesgo de copyright. **Versión con fotos: libre** |
| Then vs. now de planteles | 2,34 M | 39/49 | 34 canales | Igual que arriba |
| **Carrera de canicas con jugadores** | 0,29 M | 17/49 | **19 canales** | Fire Rankings: 12 M con 23 s |
| **Simulación "¿quién gana el trofeo?"** | | | DriveLabs | **De 0 a 1,13 M de subs en 5 meses**, 140 M de vistas; este mes 5,2 M y 2,9 M |
| Encontrar la pelota | 2,46 M | 41/49 | creadores con cara | No aplica |
| Mayor o menor | 7 mil | 5/50 | | Flojo |
| Trayectoria (career path) | 39 mil | 2/48 | | Flojo |
| Precio de transferencia | 33 mil | 1/50 | | Flojo |
| Acertijo de fútbol | 55 mil | 4/50 | | Flojo |
| Bebé futbolista | 20 M con cara / **33 mil sin cara** | | famosos | No aplica (y las fotos tienen dueño) |

**Canales que crecieron rápido con "ver quién gana":**
- **DriveLabs:** creado el 30 de mayo de 2026. En 5 meses tiene **1,13 M de subs**, 144 videos y 11 de sus últimos 50 con 1 M+. Hace un juego 3D de obstáculos con las caras de 3 jugadores: "Mbappé, Neymar or Ronaldo? One Trophy, Three Superstars".
- **Fire Rankings:** creado en diciembre de 2025. Tiene 132 mil subs y **198 M de vistas en 10 meses** con carreras de canicas. **Hoy decayó** (mediana de 94 mil) porque repite lo mismo: es la señal de que hay que variar.

## 3. Lista definitiva de formatos

| # | Formato | Recompensa | Por qué | Estado |
|---|---|---|---|---|
| 1 | **"WHO WINS THE RACE?"**: carrera de física real con las caras de los jugadores | Suspenso + elegir bando | La recompensa más rápida, 1,64 M de mediana en fútbol y canales que llegaron a YPP en meses | **Prototipo hecho** (`produccion/render_carrera.py`) |
| 2 | **"WHO IS HE? · AGE EVOLUTION"**: la cara joven envejece hasta hoy | Transformación + nostalgia + curiosidad | La que más seguido explota (9,6% pasa 10 mil vistas/hora), con solo 1,1% de oferta | Falta bajar fotos con fecha |
| 3 | **"PRIME vs NOW" con fotos**: plantel de 2017 vs. hoy, foto a foto con el año | Nostalgia + identidad de club | Mediana de 4,45 M; nosotros lo hacemos sin clips, así que sin riesgo de copyright | Usa las mismas fotos que el #2 |
| 4 | **"FIND THE REAL"** en la ola actual | Curiosidad | La ola viva de FULYON (247 mil vistas/hora) | Motor hecho |
| 5 | **Fusión (lote 1)** | Acierto | Ya está hecho; se mide esta semana | En curso |

**Cómo nos diferenciamos en la carrera (#1)**, porque Fire Rankings decayó por repetir:
- **Atada al evento del día:** los 2 equipos del Clásico, los nominados al Balón de Oro, los países de una eliminatoria.
- **Pista nueva en cada video:** el obstáculo cambia, el ganador puede ser el que va último y el final es ajustado.
- **"PICK ONE NOW"** en el cuadro 0 y "DID YOUR PICK WIN?" al final: comentario de opinión e identidad, no de puntaje.
- **Inglés, con banderas y escudos de selecciones** (identidad).

## 4. Plan para monetizar lo antes posible

- **Requisito de YPP:** 1.000 subs y 10 M de vistas de Shorts en 90 días, o sea **~110 mil vistas por día de promedio**. Desde febrero de 2027, para canales nuevos, son 20 M.
- **Volumen:** 2 videos por día, siempre a las 10:00 y 23:00 ART. El destino de cada video se decide en 72 h (reporte 13).
- **Semana 1 (25–31 oct):** el lote de fusión, más **1 carrera por día en lugar de la segunda fusión**. Si preferís no tocar el lote, la carrera va como tercer video.
- **A las 48–72 h de cada video:**
  - si un formato supera **10 veces la mediana** del canal, se clona 3–5 veces;
  - si queda debajo de la mediana, se corta.
- **Semana 2:** sumar "WHO IS HE?" y "PRIME vs NOW" (después de bajar las fotos con fecha), y quedarse con los 2 formatos que mejor midieron.
- **Realismo** (reporte 09): de los canales serios, el 11% llega a 10 M de vistas. DriveLabs muestra que se puede en meses, pero ni la mejor investigación garantiza un hit. Lo que sube las chances es **probar rápido, medir y clonar**.
