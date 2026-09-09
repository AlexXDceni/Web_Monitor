import hashlib
import os
import requests

# --- CONFIGURARE ---
URL = "https://vl.politiaromana.ro/ro/cariera/admitere-institutii-invatamant"  # Schimbă cu link-ul pe care vrei să îl urmărești
HASH_FILE = "last_hash.txt"

# Preluăm token-urile în siguranță din GitHub Environment
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")


def send_telegram_notification(text):
  """Trimite o notificare push pe telefon prin Telegram."""
  if not TELEGRAM_TOKEN or not CHAT_ID:
    print("Eroare: Lipsesc cheile TELEGRAM_TOKEN sau CHAT_ID în mediu!")
    return

  telegram_url = f"https://telegram.org{TELEGRAM_TOKEN}/sendMessage"
  payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
  try:
    response = requests.post(telegram_url, data=payload)
    response.raise_for_status()
  except requests.exceptions.RequestException as e:
    print(f"Eroare la trimiterea notificării: {e}")


def get_page_hash():
  headers = {
      "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
  }
  response = requests.get(URL, headers=headers)
  response.raise_for_status()
  page_content = response.text.encode("utf-8")
  return hashlib.sha256(page_content).hexdigest()


def check_for_updates():
  current_hash = get_page_hash()

  previous_hash = None
  if os.path.exists(HASH_FILE):
    with open(HASH_FILE, "r") as f:
      previous_hash = f.read().strip()

  if current_hash != previous_hash:
    message = f"🚨 *Update detectat!*\nA apărut conținut nou la: {URL}"
    print(message)

    send_telegram_notification(message)

    with open(HASH_FILE, "w") as f:
      f.write(current_hash)
  else:
    print("Nu s-a schimbat nimic.")


if __name__ == "__main__":
  check_for_updates()
