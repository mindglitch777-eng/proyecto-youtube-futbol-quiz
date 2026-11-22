#!/usr/bin/env python3
"""
MEDICIÓN DE LA PRUEBA "VERSIÓN LIMPIA" (22/11, CEO). Compara, a 48 h, los videos limpios (sin carteles grandes ni cartel final)
contra los normales. Para sacar el efecto del formato, cada video se mide contra la mediana de SU formato (relativo = vistas /
mediana del formato). Decide sola con ≥4 videos por lado y una diferencia clara (≥25 % en la mediana relativa).
Salida: datos/prueba_limpio.json (la lee el parte diario).
"""
import statistics as st

from comun import cargar, guardar


def main():
    rend = {v["id"]: v for v in cargar("rendimiento.json", {}).get("videos", [])}
    an = {v["video"]: v for v in cargar("analytics.json", {}).get("por_video", [])}
    pub = [p for p in cargar("publicados.json", []) if p.get("video_id") and "limpio" in p and p.get("limpio") is not None and not p.get("cancelado")]
    medidos = [(p, rend[p["video_id"]]) for p in pub if p["video_id"] in rend and rend[p["video_id"]].get("horas", 0) >= 48
               and rend[p["video_id"]].get("vistas_48h") is not None]
    todos = [v for v in rend.values() if v.get("vistas_48h") is not None]
    med_fmt = {}
    for v in todos:
        med_fmt.setdefault(v["tipo"], []).append(v["vistas_48h"])
    med_fmt = {k: st.median(x) for k, x in med_fmt.items()}
    lados = {True: [], False: []}
    for p, r in medidos:
        base = med_fmt.get(p["tipo"]) or 1
        a = an.get(p["video_id"], {})
        lados[bool(p["limpio"])].append(dict(rel=r["vistas_48h"] / base, v48=r["vistas_48h"], pct=a.get("averageViewPercentage"),
                                             com=a.get("comments"), tipo=p["tipo"]))
    def resumen(xs):
        if not xs:
            return dict(videos=0)
        pcts = [x["pct"] for x in xs if x["pct"]]
        return dict(videos=len(xs), relativo=round(st.median(x["rel"] for x in xs), 2), mediana_48h=int(st.median(x["v48"] for x in xs)),
                    pct_visto=round(st.median(pcts), 1) if pcts else None, comentarios=sum(x["com"] or 0 for x in xs))
    L, N = resumen(lados[True]), resumen(lados[False])
    veredicto = "en curso"
    if L.get("videos", 0) >= 4 and N.get("videos", 0) >= 4:
        if L["relativo"] >= N["relativo"] * 1.25:
            veredicto = "gana LIMPIA"
        elif N["relativo"] >= L["relativo"] * 1.25:
            veredicto = "gana NORMAL"
        elif L.get("videos", 0) >= 10 and N.get("videos", 0) >= 10:
            veredicto = "empate (no cambia nada)"
    out = dict(limpia=L, normal=N, veredicto=veredicto)
    guardar("prueba_limpio.json", out)
    print(out)
    return out


if __name__ == "__main__":
    main()
