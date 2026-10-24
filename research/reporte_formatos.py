#!/usr/bin/env python3
"""Genera reports/02_formatos.md desde data/processed (tablas 100% desde datos)."""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
P = ROOT / "data/processed"
lift = pd.read_csv(P / "formatos_lift.csv")
lsc = pd.read_csv(P / "formatos_lift_sin_cara.csv").set_index("formato")
v = pd.read_csv(P / "videos.csv")
can = pd.read_csv(P / "canales.csv")
# solo fútbol: canal con >= 50 % de videos de fútbol y sin palabras de otros deportes/juegos en el título
futbol = set(can.loc[can["pct_futbol"].fillna(0) >= .5, "channelId"])
FUT = (r"futbol|fútbol|football|soccer|futebol|player|jugador|jogador|futbolista|footballer|club|escudo|camiseta|"
       r"jersey|messi|ronaldo|cr7|yamal|mbapp|haaland|neymar|madrid|barça|barca|mundial|world cup|copa|gol|⚽|fifa|liga")
OTROS = r"basket|nba|lebron|minecraft|roblox|ipl|cricket|nfl|tennis|f1 |fortnite|anime|pokemon"
v = v[v["channelId"].isin(futbol) & ~v["titulo"].str.contains(OTROS, case=False, regex=True)]
q = v[v["es_quiz"].fillna(False) & v["es_short"] & (v["edad_dias"] <= 365) & v["idioma"].isin(["es", "en", "pt"])]
comp = (q.groupby(["formato", "idioma"]).agg(canales=("channelId", "nunique"), v1M=("vistas", lambda s: int((s >= 1e6).sum())),
                                            med=("vistas", "median"))
        .unstack("idioma").fillna(0).astype(int))
comp.to_csv(P / "competencia_formato_idioma.csv")

NOMBRE = {
    "verdadero_falso": "Verdadero o falso", "imagen_oculta": "Imagen oculta (silueta, pixelado, zoom)",
    "pistas": "Pistas progresivas / ¿quién soy?", "armar_equipo": "Armá tu equipo / elegí uno / ruleta",
    "impostor": "Impostor (el que no pertenece)", "escudo": "Escudo / camiseta / bandera",
    "reto_nombrar": "Nombrá jugadores (reto contrarreloj)", "carrera": "Carrera / trayectoria de clubes",
    "fichaje": "Fichaje / precio", "otro_quiz": "Otros quizzes", "ordenar": "Ordená de mayor a menor",
    "infancia": "Futbolista de chico", "tier_list": "Tier list / ranking de opinión",
    "preguntas_a_personas": "Preguntas a personas (en cámara)", "gol_o_jugada": "Adiviná por gol/jugada (usa clips)",
    "grilla_conexion": "Grilla / quién jugó con ambos", "opcion_multiple": "Opción múltiple A/B/C",
    "datos_curiosos": "Dato curioso (sin pregunta)", "duelo": "Duelo / ¿quién es mejor? / higher-lower",
    "no_quiz_futbol": "(no quiz, fútbol)", "emojis": "Emojis", "no_futbol": "(no fútbol)", "estadio": "Estadio",
}


def k(n):
    return f"{n/1e6:.1f} M".replace(".", ",") if n >= 1e6 else f"{n/1e3:.0f} mil"


def pc(x):
    return f"{x:.0%}"


f1 = ["| Formato | Shorts | Canales | **Rinde vs. el canal** | ≥2× | ≥10× | Mediana de vistas | Rinde sin cara | Duración mediana |",
      "|---|---|---|---|---|---|---|---|---|"]
for _, r in lift.iterrows():
    sc = lsc.loc[r.formato, "lift"] if r.formato in lsc.index else None
    x = lambda n: f"{n:.2f}×".replace(".", ",")
    f1.append(f"| {NOMBRE.get(r.formato, r.formato)} | {r.n} | {r.canales} | **{x(r.lift)}** | {pc(r.pct_2x)} | {pc(r.pct_10x)} | "
              f"{k(r.med)} | {'' if sc is None else x(sc)} | {r.dur:.0f} s |")

f2 = ["| Formato | Canales ES | 1M+ ES | Mediana ES | Canales EN | 1M+ EN | Mediana EN | Canales PT | 1M+ PT |",
      "|---|---|---|---|---|---|---|---|---|"]
for fm in lift.formato:
    if fm not in comp.index or fm.startswith("no_") or fm in ("otro_quiz", "datos_curiosos"):
        continue
    r = comp.loc[fm]
    f2.append(f"| {NOMBRE.get(fm, fm)} | {r[('canales','es')]} | {r[('v1M','es')]} | {k(r[('med','es')])} | {r[('canales','en')]} | "
              f"{r[('v1M','en')]} | {k(r[('med','en')])} | {r[('canales','pt')]} | {r[('v1M','pt')]} |")

# ejemplos: el short más visto de los últimos 12 meses, priorizando sin cara
f3 = ["| Formato | Ejemplo (más visto, últimos 12 meses, sin cara si hay) | Canal | Vistas |", "|---|---|---|---|"]
for fm in lift.formato:
    if fm.startswith("no_") or fm in ("otro_quiz", "datos_curiosos"):
        continue
    s = v[(v.formato == fm) & v.es_short & (v.edad_dias <= 365) & v.titulo.str.contains(FUT, case=False, regex=True)]
    s2 = s[s.cara == False]
    s = (s2 if len(s2) else s).sort_values("vistas", ascending=False)
    for _, r in s.head(2).iterrows():
        t = str(r.titulo).replace("|", "/")[:70]
        f3.append(f"| {NOMBRE.get(fm, fm)} | [{t}]({r.url}) | {r.canal} | {k(r.vistas)} |")

N_CLASIF = f"{int(v.formato.notna().sum()):,}".replace(",", ".")
txt = f"""# 02 · Formatos de quiz

**Conclusión:**
1. **Los formatos que más rinden por encima del promedio de su propio canal:** verdadero o falso, imagen oculta, pistas, armá tu equipo, impostor, escudo, nombrá jugadores y carrera. Todos rinden 1,25 a 1,45 veces lo normal del canal.
2. **Sin cara**, los mejores son carrera, imagen oculta, impostor, nombrá jugadores, armá tu equipo y escudo. **Todos se pueden hacer con plantilla.**
3. **Flojos o saturados:** emojis (0,9×, ningún outlier), duelo, opción múltiple y gol/jugada (este además usa clips, ver reporte 07).
4. **Huecos en español** (rinden bien y hay pocos canales que los hagan): **imagen oculta** (en inglés hay 49 videos de 1 M o más, en español 8), **ordená de mayor a menor** (95 contra 10), **tier list**, **armá tu equipo** y **carrera**.
5. **En español ya funcionan bien:** verdadero o falso (mediana 225 mil, 18 videos de 1 M o más), escudo, nombrá jugadores e impostor.

## Cómo se midió

- **Formato:** Gemini etiquetó cada short leyendo título, tags y descripción (`research/gemini_clasificar.py`, {N_CLASIF} videos de canales de fútbol). Es una etiqueta automática: puede tener errores en casos dudosos.
- **"Rinde vs. el canal":** mediana de (vistas del short ÷ mediana de los últimos 50 del canal). Así se compara el formato **dentro del mismo canal** y no gana el que tiene canales gigantes. **1,40×** quiere decir que ese formato rinde 40% más que lo normal del canal.
- **Base:** shorts subidos por canales de fútbol, últimos 50 de cada uno, con al menos 3 días de antigüedad. **No** los de búsqueda, que están sesgados a lo viral.
- **≥10×:** % de shorts que superan 10 veces la mediana de su canal ("pegaron").

## 1. Rendimiento por formato

{chr(10).join(f1)}

## 2. Competencia por idioma (shorts quiz del último año que encontré)

"Canales" = cuántos canales distintos lo hacen. "1M+" = shorts con 1 M de vistas o más.
⚠️ Sale de búsquedas ordenadas por vistas: mide **dónde hay éxito visible**, no el total de YouTube.

{chr(10).join(f2)}

**Lectura:**
- **Saturado en inglés y con hueco en español:** imagen oculta, ordená, tier list, armá tu equipo, gol/jugada (este no, por los clips).
- **Fuerte en español:** verdadero o falso, escudo, nombrá jugadores, impostor, preguntas a personas (esta con cara).
- **Grilla / "quién jugó con ambos":** pocos canales en los tres idiomas. Es un formato nicho, con muchos likes (reporte 05) pero vistas medias.

## 3. Ejemplos para mirar

{chr(10).join(f3)}

> La lista completa (un short por fila, con formato, vistas, likes y comentarios) está en `data/processed/videos.csv`. Se puede filtrar por `formato`.
"""
(ROOT / "reports/02_formatos.md").write_text(txt, encoding="utf-8")
print(txt[:200])
