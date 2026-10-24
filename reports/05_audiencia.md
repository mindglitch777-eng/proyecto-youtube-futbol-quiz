# 05 · Audiencia, comentarios e interacción

**Conclusión:**
1. **Depende de si hay persona en cámara.** En los videos con persona casi nadie responde el quiz (3%): comentan **chistes** (18%) y **rivalidades** (12%). **En los quiz sin cara, el 21% de los comentarios responde** ("acerté todas", "la última es Uzbekistán"). El formato sin cara invita a jugar en los comentarios.
2. El comentario más likeado casi siempre es un **remate gracioso** sobre algo absurdo del video.
3. **Para generar comentarios:** (a) meter un elemento **discutible** ("¿quién es mejor?", un ranking polémico); (b) un **detalle absurdo o gracioso** en el video; (c) **jugadores con hinchada enfrentada** (CR7, Messi, Yamal, Neymar).
4. **Los formatos con más comentarios por vista** son opción múltiple, estadio, escudo, armá tu equipo e impostor. Los que **menos** comentarios generan: gol/jugada, fichaje, ordená, tier list y nombrar jugadores.

Datos: 11.579 comentarios principales de 118 shorts quiz (los más vistos y 25 sin cara ganadores) (`data/raw/comments.json`, `data/processed/comentarios.csv`), más likes y comentarios de 17.487 shorts quiz de canales de fútbol (`data/processed/videos.csv`).

## Qué tipo de comentario aparece

Clasificación por palabras clave (aproximada):

| Tipo | Con cara | **Sin cara** |
|---|---|---|
| Responde el quiz (número, letra, "acerté") | 2,8% | **21,3%** |
| Risa / emojis de risa | 18,3% | 13,3% |
| Rivalidad (Messi, Ronaldo, Madrid, Barça, Boca, River…) | 12,0% | 9,2% |
| Dice que fue fácil o difícil | 1,7% | 1,8% |
| Pide parte 2 o más | 0,1% | 0,2% |

> Medí también las "correcciones" ("eso está mal"), pero la búsqueda por palabra clave daba falsos positivos ("Ja**mal**"), así que la descarto.

## Interacción por formato (shorts quiz con 10 mil vistas o más)

| Formato | Shorts | Likes cada 1.000 vistas | Comentarios cada 1.000 vistas |
|---|---|---|---|
| Opción múltiple | 394 | 14,92 | 1,12 |
| Estadio | 52 | 27,45 | 0,70 |
| Escudo | 750 | 26,44 | 0,62 |
| Armá tu equipo | 1216 | 29,20 | 0,48 |
| Impostor | 1054 | 34,06 | 0,44 |
| Preguntas a personas | 867 | 25,53 | 0,44 |
| Futbolista de chico | 124 | 23,82 | 0,43 |
| Verdadero o falso | 274 | 26,74 | 0,43 |
| Imagen oculta | 1646 | 12,57 | 0,42 |
| Emojis | 134 | 25,13 | 0,36 |
| Pistas | 601 | 22,52 | 0,36 |
| Carrera | 427 | 15,54 | 0,36 |
| Grilla / "quién jugó con ambos" | 422 | 28,79 | 0,34 |
| Duelo | 1605 | 19,16 | 0,30 |
| Nombrar jugadores (reto) | 1241 | 21,70 | 0,27 |
| Tier list | 1260 | 21,47 | 0,25 |
| Ordená | 1159 | 22,33 | 0,24 |
| Fichaje | 102 | 26,28 | 0,18 |
| Gol / jugada | 627 | 14,42 | 0,16 |

- **Opción múltiple** genera muchos comentarios, pero sus vistas son bajas (reporte 02). La gente responde "B", y eso no lo empuja el algoritmo.
- **Impostor, armá tu equipo y grilla** tienen los likes más altos (29–34 cada 1.000 vistas): el que acierta se siente experto.

## En los sin cara: qué se comenta

- **Orgullo nacional:** 4 de los 10 comentarios más likeados de los sin cara son de hinchas turcos por Arda Güler o Kenan Yıldız. Meter **un jugador de un país con hinchada muy activa en internet** (Turquía, Marruecos, Argentina, Brasil) dispara comentarios.
- **"Yo acerté todas / aquí los que…":** el que acierta lo grita. Conviene que la **última ronda sea la más difícil** ("solo el 1%") para que haya algo de qué presumir.
- **"Me dolió la de Valverde", "lo del offside":** detalles específicos de una ronda. Cada ronda tiene que tener algo que comentar.

## Jugadores que más aparecen en comentarios

Ronaldo (427 menciones), Messi (314), Yamal (277), Neymar (161), Ronaldinho (143), CR7 (102), Haaland (87), Mbappé (61), Di María (46), Dibu (46), Zidane (44).

Para equipos y jugadores por vistas en títulos, ver `data/processed/sujetos.csv` y el reporte 08.

## Comentarios top que muestran el patrón

- "bro got messi and ronaldo as his defenders😭😭" (23 mil likes): un armado de equipo absurdo.
- "Cómo olvidar los 772 goles que marcó CR7 en la liga argentina con Newell's." (18 mil): ironía sobre un error o una pista falsa.
- "Cada que pasaba un jugador de Argentina, pasaba una leyenda de España 🗿" (25 mil): rivalidad entre países.

**Táctica:** en cada short, dejá **un detalle que invite a corregir o a discutir**. Puede ser una opción trampa evidente o un ranking discutible, pero **nunca un dato falso**: la respuesta tiene que estar verificada.
