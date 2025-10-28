import requests
import time
import pandas as pd

RPC_URL = "https://eth-mainnet.g.alchemy.com/v2/WvUTtG0FBJY_46BC2-n0X"

def get_wallets_from_recent_blocks(start_block, end_block, max_wallets=2000):
    wallets = set()
    for block_num in range(start_block, end_block + 1):
        payload = {
            "jsonrpc": "2.0",
            "method": "eth_getBlockByNumber",
            "params": [hex(block_num), True],
            "id": 1
        }
        try:
            resp = requests.post(RPC_URL, json=payload, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            result = data.get("result")
            if not isinstance(result, dict):
                print(f"Error fetching block {block_num}: {result}")
                time.sleep(1)
                continue

            for tx in result.get("transactions", []):
                if tx.get("from"):
                    wallets.add(tx["from"].lower())
                if tx.get("to"):
                    wallets.add(tx["to"].lower())

            print(f"Fetched block {block_num}: {len(wallets)} wallets so far")
            if len(wallets) >= max_wallets:
                break
            time.sleep(0.25)

        except Exception as e:
            print(f"Error at block {block_num}: {e}")
            time.sleep(1)

    return list(wallets)[:max_wallets]


if __name__ == "__main__":
    start_block = 18000000 - 50
    end_block = 18000000
    wallets = get_wallets_from_recent_blocks(start_block, end_block, max_wallets=1500)
    pd.DataFrame(wallets, columns=["address"]).to_csv("genuine_wallets_list.csv", index=False)
    print(f"✅ Saved {len(wallets)} wallet addresses.")
