import os
import csv
import json
import math
import time
import random
import requests
import numpy as np
import pandas as pd
from tqdm import tqdm
from datetime import datetime, timezone
from collections import defaultdict

COVALENT_API_KEY = "cqt_rQ9KjFqG4f3x6cpgdWcQCDwCpj6j"  # 🔑 Replace this
RPC_URL = "https://eth-mainnet.g.alchemy.com/v2/WvUTtG0FBJY_46BC2-n0X"
CHAIN_ID = 1
INPUT_CSV = "/home/user/pond-bot-detection-bounty/data/genuine_wallets_list.csv"
OUTPUT_CSV = "/home/user/pond-bot-detection-bounty/data/genuine_wallet_features.csv"
BATCH_SAVE_INTERVAL = 50

def safe_request(url, params=None, retries=3, sleep=2):
    for attempt in range(retries):
        try:
            resp = requests.get(url, params=params, timeout=30)
            if resp.status_code == 200:
                return resp.json()
        except Exception:
            time.sleep(sleep * (attempt + 1))
    return None


def fetch_transactions(address, max_pages=5, page_size=100):
    txs = []
    for page in range(1, max_pages + 1):
        url = f"https://api.covalenthq.com/v1/{CHAIN_ID}/address/{address}/transactions_v3/"
        params = {"page-size": page_size, "page-number": page, "key": COVALENT_API_KEY}
        data = safe_request(url, params)
        if not data or "data" not in data or not data["data"]["items"]:
            break
        txs.extend(data["data"]["items"])
        if not data["data"].get("pagination", {}).get("has_more"):
            break
    return txs


def fetch_token_balances(address):
    url = f"https://api.covalenthq.com/v1/{CHAIN_ID}/address/{address}/balances_v2/"
    params = {"key": COVALENT_API_KEY}
    data = safe_request(url, params)
    if not data or "data" not in data:
        return [], 0, 0, 0
    items = data["data"]["items"]
    tokens = [t for t in items if t.get("type") == "cryptocurrency"]
    unique_token_count = len(tokens)
    spam_token_count = len([t for t in items if t.get("is_spam")])
    total_usd_value = sum([float(t.get("quote", 0) or 0) for t in items])
    return tokens, unique_token_count, total_usd_value, spam_token_count


def compute_entropy(values):
    if len(values) == 0:
        return 0.0
    values = np.array(values)
    unique, counts = np.unique(values, return_counts=True)
    probs = counts / counts.sum()
    return float(-np.sum(probs * np.log2(probs)))


def extract_features_for_address(address):
    features = defaultdict(lambda: None)
    features["address"] = address

    txs = fetch_transactions(address)
    if len(txs) == 0:
        # Minimal default row
        features.update({
            "tx_count": 0,
            "balance_eth": 0,
            "unique_token_count": 0,
            "total_token_usd_value": 0,
            "spam_token_count": 0,
            "active_days": 0,
            "avg_tx_per_active_day": 0,
            "contract_interactions": 0,
            "first_tx_timestamp": None,
            "last_tx_timestamp": None,
            "wallet_age_days": 0,
            "avg_tx_value_eth": 0,
            "std_tx_value_eth": 0,
            "max_tx_value_eth": 0,
            "min_tx_value_eth": 0,
            "unique_interacted_addresses": 0,
            "tx_time_entropy": 0,
            "tx_value_entropy": 0,
            "gas_spent_total_eth": 0,
            "avg_gas_price_gwei": 0,
            "failed_tx_count": 0,
            "failed_tx_ratio": 0,
            "incoming_tx_count": 0,
            "outgoing_tx_count": 0,
            "self_transfer_count": 0,
            "unique_contract_count": 0,
            "nft_token_count": 0,
            "defi_token_count": 0,
            "dust_balance_count": 0
        })
        return features

    # --- Transaction times ---
    timestamps = [
        datetime.fromtimestamp(tx["block_signed_at_ts"], tz=timezone.utc)
        for tx in txs if tx.get("block_signed_at_ts")
    ]
    if len(timestamps) > 0:
        features["first_tx_timestamp"] = min(timestamps)
        features["last_tx_timestamp"] = max(timestamps)
        features["wallet_age_days"] = max(1, (features["last_tx_timestamp"] - features["first_tx_timestamp"]).days)
        active_days = len(set([t.date() for t in timestamps]))
        features["active_days"] = active_days
        features["avg_tx_per_active_day"] = len(txs) / active_days if active_days else len(txs)
    else:
        features["active_days"] = 0
        features["wallet_age_days"] = 0
        features["avg_tx_per_active_day"] = 0

    # --- Transaction stats ---
    values = []
    gas_spent = []
    interacted_addresses = set()
    failed_tx = 0
    incoming, outgoing, self_tx = 0, 0, 0
    contract_interactions = 0

    for tx in txs:
        val = float(tx.get("value", 0) or 0) / 1e18
        values.append(val)
        if tx.get("gas_spent"):
            gas_spent.append(float(tx["gas_spent"]) / 1e18)
        from_addr = str(tx.get("from_address", "")).lower()
        to_addr = str(tx.get("to_address", "")).lower() if tx.get("to_address") else None
        if not from_addr or not to_addr:
            continue
        if from_addr == address.lower() and to_addr == address.lower():
            self_tx += 1
        elif from_addr == address.lower():
            outgoing += 1
        elif to_addr == address.lower():
            incoming += 1
        interacted_addresses.add(from_addr)
        interacted_addresses.add(to_addr)
        if tx.get("successful") is False:
            failed_tx += 1
        if tx.get("to_address_label") == "Contract":
            contract_interactions += 1

    if len(values) > 0:
        values_np = np.array(values)
        features["avg_tx_value_eth"] = float(np.mean(values_np))
        features["std_tx_value_eth"] = float(np.std(values_np))
        features["max_tx_value_eth"] = float(np.max(values_np))
        features["min_tx_value_eth"] = float(np.min(values_np))
        features["tx_value_entropy"] = compute_entropy(np.round(values_np, 5))
    else:
        features["avg_tx_value_eth"] = features["std_tx_value_eth"] = 0
        features["max_tx_value_eth"] = features["min_tx_value_eth"] = 0
        features["tx_value_entropy"] = 0

    features["tx_time_entropy"] = compute_entropy([t.timestamp() for t in timestamps]) if len(timestamps) > 0 else 0
    features["unique_interacted_addresses"] = len(interacted_addresses)
    features["gas_spent_total_eth"] = sum(gas_spent)
    gas_prices = [float(tx.get("gas_price", 0)) / 1e9 for tx in txs if tx.get("gas_price")]
    features["avg_gas_price_gwei"] = float(np.mean(gas_prices)) if len(gas_prices) > 0 else 0
    features["failed_tx_count"] = failed_tx
    features["failed_tx_ratio"] = failed_tx / len(txs) if len(txs) > 0 else 0
    features["incoming_tx_count"] = incoming
    features["outgoing_tx_count"] = outgoing
    features["self_transfer_count"] = self_tx
    features["contract_interactions"] = contract_interactions

    tokens, uniq_count, usd_val, spam_count = fetch_token_balances(address)
    features["unique_token_count"] = uniq_count
    features["total_token_usd_value"] = usd_val
    features["spam_token_count"] = spam_count
    features["nft_token_count"] = len([t for t in tokens if t.get("supports_erc721")])
    features["defi_token_count"] = len([t for t in tokens if "defi" in (t.get("contract_name", "").lower())])
    features["dust_balance_count"] = len([t for t in tokens if float(t.get("balance", 0)) / (10 ** int(t.get("contract_decimals", 18))) < 0.00001])

    return features


def main():
    wallets = pd.read_csv(INPUT_CSV)["address"].dropna().unique().tolist()
    print(f"Loaded {len(wallets)} genuine wallets from CSV")

    all_features = []
    if os.path.exists(OUTPUT_CSV):
        all_features = pd.read_csv(OUTPUT_CSV).to_dict("records")
        done_addrs = {f["address"] for f in all_features}
        wallets = [w for w in wallets if w not in done_addrs]
        print(f"Resuming from checkpoint, {len(wallets)} remaining wallets...")

    progress = tqdm(wallets, desc="Extracting features", ncols=100)
    for i, addr in enumerate(progress, 1):
        try:
            feats = extract_features_for_address(addr)
            all_features.append(feats)
        except Exception as e:
            print(f"[Error] {addr}: {e}")
            continue

        if i % BATCH_SAVE_INTERVAL == 0 or i == len(wallets):
            pd.DataFrame(all_features).to_csv(OUTPUT_CSV, index=False)
            progress.set_postfix_str(f"Saved {len(all_features)} wallets")

        time.sleep(random.uniform(0.5, 1.2))

    print(f"✅ Completed extraction for {len(all_features)} wallets")
    pd.DataFrame(all_features).to_csv(OUTPUT_CSV, index=False)


if __name__ == "__main__":
    main()
