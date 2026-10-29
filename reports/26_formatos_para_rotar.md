# 26 · Formatos para rotar: los que explotan rápido en canales nuevos y cuáles podemos hacer

Fecha: 29-oct-2026. Objetivo: tener 4-6 formatos probados para rotar y no caer en "plantilla" (política de contenido inauténtico) ni pensar un formato nuevo cada día.

## Cómo se hizo
1. 28 búsquedas de formatos de fútbol (últimos 90 días, ordenadas por vistas) con la API de YouTube.
2. Se quedaron los **144 canales creados en 2026** con algún short de 500 K+. De cada uno se bajó todo el historial: en qué video y a los cuántos días llegó el primer hit, cuántos hits tiene, cadencia, duración.
3. Gemini miró cuadro por cuadro **28 shorts** representativos: tipo de imagen, gancho de 0 a 3 s, sonido, estructura y si se puede hacer sin material ajeno.
4. Se hicieron **maquetas** de los formatos nuevos con nuestras herramientas (`reports/maquetas_26/`, script `research/maquetas_formatos.py`).

Datos: `data/raw/formatos_nuevos/` (canales, búsquedas, análisis de Gemini).

## Lo que tienen en común los que explotan rápido
1. **Las mismas caras famosas en el cuadro 0:** Ronaldo, Messi, Neymar, Yamal, Haaland, Mbappé.
2. **Un juego con resultado pendiente:** buscar, elegir, frenar en 99 %, salvar, eliminar. El que mira juega.
3. **Opciones numeradas a la izquierda (1, 2, 3, 4)** o porcentajes. El comentario es un número, y comentar cuesta cero.
4. **Marcador en pantalla:** corazones, %, ✓/✗, con sonido de acierto y de fallo.
5. **Música de tendencia:** phonk, funk brasileño o dembow a ~125-130 BPM, con cortes al ritmo y pocos efectos.
6. **Cortos y en loop:** la mediana va de 6 a 20 s (Eddy Kicks: 6 s). Sin cierre.
7. **Cadencia de ~1 por día**, siempre el mismo formato. El primer hit llega entre el video 1 y el 31.

## Los formatos

### A. Los podemos hacer ya, solo con código + fotos libres + caras de 68 puntos

| Formato | Ejemplo | Primer hit | Hits 500 K+ | Duración | Producción |
|---|---|---|---|---|---|
| **FIND caras graciosas** (ya lo tenemos) | GGsurvival: 3,3 M, mediana 867 K | video 1, día 0 | 25 de 36 | 31 s | Hecho |
| | FULYON: 27 M | video 3, día 4 | 43 de 95 | 33 s | |
| | MUK FT MIND, SRD Game, SpotVerse | video 3-16 | 4-15 | 12-16 s | |
| **STOP AT 99 %**: 4 jugadores, un "filtro de cara" tiembla y frena; gana el que calza | Eddy Kicks: 20,3 M | video 1, día 0 | 10 de 25 | **6 s** | Fácil (puntos de la cara) |
| **¿CUÁL LOOK? 1-4**: la foto del jugador al centro, lista 1-4, caen peinados o accesorios al ritmo | TrendPick (Neymar haircut): 3 M | video 7, día 6 | 8 de 37 | 18 s | Media |
| | Yuzix (Rate Haaland's outfit) | video 5, día 1 | 1 de 24 | 13 s | |
| | Muzam / Mr Muzu (Yamal vs Ronaldo dressing) | video 7-14 | 5-10 | 13-16 s | |
| **CATCH THE RIGHT HEAD**: cara cortada arriba, caen 3 pelos de jugadores, uno solo encaja | FOOTBALL_UNIVERSE6: 6 M | video 31, día 11 | 27 de 165 | 11 s | Media |
| **SAVE THE FOOTBALLER / corazones**: 4 jugadores, cada uno con vidas; falla, falla, el último se salva | DuoWave: **138 M** | video 10, día 4 | 63 de 195 | 24 s | Alta (física por código; ellos filman + CGI) |
| | BM Consulting (escudos de clubes): 28 M | video 2, día 1 | 29 de 74 | 20 s | |
| **Comparación partida** (altura/edad, año arriba) | FootyDuelX: 1,25 M | video 3, día 1 | 3 de 11 | 6 s | Fácil, pero limitada por las fotos libres |

### B. Los que más rinden necesitan video con IA (hoy no lo tenemos)
| Formato | Ejemplo | Primer hit | Hits 500 K+ |
|---|---|---|---|
| Parodias hiperrealistas con jugadores (comida gigante, bebé, sillas) | HappyHM: 198 M · FunBall: 62 M · dsfsdf: 105 M | video 1-2 | 110/133 · 79/116 · 17/46 |
| Versiones niño/niña de los jugadores | Watch Later: 9,1 M | video 8 | 4/24 |

Son los números más grandes del estudio. Necesitan generar video con IA (servicios pagos). Además, YouTube pide marcar como "contenido alterado o sintético" los videos realistas de personas reales. Queda como decisión tuya si en algún momento querés pagar eso.

### C. No los podemos hacer (dependen de clips ajenos o de filmar)
- Compilaciones con marcador (Football Epic, 69 M; Motion-f): son clips virales de otros.
- Desglose de precio del outfit con fotos de eventos (Global Outfit, nasib, OUTFIT BREAKDOWN): fotos de agencia y de productos.
- Antes y después con fotos de infancia reales (Era2Era): fotos con derechos.
- Retos filmados (UR PANDA, Mn Talent, Absurd Shots).

## Rotación propuesta (4 por día)
| Turno | Formato | Por qué |
|---|---|---|
| 1 | FIND | Serie principal, la que más probada está |
| 2 | STOP AT 99 % | El más corto: el loop sube el % visto. Primer hit en el video 1 |
| 3 | FIND | |
| 4 | ¿CUÁL LOOK? 1-4 | El comentario es un número. Mismo público, otra mecánica |

Semana 2: se suman CATCH THE RIGHT HEAD y SAVE THE FOOTBALLER si los primeros rinden.
**Regla para quedarse con un formato:** 10 videos. Si el promedio de "se quedó a mirar" del día 1 no llega al 50 %, se saca.

## Lo que se suma al motor para todos los formatos
- Flash + golpe de sonido + frase fuerte en el cuadro 0 (ya hecho en FIND v2).
- Opciones numeradas y pedido de comentario con número.
- Marcador (%, corazones, ✓/✗) con sonido de acierto y de fallo.
- Música: nuestro loop propio tipo phonk/funk a ~128 BPM. Al subir, si la app lo permite, se suma un sonido en tendencia a volumen bajo.
- Más fotos de frente de Haaland, Mbappé, Vinícius, Bellingham y Speed (Wikimedia).

## Límites
- La muestra son canales que ya pegaron (sesgo de supervivencia): muestra cómo lo hicieron, no la probabilidad de lograrlo.
- El análisis de Gemini es de un video por canal.
- "Hit" acá es 500 K+.
