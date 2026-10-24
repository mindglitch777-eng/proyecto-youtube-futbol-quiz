#!/usr/bin/env python3
"""Genera reports/03_anatomia_video.md desde data/processed/anatomia.csv (Gemini mirando cada short)."""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
a = pd.read_csv(ROOT / "data/processed/anatomia.csv")
can = pd.read_csv(ROOT / "data/processed/canales.csv")
fut = set(can.loc[can["pct_futbol"].fillna(0) >= .5, "canal"])
a = a[a["canal"].isin(fut)]
b = lambda s: s.astype(str).str.lower().isin(["true", "1", "1.0"])
a["cara_b"], a["loop_b"], a["cuenta_b"] = b(a["cara"]), b(a["loop"]), b(a["cuenta_regresiva"])
a["clips_b"], a["fotos_b"], a["escudos_b"], a["sub_b"] = b(a["clips_tv"]), b(a["fotos_jugadores"]), b(a["escudos"]), b(a["subtitulos"])
a["com_b"] = b(a["invita_comentar"])
grupos = {"Todos": a, "Sin cara": a[~a["cara_b"]], "Con cara": a[a["cara_b"]]}


def fila(nombre, f):
    out = [nombre]
    for g in grupos.values():
        out.append(f(g))
    return "| " + " | ".join(out) + " |"


q = lambda col, p: (lambda g: f"{g[col].quantile(p):.1f}".replace(".", ",") if len(g) else "")
pct = lambda col: (lambda g: f"{g[col].mean():.0%}" if len(g) else "")
voz = lambda v: (lambda g: f"{g['voz'].astype(str).str.lower().str.contains(v).mean():.0%}" if len(g) else "")
mus = lambda g: f"{(~g['musica'].astype(str).str.lower().str.startswith(('ninguna', 'none', 'nan'))).mean():.0%}" if len(g) else ""
viral = lambda g: f"{g['musica'].astype(str).str.lower().str.contains('viral|tendencia|phonk|trend').mean():.0%}" if len(g) else ""
gt = lambda t: (lambda g: f"{g['gancho_tipo'].astype(str).str.lower().str.contains(t).mean():.0%}" if len(g) else "")

cab = "| | " + " | ".join(f"{k} (n={len(g)})" for k, g in grupos.items()) + " |\n|---|---|---|---|"
t1 = "\n".join([cab,
    fila("Duración mediana (s)", q("duracion_s", .5)), fila("Duración 25–75% (s)", lambda g: f"{g.duracion_s.quantile(.25):.0f}–{g.duracion_s.quantile(.75):.0f}"),
    fila("Fin del gancho, mediana (s)", q("gancho_fin_s", .5)), fila("Tiempo para pensar por pregunta, mediana (s)", q("pensar_s", .5)),
    fila("Preguntas o rondas, mediana", q("n_preguntas", .5)), fila("Cambios de plano, mediana", q("planos", .5)),
    fila("Gancho = pregunta directa", gt("pregunta")), fila("Gancho = desafío (\"solo el 1%\")", gt("desaf")),
    fila("Gancho = acción/sorpresa", gt("acci")),
    fila("Cuenta regresiva", pct("cuenta_b")), fila("Loop (final empalma con el inicio)", pct("loop_b")),
    fila("Voz humana", voz("humana")), fila("Voz IA/TTS", voz("ia")), fila("Sin voz", voz("ninguna")),
    fila("Con música", mus), fila("Música de tendencia/viral/phonk", viral),
    fila("Subtítulos de la voz", pct("sub_b")), fila("Fotos de jugadores", pct("fotos_b")), fila("Escudos o logos", pct("escudos_b")),
    fila("Clips de partidos/TV ⚠️", pct("clips_b")), fila("Invita a comentar", pct("com_b")),
])

s = a[~a["cara_b"]].sort_values("vistas", ascending=False)
ej = ["| Short | Canal | Vistas | Dura | Formato (según Gemini) | Gancho | Pensar | Loop | Música | Clips |", "|---|---|---|---|---|---|---|---|---|---|"]
for _, r in s.head(25).iterrows():
    t = str(r.titulo).replace("|", "/")[:45]
    ej.append(f"| [{t}]({r.url}) | {r.canal} | {r.vistas/1e6:.1f} M | {r.duracion_s:.0f} s | {str(r.formato_gemini)[:60]} | "
              f"{str(r.gancho_texto)[:30]} ({r.gancho_fin_s} s) | {r.pensar_s} s | {'sí' if r.loop_b else 'no'} | {str(r.musica)[:25]} | {'⚠️' if r.clips_b else ''} |")

txt = f"""# 03 · Anatomía del video ganador

**Conclusión: la plantilla ganadora sin cara**
- **15 a 30 s**, con **3 o 4 rondas**.
- **Gancho escrito gigante en el primer segundo**, un desafío como "FIND THE REAL RONALDO" o "NAME THAT PLAYER".
- **3 a 4 s para pensar**, con **cuenta regresiva visible** (número grande más barra que se vacía) y tic-tac.
- **Revelación con sonido de acierto.**
- **Música de tendencia de fondo, casi siempre sin voz.**
- **El final corta al inicio (loop).**

Los videos con cara son más largos (~50–70 s) y viven de la persona: no aplican a tu caso.

Datos: Gemini miró **{len(a)} shorts de fútbol** desde su link (sin descargarlos):
- los 100 shorts quiz más vistos del último año (máximo 3 por canal);
- los 4 mejores de cada canal sin cara que creció rápido.

Detalle por video en `data/processed/anatomia.csv`; respuesta cruda en `data/raw/gemini_shorts/<id>.json`. Script: `research/gemini_shorts.py`.

> ⚠️ Los tiempos son los que reporta Gemini mirando el video: pueden errar en ±1 s y algún dato puede estar mal interpretado. No pude medir cortes con ffmpeg porque YouTube bloquea la descarga (ver README).

## 1. Números clave

{t1}

## 2. Estructura tipo (sin cara, ~20 s)

| Tramo | Segundos | Qué pasa |
|---|---|---|
| Gancho | 0–1 | Texto gigante con el desafío más la primera imagen ya en pantalla. Sin intro ni logo. |
| Ronda 1 | 1–5 | Imagen o pregunta, cuenta regresiva 3-2-1 (número central más barra), tic-tac. |
| Revelación 1 | 5–6 | Nombre o respuesta grande, sonido de acierto (ding), zoom o flash. |
| Rondas 2–4 | 6–18 | Igual, cada vez más difícil ("el último solo el 1%"). |
| Cierre / loop | 18–20 | Corte seco a una imagen que empalma con el inicio, o "¿cuántas acertaste? 👇". Nada de "suscribite" largo. |

## 3. Ejemplos sin cara para mirar (los que más vistas tienen de la muestra)

{chr(10).join(ej)}

## 4. Título, descripción y hashtags

Ver la tabla `titulos` en `data/processed/videos.csv` (columnas `titulo_len`, `titulo_pregunta`, `titulo_emojis`, `titulo_mayus`, `titulo_hashtags`) y el resumen abajo.

{{TITULOS}}
"""
# títulos de shorts quiz de fútbol con >= 1M
v = pd.read_csv(ROOT / "data/processed/videos.csv")
v = v[v["channelId"].isin(set(can.loc[can["pct_futbol"].fillna(0) >= .5, "channelId"])) & v["es_quiz"].fillna(False) & v["es_short"]]
top, resto = v[v.vistas >= 1e6], v[v.vistas < 1e6]
filas = ["| | Shorts quiz de 1 M o más | Resto |", "|---|---|---|"]
for nom, f in [("Largo del título (caracteres, mediana)", lambda d: f"{d.titulo_len.median():.0f}"),
               ("Con signo de pregunta", lambda d: f"{d.titulo_pregunta.mean():.0%}"),
               ("Con al menos 1 emoji", lambda d: f"{(d.titulo_emojis > 0).mean():.0%}"),
               ("% de mayúsculas (mediana)", lambda d: f"{d.titulo_mayus.median():.0%}"),
               ("Con hashtags en el título", lambda d: f"{(d.titulo_hashtags > 0).mean():.0%}"),
               ("Usa #shorts (título o descripción)", lambda d: f"{d.tiene_shorts_tag.mean():.0%}")]:
    filas.append(f"| {nom} | {f(top)} | {f(resto)} |")
txt = txt.replace("{TITULOS}", "\n".join(filas) + f"\n\n(n = {len(top)} shorts de 1 M o más y {len(resto)} del resto.)")
(ROOT / "reports/03_anatomia_video.md").write_text(txt, encoding="utf-8")
print(t1); print("\n".join(filas))
