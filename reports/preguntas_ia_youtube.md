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
