# Sybil/Bot Wallet Detection Dataset & Analysis (Pond Bounty)

---

## 1. Overview

This repository provides a dataset and analysis pipeline for detecting Sybil and bot wallets on the Ethereum blockchain, specifically for the Pond bounty challenge.

The core of this submission is not just a dataset, but a transparent, end-to-end analysis that:

- Identifies and removes significant data leakage found in the raw data.
- Establishes a high-performing (95.93% accuracy) and honest baseline model.
- Identifies the true behavioral and financial features that predict Sybil activity in this dataset.

---

## 2. Problem Statement

Online platforms are frequently targeted by spam, Sybil attacks, and automated bots seeking to manipulate reward systems. Detecting inauthentic wallet behaviors is essential for platform fairness and security.

This project provides:

- A high-quality Ethereum wallet dataset enriched with on-chain features.
- A fully reproducible analysis pipeline.
- A proven honest baseline model.

---

## 3. Data Sources & Initial Dataset

| Component | Description |
|---|---|
| Wallet Addresses | 3,686 wallets labeled as **Sybil (1)** or **Not Sybil (0)** |
| On-chain Features | Transaction & token data extracted using Covalent API |
| Class Balance | 1,894 Not Sybil (51.4%) • 1,792 Sybil (48.6%) |

Feature extraction procedure is implemented in **`fetch_wallet_features.py`**.

---

## 4. Analysis: From **100% (Leakage)** to **95.93% (Honest)**

### **Step 1 — The 100% Accuracy Red Flag**
A baseline `RandomForestClassifier` achieved **100% accuracy** — a strong sign of **data leakage**.

### **Step 2 — Leakage Discovery**
Feature importance analysis & visualization identified the leaking features:

| Leaking Feature | Reason for Leakage |
|---|---|
| `wallet_age_days` | Completely separated between classes |
| `active_days` | 0 for all Not Sybil wallets |
| `gas_spent_total_eth` | Direct proxy for wallet legitimacy |
| `tx_time_entropy` | Behaviorally unique to true users |

These features effectively encoded the answer — making the dataset unfair.

### **Step 3 — The Honest Baseline Model (95.93%)**
After removing 13 problematic features, a new RandomForest model was trained on **17 valid features**.

| Metric | Value |
|---|---|
| **Accuracy** | **0.96** |

| Class | Precision | Recall | F1-Score |
|---|:---:|:---:|:---:|
| Not Sybil (0) | 0.97 | 0.96 | 0.96 |
| Sybil (1) | 0.95 | 0.96 | 0.96 |
| Macro Avg | 0.96 | 0.96 | 0.96 |

This performance reflects actual behavioral signal — not leakage.

---

## 5. Final Dataset & Key Features

The final model uses **`final_submission_dataset.csv`** containing **17 verified features + target variable (`is_sybil`)**.

### Top Predictive Features (Honest Model)

| Feature | Importance | Insight |
|---|:---:|---|
| `total_token_usd_value` | 0.122 | Financial capacity matters |
| `unique_token_count` | 0.113 | Portfolio diversity is meaningful |
| `avg_gas_price_gwei` | 0.095 | Indicates real network participation |
| `failed_tx_ratio` | 0.086 | Sybils exhibit distinct tx error patterns |
| `avg_tx_value_eth` | 0.081 | Economic behavior differs |
| `spam_token_count` | 0.059 | Sybils accumulate low-value airdrops |
| `tx_value_entropy` | 0.058 | Transaction randomness signals authenticity |

### Full Feature List (17 Features)

**Financial**
```
total_token_usd_value
avg_tx_value_eth
std_tx_value_eth
max_tx_value_eth
min_tx_value_eth
```

**Portfolio**
```
unique_token_count
spam_token_count
defi_token_count
dust_balance_count
```

**Behavioral & Network**
```
unique_interacted_addresses
tx_value_entropy
avg_gas_price_gwei
failed_tx_count
failed_tx_ratio
incoming_tx_count
outgoing_tx_count
self_transfer_count
```

---

## 6. Reproducibility & Pipeline

| File | Purpose |
|---|---|
| `master_wallet_dataset.csv` | Original dataset with 31 features (contains leakage) |
| `final_submission_dataset.csv` | Cleaned dataset with 17 valid features |
| `create_final_dataset.py` | Reproduces final cleaned dataset |

### EDA & Modeling Scripts
```
eda_step_1_load.py
eda_step_2_distributions.py
eda_step_3_baseline_model.py          # (Leakage demonstration only – do not use)
eda_step_4_leakage_check.py
eda_step_5_honest_baseline_model.py   # Final 95.93% model
```

---

## Summary

This work demonstrates a **complete, honest Sybil-detection pipeline**, including:

- Leakage detection & correction.
- Clean dataset creation.
- High-performing, behavior-based Sybil classifier.
- Full reproducibility.

This ensures **fair, realistic, and trustworthy Sybil detection** suitable for research & real-world applications.

---