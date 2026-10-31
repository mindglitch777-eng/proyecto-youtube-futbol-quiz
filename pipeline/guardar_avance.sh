#!/usr/bin/env bash
# Sube al repo el estado del pipeline (datos/*.json) para que el tablero y la próxima corrida lo vean.
git config user.name "github-actions[bot]"
git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
git add pipeline/datos/*.json pipeline/grabaciones 2>/dev/null
git commit -q -m "${1:-Pipeline}: estado" || { echo "sin cambios"; exit 0; }
for i in 1 2 3 4; do git pull --rebase --autostash -q origin "${GITHUB_REF_NAME}" && git push -q origin "HEAD:${GITHUB_REF_NAME}" && break; sleep $((5 * i)); done
