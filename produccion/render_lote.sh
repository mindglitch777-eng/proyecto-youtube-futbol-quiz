#!/bin/bash
# Renderiza todos los guiones de un lote y arma SUBIR.txt. Uso: GEMINI_API_KEY=... produccion/render_lote.sh lote1
cd "$(dirname "$0")/.."
for g in produccion/guiones/$1_*.json; do
  id=$(basename "$g" .json)
  if [ -f "produccion/salida/$id/short_con_beat.mp4" ]; then echo "$id: ya estaba"; continue; fi
  echo "$id: renderizando"
  python3 produccion/render_fusion.py "$g" 2>&1 | grep -E "listo|Error|rechazada|falló" || true
  python3 produccion/paquete_subida.py "$g" > /dev/null && echo "$id: paquete ok"
done
