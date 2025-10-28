# Data Dictionary: Sybil Wallet Feature Set

| Field Name                  | Type     | Description                                                                                         | Example Value         |
|-----------------------------|----------|-----------------------------------------------------------------------------------------------------|----------------------|
| address                     | string   | Ethereum wallet address                                                                             | 0x123...abcd         |
| tx_count                    | int      | Total number of transactions on chain                                                               | 34                   |
| balance_eth                 | float    | Current ETH balance                                                                                 | 0.0035               |
| unique_token_count          | int      | Number of distinct tokens held                                                                      | 12                   |
| total_token_usd_value       | float    | Sum USD value of all tokens held                                                                    | 235.77               |
| spam_token_count            | int      | Number of tokens flagged as spam by Covalent                                                        | 3                    |
| active_days                 | int      | Number of days between first and last transaction                                                   | 715                  |
| avg_tx_per_active_day       | float    | Average tx per day over active span                                                                 | 0.14                 |
| contract_interactions       | int      | Number of transactions involving smart contracts                                                    | 17                   |
| first_tx_timestamp          | string   | ISO timestamp of earliest transaction                                                               | 2022-03-01T00:00Z    |
| last_tx_timestamp           | string   | ISO timestamp of latest transaction                                                                 | 2025-10-17T09:45Z    |
| wallet_age_days             | int      | Days since first transaction to present                                                             | 950                  |
| avg_tx_value_eth            | float    | Mean value of transactions in ETH                                                                   | 0.0021               |
| std_tx_value_eth            | float    | Std deviation of tx values in ETH                                                                   | 0.0059               |
| max_tx_value_eth            | float    | Largest single transaction value in ETH                                                             | 0.03                 |
| min_tx_value_eth            | float    | Smallest single transaction value in ETH                                                            | 0.00001              |
| unique_interacted_addresses | int      | Number of unique addresses interacted with                                                          | 98                   |
| tx_time_entropy             | float    | Shannon entropy of tx hour-of-day distribution                                                      | 2.85                 |
| tx_value_entropy            | float    | Shannon entropy of transaction value distribution                                                   | 1.41                 |
| gas_spent_total_eth         | float    | Total ETH spent on gas fees (all txs)                                                               | 0.00021              |
| avg_gas_price_gwei          | float    | Average gas price (Gwei) over all transactions                                                      | 52.3                 |
| failed_tx_count             | int      | Number of failed transactions                                                                       | 2                    |
| failed_tx_ratio             | float    | Failed transactions / total transactions                                                            | 0.06                 |
| incoming_tx_count           | int      | Transactions received                                                                               | 18                   |
| outgoing_tx_count           | int      | Transactions sent                                                                                   | 16                   |
| self_transfer_count         | int      | Transactions sent to self (same address)                                                            | 1                    |
| unique_contract_count       | int      | Unique contracts interacted with                                                                    | 8                    |
| nft_token_count             | int      | Number of tokens flagged as NFT (ERC721/1155)                                                       | 2                    |
| defi_token_count            | int      | Number of tokens associated with DeFi protocols (Uniswap/Aave/etc.)                                 | 2                    |
| dust_balance_count          | int      | Token balances with tiny USD value (< 0.01)                                                         | 4                    |

