# Bitácora del Gerente IA · Futbol Edition

Cada día el Gerente anota acá lo que vio, lo que decidió (y por qué, con números) y qué tiene que revisar después.
Antes de decidir, lee las últimas entradas: así no repite decisiones, sigue lo que dejó pendiente y mide si sus cambios funcionaron.

Formato de cada entrada:
## AAAA-MM-DD
- **Vi:** (3-5 hechos con números; aclarar la confianza de cada uno y las ADVERTENCIAS del día)
- **Decidí e hice:** (cambio · motivo · las 6 preguntas del manual: n datos / dato sano / otra explicación / peor caso y cómo se deshace / cómo se mide / mío o del CEO)
- **No toqué (a propósito):** (lo que esperé por falta de datos o porque un cambio anterior todavía está en evaluación)
- **Revisar el AAAA-MM-DD:** (qué y con qué número se confirma o se revierte)
- **Para el CEO:** (solo lo que necesita su decisión; si no hay nada, "nada")

## 2026-11-11 (entrada inicial, armada con el CEO)
- **Vi:** canal +85 % en la mediana a las 48 h (1.938 → 3.590). HEAD FIT y WHEEL son las estrellas (5,1x y 3,4x el canal; WHEEL +140 %).
  STOP cae (-33 %, 0,8x). FIT ALL: 1.088-2.541 vistas en sus 3 primeros (WHEEL/HEAD FIT 15-23k los mismos días).
- **Decidí e hice:** FIT ALL deja de ser promovido (vuelve a prueba). Extras de los 3 formatos de 20 s: mié 11, jue 12 y vie 13 a las 18:30.
  Vigía: se corrigió la falsa alarma de "no subidos" en horarios ya cubiertos por videos viejos.
- **Revisar el 2026-11-14:** FIT ALL con ≥4 videos medidos (si < 0,5x del STOP, la poda lo saca). Los 3 de 20 s a las 48 h: ¿superan 3.000?
  STOP: si sigue < 0,7x del canal una semana más, proponer al CEO bajar de 2 a 1 por día y darle el lugar a WHEEL/HEAD FIT.
- **Para el CEO:** nada.

## 2026-11-11 (tarde) · primera propuesta con prototipo
- **Vi:** la fábrica de prototipos funciona de punta a punta (Issue #3, hoja en reports/propuestas/p001/hoja.jpg).
  En las muestras se ven 2 defectos visuales de formatos viejos: DRESS UP tiene un rectángulo negro sobre el pecho del
  jugador de la izquierda, y BALLON D'OR 100 % deja un hueco transparente en las manos del jugador antes de que llegue el trofeo.
- **Decidí e hice:** nada en la grilla (la propuesta espera al CEO).
- **Revisar el 2026-11-12:** pedirle al Ingeniero (jueves) que arregle esos 2 defectos antes de que DRESS o BALLON D'OR vuelvan a salir.
- **Para el CEO:** Issue #3 (bajar el STOP a 1 por día) con su prueba visual.

## 2026-11-13 · Ingeniero
- **Ingeniero:** 2 formatos de prueba nuevos con `"listo": false`: **CONVEYOR STOP** (`cinta`, variante de WHEEL: torsos de 6 superestrellas
  colgados de una cinta aérea sobre las piernas de una estrella) y **HEAD SLOT** (`slot`, variante de HEAD FIT: tragamonedas de cabezas de
  6 superestrellas que desemboca en el cuello; JACKPOT + monedas). Solo superestrellas, con una estrella en el cuadro 0. Avanzan a saltos y
  el PERFECT!/JACKPOT! se ve solo mientras la pieza correcta está calzada. Propuesta p002 con 3 muestras de cada uno (Issue #7).
  La prueba de humo con --render dio TODO OK. No toqué render_balon.py ni DRESS: los tiene la sesión principal.
- **Para el CEO:** Issue #7 (aprobar o no CONVEYOR STOP y HEAD SLOT; si entran, que alternen con WHEEL/HEAD FIT, sin sumarse como extras).

## 2026-11-13 · Gerente IA (turno diario)
- **Vi:** 821 suscriptores; 699 K de 10 M vistas de Shorts en 90 días (7 %). Últimas 24 h ~58 K vistas y ~48 subs (11-12/11: ~45 K y ~30; confianza baja, 1 día).
  Mediana del canal a las 48 h esta semana 2.490 (antes 6.044, -59 %): efecto de los 9-15 videos por día. WHEEL 8.117 (alta) pero cansado (últimos 4 = 36 % de los anteriores).
  HEAD FIT 15.207 (3 medidos, baja). Originalidad 86, inspector 0 defectos, sin advertencias, todos los workflows OK. 14/11: 7 videos con HEAD FIT 2 veces (subidos antes del arreglo).
- **Decidí e hice:** (1) CEO aprobó #6 y #7 → `piernas`, `cinta`, `slot` con `listo: true` (máx. 3/semana) + freno nuevo en e4_plan.py: máx. 1 variante de WHEEL/HEAD FIT por día.
  6 preguntas: n = 0 videos propios (son pruebas, no promoción) / dato sano, sin advertencias / la aprobación es del CEO; el freno sale de la lección del 13/11 / peor caso: 3 formatos flojos ocupan lugares de prueba → la poda los saca, o se vuelve a `listo: false` / se mide con 4 videos de cada uno a las 48 h / del CEO (aprobado), el freno es mío.
  (2) Respondí la consulta #4 (DRESS UP): sigue pausado; arreglar + acortar; 2 pruebas con propuesta; si < 120 % visto, se saca. Le pedí el arreglo al Ingeniero.
  (3) Cerré #3 según la decisión del CEO (STOP 2 por día).
- **No toqué (a propósito):** WHEEL 1 por día (cambio del 13/11 en evaluación); el doble HEAD FIT del 14/11 (ya subido; borrar/editar es del CEO); FIT ALL (el cerebro ya casi no lo elige); A/B del arranque del STOP (sin ganador: 44/56 %).
- **Revisar el 2026-11-16:** WHEEL a 1 por día: ¿vuelve a pasar 5 K a las 48 h? ¿Vistas diarias vuelven a ~70 K? Primeras variantes nuevas en la grilla.
- **Revisar el 2026-11-18:** 2.º STOP del día contra el 1.º (hoy ~2.350 vs ~10.500): si sigue igual, volver a presentar 1 por día.
- **Revisar el 2026-11-24:** piernas/cinta/slot con 4 videos: poda o sigue.
- **Para el CEO:** respuesta de DRESS UP en el Issue #4.

## 2026-11-14 · Gerente IA (turno diario)
- **Vi:** 874 suscriptores (+53 en un día); 758 K de 10 M vistas (8 %). Mediana de la semana a 48 h 2.143 (-63 %), todavía arrastra los días de 9-15 subidas.
  HEAD FIT llegó a 4 medidos: 9.459 (confianza media), pero sus últimos vienen bajando (-71 %, baja). WHEEL 6.842 (alta), cansado (24 %). STOP +28 %.
  Originalidad 88, inspector 41 sin defectos, reserva 12/12, todos los workflows OK, sin advertencias. 15/11 con sus 6 (1 WHEEL, 1 HEAD FIT); 16/11 trae el primer LEGS WHEEL.
- **Decidí e hice:** CEO decidió en #4 (DRESS): arreglo el lunes 16/11, 2 pruebas antes del 20/11, fecha límite 22/11; si no está o queda < 120 % visto o < mediana, se saca para siempre. Le pasé el pedido al Ingeniero.
  6 preguntas: n = 1 video (por eso se prueba, no se decide) / dato sano / ola "dress" subiendo a favor / peor caso: 2 lugares de prueba flojos, se saca el 22/11 / se mide % visto y vistas 48 h / del CEO (decidido).
  En la grilla, nada: el cambio del 13/11 está en evaluación.
- **No toqué (a propósito):** WHEEL 1 por día y las variantes (recién arrancan); HEAD FIT 2 veces hoy (ya subido); WHO IS THIS (1 video, 96 % visto: el cerebro casi no lo elige).
- **Revisar el 2026-11-16:** WHEEL ≥ 5 K a 48 h con 1 por día; propuesta DRESS si el Ingeniero lo terminó.
- **Revisar el 2026-11-18:** 2.º STOP vs 1.º; tendencia de HEAD FIT con 1 por día.
- **Revisar el 2026-11-22:** DRESS (fecha límite del CEO). **2026-11-24:** piernas/cinta/slot con 4 videos.
- **Para el CEO:** nada.

## 2026-11-15 · DECISIÓN DEL CEO (cargada por Claude, sesión principal)
- **Sale el STOP clásico** de la grilla (desde el 07/11: mediana 1.650 a 48 h, mejor 4.043, 0 videos de 10 K en 10 medidos; ocupaba 2 de 6 lugares).
- **Salen los quiz**: WHO IS THIS, PRICE TAG, BALLON Q y CAREER (listo:false; 182-1.251 vistas, 92 % visto).
- **Enfoque**: la mecánica que funciona (PARAR en el momento justo) con otras lógicas y mucha variedad. Grilla: WHEEL y HEAD FIT fijos + 4 lugares de prueba que reparte el cerebro entre LEGS WHEEL, CONVEYOR STOP, HEAD SLOT (hasta 2 variantes distintas por día), BALLON D'OR, FIT ALL, SIUUU, PENALTY y GOAT CIRCLE. Prueba ≤4 por semana; nunca un formato repetido en el día.
- Reserva: sin STOP (4 retirados); se repone con WHEEL y HEAD FIT.
- Pendiente de explicarle al CEO y decidir: WALL, TRIDENT y FIND (no son de la lógica de parar).
- **Revisar el 20/11**: vistas por día y videos de 10 K por día contra la semana anterior (~60 K y ~1,5).
- 15/11 (madrugada) CEO: también salen TRIDENT y FIND (no son de la lógica de parar; WALL ya no estaba en rotación). El CEO borra en YouTube Studio los 5 programados que no van (STOP 15/11 13:00 y 23:00, BALLON Q 15/11 17:00, STOP 16/11 13:00 y 21:30; marcados "reemplazado" en publicados.json) y la fábrica los cubre con extras de la lógica nueva: 15/11 13:00 HEAD SLOT, 17:00 CONVEYOR STOP, 23:00 GOAT CIRCLE · 16/11 13:00 FIT ALL, 21:30 CONVEYOR STOP.

## 2026-11-15 · PEDIDO DEL CEO PARA EL INGENIERO (lunes 16/11) · 3 formatos nuevos con la lógica de PARAR
El CEO aprobó probar las 3 ideas (todas con superestrellas en el cuadro 0, títulos solo con estrellas, premio visual al parar bien):
1. **STOP ON YOUR FAVORITE** (lo arma Claude, sesión principal, hoy 15/11): la pelota rebota entre 6 superestrellas; parás en tu favorito. Mercado: "CAN YOU STOP THE BALL ON YOUR FAVORITE PLAYER?" 1,3 M en 3 días.
2. **STOP TO ESCAPE** (Ingeniero): estrellas encerradas (laberinto/jaula); parar en el momento justo abre la puerta de tu estrella; tensión de "quién se salva". Mercado: "DISC SPEED CHALLENGE · WHO will GET OUT?" 1,1 M; "Ronaldo & Yamal vs MONSTER in the SECRET MAZE" 3,5 M.
3. **SKILL STOP** (Ingeniero): duelo "Ronaldo x Yamal" de habilidades (recortes animados, sin descargar videos de YouTube); hay que parar justo en el caño/gol. Mercado: "Ronaldo x Yamal Skills" 4 M (lo más visto de la semana).
Además del lunes: el arreglo de DRESS (rectángulo negro + más corto) con fecha límite 22/11 (#4).
Cada uno: produccion/render_<nombre>.py, en fabrica.py y config.json con "listo": false, propuesta con prototipo. **Al aprobarse**, poné en config "estreno_hasta": fecha +7 días: el planificador les asegura 3 lugares en su primera semana (mecanismo nuevo del 15/11) y después compiten en el cerebro.
- 15/11 Claude: **STOP ON YOUR FAVORITE en rotación** (idea aprobada por el CEO): 6 caras grandes (3 estrellas de hoy + 3 leyendas: Ronaldinho, Zidane, Beckham, Henry, Zlatan; aro dorado "LEGEND"), la pelota salta y hay que pausar en tu favorito. Estreno hasta el 24/11 (3 lugares asegurados). Kaká queda afuera: su foto es de otra persona (revisar assets/fotos/kak_*). Pedido del CEO: sumar leyendas también en los otros formatos cuando haya recortes buenos.

## 2026-11-15 · AUDITORÍA (Claude, sesión principal) · puntos aplicados por pedido del CEO ("haz los puntos necesarios")
Informe: https://claude.ai/artifact/RbAWMuQCwvrBkKqZLhhaRX
- **A1 Medición**: 24 horarios fijos (antes "cada hora" corría 3-4 veces por día) + una medición extra después de cada publicación y cada vigilancia.
- **A2 Poda nueva**: contra la mediana del canal (antes contra STOP); protege formatos con un video de 10 K entre sus últimos 4; poda si los últimos 3 quedan debajo de la mediana; cada cambio queda en poda.json "historial". **FIT ALL vuelve** (la poda vieja lo había sacado el 14/11 sin avisar).
- **A3 Vigilancia**: 12 horarios fijos; además mira pasos que fallan dentro de una corrida, si cada robot corrió lo que tiene que correr (desde el 17/11), medición fresca (máx. 3 h), si el Gerente/Ingeniero guardaron su trabajo, y avisa podas/promociones en un Issue con etiqueta "aviso".
- **A4 Hoja de control diaria**: la fábrica sube control.jpg al Release del día (4 cuadros por video). El Gerente la mira cada día. 1.ª revisión (17/11): PENALTY mostraba "80 % GOLAZO!" y el nombre cortado → arreglado.
- **B1 Semana de volumen 19-25/11**: 8 por día; los 2 extra (18:30 y 22:15) solo para familias WHEEL, CABEZAS y ELEGÍ. Se compara contra la semana de 6.
- **B2 Familias**: máximo 2 por familia por día (WHEEL: rueda/piernas/cinta · CABEZAS: cabezas/slot/fitall · ELEGÍ: favorito/circulo · MOMENTO: balon/siuu/penal).
- **B3 Métrica que manda**: videos de 10 K o más por día (hoy 0,86 en los últimos 7 días medidos) y vistas por día (~52 K). Meta: 3 y 110 K. En gerente.json "norte" y en la página.
- **C2 Pruebas A/B**: se cancelan las de STOP; nuevas: título de WHEEL ("vs" contra "Find X's real body") y FAVORITE con o sin leyendas.
- **D1**: fábrica semanal archivada.
- **Revisar el 23/11**: semana de volumen (fuertes por día y vistas por día) y si la vigilancia nueva detectó algo.

## 2026-11-15 · DATOS DE LA IA DE YOUTUBE STUDIO (los pidió el CEO) · lo que no da la API
- Vistos vs. deslizados (14 días): mejores WHEEL "X vs Y or Z" 66,2 %, DRESS 66,0 %, "Find Yamal's real body" 64,8 %, FIND 70-72 % (pero se van antes del final: 1-2,5 K). Peores: STOP clásico 36-42 %, un FIT ALL 37,5 %.
- Nuestro público mira en otros canales: desafíos de pausa (caras, siluetas, cuerpos), comparativas cara a cara (CR7 vs Messi, Haaland vs Lewandowski) y jugadas virales (Yamal, CR7, Neymar, Bellingham).
- Horarios: sábado pico 11-15 h, domingo 12-15 h; semana parejo 11-00 h, jueves y viernes fuerte después de las 21 h. → En la semana de volumen el lugar extra del fin de semana pasa a las 12:00.
- Vistas diarias del feed de Shorts: 9/11 35.678 · 10/11 63.851 · 11/11 28.390 (el peor: muchos deslizamientos) · 12/11 43.098 · 13/11 65.826 · 14/11 52.893.
- **PEDIDO PARA EL INGENIERO (lunes 16/11)**: además de STOP TO ESCAPE y SKILL STOP, un **VS STOP** (comparativa cara a cara con la lógica de parar: dos estrellas, parás y gana el que elegiste / el medidor decide). Es el 2.º interés de nuestro público.
- **GERENTE, cada lunes**: pedile al CEO que le pregunte a la IA de YouTube Studio los "vistos vs. deslizados" de la semana (no hay API para eso) y sumalo al análisis.

## 2026-11-15 · MODO SIMPLE PARA EL CEO (pedido del CEO)
Ver estrategia.md sección 00: un solo mensaje el lunes con todo lo pendiente; martes a domingo avisar solo si hace falta el CEO; el CEO puede decidir escribiéndole directo al Gerente en su sesión fija. Las propuestas siguen necesitando su "sí".

## 2026-11-15 · TRANQUILIDAD PARA EL CEO (3 máquinas nuevas, pedidas por el CEO)
- **Permiso de Google**: la vigilancia prueba en cada corrida que Google siga aceptando el permiso del canal; si lo rechaza, alarma con los pasos exactos (README sección 3.5 → secreto YT_REFRESH_TOKEN).
- **Semáforo** en la página (Resumen): verde = no hay que hacer nada · amarillo = algo para decidir · rojo = algo roto.
- **Balance quincenal** (balance.yml, el 1 y el 15 de cada mes, sin IA): últimas 2 semanas contra las 2 anteriores (vistas y suscriptores por día, videos de 10 K por día, semanas para 10 M), veredicto y recomendaciones; Issue "aviso". Gerente: leelo y actuá sobre sus recomendaciones.

## 2026-11-15 · ENGAGEMENT (respuestas de la IA de YouTube Studio a las 10 preguntas del CEO) · aplicado por Claude
- Hallazgos: >15 K vistas = 55-66 % vistos y 170-220 % visto (se repite 2 veces); <3 K = 36-45 % vistos. Caída fuerte a los 5,5-6 s (videos de 7 s); pico de repeticiones a los 2,5-3,2 s. Más suscriptores: WHEEL con Messi/Ronaldo/Yamal/Mbappé (2,2-2,6 cada 1.000). El público comenta EN QUÉ INTENTO lo logró. Duración óptima 7-9 s. Duelos: Ronaldo vs Messi, Yamal vs Mbappé/Vinícius. Recomienda 2-4 por día con 2-3 h de separación y 3-4 hashtags.
- Hice: CTA "HOW MANY TRIES? COMMENT 👇" y comentario fijado de intentos en todos los formatos de parar; descripción con la misma pregunta; máximo 4 hashtags; separación ≥1,5 h en la semana de 8 (extras a las 11:00 y 18:30; afuera 22:15); prueba A/B nueva: HEAD FIT 6,4 s contra 8 s; guía de engagement en estrategia.md para todo formato nuevo.
- Pendiente del CEO: la IA recomienda 2-4 videos por día; nuestra prueba de 8 sigue hasta el 22/11 y el 24/11 se decide con números (videos de 10 K por día y vistas por día).

## 2026-11-15 · DECISIÓN DEL CEO: cantidad de videos por día
Se termina la prueba de 8 por día (16-22/11) y el **24/11** se decide con números: videos de 10 K por día y vistas por día contra la semana anterior. Si 8 no mejora → 6. Si 6 tampoco mejora → probar 4 por día con 2-3 h de separación (lo que recomienda la IA de YouTube). Gerente: el 24/11 presentale al CEO la comparación en tu mensaje y esperá su "sí".

## 2026-11-15 · Gerente IA (turno diario)
- **Vi:** métrica que manda: 1,0 video de 10 K por día (meta 3) y ~47 K vistas por día (meta 110 K). 887 suscriptores (+11 en el día; el anterior +58).
  HEAD FIT 13.115 (5 medidos, media); WHEEL 7.471 (15, alta) ya sin cansancio. Originalidad 88 → 77 (bien). Inspector 58 sin defectos, reserva 12/12, workflows OK
  (TABLERO falló 1 vez a las 06:22 al publicar la página; la corrida anterior y las siguientes del sistema andan). Advertencia: el 17/11 sin videos subidos todavía: es el tope de ~10 subidas cada 24 h, no una falla.
  Hoja de control del 16-17/11 armada a mano (esos lotes son anteriores a la máquina): 4 videos del 17/11 con defectos.
- **Decidí e hice:** cancelé (sin subir) PENALTY 15:00 ("80 % GOLAZO!"), GOAT CIRCLE 17:00 (Pedri, "Antoine"), HEAD FIT 21:30 y WHEEL 23:00 (secundarios) del 17/11 y lancé la fábrica con esos 4 como extras rehechos (mismos formatos y horas).
  6 preguntas: n = 4 videos revisados cuadro por cuadro / dato sano (lo vi) / no hay otra explicación: se fabricaron antes de los arreglos (05:20 UTC vs 05:54 y 15:54) / peor caso: la fábrica falla y el 17/11 queda con 4 huecos → la reserva (12) los cubre; se deshace borrando "cancelado" / se mide: mañana el 17/11 tiene sus 8 y los nuevos se ven bien / mío (arreglar fallas, A4).
- **No toqué (a propósito):** 16/11 con 3 de la familia WHEEL y un extra a las 22:15 (el CONVEYOR de las 21:30 lo eligió el CEO); el extra de PIERNAS a las 22:15 del 17/11 (45 min de los vecinos, se ve bien; regla nueva aplica desde el 18/11).
- **Revisar el 2026-11-16:** los 4 rehechos del 17/11 (a ojo) y que el 17/11 tenga sus 8 subidos; WHEEL a 1 por día a las 48 h; entrega del Ingeniero.
- **Revisar el 2026-11-20/22/24:** vistas y videos de 10 K por día (20/11), DRESS (22/11), cantidad por día para el CEO (24/11).
- **Para el CEO:** nada.

## 2026-11-16 (tarde) · Gerente IA · DRESS UP
- El Ingeniero terminó el arreglo de DRESS (commit 24f99d2): sin rectángulos negros, 6,8 s (antes 11,4 s), solo superestrellas. Propuesta p004 con 2 muestras: Issue #13. Sigue `listo: false` hasta el "sí" del CEO.
- **Revisar el 2026-11-22:** si aprobado, los 2 videos a las 48 h (≥120 % visto y ≥ mediana del canal); si no, DRESS sale para siempre.

## 2026-11-16 · Ingeniero
- **Ingeniero:** (1) DRESS UP (#4) arreglado: el rectángulo negro venía de pelado.busto (el relleno fuera de la foto se tomaba como
  camiseta); ahora es fondo, revisado a ojo en los 15 bustos. Versión corta de 6,8 s (antes 11,4 s): 4 accesorios a 1,55 s y el loop
  empalma antes; solo superestrellas; sin tonos amarillos. Sigue listo:false; avisado al Gerente para su propuesta.
  (2) Formato nuevo **VS STOP** (`vs`, listo:false), pedido del 15/11: 2 superestrellas cara a cara + medidor de duelo; pausar con la
  pelota en la zona dorada corona a tu estrella (la corona se ve solo mientras está en la zona). Propuesta p005 (Issue #14).
  (3) Arreglo para todos los formatos: el 👇 del CTA (cambio del 15/11) salía como un cuadradito vacío porque la fuente de los carteles
  no tiene emojis; gancho.py ahora los saca al dibujar. Hoja de p005 regenerada (sin el cuadradito y con torsos de ancho parejo).
  Para el jueves 19/11 (pedido del Gerente, prioridad alta): 3-4 variantes visuales al azar en BALLON D'OR, PENALTY y HEAD SLOT
  (originalidad 68; distancia > 10 dentro del mismo formato), y también 3 variantes en VS STOP (estadio/paleta, lugar del medidor);
  después STOP TO ESCAPE y SKILL STOP. Ojo: los videos ya fabricados y no subidos siguen con el cuadradito del CTA.
- **Para el CEO:** Issue #14 (VS STOP).

## 2026-11-16 · Gerente IA · REVISIÓN SEMANAL (lunes)
- **La semana (9 → 16/11):** +307 K vistas (~44 K por día) y +259 suscriptores (~37 por día); la anterior: ~+390 K y ~+550. Videos de 10 K: 1,0 por día (meta 3); vistas por día ~58 K (meta 110 K). 903 suscriptores.
  Qué pasó: 9-15 subidas por día y WHEEL 2 veces por día (corregido el 14/11); el 15/11 el CEO dejó solo la lógica de parar con famosos (fuera STOP clásico, quiz, TRIDENT y FIND).
- **Vi hoy:** originalidad 88 → 77 → 68 ("se empieza a ver repetitivo", 11 de 60 casi idénticos): BALLON D'OR, PENALTY y HEAD SLOT a distancia 0-6 entre sí. CONVEYOR STOP debutó con 12.152 en ~14 h (baja: 1 video); HEAD SLOT 1.843.
  WHEEL 7.866 (16, alta), HEAD FIT 8.139 (6, media). Inspector 80 sin defectos; reserva 12/12. El 17/11 tiene 5 de 8 subidos (los 3 que faltan están fabricados y esperan el tope de subidas). Imagen de #14 perdida por choque de prototipos.
- **Decidí e hice:** (1) BALLON D'OR y PENALTY a máx. 2 por semana + pedido al Ingeniero de 3-4 variantes visuales (también HEAD SLOT; el jueves, antes que ESCAPE y SKILL).
  6 preguntas: n = 11 pares casi idénticos medidos por huella / dato sano (huellas de cada video) / otra explicación: los reintentos (r0/r1) inflan un poco el conteo, pero también hay pares entre videos distintos subidos / peor caso: 2-3 lugares de prueba menos para MOMENTO; se deshace sacando max_semana / se mide: índice > 80 el 23/11 / mío (pesos de las pruebas, pedido al Ingeniero).
  (2) Máquina de prototipos: el guardado ya no se pierde por un choque y falla si no guarda; relancé la de VS STOP (#14). Mío (arreglar fallas).
- **No toqué (a propósito):** HEAD SLOT (está en estreno hasta el 22/11); la semana de 8 (decisión del CEO, se mide el 24/11); los avisos duplicados de balance (#10 y #12).
- **PLAN DE LA SEMANA (16-22/11):** 8 videos por día con la lógica de parar y solo famosos. WHEEL y HEAD FIT fijos; estrenos de CONVEYOR, LEGS WHEEL, HEAD SLOT y FAVORITE (3 lugares asegurados cada uno).
  El Ingeniero (jueves) hace las variantes visuales y después STOP TO ESCAPE y SKILL STOP. DRESS: 2 pruebas si el CEO dice sí (#13).
- **Revisar el 2026-11-19:** entrega del Ingeniero (variantes) · **20/11** vistas y videos de 10 K por día · **22/11** DRESS · **23/11** originalidad (> 80) y fin de estrenos · **24/11** comparación de la semana de 8 para el CEO.
- **Para el CEO:** #13 (DRESS) y #14 (VS STOP), sí o no. Pregunta de YouTube Studio de "vistos vs. deslizados".
- 16/11 (tarde): el Ingeniero arregló el cuadradito del CTA (el 👇 no se dibujaba en casi todos los formatos de parar; commit ef01f30). Los videos del 17 y el 18/11 ya fabricados lo traen.
  **Decidí no rehacerlos**: es un detalle chico en el texto del final, y rehacer ~12 videos gasta el tope de subidas y arriesga dejar horarios vacíos. Desde el lote del 19/11 sale bien. Revisar en la hoja de control del 19/11.

## 2026-11-17 · Ingeniero (anotación)
- **Ingeniero:** pedido del Gerente para el jueves 19/11 (CEO en #14): VS STOP más difícil (pelota más rápida y zona dorada más chica,
  con la corona siempre honesta) y regenerar la hoja de #14; 3 variantes visuales en VS, BALLON D'OR, PENALTY y HEAD SLOT
  (originalidad 57, alarma en 55); estructuras de título nuevas para WHEEL, HEAD FIT y sus variantes (títulos 66 % parecidos), con superestrellas al inicio.

## 2026-11-17 · Gerente IA (turno diario)
- **Vi:** 919 suscriptores (+16). Métrica que manda: 1,0 video de 10 K por día y ~44 K vistas por día (bajando). Originalidad 57 (límite 55): 16 de 60 casi idénticos y títulos 66 % parecidos.
  Estrenos: CONVEYOR 23.494 (1.º) y 3.476 (2.º, 10 h), FAVORITE 10.443 en 13 h, HEAD SLOT 4.046 (baja). HEAD FIT cansado (59 %, mediana 4.418, alta). WHEEL 6.539 (alta).
  Máquinas OK (solo mediciones canceladas por pisarse, normal). Inspector 104 sin defectos. Hoja de control 19/11: WHEEL 23:00 "Mbappé vs Vinícius or Vinícius".
  CEO: "Aprobado" en #13 (DRESS); en #14 pidió VS STOP "más difícil, con velocidad mayor".
- **Decidí e hice:** (1) DRESS: extras 19/11 20:00 (cancelé el BALLON D'OR de esa hora, que pasaba su tope de 2) y 20/11 20:00. El 18/11 estaba todo subido salvo HEAD FIT (fijo), así que el 2.º va el 20/11; los dos se miden el 22/11.
  6 preguntas: n = 1 video previo (por eso son pruebas) / dato sano / otra explicación: ola "dress" subiendo / peor caso: 2 lugares flojos, sale el 22/11 / se mide % visto ≥ 120 y ≥ mediana a 48 h / del CEO (aprobado).
  (2) Arreglé la causa del título con nombre repetido en WHEEL y mandé a rehacer el del 19/11 23:00. Mío (arreglar fallas).
  (3) VS STOP: pedido del CEO pasado al Ingeniero (jueves); #14 queda abierta.
- **No toqué (a propósito):** HEAD FIT (es fijo; se mira el 20/11); los videos del 17-18/11 con el cuadradito en el CTA (decidido ayer).
- **Revisar el 2026-11-18:** cancelar el video que el plan ponga el 20/11 a las 20:00 (ahí va DRESS) y verificar que los 2 DRESS y el WHEEL rehecho se vean bien; cerrar #13.
- **Revisar el 2026-11-19:** entrega del Ingeniero (variantes, títulos, VS STOP). **20/11:** HEAD FIT y vistas por día. **22/11** DRESS. **23/11** originalidad. **24/11** comparación para el CEO.
- **Para el CEO:** nada.
