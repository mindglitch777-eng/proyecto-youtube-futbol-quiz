#!/usr/bin/env python3
"""
PARTE DIARIO AUTOMÁTICO (19/11, pedido del CEO: menos Claude). Sin IA: arma el parte del día y el semáforo del análisis
con los números que ya calcula gerente.py. Lo llama gerente.py cada vez que corre (varias veces por día, en publicar_diario).
- Si el agente IA (turno de lunes/jueves) escribió el parte HOY, se respeta el suyo; si no, se arma este.
- En analisis_ia.json solo actualiza fecha, veredicto y números clave; los hallazgos los escribe el agente IA una vez por semana.
"""
import json
import subprocess
from datetime import datetime, timedelta, timezone

from comun import CONFIG, RAIZ, cargar, guardar

ART = timezone(timedelta(hours=-3))
REPO = "mindglitch777-eng/proyecto-youtube-futbol-quiz"


def nombre(t):
    return (CONFIG.get("formatos", {}).get(t) or {}).get("nombre", t.upper())


def miles(n):
    return f"{n / 1000:.0f} K" if n >= 10_000 else f"{n:,}".replace(",", ".")


def issues_abiertos():
    try:
        r = subprocess.run(["gh", "api", f"repos/{REPO}/issues?state=open&per_page=50"], capture_output=True, text=True, cwd=RAIZ, timeout=60)
        return [dict(n=i["number"], t=i["title"], et=[x["name"] for x in i.get("labels", [])]) for i in json.loads(r.stdout or "[]")
                if "pull_request" not in i]
    except Exception:
        return None


def armar(G):
    hoy = datetime.now(ART).date().isoformat()
    mon, norte, salud = G.get("monetizacion") or {}, G.get("norte") or {}, G.get("salud") or {}
    subs = mon.get("suscriptores"); vpd = norte.get("vistas_por_dia"); spd = norte.get("subs_por_dia")
    fuertes = norte.get("fuertes_por_dia")
    tit = []
    if subs is not None:
        tit.append(f"{subs} de 1.000 suscriptores" + (f" (faltan {1000 - subs})" if subs < 1000 else " ✅"))
    if vpd:
        tit.append(f"{miles(vpd)} vistas por día" + (f" y +{spd:g} suscriptores por día" if spd is not None else "") + " (promedio de 3 días)")
    titular = " · ".join(tit) or "Parte automático"

    cer = (G.get("cerebro") or {}).get("formatos") or cargar("cerebro.json", {}).get("formatos", {})
    funciona = []
    for v in (G.get("mejores") or [])[:3]:
        funciona.append(f"{nombre(v['tipo'])} del {v['fecha'][8:10]}/{v['fecha'][5:7]} {v['hora']}: {v['vistas']:,} vistas en {v['horas']} h".replace(",", "."))
    top = sorted(((k, x) for k, x in cer.items() if x.get("confianza") in ("media", "alta")), key=lambda kv: -kv[1].get("mediana_48h", 0))[:2]
    if top:
        funciona.append("Los más firmes (cerebro): " + " · ".join(f"{nombre(k)} mediana {x['mediana_48h']:,} ({x['videos']} videos)".replace(",", ".") for k, x in top))
    no = [f"{nombre(c['formato'])} se cansa: sus últimos 4 rinden el {round(100 * c['ultimos4_vs_4anteriores'])} % de los 4 anteriores"
          for c in (G.get("cansados") or [])]
    no += [f"{nombre(v['tipo'])} del {v['fecha'][8:10]}/{v['fecha'][5:7]}: {v['vistas']:,} vistas en {v['horas']} h".replace(",", ".")
           for v in (G.get("peores") or [])[:2]]
    if fuertes is not None and fuertes < norte.get("meta_fuertes", 3):
        no.append(f"Videos de 10 K o más por día: {str(fuertes).replace('.', ',')} (meta {norte.get('meta_fuertes', 3)})")
    pl = G.get("prueba_limpio") or {}
    if pl.get("limpia", {}).get("videos") or pl.get("normal", {}).get("videos"):
        L_, N_ = pl.get("limpia", {}), pl.get("normal", {})
        funciona.append(f"Prueba VERSIÓN LIMPIA: {pl.get('veredicto')} · limpia {L_.get('videos', 0)} videos (x{L_.get('relativo', '-')} su formato, "
                        f"{L_.get('pct_visto', '-')} % visto) vs normal {N_.get('videos', 0)} (x{N_.get('relativo', '-')}, {N_.get('pct_visto', '-')} %)")
    hice = []
    poda = salud.get("poda") or {}
    hice += [f"Poda automática: {nombre(h['formato'])} {h['cambio']} ({h['motivo']})" for h in poda.get("historial", []) if h["fecha"] == hoy]
    vig = cargar("vigilancia.json", {})
    ult = vig.get("ultimo") or {}
    hice += [f"Vigilancia: {a}" for a in (ult.get("acciones") or [])[:3]]
    if not hice:
        hice.append("Fábrica, publicación, medición, cerebro, poda y vigilancia trabajaron solos.")
    problemas = list(ult.get("problemas") or []) + list(salud.get("alerta_problemas") or [])
    iss = issues_abiertos()
    para = []
    if iss is not None:
        for i in iss:
            if "propuesta" in i["et"]:
                para.append(f"Propuesta para decidir: #{i['n']} {i['t']} (respondé sí o no en el Issue)")
            elif any(e in i["et"] for e in ("alerta-sistema", "alerta-subida")):
                problemas.append(f"Alarma abierta: #{i['n']} {i['t']}")
    manana = (datetime.now(ART).date() + timedelta(days=1)).isoformat()
    prog = (salud.get("subidas_programadas") or {}).get(manana)
    if prog is not None and prog < 6:
        problemas.append(f"Mañana hay {prog} videos subidos (deberían ser 6); la publicación completa con la reserva.")
    color = "red" if problemas else ("amber" if para or (fuertes is not None and fuertes < 1) else "green")
    if not para and not problemas:
        para.append("Nada para vos hoy.")
    parte = dict(fecha=hoy, autor="máquina (sin IA)", titular=titular, funciona=funciona, no_funciona=no, hice=hice,
                 para_el_ceo=problemas + para)
    frase = {"red": "Algo necesita atención: " + "; ".join(problemas[:2]),
             "amber": "Todo anda. " + ("Hay algo para que decidas." if para and para[0] != "Nada para vos hoy." else
                                       "Faltan videos de 10 K: la fábrica sigue probando formatos."),
             "green": "Todo anda solo. No tenés que hacer nada hoy."}[color]
    numeros = []
    if subs is not None:
        numeros.append(dict(label="Suscriptores", valor=f"{subs} / 1.000", nota=f"faltan {max(0, 1000 - subs)}"))
    if vpd:
        numeros.append(dict(label="Vistas del canal por día", valor=miles(vpd), nota="promedio de 3 días"))
    if fuertes is not None:
        numeros.append(dict(label="Videos de 10 K por día", valor=f"{fuertes:g}".replace(".", ","), nota="meta 3"))
    if mon.get("vistas_shorts_90d") is not None:
        numeros.append(dict(label="Vistas de Shorts 90 días", valor=f"{mon['vistas_shorts_90d'] / 1e6:.2f} M".replace(".", ","),
                            nota=f"{mon.get('semanas_a_10M') or '-'} semanas a 10 M"))
    return parte, dict(color=color, titulo=titular, frase=frase), numeros


def aplicar(G):
    """Devuelve el parte a guardar en gerente.json y actualiza analisis_ia.json (solo veredicto y números)."""
    hoy = datetime.now(ART).date().isoformat()
    previo = G.get("parte") or {}
    if previo.get("fecha") == hoy and previo.get("autor") != "máquina (sin IA)":
        return previo                                                           # el agente IA ya escribió el de hoy
    parte, veredicto, numeros = armar(G)
    A = cargar("analisis_ia.json", {})
    if A.get("fecha") != hoy or "sin IA" in (A.get("autor") or ""):
        A.update(fecha=hoy, autor="Parte automático (sin IA) · hallazgos del último turno del agente", veredicto=veredicto,
                 numeros_clave=numeros)
        guardar("analisis_ia.json", A)
    return parte


if __name__ == "__main__":
    G = cargar("gerente.json", {})
    print(json.dumps(armar(G), ensure_ascii=False, indent=1))
