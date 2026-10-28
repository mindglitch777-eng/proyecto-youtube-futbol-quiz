# 19 · Por qué no explotamos y qué replicar de verdad

**Datos de base:**
- **Canales:** 46 de fútbol que llegaron al primer millón con su video 1 a 5. Salen de cruzar más de 6.000 shorts de fútbol de 1M+ con el historial completo de 152 canales nuevos (`data/processed/virales_rapidos.csv`).
- **Videos analizados:** 43 de esos virales y 7 nuestros, vistos completos por Gemini con un cuestionario de edición. Incluye gancho cada medio segundo, cada toma, textos, audio, estructura y si se puede replicar (`data/raw/gemini_profundo/`).
- **Nuestros cuadros:** los miré yo directamente en nuestros archivos.

**Límite:** los cuadros de los virales no los pude ver yo, porque YouTube bloquea la descarga desde acá. Para esos dependo de Gemini, que sí mira y escucha el video entero.

## 1. Qué hay en los videos que explotan de entrada

| Tipo de imagen | Hits | Vistas |
|---|---|---|
| Video hecho con IA o animación 3D (deepfakes en broma, futbolistas 3D, anime) | 18 | 163 M |
| Material ajeno (partidos, clips virales, galas) con audio de meme | 17 | 115 M |
| Fotos + gráficos / juego (runner con fotos, grillas, rankings) | 8 | 49 M |

**Ninguno es un quiz con foto carnet ni una simulación de física**, salvo Fire Rankings, que explotó en su video 4.

Lo que comparten casi todos:
1. **Nombres enormes** en el cuadro 0: Ronaldo, Messi, Haaland, Mbappé, Yamal.
2. **Una mini historia con giro** en 5 a 35 segundos. Por ejemplo, Haaland finge una lesión y después baila (3,8 M). Ronaldo arranca último y termina con 6.974 puntos (108 M).
3. **El sujeto grande, llenando la pantalla, y siempre en movimiento.** La mediana es de 2,5 cortes cada 10 segundos y los edits llegan a 14.
4. **Audio de tendencia sincronizado** con cada golpe o aparición: phonk, funk brasilero o memes de audio.
5. **Corte seco que hace loop** o un llamado a pelear en los comentarios.

## 2. Qué hicimos mal (honesto)

Mirando nuestros cuadros:
- **Sujeto chiquito en pantalla vacía.** La cara ocupa alrededor del 15 % del cuadro; los virales llenan la pantalla.
- **Fotos de mala calidad e inconsistentes.**
  - Suárez 2015 con la cara de otro al lado.
  - Messi 2015 violeta.
  - Messi 2013 borroso y repetido en dos años.
  - Fotos de 2013 y 2014 rotuladas «2015».
- **Copiamos el nombre del formato, no el formato.**
  - **Evolución de FULYON (13,5 M):** no es una presentación de fotos por edad. Es un *juego runner* con fotos meme de Ronaldo, días que saltan («DAY 1 → DAY 999999») y plata que se multiplica. Lo mismo hace Suuuuu Shorts (4,7 M en su video 1).
  - **FIND (FULYON 23 M, SRD Game 2 M, MUK 1,3 M):** las 25 caras están *deformadas para dar risa*. Las nuestras eran casi la misma foto 25 veces.
- **Sin gancho ni giro.** Nuestros videos informan, los virales cuentan algo que no te esperás.
- **Audio genérico.** Los virales usan el sonido de moda. Nosotros mandamos beat propio y relator TTS.
- **Gemini puntúa nuestros videos demasiado bien.** Le pone 9/10 de idea al prime vs now y habla de «cortes frenéticos» que no existen. Para juzgar lo nuestro vale mirar los cuadros, no su nota.

## 3. Qué se puede replicar de verdad con lo que tenemos

Qué tenemos:
- Código, con el motor a 60 fps.
- Fotos libres.
- Recorte de jugadores con mediapipe.
- Deformaciones de cara por código.
- Blender, que se puede instalar.

Qué no tenemos:
- Generación de video.
- Generación de imágenes en plan gratis (la clave da cuota 0; con facturación cuesta centavos por imagen).
- Material de partidos.

| Formato | Copia a | Factible | Qué hace falta |
|---|---|---|---|
| **Runner meme «DAY 1 → DAY 999999»** | FULYON 13,5 M (video 3), Suuuuu 4,7 M (video 1), DriveLabs 24 M | Sí, con código | Pista en perspectiva, jugador recortado corriendo, puertas ×2/−50, fotos meme deformadas, contador de plata/días |
| **FIND con caras deformadas** | FULYON 23 M, SRD Game 2 M, MUK 1,3 M | Sí, con código | Deformar con mallas de la cara (ojos gigantes, boca estirada, peinados); grilla grande, barra de tiempo, círculo rojo |
| **Ranking con revelación al beat** («¿cuántos hijos tiene?», «patrimonio antes/ahora») | BALLDIT 1,2 M, Cosmic Editz 1,5 M (video 1) | Sí | Fotos buenas a pantalla completa en blanco y negro, zoom al golpe, número que aparece en el beat; datos verificados |
| **Sketch animado 2D** (burla Madrid/Barça) | Foot-high 14,5 M (video 2) | Solo con imágenes de IA | Facturación de imágenes |
| **Futbolistas 3D en un juego** («luz roja, luz verde») | Football 3D Club 108 M (video 1) | Posible con Blender, es mucho trabajo | Personajes 3D caricatura con camiseta, pelo y número |
| Edits de partidos / clips virales | Shiminski 14 M, Foot-high, TenzyFX… | No | Requiere material ajeno |

Sobre el audio: los virales usan el sonido de moda. Eso lo podés agregar vos desde el editor de Shorts al subir (biblioteca con licencia). Por eso conviene exportar sin música y con los golpes marcados.

## 4. Recomendación

1. **Frenar el calendario de plantillas.** Prime vs now, evolución por foto, duplas y carreras genéricas no tienen respaldo en estos datos.
2. Construir primero los dos formatos replicables al 100 % con código, **con el mismo esqueleto del original**:
   - el runner «DAY 1 → DAY 999999»;
   - el FIND con caras deformadas.
3. Revisar cada prototipo cuadro por cuadro contra la descripción del original antes de producir en serie.
4. Decisión del dueño del canal: ¿activar facturación de imágenes (centavos por imagen) para sketches 2D y versiones IA? ¿O invertir días en 3D con Blender, que es la apuesta de 108 M?
