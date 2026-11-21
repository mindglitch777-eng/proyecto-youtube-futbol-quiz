#!/usr/bin/env python3
"""
INVESTIGACIÓN 2.0 (19/11, pedido del CEO: investigación específica y eficiente, menos Claude).
Pregunta que responde: ¿QUÉ FORMATO le funciona a canales como el nuestro, esta semana?

1. CANALES SEGUIDOS (datos/canales_seguidos.json): canales de Shorts de fútbol. Leer sus últimos 50 videos cuesta 2 unidades
   de cuota por canal (playlistItems + videos), contra 100 por cada búsqueda: vemos muchos más videos con la misma cuota.
2. DESCUBRIMIENTO: pocas búsquedas generales (7 días). Un canal con un Short de ≥500 K entra solo a la lista; si además es
   NUEVO (<180 días) se marca "nuevo" (son los que más nos enseñan: crecieron de cero, como nosotros).
   Se saca solo de la lista si en 28 días no tuvo ningún video fuera de serie.
3. FUERA DE SERIE: un Short de 1-14 días que hace ≥5x la mediana de SU PROPIO canal (y ≥200 K). Así se ve si el FORMATO
   funciona por sí mismo, no por el tamaño del canal.
4. GEMINI MIRA los mejores fuera de serie nuevos (máx. 12 por corrida, máx. 2 por canal, nunca dos veces el mismo) y escribe:
   mecánica, primer segundo, por qué engancha, si encaja con nuestra lógica (elegir entre superestrellas + parar justo) y si se
   puede hacer con nuestro motor de video (código + recortes).
5. INFORME de 1 página (reports/dossier/dossier_AAAA-MM-DD.md + datos/dossier.json): ideas ordenadas = fuera de serie × encaje.
   Lo lee el agente de los lunes y jueves (en vez de 5 manuales) y lo ve el CEO en la página.
Uso: python3 pipeline/investigar_canales.py [--sin-gemini]
"""
import math
import statistics as st
import sys
from datetime import datetime, timedelta, timezone

from comun import CONFIG, RAIZ, cargar, gemini, guardar, yt, yt_videos
from e1_radar import dur_s

ART = timezone(timedelta(hours=-3))
DESCUBRIR = ["football shorts", "football challenge", "ronaldo messi shorts", "yamal shorts", "football edit", "football game shorts",
             "stop challenge football", "football meme"]
MIN_DESCUBRIR = 500_000          # un Short así mete al canal en la lista
FACTOR = 5                       # fuera de serie = ≥5x la mediana del propio canal
MIN_FUERA = 200_000
MAX_CANALES = 80
MAX_SUBS = 5_000_000             # los canales gigantes (clubes, ligas) no son comparables
MAX_GEMINI = 12

PROMPT = """Sos analista de YouTube Shorts de fútbol. Mirá este Short ("{titulo}", {vistas:,} vistas, {ratio}x la mediana de su canal).
Nuestro canal hace Shorts de fútbol SIN CARA, en inglés, de 6-9 s, hechos 100 % con código (recortes de fotos reales de jugadores
famosos, animación 2D, texto y sonido; no podemos usar clips de partidos ni personas filmadas). Nuestra lógica ganadora: el que mira
ELIGE entre superestrellas y tiene que PARAR/PAUSAR en el momento justo (ruedas, cintas, caras que encajan, etc.).
Respondé SOLO un JSON con estas claves (en español, frases cortas):
{{"es_futbol": true/false (¿el tema central es fútbol o futbolistas?),
 "nombre_formato": "nombre corto en inglés",
 "mecanica": "qué pasa en el video, paso a paso, en 2 frases",
 "primer_segundo": "qué se ve y se lee en el primer segundo",
 "por_que_engancha": "la razón psicológica principal (1 frase)",
 "interaccion": "pausar | adivinar | elegir | comentar | ninguna",
 "jugadores": ["los jugadores que aparecen"],
 "duracion_s": numero,
 "usa_clips_reales": true/false,
 "replicable_con_codigo": 1-5 (5 = se hace fácil con recortes y animación 2D),
 "encaja_con_nuestra_logica": 1-5 (5 = elegir entre superestrellas + parar justo),
 "idea_para_nosotros": "cómo lo haríamos NOSOTROS con nuestra lógica y vuelta propia, sin copiarlo (1-2 frases)"}}"""


def hoy():
    return datetime.now(ART)


def edad_h(iso):
    return max(1.0, (datetime.now(timezone.utc) - datetime.fromisoformat(iso.replace("Z", "+00:00"))).total_seconds() / 3600)


def descubrir(lista):
    """Búsquedas generales de 7 días: canales con un Short grande entran a la lista."""
    desde = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")
    ids = {}
    for q in DESCUBRIR:
        try:
            for it in yt("search", part="snippet", q=q, type="video", videoDuration="short", order="viewCount",
                         publishedAfter=desde, maxResults=50)["items"]:
                ids[it["id"]["videoId"]] = it["snippet"]["channelId"]
        except Exception as e:
            print("búsqueda falló", q, e, flush=True)
    grandes = {}
    for v in yt_videos(list(ids)):
        if int(v["statistics"].get("viewCount", 0)) >= MIN_DESCUBRIR and dur_s(v["contentDetails"]["duration"]) <= 180:
            grandes.setdefault(v["snippet"]["channelId"], []).append(v["id"])
    nuevos = [c for c in grandes if c not in lista and c != CONFIG["canal_id"]]
    print(f"descubrimiento: {len(ids)} videos, {len(grandes)} canales con un Short ≥{MIN_DESCUBRIR:,}, {len(nuevos)} nuevos para la lista", flush=True)
    return nuevos


def info_canales(cids):
    out = {}
    for k in range(0, len(cids), 50):
        for c in yt("channels", part="snippet,statistics,contentDetails", id=",".join(cids[k:k + 50]))["items"]:
            out[c["id"]] = dict(nombre=c["snippet"]["title"], subs=int(c["statistics"].get("subscriberCount", 0) or 0),
                                creado=c["snippet"]["publishedAt"][:10], uploads=c["contentDetails"]["relatedPlaylists"]["uploads"])
    return out


def ultimos(uploads):
    ids = [it["contentDetails"]["videoId"] for it in yt("playlistItems", part="contentDetails", playlistId=uploads, maxResults=50)["items"]]
    vids = []
    for v in yt_videos(ids):
        d = dur_s(v["contentDetails"]["duration"])
        if 0 < d <= 180:
            vids.append(dict(id=v["id"], titulo=v["snippet"]["title"], vistas=int(v["statistics"].get("viewCount", 0)),
                             coment=int(v["statistics"].get("commentCount", 0) or 0), dur=d, horas=edad_h(v["snippet"]["publishedAt"])))
    return vids


def main():
    sin_gemini = "--sin-gemini" in sys.argv
    hoy_s = hoy().date().isoformat()
    lista = cargar("canales_seguidos.json", {})
    for c in descubrir(lista):
        lista[c] = dict(desde=hoy_s, ultimo_fuera=None)
    info = info_canales(list(lista))
    fuera, revisados = [], 0
    recientes_canal = {}                                                       # 21/11: para "jugadores del momento" (investigacion_plus.py)
    for cid, meta in list(lista.items()):
        i = info.get(cid)
        if not i or i["subs"] > MAX_SUBS:
            lista.pop(cid, None); continue
        meta.update(nombre=i["nombre"], subs=i["subs"], creado=i["creado"],
                    nuevo=(hoy().date() - datetime.fromisoformat(i["creado"]).date()).days < 180)
        try:
            vids = ultimos(i["uploads"])
        except Exception as e:
            print("canal falló", i["nombre"], e, flush=True); continue
        revisados += 1
        recientes_canal[cid] = [dict(id=v["id"], t=v["titulo"][:120], v=v["vistas"], h=round(v["horas"])) for v in vids if v["horas"] <= 7 * 24]
        base = [v["vistas"] for v in vids if 72 <= v["horas"] <= 30 * 24]
        if len(base) < 5:
            continue
        med = max(1, st.median(base)); meta["mediana"] = int(med); meta["shorts_por_dia"] = round(sum(1 for v in vids if v["horas"] <= 7 * 24) / 7, 1)
        for v in vids:
            if 24 <= v["horas"] <= 14 * 24 and v["vistas"] >= MIN_FUERA and v["vistas"] >= FACTOR * med:
                fuera.append(dict(v, canal=i["nombre"], canal_id=cid, subs=i["subs"], nuevo=meta["nuevo"], ratio=round(v["vistas"] / med, 1),
                                  horas=round(v["horas"])))
                meta["ultimo_fuera"] = hoy_s
    # limpieza: fuera de la lista los que en 28 días no dieron nada
    for cid, meta in list(lista.items()):
        if (hoy().date() - datetime.fromisoformat(meta.get("ultimo_fuera") or meta["desde"]).date()).days > 28:
            lista.pop(cid)
    if len(lista) > MAX_CANALES:
        orden = sorted(lista, key=lambda c: (lista[c].get("ultimo_fuera") or "", lista[c]["desde"]), reverse=True)
        lista = {c: lista[c] for c in orden[:MAX_CANALES]}
    guardar("canales_seguidos.json", lista)
    guardar("canales_videos.json", recientes_canal)
    fuera.sort(key=lambda v: -(math.log10(v["ratio"]) * math.log10(v["vistas"]) * (1.3 if v["nuevo"] else 1)))
    print(f"canales revisados {revisados} · fuera de serie {len(fuera)}", flush=True)

    vistos = cargar("fuera_de_serie.json", {})
    por_canal = {}
    if not sin_gemini:
        import time
        fin_gemini = time.time() + 14 * 60                                     # 21/11: presupuesto total de Gemini: 14 min
        hechos = 0
        for v in fuera:
            if hechos >= MAX_GEMINI:
                break
            if v["id"] in vistos or por_canal.get(v["canal_id"], 0) >= 2:
                continue
            por_canal[v["canal_id"]] = por_canal.get(v["canal_id"], 0) + 1
            try:
                a = gemini([{"file_data": {"file_uri": f"https://www.youtube.com/watch?v={v['id']}"}},
                            {"text": PROMPT.format(titulo=v["titulo"], vistas=v["vistas"], ratio=v["ratio"])}],
                           intentos=1, timeout=150, limite=fin_gemini)
                if isinstance(a, list):
                    a = next((x for x in a if isinstance(x, dict)), None)
            except Exception as e:
                print("gemini falló", v["id"], e, flush=True); a = None
            if a:
                vistos[v["id"]] = dict(v, analisis=a, fecha=hoy_s); hechos += 1
                print("analizado", v["id"], a.get("nombre_formato"), flush=True)
        # memoria de 60 días
        lim = (hoy().date() - timedelta(days=60)).isoformat()
        vistos = {k: x for k, x in vistos.items() if x["fecha"] >= lim}
        guardar("fuera_de_serie.json", vistos)

    def puntaje(x):
        a = x["analisis"]
        enc = float(a.get("encaja_con_nuestra_logica") or 1); rep = float(a.get("replicable_con_codigo") or 1)
        if a.get("es_futbol") is False:                                       # 19/11: el primer informe trajo videos de motivación (no fútbol)
            return 0.0
        return round(math.log10(max(x["ratio"], 1.1)) * enc * rep * (0.3 if a.get("usa_clips_reales") and rep < 3 else 1), 2)
    sem = (hoy().date() - timedelta(days=7)).isoformat()
    recientes = sorted((dict(x, puntaje=puntaje(x)) for x in vistos.values() if x["fecha"] >= sem), key=lambda x: -x["puntaje"])
    mecs = {}
    for x in recientes:
        k = (x["analisis"].get("interaccion") or "ninguna").lower()
        mecs.setdefault(k, []).append(x["vistas"])
    dossier = dict(fecha=hoy_s, canales_seguidos=len(lista), canales_nuevos=sum(1 for m in lista.values() if m.get("nuevo")),
                   revisados=revisados, fuera_de_serie=len(fuera),
                   interacciones={k: dict(videos=len(v), mediana=int(st.median(v))) for k, v in sorted(mecs.items(), key=lambda kv: -len(kv[1]))},
                   ideas=[dict(id=x["id"], canal=x["canal"], subs=x["subs"], nuevo=x["nuevo"], vistas=x["vistas"], ratio=x["ratio"],
                               puntaje=x["puntaje"], **{k: x["analisis"].get(k) for k in ("nombre_formato", "mecanica", "primer_segundo",
                               "por_que_engancha", "interaccion", "jugadores", "usa_clips_reales", "replicable_con_codigo",
                               "encaja_con_nuestra_logica", "idea_para_nosotros")}) for x in recientes[:15]],
                   sin_analizar=[dict(id=v["id"], canal=v["canal"], vistas=v["vistas"], ratio=v["ratio"], titulo=v["titulo"]) for v in fuera
                                 if v["id"] not in vistos][:10])
    guardar("dossier.json", dossier)
    escribir(dossier)
    return dossier


def escribir(d):
    L = [f"# Informe de la semana · {d['fecha']}", "",
         f"Canales seguidos: **{d['canales_seguidos']}** ({d['canales_nuevos']} nuevos de <6 meses) · revisados {d['revisados']} · "
         f"videos fuera de serie (≥{FACTOR}x su canal, 1-14 días): **{d['fuera_de_serie']}**", "",
         "## Ideas para nosotros (fuera de serie × encaje con nuestra lógica × se puede hacer con código)", ""]
    for i, x in enumerate(d["ideas"][:8], 1):
        L += [f"**{i}. {x['nombre_formato']}** · puntaje {x['puntaje']} · {x['vistas']:,} vistas ({x['ratio']}x su canal) · "
              f"[{x['canal']}](https://www.youtube.com/shorts/{x['id']}){' · canal NUEVO' if x['nuevo'] else ''}",
              f"- Qué pasa: {x['mecanica']}", f"- Primer segundo: {x['primer_segundo']}", f"- Por qué engancha: {x['por_que_engancha']}",
              f"- Encaje {x['encaja_con_nuestra_logica']}/5 · con código {x['replicable_con_codigo']}/5 · interacción: {x['interaccion']}",
              f"- **Cómo lo haríamos:** {x['idea_para_nosotros']}", ""]
    if d["interacciones"]:
        L += ["## Qué tipo de interacción tienen los fuera de serie", "",
              " · ".join(f"{k}: {v['videos']} (mediana {v['mediana']:,})" for k, v in d["interacciones"].items()), ""]
    if d["sin_analizar"]:
        L += ["## Otros fuera de serie (sin analizar)", ""] + [f"- {x['titulo']} · {x['vistas']:,} ({x['ratio']}x) · "
                                                               f"[{x['canal']}](https://www.youtube.com/shorts/{x['id']})" for x in d["sin_analizar"]]
    carpeta = RAIZ / "reports" / "dossier"; carpeta.mkdir(parents=True, exist_ok=True)
    (carpeta / f"dossier_{d['fecha']}.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
