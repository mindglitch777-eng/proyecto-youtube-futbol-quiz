# Propuestas del Gerente IA

Cada archivo `<id>.json` es una propuesta al CEO. Al hacer push, la máquina `prototipo.yml` renderiza las muestras,
arma la hoja visual en `reports/propuestas/<id>/hoja.jpg`, sube los videos al Release `propuesta-<id>` y comenta en el
Issue (etiqueta `propuesta`) con la imagen y los links. El formato está explicado en `pipeline/prototipo.py`.
