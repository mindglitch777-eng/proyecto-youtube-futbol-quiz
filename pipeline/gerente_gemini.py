#!/usr/bin/env python3
"""
GERENTE GEMINI (21/11, pedido del CEO: "que no dependamos de Claude y no gastar mis tokens").
Reemplaza al Gerente IA diario (Claude). Corre en GitHub Actions con la clave de Gemini (no usa Claude).
Una vez por semana (lunes) y cuando se lo llama a mano:
1. Junta los números que ya calculan las máquinas (gerente.json, cerebro.json, poda.json, balance.json, dossier.json,
   tareas_ia.json, vivo.json) en un resumen compacto.
2. Gemini escribe el ANÁLISIS (hallazgos con dato, por qué, confianza y acción) y el MENSAJE SEMANAL al CEO, en español
   rioplatense, simple, con números reales (se le prohíbe inventar).
3. Actualiza pipeline/datos/analisis_ia.json (lo que ve el CEO en la página) y abre un Issue "aviso" con el mensaje
   (le llega al celular por la app de GitHub).
No decide cambios grandes: los recomienda. Lo chico ya lo hacen las máquinas (cerebro, poda, vigilancia).
Uso: python3 pipeline/gerente_gemini.py [--sin-issue]
"""
import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone

from comun import CONFIG, RAIZ, cargar, gemini, guardar

ART = timezone(timedelta(hours=-3))
REPO = "mindglitch777-eng/proyecto-youtube-futbol-quiz"

PROMPT = """Sos el gerente de un canal de YouTube Shorts de fútbol sin cara ("Futbol Edition", en inglés). El dueño es el CEO:
quiere monetizar (1.000 suscriptores ya cumplido + 10 millones de vistas de Shorts en 90 días) gastando el mínimo de su tiempo.
Todo lo de rutina lo hacen máquinas (fábrica diaria de 6 videos, publicación, medición, "cerebro" estadístico que reparte
pruebas, poda automática de formatos que no rinden, vigilancia, investigación diaria de canales).

Con los DATOS de abajo (son reales; NO inventes ningún número, si un dato no está decí "sin dato"), escribí en español
rioplatense, simple, sin tecnicismos:

Respondé SOLO un JSON con estas claves:
{{"veredicto": {{"color": "green|amber|red", "titulo": "frase corta con el número clave", "frase": "2 frases: cómo vamos"}},
 "hallazgos": [  // entre 4 y 7, los más importantes primero
   {{"tipo": "funciona|no|ojo", "titulo": "...", "dato": "números concretos", "por_que": "...",
     "confianza": "alta|media|baja (con cuántos videos)", "accion": "qué hace el sistema o qué se recomienda"}}],
 "mensaje_semanal": "mensaje para el CEO, máximo 12 líneas, con: 1) cómo vamos hacia la monetización (números), 2) qué formatos
   funcionaron y cuáles salieron (con números), 3) qué encontró la investigación (la mejor idea), 4) qué tiene que decidir el CEO
   (o 'nada para vos esta semana')",
 "para_el_ingeniero": "UNA tarea concreta para el ingeniero (IA) del lunes: el formato nuevo o arreglo que más valor daría, o 'nada'"}}

Reglas: con menos de 4 videos la confianza es baja. Compará siempre a 48 h y con medianas. Lo nuevo pega más al principio y
después se gasta: hacen falta formatos nuevos seguido. El CEO quiere solo jugadores MUY famosos y la lógica ganadora del canal:
elegir entre superestrellas + parar en el momento justo.

DATOS:
{datos}
"""


def vivo_por_dia():
    r = subprocess.run(["git", "show", "origin/datos-vivos:vivo.json"], capture_output=True, text=True, cwd=RAIZ)
    try:
        cs = json.loads(r.stdout or "{}").get("canal_serie", [])
    except Exception:
        return {}
    dias = {}
    for t, v, s in cs:
        dias[t[:10]] = (v, s)
    ks = sorted(dias)[-9:]
    return {k: dict(vistas=dias[k][0] - dias[a][0], subs=dias[k][1] - dias[a][1]) for a, k in zip(ks, ks[1:])}


def resumen():
    g = cargar("gerente.json", {})
    cer = cargar("cerebro.json", {})
    d = cargar("dossier.json", {})
    activos = {k: v.get("nombre", k) for k, v in CONFIG.get("formatos", {}).items()}
    return dict(
        hoy=datetime.now(ART).date().isoformat(),
        monetizacion=g.get("monetizacion"), norte=g.get("norte"), vistas_y_subs_por_dia=vivo_por_dia(),
        formatos_cerebro={activos.get(k, k): {c: x.get(c) for c in ("mediana_48h", "videos", "confianza", "vistas_48h_esperadas")}
                          for k, x in (cer.get("formatos") or {}).items()},
        cansados=g.get("cansados"), mejores_recientes=[{k: v.get(k) for k in ("tipo", "fecha", "vistas", "horas", "titulo")} for v in g.get("mejores", [])],
        peores_recientes=[{k: v.get(k) for k in ("tipo", "fecha", "vistas", "horas")} for v in g.get("peores", [])],
        poda=cargar("poda.json", {}).get("historial", [])[-6:], originalidad=(g.get("originalidad") or {}).get("indice"),
        balance_quincenal=cargar("balance.json", {}),
        en_prueba=[activos.get(k, k) for k, v in CONFIG.get("pruebas", {}).items() if v.get("listo")],
        estrenos={activos.get(k, k): v.get("estreno_hasta") for k, v in CONFIG.get("pruebas", {}).items() if v.get("listo") and v.get("estreno_hasta")},
        investigacion=dict(fecha=d.get("fecha"), mejores_ideas=[{k: x.get(k) for k in ("nombre_formato", "vistas", "ratio", "encaja_con_nuestra_logica",
                                                                                     "replicable_con_codigo", "idea_para_nosotros")} for x in d.get("ideas", [])[:5]]),
        tareas_pendientes_ia=[t.get("tipo") + ": " + t.get("que", "")[:140] for t in cargar("tareas_ia.json", {}).get("tareas", [])],
    )


def main():
    datos = resumen()
    r = gemini([{"text": PROMPT.format(datos=json.dumps(datos, ensure_ascii=False, indent=1)[:60000])}])
    if isinstance(r, list):
        r = next((x for x in r if isinstance(x, dict)), None)
    if not r or "hallazgos" not in r:
        print("Gemini no devolvió el análisis; no se cambia nada"); sys.exit(1)
    hoy = datos["hoy"]
    A = cargar("analisis_ia.json", {})
    A.update(fecha=hoy, autor="Gerente Gemini (semanal, sin Claude)", veredicto=r.get("veredicto") or A.get("veredicto"),
             hallazgos=r["hallazgos"], acciones=[dict(quien="Ingeniero (lunes)", que=r.get("para_el_ingeniero", "nada"))])
    guardar("analisis_ia.json", A)
    tarea = r.get("para_el_ingeniero", "nada")
    if tarea and tarea.strip().lower() != "nada":                               # el ingeniero del lunes la encuentra en su lista
        t = cargar("tareas_ia.json", {"tareas": []})
        t.setdefault("tareas", []).append(dict(id=f"gemini-{hoy}", prioridad=2, tipo="GERENTE", que=tarea))
        guardar("tareas_ia.json", t)
    msg = r.get("mensaje_semanal", "").strip()
    texto = (f"## Mensaje semanal · {hoy}\n\n{msg}\n\n**Tarea para el ingeniero del lunes:** {tarea}\n\n"
             "_Escrito por el Gerente Gemini (sin Claude). El análisis completo está en la página del canal._\n\n---\n"
             "_Generated by [Claude Code](https://claude.ai/code)_")
    print(texto)
    (RAIZ / "reports" / "gerente" / f"semanal_{hoy}.md").write_text(texto + "\n")
    if "--sin-issue" not in sys.argv:
        subprocess.run(["gh", "api", "-X", "POST", f"repos/{REPO}/issues", "-f", f"title=Mensaje semanal {hoy}",
                        "-f", f"body={texto}", "-f", "labels[]=aviso"], cwd=RAIZ)


if __name__ == "__main__":
    main()
