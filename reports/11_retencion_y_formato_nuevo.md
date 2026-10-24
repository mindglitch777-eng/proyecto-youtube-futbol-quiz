# 11 · Retención extrema y formato nuevo ("2 PLAYERS, 1 FACE")

## Tarea 1: cómo hacer los videos mucho más enganchables

**De dónde sale:** Gemini, al explicar por qué funcionan los 125 shorts que miró (`data/processed/anatomia.csv`, columna `por_que_funciona`), menciona:

| Motivo | % de los videos |
|---|---|
| Ritmo rápido / cortes | **71%** |
| Desafío / gamificación | 43% |
| Curiosidad / misterio / tensión | 34% |
| Humor / absurdo | 27% |
| Figuras famosas | 18% |
| Música viral | 17% |

**Qué incorporamos al motor de video** (`produccion/render_fusion.py`):

| Técnica | Cómo | Para qué |
|---|---|---|
| **Voz de locutor** (Gemini TTS, gratis) | Todo el guion en una sola locución, cortada por silencios y verificada con una transcripción | Ritmo y energía; el 37% de los ganadores sin cara usa voz IA |
| Gancho hablado y escrito en el **cuadro 0** | "Only one percent can name BOTH players!" | El 27% de los ganadores sin cara abre con pregunta y el 21% con desafío |
| **Subtítulos palabra por palabra** | Texto grande sincronizado con la voz | Se entiende sin sonido |
| **Cara que "respira"** entre los dos jugadores | El morph oscila mientras pensás | Sensación de "casi lo tengo": curiosidad |
| **Latido + crescendo** el último segundo | Zoom que late, borde rojo, ruido que sube | Tensión antes de la revelación |
| **Destello + sacudida + golpe de bajo** al revelar | 4 cuadros de flash suave, sacudida que se apaga | Corte de patrón: el "ding" del cerebro |
| **Separación de la cara** en dos | La fusión se parte y cada mitad vuelve a ser su jugador | Satisfacción visual: la recompensa |
| **Puntaje /8** | Dos nombres por ronda | Acierto parcial que la gente comenta ("6/8"); 21% de comentarios responde el quiz |
| Dificultad creciente + **"ONLY 1%"** al final | Ronda 4 con jugadores menos obvios | Quedarse hasta el final y presumir |
| **Loop** | Corte seco del cierre al cuadro 0 | Repeticiones |
| Beat propio que **baja cuando habla la voz** | Ducking automático | Voz clara; sin riesgo de copyright |

**Honestidad:** la voz, los destellos y el latido **no están medidos con nuestros datos**. Salen de lo que hacen los ganadores y de principios de atención (curiosidad, tensión, recompensa). Se validan con la prueba A/B del plan: misma ronda con y sin voz, mirando "vieron vs. deslizaron" en Studio.

## Tarea 2: formato que casi nadie explotó

**Búsqueda en los 34.258 shorts de fútbol que tenemos** (títulos con cada idea):

| Idea | Shorts encontrados | Lectura |
|---|---|---|
| **Fusión de 2 jugadores en 1 cara** | **11** (8 en inglés) | Uno tiene **6,95 M** (en español, con personas en cámara). **Hay demanda probada y casi nadie lo hace en inglés sin cara** |
| Encontrá a los dos | 3 | Personas en cámara |
| Por la voz / el sonido | 4 | Casi vacío, pero difícil sin clips |
| Juego de memoria | 134 | Mayormente logos de cadenas, no fútbol |
| Por los ojos / el pelo | 41 | Existe, rinde poco (mediana 10 mil) |
| Velocidad / "más rápido" | 76 | Con personas en cámara |

**Formato elegido: "2 PLAYERS, 1 FACE".** Dos jugadores fusionados en una sola cara con morphing (68 puntos faciales + triangulación). Hay que **nombrar a los dos**.

**Por qué debería pegar:**
1. **Junta lo que ya funciona:** caras de jugadores famosos (Find the real, 1,17× y el más viral), desafío, dificultad creciente y "only 1%".
2. **Lo nuevo:** la imagen es **extraña pero familiar** (el cerebro reconoce rasgos de alguien conocido y no lo puede ubicar). Eso genera curiosidad y ganas de repetir el video.
3. **Dos respuestas por ronda:** el acierto parcial empuja a comentar ("saqué a Messi pero no al otro").
4. **Rivalidades dentro de la misma cara** (Messi + Ronaldo, Mbappé + Haaland): el tema que más comentarios genera (reporte 05).
5. **Ronda 4 con Pulisic + Saka:** pega en el público de EE.UU. y Reino Unido, el que más paga por vista.

**Primer video:** `produccion/salida/fusion_01/` (24,3 s). Guion en `produccion/guiones/fusion_01.json`.

**Validar mañana** (cuota nueva): 4 búsquedas en inglés ("face fusion football", "2 players 1 face", "guess the fused players", "merged footballers") para confirmar con datos frescos que sigue sin competencia.

## Cómo seguir
- Alternar: **fusión** (formato nuevo) y **find the real** (el más viral), en la misma franja horaria, durante 2 semanas.
- Métrica que decide: **"vieron vs. deslizaron"** y **retención media** a las 48 h.
- Si la fusión gana: variantes como fusión de 3, "fusión de compañeros de equipo", leyenda + estrella actual, o la fusión que "se deshace" de a poco.
