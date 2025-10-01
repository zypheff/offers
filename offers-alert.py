import requests
from bs4 import BeautifulSoup
import json
import smtplib
from email.mime.text import MIMEText
from pathlib import Path
import os

URL = "https://compuvisionperu.pe/CYM/shop-list-prod-remates.php"
STATE_FILE = Path("seen_offers.json")

# Configuración del correo (mejor usar variables de entorno en GitHub Actions)
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_USER = os.getenv("EMAIL_USER", "tu_correo@gmail.com")
EMAIL_PASS = os.getenv("EMAIL_PASS", "TU_CONTRASEÑA_APP")
EMAIL_TO = os.getenv("EMAIL_TO", "destinatario@gmail.com")

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
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(list(ids), f, indent=2, ensure_ascii=False)

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
    seen = cargar_estado()
    ofertas = obtener_ofertas()

    # 🔑 Inicialización: si el JSON está vacío, guarda todos los IDs actuales
    if not seen:
        seen = {o["id"] for o in ofertas}
        guardar_estado(seen)
        print(f"Inicializado con {len(seen)} ofertas actuales.")
        return

    # En ejecuciones posteriores, detectar solo novedades
    nuevas = [o for o in ofertas if o["id"] not in seen]

    if nuevas:
        print("=== NUEVAS OFERTAS DETECTADAS ===")
        for o in nuevas:
            print(f"{o['nombre']} — {o['precio']} -> {o['enlace']}")
            seen.add(o["id"])
        guardar_estado(seen)
        enviar_email(nuevas)
    else:
        print("Sin novedades.")

if __name__ == "__main__":
    main()