# 07 · Riesgos y políticas

**Conclusión:** el riesgo grande no es el escudo, es (1) los **clips de transmisión** (Content ID, prohibido), (2) la **música comercial** agregada por fuera de YouTube y (3) que el canal parezca **"contenido inauténtico"**: la misma plantilla con cambios mínimos. Las fotos de jugadores de agencias (Getty, AFP, etc.) son un riesgo medio: los reclamos son manuales, no de Content ID.

> No pude abrir support.google.com desde este entorno: la red lo bloquea. Las reglas salen de la cobertura periodística que cita a YouTube (links abajo). Antes de monetizar, conviene releerlas en el Centro de ayuda.

## Política de "contenido inauténtico" (ex "repetitivo")

- Desde el **15-jul-2025**, YouTube renombró "contenido repetitivo" como **"contenido inauténtico"**. Apunta a lo **producido en masa con diferencias superficiales**: los ejemplos son "historias narradas casi iguales" y "slideshows con la misma narración". YouTube dice que la regla no es nueva; lo que cambia es que ahora la detecta mejor. ([Social Media Today](https://www.socialmediatoday.com/news/youtube-clarifies-monetization-update-inauthentic-repeated-content/752892/), [Search Engine Journal](https://www.searchenginejournal.com/youtube-clarifies-monetization-update-targeting-spam-not-reaction-channels/550755/), [Plagiarism Today](https://www.plagiarismtoday.com/2025/07/08/youtube-targets-inauthentic-content/))
- Usar IA está permitido; lo que no se monetiza es el contenido masivo de bajo esfuerzo.

**Cómo evitarlo con contenido de plantilla (aplicado al pipeline):**

| Riesgo | Qué hacer |
|---|---|
| 3 shorts/día idénticos salvo el jugador | Rotar **al menos 4 formatos** por semana (emojis, carrera, impostor, verdadero/falso…). |
| Misma voz TTS y mismo guion cada día | Variar el gancho, el texto y la frase de cierre. La voz es opcional: muchos top no usan voz (ver reporte 03). |
| Preguntas sin valor | Cada pregunta con dato verificable y fuente (ya está en el diseño). Agregar un dato curioso en la revelación. |
| Canal que parece granja | Comentarios fijados reales, responder comentarios, series con nombre ("Parte 3"). |

## Elemento por elemento

| Elemento | Riesgo | Por qué | Alternativa libre |
|---|---|---|---|
| **Clips de partidos o transmisiones** | 🔴 Prohibido | Content ID compara audio y video automáticamente, aunque duren pocos segundos. Es reclamo o bloqueo seguro; las ligas también envían strikes. | No usar. Animación o gráfico del gol (flechas en una cancha dibujada). |
| **Música comercial** (agregada al editar afuera) | 🔴 Alto | Content ID de audio: el reclamo se lleva la monetización o silencia el short. | [Biblioteca de audio de YouTube](https://studio.youtube.com) (en Studio), música CC0 de [Pixabay Music](https://pixabay.com/music/), o sonidos de la app de Shorts (licenciados para Shorts). |
| **Fotos de jugadores de agencias** (Getty, AFP, Reuters, sitios de clubes) | 🟠 Medio | Tienen copyright. No hay Content ID para fotos, pero la agencia puede pedir que se baje el video (strike). | [Wikimedia Commons](https://commons.wikimedia.org) (CC-BY/CC-BY-SA: atribuir en la descripción), siluetas o ilustraciones propias. |
| **Escudos y logos de clubes** | 🟡 Bajo-medio | Son marca registrada: el riesgo es por **confusión o patrocinio** y no hay Content ID para imágenes. En un quiz de fans el uso es descriptivo. | Usarlos dentro del quiz sí; **nunca** en el nombre, el avatar o el banner del canal, ni dando a entender que el canal es oficial. |
| **Imágenes IA realistas de jugadores** | 🟠 Medio | YouTube exige etiquetar el contenido sintético realista de personas reales, y existe detección de parecido. Además daña la confianza. | Caricaturas o estilizado evidente, o no usarlas. |
| **Voz TTS** (edge-tts) | 🟢 Bajo | No imita a una persona real. | edge-tts gratis; **no** clonar voces de relatores ni de jugadores. |
| **Efectos de sonido** | 🟢 Bajo | — | Biblioteca de audio de YouTube y Pixabay (CC0). |
| **Banderas, texto, emojis y datos** | 🟢 Ninguno | Los datos no tienen copyright. Los emojis Noto de Google son libres (Apache 2.0). | [Noto Emoji](https://github.com/googlefonts/noto-emoji), [Twemoji](https://github.com/jdecked/twemoji) (CC-BY 4.0). |

## Si llega un reclamo

1. **Reclamo de Content ID** (no es strike): en Studio → Contenido → "Restricciones". Si es música o un clip, **reemplazá o recortá el fragmento** desde el editor de Studio. Disputá **solo** si el material es 100 % tuyo o tiene licencia libre (guardá el link de la licencia).
2. **Strike por copyright** (por pedido de baja manual): el video se borra. Hay tres caminos: esperar 90 días con la Escuela de Copyright completa, pedir la retractación al reclamante o presentar una contranotificación si tenés derecho. Con **3 strikes activos se cierra el canal**.
3. Mantené un `licencias.csv` por short: fuente de cada foto o sonido. El pipeline lo genera solo (ver reporte 09).

## Fuentes
- [TechCrunch, 10-ago-2026: nuevos umbrales del YPP](https://techcrunch.com/2026/08/10/youtube-now-requires-creators-to-have-twice-as-many-watch-hours-to-start-earning-money/)
- [Social Media Today: aclaración de "inauthentic content"](https://www.socialmediatoday.com/news/youtube-clarifies-monetization-update-inauthentic-repeated-content/752892/)
- [Search Engine Journal](https://www.searchenginejournal.com/youtube-clarifies-monetization-update-targeting-spam-not-reaction-channels/550755/)
- [Gulf News: vigencia desde el 15-jul-2025](https://gulfnews.com/technology/youtube-updates-monetisation-policies-ai-and-repetitive-content-ban-begins-july-15-1.500192660)
