import os
import time
import psycopg2
from web3 import Web3

print("Indexer started", flush=True)

RPC_URL = os.getenv("BASE_RPC_URL")
assert RPC_URL, "BASE_RPC_URL is not set"

POOLS = [
    {
        "token": "WETH",
        "pool": Web3.to_checksum_address(
            "0xd0b53D9277642d899DF5C87A3966A349A798F224"
        ),
        "base_decimals": 18,
        "quote_decimals": 6
    },
    {
        "token": "cbBTC",
        "pool": Web3.to_checksum_address(
            "0xeC558e484cC9f2210714E345298fdc53B253c27D"
        ),
        "base_decimals": 8,
        "quote_decimals": 6
    }
]


WETH_DECIMALS = 18
USDC_DECIMALS = 6

POLL_INTERVAL = 60
BLOCK_BATCH = 50

w3 = Web3(Web3.HTTPProvider(RPC_URL))

SWAP_TOPIC = Web3.keccak(
    text="Swap(address,address,int256,int256,uint160,uint128,int24)"
).hex()
SWAP_TOPIC = "0x" + SWAP_TOPIC


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
            print("Waiting for Postgres...", flush=True)
            time.sleep(2)


conn = wait_for_db()
cur = conn.cursor()

last_block = w3.eth.block_number - 1

while True:
    latest = w3.eth.block_number

    if latest > last_block:
        from_block = last_block + 1
        to_block = min(from_block + BLOCK_BATCH, latest)

        for cfg in POOLS:
            logs = w3.eth.get_logs({
                "fromBlock": from_block,
                "toBlock": to_block,
                "address": cfg["pool"],
                "topics": [SWAP_TOPIC]
            })

            print(
                f"{cfg['token']} | Blocks {from_block}-{to_block} | swaps: {len(logs)}",
                flush=True
            )

            for log in logs:
                trader = Web3.to_checksum_address(
                    "0x" + log["topics"][2].hex()[-40:]
                )

                data = log["data"]
                amount0 = int.from_bytes(data[0:32], "big", signed=True)
                amount1 = int.from_bytes(data[32:64], "big", signed=True)

                base_amount = abs(amount0) / 10 ** cfg["base_decimals"]
                quote_amount = abs(amount1) / 10 ** cfg["quote_decimals"]

                side = "buy" if amount0 < 0 else "sell"
                usd_value = quote_amount

                cur.execute(
                    """
                    INSERT INTO trades
                    (token, tx_hash, block_number, trader, side,
                     eth_amount, usdc_amount, usd_value)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                    """,
                    (
                        cfg["token"],
                        log["transactionHash"].hex(),
                        log["blockNumber"],
                        trader,
                        side,
                        base_amount,
                        quote_amount,
                        usd_value
                    )
                )

        conn.commit()
        last_block = to_block

    time.sleep(POLL_INTERVAL)

