import time
import psycopg2

TOP_N = 10
MIN_TRADES = 3

INTERVALS = {
    "1h": "1 hour",
    "24h": "24 hours"
}

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

while True:
    # 1. Calculate smart wallets (24h)
    cur.execute(
        f"""
        WITH ranked AS (
          SELECT
            trader,
            COUNT(*) AS trades,
            SUM(usd_value) AS volume,
            RANK() OVER (ORDER BY SUM(usd_value) DESC) AS rnk
          FROM trades
          WHERE timestamp > now() - interval '24 hours'
          GROUP BY trader
        )
        SELECT trader, trades, volume, rnk
        FROM ranked
        WHERE rnk <= {TOP_N}
          AND trades >= {MIN_TRADES}
        """
    )

    smart = cur.fetchall()

    cur.execute("DELETE FROM smart_wallets")

    for wallet, trades, volume, rnk in smart:
        cur.execute(
            """
            INSERT INTO smart_wallets
            (wallet, trades, volume, rank)
            VALUES (%s, %s, %s, %s)
            """,
            (wallet, trades, volume, rnk)
        )

    # 2. Smart Money Flow
    for period, interval in INTERVALS.items():
        cur.execute(
            f"""
            SELECT
              SUM(CASE WHEN side='buy'  THEN usd_value ELSE 0 END),
              SUM(CASE WHEN side='sell' THEN usd_value ELSE 0 END)
            FROM trades
            WHERE trader IN (SELECT wallet FROM smart_wallets)
              AND timestamp > now() - interval '{interval}'
            """
        )

        inflow, outflow = cur.fetchone()
        inflow = inflow or 0
        outflow = outflow or 0
        net_flow = inflow - outflow

        cur.execute(
            """
            INSERT INTO token_flow (period, inflow, outflow, net_flow)
            VALUES (%s, %s, %s, %s)
            """,
            (f"smart_{period}", inflow, outflow, net_flow)
        )

    conn.commit()
    time.sleep(300)
