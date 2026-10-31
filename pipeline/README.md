# Fábrica Futbol Edition · cómo funciona y cómo se configura

## Qué hace sola
| Cuándo | Workflow | Qué hace |
|---|---|---|
| Domingo 09:00 (ARG) | `FÁBRICA semanal` | 1 radar de virales → 2 análisis con Gemini (+ grabaciones cuadro por cuadro) → 3 rendimiento de nuestro canal → 4 plan de la semana → 5 producción de los videos → 6 control de calidad → Release `semana-<fecha>` con los videos |
| Todos los días 07:30 (ARG) | `PUBLICAR diario` | Sube por la API de YouTube los 4 videos del día, programados a su hora, y mide el canal |
| En cada corrida | (los dos) | Actualiza el tablero en GitHub Pages |

Para lanzar la fábrica a mano: pestaña **Actions → FÁBRICA semanal → Run workflow**, o editá `pipeline/lanzar.txt`.

## Configuración (una sola vez, ~20 minutos)

### 1. Rama principal
GitHub → **Settings → General → Default branch** → elegí `ccr-a2c8fa85-10k0an`.
(Los horarios automáticos de GitHub solo corren en la rama principal.)

### 2. Tablero
**Settings → Pages → Build and deployment → Source: GitHub Actions.**
El tablero queda en `https://mindglitch777-eng.github.io/proyecto-youtube-futbol-quiz/`.

### 3. Permiso para subir a tu canal (OAuth)
1. [Google Cloud Console](https://console.cloud.google.com/) → tu proyecto → **APIs y servicios → Biblioteca**: activá **YouTube Data API v3** y **YouTube Analytics API**.
2. **Pantalla de consentimiento de OAuth**: tipo *Externo*; agregá tu mail como usuario de prueba y después tocá **Publicar app** (pasarla a *En producción*). Si queda en *Prueba*, el permiso vence cada 7 días.
3. **Credenciales → Crear credenciales → ID de cliente de OAuth** → tipo **Aplicación web** → en *URI de redireccionamiento autorizados* poné `https://developers.google.com/oauthplayground`. Guardá el **ID de cliente** y el **secreto**.
4. Entrá a [OAuth Playground](https://developers.google.com/oauthplayground) → engranaje ⚙ → **Use your own OAuth credentials** → pegá ID y secreto.
5. En *Input your own scopes* pegá (separados por espacio):
   `https://www.googleapis.com/auth/youtube.upload https://www.googleapis.com/auth/youtube.readonly https://www.googleapis.com/auth/yt-analytics.readonly`
   → **Authorize APIs** → entrá con la cuenta del canal → **Exchange authorization code for tokens** → copiá el **Refresh token**.

### 4. Secretos en GitHub
**Settings → Secrets and variables → Actions → New repository secret**, uno por uno:

| Nombre | Valor |
|---|---|
| `YOUTUBE_API_KEY` | tu clave de la API de YouTube |
| `GEMINI_API_KEY` | tu clave de Gemini |
| `YT_CLIENT_ID` | ID de cliente OAuth (paso 3) |
| `YT_CLIENT_SECRET` | secreto del cliente OAuth |
| `YT_REFRESH_TOKEN` | refresh token (paso 3.5) |

Los secretos no se ven en el código ni en los registros. **Nunca los pegues en archivos del repo**: el repo es público.

## Lo que hacés vos cada semana
- (Opcional) Grabar con el celular los virales que marca el tablero y subirlos a `pipeline/grabaciones/` desde la app de GitHub (**Add file → Upload files**). El domingo se analizan cuadro por cuadro.
- Fijar el comentario de cada video (la API de YouTube no permite fijar) y responder los primeros comentarios.

## Límites a tener en cuenta
- La API da 10.000 unidades por día; cada subida gasta 1.600 → 4 por día entran sobrado.
- YouTube tiene un límite diario de subidas por canal (también por API). Si se alcanza, la publicación lo anota y sigue al día siguiente.
- La fábrica sabe hacer 4 formatos (STOP, FIND, ¿CUÁL LOOK?, CATCH THE RIGHT HEAD). Los formatos nuevos que detecta el análisis aparecen en el tablero como candidatos para construir.
