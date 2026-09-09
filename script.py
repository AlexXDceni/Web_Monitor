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


def get_latest_announcement_hash():
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

    # Eliminăm elementele inutile din pagină
    for tag in soup(["script", "style", "input", "meta", "noscript", "form", "svg"]):
        tag.decompose()

    # Identificăm link-urile care conțin anunțuri (butoanele/titlurile cu 'Citește tot' sau titlurile albastre)
    # Paginile CMS de tipul acesta au anunțurile structurate în blocuri distincte
    announcements = []

    # Căutăm toate container-ele sau titlurile de anunțuri
    for article in soup.find_all(["div", "article"]):
        # Dacă găsim o zonă de text care conține o dată (ex: "03 Septembrie 2026") și un titlu
        text = article.get_text(strip=True)
        if "Sursa:" in text or "Citește tot" in text:
            announcements.append(text)

    if announcements:
        # Luăm doar primul anunț (cel mai recent de sus)
        latest_announcement = announcements[0]
    else:
        # Fallback: extragem primele 3 titluri și link-uri din pagină
        links = soup.find_all("a", href=True)
        relevant_links = [
            f"{l.get_text(strip=True)}|{l['href']}"
            for l in links
            if "admitere" in l["href"] or "Citește" in l.get_text()
        ]
        latest_announcement = "".join(relevant_links[:3])

    return hashlib.sha256(latest_announcement.encode("utf-8")).hexdigest()


def check_for_updates():
    try:
        current_hash = get_latest_announcement_hash()
    except requests.exceptions.HTTPError as e:
        print(f"Site-ul a blocat cererea: {e}")
        return

    previous_hash = None
    if os.path.exists(HASH_FILE):
        with open(HASH_FILE, "r") as f:
            previous_hash = f.read().strip()

    if current_hash != previous_hash:
        message = f"🚨 *Anunț nou la admiteri!*\nVerifică pagina: {URL}"
        print("[INFO] Anunț nou detectat. Se trimite notificare pe Telegram...")

        send_telegram_notification(message)

        with open(HASH_FILE, "w") as f:
            f.write(current_hash)
    else:
        print("Nu s-a adăugat niciun anunț nou.")


if __name__ == "__main__":
    check_for_updates()
