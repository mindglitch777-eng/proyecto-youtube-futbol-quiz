# Errores aprendidos · Futbol Edition

Lo que salió mal, por qué, y qué cambió para que no vuelva a pasar. El Gerente IA lo lee junto con el manual y suma cada error nuevo.

| Fecha | Qué pasó | Por qué | Qué cambió |
|---|---|---|---|
| 07/11 | Se agotó la cuota de la API y el detector de olas dejó datos vacíos | 3 corridas en un día (~7.000 unidades cada una) | El detector reusa datos de menos de 18 h y no pisa datos buenos si la búsqueda vuelve incompleta |
| 07/11 | estado.json quedó roto con marcas de conflicto | Fábrica y publicación escribían a la vez | guardar_avance.py combina por archivo en vez de rebase |
| 07/11 | Títulos raros o cortados ("…Gavi Be honest", "…You w") | La regla anti-repetición pegaba frases sueltas | Variantes completas por formato y auditor antes de subir |
| 08/11 | La investigación se cortó | Gemini devolvió una lista en vez de un objeto | Se acepta lista u objeto |
| 09/11 | No veíamos la ola de FIT (18 videos +1 M) | "FitAll" no coincidía con la palabra "fit" | Clasificación ampliada; revisar a mano el top del radar cuando una familia "otros" crece |
| 09/11 | La página mostraba un radar de hace 8 días | Leía un archivo que ya nadie actualizaba | El radar sale del detector diario y muestra su antigüedad |
| 09/11 | FIT ALL entró promovido a la mejor hora y rindió 1-2,5k | Se promovió por la ola del mercado, sin datos propios | Una ola del mercado justifica PROBAR rápido, no promover; promover requiere ≥4 videos propios |
| 11/11 | La fábrica no corrió | Corte de DNS de los servidores de Ubuntu | Reintentos en la instalación |
| 11/11 | Falsa alarma de "no subidos" | La vigía no sabía que esos horarios ya estaban cubiertos | La vigía descuenta los horarios cubiertos |
| 11/11 | Un recorte de "Ronaldo Nazário" era Cristiano; fotos con marca de agua | Se confió en el nombre del archivo | Revisión a ojo obligatoria + assets/recortes/descartados.json |
| 11/11 | La memoria anti-repetición quedó ilegible (habría frenado TODA la fábrica al día siguiente) | El Ballon d'Or guardaba listas dentro de listas y la carga solo convertía un nivel | Carga recursiva; lección: todo formato nuevo se prueba también cargando la memoria guardada, no solo generando |
| 11/11 | La fábrica de prototipos falló 2 veces al terminar | Mezclaba mensajes de la fábrica con su resultado; no podía guardar con voces nuevas sin guardar | Resultado en archivo aparte y guardado con stash |
| 11/11 | La vigilancia avisó "publicación sin terminar hace 9 h" sin que nada fallara | De noche hay 8 h sin corridas programadas y GitHub atrasa | Límite de 12 h para la publicación |
| 13/11 | El crecimiento cayó a la mitad (70 K → 42 K vistas por día) | Se subieron 9-15 videos por día con extras de formatos sin datos propios, y WHEEL salió 2 veces por día | Vuelta a 6 por día y un solo WHEEL; los extras solo con formatos que ya rindieron en nuestro canal |
| 13/11 | Títulos y ruedas con jugadores secundarios (Cole, Pedri, Gavi) rendían 3 veces menos | El anti-repetición variaba los NOMBRES en vez de variar combinaciones de estrellas | Títulos solo con superestrellas; rueda con 3 estrellas; la variedad sale de combinaciones, cuerpos y ganchos |
| 15/11 | Los 5 videos de reemplazo se hicieron pero no se publicaron | Los formatos nuevos imprimen "loading data from…" al cargar el modelo de caras y el workflow tomaba la última línea como carpeta | El workflow toma solo la línea que empieza con el nombre de carpeta (refuerzo y reserva) |
| 15/11 | Se volvieron a subir 2 videos que el CEO había borrado (y 3 más estaban por subirse) | Claude los marcó como "reemplazado", que en el sistema significa "volver a subir" | Etiqueta nueva "cancelado" que la publicación respeta: nunca se vuelve a subir |
| 15/11 | En WHEEL y HEAD FIT el "PERFECT!" seguía en pantalla cuando ya pasaba otro jugador | Ventana de 0,5 s en ruedas que cambian de pieza cada 0,2 s | Ventana de 0,1 s; regla para todo formato nuevo |
| 15/11 | 4 videos del 17/11 (sin subir) traían defectos ya arreglados: "80 % GOLAZO!" y jugadores secundarios | Se fabricaron a la madrugada, antes de los arreglos del día; un arreglo no toca lo ya fabricado | Cada vez que cambia una regla visual o de jugadores, el Gerente revisa los lotes ya hechos sin subir y los cancela/rehace antes de que salgan |
| 16/11 | La propuesta VS STOP (#14) mostraba una imagen rota | Dos corridas de prototipos renderizaron la misma hoja (p004); al guardar chocaron y se perdió todo el guardado (también la de p005), pero la corrida terminó "bien" | El guardado ahora deja ganar la hoja más nueva y, si no puede guardar, la corrida falla y avisa |
| 16/11 | La originalidad cayó 88 → 68 en 3 días | BALLON D'OR, PENALTY y HEAD SLOT tienen un solo armado visual: con otro jugador el video sale casi igual | Máx. 2 por semana hasta que tengan variantes; a todo formato nuevo se le pide ≥3 variantes visuales que muevan la huella |
| 17/11 | Un título de WHEEL salió "Mbappé vs Vinícius or Vinícius" (lo frenó la hoja de control antes de subirse) | La rueda elegía 3 FOTOS de estrellas al azar y algunos jugadores tienen 2 fotos | Se eligen 3 jugadores distintos y después una foto de cada uno; probado en 400 títulos |
