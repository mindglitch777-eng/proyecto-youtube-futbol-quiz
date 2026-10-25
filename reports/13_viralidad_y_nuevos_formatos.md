# 13 · Cómo se hacen virales los shorts y qué formatos agregar

Datos del 25-oct-2026, con ~5.400 unidades de cuota:
- 21.897 shorts recientes medidos dos veces, con 13 h de diferencia (`data/raw/snapshots/`, `data/processed/velocidad.csv`);
- 1.714 shorts de otros nichos con su mecánica etiquetada;
- muestra al azar de 3.996 shorts de fútbol con la misma taxonomía (`data/processed/oportunidad_mecanicas.csv`);
- 14 búsquedas de competencia en fútbol;
- historial completo de FULYON SHORTS;
- 16 evoluciones analizadas por Gemini mirando el video.

## 1. Cuándo se decide si un video pega

| Edad del video | % de todas las vistas por hora | Vistas por hora del video típico |
|---|---|---|
| < 1 día | 15% | 940 |
| 1–2 días | 16% | 415 |
| 2–3 días | 11% | 141 |
| 3–7 días | 21% | 61 |
| 1–4 semanas | 23% | 6–26 |
| 1–3 meses | 15% | 0–1 |

- **El destino de un short se decide en 72 h.** Los que despegan tarde ("late bloomers": más de 7 días y 3 veces su promedio) son **9 de 18.138 (0,05%)**.
- **Implicancia:** cada video se juzga a las 48–72 h; no tiene sentido esperar que "levante". Lo que suma es **publicar seguido** (más intentos).

## 2. Cómo crece un canal que pega: el caso FULYON SHORTS

FULYON SHORTS (creado en feb-2026, 92 videos, 121 M de vistas, 50 mil subs, **1 video por día** desde el 5 de junio):
1. **Video 3:** "Cristiano Ronaldo Evolution (Day 1 → Day 999999)" hizo **13,5 M**.
2. **Clonó la fórmula como serie diaria** ("WORLD CUP EVOLUTION | DAY 9, 10, 11…") durante el Mundial: 4–16 M por episodio.
3. Cuando se agotó (agosto–septiembre, 30–900 mil), **cambió**: duelos de habilidad (5,9 M), "Level 1 → 100".
4. Desde el 16 de octubre: **"FIND X Y Z"** (16 s) con títulos casi idénticos, que dio 9,7 M y 2,8 M. **Hoy, "FIND YAMAL RONALDO NEYMAR" crece a 247.000 vistas por hora** (3,2 M en 15 h): es el short de fútbol más rápido de toda la muestra.

**Reglas que salen de acá:**
- Cuando algo pega (10 veces la mediana del canal en 48 h), **se clona 3 a 5 veces** con el mismo formato y casi el mismo título.
- **Atarlo a un evento en vivo** multiplica (Mundial, Clásico, Balón de Oro).
- **Cambiar rápido** cuando decae.
- Es muy aleatorio: el mismo título hizo 13,5 M un día y 0,9 M al siguiente. Por eso importa el volumen.

## 3. Qué mecánicas faltan en fútbol (oferta vs. demanda)

"Rinde" = vistas ÷ mediana del canal, dentro de los shorts de fútbol que usan esa mecánica.

| Mecánica | % de shorts de fútbol que la usan | Rinde en fútbol | Mediana en otros nichos |
|---|---|---|---|
| **Evolución / antes y después** | **0,45%** | **2,34×** | **9,5 M** (89% sin cara) |
| Verdadero o falso | 1,6% | 2,03× | 20,9 M (casi todo con cara) |
| Emojis | 0,48% | 2,32× | 9,0 M |
| Adivinar la edad | 0,28% | 0,62× | 6,1 M |
| Por voz o sonido | 1,05% | 1,00× | 6,1 M (en fútbol usa audio con derechos) |
| Encontrar el real | 3,4% | 1,08× | 8,1 M (y hoy explota en fútbol) |
| Fusión | 0,38% | 0,97× | **0,05 M** |
| Elegir uno | 7,5% | 1,19× | 6,6 M (en fútbol ya está lleno) |

**Competencia en búsquedas de fútbol (último año):**
- **Evolución pasiva** ("Then vs Now", camisetas, botines): ~46 de 50 resultados la usan, **mediana 3–4 M, 44 de 46 con 1 M+**. Hay mucha demanda y algo de oferta.
- **Evolución interactiva** ("guess the footballer evolution"): 30 videos, **mediana 2 mil**. **Prácticamente nadie la hace bien.**
- **Fusión:** ~45 videos en 4 búsquedas, mediana 6–81 mil, aciertos aislados (5,7 M y 6,95 M). **No es un océano vacío.** Hay competencia chica y pegada irregular. Sigue valiendo como prueba, pero fuera del fútbol rinde poco: es la señal más débil de las tres.

## 4. Anatomía de las evoluciones que pegan (Gemini)

- **20–37 s**, fotos (no hace falta video) con **el año en pantalla** ("1978 / 2026"), **música nostálgica de tendencia**, sin voz, **loop** al inicio, 7–15 cambios de imagen.
- Funcionan por **nostalgia** ("2002 WORLD CUP WINNERS THEN VS NOW", 11,1 M) y por la curiosidad del cambio físico.
- Lo que falta, la **versión juego**: "¿quién es?" mientras la cara joven se transforma en la actual.

## 5. Recomendación

1. **Esta semana:** de los 2 por día, **1 fusión (formato nuevo, a prueba) + 1 "FIND THE REAL" (la ola viva que hoy explota)**.
   - Los títulos al estilo de FULYON: "FIND YAMAL RONALDO NEYMAR".
   - Así comparamos cara a cara y aprovechamos la tendencia mientras dura.
2. **Próximo formato a construir: "WHO IS THIS NOW?" (evolution quiz).** Una foto de joven (por ejemplo, el Mundial 2002 o 2006) se transforma con morph en la cara actual del mismo jugador. Hay que adivinar quién es antes de que termine.
   - Junta la mecánica más fuerte con poca oferta (evolución: 2,34× en fútbol, 9,5 M afuera), la nostalgia y la interacción de comentar "lo saqué en 2006".
   - Tenemos la tecnología: alineación de caras, verificación de identidad y morph.
   - Falta bajar fotos con fecha de Wikimedia, que se hace con el workflow.
3. **Regla de clonado:** si un video pasa 10 veces la mediana del canal a las 48 h, se hacen 3–5 versiones con el mismo título y formato en los días siguientes.
4. **Idea para más adelante:** el "juego runner" con caras de jugadores, que FULYON usó para varios episodios de 4–16 M. Es más complejo de producir.

## 6. El cruce: menos explotado Y más fuerte, solo sin cara

Recalculé la tabla **solo con videos sin cara**, que es lo que podemos hacer nosotros (`data/processed/oportunidad_sin_cara.csv`).
- **Puntaje** = mediana de vistas en otros nichos (en millones) × cuánto rinde en fútbol ÷ (% de shorts de fútbol que la usan + 0,3).
- Sube cuando la mecánica pega afuera, rinde en fútbol y casi nadie la hace.

| Mecánica (sin cara) | % de fútbol | Rinde | Mediana otros nichos | % con 1 M+ (otros nichos) | Puntaje |
|---|---|---|---|---|---|
| **Evolución** | **0,71%** | **2,33×** | **9,2 M** | **100%** (44/44) | **21,1** |
| Verdadero/falso | 1,18% | 0,99× | 10,7 M (solo 6 videos) | 83% | 7,2 |
| Emojis | 0,67% | 2,32× | 2,4 M | 74% | 5,6 |
| Diferencias | 0,27% | 2,09× | 1,1 M | 55% | 4,0 |
| Encontrar el real | 4,16% | 1,08× | 5,9 M | 68% | 1,4 |
| Fusión | 0,47% | 1,17× | 0,05 M | 4% | 0,07 |

**La evolución gana por lejos: el puntaje es 3 veces el del segundo.**

**Búsquedas de validación de hoy** (12 consultas, 1.200 unidades):
- **"Adiviná al futbolista de bebé"** es el juego de fútbol más grande del año: 99 M, 88 M, 77 M, KSI 61 M, IShowSpeed 64 M.
  - **Pero todo eso es con cara y con famosos** (Lamine Yamal, Haaland, Kroos jugando): mediana de **20 M con cara** contra **33 mil sin cara** (22 videos).
  - Las fotos de infancia, además, tienen dueño.
  - **Conclusión: no lo copiamos.**
- **Evolución pasiva en fútbol:** 41 de 43 resultados con 1 M+.
  - "Real Madrid Now vs 2017 Prime" hizo 47,7 M.
  - "Pau Cubarsí Age Evolution (2008–2026)" hizo 2,4 M.
- **Evolución como juego** ("Then vs Now, can you guess who?"): un solo intento, de 37 mil. **No es que no funcione: nadie lo probó en serio.**
- **Emojis en fútbol:** mediana de 23 mil y un solo caso de 3,5 M (turco). Es secundario.

## 7. Formato propuesto: "WHO IS HE? · AGE EVOLUTION"

Junta la mecánica sin cara más fuerte (evolución) con la nuestra (adivinar):

1. **0 s:** cuadro 0 con la foto más vieja del jugador, el año gigante ("2005") y el texto "GUESS HIM BEFORE 2026".
2. **0–20 s:** el año avanza y la cara envejece con morph, foto tras foto alineadas por los ojos (ya tenemos la tecnología). Los equipos y las banderas aparecen como pistas en los últimos años.
3. **Revelación:** nombre, cara actual y "WHAT YEAR DID YOU GET IT?". Esa pregunta pide un comentario con número, como el puntaje.
4. **Loop** de vuelta a la foto vieja.

**Por qué tiene la mayor probabilidad:**
- Aunque no adivines, mirás el cambio: **la satisfacción de la evolución pasiva**, que es la que da 1 M+ casi siempre.
- El que juega se queda hasta el final: **retención**.
- La competencia directa es prácticamente cero.

**Qué falta:** de 6 a 10 fotos con fecha por jugador (Wikimedia, desde la fecha de la foto). Se baja con el mismo workflow de GitHub.
