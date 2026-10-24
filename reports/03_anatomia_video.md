# 03 · Anatomía del video ganador

**Conclusión: la plantilla ganadora sin cara**
- **15 a 30 s**, con **3 o 4 rondas**.
- **Gancho escrito gigante en el primer segundo**, un desafío como "FIND THE REAL RONALDO" o "NAME THAT PLAYER".
- **2 a 3 s para pensar**, con **cuenta regresiva visible** (número grande más barra que se vacía) y tic-tac.
- **Revelación con sonido de acierto.**
- **Música de tendencia de fondo, casi siempre sin voz.**
- **El final corta al inicio (loop).**

Los videos con cara son más largos (~50–70 s) y viven de la persona: no aplican a tu caso.

Datos: Gemini miró **125 shorts de fútbol** desde su link (sin descargarlos):
- los 100 shorts quiz más vistos del último año (máximo 3 por canal);
- los 4 mejores de cada canal sin cara que creció rápido.

Detalle por video en `data/processed/anatomia.csv`; respuesta cruda en `data/raw/gemini_shorts/<id>.json`. Script: `research/gemini_shorts.py`.

> ⚠️ Los tiempos son los que reporta Gemini mirando el video: pueden errar en ±1 s y algún dato puede estar mal interpretado. No pude medir cortes con ffmpeg porque YouTube bloquea la descarga (ver README).

## 1. Números clave

| | Todos (n=125) | Sin cara (n=52) | Con cara (n=73) |
|---|---|---|---|
| Duración mediana (s) | 36,0 | 28,5 | 52,0 |
| Duración 25–75% (s) | 22–60 | 18–34 | 28–71 |
| Fin del gancho, mediana (s) | 2,0 | 2,0 | 2,1 |
| Tiempo para pensar por pregunta, mediana (s) | 2,0 | 2,0 | 2,2 |
| Preguntas o rondas, mediana | 5,0 | 3,5 | 5,0 |
| Cambios de plano, mediana | 4,0 | 4,0 | 5,0 |
| Gancho = pregunta directa | 34% | 27% | 40% |
| Gancho = desafío ("solo el 1%") | 23% | 21% | 25% |
| Gancho = acción/sorpresa | 25% | 27% | 23% |
| Cuenta regresiva | 30% | 44% | 19% |
| Loop (final empalma con el inicio) | 30% | 44% | 19% |
| Voz humana | 56% | 15% | 85% |
| Voz IA/TTS | 18% | 37% | 5% |
| Sin voz | 24% | 44% | 10% |
| Con música | 79% | 94% | 68% |
| Música de tendencia/viral/phonk | 33% | 60% | 14% |
| Subtítulos de la voz | 11% | 2% | 18% |
| Fotos de jugadores | 51% | 56% | 48% |
| Escudos o logos | 38% | 31% | 44% |
| Clips de partidos/TV ⚠️ | 37% | 63% | 18% |
| Invita a comentar | 57% | 50% | 62% |

## 2. Estructura tipo (sin cara, ~20 s)

| Tramo | Segundos | Qué pasa |
|---|---|---|
| Gancho | 0–1 | Texto gigante con el desafío más la primera imagen ya en pantalla. Sin intro ni logo. |
| Ronda 1 | 1–5 | Imagen o pregunta, cuenta regresiva 3-2-1 (número central más barra), tic-tac. |
| Revelación 1 | 5–6 | Nombre o respuesta grande, sonido de acierto (ding), zoom o flash. |
| Rondas 2–4 | 6–18 | Igual, cada vez más difícil ("el último solo el 1%"). |
| Cierre / loop | 18–20 | Corte seco a una imagen que empalma con el inicio, o "¿cuántas acertaste? 👇". Nada de "suscribite" largo. |

## 3. Ejemplos sin cara para mirar (los que más vistas tienen de la muestra)

| Short | Canal | Vistas | Dura | Formato (según Gemini) | Gancho | Pensar | Loop | Música | Clips |
|---|---|---|---|---|---|---|---|---|---|
| [Guess The Player 🤔 pt.6](https://youtube.com/shorts/quKuZTx7_EQ) | Blade Sports | 49.5 M | 18 s | adivina el jugador de fútbol basado en su silueta de una jug | GUESS PLAYER (3.0 s) | 3.0 s | no | canción pop viral de fond | ⚠️ |
| [Mbappe Vs Argentina💀🤯 #shorts #football #socc](https://youtube.com/shorts/A5c9iaN2dYI) | Life Football | 36.5 M | 83 s | análisis de jugada de fútbol con texto superpuesto y narraci | Mbappe Vs Argentina 💀 (4.0 s) | 0.0 s | sí | de fondo | ⚠️ |
| [Ronaldo Vs Juventus Prime☠️👀 #shorts #footbal](https://youtube.com/shorts/GPkaaQCWGGg) | Life Football | 33.7 M | 78 s | recopilación de jugadas de un partido con texto superpuesto  | Ronaldo Vs Juventus (3.0 s) | 0.0 s | sí | de fondo, música dramátic | ⚠️ |
| [Lamine Yamal vs Ronaldo Dressing Challenge 😱🔥](https://youtube.com/shorts/PwYDlELz-f8) | Muzam | 30.9 M | 16 s | juego de personalización de avatares de futbolistas mediante | ranki te cankin can y que fue (1.0 s) | 0.0 s | sí | tendencia/viral |  |
| [Who is the GOAT? Lamine Yamal or Ronaldo?🤩🤫 #](https://youtube.com/shorts/KH3qZ7zOwv4) | Funny Sharpener | 24.6 M | 15 s | juego de emparejar caras de futbolistas con sus equipos o pa | el de top of your game (1.0 s) | 0.0 s | sí | canción viral de fondo |  |
| [Ranking Funniest Unusual Ronaldo Goals](https://youtube.com/shorts/QuJlv-OuTjI) | TIER | 20.5 M | 33 s | Ranking de goles inusuales de Cristiano Ronaldo con una list | RANKING FUNNIEST UNUSUAL RONAL (2.0 s) | 0.0 s | no | De fondo, ritmo rápido y  | ⚠️ |
| [Arda Güler 🪄🇹🇷](https://youtube.com/shorts/dcVzHXjh_5k) | UEFA | 18.3 M | 8 s | clip de jugada espectacular con música de tendencia | nan (0.0 s) | 0.0 s | sí | música electrónica de ten | ⚠️ |
| [Who Scored THIS Unreal Goal For Barça? 🤯](https://youtube.com/shorts/lNlxq_6NMog) | MStriker | 17.4 M | 30 s | Adivina el jugador de fútbol a partir de un clip con silueta | NAME THAT PLAYER (0.5 s) | 3.0 s | sí | música electrónica de ten | ⚠️ |
| [Guess the player by their skill!](https://youtube.com/shorts/9bJrFcSo868) | Futcrunch | 17.1 M | 33 s | adivinar jugador por sus habilidades o estilo de juego (con  | Guess the player by their skil (2.1 s) | 4.0 s | sí | nan |  |
| [Ranking Unexpected Football Edits #football #](https://youtube.com/shorts/1iIGwEpb2sw) | Merixfuy | 17.1 M | 52 s | Ranking de clips de fútbol editados con transiciones rápidas | Ranking Unexpected Top Footbal (3.0 s) | 0.0 s | sí | tendencia/viral (remix de | ⚠️ |
| [Ranking Best Flag Football Moments 🏈](https://youtube.com/shorts/ToJv33Ew-iE) | ZedBall | 15.5 M | 41 s | Ranking de los 5 mejores momentos de flag football, presenta | This is what happens when your (3.5 s) | 0.0 s | sí | Música de fondo rítmica y | ⚠️ |
| [Ranking The Most Humiliating Ankle Breakers E](https://youtube.com/shorts/OeDcWPdrLWA) | Trash Tier | 13.4 M | 37 s | Ranking de momentos de fútbol con clips de 'ankle breakers'  | Ranking Best Ankle Breaker Mom (0.5 s) | 0.0 s | no | Música de fondo de tenden | ⚠️ |
| [Guess The Player 🤔 pt.7](https://youtube.com/shorts/7lvlBCStPnU) | Blade Sports | 13.3 M | 18 s | adivinar el jugador de fútbol según jugada | GUESS PLAYER (3.0 s) | 3.0 s | sí | canción viral en loop de  | ⚠️ |
| [Guess The Player 🤔 pt.4](https://youtube.com/shorts/kWlV9MKeIH8) | Blade Sports | 13.1 M | 18 s | adivinar jugador entre dos opciones con cuenta regresiva | GUESS PLAYER (4.0 s) | 3.0 s | no | canción pop melódica en i | ⚠️ |
| [Ranking Funniest Shameless Handball Goals](https://youtube.com/shorts/tfv9iAtzzyg) | TIER | 12.2 M | 33 s | ranking de momentos polémicos de fútbol con comentarios humo | RANKING FUNNIEST SHAMELESS HAN (2.0 s) | 0.0 s | no | música de fondo rítmica y | ⚠️ |
| [Only 1% Can Guess The IMPOSSIBLE Real Madrid ](https://youtube.com/shorts/cCCph2yHWsM) | MStriker | 11.3 M | 28 s | adivinar 4 futbolistas por niveles de dificultad creciente | EASY, MEDIUM, HARD, IMPOSSIBLE (6.0 s) | 2.0 s | no | remix viral de fondo con  | ⚠️ |
| [Ranking Funniest Big Brain Football Calls](https://youtube.com/shorts/nFQy04XvsvA) | TIER | 10.6 M | 34 s | Ranking de momentos polémicos o curiosos en el fútbol con un | RANKING FUNNIEST BIG BRAIN FOO (2.0 s) | 0.0 s | no | Música de fondo cómica y  | ⚠️ |
| [Ronaldo Vs Albulayhi😈☠️ #shorts #football #so](https://youtube.com/shorts/bCJekB9Pea4) | Life Football | 10.5 M | 61 s | recopilación de momentos de confrontación de un jugador espe | Son Vs Albulayhi 🤡 Wait for it (3.0 s) | 0.0 s | no | música de tendencia/viral | ⚠️ |
| [Guess the Player: Real Madrid Edition – I dar](https://youtube.com/shorts/M-6uBP34hJM) | Its-sdk | 10.0 M | 46 s | Juego de adivinar el jugador de fútbol a partir de un clip d | EASY MEDIUM HARD IMPOSSIBLE (0.5 s) | 3.0 s | no | Canción de tendencia/vira | ⚠️ |
| [Ranking Funniest 2026 World Cup Fans](https://youtube.com/shorts/YeQP-pSNCfQ) | TIER | 9.9 M | 36 s | Ranking de momentos divertidos de fans en el fútbol | RANKING FUNNIEST 2026 WORLD CU (3.0 s) | 0.0 s | no | Música de fondo cómica y  | ⚠️ |
| [Ranking Best Dodgeball Fail Moments!💀](https://youtube.com/shorts/YZ1U8tNXC0M) | Trash Tier | 9.1 M | 32 s | Recopilación de clips de momentos fallidos en dodgeball con  | Ranking Best Dodgeball Fail Mo (2.0 s) | 0.0 s | no | Música de fondo viral y r | ⚠️ |
| [FIND RONALDO HAALAND LAMINE YAMAL / 99% FAIL ](https://youtube.com/shorts/LrK_zRBs0p0) | SpotVerse | 8.7 M | 16 s | juego de encontrar al jugador diferente en una cuadrícula de | FIND RONALDO (1.0 s) | 4.0 s | sí | música de fondo rítmica y |  |
| [FIND RONALDO NEYMAR VINICIUS JUNIOR](https://youtube.com/shorts/yHAn_w0jBNg) | SpotVerse | 8.7 M | 16 s | juego de encontrar al jugador real entre una cuadrícula de v | FIND REAL RONALDO (1.0 s) | 3.0 s | no | música de tendencia tipo  |  |
| [Guess The Players 🤔](https://youtube.com/shorts/QCr47rL1dhc) | Samuel Comps | 8.4 M | 18 s | adivinar el jugador de fútbol entre 2 opciones | GUESS THE PLAYER (3.0 s) | 3.0 s | no | tendencia/viral con ritmo | ⚠️ |
| [Lamine Yamal vs Ronaldo Dressing Challenge 😱🔥](https://youtube.com/shorts/ND-eXAr9aMw) | Muzam | 7.5 M | 16 s | Juego de personalización de jugadores mediante la selección  | Ranki ti cankin can, y qué fue (1.0 s) | 0.0 s | sí | Música urbana viral de fo |  |

## 4. Título, descripción y hashtags

Ver la tabla `titulos` en `data/processed/videos.csv` (columnas `titulo_len`, `titulo_pregunta`, `titulo_emojis`, `titulo_mayus`, `titulo_hashtags`) y el resumen abajo.

| | Shorts quiz de 1 M o más | Resto |
|---|---|---|
| Largo del título (caracteres, mediana) | 53 | 60 |
| Con signo de pregunta | 29% | 38% |
| Con al menos 1 emoji | 56% | 51% |
| % de mayúsculas (mediana) | 17% | 19% |
| Con hashtags en el título | 54% | 60% |
| Usa #shorts (título o descripción) | 40% | 39% |

(n = 1736 shorts de 1 M o más y 12691 del resto.)
