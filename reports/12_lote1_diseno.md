# 12 · Lote 1: diseño de los 14 videos "2 PLAYERS, 1 FACE"

## ¿Es el mejor formato "no explotado" que tenemos?

**Sí, dentro de lo que pudimos medir.**
- De todas las ideas que revisamos contra los 34.258 shorts de fútbol del dataset, la fusión es la única que junta las dos cosas: **demanda probada** (un video de 6,95 M) y **casi nada de competencia** (11 videos en total, ninguno en inglés sin cara con este formato).
- **Lo que falta:** confirmarlo con búsquedas frescas en YouTube cuando se renueve la cuota, y con las métricas reales de los primeros videos. Hasta que la audiencia responda, es la mejor apuesta y no una certeza.

## Precisión en las caras (lo que pediste)

| Problema | Solución |
|---|---|
| Fotos con poses distintas (nadie adivina) | Para cada jugador se mide el giro de la cabeza con 5 puntos faciales (YuNet). Para cada par se eligen, entre **todas** sus fotos, las dos con **el ángulo más parecido**. Si miran a lados opuestos, **se espeja una** |
| Fotos de otra persona (búsqueda de Wikimedia) | **Reconocimiento facial** (SFace): de las ~8 fotos de cada jugador se queda con la identidad que se repite; se descartan estatuas, murales, chicos y otras personas |
| Fotos borrosas, mano en la cara, perfil | Penalización automática por desenfoque y por pose, más **revisión a ojo** de las 47 fusiones (hojas de control) |
| Jugadores sin foto confiable | **Fuera del lote:** Arda Güler, Gavi, Kaká, Julián Álvarez, Raphinha, Palmer, Dybala, Van Dijk y Modrić. Prefiero no usarlos antes que arriesgar una cara equivocada |

## Psicología aplicada, elemento por elemento

| Elemento | Decisión | Por qué |
|---|---|---|
| Cuadro 0 | Fusión ya visible + gancho escrito "ONLY 1%…" | El primer segundo decide; el 27% de los ganadores sin cara abre con pregunta y el 21% con desafío |
| Ronda 1 | Megaestrellas (Messi+Ronaldo, Salah+Haaland, Kane+Beckham…) | Acierto fácil: dopamina temprana, la persona se queda |
| Curva | EASY → MEDIUM → HARD → **ONLY 1%** | Lo más comentado en sin cara: "acerté todas" (21% de los comentarios responde el quiz) |
| Tiempo para pensar | **4,5 s**, y **5 s** en la final (antes 3 s) | Pediste más tiempo; se compensa con una pista a la mitad |
| **Pista a mitad de tiempo** | "HINT: M•••• + R••••••" con sonido | El que casi lo tenía acierta: más aciertos, más comentarios con puntaje |
| La cara "respira" entre los dos | Oscila mientras pensás | "Lo tengo en la punta de la lengua": curiosidad (34% según Gemini) |
| Último segundo | Latido, borde rojo, sonido que sube | Tensión antes de la recompensa |
| Revelación | Destello, sacudida, golpe de bajo y **la cara se parte en dos** | Ritmo y recompensa visual (el ritmo rápido aparece en el 71% de los ganadores) |
| Voz | Locutor (edge-tts, sin límite) + subtítulos grandes | Se entiende sin sonido; el 37% de los ganadores sin cara usa voz IA |
| Pares con relación | Rivales, compañeros históricos, leyenda + estrella, misma selección | El "¡ah, claro!" al revelar, y tema para comentar |
| Temas con fecha | **Clásico** (25-oct), **Balón de Oro** (26-oct) | Interés del día sin usar clips ni noticias |
| Hinchadas activas | Argentina, Brasil, Inglaterra, Francia, Marruecos, Egipto, Corea, Georgia, Uruguay, EE.UU. | Orgullo nacional: los comentarios más likeados de los sin cara |
| Público que paga más | Kane, Saka, Rice, Foden, Bellingham, Pulisic en varias rondas | EE.UU. y Reino Unido |
| Puntaje "/8" o "/6" | Dos nombres por ronda | Comentarios del tipo "6/8" |
| Cierre | "What's your score? Be honest!" + corte al cuadro 0 | Pide el comentario y el loop suma repeticiones |
| Variedad | 14 temas distintos, preguntas y reacciones variadas | Evitar la política de "contenido inauténtico" (reporte 07) |
| Datos verificables | Nacionalidad, ganadores del Balón de Oro, clubes **históricos** | Nada que pueda estar desactualizado en 2026 |

## Calendario

`produccion/salida/lote1_CALENDARIO.md`: 2 por día a las **10:00 y 23:00 ART**, del domingo 25 al sábado 31 de octubre.

## Qué mirar después
- **Vieron vs. deslizaron** por tema, a las 48 h: duplicar los 2 mejores temas en el lote 2.
- Si la **retención** cae en la ronda 1, el gancho no alcanza (probar fusión más rara en el cuadro 0). Si cae en la 3 o la 4, sobra tiempo para pensar.
