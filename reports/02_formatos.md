# 02 · Formatos de quiz

**Conclusión (generada desde los datos):**
1. **Mejores formatos vs. el promedio de su canal:** armá tu equipo / elegí uno / ruleta 1,35×, verdadero o falso 1,33×, futbolista de chico 1,29×, nombrá jugadores 1,28×, impostor 1,27×, escudo / camiseta / bandera 1,26×, imagen oculta 1,25×, pistas progresivas / ¿quién soy? 1,25×. **Entre los mejores la diferencia es chica: la ejecución pesa más que la elección.**
2. **Sin cara:** nombrá jugadores 1,42×, impostor 1,35×, armá tu equipo / elegí uno / ruleta 1,35×, futbolista de chico 1,32×, escudo / camiseta / bandera 1,29×, verdadero o falso 1,27×, carrera / trayectoria de clubes 1,25×, fichaje / precio 1,24×.
3. **Más flojos:** adiviná por gol/jugada 1,09×, tier list / ranking de opinión 1,09×, preguntas a personas 1,08×, duelo / ¿quién es mejor? / higher-lower 1,06×, opción múltiple a/b/c 1,02×.
4. **Huecos en español** (mucho éxito en inglés, poco en español): armá tu equipo / elegí uno / ruleta (97 videos de 1 M+ en inglés contra 33 en español); imagen oculta (73 videos de 1 M+ en inglés contra 9 en español); ordená de mayor a menor (116 videos de 1 M+ en inglés contra 10 en español); adiviná por gol/jugada (84 videos de 1 M+ en inglés contra 8 en español); tier list / ranking de opinión (126 videos de 1 M+ en inglés contra 31 en español); duelo / ¿quién es mejor? / higher-lower (142 videos de 1 M+ en inglés contra 50 en español).
5. **Fuertes en español** (cantidad de videos de 1 M+): verdadero o falso (18), nombrá jugadores (66), escudo / camiseta / bandera (28), preguntas a personas (55).

## Cómo se midió

- **Formato:** Gemini etiquetó cada short leyendo título, tags y descripción (`research/gemini_clasificar.py`, 30.721 videos de canales de fútbol). Es una etiqueta automática: puede tener errores en casos dudosos.
- **"Rinde vs. el canal":** mediana de (vistas del short ÷ mediana de los últimos 50 del canal). Así se compara el formato **dentro del mismo canal** y no gana el que tiene canales gigantes. **1,40×** quiere decir que ese formato rinde 40% más que lo normal del canal.
- **Base:** shorts subidos por canales de fútbol, últimos 50 de cada uno, con al menos 3 días de antigüedad. **No** los de búsqueda, que están sesgados a lo viral.
- **≥10×:** % de shorts que superan 10 veces la mediana de su canal ("pegaron").

## 1. Rendimiento por formato

| Formato | Shorts | Canales | **Rinde vs. el canal** | ≥2× | ≥10× | Mediana de vistas | Rinde sin cara | Duración mediana |
|---|---|---|---|---|---|---|---|---|
| Armá tu equipo / elegí uno / ruleta | 660 | 139 | **1,35×** | 36% | 6% | 152 mil | 1,35× | 83 s |
| Verdadero o falso | 129 | 66 | **1,33×** | 34% | 12% | 52 mil | 1,27× | 45 s |
| Futbolista de chico | 89 | 34 | **1,29×** | 36% | 6% | 39 mil | 1,32× | 47 s |
| Nombrá jugadores (reto contrarreloj) | 580 | 152 | **1,28×** | 35% | 8% | 114 mil | 1,42× | 63 s |
| Impostor (el que no pertenece) | 527 | 96 | **1,27×** | 38% | 13% | 43 mil | 1,35× | 33 s |
| Escudo / camiseta / bandera | 417 | 109 | **1,26×** | 36% | 6% | 35 mil | 1,29× | 60 s |
| Imagen oculta (silueta, pixelado, zoom) | 904 | 149 | **1,25×** | 36% | 10% | 37 mil | 1,23× | 26 s |
| Pistas progresivas / ¿quién soy? | 295 | 110 | **1,25×** | 38% | 6% | 54 mil | 1,23× | 57 s |
| Emojis | 88 | 29 | **1,17×** | 38% | 6% | 49 mil | 1,17× | 52 s |
| Carrera / trayectoria de clubes | 169 | 59 | **1,15×** | 31% | 6% | 42 mil | 1,25× | 51 s |
| Otros quizzes | 2117 | 286 | **1,15×** | 33% | 8% | 47 mil | 1,07× | 62 s |
| Fichaje / precio | 87 | 47 | **1,15×** | 30% | 7% | 148 mil | 1,24× | 62 s |
| Grilla / quién jugó con ambos | 170 | 59 | **1,14×** | 32% | 4% | 61 mil | 1,14× | 76 s |
| Ordená de mayor a menor | 663 | 148 | **1,13×** | 35% | 10% | 112 mil | 1,14× | 45 s |
| Adiviná por gol/jugada (usa clips) | 487 | 138 | **1,09×** | 30% | 10% | 38 mil | 1,09× | 22 s |
| Tier list / ranking de opinión | 730 | 130 | **1,09×** | 26% | 10% | 114 mil | 1,09× | 42 s |
| Preguntas a personas (en cámara) | 582 | 119 | **1,08×** | 33% | 11% | 54 mil |  | 63 s |
| Duelo / ¿quién es mejor? / higher-lower | 1077 | 246 | **1,06×** | 33% | 10% | 49 mil | 1,06× | 39 s |
| Dato curioso (sin pregunta) | 417 | 125 | **1,03×** | 28% | 6% | 56 mil | 1,00× | 44 s |
| Opción múltiple A/B/C | 246 | 106 | **1,02×** | 28% | 5% | 32 mil | 0,98× | 43 s |
| (no quiz, fútbol) | 6471 | 376 | **0,99×** | 28% | 7% | 54 mil | 0,99× | 36 s |
| (no fútbol) | 1293 | 191 | **0,85×** | 22% | 5% | 38 mil | 0,86× | 53 s |

## 2. Competencia por idioma (shorts quiz del último año que encontré)

"Canales" = cuántos canales distintos lo hacen. "1M+" = shorts con 1 M de vistas o más.
⚠️ Sale de búsquedas ordenadas por vistas: mide **dónde hay éxito visible**, no el total de YouTube.

| Formato | Canales ES | 1M+ ES | Mediana ES | Canales EN | 1M+ EN | Mediana EN | Canales PT | 1M+ PT |
|---|---|---|---|---|---|---|---|---|
| Armá tu equipo / elegí uno / ruleta | 44 | 33 | 90 mil | 60 | 97 | 224 mil | 22 | 15 |
| Verdadero o falso | 38 | 18 | 59 mil | 32 | 10 | 249 mil | 11 | 2 |
| Futbolista de chico | 12 | 4 | 40 mil | 23 | 3 | 37 mil | 10 | 3 |
| Nombrá jugadores (reto contrarreloj) | 51 | 66 | 98 mil | 64 | 67 | 147 mil | 24 | 12 |
| Impostor (el que no pertenece) | 41 | 26 | 44 mil | 43 | 34 | 50 mil | 21 | 5 |
| Escudo / camiseta / bandera | 39 | 28 | 86 mil | 48 | 10 | 35 mil | 23 | 4 |
| Imagen oculta (silueta, pixelado, zoom) | 46 | 9 | 57 mil | 71 | 73 | 27 mil | 26 | 9 |
| Pistas progresivas / ¿quién soy? | 44 | 18 | 43 mil | 47 | 31 | 32 mil | 18 | 7 |
| Emojis | 11 | 1 | 29 mil | 19 | 6 | 93 mil | 11 | 0 |
| Carrera / trayectoria de clubes | 18 | 6 | 138 mil | 23 | 3 | 26 mil | 18 | 3 |
| Fichaje / precio | 22 | 7 | 42 mil | 21 | 17 | 357 mil | 7 | 1 |
| Grilla / quién jugó con ambos | 16 | 8 | 40 mil | 23 | 3 | 76 mil | 15 | 7 |
| Ordená de mayor a menor | 33 | 10 | 36 mil | 78 | 116 | 96 mil | 21 | 9 |
| Adiviná por gol/jugada (usa clips) | 53 | 8 | 21 mil | 86 | 84 | 32 mil | 21 | 4 |
| Tier list / ranking de opinión | 41 | 31 | 85 mil | 75 | 126 | 128 mil | 18 | 9 |
| Preguntas a personas (en cámara) | 70 | 55 | 36 mil | 46 | 18 | 88 mil | 17 | 8 |
| Duelo / ¿quién es mejor? / higher-lower | 95 | 50 | 40 mil | 127 | 142 | 47 mil | 32 | 7 |
| Opción múltiple A/B/C | 38 | 10 | 4 mil | 53 | 17 | 10 mil | 16 | 1 |

**Lectura:**
- **Saturado en inglés y con hueco en español:** imagen oculta, ordená, tier list, armá tu equipo, gol/jugada (este no, por los clips).
- **Fuerte en español:** verdadero o falso, escudo, nombrá jugadores, impostor, preguntas a personas (esta con cara).
- **Grilla / "quién jugó con ambos":** pocos canales en los tres idiomas. Es un formato nicho, con muchos likes (reporte 05) pero vistas medias.

## 3. Ejemplos para mirar

| Formato | Ejemplo (más visto, últimos 12 meses, sin cara si hay) | Canal | Vistas |
|---|---|---|---|
| Armá tu equipo / elegí uno / ruleta | [RONALDINHO PICKED HIS ULTIMATE TEAM 😱🔥#efootball #efootball2025 #short](https://youtube.com/shorts/xu498c5WjVc) | ★PES GAMER 20 | 44,1 M |
| Armá tu equipo / elegí uno / ruleta | [⚽️GUESS THE FIFA WORLD CUP PLAYER BY THEIR JERSEY NUMBER / 🏆 WHO BUILT](https://youtube.com/shorts/OfjFEfmHcTk) | DAIMER | 10,3 M |
| Verdadero o falso | [Christiano Ronaldo support Argentina Messi. Is this real? #cr7 #messi ](https://youtube.com/shorts/DJhokGyN2Yo) | Sports Insights | 3,7 M |
| Verdadero o falso | [ZERO BALL KNOWLEDGE SHOWN IN THIS TRUE OR FALSE QUIZ 👀 #football #socc](https://youtube.com/shorts/s6L-mjGcsvc) | GOAL's Front Three | 2,4 M |
| Futbolista de chico | [🇧🇷 2002 WORLD CUP WINNERS THEN VS NOW #football #shorts](https://youtube.com/shorts/BkgMJShPtdI) | FootyPivot | 11,1 M |
| Futbolista de chico | [ADIVINHE O JOGADOR QUANDO CRIANÇA?👋🏼⚽️ #shorts](https://youtube.com/shorts/T65b98OuG6g) | DesocupadosFC | 4,8 M |
| Nombrá jugadores (reto contrarreloj) | [Son Harfle Futbolcu Challenge  #football #futbol #challenge #shortvide](https://youtube.com/shorts/g9YZnenADvE) | Göktuğ Emin Kaba | 11,5 M |
| Nombrá jugadores (reto contrarreloj) | [JOGADORES QUE FIZERAM GOL NA COPA ⚽️](https://youtube.com/shorts/Xsa51mUdnYI) | Keke do Bola Fora | 5,8 M |
| Impostor (el que no pertenece) | [Hangisi Imposter?  #football #soccer #challenge #futbol #shortvideo #s](https://youtube.com/shorts/I9YUYcMOKL4) | AYAYAY Football | 7,8 M |
| Impostor (el que no pertenece) | [FIND RONALDO JUDE BELLINGHAM HAALAND](https://youtube.com/shorts/FACb6nTYEls) | SpotVerse | 5,2 M |
| Escudo / camiseta / bandera | [GUESS FOOTBALL CLUB LOGO #USA](https://youtube.com/shorts/6LXaZ4CFkoM) | Ovis Games | 42,4 M |
| Escudo / camiseta / bandera | [⚽️ Forma Numarasını Tahmin Et, Golü At! #28](https://youtube.com/shorts/8ZBfBRaHUXs) | Akıl Oyunu | 8,4 M |
| Imagen oculta (silueta, pixelado, zoom) | [Top 4 Momentos Engraçados Acerte o Jogador #shorts  #futebol  #ranking](https://youtube.com/shorts/X3MRo5WpFhA) | Kazin dos Rank | 18,7 M |
| Imagen oculta (silueta, pixelado, zoom) | [Who Scored THIS Unreal Goal For Barça? 🤯](https://youtube.com/shorts/lNlxq_6NMog) | MStriker | 17,4 M |
| Pistas progresivas / ¿quién soy? | [99% of people didn't now the last player . i dare you to now him.](https://youtube.com/shorts/BrB4I7FlpGE) | Its-sdk | 8,8 M |
| Pistas progresivas / ¿quién soy? | [Yo fui el maestro de ese entrenador que todos conocemos… ¿quienes son?](https://youtube.com/shorts/ct8CP38t03Q) | David_S Football | 8,0 M |
| Emojis | [Emojilerle Futbolcu Challenge #football #futbol #challenge #shortvideo](https://youtube.com/shorts/8PfpA5cR9Ko) | AYAYAY Football | 3,5 M |
| Emojis | [ERRATE den FUSSBALLER NUR an EMOJIS! ⚽ 👀](https://youtube.com/shorts/4idLzYy4zNA) | LarsHolzi | 628 mil |
| Carrera / trayectoria de clubes | [UM JOGADOR QUE JOGOU POR…](https://youtube.com/shorts/Xz0_D4mLu0Y) | Cayo Da Resenha | 5,6 M |
| Carrera / trayectoria de clubes | [En qué clubes jugaron estos futbolistas? 🤔⚽️ #futbol #fcbarcelona #rod](https://youtube.com/shorts/LzFRBcgBJBg) | Edson FDB | 5,3 M |
| Fichaje / precio | [CUÁL ES TU SOBRE MUNDIAL 2026 JUGADOR GRATIS 🎁😱? #mundial2026 #mundial](https://youtube.com/shorts/hfan9TO8xN0) | MOISÉS ISMAEL PS MOD Z🇪🇨 | 4,4 M |
| Fichaje / precio | [Player Values Then vs Now… 😅](https://youtube.com/shorts/9xfL40hgLNo) | Tom Harris Football | 2,9 M |
| Grilla / quién jugó con ambos | [Sürpriz Sonlu Takımlı XOX!  #football #soccer #futbol  #challenge #sho](https://youtube.com/shorts/-BdFZ7HYEes) | AYAYAY Football | 3,4 M |
| Grilla / quién jugó con ambos | [Fenerbahçe ve Beşiktaş'ta Oynamış Aynı Futbolcuyu Söyleyen Elenir! #fo](https://youtube.com/shorts/ptFOCfuYyTM) | AYAYAY Football | 3,3 M |
| Ordená de mayor a menor | [Ranking The Best World Cup Teams 😭 #shorts #fifa #worldcup #football #](https://youtube.com/shorts/V9MMwxcN82w) | Alpaca Ranks | 17,4 M |
| Ordená de mayor a menor | [Ranking Unexpected Football Edits #football #shorts #viral #ranking #r](https://youtube.com/shorts/1iIGwEpb2sw) | Merixfuy | 17,1 M |
| Adiviná por gol/jugada (usa clips) | [Yamal & His Skills Are Insane..🤯🔥](https://youtube.com/shorts/csIa38fGT98) | FlashPass | 29,3 M |
| Adiviná por gol/jugada (usa clips) | [Lamine Yamal Skills 💫](https://youtube.com/shorts/XhN2ZfXcegY) | Femyft | 26,0 M |
| Tier list / ranking de opinión | [Which one was the best? ❤️ #worldcup #football #ranking](https://youtube.com/shorts/TTvJBFuWecs) | FootballRanks | 29,0 M |
| Tier list / ranking de opinión | [Top 5 Momentos del hermano de Lamine Yamal en la final del mundial, Ke](https://youtube.com/shorts/RvSRJVqUUw0) | PituX | 28,6 M |
| Preguntas a personas (en cámara) | [Kids World Cup Debate! 🏆⚽️](https://youtube.com/shorts/CdNPjxnrEWU) | BR2 | 21,7 M |
| Preguntas a personas (en cámara) | [Julian Alvarez Picked His Current best Player of nations 😱🔥 #efootball](https://youtube.com/shorts/_Yr9aIc9evA) | ★PES GAMER 20 | 19,5 M |
| Duelo / ¿quién es mejor? / higher-lower | [Real Madrid or Barcelona?⚽🥳#football #mbappe #lamineyamal](https://youtube.com/shorts/02LL1LzcQQw) | GUGUGAMER  | 97,3 M |
| Duelo / ¿quién es mejor? / higher-lower | [Yamal At 18 Vs Mbappe  😅](https://youtube.com/shorts/4pDpcj1bSmY) | cfcfootball | 52,8 M |
| Opción múltiple A/B/C | [Which Footballer Has The Best Boots? 👞⚽️](https://youtube.com/shorts/Jo30fOWrAYU) | BR2 | 23,7 M |
| Opción múltiple A/B/C | [Which World Cup Ball is Best? 🎯⚽️](https://youtube.com/shorts/8j0s7mzsLZM) | BR2 | 8,8 M |

> La lista completa (un short por fila, con formato, vistas, likes y comentarios) está en `data/processed/videos.csv`. Se puede filtrar por `formato`.
