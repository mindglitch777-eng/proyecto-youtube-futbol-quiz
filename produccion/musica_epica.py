#!/usr/bin/env python3
"""
MÚSICA ORIGINAL (19/11, pedido del CEO: "el audio de siempre está quemado"). Trap cinematográfico generado por código
(sin derechos de terceros): pad de acordes en menor, bajo 808, clap a medio tiempo, hi-hats con redobles y campanita.
Variantes por semilla (tonalidad, progresión, tempo) para que no suene siempre igual.
Uso: musica_epica.pista(dur_s, semilla=0, golpes=[t1, t2...]) -> np.float32 mono [-1, 1] a 44.1 kHz
     (golpes = momentos con impacto: cambio de líder → riser antes y golpe grave encima).
"""
import numpy as np

SR = 44100
PROGRESIONES = [[0, -4, 3, -2], [0, 3, -2, -4], [0, -4, -2, -5], [0, 5, 3, -4]]   # semitonos desde la tónica (menor)


def _lp(x, corte):
    """Pasa bajos de un polo (suave, barato)."""
    a = np.exp(-2 * np.pi * corte / SR)
    y = np.empty_like(x); acc = 0.0
    b = 1 - a
    for i in range(len(x)):
        acc = b * x[i] + a * acc; y[i] = acc
    return y


def _lp_rapido(x, corte):
    # versión vectorizada aproximada (dos pasadas de media móvil) para señales largas
    n = max(1, int(SR / (corte * 2.2)))
    k = np.ones(n, np.float32) / n
    return np.convolve(np.convolve(x, k, "same"), k, "same")


def _saw(f, t):
    return 2 * ((f * t) % 1.0) - 1


def pista(dur, semilla=0, golpes=()):
    rng = np.random.default_rng(semilla)
    bpm = [140, 136, 144, 132][semilla % 4]
    tonica = 45 + [0, 2, -2, 3, 5][semilla % 5]                                 # A2 y vecinas
    prog = PROGRESIONES[semilla % len(PROGRESIONES)]
    n = int(dur * SR); t = np.arange(n) / SR
    beat = 60 / bpm; compas = 4 * beat
    out = np.zeros(n, np.float32)

    def hz(m):
        return 440 * 2 ** ((m - 69) / 12)

    # --- pad: tríada menor/mayor según grado, 3 sierras desafinadas por nota, filtrada, ataque lento
    pad = np.zeros(n, np.float32)
    dur_acorde = 2 * compas
    for k in range(int(dur / dur_acorde) + 1):
        a, b = int(k * dur_acorde * SR), min(n, int((k + 1) * dur_acorde * SR))
        if a >= n:
            break
        raiz = tonica + 12 + prog[k % len(prog)]
        menor = prog[k % len(prog)] in (0, 5)
        notas = [raiz, raiz + (3 if menor else 4), raiz + 7, raiz + 12]
        tt = t[a:b] - t[a]
        seg = np.zeros(b - a, np.float32)
        for m in notas:
            for det in (-0.12, 0.0, 0.11):
                seg += _saw(hz(m + det), tt) * 0.06
        env = np.minimum(1, tt / 0.6) * np.minimum(1, (dur_acorde - tt) / 0.25 + 0.0)
        pad[a:b] += seg * np.clip(env, 0, 1)
    pad = _lp_rapido(pad, 1400)

    # --- 808 + clap + hats
    bajo = np.zeros(n, np.float32); perc = np.zeros(n, np.float32)
    patron_bombo = [0, 0.75, 2.5]                                               # en negras dentro del compás
    for c in range(int(dur / compas) + 1):
        raiz = tonica - 12 + prog[(c // 2) % len(prog)]
        for p in patron_bombo:
            t0 = c * compas + p * beat
            a = int(t0 * SR)
            if a >= n:
                continue
            L = min(n - a, int(0.9 * SR)); tt = np.arange(L) / SR
            f = hz(raiz) * (1 + 1.6 * np.exp(-tt * 38))
            fase = 2 * np.pi * np.cumsum(f) / SR
            bajo[a:a + L] += np.tanh(np.sin(fase) * 2.2) * np.exp(-tt * 2.6) * 0.55
        # clap a medio tiempo (tiempo 3)
        a = int((c * compas + 2 * beat) * SR)
        if a < n:
            L = min(n - a, int(0.25 * SR)); tt = np.arange(L) / SR
            ruido = rng.standard_normal(L).astype(np.float32)
            ruido = ruido - _lp_rapido(ruido, 900)
            perc[a:a + L] += ruido * np.exp(-tt * 22) * 0.32
        # hats en corcheas, redobles de semicorcheas/tresillos al final de cada 2 compases
        pasos = [i * 0.5 for i in range(8)]
        if c % 2 == 1:
            pasos = pasos[:6] + [3.0 + i / 6 for i in range(6)]
        for p in pasos:
            a = int((c * compas + p * beat) * SR)
            if a >= n:
                continue
            L = min(n - a, int(0.05 * SR)); tt = np.arange(L) / SR
            ruido = rng.standard_normal(L).astype(np.float32)
            perc[a:a + L] += (ruido - _lp_rapido(ruido, 5000)) * np.exp(-tt * 70) * 0.10
    # --- campanita (arpegio) cada 2 compases, suave
    campana = np.zeros(n, np.float32)
    for c in range(0, int(dur / compas) + 1, 2):
        raiz = tonica + 24 + prog[(c // 2) % len(prog)]
        for i, m in enumerate([0, 7, 12, 15, 12, 7]):
            a = int((c * compas + i * beat * 0.5 + 4 * beat) * SR)
            if a >= n:
                continue
            L = min(n - a, int(0.6 * SR)); tt = np.arange(L) / SR
            campana[a:a + L] += (np.sin(2 * np.pi * hz(raiz + m) * tt) + 0.3 * np.sin(2 * np.pi * hz(raiz + m) * 3 * tt)) * np.exp(-tt * 6) * 0.07

    # --- intro: primeros 2 compases solo pad + campana (entra la base después)
    entrada = np.clip((t - 2 * compas) / 0.05, 0, 1).astype(np.float32)
    # --- ducking del pad con el bombo (sidechain)
    duck = 1 - 0.45 * np.clip(_lp_rapido(np.abs(bajo), 30) * 3, 0, 1)
    out = pad * duck * 0.9 + campana + (bajo + perc) * entrada

    # --- impactos: riser de ruido 1,5 s antes + golpe grave
    for g in golpes:
        a0, a1 = int(max(0, g - 1.5) * SR), int(g * SR)
        if a1 <= 0 or a0 >= n:
            continue
        L = min(n, a1) - a0; tt = np.arange(L) / SR
        r = rng.standard_normal(L).astype(np.float32)
        r = r - _lp_rapido(r, 1500)
        out[a0:a0 + L] += r * (tt / max(tt[-1], 1e-3)) ** 2 * 0.22
        L2 = min(n - a1, int(1.2 * SR))
        if L2 > 0:
            tt = np.arange(L2) / SR
            f = 55 * (1 + 2 * np.exp(-tt * 25))
            out[a1:a1 + L2] += np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 3) * 0.7
    fin = np.clip((dur - t) / 1.2, 0, 1)
    out *= fin
    return (np.tanh(out * 1.3) * 0.85).astype(np.float32)


if __name__ == "__main__":
    import sys
    import wave
    d = float(sys.argv[1]) if len(sys.argv) > 1 else 20
    x = pista(d, int(sys.argv[2]) if len(sys.argv) > 2 else 0, golpes=[d / 2])
    with wave.open(sys.argv[3] if len(sys.argv) > 3 else "musica_epica.wav", "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((x * 32767).astype(np.int16).tobytes())
