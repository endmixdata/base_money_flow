from web3 import Web3
import os

RPC_URL = "https://base-mainnet.infura.io/v3/bec07fd60dd44de399e3e68ffc508867"
w3 = Web3(Web3.HTTPProvider(RPC_URL))

FACTORY = Web3.to_checksum_address(
    "0x33128a8fC17869897dcE68Ed026d694621f6FDfD"
)

cbBTC = Web3.to_checksum_address(
    "0xcbB7C0000000000000000000000000000000000"
)

USDC = Web3.to_checksum_address(
    "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
)

FACTORY_ABI = [
    {
        "inputs": [
            {"internalType": "address", "name": "tokenA", "type": "address"},
            {"internalType": "address", "name": "tokenB", "type": "address"},
            {"internalType": "uint24", "name": "fee", "type": "uint24"}
        ],
        "name": "getPool",
        "outputs": [
            {"internalType": "address", "name": "pool", "type": "address"}
        ],
        "stateMutability": "view",
        "type": "function"
    }
]

factory = w3.eth.contract(address=FACTORY, abi=FACTORY_ABI)

pool = factory.functions.getPool(cbBTC, USDC, 500).call()
print("cbBTC / USDC pool:", pool)
