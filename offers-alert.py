from playwright.sync_api import sync_playwright
import json
import smtplib
from email.mime.text import MIMEText
from pathlib import Path

URL = "https://compuvisionperu.pe/CYM/shop-list-prod-remates.php"
STATE_FILE = Path("seen_offers.json")

# --- Configuración del correo ---
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_USER = "akezuya@gmail.com"          # <-- tu Gmail
EMAIL_PASS = "swin lwtt hwor odhf"        # <-- tu contraseña de aplicación
EMAIL_TO   = "mf-a@outlook.com"           # <-- destinatario


# --- Funciones principales ---
def obtener_ofertas():
    ofertas = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(URL)
        page.wait_for_selector("div.product")  # esperar a que Vue cargue

        products = page.query_selector_all("div.product")
        for prod in products:
            enlace_tag = prod.query_selector(".product_title a")
            if not enlace_tag:
                continue
            nombre = enlace_tag.inner_text().strip()
            enlace = enlace_tag.get_attribute("href")
            precio_tag = prod.query_selector(".product_price")
            precio = precio_tag.inner_text().strip() if precio_tag else "Sin precio"

            id_unico = f"{enlace}|{nombre}"
            ofertas.append({
                "id": id_unico,
                "nombre": nombre,
                "enlace": enlace,
                "precio": precio
            })
        browser.close()
    return ofertas


def cargar_estado():
    if STATE_FILE.exists():
        data = json.loads(STATE_FILE.read_text())
        # si es lista de strings, convertir
        if data and isinstance(data[0], str):
            convertido = []
            for s in data:
                enlace, nombre = s.split("|", 1)
                convertido.append({
                    "id": s,
                    "nombre": nombre,
                    "enlace": enlace,
                    "precio": "Desconocido"
                })
            return convertido
        return data
    return []

def guardar_estado(ofertas):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(ofertas, f, indent=2, ensure_ascii=False)


def enviar_email(ofertas):
    cuerpo = "<h3>Nuevas ofertas encontradas:</h3><ul>"
    for o in ofertas:
        cuerpo += f"<li>{o['nombre']} — {o['precio']} → <a href='{o['enlace']}'>Ver oferta</a></li>"
    cuerpo += "</ul>"

    msg = MIMEText(cuerpo, "html")
    msg["Subject"] = "Nueva oferta detectada en Compuvision"
    msg["From"] = EMAIL_USER
    msg["To"] = EMAIL_TO

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASS)
        server.sendmail(EMAIL_USER, EMAIL_TO, msg.as_string())


def main():
    seen = cargar_estado()  # lista de dicts
    seen_ids = {o["id"] for o in seen}

    ofertas = obtener_ofertas()

    if not seen:
        guardar_estado(ofertas)
        print(f"Inicializado con {len(ofertas)} ofertas actuales.")
        return

    nuevas = [o for o in ofertas if o["id"] not in seen_ids]

    if nuevas:
        print("=== NUEVAS OFERTAS DETECTADAS ===")
        for o in nuevas:
            print(f"{o['nombre']} — {o['precio']} -> {o['enlace']}")
        # combinar lo anterior con las nuevas
        seen.extend(nuevas)
        guardar_estado(seen)
        enviar_email(nuevas)
    else:
        print("Sin novedades.")

if __name__ == "__main__":
    main()
