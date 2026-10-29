# 25 · Cómo funciona el algoritmo de Shorts en 2026 (y cómo lo usan los canales de fútbol que crecen)

Fecha: 29-oct-2026. Tres fuentes:
1. **Lo que dice YouTube** (entrevista de Todd Sherman, jefe de producto de Shorts, en Creator Insider; páginas de ayuda; anuncios de 2025-2026), vía coberturas de prensa.
2. **Estudios publicados** (Metricool 2026: 799.718 videos; Social Insider; Tubular; papers en arXiv).
3. **Nuestros datos:** 130 canales de fútbol en Shorts con algún video de 1 M+ en los últimos 3 meses, 18.674 videos (YouTube Data API) + 7 videos nuestros con datos de Studio + 11 virales medidos cuadro a cuadro.

Todos los análisis de nuestros datos comparan cada video **contra la mediana de su propio canal** (×1,00 = normal del canal), así un canal de 10 M de suscriptores no se mezcla con uno de 500.

---

## 1. Cómo decide YouTube a quién mostrarle un Short

**El mecanismo (dicho por YouTube):**
- Cada Short se muestra primero a un **grupo de prueba** en el feed. Si ese grupo responde bien, lo muestra a un grupo más grande; si no, se frena. YouTube lo describe como "explorar y explotar".
- En el feed **nadie elige el video**: aparece solo. Por eso la señal que más pesa es si la persona **se queda o desliza** ("Se quedó a mirar" vs "Descartado"), y después cuánto lo mira y si lo repite.
- Sherman: "**la audiencia es el algoritmo**". No hay trucos de sistema: el sistema sigue lo que hace la gente.

**Lo que confirma nuestro canal:** cada video recibe su prueba de ~1.000-1.500 personas (por eso todos quedan en ~1.400) y se frena porque entre el 50 % y el 88 % desliza.

**Cambios confirmados que importan hoy:**
| Fecha | Cambio | Qué nos implica |
|---|---|---|
| Oct-2024 | Shorts de hasta 3 minutos | La duración no es un límite; manda la retención. |
| 31-mar-2025 | Una vista cuenta apenas el Short arranca (y cada repetición). Para monetizar se usan las **"vistas interesadas"** (las de antes). | El número público infla; para YPP mirar "vistas interesadas" en Studio (hoy: 3,9 K de 9,5 K). |
| 15-jul-2025 | Política de **contenido inauténtico**: lo repetitivo o producido en masa "con plantilla y poca variación" no se monetiza, y puede afectar **todo el canal**. | Una serie está bien, pero cada video tiene que ser distinto de verdad (otros jugadores, otra historia, otra edición), no la misma plantilla con el nombre cambiado. |
| 1-oct-2026 | Las recomendaciones de Shorts **priorizan contenido original** y bajan el alcance de lo re-subido de otros creadores. | Nos favorece: lo nuestro es animación propia. Evitar clips ajenos. |
| 1-feb-2027 | YPP por Shorts: **10 M de vistas válidas en 90 días** + 1.000 suscriptores. | Meta concreta: ~111.000 vistas válidas por día en promedio. |

**Mitos que YouTube desmintió (Sherman):**
- Subir 5 o 10 por día **no** desbloquea más alcance.
- Borrar y volver a subir un Short que no anduvo **no** se recomienda: puede leerse como spam.
- Los **hashtags** no son necesarios.
- La **hora** casi no importa, salvo en noticias de último momento.

---

## 2. Lo que dicen nuestros datos (130 canales, 18.674 Shorts)

### 2.1 Es una lotería con boletos que se pueden mejorar
- El **10 % de mejores videos de cada canal se lleva el 70 % de todas sus vistas** (mediana de 120 canales).
- Solo el **11,5 % de los videos** llega a 10 veces la mediana de su canal, o sea **1 de cada 9**.
- Hasta los canales grandes viven de pocos hits: la mayoría de sus videos son "normales".

**Implicancia:** no hay que juzgar el canal por un video. Hacen falta **muchos intentos buenos**: cada video bien hecho es un boleto, y la calidad del gancho cambia cuántos números tiene ese boleto.

### 2.2 Frecuencia: subir más no castiga ni premia por video
Vistas de cada video según cuántos subió el canal ese mismo día:

| Videos ese día | Vistas (vs normal del canal) |
|---|---|
| 1 | ×1,02 |
| 2 | ×0,98 |
| 3 | ×0,90 |
| 4 | ×1,09 |
| 5+ | ×0,95 |

Coincide con YouTube: no hay premio por volumen, pero **tampoco se canibalizan**. Entonces más videos buenos = más boletos = más vistas totales.
Los canales grandes de la muestra suben en promedio **0,7 por día** (FOOTIEHAWK 0,9; 217aep 0,7; @xa07_Editx 2,2).

### 2.3 Horario: casi no importa
- Las vistas según la hora UTC de subida van de ×0,81 a ×1,28, sin un patrón firme.
- Las horas más usadas por los canales son **12, 16 y 11 UTC** (9, 13 y 8 h de Argentina): el mediodía europeo.
- Conclusión: subir en un horario fijo por costumbre está bien, pero no es una palanca.

### 2.4 Duración: no es una palanca por sí sola
| Duración | Vistas (vs normal del canal) | % de hits |
|---|---|---|
| 0-10 s | ×1,01 | 12,7 % |
| 10-15 s | ×0,95 | 11,7 % |
| 15-20 s | ×0,89 | 9,9 % |
| 20-30 s | ×1,04 | 11,0 % |
| 30-45 s | ×1,00 | 11,4 % |
| 45-60 s | ×0,99 | 11,4 % |
| 60-90 s | ×1,16 | 10,5 % |
| 90-180 s | ×1,00 | 7,9 % |

Es casi plano. **La duración correcta es la que el contenido sostiene sin bajar el ritmo.** Por eso nuestro FIND de 18 s retiene 76 %, y el rematch de 55 s pierde gente en los últimos 4 s. (Corrige la regla 17 del reporte 24: el límite no es un número fijo, es "nunca un segundo de relleno".)

### 2.5 Títulos: pesan poco (el 98 % de las vistas viene del feed, donde casi no se leen)
| Rasgo del título | Vistas con | Sin | % hits con | Sin |
|---|---|---|---|---|
| "find" | **×2,14** | ×1,00 | **21 %** | 11 % |
| Mr Beast | ×1,24 | ×1,00 | 13 % | 11 % |
| Neymar | ×1,16 | ×0,99 | 13 % | 11 % |
| Yamal | ×1,13 | ×0,99 | 14 % | 11 % |
| IShowSpeed | ×1,13 | ×1,00 | 14 % | 11 % |
| Ronaldo / CR7 | ×1,01 | ×1,00 | 12 % | 10 % |
| hashtags (cualquiera) | ×0,99 | ×1,02 | 11 % | 11 % |
| TODO EN MAYÚSCULAS | ×1,00 | ×1,00 | **6 %** | 12 % |

- Lo que suma son **los nombres que la gente quiere ver** (Yamal, Neymar, Speed, Mr Beast) y el **formato del momento** (FIND).
- Hashtags y emojis: neutros.
- Mayúsculas totales: la mitad de hits.
- El título no salva un video; el cuadro 0 sí.

### 2.6 Un Short no muere a las 48 h
Vistas según la edad del video (vs normal del canal):

| Edad | ×0-2 d | 3-7 d | 8-30 d | 31-90 d |
|---|---|---|---|---|
| Vistas | ×0,49 | ×0,70 | ×0,96 | ×1,13 |

A los 2 días un video tiene la mitad de lo que va a tener. Sigue sumando durante semanas: YouTube lo vuelve a probar con otros grupos. Social Insider encontró picos hasta 25-30 días después.
**Implicancia:** "se quedó a mirar" de la primera hora sirve para juzgar el gancho. Las vistas se juzgan a los **7 días**, no a las 48 h. Y nunca hay que borrar un video que arrancó flojo.

### 2.7 El engagement no es lo que hace un hit
| | Me gusta por vista | Comentarios por vista |
|---|---|---|
| Hits (10× la mediana) | 1,07 % | 0,005 % |
| Videos normales | 1,62 % | 0,015 % |

Los hits tienen **menos** likes y comentarios por vista, porque llegan a gente que no es fan del canal. Lo que empuja un video es que **la gente se quede y lo termine**. Los comentarios suman, pero son consecuencia, no causa.
(Metricool 2026, global: el engagement de Shorts cayó de 4,94 % a 1,85 % mientras las vistas subieron 127 %; el tiempo medio por Short es ~16 s.)

### 2.8 Cómo manejan el algoritmo los canales que más crecen
1. **Serie fija:** en 87 de 113 canales, más de la mitad de los videos giran alrededor de las **mismas 2 palabras** (mismos jugadores o el mismo formato). La mediana es 75 %. Ejemplos:
   - FOOTIEHAWK (9,9 M de subs): "ronaldo messi" en el 99 % de sus videos.
   - 217aep (4,6 M): "ronaldo neymar yamal", 91 %.
   - FlashPass (6,7 M): "ronaldo neymar yamal", 80 %.
   - PKM FootBall: "maze ronaldo challenge", 100 %.
   - HappyHM: "#mbappe #haaland", 95 %.

   El algoritmo aprende rápido a quién mostrarle un canal que hace siempre lo mismo para el mismo público.
2. **Mismos 4-5 jugadores:** Ronaldo, Neymar, Yamal y Messi en casi todos; Speed y Mr Beast como "invitados".
3. **Cadencia estable:** ~1 por día; los más agresivos, 2-3.
4. **Después de un hit no cambian nada:** los 10 videos siguientes rinden ×2,29 vs ×2,14 los 10 anteriores. O sea, los hits llegan en rachas (cuando el formato está caliente) y los canales siguen con lo mismo; los títulos de después se parecen solo un poco más (0,20 vs 0,19).
5. **Casos de este mes** (reporte 22):
   - SpotVerse: 14 FIND seguidos con 14-74 K cada uno, y el 16 hizo 8,7 M.
   - Tima Gmx: 40 runners con 1-7 K, y el 41 hizo 387 K.
   - GoalQuiz: el primero hizo 688 K.

   Ninguno cambió de formato a cada rato.

### 2.9 Límite de estos datos
- La muestra son canales **que ya tuvieron éxito** (sesgo de supervivencia). No sirve para calcular la probabilidad de que un canal nuevo pegue, solo para ver cómo se comportan los que pegaron.
- Los 46 canales "virales rápidos" se eligieron justamente porque pegaron en sus primeros 5 videos.
- Todo es correlación, no prueba de causa.

---

## 3. Lo que esto significa para Futbol Edition

**Diagnóstico:**
- Nuestros videos reciben su prueba completa (~1.400) y la pierden en el primer medio segundo (40,5 % se queda; los que pegan están en 65-80 %).
- Además cambiamos de formato casi en cada video (carreras, FIND, evolución, copa, anillos, runner), así que YouTube no puede aprender a quién mostrarnos.

**Cómo accionar:**
1. **Una serie principal + una de prueba.** La principal ocupa el 70-80 % de los videos, con el mismo formato y los mismos 4-5 jugadores. Candidata por datos: **FIND** (formato del momento ×2,14, nuestro mejor % visto 76,6 %). La de prueba: runner (nuestro mejor "se quedó", 50,7 %) o anillos (49,8 %).
2. **Volumen: 2 por día durante 30 días** (60 boletos). Con 1 hit cada ~9 videos son 6-7 hits esperables si la calidad está al nivel de los canales del dataset. Es una estimación, no una promesa.
3. **Cada video pasa el control de retención** (reporte 24) antes de subirse.
4. **Medir bien:**
   - "Se quedó a mirar" en la **primera hora**: juzga el gancho.
   - Vistas a los **7 días**: juzgan el video.
   - Vistas interesadas en 90 días: el camino al YPP.
5. **No borrar, no re-subir, no cambiar de formato por un video flojo.** Se cambia solo si 15 videos seguidos con el gancho corregido no mejoran el "se quedó".
6. **Títulos:** el nombre del jugador más buscado + el formato ("FIND YAMAL NEYMAR RONALDO"). Sin todo en mayúsculas forzadas ni montones de hashtags: no suman.
7. **Originalidad:** cada video con jugadores, orden y edición distintos (política de contenido inauténtico).

**La meta en números:**

| Etapa | Objetivo |
|---|---|
| Próximos 15 videos | "Se quedó a mirar" ≥ 55 % de promedio |
| 30 días / 60 videos | Al menos 3 videos de más de 50 K |
| 90 días | 10 M de vistas válidas + 1.000 suscriptores (YPP) |

---

## Fuentes
- YouTube / Todd Sherman (Creator Insider, ago-2023): Search Engine Journal, "YouTube Explains How Shorts Algorithm Works"; Benzinga, "YouTube Shorts Chief Debunks Popular Myths"; MediaPost.
- Conteo de vistas 31-mar-2025: ppc.land, routenote, vidIQ.
- Contenido inauténtico 15-jul-2025: ayuda de YouTube (support.google.com/youtube/answer/1311392), Search Engine Journal.
- Prioridad a lo original 1-oct-2026: MediaPost (05-oct-2026), Uppbeat, Vanguard.
- Metricool, estudio YouTube 2026 (799.718 videos); Social Insider (picos tardíos); Tubular (77 % de vistas en videos de menos de 1 minuto).
- Papers: arXiv 2605.18653 (WEBSHORTS, la viralidad depende de tendencias externas), arXiv 2512.21402 (11.000 Shorts).
- Datos propios: `data/raw/algoritmo/`, `data/processed/algoritmo_resultados.json`, scripts `research/algoritmo_dataset.py` y `research/algoritmo_analisis.py`.
