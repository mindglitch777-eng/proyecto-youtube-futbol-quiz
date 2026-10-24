#!/usr/bin/env python3
"""Genera SUBIR.txt (título, descripción con créditos CC, hashtags, comentario fijado) para un guion."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
g = json.loads(Path(sys.argv[1]).read_text())
cred = json.loads((ROOT / "assets/fotos/creditos.json").read_text())
out = ROOT / "salida" / g["id"]
nombres = [r["nombre"] for r in g["rondas"]]
creditos = "\n".join(f"- {cred[r['foto']]['jugador']}: \"{cred[r['foto']]['archivo'].removeprefix('File:')}\" by "
                     f"{cred[r['foto']]['autor'] or 'unknown'}, {cred[r['foto']]['licencia']} ({cred[r['foto']]['pagina']}). Edited (distorted)."
                     for r in g["rondas"])
tags = ["#football", "#soccer", "#footballquiz", "#shorts"] + [f"#{n.lower().replace('é', 'e').replace(' ', '')}" for n in nombres[:3]]
txt = f"""=== TÍTULO (elegí uno; hasta 100 caracteres) ===
A) FIND THE REAL {nombres[0].upper()} 🔎 Only 1% get all {len(nombres)}
B) Only 1% can find the REAL {nombres[-1]} 🤯
C) FIND REAL {' '.join(n.upper() for n in nombres)}

=== DESCRIPCIÓN ===
Can you find the real one every round? The last one is only for the 1% 🧠
Comment your score /{len(nombres)} 👇

{' '.join(tags)}

Photo credits (Wikimedia Commons). Images were modified; the modified images are shared under CC BY-SA 4.0:
{creditos}

=== COMENTARIO PARA FIJAR (lo escribís vos apenas sale) ===
Be honest… how many did you get? 👇 {'/'.join(['0', '1', '2', '3', '4'][:len(nombres) + 1])}

=== CÓMO SUBIR (desde el celular) ===
1. Subí "short_solo_efectos.mp4" si vas a agregar un sonido de tendencia, o "short_con_beat.mp4" si no.
2. En el editor de Shorts → "Agregar sonido" → elegí uno en tendencia (phonk / ritmo rápido).
   Bajá el volumen del sonido a ~40% para que se escuchen el tic-tac y el "ding".
3. Pegá título, descripción y hashtags. Audiencia: "No es para niños".
4. Horario: 10:00 o 23:00 (hora Argentina).
5. Cuando salga, fijá el comentario de arriba y respondé los primeros comentarios en la primera hora.
6. A las 48 h anotá en produccion/registro.csv: vistas, % "vieron vs. deslizaron", retención media, comentarios.
"""
(out / "SUBIR.txt").write_text(txt, encoding="utf-8")
print(txt)
