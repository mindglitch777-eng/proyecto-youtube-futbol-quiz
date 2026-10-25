#!/usr/bin/env python3
"""Arma los guiones de las 7 carreras temáticas (produccion/guiones/carrera_XX.json) con las frases del relator."""
import json
from pathlib import Path

from render_carrera import lineas_voz

ROOT = Path(__file__).resolve().parent
ORO, CIAN, BLANCO_, GRANATE = [255, 205, 70], [90, 210, 255], [245, 245, 245], [200, 30, 90]


def j(nombre, voz=None, anillo=None):
    d = {"tipo": "jugador", "nombre": nombre, "voz": voz or nombre}
    if anillo:
        d["anillo"] = anillo
    return d


def p(nombre, pais, anillo):
    return {"tipo": "pais", "nombre": nombre, "pais": pais, "voz": nombre, "corto": nombre.upper(), "anillo": anillo}


def c(nombre, corto, colores, estilo, voz=None, anillo=None):
    return {"tipo": "club", "nombre": nombre, "corto": corto, "colores": colores, "estilo": estilo,
            "voz": voz or nombre, "anillo": anillo or colores[0]}


LOTE = [
    dict(id="carrera_01", ganador="Lamine Yamal", paleta="oro", evento="BALLON D'OR 2026 PREDICTION", titulo="WHO WINS THE RACE?",
         gancho="WHO DESERVES THE BALLON D'OR?", voz_intro="Who deserves the Ballon d'Or? Pick your player now!",
         eliminar=3, circuito=["clavos", "aspas", "rebotadores", "zigzag", "acelerador", "molinos", "embudo"],
         competidores=[j("Lamine Yamal", anillo=ORO), j("Kylian Mbappé", "Mbappé", CIAN), j("Ousmane Dembélé", "Dembélé", [255, 120, 80]),
                       j("Harry Kane", "Kane", [240, 70, 70]), j("Lionel Messi", "Messi", [120, 200, 255]),
                       j("Vinícius Júnior", "Vinicius", [255, 255, 255]), j("Erling Haaland", "Haaland", [170, 120, 255])],
         cierre="WHO SHOULD WIN IT? COMMENT"),
    dict(id="carrera_02", ganador="Argentina", paleta="cancha", evento="WORLD CUP CHAMPIONS", titulo="WHO WINS THE RACE?",
         gancho="8 WORLD CHAMPIONS. ONLY 1 WINS", voz_intro="Eight world champions. Only one wins. Pick your country now!",
         eliminar=3, circuito=["zigzag", "clavos", "molinos", "acelerador", "rebotadores", "aspas"],
         competidores=[p("Brazil", "BR", [255, 220, 0]), p("Germany", "DE", [240, 240, 240]), p("Italy", "IT", [60, 140, 255]),
                       p("Argentina", "AR", [120, 200, 255]), p("France", "FR", [70, 90, 230]), p("Uruguay", "UY", [150, 210, 255]),
                       p("England", "ENG", [240, 60, 60]), p("Spain", "ES", [255, 190, 0])],
         cierre="DID YOUR COUNTRY WIN?"),
    dict(id="carrera_03", ganador="Boca Juniors", paleta="fuego", evento="COPA LIBERTADORES GIANTS", titulo="WHO WINS THE RACE?",
         gancho="THE BIGGEST CLUBS IN SOUTH AMERICA", voz_intro="The giants of South America. Pick your club now!",
         eliminar=3, circuito=["clavos", "zigzag", "aspas", "rebotadores", "molinos", "acelerador", "embudo"],
         competidores=[c("Boca Juniors", "BOCA", [[0, 45, 130], [255, 200, 0]], "franja", anillo=[255, 200, 0]),
                       c("River Plate", "RIVER", [[245, 245, 245], [220, 30, 40]], "banda", anillo=[245, 245, 245]),
                       c("Flamengo", "FLA", [[200, 20, 30], [20, 20, 20]], "rayas", anillo=[230, 40, 40]),
                       c("Palmeiras", "PALMEIRAS", [[0, 110, 60], [245, 245, 245]], "franja", anillo=[40, 200, 110]),
                       c("Peñarol", "PEÑAROL", [[255, 205, 0], [20, 20, 20]], "rayas", anillo=[255, 205, 0]),
                       c("Racing Club", "RACING", [[120, 190, 240], [245, 245, 245]], "rayas", anillo=[120, 190, 240]),
                       c("Independiente", "INDEPENDIENTE", [[200, 16, 30]], "liso", anillo=[255, 90, 90]),
                       c("Corinthians", "CORINTHIANS", [[245, 245, 245], [20, 20, 20]], "mitades", anillo=[200, 200, 200])],
         cierre="WHO IS YOUR CLUB? COMMENT"),
    dict(id="carrera_04", ganador="Cristiano Ronaldo", paleta="violeta", evento="THE GOAT DEBATE", titulo="WHO WINS THE RACE?",
         gancho="WHO IS THE REAL GOAT?", voz_intro="Who is the real goat? Pick one now!",
         eliminar=0, circuito=["clavos", "molinos", "zigzag", "rebotadores", "aspas", "acelerador", "embudo"],
         competidores=[j("Lionel Messi", "Messi", [120, 200, 255]), j("Cristiano Ronaldo", "Ronaldo", [240, 70, 70]),
                       j("Neymar", anillo=[255, 220, 0]), j("Kylian Mbappé", "Mbappé", [80, 120, 255]),
                       j("Erling Haaland", "Haaland", [170, 120, 255]), j("Lamine Yamal", anillo=ORO)],
         cierre="IS YOUR GOAT THE WINNER?"),
    dict(id="carrera_05", ganador="Manchester United", paleta="noche", evento="PREMIER LEAGUE BIG 6", titulo="WHO WINS THE RACE?",
         gancho="ONLY ONE CLUB CAN WIN", voz_intro="The Premier League big six. Pick your club now!",
         eliminar=2, circuito=["zigzag", "rebotadores", "clavos", "aspas", "acelerador", "molinos"],
         competidores=[c("Arsenal", "ARSENAL", [[220, 0, 20], [245, 245, 245]], "franja", anillo=[255, 70, 70]),
                       c("Chelsea", "CHELSEA", [[3, 70, 148]], "liso", anillo=[60, 120, 255]),
                       c("Liverpool", "LIVERPOOL", [[200, 16, 46]], "liso", anillo=[200, 16, 46]),
                       c("Manchester City", "CITY", [[108, 171, 221]], "liso", "Man City", [108, 171, 221]),
                       c("Manchester United", "UNITED", [[218, 41, 28], [20, 20, 20]], "mitades", "Man United", [255, 210, 0]),
                       c("Tottenham Hotspur", "SPURS", [[245, 245, 245], [19, 34, 87]], "franja", "Spurs", [245, 245, 245])],
         cierre="DID YOUR CLUB WIN?"),
    dict(id="carrera_06", ganador="Lamine Yamal", paleta="noche", evento="EL CLÁSICO", titulo="REAL MADRID vs BARÇA RACE",
         gancho="MADRID OR BARÇA? PICK ONE", voz_intro="Madrid or Barca? Pick your side now!",
         eliminar=0, circuito=["clavos", "aspas", "zigzag", "rebotadores", "molinos", "embudo"],
         competidores=[j("Kylian Mbappé", "Mbappé", BLANCO_), j("Vinícius Júnior", "Vinicius", BLANCO_),
                       j("Jude Bellingham", "Bellingham", BLANCO_), j("Lamine Yamal", anillo=GRANATE),
                       j("Pedri", anillo=GRANATE), j("Robert Lewandowski", "Lewandowski", GRANATE)],
         cierre="MADRID OR BARÇA FAN?"),
    dict(id="carrera_07", ganador="Ronaldinho", paleta="fuego", evento="LEGENDS vs NEW GEN", titulo="WHO WINS THE RACE?",
         gancho="LEGENDS OR THE NEW GENERATION?", voz_intro="Legends or the new generation? Pick one now!",
         eliminar=3, circuito=["rebotadores", "zigzag", "clavos", "molinos", "acelerador", "aspas", "embudo"],
         competidores=[j("Ronaldinho", anillo=ORO), j("Zinedine Zidane", "Zidane", ORO), j("Thierry Henry", "Henry", ORO),
                       j("David Beckham", "Beckham", ORO), j("Lamine Yamal", anillo=CIAN), j("Jude Bellingham", "Bellingham", CIAN),
                       j("Jamal Musiala", "Musiala", CIAN), j("Bukayo Saka", "Saka", CIAN)],
         cierre="LEGENDS OR NEW GEN?"),
    dict(id="carrera_08", ganador="Cristiano Ronaldo", paleta="oro", evento="ONE TROPHY. THREE SUPERSTARS", titulo="WHO GETS THE TROPHY?",
         gancho="MBAPPÉ, YAMAL OR RONALDO?", voz_intro="Mbappé, Yamal or Ronaldo? Pick one now!",
         eliminar=1, circuito=["clavos", "aspas", "zigzag", "rebotadores", "acelerador", "molinos", "embudo"],
         competidores=[j("Kylian Mbappé", "Mbappé", CIAN), j("Lamine Yamal", anillo=ORO), j("Cristiano Ronaldo", "Ronaldo", [240, 70, 70])],
         cierre="IF YOU LIKE RONALDO, COMMENT SIUU",
         titulos=["Mbappé, Yamal or Ronaldo? One Trophy, Three Superstars! 🏆", "Who gets the trophy? Mbappé, Yamal or Ronaldo 😱", "MBAPPÉ vs YAMAL vs RONALDO race 🏁"]),
    dict(id="carrera_09", ganador="Cristiano Ronaldo", paleta="violeta", evento="ONE TROPHY. THREE LEGENDS", titulo="WHO GETS THE TROPHY?",
         gancho="MESSI, NEYMAR OR RONALDO?", voz_intro="Messi, Neymar or Ronaldo? Pick one now!",
         eliminar=1, circuito=["rebotadores", "zigzag", "molinos", "clavos", "aspas", "acelerador", "embudo"],
         competidores=[j("Lionel Messi", "Messi", [120, 200, 255]), j("Neymar", anillo=[255, 220, 0]), j("Cristiano Ronaldo", "Ronaldo", [240, 70, 70])],
         cierre="IF YOU LIKE RONALDO, COMMENT SIUU",
         titulos=["Messi, Neymar or Ronaldo? Only ONE gets the trophy 🏆", "Messi vs Neymar vs Ronaldo race 😱 Who wins?", "The GOAT race: Messi, Neymar or Ronaldo? 🐐"]),
]

# Balón de Oro: versión B donde gana Kane (favorito de las casas de apuestas); se sube la que coincida con el real
LOTE.append(dict(next(g for g in LOTE if g["id"] == "carrera_01"), id="carrera_01b", ganador="Harry Kane"))

UCL_MAR = [c("FC Barcelona", "BARÇA", [[165, 0, 68], [0, 77, 152]], "rayas", "Barca", [255, 90, 140]),
           c("Manchester United", "UNITED", [[218, 41, 28], [20, 20, 20]], "mitades", "Man United", [255, 210, 0]),
           c("Bayern Munich", "BAYERN", [[220, 5, 45], [245, 245, 245]], "franja", "Bayern", [240, 60, 80]),
           c("Atlético Madrid", "ATLÉTICO", [[203, 53, 36], [245, 245, 245]], "rayas", "Atletico", [230, 90, 70]),
           c("Paris Saint-Germain", "PSG", [[0, 65, 112], [218, 41, 28]], "franja", "P S G", [80, 140, 255]),
           c("Villarreal", "VILLARREAL", [[255, 225, 0]], "liso", "Villarreal", [255, 225, 0]),
           c("Inter", "INTER", [[0, 104, 168], [20, 20, 20]], "rayas", "Inter", [60, 160, 255]),
           c("Roma", "ROMA", [[142, 31, 47], [240, 188, 66]], "franja", "Roma", [240, 188, 66])]
UCL_MIE = [c("Real Madrid", "MADRID", [[245, 245, 245], [0, 82, 159]], "franja", "Real Madrid", [245, 245, 245]),
           c("Liverpool", "LIVERPOOL", [[200, 16, 46]], "liso", "Liverpool", [230, 40, 70]),
           c("Manchester City", "CITY", [[108, 171, 221]], "liso", "Man City", [108, 171, 221]),
           c("Arsenal", "ARSENAL", [[220, 0, 20], [245, 245, 245]], "franja", "Arsenal", [255, 90, 90]),
           c("Napoli", "NAPOLI", [[18, 160, 215]], "liso", "Napoli", [18, 160, 215]),
           c("Borussia Dortmund", "BVB", [[253, 225, 0], [20, 20, 20]], "franja", "Dortmund", [253, 225, 0]),
           c("FC Porto", "PORTO", [[0, 64, 140], [245, 245, 245]], "rayas", "Porto", [80, 130, 230]),
           c("RB Leipzig", "LEIPZIG", [[245, 245, 245], [221, 1, 63]], "franja", "Leipzig", [221, 1, 63])]
LOTE += [
    dict(id="carrera_10", ganador="FC Barcelona", paleta="noche", evento="CHAMPIONS LEAGUE TUESDAY", titulo="PREDICTION RACE",
         gancho="WHO WINS ON TUESDAY NIGHT?", voz_intro="Champions League Tuesday. Pick your club now!",
         eliminar=3, circuito=["clavos", "aspas", "zigzag", "rebotadores", "acelerador", "molinos", "embudo"], competidores=UCL_MAR,
         cierre="WHO WINS TONIGHT? COMMENT",
         titulos=["Champions League Tuesday: who wins? 🏆 Prediction race", "UCL prediction race 😱 Pick your club", "Barça, Bayern or United? UCL prediction 🏁"]),
    dict(id="carrera_11", ganador="Real Madrid", paleta="oro", evento="CHAMPIONS LEAGUE WEDNESDAY", titulo="PREDICTION RACE",
         gancho="WHO WINS ON WEDNESDAY NIGHT?", voz_intro="Champions League Wednesday. Pick your club now!",
         eliminar=3, circuito=["zigzag", "rebotadores", "clavos", "molinos", "aspas", "acelerador", "embudo"], competidores=UCL_MIE,
         cierre="WHO WINS TONIGHT? COMMENT",
         titulos=["Champions League Wednesday: who wins? 🏆 Prediction race", "Madrid, Liverpool or City? UCL prediction 😱", "UCL prediction race 🏁 Pick your club"]),
]

if __name__ == "__main__":
    for g in LOTE:
        g["formato"] = "carrera"
        g["voz_lineas"] = lineas_voz(g)
        (ROOT / "guiones" / f"{g['id']}.json").write_text(json.dumps(g, ensure_ascii=False, indent=1))
        print(g["id"], len(g["voz_lineas"]), "frases")
