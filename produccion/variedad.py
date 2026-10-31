#!/usr/bin/env python3
"""
VARIEDAD: memoria permanente para que ningún video se repita y todos los formatos roten con criterio.
Se guarda en pipeline/datos/variedad.json y la usa la fábrica cada semana.

Reglas:
- Grupo de jugadores: la misma combinación nunca se repite dentro de un formato (para siempre).
- Protagonista: el mismo jugador no protagoniza dos videos seguidos ni más de 2 veces por día.
- Ganador (PLINKO / HOYO): sale el que menos veces ganó (con empate al azar); nunca el mismo dos veces seguidas.
- Música: rota entre las pistas de moda; la que menos se usó y nunca una de las últimas 3.
- Títulos: plantilla menos usada de su formato; nunca la misma que el video anterior de ese formato.
- Semilla de física/escena: única para siempre (el resultado visual nunca es igual).
"""
import json
from collections import Counter
from pathlib import Path

RUTA = Path(__file__).resolve().parents[1] / "pipeline" / "datos" / "variedad.json"
MUSICAS = ["trallallero_2", "bombardiro_0", "tung_tung_0", "patapim_0", "chipi_chapa_0", "trallallero_1"]


class Variedad:
    def __init__(self, datos=None):
        d = datos or {}
        self.grupos = {k: set(tuple(x) for x in v) for k, v in d.get("grupos", {}).items()}
        self.protas = d.get("protagonistas", [])                     # [[fecha, jugador], ...]
        self.ganadores = Counter(d.get("ganadores", {}))
        self.ult_ganador = d.get("ult_ganador")
        self.musicas = d.get("musicas", [])
        self.titulos = {k: v for k, v in d.get("titulos", {}).items()}
        self.semillas = set(d.get("semillas", []))

    @classmethod
    def cargar(cls):
        return cls(json.loads(RUTA.read_text()) if RUTA.exists() else None)

    def guardar(self):
        RUTA.parent.mkdir(parents=True, exist_ok=True)
        RUTA.write_text(json.dumps(dict(grupos={k: sorted(map(list, v)) for k, v in self.grupos.items()}, protagonistas=self.protas[-400:],
                                        ganadores=dict(self.ganadores), ult_ganador=self.ult_ganador, musicas=self.musicas[-200:],
                                        titulos=self.titulos, semillas=sorted(self.semillas)[-5000:]), ensure_ascii=False, indent=1))

    # ---------------------------------------------------------------- jugadores
    def grupo(self, formato, k, rng, jugadores, fecha=None):
        """k jugadores (tuplas (nombre, clave, peso)) sin repetir combinación en el formato; el primero es el protagonista."""
        usados = self.grupos.setdefault(formato, set())
        ult = self.protas[-1][1] if self.protas else None
        hoy = Counter(p for f, p in self.protas if f == fecha)
        for intento in range(400):
            pool = list(jugadores); out = []
            while len(out) < k:
                j = rng.choices(pool, [w for *_, w in pool])[0]
                pool.remove(j); out.append(j)
            clave = tuple(sorted(n for n, *_ in out))
            prota = out[0][0]
            if clave in usados:
                continue
            if intento < 300 and (prota == ult or hoy[prota] >= 2):
                continue
            usados.add(clave)
            self.protas.append([fecha, prota])
            return out
        raise RuntimeError(f"sin combinaciones nuevas para {formato}")

    def ganador(self, nombres, rng):
        """Índice del ganador: el que menos ganó, nunca el mismo que el video anterior."""
        cand = [i for i, n in enumerate(nombres) if n != self.ult_ganador] or list(range(len(nombres)))
        minimo = min(self.ganadores[nombres[i]] for i in cand)
        i = rng.choice([i for i in cand if self.ganadores[nombres[i]] == minimo])
        self.ganadores[nombres[i]] += 1; self.ult_ganador = nombres[i]
        return i

    def anotar_ganador(self, nombre):
        self.ganadores[nombre] += 1; self.ult_ganador = nombre

    # ---------------------------------------------------------------- música, títulos, semillas
    def musica(self, rng, opciones=MUSICAS):
        uso = Counter(self.musicas)
        cand = [m for m in opciones if m not in self.musicas[-3:]] or list(opciones)
        minimo = min(uso[m] for m in cand)
        m = rng.choice([m for m in cand if uso[m] == minimo])
        self.musicas.append(m)
        return m

    def titulo(self, formato, plantillas, rng):
        uso = self.titulos.setdefault(formato, [])
        c = Counter(uso)
        cand = [i for i in range(len(plantillas)) if not uso or i != uso[-1]] or list(range(len(plantillas)))
        minimo = min(c[i] for i in cand)
        i = rng.choice([i for i in cand if c[i] == minimo])
        uso.append(i); self.titulos[formato] = uso[-100:]
        return plantillas[i]

    def semilla(self, rng):
        while True:
            s = rng.randint(1, 10 ** 6)
            if s not in self.semillas:
                self.semillas.add(s); return s
