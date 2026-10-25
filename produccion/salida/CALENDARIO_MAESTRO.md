# Calendario maestro (2 shorts por día)

**Horarios: 10:00 y 23:00, hora Argentina**, siempre los mismos (el algoritmo y tu audiencia se acostumbran).
Cada carpeta `produccion/salida/<id>/` tiene el video y `SUBIR.txt` (título, descripción con créditos y comentario para fijar).

| Cuándo | Video | Por qué ese día | Título A |
|---|---|---|---|
| dom 25-10 23:00 | `carrera_06` | Noche del Clásico (se jugó hoy 21:00 de España) | EL CLÁSICO RACE 🏁 Who wins? Pick one! |
| lun 26-10 10:00 | `find_the_real_02` | Ola FIND de FULYON (23 M y creciendo) | FIND YAMAL MESSI RONALDO 🔎 |
| lun 26-10 23:00 | `carrera_01` | Balón de Oro (ceremonia 17:00 ART): subí carrera_01 si gana YAMAL o carrera_01b si gana KANE | BALLON D'OR 2026 PREDICTION RACE 🏁 Who wins? Pick one! |
| mar 27-10 10:00 | `evo_01` | Evolución: Messi desde 2005 | Wait for it… 😳 Age evolution |
| mar 27-10 23:00 | `carrera_08` | Trío con Ronaldo (fórmula DriveLabs) | Mbappé, Yamal or Ronaldo? One Trophy, Three Superstars! 🏆 |
| mié 28-10 10:00 | `objeto_01` | Evolución de pelotas del Mundial (el formato de 10–26 M) | World Cup ball evolution (1930–2026) ⚽🔥 |
| mié 28-10 23:00 | `dupla_02` | Dupla: Messi y Neymar | MESSI & NEYMAR age evolution 😳 |
| jue 29-10 10:00 | `prime_01` | Prime vs now: Barcelona 2015 | BARCELONA 2015 THEN vs NOW 😳 |
| jue 29-10 23:00 | `carrera_04` | Debate GOAT (gana Ronaldo) | THE GOAT DEBATE RACE 🏁 Who wins? Pick one! |
| vie 30-10 10:00 | `find_the_real_03` | FIND | FIND MBAPPÉ VINÍCIUS BELLINGHAM 🔎 |
| vie 30-10 23:00 | `carrera_02` | Campeones del mundo (gana Argentina) | WORLD CUP CHAMPIONS RACE 🏁 Who wins? Pick one! |
| sáb 31-10 10:00 | `evo_02` | Evolución: Neymar | Wait for it… 😳 Age evolution |
| sáb 31-10 23:00 | `carrera_03` | Libertadores (gana Boca) | COPA LIBERTADORES GIANTS RACE 🏁 Who wins? Pick one! |
| dom 01-11 10:00 | `dupla_01` | Dupla: Lampard y Drogba (público UK) | LAMPARD & DROGBA age evolution 😳 |
| dom 01-11 23:00 | `carrera_09` | Trío con Ronaldo | Messi, Neymar or Ronaldo? Only ONE gets the trophy 🏆 |
| lun 02-11 10:00 | `prime_02` | Prime vs now: Alemania 2014 | GERMANY 2014 THEN vs NOW 😳 |
| lun 02-11 23:00 | `carrera_05` | Premier Big 6 (gana United) | PREMIER LEAGUE BIG 6 RACE 🏁 Who wins? Pick one! |
| mar 03-11 10:00 | `carrera_10` | Predicción Champions del martes (gana Barça) | Champions League Tuesday: who wins? 🏆 Prediction race |
| mar 03-11 23:00 | `evo_03` | Evolución: Beckham | Wait for it… 😳 Age evolution |
| mié 04-11 10:00 | `carrera_11` | Predicción Champions del miércoles (gana Madrid) | Champions League Wednesday: who wins? 🏆 Prediction race |
| mié 04-11 23:00 | `find_the_real_04` | FIND | FIND NEYMAR SALAH KANE 🔎 |
| jue 05-11 10:00 | `dupla_03` | Dupla: Casillas y Ramos | CASILLAS & RAMOS age evolution 😳 |
| jue 05-11 23:00 | `carrera_07` | Leyendas vs nueva generación (gana Ronaldinho) | LEGENDS vs NEW GEN RACE 🏁 Who wins? Pick one! |
| vie 06-11 10:00 | `evo_04` | Evolución: Salah | Wait for it… 😳 Age evolution |
| vie 06-11 23:00 | `lote1_02` | Fusión: Argentina vs Brasil | ARGENTINA vs BRAZIL in ONE face 🇦🇷🇧🇷 |
| sáb 07-11 10:00 | `prime_03` | Prime vs now: España 2010 | SPAIN 2010 THEN vs NOW 😳 |
| sáb 07-11 23:00 | `find_the_real_05` | FIND | FIND HAALAND PEDRI SAKA 🔎 |
| dom 08-11 10:00 | `evo_05` | Evolución: Zlatan | Wait for it… 😳 Age evolution |
| dom 08-11 23:00 | `dupla_04` | Dupla: Suárez y Messi | SUÁREZ & MESSI age evolution 😳 |
| lun 09-11 10:00 | `prime_04` | Prime vs now: Francia 2018 | FRANCE 2018 THEN vs NOW 😳 |
| lun 09-11 23:00 | `lote1_04` | Fusión: Premier League | PREMIER LEAGUE stars in ONE face 🤯 |
| mar 10-11 10:00 | `evo_06` | Evolución: Modrić | Wait for it… 😳 Age evolution |
| mar 10-11 23:00 | `lote1_06` | Fusión: jóvenes estrellas | YOUNG STARS in ONE face 🤯 Name both |
| mié 11-11 10:00 | `evo_07` | Evolución: Kane | Wait for it… 😳 Age evolution |
| mié 11-11 23:00 | `lote1_10` | Fusión: Messi o Ronaldo | MESSI + ? Only 1% know 😳 |

## Reglas de la semana
1. **Día 1 a 4: probar todos los formatos** (carreras, evolución, prime vs now, fusión, find the real).
2. **A las 48–72 h de cada video**, anotá en `produccion/registro.csv` vistas, % vieron vs. deslizaron y retención.
3. **El jueves**: el formato que pase **10 veces la mediana del canal** se **clona 3–5 veces** la semana siguiente
   (mismo formato, título casi igual, otro tema). El que quede abajo de la mediana sale del calendario.
4. **Eventos en vivo** (finales, clásicos, Balón de Oro, fechas FIFA): una carrera o evolución del tema ese mismo día.
5. Respondé los primeros 5 comentarios de cada video en la primera hora.
