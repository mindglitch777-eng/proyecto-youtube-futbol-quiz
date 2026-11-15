# Reparto de tareas: permiso de Analytics vs. IA de YouTube Studio

Las dos herramientas nos alimentan. Cada una hace lo que mejor hace y no se pisan.

## 1 · Permiso de Analytics (automático, todos los días, sin nadie)
Script: `pipeline/e3b_analytics.py` (corre en cada publicación). Guarda `pipeline/datos/analytics.json` y la historia diaria.

| Qué mide | Para qué lo usamos |
|---|---|
| Por video: vistas, % promedio visto, duración media, likes, comentarios, compartidos, suscriptores ganados | Decidir qué formato repetir y cuál podar, sin esperar días a las vistas |
| Curva de retención de los últimos 12 videos | Ver en qué segundo se va la gente y si el loop se repite (>100%) |
| Fuentes de tráfico, países, edades, dispositivos, suscriptos vs. no | Horarios, idioma, temas y jugadores según quién nos mira |
| Historia diaria por formato | Comparar antes / después de cada cambio (gancho, superestrella, pitazo...) |

Si un día el permiso falla, la etapa queda "pendiente" en el tablero y la vigía lo ve.

## 2 · IA de YouTube Studio (vos le preguntás; para lo que solo ella sabe)
Una pregunta por mensaje, copiada tal cual. Pasá captura de cada respuesta.

**El dato que la API no da**
1. "Hacé una tabla con todos mis videos: título, porcentaje que eligió ver (visto vs. descartado) y vistas. Ordenala de mayor a menor porcentaje que eligió ver."
2. "Comparame los 3 videos con mayor porcentaje que eligió ver contra los 3 con menor: ¿qué tienen distinto en el primer segundo, la imagen de inicio y el título?"

**Por qué explota uno y otro no**
3. "Comparame mi video con más vistas contra mi STOP CHALLENGE con menos vistas: ¿qué pasó distinto en la primera hora y por qué YouTube empujó a uno y no al otro?"
4. "¿Qué tienen en común mis videos de más de 20.000 vistas? Decime 5 patrones concretos (título, duración, primer segundo, sonido, hashtags)."

**Ideas y tendencias (lo que explota hoy, con lo que ya nos funciona)**
5. "¿Qué formatos de Shorts de fútbol interactivos (retos para pausar, encontrar, adivinar) están creciendo más rápido esta semana en canales chicos? Dame 10 ideas concretas parecidas a mi STOP CHALLENGE que mi audiencia también vea."
6. "¿Qué jugadores, partidos y memes de fútbol están en tendencia esta semana entre mi público? Dame 10 títulos de Shorts listos para usar."
7. "¿Qué sonidos o canciones en tendencia usan los Shorts de fútbol que más crecieron esta semana?"
8. "¿Qué buscan los espectadores de mi canal en YouTube que yo todavía no hice? Dame 10 temas."

**Cada cuánto:** las 8 ahora; después, 5 a 8 cada domingo antes de la fábrica (tendencias de la semana).

## Si el permiso de Analytics no está activo
1. Google Cloud (el mismo proyecto del cliente OAuth) → APIs y servicios → Biblioteca → **YouTube Analytics API** → Habilitar.
2. OAuth Playground → ⚙ → Use your own OAuth credentials → pegá ID y secreto.
3. *Input your own scopes* (separados por espacio):
   `https://www.googleapis.com/auth/youtube.upload https://www.googleapis.com/auth/youtube.readonly https://www.googleapis.com/auth/yt-analytics.readonly`
4. Authorize → cuenta del canal → Exchange authorization code for tokens → copiá el **refresh token**.
5. GitHub → Settings → Secrets and variables → Actions → **YT_REFRESH_TOKEN** → Update → pegalo. (Nunca en el chat: el repo es público.)

## 15/11 · Preguntas de ENGAGEMENT (pedido del CEO) — para la IA de YouTube Studio
Lo que funciona:
1. Comparando mis Shorts que superaron las 15.000 visualizaciones con los que no llegaron a 3.000 en los últimos 28 días, ¿en qué se diferencian el porcentaje de vistos vs. deslizados, la retención y los primeros 3 segundos?
2. En mis Shorts con más vistas, ¿en qué segundo exacto se va la mayoría de la gente, y en qué segundo hay más repeticiones?
3. ¿Qué Shorts míos generaron más suscriptores por cada 1.000 vistas, y qué tienen en común?
Engagement:
4. ¿Qué tipo de comentario fijado o pregunta al final del video genera más comentarios en canales de desafíos de pausa de fútbol como el mío?
5. Mis espectadores, ¿comentan más cuando el video les pide elegir un jugador, adivinar un número o decir en qué intento lo lograron?
6. ¿Qué duración de Short (5-7 s, 8-12 s o más de 15 s) da mejor retención y más repeticiones en mi canal y en los desafíos de pausa en general?
Formatos nuevos:
7. En los desafíos de pausa de fútbol que se volvieron virales este mes, ¿qué elementos se repiten en los primeros 2 segundos: texto, sonido, cara del jugador, cuenta regresiva?
8. ¿Qué jugadores y qué leyendas generan más interés entre mis espectadores en este momento, y hay algún enfrentamiento cara a cara (por ejemplo Messi vs Ronaldo) que estén buscando?
Publicación:
9. Con mi público, ¿conviene publicar 6 u 8 Shorts por día? ¿Cuánto tiempo conviene dejar entre un Short y otro para que no compitan entre sí?
10. ¿Hay algo en mis títulos, hashtags o descripciones que esté frenando la distribución en el feed de Shorts?
Con las respuestas: guía de engagement para el Ingeniero (gancho, duración, pregunta final y comentario fijado de cada formato nuevo).
