#!/usr/bin/env python3
"""Nacionalidad (selección) de cada jugador y bandera Twemoji (CC BY 4.0) en PNG. Datos: selección que representa."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DIR = ROOT / "assets" / "banderas"
PAIS = {
    "Messi": "AR", "Ronaldo": "PT", "Mbappé": "FR", "Haaland": "NO", "Yamal": "ES", "Vinícius": "BR", "Bellingham": "ENG",
    "Neymar": "BR", "Salah": "EG", "Kane": "ENG", "Pedri": "ES", "Saka": "ENG", "Pulisic": "US", "Ronaldinho": "BR",
    "Zidane": "FR", "Beckham": "ENG", "Henry": "FR", "Ibrahimović": "SE", "Rooney": "ENG", "Gerrard": "ENG", "Ramos": "ES",
    "Kroos": "DE", "De Bruyne": "BE", "Lewandowski": "PL", "Griezmann": "FR", "Foden": "ENG", "Rice": "ENG", "Rashford": "ENG",
    "Musiala": "DE", "Wirtz": "DE", "Hakimi": "MA", "Valverde": "UY", "Lautaro": "AR", "Di María": "AR", "Son": "KR",
    "Ødegaard": "NO", "Rodrygo": "BR", "Dembélé": "FR", "Kvaratskhelia": "GE", "McKennie": "US", "Bale": "WAL", "Benzema": "FR",
}
SUB = {"ENG": "1f3f4-e0067-e0062-e0065-e006e-e0067-e007f", "WAL": "1f3f4-e0067-e0062-e0077-e006c-e0073-e007f"}


def codigo_twemoji(pais):
    if pais in SUB:
        return SUB[pais]
    return "-".join(f"{0x1F1E6 + ord(c) - ord('A'):x}" for c in pais)


def png(pais, lado=160):
    """Ruta a la bandera en PNG (se baja el SVG de Twemoji la primera vez)."""
    dst = DIR / f"{pais}_{lado}.png"
    if not dst.exists():
        import cairosvg
        import requests
        svg = requests.get(f"https://raw.githubusercontent.com/jdecked/twemoji/main/assets/svg/{codigo_twemoji(pais)}.svg", timeout=30)
        svg.raise_for_status()
        cairosvg.svg2png(bytestring=svg.content, write_to=str(dst), output_width=lado, output_height=lado)
    return dst


if __name__ == "__main__":
    for p in sorted(set(PAIS.values())):
        print(p, png(p))
