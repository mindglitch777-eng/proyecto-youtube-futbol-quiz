#!/usr/bin/env python3
"""Genera reports/01_canales.md desde data/processed/canales.csv (tablas 100% desde datos)."""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
c = pd.read_csv(ROOT / "data/processed/canales.csv")
q = c[c["clase"].isin(["quiz_puro", "quiz_mixto"])].copy()


def m(n):
    """Formato argentino: 66.816 M, 4,6 M, 982 mil."""
    if n >= 1e8:
        return f"{n/1e6:,.0f} M".replace(",", ".")
    if n >= 1e6:
        return f"{n/1e6:.1f} M".replace(".", ",")
    return f"{n/1e3:.0f} mil"


def tabla(df, extra=None):
    filas = ["| Canal | Creado | Idioma | Subs | Vistas | Videos | Mediana últ. 50 | Por día | % con cara | Formato principal |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for _, r in df.iterrows():
        filas.append(f"| [{r.canal}]({r.url}) | {r.creado[:7]} | {r.idioma_principal} | {m(r.subs or 0)} | {m(r.vistas_totales)} | "
                     f"{r.videos_totales} | {m(r.mediana_vistas_ult or 0)} | {str(r.subidas_por_dia_ult).replace('.', ',')} | "
                     f"{'' if pd.isna(r.pct_con_cara) else f'{r.pct_con_cara:.0%}'} | {r.formato_principal} |")
    return "\n".join(filas)


oficiales = q["canal"].str.contains("LALIGA|UEFA|Bundesliga|FIFA|Premier League|Serie A", case=False)
jov = q[q["joven_12m"] & ~oficiales].sort_values("vistas_por_dia_vida", ascending=False)
sin_cara = jov[jov["pct_con_cara"].fillna(1) <= 0.15]
es = q[(q["idioma_principal"] == "es") & (q["pct_con_cara"].fillna(1) <= 0.2) & ~oficiales].sort_values("mediana_vistas_ult", ascending=False)
top = q[~oficiales].sort_values("vistas_totales", ascending=False)

txt = f"""# 01 · Panorama de canales

**Conclusión:**
1. Los gigantes del nicho ({', '.join(top.canal.head(4))}) son **personas en cámara** (retos, entrevistas). No son copiables con una plantilla.
2. Lo que sí es copiable: **canales sin cara, nacidos en 2026, que llegan a decenas de millones en semanas** con imagen oculta, impostor, tier list y duelo (tabla 2).
3. **En español, los canales sin cara son pocos y chicos** (tabla 3). Ese hueco es la oportunidad.

Datos: {len(c)} canales medidos, de los cuales **{(c.clase=='quiz_puro').sum()} son quiz puro, {(c.clase=='quiz_mixto').sum()} mixtos y {(c.clase=='no_quiz').sum()} no quiz**.
- **Cómo se clasificaron:** Gemini etiquetó el formato de los últimos 50 videos de cada canal según título y tags. Quiz puro = 70% o más quiz; mixto = entre 20% y 70%.
- **Archivo completo:** `data/processed/canales.csv` (país, subs, vistas, ritmo, mejor video, proporción mejor/mediana, % de outliers, etc.).
- **Fuera de estas tablas:** los canales oficiales de ligas (UEFA, LaLiga…).

## 1. Los más grandes (quiz puro o mixto)

{tabla(top.head(12))}

## 2. Jóvenes (creados en los últimos 12 meses) que más rápido crecen

Ordenados por vistas por día de vida del canal.

{tabla(jov.head(15))}

### Solo sin cara (15% o menos de videos con personas)

{tabla(sin_cara.head(12))}

## 3. En español y sin cara

{tabla(es.head(12))}

## Lecturas

- **Proporción mejor/mediana:** en los canales jóvenes el mejor video suele ser **10 a 300 veces** la mediana (columna `mejor_sobre_mediana`). El canal vive de sus outliers.
- **Ritmo:** los jóvenes que más crecen suben **~1 por día** (columna "Por día" de la tabla 2). Más detalle en el reporte 04.
- **Nota sobre "país":** casi ningún canal lo declara (columna `pais` del CSV). Por eso el idioma sale de los títulos.
"""
(ROOT / "reports/01_canales.md").write_text(txt, encoding="utf-8")
print(txt[:3000])
