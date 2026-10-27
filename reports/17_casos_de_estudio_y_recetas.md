# 17 · Casos de estudio (canales que explotaron de la nada) y recetas exactas para replicar

Fuente: YouTube Data API (historial completo de 12 canales, `research/casos.py` → `data/processed/casos.csv`) y Gemini mirando los videos que más pegaron (`research/gemini_receta.py` → `data/raw/gemini_recetas/`). Fecha: 27-oct-2026.

## 1. Qué tan rápido explotaron

| Canal | Formato principal | Videos hasta el 1er 1M | Días hasta el 1er 1M | Días a 10M vistas totales | Videos/día | % de videos con 1M+ |
|---|---|---|---|---|---|---|
| Footypoints | memes de clásicos/rivalidad | **2** | **3** | 21 | 0,4 | 21 % |
| FULYON SHORTS | evolución + FIND | **3** | **4** | **4** | 0,7 | **28 %** |
| Fire Rankings | carrera de canicas con caras | **4** | 26 | 31 | 1,0 | 13 % |
| Rival Stats | quién tiene más trofeos | 13 | **5** | 13 | 1,8 | 4 % |
| MainFutLab | "IA predice" campeones | 21 | 17 | 27 | 1,3 | 7 % |
| Footrix | torneo en círculo + campeones por año | 26 | 24 | 52 | 0,9 | 15 % |
| Sphere Stars | laberinto/carrera de bolas | 29 | 64 | 77 | 0,4 | 9 % |
| GreyHaT Sim | simulación de física | 30 | 33 | 73 | 0,7 | 6 % |
| Icon Stories | evolución narrada | 44 | 46 | 52 | 1,0 | 14 % |
| DriveLabs | runner 3D "¿quién gana?" | 54 | 42 | 42 | 1,0 | 18 % |
| bouncyball | pelota que rebota en anillos | 58 | 63 | 88 | 0,5 | 20 % |
| Frox | evolución | 61 | 18 | 21 | **3,1** | **5 %** |

**Mediana: el primer video de 1M llega en el video 27-28, a los 25 días.** El cuartil rápido (Footypoints, FULYON, Fire Rankings, Rival Stats) llegó en menos de 2 semanas o menos de 15 videos.

### Las 5 lecciones que salen de los números
1. **El primer 1M siempre sale del formato que después repiten.** Nadie explotó con un formato y vivió de otro. Por eso elegimos 4-5 formatos fijos y no rotamos 15.
2. **Nombres grandes + debate.** Todos los primeros 1M tienen Messi, Ronaldo, Mbappé, Yamal, un clásico o "¿quién tiene más trofeos?". Ningún primer 1M fue de un jugador de nicho.
3. **Más videos por día no acelera.** Frox subió 3,1 por día y solo el 5 % de sus videos pasó el millón; FULYON (0,7 por día) llegó al 28 %. Con estos datos, 2 por día es el máximo sano.
4. **Duración corta.** La mediana de duración está entre 13 y 41 s, salvo Rival Stats (58 s) y Footrix (41 s). Ellos van más largos porque el cuadro o la cuenta sostienen la tensión.
5. **Calidad visual consistente, no espectacular.** Los canales que más rápido crecieron (FULYON, Fire Rankings) son visualmente simples y limpios. Lo que pesa es la claridad del gancho en el primer segundo.

## 2. Recetas exactas (lo que Gemini vio cuadro por cuadro)

### Footrix · torneo en círculo (3,9 M y 2,6 M)
- **Regla:** 8 participantes, cuartos, semis y final; "FIRST OUT GOES THROUGH".
- **Layout:** título arriba, cuadro de 8 con fotos en el 15-40 %, arena circular con neón en el 40-75 %, ronda y regla abajo.
- **Movimiento:** cámara fija, cortes entre partidos, 60 fps.
- **Sonido:** golpe por rebote, "pop" con chispas al salir y fanfarria con confeti al final.
- **Cierre:** a los 58 s, pantalla de campeón.
- **Lo que Gemini mejoraría:** narración, deformación elástica y sincronía con la música.

### bouncyball · escapar de anillos (86,2 M y 39,5 M)
- **Regla:** una pelota rebota dentro de anillos con un contador que baja.
- **Imagen:** fondo psicodélico, estela de luz que cambia de color.
- **Sonido:** cada rebote es una nota de una melodía. **No hay música de fondo, el sonido son los rebotes.**
- **Duración:** 18-24 s, con cierre abrupto (loop).

### Fire Rankings · carrera de canicas (14,7 M)
- **Imagen:** tubos verdes sobre cielo azul, caras con borde blanco y nombre encima.
- **Movimiento:** la cámara baja lenta siguiendo al grupo.
- **Sonido:** música urbana de moda.
- **Gancho:** "Messi liderando en el segundo 1".
- **Cierre:** sin pantalla final (loop).

### Sphere Stars · laberinto de bolas con banderas (5,9 M)
- Laberinto de neón violeta, bolas con banderas y la Copa del Mundo abajo.
- 22 s, trap de fondo.

### Rival Stats · carrera de trofeos (4,2 M)
- Línea de tiempo horizontal año por año.
- Dos contadores (azul y rojo) y un "clank" por cada trofeo.
- Cierre con el total final (Messi 46, Ronaldo 36).

### MainFutLab · "AI predicts" (5,1 M)
- Año, bandera y escudo arriba, celebración en el centro.
- Cortes al ritmo de phonk a 130 bpm.

### FULYON · FIND (23,4 M)
- Grilla 5x5 numerada y "FIND [JUGADOR]" en amarillo.
- Barra de tiempo de 3,5 s con tic-tac, círculo rojo sobre la respuesta y campana.
- 15 s, 3 rondas.

### DriveLabs · runner (24,3 M y 20,1 M)
- Pista en perspectiva, 3 caras arriba con casilleros "?" que se van llenando y humo entre fases.
- Cierre con "YOU WIN!".
- Requiere avatares 3D o dibujados, así que no lo replicamos.

## 3. Qué hacemos con esto (V2)

| Formato nuestro | Replica a | Qué le sumamos para superarlo |
|---|---|---|
| **CIRCLE CUP V2** | Footrix | Dos arcos con red (es fútbol, no "el primero que sale"), marcador, match point, gol final en cámara lenta, escudos reales, skins de pelota y arco, nota musical por rebote, 60 fps sin temblores |
| **RING ESCAPE** (nuevo) | bouncyball (86 M) | La pelota es un escudo o una cara y escapa de N anillos con el número del anillo. Dos competidores a la vez: "¿quién escapa primero?" (debate en comentarios) |
| **TROPHY RACE** (nuevo) | Rival Stats | Contadores con datos verificados, trofeos que caen, choque de líderes |
| **CARRERAS V2** | Fire Rankings / Sphere Stars | Circuito largo, ganador popular (el 86 % de los top lo hace), escudos reales |
| **FIND / EVOLUTION** | FULYON | Se mantienen, ya replican la receta |

Nota de honestidad: los números de vistas son públicos (API). La "receta" es la descripción que da Gemini y puede tener errores de detalle. Lo validamos mirando nosotros los videos de los canales y no inventamos números.
