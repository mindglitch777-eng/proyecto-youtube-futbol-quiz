#!/usr/bin/env python3
"""
CEREBRO (Fase 2, 11/11) · máquina SIN IA que decide la grilla con estadística y aprende de cada video.

Qué hace:
1. APRENDE: para cada formato y cada hora calcula cuánto rinde un video a las 48 h (más un plus por suscriptores),
   dándole más peso a lo reciente (vida media 14 días: el público se cansa y las olas pasan).
   Usa estadística bayesiana: con pocos videos el número se "achica" hacia el promedio del canal, así un video
   con suerte no promueve un formato y uno con mala suerte no lo entierra.
2. ELIGE (muestreo de Thompson): cada vez que hay un lugar de PRUEBA, "tira los dados" con lo que sabe de cada formato:
   el que más rinde sale más seguido, pero el que tiene pocos datos también tiene su chance (explora sin desperdiciar).
3. CUIDA LA ORIGINALIDAD: ningún formato pasa del 35 % de los videos de los últimos 7 días (más lo planificado),
   para que el canal no parezca de plantilla (el mayor riesgo para monetizar).
4. PRUEBAS A/B AUTOMÁTICAS (datos/experimentos.json): alterna dos versiones de algo (ej. el STOP difícil vs normal),
   mide las dos a las 48 h y, cuando una gana con ≥90 % de seguridad y ≥4 videos por lado, la declara GANADORA y la
   planificación la usa sola desde ese día. Si en 21 días no hay ganador, queda "empate" y se deja como estaba.
Salida: datos/cerebro.json (lo lee el Gerente IA y el tablero). Uso: python3 cerebro.py (imprime el resumen).
Lo usa e4_plan.py al armar la semana.
"""
import json
import math
import random
from datetime import date, datetime, timedelta, timezone

from comun import cargar, guardar

ART = timezone(timedelta(hours=-3))
VIDA_MEDIA = 14            # días: a esta edad un video pesa la mitad
K_PREVIO = 2.0             # "videos imaginarios" con el promedio del canal (encoge lo que tiene pocos datos)
K_HORA = 3.0
TOPE_ORIGINALIDAD = 0.35   # ningún formato > 35 % de los últimos 7 días + lo planificado
P_GANADOR = 0.90
MIN_POR_BRAZO = 4
DIAS_MAX_EXP = 21
EXPERIMENTOS_INICIALES = [
    dict(id="e1_stop_arranque", tipo="stop", param="arranque", brazos=["grilla", "estrella"],
         pregunta="¿El STOP rinde más arrancando con la grilla de 4 o con zoom a la estrella?"),
    dict(id="e2_stop_hard", tipo="stop", param="hard", brazos=[False, True],
         pregunta="¿El STOP de la noche rinde más en modo HARD (grilla nueva, más difícil) o normal?"),
]


def _hoy():
    return datetime.now(ART).date()


def observaciones():
    """Un registro por video medido a 48 h: tipo, hora, fecha, variante/brazo, y = log(vistas 48 h) + plus de suscriptores."""
    rend = {v["id"]: v for v in cargar("rendimiento.json", {}).get("videos", [])}
    subs = {v["video"]: v.get("subs_cada_1000", 0) or 0 for v in cargar("analytics.json", {}).get("por_video", [])}
    pub = {p["video_id"]: p for p in cargar("publicados.json", []) if p.get("video_id")}
    obs = []
    for vid, r in rend.items():                                                # también los subidos a mano (sin hora conocida)
        if r.get("horas", 0) < 48 or r.get("vistas_48h") is None or not r.get("tipo"):
            continue
        p = pub.get(vid, {})
        fecha = p.get("fecha") or (r.get("publicado") or "")[:10]
        if not fecha:
            continue
        y = math.log(1 + r["vistas_48h"]) + 0.1 * min(5.0, subs.get(vid, 0))
        edad = max(0, (_hoy() - date.fromisoformat(fecha)).days)
        obs.append(dict(tipo=p.get("tipo") or r["tipo"], hora=(p.get("hora") or "")[:5] or None, fecha=fecha, y=y,
                        w=0.5 ** (edad / VIDA_MEDIA), variante=p.get("variante"), exp=p.get("exp"), v48=r["vistas_48h"]))
    return obs


def _post(ys_ws, mu0, s2, k0):
    sw = sum(w for _, w in ys_ws)
    m = (k0 * mu0 + sum(y * w for y, w in ys_ws)) / (k0 + sw)
    return m, s2 / (k0 + sw), sw


def modelo(obs=None):
    """Posterior por formato y efecto por hora (lo que rinde una hora por encima/abajo de lo esperado por su formato)."""
    obs = observaciones() if obs is None else obs
    if not obs:
        return dict(mu0=8.5, s2=1.0, formatos={}, horas={}, n=0)
    sw = sum(o["w"] for o in obs)
    mu0 = sum(o["y"] * o["w"] for o in obs) / sw
    por = {}
    for o in obs:
        por.setdefault(o["tipo"], []).append(o)
    medias = {t: sum(o["y"] * o["w"] for o in xs) / sum(o["w"] for o in xs) for t, xs in por.items()}
    res = [(o["y"] - medias[o["tipo"]]) ** 2 * o["w"] for o in obs]
    s2 = max(0.25, sum(res) / max(1e-9, sw))                                   # varianza dentro de cada formato
    formatos = {}
    for t, xs in por.items():
        m, v, ef = _post([(o["y"], o["w"]) for o in xs], mu0, s2, K_PREVIO)
        formatos[t] = dict(media=m, var=v, videos=len(xs), peso_datos=round(ef, 1),
                           vistas_48h_esperadas=int(math.exp(m)), mediana_48h=sorted(o["v48"] for o in xs)[len(xs) // 2])
    horas = {}
    for o in (o for o in obs if o["hora"]):
        horas.setdefault(o["hora"], []).append((o["y"] - formatos[o["tipo"]]["media"], o["w"]))
    horas = {h: dict(efecto=_post(v, 0.0, s2, K_HORA)[0], videos=len(v)) for h, v in horas.items()}
    return dict(mu0=mu0, s2=s2, formatos=formatos, horas=horas, n=len(obs))


def muestra(M, tipo, rng):
    """Thompson: un valor posible del rendimiento del formato (los que tienen pocos datos varían más = exploran)."""
    f = M["formatos"].get(tipo)
    if not f:
        return rng.gauss(M["mu0"], math.sqrt(M["s2"] / K_PREVIO))
    return rng.gauss(f["media"], math.sqrt(f["var"]))


def efecto_hora(M, hora):
    h = M["horas"].get(hora[:5])
    return h["efecto"] if h else 0.0


def recientes(dias=7):
    """Tipos de los videos de los últimos N días (para el tope de originalidad)."""
    desde = (_hoy() - timedelta(days=dias)).isoformat()
    return [p["tipo"] for p in cargar("publicados.json", []) if p.get("video_id") and p["fecha"] >= desde]


def permite(tipo, previos, planificados, fijo=False):
    """Tope de originalidad: False si el formato ya pasa el 35 % de lo reciente + lo planificado (los fijos no se bloquean)."""
    if fijo:
        return True
    todos = list(previos) + list(planificados)
    return (todos.count(tipo) + 1) / (len(todos) + 1) <= TOPE_ORIGINALIDAD


def elegir(M, candidatos, rng, factor=None, previos=(), planificados=()):
    """El formato de PRUEBA para un lugar: Thompson × factor de olas/investigación, respetando el tope de originalidad."""
    factor = factor or {}
    ok = [k for k in candidatos if permite(k, previos, planificados)] or list(candidatos)
    return max(ok, key=lambda k: muestra(M, k, rng) + math.log(max(0.05, factor.get(k, 1.0))))


# ------------------------------------------------------------------ pruebas A/B
def experimentos():
    ex = cargar("experimentos.json", None)
    if ex is None:
        ex = {"activos": [dict(e, inicio=_hoy().isoformat(), estado="en curso") for e in EXPERIMENTOS_INICIALES], "terminados": []}
        guardar("experimentos.json", ex)
    return ex


def _brazo(o, e):
    if o["tipo"] != e["tipo"]:
        return None
    if o.get("exp") and o["exp"].get("id") == e["id"]:
        return o["exp"]["brazo"]
    if e["param"] == "arranque" and o.get("variante") in e["brazos"]:          # el STOP ya guardaba su arranque: vale la historia
        return o["variante"]
    return None


def evaluar(M=None, obs=None, rng=None):
    """Mide cada prueba A/B; declara ganador (≥90 % y ≥4 videos por lado) o empate a los 21 días. Devuelve el estado."""
    obs = observaciones() if obs is None else obs
    M = M or modelo(obs)
    rng = rng or random.Random(0)
    ex = experimentos()
    seguir = []
    for e in ex["activos"]:
        datos = {json.dumps(b): [] for b in e["brazos"]}
        for o in obs:
            b = _brazo(o, e)
            if b is not None and json.dumps(b) in datos:
                datos[json.dumps(b)].append((o["y"], o["w"]))
        f = M["formatos"].get(e["tipo"], {})
        post = {k: _post(v, f.get("media", M["mu0"]), M["s2"], K_PREVIO) for k, v in datos.items()}
        gana = {k: 0 for k in post}
        for _ in range(4000):
            s = {k: rng.gauss(m, math.sqrt(v)) for k, (m, v, _) in post.items()}
            gana[max(s, key=s.get)] += 1
        e["medicion"] = {k: dict(videos=len(datos[k]), vistas_48h_esperadas=int(math.exp(post[k][0])), p_mejor=round(gana[k] / 4000, 2))
                         for k in post}
        mejor = max(gana, key=gana.get)
        dias = (_hoy() - date.fromisoformat(e["inicio"])).days
        if gana[mejor] / 4000 >= P_GANADOR and all(len(v) >= MIN_POR_BRAZO for v in datos.values()):
            e.update(estado="ganador", ganador=json.loads(mejor), fin=_hoy().isoformat()); ex["terminados"].append(e)
        elif dias >= DIAS_MAX_EXP:
            e.update(estado="empate", ganador=None, fin=_hoy().isoformat()); ex["terminados"].append(e)
        else:
            seguir.append(e)
    ex["activos"] = seguir
    guardar("experimentos.json", ex)
    return ex


def parametros_ganadores(tipo):
    """Lo que ya ganó una prueba A/B para ese formato: {param: valor} (lo aplica e4_plan)."""
    return {e["param"]: e["ganador"] for e in cargar("experimentos.json", {"terminados": []})["terminados"]
            if e["tipo"] == tipo and e.get("estado") == "ganador"}


def brazo_para(tipo, contador):
    """Para un lugar de ese formato: {"param": valor, "exp": {...}} alternando los brazos de la prueba activa (o {})."""
    for e in cargar("experimentos.json", {"activos": []})["activos"]:
        if e["tipo"] == tipo:
            b = e["brazos"][contador % len(e["brazos"])]
            return {e["param"]: b, "exp": dict(id=e["id"], brazo=b)}
    return {}


# ------------------------------------------------------------------ resumen
def main():
    obs = observaciones()
    M = modelo(obs)
    ex = evaluar(M, obs)
    fmt = sorted(M["formatos"].items(), key=lambda kv: -kv[1]["media"])
    rng = random.Random(1)
    sim = {}
    cands = list(M["formatos"])
    for _ in range(2000):
        k = max(cands, key=lambda k: muestra(M, k, rng)) if cands else None
        sim[k] = sim.get(k, 0) + 1
    rec = recientes()
    salida = dict(
        fecha=datetime.now(ART).isoformat(timespec="minutes"), videos_medidos=M["n"],
        formatos={t: dict(vistas_48h_esperadas=f["vistas_48h_esperadas"], mediana_48h=f["mediana_48h"], videos=f["videos"],
                          peso_datos=f["peso_datos"], prob_mejor=round(sim.get(t, 0) / 2000, 2),
                          confianza="alta" if f["peso_datos"] >= 6 else "media" if f["peso_datos"] >= 3 else "baja") for t, f in fmt},
        horas={h: dict(efecto=f"{(math.exp(v['efecto']) - 1) * 100:+.0f}%", videos=v["videos"]) for h, v in sorted(M["horas"].items())},
        originalidad=dict(tope=f"{TOPE_ORIGINALIDAD:.0%}", ultimos_7_dias={t: f"{rec.count(t) / len(rec):.0%}" for t in sorted(set(rec), key=rec.count, reverse=True)} if rec else {}),
        experimentos=dict(activos=[dict(id=e["id"], pregunta=e["pregunta"], medicion=e.get("medicion")) for e in ex["activos"]],
                          terminados=[dict(id=e["id"], estado=e["estado"], ganador=e.get("ganador"), fin=e.get("fin")) for e in ex["terminados"]]),
    )
    meta = cargar("cerebro.json", {}).get("meta") or dict(inicio=_hoy().isoformat(), mediana_48h_inicial=_mediana_semana(obs),
                                                          objetivo="+25 % en 3 semanas con originalidad ≥75")
    salida["meta"] = meta
    salida["meta"]["mediana_48h_ultimos_7_dias"] = _mediana_semana(obs)
    guardar("cerebro.json", salida)
    print(f"CEREBRO · {M['n']} videos medidos")
    for t, f in salida["formatos"].items():
        print(f"  {t:12s} esperado {f['vistas_48h_esperadas']:>7,} · prob. de ser el mejor {f['prob_mejor']:.0%} · confianza {f['confianza']}")
    print("  horas:", ", ".join(f"{h} {v['efecto']}" for h, v in salida["horas"].items()))
    for e in salida["experimentos"]["activos"]:
        print("  A/B", e["id"], e["medicion"])
    return salida


def _mediana_semana(obs):
    desde = (_hoy() - timedelta(days=9)).isoformat()
    xs = sorted(o["v48"] for o in obs if o["fecha"] >= desde)
    return xs[len(xs) // 2] if xs else None


if __name__ == "__main__":
    main()
