#!/usr/bin/env python3
"""
PRUEBA DE HUMO (Fase 1 · Blindaje, 11/11): corre toda la cadena en seco para que un error de código NO llegue al canal.
📌 Nació del 11/11: la memoria anti-repetición quedó ilegible y habría frenado toda la fábrica al día siguiente.
Revisa: que todo el código compile, que todos los datos se lean, que la memoria anti-repetición se guarde y se vuelva a
leer, que cada formato activo arme su guion y su título, el plan del día, el planificador de subidas y la reserva, los
números del gerente y (con --render) que un video real se renderice y pase el inspector visual.
Corre en GitHub en cada cambio (pruebas.yml) y lo corren el Gerente y el Ingeniero antes de cada push.
Uso: python3 pipeline/prueba_humo.py [--render]      → sale con código 1 si algo falla
"""
import json
import py_compile
import random
import shutil
import sys
import tempfile
import traceback
from datetime import date, timedelta
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "pipeline")); sys.path.insert(0, str(RAIZ / "produccion"))
resultados = []


def prueba(nombre):
    def deco(fn):
        try:
            det = fn()
            resultados.append((True, nombre, det or ""))
        except Exception as e:
            resultados.append((False, nombre, f"{type(e).__name__}: {e}\n{traceback.format_exc(limit=3)}"))
        return fn
    return deco


def main():
    render = "--render" in sys.argv
    datos = RAIZ / "pipeline" / "datos"
    resguardo = Path(tempfile.mkdtemp()) / "datos"
    shutil.copytree(datos, resguardo)                                         # la prueba nunca deja cambios en los datos
    try:
        @prueba("todo el código compila")
        def _():
            fs = list((RAIZ / "pipeline").glob("*.py")) + list((RAIZ / "produccion").glob("*.py"))
            for f in fs:
                py_compile.compile(str(f), doraise=True)
            return f"{len(fs)} archivos"

        @prueba("todos los datos se leen")
        def _():
            for p in datos.glob("*.json"):
                json.loads(p.read_text())
            json.loads((RAIZ / "pipeline" / "config.json").read_text())
            return f"{len(list(datos.glob('*.json')))} archivos"

        @prueba("memoria anti-repetición: guardar y volver a leer")
        def _():
            from variedad import Variedad
            V = Variedad.cargar(); V.guardar(); V2 = Variedad.cargar()
            assert len(V2.grupos) == len(V.grupos)
            return f"{len(V.grupos)} grupos"

        @prueba("cada formato activo arma su guion y su título")
        def _():
            import fabrica
            cfg = json.loads((RAIZ / "pipeline" / "config.json").read_text())
            tipos = ["stop", "rueda", "cabezas"] + [k for k, v in cfg["pruebas"].items() if v.get("listo") and k not in ("rueda", "cabezas")]
            dia = (date.today() + timedelta(days=40)).isoformat()
            slots = [dict(fecha=dia, hora=f"{8 + i % 15:02d}:{(i * 7) % 60:02d}", tipo=t) for i, t in enumerate(tipos)]
            man, _ = fabrica.fabricar(slots, Path(tempfile.mkdtemp()), random.Random(1), prefijo="humo", renderizar=False)
            malos = [m["id"] for m in man if not m.get("titulo") or len(m["titulo"]) > 100]
            assert len(man) == len(tipos) and not malos, f"títulos vacíos o largos: {malos}"
            return ", ".join(tipos)

        @prueba("plan del día")
        def _():
            import e4_plan
            e4_plan.main(date.today() + timedelta(days=40), 1)
            p = json.loads((datos / "plan.json").read_text())
            assert len(p["slots"]) == 6
            return " · ".join(f"{s['hora']} {s['tipo']}" for s in p["slots"])

        @prueba("planificador de subidas y reserva")
        def _():
            import e6_bajar, reserva
            cupo, n = e6_bajar.cupo_24h()
            reserva.huecos([])
            return f"cupo libre {cupo} · reserva {len(reserva.stock())}"

        @prueba("números del gerente + originalidad")
        def _():
            import gerente
            gerente.main()
            return "ok"

        if render:
            @prueba("un video real se renderiza y pasa el inspector visual")
            def _():
                import fabrica, inspector_visual
                d = Path(tempfile.mkdtemp())
                man, err = fabrica.fabricar([dict(fecha=(date.today() + timedelta(days=40)).isoformat(), hora="12:00", tipo="rueda")], d,
                                            random.Random(2), prefijo="humo")
                assert not err and (d / man[0]["archivo"]).exists(), f"no se renderizó: {err}"
                defectos = inspector_visual.inspeccionar(d / man[0]["archivo"], "rueda")
                assert not defectos, f"inspector: {defectos}"
                return man[0]["titulo"]
    finally:
        shutil.rmtree(datos); shutil.copytree(resguardo, datos)
    ok = all(r[0] for r in resultados)
    for bien, nombre, det in resultados:
        print(("✅ " if bien else "❌ ") + nombre + (f" — {det}" if det else ""))
    print("\nRESULTADO:", "TODO OK" if ok else "HAY FALLAS")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
