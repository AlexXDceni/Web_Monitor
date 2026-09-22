from datetime import datetime
import hashlib
import os
from bs4 import BeautifulSoup
import requests


# SSL/TTL verif error ignoring
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- CONFIGURARE ---
URL = "https://vl.politiaromana.ro/ro/cariera/admitere-institutii-invatamant"

FIRST_HTML_TAG = "div"
FIRST_HTML_CLASS = "boxStire"
SECOND_HTML_TAG = "span"
SECOND_HTML_CLASS = "dataStire"



HASH_FILE = "last_hash.txt"
TELEGRAM_TOKEN = str(os.environ.get("TELEGRAM_TOKEN", "")).strip()
CHAT_ID = str(os.environ.get("CHAT_ID", "")).strip()


def send_telegram_notification(text):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("Error: TELEGRAM_TOKEN or CHAT_ID is missing!")
        return

    telegram_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    inline_keyboard = {
        "inline_keyboard": [
            [
                {
                    "text": "🌐 Open Website",
                    "url": URL
                }
            ]
        ]
    }

    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML", "reply_markup": inline_keyboard}

    try:
        response = requests.post(telegram_url, json=payload, timeout=15)
        if response.status_code == 200:
            print("Success: The notification has been sent to Telegram!")
        else:
            print(f"Telegram server responded with code: {response.status_code}")
    except Exception as e:
        print(f"Failed to send notification. Error: {e}")

def get_latest_announcement_hash():
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            " (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "ro-RO,ro;q=0.9,en-US;q=0.8,en;q=0.7",
    }

    session = requests.Session()
    response = session.get(URL, headers=headers, timeout=15, verify=False)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    # soup = soup.prettify()

    blocks = soup.find_all(FIRST_HTML_TAG, class_=FIRST_HTML_CLASS)

    final_soup = blocks[0].find(SECOND_HTML_TAG, class_=SECOND_HTML_CLASS).text.strip()

    return hashlib.sha256(final_soup.encode("utf-8")).hexdigest()

def check_for_updates():
    try:
        current_hash = get_latest_announcement_hash()
    except requests.exceptions.Timeout:
        print(f"The request timed out.")
        return
    except requests.exceptions.HTTPError as e:
        print(f"The website has blocked the request: {e}")
        return
    except requests.exceptions.ConnectionError as e:
        print(f"Connection/DNS error: {e}")
        return
    except requests.exceptions.RequestException as e:
        print(f"Unexpected error occurred: {e}")
        return


    previous_hash = None
    if os.path.exists(HASH_FILE):
        with open(HASH_FILE, "r") as f:
            previous_hash = f.read().strip()

    if current_hash != previous_hash:
        # message = f"🚨 *New Announcement!*\nCheck page: {URL}"

        time = datetime.now().strftime("%d %B %Y, %H:%M")
        message = (
            "╔════════════════════╗\n"
            "🚨  <b>NEW ANNOUNCEMENT</b>  🚨\n"
            "╚════════════════════╝\n\n"
            "📌 <b>Status:</b> Change detected!\n"
            f"⏰ <b>Verified at:</b> <code>{time}</code>\n\n"
            "🔗 <i>Click here to view the announcement.</i>"
        )

        print("[INFO] Change detected. Sending notification to Telegram...")

        send_telegram_notification(message)

        with open(HASH_FILE, "w") as f:
            f.write(current_hash)
    else:
        print("No new announcement added.")

if __name__ == "__main__":
    check_for_updates()
