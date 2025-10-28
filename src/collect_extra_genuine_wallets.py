#!/usr/bin/env python3
"""
collect_extra_genuine_wallets.py

Collect ~600 additional historical genuine (EOA) wallets by scanning older blocks
using Alchemy RPC. Saves results to:
  ./data/genuine_wallets_extra.csv

If ./data/genuine_wallets_list.csv exists, the script will avoid adding duplicates
and will optionally merge and write a combined file ./data/genuine_wallets_combined.csv

Configurable parameters are at the top of the file.
"""

import csv
import os
import random
import time
from pathlib import Path

from tqdm import tqdm
from web3 import Web3

# ---------------- CONFIG ----------------
RPC_URL = "https://eth-mainnet.g.alchemy.com/v2/WvUTtG0FBJY_46BC2-n0X"

# Target number of new genuine wallets to collect
TARGET_NEW_WALLETS = 600

# Block range to sample (older blocks -> older wallets).
# Adjust these to focus on particular years. Defaults chosen to capture ~2019-2022 era.
START_BLOCK = 10_000_000   # adjust if desired
END_BLOCK = 14_000_000     # adjust if desired

# How many blocks to skip between samples (larger -> faster & more spread out)
BLOCK_STEP = 37

# Limit max transactions read per block to avoid huge block scans
MAX_TXS_PER_BLOCK = 200

# Sleep between RPC calls to be gentle on the provider (seconds)
SLEEP_BETWEEN_BLOCKS = 0.18

# File paths
DATA_DIR = Path("./data")
EXISTING_GENUINE_FILE = DATA_DIR / "genuine_wallets_list.csv"
EXTRA_OUT_FILE = DATA_DIR / "genuine_wallets_extra.csv"
COMBINED_OUT_FILE = DATA_DIR / "genuine_wallets_combined.csv"
# ----------------------------------------

DATA_DIR.mkdir(parents=True, exist_ok=True)

w3 = Web3(Web3.HTTPProvider(RPC_URL, request_kwargs={"timeout": 30}))

if not w3.is_connected():
    raise SystemExit(f"ERROR: Could not connect to RPC at {RPC_URL}. Check your URL/key and network.")

def is_eoa(address: str) -> bool:
    """
    Return True if address is an EOA (no contract code present).
    web3.eth.get_code returns a HexBytes object - treat '0x' or empty as EOA.
    """
    try:
        code = w3.eth.get_code(Web3.to_checksum_address(address))
        # HexBytes(b'') -> b'' . hex() -> '0x'
        code_hex = code.hex() if hasattr(code, "hex") else str(code)
        return code_hex in ("0x", "0x0", "")
    except Exception:
        # If RPC hiccup, assume not EOA (safer) — but we swallow error to continue
        return False

def safe_get_block(bnum: int):
    """Fetch block with full transactions, but return None on failure."""
    try:
        block = w3.eth.get_block(bnum, full_transactions=True)
        return block
    except Exception as e:
        # print(f"[block {bnum}] RPC error: {e}")
        return None

def read_existing_addresses(path: Path):
    """Read existing addresses from CSV if present (single-column CSV or header)."""
    existing = set()
    if not path.exists():
        return existing
    try:
        with path.open("r", newline="") as f:
            reader = csv.reader(f)
            for row in reader:
                if not row:
                    continue
                addr = row[0].strip()
                if addr.startswith("address") or addr.lower() == "wallet":
                    # skip header-like lines
                    continue
                if addr and len(addr) == 42 and addr.startswith("0x"):
                    existing.add(addr.lower())
    except Exception as e:
        print(f"Warning: could not read {path}: {e}")
    return existing

def write_addresses(path: Path, addrs):
    """Write addresses (iterable) to CSV, one per line (no header)."""
    with path.open("w", newline="") as f:
        writer = csv.writer(f)
        for a in addrs:
            writer.writerow([a])

def collect_new_wallets():
    existing = read_existing_addresses(EXISTING_GENUINE_FILE)
    print(f"Found {len(existing)} existing genuine addresses (will avoid duplicates).")

    found = set()
    # Pre-seed found with existing to simplify dedupe logic; we will only count new.
    already_seen = set(existing)

    # iterate block numbers in a spread-out way; stepping avoids scanning every block
    block_numbers = list(range(START_BLOCK, END_BLOCK + 1, BLOCK_STEP))

    # randomize order so results are not biased by contiguous block clusters
    random.shuffle(block_numbers)

    pbar = tqdm(total=TARGET_NEW_WALLETS, desc="Collecting new genuine wallets")
    try:
        for bn in block_numbers:
            if len(found) >= TARGET_NEW_WALLETS:
                break

            block = safe_get_block(bn)
            if block is None:
                time.sleep(SLEEP_BETWEEN_BLOCKS)
                continue

            txs = block.transactions or []
            # sample transactions to limit per-block processing
            if len(txs) > MAX_TXS_PER_BLOCK:
                txs_sample = random.sample(txs, MAX_TXS_PER_BLOCK)
            else:
                txs_sample = txs

            for tx in txs_sample:
                # Try to get from and to addresses
                try:
                    fr = (tx["from"] or "").lower()
                except Exception:
                    fr = None
                try:
                    to = (tx["to"] or "").lower()
                except Exception:
                    to = None

                candidates = []
                if fr:
                    candidates.append(fr)
                if to:
                    candidates.append(to)

                for addr in candidates:
                    if not addr or len(addr) != 42 or not addr.startswith("0x"):
                        continue
                    if addr in already_seen:
                        continue  # skip duplicates and existing
                    # Check EOA
                    if not is_eoa(addr):
                        continue
                    # Optionally ensure this address has at least one historical tx (we sampled it from txs)
                    # Optionally check balance > 0 to bias toward "real" wallets (commented out)
                    # try:
                    #     bal = w3.eth.get_balance(Web3.to_checksum_address(addr))
                    #     if bal == 0:
                    #         continue
                    # except Exception:
                    #     pass

                    # Accept this address
                    found.add(addr)
                    already_seen.add(addr)
                    pbar.update(1)
                    if len(found) >= TARGET_NEW_WALLETS:
                        break
                if len(found) >= TARGET_NEW_WALLETS:
                    break

            time.sleep(SLEEP_BETWEEN_BLOCKS)
    except KeyboardInterrupt:
        print("\nInterrupted by user — saving current results...")

    pbar.close()
    return sorted(found)

def merge_with_existing(existing_path: Path, extra_path: Path, combined_path: Path):
    existing = read_existing_addresses(existing_path)
    extra = read_existing_addresses(extra_path)
    combined = sorted(existing.union(extra))
    write_addresses(combined_path, combined)
    print(f"Merged {len(existing)} existing + {len(extra)} extra -> {len(combined)} combined addresses.")
    return combined

if __name__ == "__main__":
    print("Collecting extra genuine wallets using Alchemy RPC.")
    print(f"Block range: {START_BLOCK} -> {END_BLOCK} (step {BLOCK_STEP}), target new: {TARGET_NEW_WALLETS}")

    new_wallets = collect_new_wallets()
    print(f"\nCollected {len(new_wallets)} new genuine wallet addresses.")

    if new_wallets:
        write_addresses(EXTRA_OUT_FILE, new_wallets)
        print(f"Wrote new addresses to {EXTRA_OUT_FILE}")

    # If existing file present, merge and write combined
    if EXISTING_GENUINE_FILE.exists():
        merged = merge_with_existing(EXISTING_GENUINE_FILE, EXTRA_OUT_FILE, COMBINED_OUT_FILE)
        print(f"Combined file saved to {COMBINED_OUT_FILE}")
    else:
        # No existing file: write new as combined
        write_addresses(COMBINED_OUT_FILE, new_wallets)
        print(f"No existing genuine list found. New list written to {COMBINED_OUT_FILE}")

    print("Done.")
