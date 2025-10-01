import time
import requests
from bs4 import BeautifulSoup

URL = "https://compuvisionperu.pe/CYM/shop-list-prod-remates.php"
CHECK_INTERVAL = 300  # cada 5 minutos

# Guardamos las ofertas ya vistas
seen_offers = set()

def obtener_ofertas():
    resp = requests.get(URL)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    ofertas = []
    for prod in soup.select("div.product"):
        # título + enlace
        enlace_tag = prod.select_one("h4 a")
        if not enlace_tag:
            continue
        nombre = enlace_tag.get_text(strip=True)
        enlace = enlace_tag["href"]

        # precio
        precio_tag = prod.select_one(".product_price")
        precio = precio_tag.get_text(strip=True) if precio_tag else "Sin precio"

        ofertas.append({
            "id": enlace,   # lo usamos como identificador único
            "nombre": nombre,
            "enlace": enlace,
            "precio": precio
        })
    return ofertas

def notificar(ofertas):
    # Aquí decides cómo notificar: print, email, Telegram, etc.
    print("=== NUEVAS OFERTAS DETECTADAS ===")
    for o in ofertas:
        print(f"{o['nombre']} — {o['precio']} -> {o['enlace']}")

def main_loop():
    global seen_offers
    # Inicializa con las ofertas actuales
    ofertas = obtener_ofertas()
    for o in ofertas:
        seen_offers.add(o["id"])
    print(f"Monitor iniciado con {len(seen_offers)} ofertas ya vistas.")

    while True:
        try:
            ofertas = obtener_ofertas()
        except Exception as e:
            print("Error al obtener ofertas:", e)
            time.sleep(CHECK_INTERVAL)
            continue

        nuevas = [o for o in ofertas if o["id"] not in seen_offers]
        if nuevas:
            notificar(nuevas)
            for o in nuevas:
                seen_offers.add(o["id"])

        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main_loop()
