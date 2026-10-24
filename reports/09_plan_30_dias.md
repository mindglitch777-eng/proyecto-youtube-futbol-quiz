# 09 · Plan de 30 días (BORRADOR: falta que elijas formatos e idioma)

**Resumen:**
- **2 shorts por día**, de 15 a 30 s, sin cara, en **español neutro**.
- **4 formatos en rotación** las primeras 2 semanas. Después **se duplica lo que pega y se corta lo que no**.
- Meta del mes: **encontrar 1 formato con mediana mayor a 20 mil vistas a las 48 h**.

> Es una propuesta: antes de producir, vos elegís formatos e idioma (puntos de control 2 y 3).

## Formatos candidatos (de los reportes 02 y 03)

| # | Formato | Por qué | Cómo se hace sin cara ni clips |
|---|---|---|---|
| A | **Encontrá al real / impostor** (grilla de caras) | Rinde 1,38× sin cara; 26 a 30 videos de 1 M+ por idioma; SpotVerse llegó a 43 M con 37 videos | Grilla 5×5 de fotos libres de Wikimedia, una "intrusa"; barra de tiempo; revelación con círculo y sonido de acierto |
| B | **Imagen oculta / silueta** | 1,39× sin cara; en inglés hay 49 videos de 1 M+, en español solo 8 → hueco | Silueta negra de foto libre que se va revelando (pixelado → nítido); 4 rondas de 3 s |
| C | **Verdadero o falso** | Formato con más rendimiento relativo (1,43×) y mediana de 225 mil en español | Fondo de color, frase grande, 3 s, revelación con ✅/❌ y un dato verificado |
| D | **Carrera del jugador** (escudos de sus clubes) | Mejor formato sin cara (1,46×); poca competencia (15 canales en español) | Escudos en fila con flechas → "¿quién es?"; datos de Wikipedia/Transfermarkt como fuente |
| E | **Ordená de mayor a menor** | 95 videos de 1 M+ en inglés contra 10 en español | 4 jugadores o equipos, el usuario piensa el orden; revelación con números (goles, valor, títulos) |
| F | **Tier list express** | Mucho debate en comentarios; 31 videos de 1 M+ en español | Plantilla S/A/B/C con 6 jugadores; queda "polémico" a propósito |

**Propuesta:** arrancar con **A, B, C y D** (más rendimiento relativo y más fáciles de automatizar). E y F entran en la semana 3 si sobra capacidad.

## Calendario

| Semana | Shorts | Qué |
|---|---|---|
| 1 (días 1–7) | 14 | Rotación A-B-C-D (3 o 4 de cada uno). Un tema de actualidad por día (Clásico, Balón de Oro, Libertadores). |
| 2 (días 8–14) | 14 | Igual. Ajustar el gancho y la duración según la retención de la semana 1. |
| 3 (días 15–21) | 14 a 21 | **Duplicar** los 2 formatos que más rindieron (60% del volumen). Probar E o F. Sumar el tercer short del día solo si el pipeline lo hace en menos de 20 minutos. |
| 4 (días 22–30) | 14 a 21 | Más fuerte en el ganador. Series ("Parte 2, 3…") de lo que pegó. |

**Horarios fijos:** 12:00 y 20:00 (hora Argentina). Ver reporte 04: el horario pesa poco, la constancia sí.

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
