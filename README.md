# Web Announcement Monitor

An automated Python script that monitors a specific web page for new announcements and sends instant notifications via **Telegram** when updates are detected.

---

## 📌 Features

* **HTML Parsing:** Extract relevant update elements using `BeautifulSoup`.
* **Hash-based Tracking:** Generates a SHA-256 hash of the content to detect actual changes without false alarms.
* **Telegram Alerts:** Sends direct Markdown-formatted notification messages via Telegram Bot API.

---

## 🛠️ Requirements

* **Python 3.8+**
* Required packages: `beautifulsoup4`, `requests`

---

## 🚀 Local Setup & Configuration

### 1. Installation
Install the necessary dependencies:
```bash
pip install beautifulsoup4 requests
```
### 2. Environment Variables
Set your Telegram Bot credentials as environment variables:

* **Linux / macOS:**
 ```bash
  export TELEGRAM_TOKEN="your_telegram_bot_token"
  export CHAT_ID="your_chat_id"
```
* **Windows (CMD):**
```bash
  set TELEGRAM_TOKEN=your_telegram_bot_token
  set CHAT_ID=your_chat_id
```
### 3. Target URL Setup
In `main.py`, update the `URL` constant with the web page you wish to monitor:

URL = "https://example.com/announcements"

---

## ⚙️ How to Enable GitHub Actions Automation

To run this monitor automatically on a schedule using GitHub Actions, open `.github/workflows/run.yml` and **uncomment the workflow code**.

1. Navigate to `.github/workflows/run.yml`.
2. Remove the comment symbols (`#`) from the file content to activate the workflow trigger.
3. Add `TELEGRAM_TOKEN` and `CHAT_ID` to your GitHub Repository Secrets (**Settings > Secrets and variables > Actions**).

Once uncommented, GitHub Actions will automatically execute the script on your specified cron schedule.
