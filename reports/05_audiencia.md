# 05 · Audiencia, comentarios e interacción

**Conclusión:**
1. La gente **no comenta su respuesta** al quiz: solo el ~3% de los comentarios lo hace. Comentan **chistes sobre el video** (16% tienen risa/emoji) y **rivalidades** (11%: Messi/Ronaldo, Madrid/Barça).
2. El comentario más likeado casi siempre es un **remate gracioso** sobre algo absurdo del video.
3. **Para generar comentarios:** (a) meter un elemento **discutible** ("¿quién es mejor?", un ranking polémico); (b) un **detalle absurdo o gracioso** en el video; (c) **jugadores con hinchada enfrentada** (CR7, Messi, Yamal, Neymar).
4. **Los formatos con más comentarios por vista** son opción múltiple, futbolista de chico, estadio, escudo, imagen oculta e impostor. Los que **menos** comentarios generan: gol/jugada, fichaje, nombrar jugadores y carrera.

Datos: 7.818 comentarios principales de los 80 shorts quiz más vistos (`data/raw/comments.json`, `data/processed/comentarios.csv`), más likes y comentarios de 12.000 shorts quiz (`data/processed/videos.csv`).

## Qué tipo de comentario aparece

Clasificación por palabras clave (aproximada):

| Tipo | % de comentarios |
|---|---|
| Risa / emojis de risa | 16,1% |
| Rivalidad (Messi, Ronaldo, Madrid, Barça, Boca, River…) | 11,0% |
| Responde el quiz (número, letra, "acerté") | 3,1% |
| Dice que fue fácil o difícil | 1,7% |
| Pide parte 2 o un tema | 0,8% |

> Medí también las "correcciones" ("eso está mal"), pero la búsqueda por palabra clave daba falsos positivos ("Ja**mal**"), así que la descarto.

## Interacción por formato (shorts quiz con 10 mil vistas o más)

| Formato | Shorts | Likes cada 1.000 vistas | Comentarios cada 1.000 vistas |
|---|---|---|---|
| Opción múltiple | 297 | 12,0 | **1,52** |
| Futbolista de chico | 77 | 26,0 | 0,80 |
| Estadio | 53 | 23,5 | 0,67 |
| Escudo | 620 | 27,3 | 0,64 |
| Imagen oculta | 1.175 | 12,3 | 0,53 |
| Armar equipo | 770 | 27,4 | 0,49 |
| **Impostor** | 812 | **37,3** | 0,48 |
| Tier list | 527 | 21,8 | 0,40 |
| Duelo | 866 | 18,6 | 0,38 |
| Grilla / "quién jugó con ambos" | 261 | 35,0 | 0,31 |
| Nombrar jugadores (reto) | 878 | 23,9 | 0,25 |
| Gol / jugada | 357 | 14,4 | 0,14 |

- **Opción múltiple** genera muchos comentarios, pero sus vistas son bajas (reporte 02). La gente responde "B", y eso no lo empuja el algoritmo.
- **Impostor y grilla** tienen los likes más altos: el que acierta se siente experto.

## Jugadores que más aparecen en comentarios

Ronaldo (427 menciones), Messi (314), Yamal (277), Neymar (161), Ronaldinho (143), CR7 (102), Haaland (87), Mbappé (61), Di María (46), Dibu (46), Zidane (44).

Para equipos y jugadores por vistas en títulos, ver `data/processed/sujetos.csv` y el reporte 08.

## Comentarios top que muestran el patrón

- "bro got messi and ronaldo as his defenders😭😭" (23 mil likes): un armado de equipo absurdo.
- "Cómo olvidar los 772 goles que marcó CR7 en la liga argentina con Newell's." (18 mil): ironía sobre un error o una pista falsa.
- "Cada que pasaba un jugador de Argentina, pasaba una leyenda de España 🗿" (25 mil): rivalidad entre países.

**Táctica:** en cada short, dejá **un detalle que invite a corregir o a discutir**. Puede ser una opción trampa evidente o un ranking discutible, pero **nunca un dato falso**: la respuesta tiene que estar verificada.
