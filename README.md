# Proyecto YouTube: quizzes de fútbol en Shorts

**Empezá por [`reports/00_resumen_ejecutivo.md`](reports/00_resumen_ejecutivo.md).**

## Estructura

```
reports/           reportes 00 a 09 (leer en el celular)
data/raw/          datos crudos de la API (cache: no se vuelve a gastar cuota)
  api/             cada respuesta de YouTube, tal cual
  videos.json      todos los videos con stats
  channels.json    canales
  gemini_formatos.json   formato de cada short (Gemini, por título)
  gemini_shorts/   análisis de Gemini mirando cada short
  comments.json    comentarios de los shorts top
  quota.json       cuota gastada por día
data/processed/    CSV limpios: videos, canales, formatos, anatomia, crecimiento, comentarios…
research/          scripts
```

## Scripts (en orden)

| Script | Qué hace | Cuota de YouTube |
|---|---|---|
| `research/yt_research.py search` | Búsquedas base | 100 por búsqueda |
| `research/yt_research.py formatos` / `propuestos` / `mercados` / `fresco` | Formatos alternativos, por país, muestra sin sesgo | 100 por búsqueda |
| `research/yt_research.py channels` / `canales_quiz` | Stats y últimos 50 de cada canal | ~2 por canal |
| `research/yt_research.py comments N` | Comentarios de N shorts | 1 por short |
| `research/gemini_clasificar.py` | Gemini etiqueta el formato de cada short (texto) | 0 (Gemini gratis) |
| `research/gemini_shorts.py --lista X.json` | Gemini **mira** cada short y saca su anatomía | 0 |
| `research/analyze.py` | Arma todos los CSV | 0 |
| `research/crecimiento.py` | Curvas de crecimiento | 0 |
| `research/realismo.py` | Tasa de éxito sin sesgo (muestra por fecha) | 0 |
| `research/reporte_*.py` | Regenera los reportes 01, 02 y 03 desde los CSV | 0 |

**Claves:** se pasan como variables de entorno y **nunca** se guardan en el repo:
```
export YOUTUBE_API_KEY=...   GEMINI_API_KEY=...   QUOTA_CAP=9000
```
- Todo es **reanudable**: si se corta, se vuelve a correr y sigue donde estaba.
- La cuota se cuenta por día del Pacífico (así resetea YouTube).
- El plan gratis de Gemini tiene un tope diario por modelo. Si da 429, se sigue al día siguiente o se cambia de modelo con `GEMINI_MODELS=gemini-3.1-flash-lite,...`.

## Sobre descargar videos

- Desde la nube de Claude, `googlevideo.com` está bloqueado por la política de red.
- Desde GitHub Actions (`.github/workflows/medir_videos.yml` + `research/medir_video.py`), YouTube responde "Sign in to confirm you're not a bot". Solo andaría pasando cookies de una cuenta de Google, y eso arriesga esa cuenta, así que **no lo recomiendo**. Además va contra los Términos de YouTube.
- **El camino que funciona es Gemini mirando el link** (`gemini_shorts.py`).

## Producción

Pendiente: se construye cuando elijas formatos e idioma (ver reporte 09).
