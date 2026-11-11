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
