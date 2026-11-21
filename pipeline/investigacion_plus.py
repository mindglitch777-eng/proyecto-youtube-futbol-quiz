#!/usr/bin/env python3
"""
INVESTIGACIÓN PLUS (21/11, CEO: "mejorar mucho la investigación, que sea lo que necesitamos"). Sin Claude: código + Gemini.
Corre todos los días después de investigar_canales.py (radar_canales.yml). Cinco piezas:

1. OLAS CONFIRMADAS: una mecánica cuenta como ola solo si aparece en ≥3 CANALES distintos en 7 días (un video suelto puede
   ser suerte). Gemini agrupa los videos fuera de serie analizados por mecánica.
2. POR QUÉ LOS NUESTROS NO EXPLOTAN: para un formato activo por día (rota), Gemini mira nuestro MEJOR y nuestro PEOR video
   (con su retención real de YouTube) y dice qué cambia y qué hacer en el primer segundo.
3. JUGADORES DEL MOMENTO: qué jugadores suman más vistas esta semana en los canales que seguimos (vistas por hora).
4. LO QUE PIDE EL PÚBLICO: comentarios de nuestros videos de los últimos 7 días → Gemini resume pedidos y quejas.
5. LISTA DE IDEAS (datos/ideas.json): todas las ideas con puntaje y estado (idea → propuesta → estreno → fijo / retirado).
   El estado se sincroniza solo con config.json; el ingeniero lee esta lista en vez de investigar desde cero.
Salida: datos/investigacion_plus.json, datos/ideas.json y secciones nuevas en el informe del día (reports/dossier/).
Uso: python3 pipeline/investigacion_plus.py [--sin-gemini]
"""
import json
import re
import sys
from datetime import datetime, timedelta, timezone

import time

from comun import CONFIG, RAIZ, cargar, gemini as _gemini, guardar, yt

FIN = time.time() + 12 * 60                                                   # presupuesto total de Gemini: 12 min


def gemini(partes):
    return _gemini(partes, intentos=1, timeout=150, limite=FIN)

ART = timezone(timedelta(hours=-3))
JUGADORES = {"Messi": r"messi", "Ronaldo": r"ronaldo(?!inho)|cr7|cristiano", "Mbappé": r"mbapp", "Yamal": r"yamal", "Neymar": r"neymar",
             "Vinícius": r"vin[ií]cius|vini jr", "Haaland": r"haaland", "Bellingham": r"bellingham", "Kane": r"\bkane\b", "Salah": r"salah",
             "Lewandowski": r"lewandowski", "Ronaldinho": r"ronaldinho", "Zlatan": r"zlatan|ibrahimovi", "Benzema": r"benzema",
             "Modrić": r"modri", "De Bruyne": r"de bruyne", "Raphinha": r"raphinha", "Pedri": r"pedri", "Musiala": r"musiala",
             "Zidane": r"zidane", "Beckham": r"beckham", "Henry": r"\bhenry\b", "R9": r"\br9\b|nazario|naz[aá]rio",
             "Rodrygo": r"rodrygo", "Güler": r"g[uü]ler", "Olise": r"olise", "Doué": r"dou[eé]", "Dembélé": r"demb[eé]l"}
ESTADOS = ("idea", "propuesta", "estreno", "fijo", "rotacion", "retirado")


def hoy():
    return datetime.now(ART).date()


# ---------------------------------------------------------------- 1. olas confirmadas
def olas_confirmadas(con_gemini):
    vistos = cargar("fuera_de_serie.json", {})
    desde = (hoy() - timedelta(days=7)).isoformat()
    xs = [dict(id=k, canal=x.get("canal_id") or x.get("canal"), nombre=x["analisis"].get("nombre_formato"), mec=x["analisis"].get("mecanica"),
               vistas=x["vistas"], ratio=x["ratio"], encaje=x["analisis"].get("encaja_con_nuestra_logica"),
               codigo=x["analisis"].get("replicable_con_codigo"), futbol=x["analisis"].get("es_futbol", True))
          for k, x in vistos.items() if x.get("fecha", "") >= desde and x.get("analisis")]
    xs = [x for x in xs if x["futbol"] is not False]
    if len(xs) < 3 or not con_gemini:
        return []
    lista = "\n".join(f"{i}. [{x['canal']}] {x['nombre']}: {x['mec']}" for i, x in enumerate(xs))
    r = gemini([{"text": "Agrupá estos videos de YouTube Shorts de fútbol por MECÁNICA (misma idea de juego/edición, aunque cambien los "
                         "jugadores o el título). Respondé SOLO JSON: {\"grupos\": [{\"nombre\": \"nombre corto en inglés\", "
                         "\"mecanica\": \"1 frase en español\", \"indices\": [números]}]}. Cada video en un solo grupo.\n\n" + lista}])
    grupos = (r or {}).get("grupos", []) if isinstance(r, dict) else []
    out = []
    for g in grupos:
        miembros = [xs[i] for i in g.get("indices", []) if isinstance(i, int) and 0 <= i < len(xs)]
        canales = {m["canal"] for m in miembros}
        if not miembros:
            continue
        out.append(dict(nombre=g.get("nombre"), mecanica=g.get("mecanica"), canales=len(canales), videos=len(miembros),
                        vistas=sum(m["vistas"] for m in miembros), confirmada=len(canales) >= 3,
                        encaje=round(sum((m["encaje"] or 0) for m in miembros) / len(miembros), 1),
                        codigo=round(sum((m["codigo"] or 0) for m in miembros) / len(miembros), 1),
                        ejemplos=[f"https://www.youtube.com/shorts/{m['id']}" for m in sorted(miembros, key=lambda m: -m["vistas"])[:3]]))
    return sorted(out, key=lambda o: (-o["confirmada"], -o["canales"], -o["vistas"]))


# ---------------------------------------------------------------- 2. diagnóstico de nuestros formatos
def diagnostico(con_gemini):
    rend = [v for v in cargar("rendimiento.json", {}).get("videos", []) if v.get("horas", 0) >= 48 and v.get("vistas_48h") is not None]
    an = {v["video"]: v for v in cargar("analytics.json", {}).get("por_video", [])}
    activos = [k for k, v in CONFIG["pruebas"].items() if v.get("listo")] + ["rueda", "cabezas"]
    memoria = cargar("investigacion_plus.json", {}).get("diagnosticos", {})
    cand = []
    for k in dict.fromkeys(activos):
        vs = sorted([v for v in rend if v["tipo"] == k], key=lambda v: -v["vistas_48h"])
        if len(vs) >= 3:
            cand.append((memoria.get(k, {}).get("fecha", ""), k, vs[0], vs[-1]))
    if not cand or not con_gemini:
        return memoria
    cand.sort()                                                                 # el que hace más que no se diagnostica
    _, k, mejor, peor = cand[0]

    def ficha(v):
        a = an.get(v["id"], {})
        return f"{v['vistas_48h']:,} vistas a 48 h, {a.get('averageViewPercentage', 's/d')} % visto, {a.get('subs_cada_1000', 's/d')} subs cada 1.000"
    nombre = CONFIG["formatos"].get(k, {}).get("nombre", k)
    r = gemini([{"file_data": {"file_uri": f"https://www.youtube.com/watch?v={mejor['id']}"}},
                {"file_data": {"file_uri": f"https://www.youtube.com/watch?v={peor['id']}"}},
                {"text": f"Son 2 Shorts del MISMO formato de nuestro canal ('{nombre}'). El 1.º es el MEJOR ({ficha(mejor)}); el 2.º el PEOR "
                         f"({ficha(peor)}). Compará cuadro por cuadro qué cambia (jugadores, primer segundo, texto, ritmo, dificultad, final, "
                         "sonido). Respondé SOLO JSON en español: {\"diferencias\": [\"...\"], \"primer_segundo\": \"qué hacer en el cuadro 0\", "
                         "\"cambios\": [\"hasta 3 cambios concretos para la fábrica\"]}"}])
    if isinstance(r, list):
        r = next((x for x in r if isinstance(x, dict)), None)
    if r:
        memoria[k] = dict(fecha=hoy().isoformat(), formato=nombre, mejor=dict(id=mejor["id"], vistas=mejor["vistas_48h"]),
                          peor=dict(id=peor["id"], vistas=peor["vistas_48h"]), **r)
    return memoria


# ---------------------------------------------------------------- 3. jugadores del momento
def jugadores_calientes():
    vids = [v for vs in cargar("canales_videos.json", {}).values() for v in vs]
    tot = {}
    for v in vids:
        t = v["t"].lower()
        for n, pat in JUGADORES.items():
            if re.search(pat, t):
                d = tot.setdefault(n, dict(videos=0, vistas=0, vph=0)); d["videos"] += 1; d["vistas"] += v["v"]; d["vph"] += v["v"] / max(1, v["h"])
    return sorted(({"jugador": n, **{k: int(x) for k, x in d.items()}} for n, d in tot.items()), key=lambda x: -x["vph"])[:12]


# ---------------------------------------------------------------- 4. lo que pide el público
def publico(con_gemini):
    desde = (hoy() - timedelta(days=7)).isoformat()
    pub = [p for p in cargar("publicados.json", []) if p.get("video_id") and p.get("fecha", "") >= desde and p.get("fecha", "") <= hoy().isoformat()
           and not p.get("cancelado")]
    textos = []
    for p in pub[:45]:
        try:
            r = yt("commentThreads", part="snippet", videoId=p["video_id"], maxResults=50, order="relevance", textFormat="plainText")
            textos += [f"[{p['tipo']}] " + it["snippet"]["topLevelComment"]["snippet"]["textDisplay"][:200] for it in r.get("items", [])]
        except Exception:
            continue
    res = dict(comentarios=len(textos))
    if textos and con_gemini:
        r = gemini([{"text": "Comentarios de la última semana de un canal de Shorts de fútbol (entre corchetes, el formato del video). "
                             "Resumí en español. Respondé SOLO JSON: {\"pedidos\": [\"jugadores o desafíos que piden\"], \"quejas\": [\"...\"], "
                             "\"dificultad\": \"¿dicen que es fácil o difícil?\", \"ideas\": [\"ideas de videos que salen de los comentarios\"]}\n\n"
                             + "\n".join(textos[:400])}])
        if isinstance(r, dict):
            res.update(r)
    return res


# ---------------------------------------------------------------- 5. lista de ideas
def lista_ideas(olas):
    ideas = cargar("ideas.json", {})
    d = cargar("dossier.json", {})
    for x in d.get("ideas", []):
        if not x.get("nombre_formato") or (x.get("puntaje") or 0) <= 0:
            continue
        k = re.sub(r"[^a-z0-9]+", "_", x["nombre_formato"].lower()).strip("_")
        i = ideas.setdefault(k, dict(nombre=x["nombre_formato"], estado="idea", desde=d.get("fecha"), puntaje=0, senales=[]))
        i["puntaje"] = max(i.get("puntaje", 0), x["puntaje"])
        i["como"] = x.get("idea_para_nosotros"); i["ejemplo"] = f"https://www.youtube.com/shorts/{x['id']}"
        if x["id"] not in i["senales"]:
            i["senales"].append(x["id"])
    for o in olas:
        if not o.get("nombre"):
            continue
        k = re.sub(r"[^a-z0-9]+", "_", o["nombre"].lower()).strip("_")
        i = ideas.setdefault(k, dict(nombre=o["nombre"], estado="idea", desde=hoy().isoformat(), puntaje=0, senales=[]))
        i.update(ola_canales=o["canales"], ola_confirmada=o["confirmada"], como=i.get("como") or o.get("mecanica"))
        i["puntaje"] = max(i.get("puntaje", 0), round(o["canales"] * 10 * (o["encaje"] or 1) / 5, 1))
    # estado sincronizado con la fábrica (si el ingeniero anotó "formato": "<clave de config>")
    fijos = {"rueda", "cinta", "favorito"}
    for i in ideas.values():
        f = i.get("formato")
        if f and f in CONFIG["pruebas"]:
            v = CONFIG["pruebas"][f]
            i["estado"] = ("fijo" if f in fijos else "estreno" if (v.get("estreno_hasta") or "") >= hoy().isoformat()
                           else "rotacion" if v.get("listo") else "retirado")
    guardar("ideas.json", ideas)
    return sorted(ideas.values(), key=lambda i: (ESTADOS.index(i.get("estado", "idea")) if i.get("estado") in ESTADOS else 0, -i.get("puntaje", 0)))


def main():
    con_gemini = "--sin-gemini" not in sys.argv
    out = cargar("investigacion_plus.json", {})
    try:
        out["olas"] = olas_confirmadas(con_gemini)
    except Exception as e:
        print("olas falló:", e)
    try:
        out["diagnosticos"] = diagnostico(con_gemini)
    except Exception as e:
        print("diagnóstico falló:", e)
    out["jugadores"] = jugadores_calientes()
    try:
        out["publico"] = publico(con_gemini)
    except Exception as e:
        print("público falló:", e)
    ideas = lista_ideas(out.get("olas", []))
    out["fecha"] = hoy().isoformat()
    guardar("investigacion_plus.json", out)
    # secciones nuevas del informe del día
    L = ["", "## Olas confirmadas (misma mecánica en 3 canales o más, 7 días)", ""]
    for o in out.get("olas", [])[:6]:
        L.append(f"- {'✅' if o['confirmada'] else '·'} **{o['nombre']}** · {o['canales']} canales · {o['videos']} videos · {o['vistas']:,} vistas · "
                 f"encaje {o['encaje']}/5 · código {o['codigo']}/5 — {o['mecanica']} ({' '.join(o['ejemplos'][:2])})")
    L += ["", "## Jugadores del momento (vistas por hora en los canales que seguimos)", "",
          " · ".join(f"{j['jugador']} {j['vph']:,}/h ({j['videos']} videos)" for j in out["jugadores"][:10])]
    dg = sorted(out.get("diagnosticos", {}).values(), key=lambda x: x.get("fecha", ""), reverse=True)[:1]
    for x in dg:
        L += ["", f"## Por qué no explota: {x['formato']} (mejor {x['mejor']['vistas']:,} vs peor {x['peor']['vistas']:,})", ""]
        L += [f"- {c}" for c in x.get("cambios", [])] + [f"- Primer segundo: {x.get('primer_segundo')}"]
    pb = out.get("publico", {})
    if pb.get("pedidos") or pb.get("quejas"):
        L += ["", f"## Lo que pide el público ({pb.get('comentarios', 0)} comentarios)", "",
              "- Piden: " + "; ".join(pb.get("pedidos", [])[:6]), "- Quejas: " + "; ".join(pb.get("quejas", [])[:4]),
              f"- Dificultad: {pb.get('dificultad', '')}"]
    L += ["", "## Lista de ideas (para el ingeniero: elegí de acá)", ""]
    for i in ideas[:10]:
        L.append(f"- [{i.get('estado')}] **{i['nombre']}** · puntaje {i.get('puntaje')}"
                 + (f" · ola en {i['ola_canales']} canales" if i.get("ola_canales") else "") + f" — {i.get('como') or ''}")
    f = RAIZ / "reports" / "dossier" / f"dossier_{hoy().isoformat()}.md"
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text((f.read_text() if f.exists() else f"# Informe del día · {hoy().isoformat()}\n") + "\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
