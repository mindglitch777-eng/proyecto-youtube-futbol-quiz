# 09 · Plan de 30 días (BORRADOR: falta que elijas formatos e idioma)

**Resumen:**
- **2 shorts por día**, de 15 a 30 s, sin cara, en **español neutro**.
- **4 formatos en rotación** las primeras 2 semanas. Después **se duplica lo que pega y se corta lo que no**.
- Meta del mes: **encontrar 1 formato con mediana mayor a 20 mil vistas a las 48 h**.

> Es una propuesta: antes de producir, vos elegís formatos e idioma (puntos de control 2 y 3).

## Formatos candidatos (de los reportes 02 y 03)

| # | Formato | Por qué | Cómo se hace sin cara ni clips |
|---|---|---|---|
| A | **Encontrá al real / impostor** (grilla de caras) | Rinde 1,35× sin cara; en español buscar "encuentra al verdadero" da solo 12 videos (hueco); SpotVerse llegó a 43 M con 37 videos | Grilla 5×5 de fotos libres de Wikimedia, una "intrusa"; barra de tiempo; revelación con círculo y sonido de acierto |
| B | **Imagen oculta / silueta** | 1,23× sin cara; **el hueco más grande**: en inglés 73 videos de 1 M+, en español 9 | Silueta negra de foto libre que se va revelando (pixelado → nítido); 4 rondas de 3 s |
| C | **Nombrá jugadores (versión sin cara)** | **El mejor sin cara (1,42×)**; en español 66 videos de 1 M+ | "Nombrá 5 jugadores que jugaron en Boca y Real Madrid en 10 s": temporizador grande y revelación de la lista |
| D | **Verdadero o falso** | 1,27× sin cara; fuerte en español (18 videos de 1 M+) | Fondo de color, frase grande, 3 s, revelación con ✅/❌ y un dato verificado |
| E | **Armá tu equipo / elegí uno** | 1,35× sin cara; en inglés 97 videos de 1 M+, en español 33 | "Elegí 1 por línea": 4 pantallas de 2 opciones, el equipo final, "¿cuál armaste? 👇" |
| F | **Carrera del jugador** (escudos de sus clubes) | 1,25× sin cara; poca competencia (18 canales en español) | Escudos en fila con flechas → "¿quién es?"; datos de Wikipedia/Transfermarkt como fuente |

**Propuesta:** arrancar con **A, B, C y D** (los de más rendimiento sin cara o más hueco en español, y fáciles de automatizar). E y F entran en la semana 3 si sobra capacidad.

## Calendario

| Semana | Shorts | Qué |
|---|---|---|
| 1 (días 1–7) | 14 | Rotación A-B-C-D (3 o 4 de cada uno). Un tema de actualidad por día (Clásico, Balón de Oro, Libertadores). |
| 2 (días 8–14) | 14 | Igual. Ajustar el gancho y la duración según la retención de la semana 1. |
| 3 (días 15–21) | 14 a 21 | **Duplicar** los 2 formatos que más rindieron (60% del volumen). Probar E o F. Sumar el tercer short del día solo si el pipeline lo hace en menos de 20 minutos. |
| 4 (días 22–30) | 14 a 21 | Más fuerte en el ganador. Series ("Parte 2, 3…") de lo que pegó. |

**Horarios fijos:** 12:00 y 21:00 (hora Argentina); evitar las 16–17 h. Ver reporte 04: el horario pesa poco, la constancia sí.

## Métricas y reglas de decisión

Anotar cada short en `produccion/registro.csv` (el pipeline lo genera): fecha, formato, tema, y a las 48 h vistas, % de "vieron vs. deslizaron", retención media y comentarios.

| Métrica (de YouTube Studio) | Dónde | Bueno |
|---|---|---|
| **"Vieron vs. deslizaron"** (Shorts feed) | Studio → Analytics → el short | **Más de 70%** |
| Retención media | Igual | **Más de 80% en shorts de 15–20 s**; más de 100% indica que hay loop |
| Vistas a las 48 h | Studio | La referencia la marca tu propia mediana |
| Comentarios cada 1.000 vistas | Studio | Más de 0,5 (reporte 05) |

**Reglas:**
- **Cortar un formato** si después de 6 shorts su mediana de vistas a 48 h es menor que la mitad de la mediana del canal **y** "vieron vs. deslizaron" está debajo de 60%.
- **Duplicar un formato** si 1 de cada 6 shorts supera 5× la mediana del canal, o si "vieron vs. deslizaron" está arriba de 75%.
- **Si algo pega (10× la mediana):** en 24 h sacar la "Parte 2" con la misma plantilla y otro tema.
- **Día 30:** si ningún formato supera 20 mil de mediana, cambiar el idioma (inglés) o el estilo visual antes de seguir invirtiendo tiempo.

## Qué NO hacer (reporte 07)

- Clips de partidos, ni siquiera "con filtro" (MStriker los usa, pero es riesgo de Content ID).
- Música comercial agregada fuera de YouTube. Usá los sonidos del editor de Shorts o la Biblioteca de audio.
- Subir 3 iguales por día: ver la política de "contenido inauténtico". Variá formato, gancho y tema.
