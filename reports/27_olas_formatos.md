# 27 · Olas de formatos (31/10/2026): qué explota Y se sostiene

Datos: 45 búsquedas de Shorts de fútbol de los últimos 45 días (1.946 videos, 786 canales), historial completo de los 70 canales
que más vistas por día hacen, y 12 videos analizados por Gemini. Archivos: `data/raw/olas/`.

## Cómo despegan los canales nuevos (creados en 2026)

| Canal | Creado | Subs | Shorts hasta 1M | % de Shorts recientes ≥ 1M | Subidas/día | Duración | Formato |
|---|---|---|---|---|---|---|---|
| FunBall | ago-26 | 480k | 1 | 37 % | 1,8 | 9 s | rota 4-5 formatos fijos |
| Eddy Kicks | sep-26 | 88k | 1 | 30 % | 0,8 | 6 s | solo STOP |
| MStriker | ago-26 | 78k | 2 | 50 % | 1,0 | 26 s | solo quiz "only 1% can guess" |
| Zayden FC | jun-26 | 82k | 14 | 53 % | 0,7 | 6 s | solo "X x Y skills" |
| Aerooo | jun-26 | 63k | 2 | 33 % | 1,1 | 6 s | solo "X x Y skills" |
| Football Epic | may-26 | 453k | 1 | 10 % | 0,9 | 25 s | solo "A VS B VS C… ✓/✗" |
| Ariz Arakan | may-26 | 92k | 7 | 57 % | 0,4 | 18 s | solo desafío de arquero |

Conclusiones:
1. **Un formato que funciona explota enseguida: 1M en los primeros 1-14 Shorts (mediana 1-2).** Si después de ~10-15 videos
   no aparece ningún hit, el formato no va → se descarta. (LOOK y HOYO ya afuera.)
2. **Los que se sostienen repiten la misma plantilla siempre** (mismo título con otros jugadores) y suben 0,4-1,9 por día.
   El canal que más creció (FunBall) **rota 4-5 formatos fijos** → coincide con nuestra idea de varios formatos por día.
3. **Son cortos**: mediana 6-25 s. Los de 5-6 s con loop (STOP, skills, race) tienen el % de hits más alto.
4. Siempre los mismos 6 jugadores: Messi, Ronaldo, Yamal, Neymar, Mbappé, Haaland.

## Lo más visto de canales nuevos y si se puede hacer con código

| Formato | Ejemplo | Vistas | ¿Por código? |
|---|---|---|---|
| Sketch con IA / face-swap (jugadores haciendo bromas) | MusMusTV, ainimal-rescue-ai, FunBall | 13-91 M | ❌ necesita IA de video |
| **Dressing challenge**: accesorios caen sobre 2 jugadores, los que no van se descartan | Muzam | 31 M | ✅ |
| Rankings con clips reales | TIER, Sports Moment Rank | 7-27 M | ❌ footage con derechos |
| **Footballer race / who is fastest** (5 s, 4 caras, puesto 1-4) | FunBall | 7-9 M | ✅ |
| **Globos con escudos que revientan** ("Real Madrid or Barcelona?") | Qatil Bewafa | 10 M | ✅ |
| **Eliminación ✓/✗** (cada jugador intenta algo, queda uno) | Football Epic | 10 M | ✅ (con escena propia) |
| **Pelotas con caras cayendo (satisfying)** | 3D Club | 9 M | ✅ (valida PLINKO) |
| Pause test 4 cuadrantes | YT SUPER PLAYER, Eddy Kicks | 8-20 M | ✅ = nuestro STOP |
| FIND | FULYON, GOALPREDICT | 6-9 M | ✅ = nuestro FIND |
| Catch the right head | FOOTBALL_UNIVERSE6 | 6 M | ✅ = nuestro CATCH |

## Formatos nuevos propuestos (inspirados en lo que funciona + nuestra dopamina)

1. **RACE 5s** (who is fastest): 4 caras en carriles, largan al "GO", adelantos y empates hasta la meta, puestos #1-#4 con medallas.
   Loop de 5-6 s. El más barato de producir y el de más % de hits.
2. **FILL RACE** (satisfying): 4 tubos, uno por jugador; caen cientos de pelotitas con caras; el primero que se llena gana la carta.
   Mezcla el "satisfying" de 3D Club con la carrera.
3. **SURVIVE ✓/✗**: 6 jugadores intentan de a uno un desafío (penal al ángulo, travesaño, chilena…) → ✓ o ✗ con sonido;
   queda uno → corona. Título "A VS B VS C VS D VS E VS F", como Football Epic.
4. **BALLOON POP**: globos con escudos de clubes que se inflan y revientan uno por uno; el último queda gigante → "Real Madrid or Barcelona?".

## Programación

- Hoy la API permite **6 subidas por día** (10.000 unidades ÷ 1.600). Para más hay que pedir más cuota a Google (gratis, unos días).
- Grilla propuesta: **6 por día, 6 formatos distintos**, cada uno a la misma hora todos los días (el algoritmo y la audiencia aprenden la serie).
- Regla automática: cada formato con ≥ 12 videos publicados y **ningún video arriba del doble de la mediana del canal** pasa a "en pausa"
  y libera su lugar para el siguiente formato nuevo.
