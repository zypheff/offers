import time, requests, json
from bs4 import BeautifulSoup
from pathlib import Path

URL = "https://compuvisionperu.pe/CYM/shop-list-prod-remates.php"
STATE_FILE = Path("seen_offers.json")

def obtener_ofertas():
    resp = requests.get(URL)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    ofertas = []
    for prod in soup.select("div.product"):
        enlace_tag = prod.select_one("h4 a")
        if not enlace_tag:
            continue
        nombre = enlace_tag.get_text(strip=True)
        enlace = enlace_tag["href"]
        precio_tag = prod.select_one(".product_price")
        precio = precio_tag.get_text(strip=True) if precio_tag else "Sin precio"

        ofertas.append({
            "id": enlace,
            "nombre": nombre,
            "enlace": enlace,
            "precio": precio
        })
    return ofertas

def cargar_estado():
    if STATE_FILE.exists():
        return set(json.loads(STATE_FILE.read_text()))
    return set()

def guardar_estado(ids):
    STATE_FILE.write_text(json.dumps(list(ids)))

def main():
    seen = cargar_estado()
    ofertas = obtener_ofertas()
    nuevas = [o for o in ofertas if o["id"] not in seen]

    if nuevas:
        print("=== NUEVAS OFERTAS DETECTADAS ===")
        for o in nuevas:
            print(f"{o['nombre']} — {o['precio']} -> {o['enlace']}")
            seen.add(o["id"])
        guardar_estado(seen)
    else:
        print("Sin novedades.")

if __name__ == "__main__":
    main()
