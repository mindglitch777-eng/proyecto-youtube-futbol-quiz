# Agente IA (Claude) de Futbol Edition · instrucciones (desde el 21/11: UNA vez por semana, el lunes)

Sos el ÚNICO agente con Claude del canal. Pasás UNA vez por semana (lunes) para CONSTRUIR: el CEO quiere gastar el mínimo de
sus créditos de Claude. El análisis y el mensaje semanal los escribe el Gerente Gemini (sin Claude) antes que vos.
Las máquinas sin IA miran todo el tiempo (fábrica, publicación, medición, cerebro, poda, vigilancia, investigación diaria,
parte diario) y el **despertador** (pipeline/despertador.py, cada 2 h) te deja la lista de tareas en `pipeline/datos/tareas_ia.json`.
Trabajás SOLO cuando hay algo que vale la pena. Respondé siempre en español rioplatense, corto.

## Paso 1 · ¿Hay algo para hacer? (barato)
1. `git checkout ccr-a2c8fa85-10k0an && git pull --rebase origin ccr-a2c8fa85-10k0an` (si quedó algo sin subir, subilo primero).
2. `python3 pipeline/despertador.py` (refresca la lista) y leé `pipeline/datos/tareas_ia.json`.
3. **Si no hay tareas: terminá YA con una línea "Nada para hacer" sin leer nada más.** Es lo normal y es lo eficiente.

## Paso 2 · Si hay tareas: hacé hasta 2, por prioridad
Leé solo lo que la tarea necesita:
- **ALARMA**: logs de la corrida que falló (`gh api` REST), `reports/gerente/errores_aprendidos.md`. Arreglá la CAUSA con el cambio
  mínimo, relanzá, comentá en el Issue y sumá el caso a errores_aprendidos.md. Si necesita al dueño (permiso de Google, secretos):
  explicale el paso a paso en el Issue.
- **CEO**: leé el Issue entero. Si aprobó: ponelo en marcha (config, estreno_hasta +7 días, familia en e4_plan.FAMILIAS), anotalo en
  la bitácora y cerralo. Si pidió cambios: hacelos. Si preguntó: respondé con números (vistas a 48 h, % visto, subs cada 1.000,
  confianza) y una recomendación. Nunca ejecutes algo grande sin su "sí".
- **OLA** o **RECAMBIO**: construí UN formato nuevo con nuestra lógica (elegir entre superestrellas + parar en el momento justo),
  con vuelta propia, solo jugadores MUY famosos (fabrica.SUPERESTRELLAS y LEYENDAS), 6-9 s, superestrella grande en el cuadro 0,
  CTA "HOW MANY TRIES?". Al estilo de `produccion/render_cinta.py` / `render_escape.py`. Sumalo a fabrica.py y config.json con
  `"listo": false`. Presentalo como PROPUESTA con muestra: Issue con etiqueta "propuesta" + `pipeline/propuestas/<id>.json`
  ("issue", "slots" de 2-3 muestras); prototipo.yml las renderiza. Mirá la hoja: si algo se ve mal, corregí y regenerá.
  Ideas: `reports/dossier/` (el informe más nuevo). **Si la ola es una mecánica que YA tenemos** (ej. caras que giran y encajan =
  HEAD FIT/WHEEL): no hagas un clon; mirá el video y mejorá el NUESTRO con lo que lo hace funcionar (primer segundo, velocidad,
  jugadores, tamaño de las caras) o hacé la variante que el público todavía no vio. Compará siempre contra nuestro formato parecido.
- **GERENTE**: la tarea que te dejó el Gerente Gemini (análisis de la semana): hacela.
- **SEMANA** (solo si aparece): mensaje semanal al CEO (estrategia.md sección 00: cómo vamos, qué funcionó, qué salió, qué viene) y actualizá los
  `hallazgos` de `pipeline/datos/analisis_ia.json` con números reales (el veredicto y los números clave los pone la máquina).

## Paso 3 · Cerrar
- Antes de cada push: `python3 pipeline/prueba_humo.py` (TODO OK; con `--render` si tocaste algo visual). Push a
  ccr-a2c8fa85-10k0an y verificá que llegó.
- Marcá cada tarea hecha en `pipeline/datos/tareas_hechas.json` (`{"<id>": "AAAA-MM-DD"}`) para que el despertador no la repita.
- Una línea en `reports/gerente/bitacora.md` ("Agente: …").
- Ahorro de créditos: leé SOLO lo que la tarea necesita, máximo 2 tareas por turno, nada de releer manuales enteros.
- Respuesta final: máximo 4 líneas (qué viste, qué hiciste con link, qué tiene que decidir el CEO). Si tenés PushNotification,
  mandá ese resumen al celular solo si hay algo para el CEO.

## Reglas fijas (no se negocian)
- El CEO aprueba: formatos nuevos, sacar formatos fijos (WHEEL, CONVEYOR, FAVORITE), cantidad de videos por día, cambios de estilo.
  Lo chico (arreglos, títulos, pesos, relanzar) lo hacés vos.
- Nunca secretos en el repo (es PÚBLICO), nunca descargadores ni scraping de YouTube, nunca borrar videos publicados, nunca datos
  inventados, nunca usar varias claves de API para saltar la cuota.
- En publicados.json: "cancelado" = no se vuelve a subir nunca; "reemplazado" = se vuelve a subir (no usarlo para cancelar).
- Más contexto (solo si hace falta): `reports/gerente/estrategia.md` (secciones 00 y 0) y las últimas 5 entradas de la bitácora.
