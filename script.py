from datetime import datetime, timedelta
import hashlib
import html
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

THIRD_HTML_TAG = "h3"
FORTH_HTML_TAG = "a"

HASH_FILE = "last_hash.txt"
TELEGRAM_TOKEN = str(os.environ.get("TELEGRAM_TOKEN", "")).strip()
CHAT_ID = str(os.environ.get("CHAT_ID", "")).strip()


def send_telegram_notification(text, announcement_url):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("Error: TELEGRAM_TOKEN or CHAT_ID is missing!")
        return

    telegram_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    inline_keyboard = {
        "inline_keyboard": [
            [
                {
                    "text": "📄 Open Announcement",
                    "url": announcement_url
                },
                {
                    "text": "🌐 Open Main Page",
                    "url": URL
                }
            ]
        ]
    }

    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "reply_markup": inline_keyboard,
        "disable_web_page_preview": True
    }

    try:
        response = requests.post(telegram_url, json=payload, timeout=15)
        if response.status_code == 200:
            print("Success: The notification has been sent to Telegram!")
        else:
            print(f"Telegram server responded with code: {response.status_code}")
    except Exception as e:
        print(f"Failed to send notification. Error: {e}")


def get_latest_announcement_data():
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
    blocks = soup.find_all(FIRST_HTML_TAG, class_=FIRST_HTML_CLASS)

    if not blocks:
        raise ValueError("No announcement blocks found on the page.")

    first_block = blocks[0]

    date_soup = first_block.find(SECOND_HTML_TAG, class_=SECOND_HTML_CLASS).text.strip()
    
    title_element = first_block.find(THIRD_HTML_TAG)
    title_soup = title_element.text.strip() if title_element else "No title"

    link_element = title_element.find(FORTH_HTML_TAG) if title_element else None
    raw_link = link_element.get("href", "").strip() if link_element else ""

    if raw_link.startswith("http"):
        link_soup = raw_link
    else:
        link_soup = f"https://vl.politiaromana.ro{raw_link}"

    hash_content = f"{date_soup}_{title_soup}"
    current_hash = hashlib.sha256(hash_content.encode("utf-8")).hexdigest()

    return current_hash, title_soup, date_soup, link_soup


def check_for_updates():
    try:
        current_hash, title, announcement_date, link = get_latest_announcement_data()
    except requests.exceptions.Timeout:
        print("The request timed out.")
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
    except Exception as e:
        print(f"Parsing error: {e}")
        return

    previous_hash = None
    if os.path.exists(HASH_FILE):
        with open(HASH_FILE, "r", encoding="utf-8") as f:
            previous_hash = f.read().strip()

    if current_hash != previous_hash:
        time = (datetime.now() + timedelta(hours=3)).strftime("%d %B %Y, %H:%M")

        safe_title = html.escape(title)
        safe_date = html.escape(announcement_date)

        message = (
            "╔════════════════════╗\n"
            "🚨  <b>NEW ANNOUNCEMENT</b>  🚨\n"
            "╚════════════════════╝\n\n"
            f"📌 <b>Title:</b> {safe_title}\n"
            f"📅 <b>Publication Date:</b> {safe_date}\n"
            f"⏰ <b>Checked at:</b> <code>{time}</code>\n\n"
            "🔗 <i>Use the buttons below for more details.</i>"
        )

        print("[INFO] Change detected. Sending notification to Telegram...")

        send_telegram_notification(message, link)

        with open(HASH_FILE, "w", encoding="utf-8") as f:
            f.write(current_hash)
    else:
        print("No new announcement added.")


if __name__ == "__main__":
    check_for_updates()