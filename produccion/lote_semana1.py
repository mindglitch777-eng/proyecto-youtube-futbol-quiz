#!/usr/bin/env python3
"""
Lote de la semana 1: 14 videos "2 PLAYERS, 1 FACE" (2 por día, 10:00 y 23:00 hora Argentina).

Reglas que salen de la investigación (reportes 02-11):
- ronda 1 FÁCIL con megaestrellas (Messi, Ronaldo, Mbappé, Yamal…): el gancho tiene que ganarse en 1 s
- dificultad creciente y última ronda "ONLY 1%" (lo que más comentarios genera: "acerté todas")
- pares con RELACIÓN (rivales, compañeros históricos, leyenda + estrella, misma selección): el "¡ah!" al revelar
- jugadores con hinchadas muy activas (Argentina, Brasil, Turquía, Marruecos, Corea) para disparar comentarios
- Yamal y Mbappé, los que más rinden en inglés (1,48× y 1,44×), aparecen varias veces
- temas variados (contra el "contenido inauténtico"); solo datos verificables (nacionalidad, Balón de Oro, clubes históricos)

Genera produccion/guiones/lote1_XX.json eligiendo fotos con la misma pose (poses.csv) y espejando si hace falta.
"""
import json
import random
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
POSES = pd.read_csv(ROOT / "assets/poses.csv")

# nombre corto en pantalla/voz -> nombre del pedido de fotos
J = {
    "Messi": "Lionel Messi", "Ronaldo": "Cristiano Ronaldo", "Mbappé": "Kylian Mbappé", "Haaland": "Erling Haaland",
    "Yamal": "Lamine Yamal", "Vinícius": "Vinícius Júnior", "Bellingham": "Jude Bellingham", "Neymar": "Neymar",
    "Salah": "Mohamed Salah", "Kane": "Harry Kane", "Raphinha": "Raphinha", "Pedri": "Pedri", "Palmer": "Cole Palmer",
    "Saka": "Bukayo Saka", "Pulisic": "Christian Pulisic", "Ronaldinho": "Ronaldinho", "Zidane": "Zinedine Zidane",
    "Beckham": "David Beckham", "Henry": "Thierry Henry", "Kaká": "Kaká", "Ibrahimović": "Zlatan Ibrahimović",
    "Rooney": "Wayne Rooney", "Gerrard": "Steven Gerrard", "Ramos": "Sergio Ramos", "Modrić": "Luka Modrić",
    "Kroos": "Toni Kroos", "De Bruyne": "Kevin De Bruyne", "Van Dijk": "Virgil van Dijk", "Lewandowski": "Robert Lewandowski",
    "Griezmann": "Antoine Griezmann", "Foden": "Phil Foden", "Rice": "Declan Rice", "Rashford": "Marcus Rashford",
    "Musiala": "Jamal Musiala", "Wirtz": "Florian Wirtz", "Güler": "Arda Güler", "Hakimi": "Achraf Hakimi",
    "Valverde": "Federico Valverde", "Julián": "Julián Álvarez", "Lautaro": "Lautaro Martínez", "Di María": "Ángel Di María",
    "Dibu": "Emiliano Martínez", "Son": "Son Heung-min", "Ødegaard": "Martin Ødegaard", "Rodrygo": "Rodrygo", "Gavi": "Gavi",
    "Dembélé": "Ousmane Dembélé", "Kvaratskhelia": "Khvicha Kvaratskhelia", "McKennie": "Weston McKennie", "Bale": "Gareth Bale",
    "Benzema": "Karim Benzema", "Dybala": "Paulo Dybala",
}

# (id, día y hora, tema, titulos, pares [(a, b), ...] en orden de dificultad, voz de apertura, comentario fijado)
LOTE = [
    ("01", "dom 25-oct 10:00", "Barça vs Madrid icons (día del Clásico)",
     ["BARÇA vs MADRID in ONE face 🤯 Name both!", "Clásico icons FUSED ⚽ Only 1% get 8/8", "Messi + Ronaldo = ? 😳"],
     [("Messi", "Ronaldo"), ("Ronaldinho", "Zidane"), ("Neymar", "Benzema"), ("Henry", "Ramos")],
     "Barça and Madrid icons, fused. Name BOTH players!", "Clásico day 🔥 what's your score /8? Barça or Madrid fan? 👇"),
    ("02", "dom 25-oct 23:00", "Argentina vs Brasil",
     ["ARGENTINA vs BRAZIL in ONE face 🇦🇷🇧🇷", "Can you name BOTH? Argentina x Brazil 🤯", "Messi + Neymar = ? 😳"],
     [("Messi", "Neymar"), ("Di María", "Rodrygo"), ("Lautaro", "Vinícius")],
     "Argentina meets Brazil. Only one percent name all six!", "Argentina or Brazil fans… who scored higher? /6 👇"),
    ("03", "lun 26-oct 10:00", "Ganadores del Balón de Oro (día de la ceremonia)",
     ["BALLON D'OR WINNERS fused 🏆 Name both!", "2 Ballon d'Or winners, 1 face 🤯", "Only 1% name these Ballon d'Or legends"],
     [("Ronaldo", "Benzema"), ("Messi", "Zidane"), ("Ronaldinho", "Dembélé")],
     "Ballon d'Or winners, fused together. Name both!", "Ballon d'Or night 🏆 your score /6? 👇"),
    ("04", "lun 26-oct 23:00", "Premier League",
     ["PREMIER LEAGUE stars in ONE face 🤯", "Name BOTH Premier League players ⚽", "Salah + Haaland = ? 😳"],
     [("Salah", "Haaland"), ("Saka", "De Bruyne"), ("Foden", "Rice"), ("Ødegaard", "Son")],
     "Premier League stars, one face. Name both!", "Real Premier League fans get 8/8… did you? 👇"),
    ("05", "mar 27-oct 10:00", "Inglaterra: leyendas + estrellas",
     ["ENGLAND legends + stars FUSED 🏴", "Only real England fans get 8/8", "Kane + Beckham = ? 😳"],
     [("Kane", "Beckham"), ("Bellingham", "Rooney"), ("Saka", "Gerrard"), ("Rice", "Rashford")],
     "England legends fused with today's stars. Name both!", "England fans, be honest: score /8? 👇"),
    ("06", "mar 27-oct 23:00", "Jóvenes estrellas",
     ["YOUNG STARS in ONE face 🤯 Name both", "Yamal + ? Only 1% know", "The future of football… fused 😳"],
     [("Yamal", "Bellingham"), ("Musiala", "Wirtz"), ("Pedri", "Kvaratskhelia")],
     "The best young players in the world, fused. Name both!", "Who's the best young player? And your score /6 👇"),
    ("07", "mié 28-oct 10:00", "Francia",
     ["FRANCE stars in ONE face 🇫🇷", "Mbappé + ? Name both!", "Only real France fans get 6/6"],
     [("Mbappé", "Griezmann"), ("Zidane", "Henry"), ("Dembélé", "Benzema")],
     "France legends and stars, fused. Name both!", "Allez les Bleus 🇫🇷 score /6? 👇"),
    ("08", "mié 28-oct 23:00", "Delanteros",
     ["STRIKERS fused 🎯 Name BOTH", "Haaland + Kane = ? 😳", "Only 1% name all 6 strikers"],
     [("Haaland", "Kane"), ("Lewandowski", "Ibrahimović"), ("Lautaro", "Benzema")],
     "Elite strikers, fused into one face. Name both!", "Best striker of the 6? And your score 👇"),
    ("09", "jue 29-oct 10:00", "España vs Alemania",
     ["SPAIN vs GERMANY in ONE face 🇪🇸🇩🇪", "Yamal + ? Name both!", "Only 1% get 6/6"],
     [("Yamal", "Musiala"), ("Pedri", "Kroos"), ("Ramos", "Wirtz")],
     "Spain meets Germany. Name both players!", "Spain or Germany? Score /6 👇"),
    ("10", "jue 29-oct 23:00", "Messi o Ronaldo + ¿quién?",
     ["MESSI + ? Only 1% know 😳", "Ronaldo fused with WHO? 🤯", "Messi or Ronaldo + ? Name both"],
     [("Messi", "Yamal"), ("Ronaldo", "Mbappé"), ("Messi", "Di María"), ("Ronaldo", "Bale")],
     "Messi or Ronaldo… fused with who? Name both!", "Team Messi or Team Ronaldo? Score /8 👇"),
    ("11", "vie 30-oct 10:00", "Leyendas",
     ["LEGENDS in ONE face 👑 Name both", "Only 90s kids get 8/8", "Beckham + Henry = ? 😳"],
     [("Beckham", "Henry"), ("Rooney", "Ibrahimović"), ("Gerrard", "Bale"), ("Ramos", "Di María")],
     "Football legends, fused. Name both!", "Which legend was the best? Score /8 👇"),
    ("12", "vie 30-oct 23:00", "Hinchadas de todo el mundo",
     ["ONLY REAL FANS name both 🌍", "Salah + Hakimi = ? 😳", "Your country's star is here… find him"],
     [("Salah", "Hakimi"), ("Son", "Kvaratskhelia"), ("Lewandowski", "Ødegaard"), ("Valverde", "Pulisic")],
     "Superstars from around the world, fused. Name both!", "Drop your country flag + score /8 👇"),
    ("13", "sáb 31-oct 10:00", "Mediocampistas",
     ["MIDFIELD MAESTROS fused 🧠", "Kroos + De Bruyne = ? 😳", "Only 1% name all 8 midfielders"],
     [("Kroos", "De Bruyne"), ("Pedri", "Valverde"), ("Rice", "Musiala"), ("Bellingham", "Foden")],
     "The best midfielders, fused. Name both!", "Best midfielder ever? And your score /8 👇"),
    ("14", "sáb 31-oct 23:00", "Modo imposible",
     ["IMPOSSIBLE fusion quiz 💀 nobody gets 8/8", "This is the HARDEST one 😳", "Only 0.1% name all 8"],
     [("Yamal", "Mbappé"), ("Pulisic", "Wirtz"), ("Haaland", "Lewandowski"), ("Foden", "Kvaratskhelia")],
     "The hardest fusion quiz on YouTube. Name both!", "Nobody gets 8/8… prove me wrong 👇"),
]

ETIQUETAS = {3: ["EASY", "MEDIUM", "ONLY 1%"], 4: ["EASY", "MEDIUM", "HARD", "ONLY 1%"]}
PREG = [["Level two. Who are these two?", "Okay, harder now.", "Level two. Look closely."],
        ["This one is tricky.", "Getting harder…", "Only real fans get this one."],
        ["Final round. Only one percent get this.", "Last one. This is the hardest.", "Final round. Good luck."]]
REACC = ["Too easy?", "Did you get it?", "No way!", "Got both?", "Easy, right?", ""]


def candidatas(jugador, n=8):
    d = POSES[(POSES.jugador == J[jugador]) & (POSES.puntaje < 150)].sort_values("puntaje")
    if d.empty:
        raise SystemExit(f"sin foto válida para {jugador}")
    return d.head(n).to_dict("records")


def mejor_par(a, b):
    """Entre todas las fotos válidas de A y B, elige las de ángulo más parecido (espejando B si miran a lados opuestos).
    'asimetria' es el giro medido con YuNet (posición de la nariz respecto de los ojos): espejar cambia el signo."""
    mejor = None
    for fa in candidatas(a):
        for fb in candidatas(b):
            for espejar in (False, True):
                yb = -fb["asimetria"] if espejar else fb["asimetria"]
                costo = (abs(fa["asimetria"] - yb) * 400 + abs(fa["pitch"] - fb["pitch"]) * 150
                         + (fa["puntaje"] + fb["puntaje"]) * 0.25 + abs(fa["boca"] - fb["boca"]) * 150)
                if mejor is None or costo < mejor[0]:
                    mejor = (costo, fa, fb, espejar)
    return mejor


def main():
    rnd = random.Random(2026)
    (ROOT / "guiones").mkdir(exist_ok=True)
    resumen = []
    for vid, cuando, tema, titulos, pares, apertura, fijado in LOTE:
        n = len(pares)
        rondas = []
        for i, (a, b) in enumerate(pares):
            costo, pa, pb, esp = mejor_par(a, b)
            fa, fb = pa["foto"], pb["foto"]
            if i == 0:
                preg = apertura
            else:
                preg = rnd.choice(PREG[min(i - 1, 2)] if i < n - 1 else PREG[2])
            reac = rnd.choice(REACC) if i < n - 1 else "Did you get it?"
            rondas.append({"a": fa, "b": fb, "espejar_b": bool(esp), "cara_a": json.loads(pa["cara"]), "cara_b": json.loads(pb["cara"]), "nombre_a": a, "nombre_b": b,
                           "etiqueta": ETIQUETAS[n][i], "respira": [0.12, 0.1, 0.08, 0.06][i] if n == 4 else [0.12, 0.09, 0.06][i],
                           "voz_pregunta": preg, "voz_revela": f"{a} and {b}! {reac}".strip(), "costo_pose": round(costo, 1),
                           "pensar": 5.0 if i == n - 1 else 4.5})
        g = {"id": f"lote1_{vid}", "publicar": cuando, "tema": tema, "voz": "Puck", "pensar": 4.5,
             "voz_cierre": f"What's your score out of {2 * n}? Be honest!", "titulos": titulos,
             "descripcion": f"Two footballers. One face. Name BOTH players in every round — the last one is only for the 1% 🧠",
             "comentario_fijado": fijado, "rondas": rondas}
        (ROOT / "guiones" / f"lote1_{vid}.json").write_text(json.dumps(g, ensure_ascii=False, indent=1))
        resumen.append((vid, cuando, tema, [f"{r['nombre_a']}+{r['nombre_b']} ({r['costo_pose']}{', espejo' if r['espejar_b'] else ''})" for r in rondas]))
    for r in resumen:
        print(*r[:3], "|", "; ".join(r[3]))


if __name__ == "__main__":
    main()
