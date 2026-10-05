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

PROCESSED_HASHES_FILE = "processed_hashes.txt"
TELEGRAM_TOKEN = str(os.environ.get("TELEGRAM_TOKEN", "")).strip()
CHAT_ID = str(os.environ.get("CHAT_ID", "")).strip()


def send_telegram_notification(text, url, announcement_url):
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
                    "url": url
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


def load_processed_hashes():
    """Încarcă toate hash-urile salvate anterior dintr-un fișier."""
    if os.path.exists(PROCESSED_HASHES_FILE):
        with open(PROCESSED_HASHES_FILE, "r", encoding="utf-8") as f:
            return set(line.strip() for line in f if line.strip())
    return set()


def save_processed_hashes(hashes):
    """Salvează setul de hash-uri în fișier (păstrează ultimele 100 pentru a preveni creșterea nelimitată)."""
    recent_hashes = list(hashes)[-100:]
    with open(PROCESSED_HASHES_FILE, "w", encoding="utf-8") as f:
        for h in recent_hashes:
            f.write(f"{h}\n")


def get_all_announcements():
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

    announcements = []

    for block in blocks:
        date_soup = block.find(SECOND_HTML_TAG, class_=SECOND_HTML_CLASS).text.strip()

        title_element = block.find(THIRD_HTML_TAG)
        title_soup = title_element.text.strip() if title_element else "No title"

        link_element = title_element.find(FORTH_HTML_TAG) if title_element else None
        raw_link = link_element.get("href", "").strip() if link_element else ""

        if raw_link.startswith("http"):
            link_soup = raw_link
        else:
            link_soup = f"https://vl.politiaromana.ro{raw_link}"

        # Hash unic bazat pe titlu și dată
        hash_content = f"{date_soup}_{title_soup}"
        item_hash = hashlib.sha256(hash_content.encode("utf-8")).hexdigest()

        announcements.append({
            "hash": item_hash,
            "title": title_soup,
            "date": date_soup,
            "link": link_soup
        })

    return announcements


def check_for_updates():
    try:
        announcements = get_all_announcements()
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

    processed_hashes = load_processed_hashes()

    # Daca fisierul este gol (prima rulare), salvăm anunțurile curente fără a trimite spam
    if not processed_hashes:
        print("[INFO] First run detected. Saving current announcements as baseline...")
        for item in announcements:
            processed_hashes.add(item["hash"])
        save_processed_hashes(processed_hashes)
        return

    # Inversăm lista pentru a procesa anunțurile de la cel mai vechi la cel mai nou
    new_announcements = [item for item in reversed(announcements) if item["hash"] not in processed_hashes]

    if new_announcements:
        print(f"[INFO] Found {len(new_announcements)} new announcement(s)!")

        time_now = (datetime.now() + timedelta(hours=3)).strftime("%d %B %Y, %H:%M")

        for item in new_announcements:
            safe_title = html.escape(item["title"])
            safe_date = html.escape(item["date"])

            message = (
                "╔════════════════════╗\n"
                "🚨  <b>NEW ANNOUNCEMENT</b>  🚨\n"
                "╚════════════════════╝\n\n"
                f"📌 <b>Title:</b> {safe_title}\n"
                f"📅 <b>Publication Date:</b> {safe_date}\n"
                f"⏰ <b>Checked at:</b> <code>{time_now}</code>\n\n"
                "🔗 <i>Use the buttons below for more details.</i>"
            )

            send_telegram_notification(message, URL, item["link"])
            processed_hashes.add(item["hash"])

        # Salvează lista actualizată de hash-uri
        save_processed_hashes(processed_hashes)
    else:
        print("No new announcement added.")


if __name__ == "__main__":
    check_for_updates()