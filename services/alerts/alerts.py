import os
import time
import psycopg2
import requests

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

assert BOT_TOKEN, "TELEGRAM_BOT_TOKEN not set"
assert CHAT_ID, "TELEGRAM_CHAT_ID not set"

ALERT_THRESHOLD = 20000  # USD
CHECK_INTERVAL = 300     # seconds

def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text
    }
    requests.post(url, json=payload, timeout=10)

def wait_for_db():
    while True:
        try:
            return psycopg2.connect(
                host="postgres",
                dbname="smartmoney",
                user="smf",
                password="smf_pass"
            )
        except psycopg2.OperationalError:
            time.sleep(2)

conn = wait_for_db()
cur = conn.cursor()

last_alert_ts = None

while True:
    cur.execute(
        """
        SELECT net_flow, updated_at
        FROM token_flow
        WHERE period = 'smart_1h'
        ORDER BY updated_at DESC
        LIMIT 1
        """
    )

    row = cur.fetchone()

    if row:
        net_flow, ts = row

        if last_alert_ts is None or ts > last_alert_ts:
            if abs(net_flow) >= ALERT_THRESHOLD:
                direction = "accumulating" if net_flow > 0 else "distributing"
                sign = "+" if net_flow > 0 else "-"

                message = (
                    "🧠 Smart Money Alert (Base)\n\n"
                    f"Token: WETH\n"
                    f"Period: 1h\n"
                    f"Net Flow: {sign}${abs(int(net_flow))}\n\n"
                    f"Smart wallets are {direction}."
                )

                send_message(message)
                last_alert_ts = ts

    time.sleep(CHECK_INTERVAL)
