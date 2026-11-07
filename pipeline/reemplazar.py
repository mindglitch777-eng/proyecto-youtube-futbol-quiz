#!/usr/bin/env python3
"""
REEMPLAZAR videos programados (todavía no publicados) por versiones nuevas: los borra de YouTube y los marca como "reemplazado"
en publicados.json, así la subida sube los nuevos de esos días. Necesita el permiso youtube.force-ssl en el token del canal.
Pedido: pipeline/reemplazar.json {"video_ids": [...], "motivo": "..."}. Corre en GitHub (workflow reemplazar.yml).
Seguridad: NUNCA borra un video ya publicado (chequea que siga privado y con publishAt en el futuro).
"""
import json
from datetime import datetime, timezone

import requests

from comun import PIPE, cargar, guardar, token_canal


def main():
    pedido = json.loads((PIPE / "reemplazar.json").read_text())
    tok = token_canal(); h = {"Authorization": f"Bearer {tok}"}
    pub = cargar("publicados.json", [])
    ahora = datetime.now(timezone.utc)
    hechos = []
    for vid in pedido["video_ids"]:
        r = requests.get("https://www.googleapis.com/youtube/v3/videos", params={"part": "status", "id": vid}, headers=h, timeout=60)
        it = (r.json().get("items") or [None])[0] if r.ok else None
        if not it:
            print("no encontrado (quizás ya borrado):", vid); hechos.append(vid); continue
        st_ = it["status"]; pa = st_.get("publishAt")
        if st_.get("privacyStatus") != "private" or not pa or datetime.fromisoformat(pa.replace("Z", "+00:00")) <= ahora:
            print("NO se borra (ya publicado o sin programar):", vid); continue
        d = requests.delete("https://www.googleapis.com/youtube/v3/videos", params={"id": vid}, headers=h, timeout=60)
        print("borrado" if d.status_code == 204 else f"error {d.status_code} {d.text[:200]}", vid, flush=True)
        if d.status_code == 204:
            hechos.append(vid)
    for x in pub:
        if x.get("video_id") in hechos:
            x["reemplazado"] = pedido.get("motivo", "reemplazado"); x["reemplazado_el"] = ahora.isoformat(timespec="seconds")
    guardar("publicados.json", pub)
    print(len(hechos), "reemplazados de", len(pedido["video_ids"]))


if __name__ == "__main__":
    main()
