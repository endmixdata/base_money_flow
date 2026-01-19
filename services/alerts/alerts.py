import os
import time
import psycopg2
import requests
from datetime import datetime

# ===============================
# ENV
# ===============================
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

assert BOT_TOKEN, "TELEGRAM_BOT_TOKEN not set"
assert CHAT_ID, "TELEGRAM_CHAT_ID not set"

# ===============================
# SMART ALERTS CONFIG
# ===============================
ALERT_THRESHOLD = 20000        # USD
CHECK_INTERVAL = 300           # 5 минут
COOLDOWN_SECONDS = 3 * 60 * 60 # 3 часа

# ===============================
# DIVERGENCE CONFIG (TEST VALUES)
# ===============================
RAW_THRESHOLD = 50000
SMART_THRESHOLD = 20000
DIVERGENCE_COOLDOWN = 3 * 60 * 60  # 3 часа

SEVERITY_WEAK = 50000
SEVERITY_STRONG = 150000

# ===============================
# HELPERS
# ===============================
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

# ===============================
# DB
# ===============================
conn = wait_for_db()
cur = conn.cursor()

# ===============================
# STATE
# ===============================
# smart trend state
# state[token] = { "direction": str, "ts": datetime }
state = {}

# divergence state
# div_state[token] = { "ts": datetime }
div_state = {}

# ===============================
# WARMUP SMART STATE
# ===============================
cur.execute(
    """
    SELECT DISTINCT ON (token)
        token,
        net_flow
    FROM token_flow
    WHERE period = 'smart_1h'
    ORDER BY token, updated_at DESC
    """
)

now = datetime.utcnow()

for token, net_flow in cur.fetchall():
    if abs(net_flow) < ALERT_THRESHOLD:
        continue

    direction = "accumulating" if net_flow > 0 else "distributing"
    state[token] = {
        "direction": direction,
        "ts": now
    }

print("Alert state warmed up", flush=True)

# ===============================
# MAIN LOOP
# ===============================
while True:
    now = datetime.utcnow()

    # ======================================================
    # 1️⃣ SMART TREND ALERTS
    # ======================================================
    cur.execute(
        """
        SELECT DISTINCT ON (token)
            token,
            net_flow,
            updated_at
        FROM token_flow
        WHERE period = 'smart_1h'
        ORDER BY token, updated_at DESC
        """
    )

    rows = cur.fetchall()

    for token, net_flow, updated_at in rows:
        if abs(net_flow) < ALERT_THRESHOLD:
            continue

        direction = "accumulating" if net_flow > 0 else "distributing"
        prev = state.get(token)

        should_alert = False

        if prev is None:
            should_alert = True
        elif prev["direction"] != direction:
            should_alert = True
        elif (now - prev["ts"]).total_seconds() >= COOLDOWN_SECONDS:
            should_alert = True

        if not should_alert:
            continue

        sign = "+" if net_flow > 0 else "-"

        message = (
            "🧠 Smart Money Trend (Base)\n\n"
            f"Token: {token}\n"
            f"Direction: {direction.capitalize()}\n"
            f"Period: 1h\n"
            f"Net Flow: {sign}${abs(int(net_flow))}\n\n"
            f"Smart wallets started {direction}."
        )

        send_message(message)

        state[token] = {
            "direction": direction,
            "ts": now
        }

    # ======================================================
    # 2️⃣ DIVERGENCE ALERTS (RAW vs SMART)
    # ======================================================
    cur.execute(
        """
        WITH latest AS (
          SELECT DISTINCT ON (token, period)
            token, period, net_flow, updated_at
          FROM token_flow
          WHERE period IN ('raw_1h', 'smart_1h')
          ORDER BY token, period, updated_at DESC
        )
        SELECT
          r.token,
          r.net_flow AS raw_flow,
          s.net_flow AS smart_flow
        FROM latest r
        JOIN latest s
          ON r.token = s.token
        WHERE r.period = 'raw_1h'
          AND s.period = 'smart_1h'
        """
    )

    rows = cur.fetchall()

    for token, raw_flow, smart_flow in rows:
        if raw_flow is None or smart_flow is None:
            continue

        if abs(raw_flow) < RAW_THRESHOLD:
            continue
        if abs(smart_flow) < SMART_THRESHOLD:
            continue

        # направления должны быть противоположны
        if raw_flow * smart_flow >= 0:
            continue

        impact = min(abs(raw_flow), abs(smart_flow))

        if impact < SEVERITY_WEAK:
            continue
        elif impact >= SEVERITY_STRONG:
            severity = "STRONG"
            emoji = "🔴"
        else:
            severity = "WEAK"
            emoji = "🟡"

        prev = div_state.get(token)
        if prev and (now - prev["ts"]).total_seconds() < DIVERGENCE_COOLDOWN:
            continue

        market_dir = "buying" if raw_flow > 0 else "selling"
        smart_dir = "buying" if smart_flow > 0 else "selling"

        message = (
            f"{emoji} {severity} Divergence (Base)\n\n"
            f"Token: {token}\n"
            f"Period: 1h\n\n"
            f"Market Flow: {'+' if raw_flow > 0 else '-'}${abs(int(raw_flow))}\n"
            f"Smart Flow:  {'+' if smart_flow > 0 else '-'}${abs(int(smart_flow))}\n\n"
            f"Smart wallets are {smart_dir} while market is {market_dir}."
        )

        send_message(message)
        div_state[token] = {"ts": now}

    # ======================================================
    time.sleep(CHECK_INTERVAL)
