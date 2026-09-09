import hashlib
import os
import requests

# --- CONFIGURARE ---
URL = "https://vl.politiaromana.ro/ro/cariera/admitere-institutii-invatamant"
HASH_FILE = "last_hash.txt"

# Curățăm automat eventualele spații adăugate din greșeală în GitHub Secrets
TELEGRAM_TOKEN = str(os.environ.get("TELEGRAM_TOKEN", "")).strip()
CHAT_ID = str(os.environ.get("CHAT_ID", "")).strip()


def send_telegram_notification(text):
  """Trimite o notificare push pe telefon prin Telegram."""
  if not TELEGRAM_TOKEN or not CHAT_ID:
    print("Eroare: Lipsesc cheile TELEGRAM_TOKEN sau CHAT_ID în mediu!")
    return

  # Construim URL-ul complet direct, folosind formatarea securizată din requests
  telegram_url = f"https://telegram.org{TELEGRAM_TOKEN}/sendMessage"

  payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}

  print(
      f"Se încearcă trimiterea către bot-ul cu token-ul care începe cu:"
      f" {TELEGRAM_TOKEN[:10]}..."
  )

  try:
    response = requests.post(telegram_url, data=payload, timeout=15)
    response.raise_for_status()
    print("Notificarea a fost trimisă cu succes pe Telegram!")
  except requests.exceptions.RequestException as e:
    print(f"Eroare la trimiterea notificării: {e}")


def get_page_hash():
  headers = {
      "User-Agent": (
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
          " (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
      ),
      "Accept": (
          "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8"
      ),
      "Accept-Language": "ro-RO,ro;q=0.9,en-US;q=0.8,en;q=0.7",
      "Cache-Control": "max-age=0",
      "Connection": "keep-alive",
  }

  session = requests.Session()
  response = session.get(URL, headers=headers, timeout=15)
  response.raise_for_status()

  page_content = response.text.encode("utf-8")
  return hashlib.sha256(page_content).hexdigest()


def check_for_updates():
  try:
    current_hash = get_page_hash()
  except requests.exceptions.HTTPError as e:
    print(f"Site-ul a blocat cererea: {e}")
    return

  previous_hash = None
  if os.path.exists(HASH_FILE):
    with open(HASH_FILE, "r") as f:
      previous_hash = f.read().strip()

  if current_hash != previous_hash:
    message = f"🚨 *Update detectat!*\nA apărut conținut nou la admiteri: {URL}"
    print(message)

    send_telegram_notification(message)

    with open(HASH_FILE, "w") as f:
      f.write(current_hash)
  else:
    print("Nu s-a schimbat nimic.")


if __name__ == "__main__":
  check_for_updates()
