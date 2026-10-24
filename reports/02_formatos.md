# 02 · Formatos de quiz

**Conclusión:**
1. **Los formatos que más rinden por encima del promedio de su propio canal:** verdadero o falso, imagen oculta, pistas, armá tu equipo, impostor, escudo, nombrá jugadores y carrera. Todos rinden 1,25 a 1,45 veces lo normal del canal.
2. **Sin cara**, los mejores son carrera, imagen oculta, impostor, nombrá jugadores, armá tu equipo y escudo. **Todos se pueden hacer con plantilla.**
3. **Flojos o saturados:** emojis (0,9×, ningún outlier), duelo, opción múltiple y gol/jugada (este además usa clips, ver reporte 07).
4. **Huecos en español** (rinden bien y hay pocos canales que los hagan): **imagen oculta** (en inglés hay 49 videos de 1 M o más, en español 8), **ordená de mayor a menor** (95 contra 10), **tier list**, **armá tu equipo** y **carrera**.
5. **En español ya funcionan bien:** verdadero o falso (mediana 225 mil, 18 videos de 1 M o más), escudo, nombrá jugadores e impostor.

## Cómo se midió

- **Formato:** Gemini etiquetó cada short leyendo título, tags y descripción (`research/gemini_clasificar.py`, 21.277 videos de canales de fútbol). Es una etiqueta automática: puede tener errores en casos dudosos.
- **"Rinde vs. el canal":** mediana de (vistas del short ÷ mediana de los últimos 50 del canal). Así se compara el formato **dentro del mismo canal** y no gana el que tiene canales gigantes. **1,40×** quiere decir que ese formato rinde 40% más que lo normal del canal.
- **Base:** shorts subidos por canales de fútbol, últimos 50 de cada uno, con al menos 3 días de antigüedad. **No** los de búsqueda, que están sesgados a lo viral.
- **≥10×:** % de shorts que superan 10 veces la mediana de su canal ("pegaron").

## 1. Rendimiento por formato

| Formato | Shorts | Canales | **Rinde vs. el canal** | ≥2× | ≥10× | Mediana de vistas | Rinde sin cara | Duración mediana |
|---|---|---|---|---|---|---|---|---|
| Verdadero o falso | 89 | 47 | **1,43×** | 37% | 16% | 66 mil | 1,27× | 45 s |
| Imagen oculta (silueta, pixelado, zoom) | 557 | 99 | **1,40×** | 39% | 10% | 47 mil | 1,39× | 27 s |
| Pistas progresivas / ¿quién soy? | 230 | 84 | **1,34×** | 39% | 8% | 81 mil | 1,28× | 56 s |
| Armá tu equipo / elegí uno / ruleta | 560 | 109 | **1,33×** | 35% | 7% | 200 mil | 1,36× | 81 s |
| Impostor (el que no pertenece) | 433 | 71 | **1,32×** | 39% | 11% | 51 mil | 1,38× | 33 s |
| Escudo / camiseta / bandera | 280 | 77 | **1,31×** | 35% | 6% | 44 mil | 1,35× | 61 s |
| Nombrá jugadores (reto contrarreloj) | 431 | 117 | **1,28×** | 35% | 8% | 159 mil | 1,37× | 64 s |
| Carrera / trayectoria de clubes | 91 | 42 | **1,25×** | 32% | 5% | 97 mil | 1,46× | 67 s |
| Fichaje / precio | 54 | 28 | **1,21×** | 35% | 9% | 302 mil |  | 62 s |
| Otros quizzes | 1610 | 215 | **1,15×** | 34% | 9% | 53 mil | 1,04× | 62 s |
| Ordená de mayor a menor | 614 | 124 | **1,14×** | 36% | 11% | 123 mil | 1,15× | 44 s |
| Futbolista de chico | 40 | 23 | **1,12×** | 28% | 2% | 41 mil |  | 54 s |
| Tier list / ranking de opinión | 665 | 104 | **1,09×** | 27% | 10% | 117 mil | 1,09× | 40 s |
| Preguntas a personas (en cámara) | 522 | 100 | **1,08×** | 33% | 11% | 50 mil |  | 63 s |
| Adiviná por gol/jugada (usa clips) | 346 | 96 | **1,04×** | 29% | 10% | 49 mil | 1,04× | 22 s |
| Grilla / quién jugó con ambos | 128 | 43 | **1,04×** | 31% | 5% | 58 mil | 1,13× | 84 s |
| Opción múltiple A/B/C | 204 | 84 | **1,02×** | 29% | 5% | 32 mil | 1,02× | 42 s |
| Dato curioso (sin pregunta) | 300 | 86 | **1,02×** | 30% | 7% | 65 mil | 1,00× | 48 s |
| Duelo / ¿quién es mejor? / higher-lower | 792 | 185 | **1,02×** | 32% | 9% | 61 mil | 1,00× | 37 s |
| (no quiz, fútbol) | 4907 | 287 | **0,99×** | 28% | 7% | 60 mil | 0,98× | 34 s |
| Emojis | 52 | 20 | **0,92×** | 33% | 0% | 39 mil | 0,91× | 62 s |
| (no fútbol) | 999 | 151 | **0,91×** | 24% | 6% | 43 mil | 0,90× | 52 s |

## 2. Competencia por idioma (shorts quiz del último año que encontré)

"Canales" = cuántos canales distintos lo hacen. "1M+" = shorts con 1 M de vistas o más.
⚠️ Sale de búsquedas ordenadas por vistas: mide **dónde hay éxito visible**, no el total de YouTube.

| Formato | Canales ES | 1M+ ES | Mediana ES | Canales EN | 1M+ EN | Mediana EN | Canales PT | 1M+ PT |
|---|---|---|---|---|---|---|---|---|
| Verdadero o falso | 30 | 18 | 225 mil | 17 | 7 | 353 mil | 8 | 2 |
| Imagen oculta (silueta, pixelado, zoom) | 34 | 8 | 68 mil | 46 | 49 | 39 mil | 20 | 9 |
| Pistas progresivas / ¿quién soy? | 32 | 18 | 121 mil | 28 | 16 | 194 mil | 16 | 7 |
| Armá tu equipo / elegí uno / ruleta | 35 | 33 | 126 mil | 43 | 69 | 287 mil | 18 | 15 |
| Impostor (el que no pertenece) | 34 | 26 | 49 mil | 28 | 26 | 58 mil | 19 | 5 |
| Escudo / camiseta / bandera | 30 | 28 | 91 mil | 30 | 9 | 51 mil | 19 | 4 |
| Nombrá jugadores (reto contrarreloj) | 37 | 65 | 196 mil | 48 | 54 | 190 mil | 22 | 12 |
| Carrera / trayectoria de clubes | 15 | 6 | 105 mil | 11 | 1 | 197 mil | 16 | 3 |
| Fichaje / precio | 16 | 7 | 37 mil | 10 | 13 | 2,9 M | 4 | 1 |
| Ordená de mayor a menor | 28 | 10 | 118 mil | 66 | 95 | 122 mil | 20 | 9 |
| Futbolista de chico | 9 | 4 | 97 mil | 12 | 1 | 41 mil | 9 | 3 |
| Tier list / ranking de opinión | 35 | 31 | 115 mil | 60 | 73 | 131 mil | 14 | 9 |
| Preguntas a personas (en cámara) | 60 | 52 | 39 mil | 33 | 17 | 66 mil | 16 | 8 |
| Adiviná por gol/jugada (usa clips) | 40 | 6 | 18 mil | 59 | 82 | 60 mil | 16 | 4 |
| Grilla / quién jugó con ambos | 15 | 8 | 43 mil | 15 | 1 | 59 mil | 13 | 7 |
| Opción múltiple A/B/C | 28 | 10 | 2 mil | 39 | 15 | 9 mil | 15 | 1 |
| Duelo / ¿quién es mejor? / higher-lower | 74 | 49 | 60 mil | 91 | 107 | 61 mil | 25 | 7 |
| Emojis | 8 | 1 | 29 mil | 8 | 5 | 230 mil | 11 | 0 |

**Lectura:**
- **Saturado en inglés y con hueco en español:** imagen oculta, ordená, tier list, armá tu equipo, gol/jugada (este no, por los clips).
- **Fuerte en español:** verdadero o falso, escudo, nombrá jugadores, impostor, preguntas a personas (esta con cara).
- **Grilla / "quién jugó con ambos":** pocos canales en los tres idiomas. Es un formato nicho, con muchos likes (reporte 05) pero vistas medias.

## 3. Ejemplos para mirar

| Formato | Ejemplo (más visto, últimos 12 meses, sin cara si hay) | Canal | Vistas |
|---|---|---|---|
| Verdadero o falso | [ZERO BALL KNOWLEDGE SHOWN IN THIS TRUE OR FALSE QUIZ 👀 #football #socc](https://youtube.com/shorts/s6L-mjGcsvc) | GOAL's Front Three | 2,4 M |
| Verdadero o falso | [Will Ronaldo win a World Cup? 🤫👇 #ronaldo #football all](https://youtube.com/shorts/zk7BjdDkEQc) | Funny Sharpener | 1,3 M |
| Imagen oculta (silueta, pixelado, zoom) | [Top 4 Momentos Engraçados Acerte o Jogador #shorts  #futebol  #ranking](https://youtube.com/shorts/X3MRo5WpFhA) | Kazin dos Rank | 18,7 M |
| Imagen oculta (silueta, pixelado, zoom) | [Who Scored THIS Unreal Goal For Barça? 🤯](https://youtube.com/shorts/lNlxq_6NMog) | MStriker | 17,4 M |
| Pistas progresivas / ¿quién soy? | [99% of people didn't now the last player . i dare you to now him.](https://youtube.com/shorts/BrB4I7FlpGE) | Its-sdk | 8,8 M |
| Pistas progresivas / ¿quién soy? | [Yo fui el maestro de ese entrenador que todos conocemos… ¿quienes son?](https://youtube.com/shorts/ct8CP38t03Q) | David_S Football | 8,0 M |
| Armá tu equipo / elegí uno / ruleta | [RONALDINHO PICKED HIS ULTIMATE TEAM 😱🔥#efootball #efootball2025 #short](https://youtube.com/shorts/xu498c5WjVc) | ★PES GAMER 20 | 44,1 M |
| Armá tu equipo / elegí uno / ruleta | [⚽️GUESS THE FIFA WORLD CUP PLAYER BY THEIR JERSEY NUMBER / 🏆 WHO BUILT](https://youtube.com/shorts/OfjFEfmHcTk) | DAIMER | 10,3 M |
| Impostor (el que no pertenece) | [Hangisi Imposter?  #football #soccer #challenge #futbol #shortvideo #s](https://youtube.com/shorts/I9YUYcMOKL4) | AYAYAY Football | 7,8 M |
| Impostor (el que no pertenece) | [FIND RONALDO JUDE BELLINGHAM HAALAND](https://youtube.com/shorts/FACb6nTYEls) | SpotVerse | 5,2 M |
| Escudo / camiseta / bandera | [GUESS FOOTBALL CLUB LOGO #USA](https://youtube.com/shorts/6LXaZ4CFkoM) | Ovis Games | 42,4 M |
| Escudo / camiseta / bandera | [⚽️ Forma Numarasını Tahmin Et, Golü At! #28](https://youtube.com/shorts/8ZBfBRaHUXs) | Akıl Oyunu | 8,4 M |
| Nombrá jugadores (reto contrarreloj) | [JOGADORES QUE FIZERAM GOL NA COPA ⚽️](https://youtube.com/shorts/Xsa51mUdnYI) | Keke do Bola Fora | 5,8 M |
| Nombrá jugadores (reto contrarreloj) | [Futbolcuların Ülkelerini Bul!  #football #soccer #futbol #challenge #s](https://youtube.com/shorts/VXJ2EnLIUNg) | AYAYAY Football | 3,8 M |
| Carrera / trayectoria de clubes | [UM JOGADOR QUE JOGOU POR…](https://youtube.com/shorts/Xz0_D4mLu0Y) | Cayo Da Resenha | 5,6 M |
| Carrera / trayectoria de clubes | [En qué clubes jugaron estos futbolistas? 🤔⚽️ #futbol #fcbarcelona #rod](https://youtube.com/shorts/LzFRBcgBJBg) | Edson FDB | 5,3 M |
| Fichaje / precio | [CUÁL ES TU SOBRE MUNDIAL 2026 JUGADOR GRATIS 🎁😱? #mundial2026 #mundial](https://youtube.com/shorts/hfan9TO8xN0) | MOISÉS ISMAEL PS MOD Z🇪🇨 | 4,4 M |
| Fichaje / precio | [Player Values Then vs Now… 😅](https://youtube.com/shorts/9xfL40hgLNo) | Tom Harris Football | 2,9 M |
| Ordená de mayor a menor | [Ranking The Best World Cup Teams 😭 #shorts #fifa #worldcup #football #](https://youtube.com/shorts/V9MMwxcN82w) | Alpaca Ranks | 17,4 M |
| Ordená de mayor a menor | [Ranking Unexpected Football Edits #football #shorts #viral #ranking #r](https://youtube.com/shorts/1iIGwEpb2sw) | Merixfuy | 17,1 M |
| Futbolista de chico | [ADIVINHE O JOGADOR QUANDO CRIANÇA?👋🏼⚽️ #shorts](https://youtube.com/shorts/T65b98OuG6g) | DesocupadosFC | 4,8 M |
| Futbolista de chico | [ADIVINHE O JOGADOR CRIANÇA!👋🏼⚽️ #shorts](https://youtube.com/shorts/Gd6IYAEVzUQ) | DesocupadosFC | 3,0 M |
| Tier list / ranking de opinión | [Which one was the best? ❤️ #worldcup #football #ranking](https://youtube.com/shorts/TTvJBFuWecs) | FootballRanks | 29,0 M |
| Tier list / ranking de opinión | [Top 5 Momentos del hermano de Lamine Yamal en la final del mundial, Ke](https://youtube.com/shorts/RvSRJVqUUw0) | PituX | 28,6 M |
| Preguntas a personas (en cámara) | [Kids World Cup Debate! 🏆⚽️](https://youtube.com/shorts/CdNPjxnrEWU) | BR2 | 21,7 M |
| Preguntas a personas (en cámara) | [Julian Alvarez Picked His Current best Player of nations 😱🔥 #efootball](https://youtube.com/shorts/_Yr9aIc9evA) | ★PES GAMER 20 | 19,5 M |
| Adiviná por gol/jugada (usa clips) | [Yamal & His Skills Are Insane..🤯🔥](https://youtube.com/shorts/csIa38fGT98) | FlashPass | 29,3 M |
| Adiviná por gol/jugada (usa clips) | [Lamine Yamal Skills 💫](https://youtube.com/shorts/XhN2ZfXcegY) | Femyft | 26,0 M |
| Grilla / quién jugó con ambos | [Sürpriz Sonlu Takımlı XOX!  #football #soccer #futbol  #challenge #sho](https://youtube.com/shorts/-BdFZ7HYEes) | AYAYAY Football | 3,4 M |
| Grilla / quién jugó con ambos | [Fenerbahçe ve Beşiktaş'ta Oynamış Aynı Futbolcuyu Söyleyen Elenir! #fo](https://youtube.com/shorts/ptFOCfuYyTM) | AYAYAY Football | 3,3 M |
| Opción múltiple A/B/C | [Which Footballer Has The Best Boots? 👞⚽️](https://youtube.com/shorts/Jo30fOWrAYU) | BR2 | 23,7 M |
| Opción múltiple A/B/C | [Which World Cup Ball is Best? 🎯⚽️](https://youtube.com/shorts/8j0s7mzsLZM) | BR2 | 8,8 M |
| Duelo / ¿quién es mejor? / higher-lower | [Real Madrid or Barcelona?⚽🥳#football #mbappe #lamineyamal](https://youtube.com/shorts/02LL1LzcQQw) | GUGUGAMER  | 97,3 M |
| Duelo / ¿quién es mejor? / higher-lower | [Yamal At 18 Vs Mbappe  😅](https://youtube.com/shorts/4pDpcj1bSmY) | cfcfootball | 52,8 M |
| Emojis | [Emojilerle Futbolcu Challenge #football #futbol #challenge #shortvideo](https://youtube.com/shorts/8PfpA5cR9Ko) | AYAYAY Football | 3,5 M |
| Emojis | [ERRATE den FUSSBALLER NUR an EMOJIS! ⚽ 👀](https://youtube.com/shorts/4idLzYy4zNA) | LarsHolzi | 628 mil |

> La lista completa (un short por fila, con formato, vistas, likes y comentarios) está en `data/processed/videos.csv`. Se puede filtrar por `formato`.
