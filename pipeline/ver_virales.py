#!/usr/bin/env python3
"""
VER los virales como lo haría una persona: abre cada short en un Chromium común, lo deja reproducir
y graba la pantalla del navegador (video + un cuadro cada 0,5 s). No descarga el archivo de YouTube ni usa
cookies, tokens o proxies: si YouTube pide verificación anti-bot, se frena y lo deja anotado.

Uso: python3 pipeline/ver_virales.py ID1,ID2,...   (o lee datos/ver.json)
Salida: pipeline/datos/vistos/<id>/ (cuadro_XXX.jpg, pantalla.webm, info.json)
"""
import json
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

OUT = Path(__file__).resolve().parent / "datos" / "vistos"
SEGUNDOS = 20
BLOQUEOS = ["confirm you’re not a bot", "confirm you're not a bot", "unusual traffic", "Sign in to confirm"]


def ver(pag, vid):
    d = OUT / vid; d.mkdir(parents=True, exist_ok=True)
    pag.goto(f"https://www.youtube.com/shorts/{vid}", wait_until="domcontentloaded", timeout=60000)
    time.sleep(4)
    html = pag.content()
    if any(b.lower() in html.lower() for b in BLOQUEOS):
        pag.screenshot(path=str(d / "bloqueo.jpg"))
        return dict(id=vid, estado="bloqueado_por_youtube")
    for sel in ["button:has-text('Reject all')", "button:has-text('Accept all')"]:          # aviso de cookies, si aparece
        if pag.locator(sel).count():
            pag.locator(sel).first.click(); time.sleep(2); break
    pag.evaluate("() => { const v = document.querySelector('video'); if (v) { v.muted = true; v.currentTime = 0; v.play(); } }")
    info = pag.evaluate("() => { const v = document.querySelector('video'); return v ? {dur: v.duration, w: v.videoWidth, h: v.videoHeight} : null }")
    if not info:
        pag.screenshot(path=str(d / "sin_video.jpg"))
        return dict(id=vid, estado="sin_video")
    caja = pag.locator("video").first.bounding_box()
    n = 0; t0 = time.time()
    while time.time() - t0 < min(SEGUNDOS, (info["dur"] or SEGUNDOS) + 0.5):
        pag.screenshot(path=str(d / f"cuadro_{n:03d}.jpg"), clip=caja, type="jpeg", quality=80)
        n += 1; time.sleep(0.45)
    t = pag.evaluate("() => document.querySelector('video').currentTime")
    return dict(id=vid, estado="ok", cuadros=n, duracion=info["dur"], tamano=[info["w"], info["h"]], llego_a=t)


def main():
    ids = sys.argv[1].split(",") if len(sys.argv) > 1 else json.loads((OUT.parent / "ver.json").read_text())
    OUT.mkdir(parents=True, exist_ok=True)
    res = []
    with sync_playwright() as p:
        nav = p.chromium.launch(args=["--autoplay-policy=no-user-gesture-required"])
        ctx = nav.new_context(viewport={"width": 540, "height": 960}, locale="en-US",
                              record_video_dir=str(OUT / "_pantalla"), record_video_size={"width": 540, "height": 960})
        pag = ctx.new_page()
        for vid in ids:
            try:
                r = ver(pag, vid.strip())
            except Exception as e:                                             # noqa: BLE001
                r = dict(id=vid, estado="error", detalle=str(e)[:200])
            print(json.dumps(r), flush=True)
            res.append(r)
            if r["estado"] == "bloqueado_por_youtube":
                break                                                          # no insistir
        ctx.close(); nav.close()
    (OUT / "resultado.json").write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
