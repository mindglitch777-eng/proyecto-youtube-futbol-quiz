# 15 · Cómo lo hace la competencia que pega y qué copiamos o mejoramos

**Datos:**
- Historial de 12 canales de carreras y evoluciones: sus últimos 50 videos (`data/raw/competencia/`).
- Gemini miró **71 shorts**: los 4 mejores y los 2 peores de cada canal (`data/raw/gemini_competencia/`).
- Pregunta de fondo: ¿qué separa un hit de un fracaso **dentro del mismo canal**?

## 1. Carreras

| Canal | Desde | Subs | Lo que hace |
|---|---|---|---|
| **DriveLabs** | may-2026 | **1,13 M** | 3 jugadores, **Ronaldo siempre**: "Mbappé, Neymar or Ronaldo? One Trophy, Three Superstars!". Hits de 20 M, 5 M y 5 M |
| Footypoints | nov-2025 | 139 mil | "Real Madrid vs Barcelona / Who Wins?" **atado al partido real**: 38,8 M |
| Sphere Stars | abr-2026 | 11 mil | "Who Will Win the World Cup 2026? **Predictions** Maze": 5,9 M y 3,6 M |
| Fire Rankings | dic-2025 | 132 mil | Carreras de canicas; hoy **decayó** (mediana de 94 mil) por repetir sin evento ni ganador fuerte |

**Lo que separa los hits de los fracasos (Gemini):**
- **Gana el popular:** 19 de 22 hits (86%) contra 4 de 11 fracasos (36%). Ganan Ronaldo, Messi, Argentina o el favorito del momento.
- **Ronaldo en el título:** en DriveLabs, los videos con Ronaldo tienen una mediana de **393 mil**; sin él, **3 mil**.
- **Predicción de un evento real:** "Who wins the World Cup / El Clásico?" es lo que más explotó.
- **Sin voz** (2 de 22) y con **música de tendencia** (remix acelerado, cumbia o funk brasileño); duran ~22 s y casi todos hacen **loop**.
- **Los fracasos:** temas sin debate ("Christmas gift"), cortes sin ganador claro y títulos sin estrella.

**Qué cambiamos:**
1. **El ganador lo elegimos nosotros**, el del debate del día:
   - la física es real: entre cientos de simulaciones nos quedamos con una donde gana él y el final es ajustado;
   - por eso la descripción ya no dice "no edits".
2. **2 tríos con Ronaldo** con la fórmula de títulos de DriveLabs (`carrera_08`, `carrera_09`).
3. **"PREDICTION"** en el Balón de Oro y carreras atadas a eventos.
4. **Dos versiones de audio:**
   - `short.mp4`, con relator: nuestro toque, porque la competencia no lo tiene;
   - `short_sin_voz.mp4`, para sumar un sonido en tendencia desde el editor de Shorts, como hacen ellos.
   - Las alternamos para medir cuál rinde más.

## 2. Evolución y "then vs now"

| Canal | Lo que pega |
|---|---|
| Kickoff to Immortality | **Evolución de objetos**: botines del Mundial (26 M), camisetas de Argentina (19,7 M), pelotas (10 M) |
| Frox / Icon Stories | **Duplas con vínculo**: Jude y Jobe Bellingham (2,5 M), Pelé y Neymar (2,3 M), Ronaldo y su hija, Haaland y su papá |
| Unstoppable Football (2,1 M subs) | "Neymar Evolution" (6,6 M), "Football Then vs Now" (4 M) |
| FootyPivot | "2002 WORLD CUP WINNERS THEN VS NOW": **11,1 M**. El resto de su serie: 0,2 M |

**Patrón:**
- **Edad y año en pantalla**, empezando de chico.
- Música nostálgica o acelerada en tendencia y **sin voz**.
- 20–35 s, con loop.
- **Nostalgia de equipos campeones legendarios.**

**Qué hicimos (tu idea):**
- **AGE EVOLUTION pasivo**, sin pregunta forzada:
  - arranca con la foto **más vieja** que existe (Messi 2005, 18 años);
  - el nombre queda oculto hasta el final ("WAIT FOR IT…");
  - la bandera aparece recién al 72%;
  - cierra con "WHEN DID YOU RECOGNIZE HIM?".
- **Nuestro toque:** las caras se **transforman con morph alineado** (como el efecto "hipnótico" que Gemini destacó en los hits con IA), no con cortes. Y sin usar fotos de infancia con dueño.
- **PRIME vs NOW** con fotos libres, no clips de TV: cada jugador se transforma de su foto de entonces a la de hoy.

**Límite honesto:**
- Commons tiene pocas fotos de frente de algunos jugadores en sus primeros años. Ronaldo solo sirve desde 2014, y Ronaldinho y Kaká no tienen.
- Por eso las evoluciones son de quienes tienen fotos viejas buenas: Messi, Neymar, Beckham, Salah, Zlatan, Modrić y Kane.

## 3. Pendiente para la semana 2 (según los números)
- **Duplas** (Messi y Neymar, Ronaldo y Messi): dos paneles evolucionando a la vez.
- **Evolución de camisetas o botines** dibujados por nosotros (colores y diseño, sin escudos): la evolución de objetos es lo que más pega (26 M).
- **Carreras de predicción** para cada partido grande de la semana (Champions, clásicos).
