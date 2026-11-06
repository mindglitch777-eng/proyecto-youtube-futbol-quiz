#!/usr/bin/env bash
# Sube al repo el estado del pipeline (datos/*.json) combinando con lo que otra corrida haya guardado en paralelo.
python3 "$(dirname "$0")/guardar_avance.py" "${1:-Pipeline}"
