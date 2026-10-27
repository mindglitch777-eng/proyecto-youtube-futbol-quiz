# 16 · Simulaciones, calidad y cadencia: qué cambiamos después de los primeros 3 shorts

**Datos:**
- 23 búsquedas nuevas de simulaciones (API, 27-oct).
- Historial de 17 canales de simulación y predicción (`data/raw/competencia_sim/`).
- Gemini miró **39 shorts**: simulaciones y los sin cara de fútbol más vistos de los últimos 75 días (`data/raw/gemini_virales/`).
- Cadencia medida en 83 canales con historial (`data/raw/channel_history.json`).

## 1. El círculo con arcos (tu idea): pega solo como TORNEO bien hecho

| Canal | Qué hace | Resultado |
|---|---|---|
| Neon Arcade | Partidos sueltos en serie (3.844 videos) | Mediana de **1 mil** |
| Pixel Pitch / Ball Fight Simulation / Physics Predicts | Un partido por video, predicción | Mediana de **1 mil** |
| **Footrix** | **Cuadro de eliminación** (cuartos, semis, final), arena circular, 3D pulido (9/10), 59 s, evento grande | **3,9 M** (Balón de Oro), **2,6 M** (Nations League) |

→ Hicimos la **CIRCLE CUP** (`produccion/render_copa.py`):
- 8 competidores en cuadro, cada partido con **dos arcos en un anillo que gira** y una pelota con física real.
- Cuartos al primer gol, semis a 2 y final a 3.
- **Cada rebote suena a nota** y la pelota acelera rebote a rebote.
- Césped, red, estela, temblor en el gol, "MATCH POINT" y gol final en cámara lenta.

## 2. Lo que explota en simulaciones (no fútbol) y copiamos
- **visualizing magic** (548 mil subs, mediana 455 mil) y **bouncyball** (294 mil subs, mediana 318 mil).
- Hacen tres cosas: sonido sincronizado a cada choque, algo que **escala** (gravedad, tamaño, velocidad) y loop.

## 3. Lo más visto sin cara en fútbol
- **Parodias 3D/IA de jugadores reales** (GUGUGAMER: 474 M, 203 M, 97 M). No lo hacemos:
  - no tenemos generador de video;
  - y la semejanza realista de personas reales tiene reglas de etiquetado y riesgo de suplantación.
- **FOOTIEHAWK** (9,9 M subs) hace eliminación de jugadores hasta **Messi vs Ronaldo** y "LIKE = Ronaldo / SUBSCRIBE = Messi". Lo usamos en el cierre de la GOAT Cup.

## 4. Carreras v4 (tu crítica: cortas y poco interesantes)
- **13 tramos** en vez de 6–7: la carrera dura 27–31 s y el video 35–39 s (antes 21–24 s).
- **Obstáculos nuevos:**
  - **portales** que te mandan 700 px para atrás ("SENT BACK!": remontadas);
  - **trampolines**;
  - **péndulos**.
- **Corona** para el líder y **estela** de color detrás de cada bola.

## 5. ¿3 shorts por día? Los datos dicen que no (todavía)

| Ritmo del canal | Mediana de vistas por video | % de videos con 1 M+ |
|---|---|---|
| ~1 por día | **95 mil** | **15,1%** |
| ~2 por día | 35 mil | 4,4% |
| ~3 por día | 60 mil | 3,3% |

- Dentro de un mismo canal, los días con 3 videos rinden un poco menos por video: 0,93 veces la mediana del canal, contra 1,02 los días con uno solo.
- Es correlación, no causa: los que suben mucho suelen tener menos calidad.
- **Recomendación:** quedarse en **2 por día** y subir la calidad. Pasar a 3 solo cuando un formato pegue y haya que clonarlo rápido.
