import os
import time
import psycopg2
import requests
from datetime import datetime, timedelta

# ===============================
# ENV
# ===============================
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

assert BOT_TOKEN, "TELEGRAM_BOT_TOKEN not set"
assert CHAT_ID, "TELEGRAM_CHAT_ID not set"

# ===============================
# CONFIG
# ===============================
ALERT_THRESHOLD = 20000

SEVERITY_WEAK = 50000
SEVERITY_STRONG = 150000

CHECK_INTERVAL = 60  # проверяем раз в минуту

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
            time.sleep(5)

conn = wait_for_db()
cur = conn.cursor()

last_sent_date = None

# ===============================
# MAIN LOOP
# ===============================
while True:
    now = datetime.utcnow()
    today = now.date()

    # 👉 шлём только один раз в день
    if last_sent_date == today:
        time.sleep(CHECK_INTERVAL)
        continue

    # 👉 ждём 00:00–00:05 UTC
    if now.hour != 0:
        time.sleep(CHECK_INTERVAL)
        continue

    cur.execute(
        """
        WITH flows AS (
          SELECT
            token,
            MAX(CASE WHEN period='raw_24h'   THEN net_flow END) AS raw_flow,
            MAX(CASE WHEN period='smart_24h' THEN net_flow END) AS smart_flow
          FROM token_flow
          WHERE period IN ('raw_24h', 'smart_24h')
          GROUP BY token
        )
        SELECT token, raw_flow, smart_flow
        FROM flows
        ORDER BY token
        """
    )

    rows = cur.fetchall()

    lines = []
    lines.append("📊 Daily Smart Money Summary (Base)\n")

    for token, raw_flow, smart_flow in rows:
        if smart_flow is None or abs(smart_flow) < ALERT_THRESHOLD:
            lines.append(f"{token}\n• No significant smart activity\n")
            continue

        raw_flow = raw_flow or 0
        smart_flow = smart_flow or 0

        lines.append(f"{token}")

        lines.append(
            f"• Smart Flow (24h): "
            f"{'+' if smart_flow > 0 else '-'}${abs(int(smart_flow))}"
        )

        lines.append(
            f"• Market Flow (24h): "
            f"{'+' if raw_flow > 0 else '-'}${abs(int(raw_flow))}"
        )

        if raw_flow * smart_flow < 0:
            impact = min(abs(raw_flow), abs(smart_flow))
            if impact >= SEVERITY_STRONG:
                sev = "STRONG"
            elif impact >= SEVERITY_WEAK:
                sev = "WEAK"
            else:
                sev = None

            if sev:
                lines.append(f"• Divergence: {sev}")

        lines.append("")

    message = "\n".join(lines).strip()
    send_message(message)
    # ======================================================
    # TOKEN PROFILES (7D BASELINE)
    # ======================================================
    cur.execute(
        """
        WITH last_7d AS (
          SELECT
            token,
            period,
            ABS(net_flow) AS value
          FROM token_flow
          WHERE period IN ('raw_1h', 'smart_1h', 'raw_24h')
            AND updated_at > now() - interval '7 days'
        ),
        agg AS (
          SELECT
            token,
            AVG(CASE WHEN period='raw_1h'   THEN value END) AS avg_raw_1h,
            AVG(CASE WHEN period='smart_1h' THEN value END) AS avg_smart_1h,
            AVG(CASE WHEN period='raw_24h'  THEN value END) AS avg_volume_24h
          FROM last_7d
          GROUP BY token
        )
        INSERT INTO token_profiles
          (token, avg_raw_1h, avg_smart_1h, avg_volume_24h, updated_at)
        SELECT
          token,
          avg_raw_1h,
          avg_smart_1h,
          avg_volume_24h,
          now()
        FROM agg
        ON CONFLICT (token) DO UPDATE SET
          avg_raw_1h     = EXCLUDED.avg_raw_1h,
          avg_smart_1h   = EXCLUDED.avg_smart_1h,
          avg_volume_24h = EXCLUDED.avg_volume_24h,
          updated_at     = now();
        """
    )

    conn.commit()
    # ======================================================
    # DATA CLEANUP
    # ======================================================
    cur.execute("DELETE FROM trades WHERE timestamp < now() - interval '7 days'")
    cur.execute("DELETE FROM uniswap_swaps WHERE timestamp < now() - interval '3 days'")
    cur.execute("DELETE FROM blocks WHERE timestamp < now() - interval '3 days'")
    cur.execute("DELETE FROM token_flow WHERE updated_at < now() - interval '30 days'")

    conn.commit()

    last_sent_date = today
    time.sleep(CHECK_INTERVAL)
