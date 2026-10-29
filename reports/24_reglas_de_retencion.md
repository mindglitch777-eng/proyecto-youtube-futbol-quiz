# 24 · Reglas de retención (v1): cómo tiene que arrancar, avanzar y terminar cada short

**Objetivo de cada video:** que "se quedó a mirar" pase el **65 %** y el % visto pase el **90 %** (con loop).
Hoy: canal 40,5 %; mejor video 50,7 % (runner); peor 12,2 % (carrera).

## De dónde salen
- `research/medir_gancho.py` midió lo mismo en 11 virales (tus grabaciones) y en nuestros 7 shorts subidos, y lo cruzamos con el "se quedó a mirar" real de Studio. Datos: `data/processed/gancho_medido.json`.
- Límite: las grabaciones tienen la interfaz de YouTube encima (se recortó) y son 11 videos. Las reglas son hipótesis fuertes, no leyes: se recalibran con cada subida (ver "Ciclo").

| Medida | Virales (mediana) | Nuestros (mediana) | Lo que dice |
|---|---|---|---|
| Brillo del cuadro 0 | **150** | 55 | Nuestro único video claro (runner, 195) es el que más retiene. |
| Tamaño de la cara más grande en el cuadro 0 | **2,7 %** (hasta 13 %) | 0,3 % | Nuestras caras son 5-10 veces más chicas. |
| Movimiento en el primer segundo | **5,2** | 0,0 | Nuestras carreras arrancan congeladas. |
| Golpes de sonido por segundo | 0,5 | **1,8** | Sorpresa: tenemos MÁS efectos que los virales. Ellos usan una música/tendencia continua y pocos golpes, sincronizados con lo que pasa. |
| Duración | 31 s (FIND: 12-16 s) | 24 s | |

**Conclusión de los números:** no nos falta ruido, nos falta un **cuadro 0 que se entienda y atrape en medio segundo**.

## Las reglas

### A. El cuadro 0 (se decide en medio segundo, antes de que la persona "piense")
1. **Claro y colorido.** Brillo ≥ 130 (medible). Nada de fondos oscuros.
2. **Una cara famosa grande.** ≥ 3 % de la pantalla, ideal 6-13 %. El cerebro detecta caras conocidas antes que cualquier otra cosa.
3. **Ya se está moviendo.** Movimiento ≥ 4 en el primer segundo. El ojo sigue lo que se mueve; lo quieto se desliza.
4. **El desafío se entiende sin leer.** Máximo 3-4 palabras grandes: "FIND YAMAL", "DAY 1", "$0". Sin portada, sin intro, sin logo.
5. **Suena desde el cuadro 0.**

### B. Segundos 0-3: abrir una pregunta que el cerebro necesita cerrar
6. **Bucle abierto:** se plantea una pregunta con respuesta pendiente (¿dónde está?, ¿llega a rico?, ¿quién gana?). El cerebro tolera mal lo inconcluso (efecto Zeigarnik).
7. **Primera recompensa antes de 1,5 s:** algo pasa y "paga" (la primera puerta, el primer número que sube, el primer cambio de foto).
8. **Que el espectador participe:** buscar, adivinar o elegir. Mirar pasivo se desliza; jugar retiene.

### C. Desarrollo: dopamina por anticipación + sorpresa
9. **Algo grande cada ≤ 2 s; nunca más de 4 s sin un cambio fuerte** (medible).
10. **Recompensa variable:** a veces gana, a veces pierde, a veces sale algo raro (el "???"). Lo impredecible engancha más que lo previsible.
11. **Escalada:** cada paso vale más que el anterior (números más grandes, más tensión, más rápido) hasta el pico.
12. **Barra de progreso o contador visible** (tiempo, DAY, puertas restantes): saber que falta poco hace que no te vayas justo antes del final.
13. **Cortes de patrón cada 3-5 s:** meme, zoom, cambio de color, cara deformada. Rompen el piloto automático.
14. **Sonido:** una música/tendencia continua y reconocible de fondo, y pocos efectos fuertes solo en los momentos clave, sincronizados con la imagen (golpe = pasa algo). Sin silencios de más de 0,8 s.

### D. Final: el loop
15. **Cortar justo en la revelación.** Nada de cierre, cartel o despedida: ahí es donde hoy perdemos entre el 30 % y el 75 % de la gente que quedaba.
16. **El último cuadro empalma con el primero** para que el video se repita solo sin que la persona se dé cuenta (% visto > 100 %).
17. **Duración:** FIND 12-18 s; runner/evolución ≤ 25 s.

### E. Interacción (lo que más empuja al algoritmo después de la retención)
18. **Pedido de comentario con respuesta concreta y corta,** visible desde la mitad del video, no al final: "Comment your time ⏱️", "What DAY did he go broke? 👇", "Who would you pick?".
19. **Un poco de polémica o desafío:** "Only 1% can…", un resultado discutible. La gente comenta para corregir.
20. **Título = la pregunta del cuadro 0,** no un resumen.

## El sistema
1. **Antes de subir:** `python3 produccion/control_retencion.py <video.mp4>` revisa las reglas medibles (1, 2, 3, 5, 9, 14, 17) y dice PASA / NO PASA y por qué. Un video que no pasa no se sube.
2. **Revisión a mano** (lo que la máquina no mide): reglas 4, 6, 7, 8, 10, 11, 12, 15, 16, 18.
3. **Ciclo:** después de cada subida se anota en `data/medicion/registro_subidas.csv` el "se quedó a mirar" de la primera hora. Con 10-15 videos más se recalibran los umbrales: lo que no se correlacione se saca y lo que sí, se ajusta.
