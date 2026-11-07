#!/usr/bin/env python3
"""
AUDITOR ANTES DE SUBIR (09/11): última revisión de cada video justo antes de mandarlo a YouTube (después ya no se puede
editar el título por la API). Arregla solo lo que se puede arreglar sin volver a renderizar:
- hashtags repetidos (#messi #messi) y título > 100 caracteres (corta en una palabra entera, nunca a la mitad);
- título casi igual a uno ya subido en los últimos días (regla 8): cambia los emojis o el par de jugadores secundarios;
- falta el archivo o pesa menos de 200 KB (render roto): no se sube y queda en la vigía.
Devuelve (video_corregido, lista_de_avisos).
"""
import difflib
import random
import re
from pathlib import Path

EMOJIS = ["🔥", "🛑", "😱", "🤯", "💀", "⚽", "😤", "👀", "🎯"]
STOP = ["Football Stop Challenge ⚽🛑 Can you stop {a} at 100%?", "Football Stop Challenge ⚽🛑 Only legends stop {a} 💀",
        "Football Stop Challenge ⚽🛑 99% fail with {a} 😤", "Football Stop Challenge ⚽🛑 Stop {a} before {b} 6️⃣7️⃣",
        "Football Stop Challenge ⚽🛑 Impossible level: {a} vs {b}"]
_EMO = re.compile(r"[🔥🛑😱🤯💀⚽😤👀🎯🐐🏆⏱️]+")


def _norm(t):
    t = re.sub(r"#\w+", "", t.lower())
    return re.sub(r"[^a-z0-9áéíóúñü%' ]+", " ", t).split()


def parecido(a, b):
    return difflib.SequenceMatcher(None, _norm(a), _norm(b)).ratio()


def _armar(base, tags):
    out = base.strip()
    for t in dict.fromkeys(x.lower() for x in tags):
        if len(out) + len(t) + 1 <= 100:
            out += " " + t
    return out


def _cortar(t, n=100):
    if len(t) <= n:
        return t
    return t[:n].rsplit(" ", 1)[0].rstrip(" ,:-·")


def auditar(m, previos, carpeta=None, umbral=0.9):
    avisos = []
    t0 = m["titulo"]
    tags = [w for w in t0.split() if w.startswith("#")]
    base = " ".join(w for w in t0.split() if not w.startswith("#"))
    rng = random.Random(m["id"])
    js = [j for j in m.get("jugadores", []) if isinstance(j, str)]
    estrella = js[0] if js else None
    if m.get("tipo") == "stop" and estrella and estrella.lower() not in base.lower():   # regla 1: la estrella también en el título
        otros = [j for j in js[1:] if j != estrella] or ["Messi"]
        base = rng.choice(STOP).format(a=estrella, b=otros[0])
        avisos.append(f"{m['id']}: el título no nombraba a la estrella ({estrella}), corregido")
    r = re.match(r"Find (.+?)'s real body \S+ (.+?) or (.+?)\?$", base)
    if m.get("tipo") == "rueda" and r and any(parecido(base, p) >= 0.8 for p in previos):  # fórmula del mercado (18-26k vistas)
        base = f"{r[1]} vs {r[2]} or {r[3]} stop challenge " + "".join(rng.sample(["🔥", "🛑", "😱", "🤯", "💀"], 2))
        avisos.append(f"{m['id']}: WHEEL repetido, pasado a la fórmula 'X vs Y or Z'")
    if any(parecido(base, p) >= umbral for p in previos):                     # casi idéntico a uno ya subido
        for _ in range(60):
            nuevo = _EMO.sub("", base).strip() + " " + "".join(rng.sample(EMOJIS, 2))
            if all(parecido(nuevo, p) < umbral for p in previos) or _ == 59:
                base = nuevo; break
        avisos.append(f"{m['id']}: título casi repetido, cambiado")
    titulo = _cortar(_armar(base, tags))
    if titulo != t0:
        m = {**m, "titulo": titulo}
        if not avisos:
            avisos.append(f"{m['id']}: título prolijado ({t0!r} → {titulo!r})")
    if carpeta is not None:
        f = Path(carpeta) / m["archivo"]
        if not f.exists() or f.stat().st_size < 200_000:
            avisos.append(f"{m['id']}: video ausente o roto ({f.stat().st_size if f.exists() else 0} bytes): no se sube")
            m = {**m, "_roto": True}
    return m, avisos


if __name__ == "__main__":                                                   # prueba rápida
    import json, sys
    vids = json.loads(Path(sys.argv[1]).read_text())
    prev = []
    for v in vids:
        w, a = auditar(v, prev); prev.append(w["titulo"])
        print(("✔ " if not a else "✎ ") + w["titulo"], *a, sep="\n   ")
