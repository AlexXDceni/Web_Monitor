import hashlib
import os
from bs4 import BeautifulSoup
import requests

# --- CONFIGURARE ---
URL = "https://vl.politiaromana.ro/ro/cariera/admitere-institutii-invatamant"
HASH_FILE = "last_hash.txt"

TELEGRAM_TOKEN = str(os.environ.get("TELEGRAM_TOKEN", "")).strip()
CHAT_ID = str(os.environ.get("CHAT_ID", "")).strip()


def send_telegram_notification(text):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("Eroare: Lipsesc cheile TELEGRAM_TOKEN sau CHAT_ID în mediu!")
        return

    telegram_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}

    try:
        response = requests.post(telegram_url, json=payload, timeout=15)
        if response.status_code == 200:
            print("Succes: Notificarea a fost trimisă pe Telegram!")
        else:
            print(f"Serverul Telegram a răspuns cu codul: {response.status_code}")
    except Exception as e:
        print(f"Trimiterea a eșuat. Eroare: {e}")


def get_clean_page_hash():
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            " (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "ro-RO,ro;q=0.9,en-US;q=0.8,en;q=0.7",
    }

    session = requests.Session()
    response = session.get(URL, headers=headers, timeout=15)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # Eliminăm tag-urile dinamice care se schimbă la fiecare request
    for tag in soup(["script", "style", "input", "meta", "noscript"]):
        tag.decompose()

    # Încercăm să izolăm doar zona principală de conținut
    # Dacă site-ul folosește un tag <main> sau o clasă de conținut, o folosim pe aceea
    main_content = soup.find("main") or soup.find("div", class_="content") or soup.body

    # Extragerea doar a textului curățat de spații suplimentare
    clean_text = main_content.get_text(separator=" ", strip=True)

    return hashlib.sha256(clean_text.encode("utf-8")).hexdigest()


def check_for_updates():
    try:
        current_hash = get_clean_page_hash()
    except requests.exceptions.HTTPError as e:
        print(f"Site-ul a blocat cererea: {e}")
        return

    previous_hash = None
    if os.path.exists(HASH_FILE):
        with open(HASH_FILE, "r") as f:
            previous_hash = f.read().strip()

    if current_hash != previous_hash:
        message = f"🚨 *Update detectat!*\nA apărut conținut nou la admiteri: {URL}"
        print("[INFO] Schimbare reală detectată pe pagină. Se trimite notificare...")

        send_telegram_notification(message)

        with open(HASH_FILE, "w") as f:
            f.write(current_hash)
    else:
        print("Nu s-a schimbat nimic.")


if __name__ == "__main__":
    check_for_updates()
