# 18 · V2: motor profesional, formatos nuevos y calendario al 13-nov

## Qué se pidió
- Calidad igual o superior a la de la competencia, sin movimientos raros.
- Replicar de verdad los formatos virales.
- Escudos reales sí o sí, y distintas skins de pelota y de arco.
- Probar todo antes de entregar.
- Calendario nuevo.

## Motor V2 (`produccion/motor.py`)
- Vectores con antialias (cairo) y textos con Pillow. Salida a 60 fps en H.264, CRF 23, con faststart.
- Cámara: resorte críticamente amortiguado (`Resorte`). Se eliminó el temblor de pantalla en copas y carreras.
- 5 skins de pelota: clásica, dorada, champions, neón y mundial. Tienen sombreado esférico y brillo especular.
- 3 skins de arco: blanco, neón y dorado.
- Copa vectorial, chispas y confeti deterministas.
- Audio propio sintetizado: notas por rebote, silbato, bocina, tribuna y beat. Sin derechos de terceros.

## Escudos reales
- `escudos.py` corre en GitHub Actions y baja la imagen del infobox de Wikipedia de 46 clubes. Los logos "fair use" se leen del campo `image=` porque la API de imágenes no los devuelve.
- `render_carrera.competidores()` usa el escudo real y **falla si falta**: nunca se inventa un escudo.
- En la descripción se aclara que los escudos son marcas de sus clubes y se muestran solo para identificarlos.

## Formatos V2

| Script | Formato | Replica a | Videos |
|---|---|---|---|
| `render_copa_v2.py` | Circle Cup V2 | Footrix (3,9 M) | copa_01-03 |
| `render_ring_escape.py` | Ring Escape (nuevo) | bouncyball (86,2 M) | ring_01-03 |
| `render_trophy_race.py` | Trophy Race (nuevo) | Rival Stats (4,2 M) | trofeos_01 |
| `render_carrera_v5.py` | Carreras V5 | Fire Rankings (14,7 M), Sphere Stars (5,9 M) | carrera_02-05, 07-11 |

Detalles por formato:
- **Ring Escape:** 1 contra 1 usa 5 anillos con pelotas grandes. Con 3 o 4 jugadores usa 7 anillos. Cada rebote toca una nota de *Glory Glory* (Battle Hymn, dominio público). La semilla se elige por ganador, cambios de líder y final ajustado.
- **Trophy Race:** solo datos verificados a mano. Messi 16 (8 Balones de Oro, 4 Champions, Mundial 2022, Copa América 2021 y 2024, Finalissima 2022). Ronaldo 13 (5 Balones de Oro, 5 Champions, Euro 2016, Nations League 2019 y 2025).

## Pruebas
`probar_todo.py` renderiza los 16 videos y valida en cada uno:
- que termine sin error;
- 1080x1920 a 60 fps;
- que tenga audio;
- duración en rango;
- que gane el que pide el guion.

El resultado queda en `salida/prueba_v2.json`.

## Calendario
`calendario_v2.py` arma 35 publicaciones del 27-oct al 13-nov, 2 por día. Cada día lleva 1 simulación y 1 pasivo.
- Las fechas de Champions (3 y 4 de noviembre) llevan predicción con escudos.
- Las fusiones viejas salen del calendario porque no tienen respaldo en los datos.
