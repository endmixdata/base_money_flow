import time
import psycopg2
from web3 import Web3

print("Indexer started", flush=True)

w3 = Web3(Web3.HTTPProvider("https://base-mainnet.infura.io/v3/bec07fd60dd44de399e3e68ffc508867"))

def wait_for_db():
    while True:
        try:
            conn = psycopg2.connect(
                host="postgres",
                dbname="smartmoney",
                user="smf",
                password="smf_pass"
            )
            return conn
        except psycopg2.OperationalError:
            print("Waiting for Postgres...", flush=True)
            time.sleep(2)

conn = wait_for_db()
cur = conn.cursor()

while True:
    block = w3.eth.block_number
    print("Latest Base block:", block, flush=True)

    cur.execute(
        """
        INSERT INTO blocks(block_number)
        VALUES (%s)
        ON CONFLICT DO NOTHING
        """,
        (block,)
    )
    conn.commit()

    time.sleep(30)
