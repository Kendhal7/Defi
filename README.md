# Defi

# 1. Ethereum Token Transaction Analyzer

This Python script reads transaction data from CSV files, cleans and processes the data, and performs a simple analysis of the transactions. It calculates the number of tokens bought, the number of wins (where total sold > total bought + fee amount), and the win ratio. The results are saved in CSV files.

## Requirements

- Python 3.7 or higher.
- Python packages: pandas

## Setup

1. Clone the repository and navigate into it:
```bash
git clone https://github.com/your_username/your_repository.git
cd your_repository
```

2. Install the required Python packages:
```bash
pip install -r requirements.txt
```

## Usage

1. Place the CSV files you want to analyze in a folder named 'csv' in the same directory as the script.
2. Run the script:
```bash
python analyze_transactions.py
```

3. The results will be saved in a subfolder 'csv/results' in the same directory as the script.

## Explanation

- `process_currency(currency)`: Processes the currency value from each cell, splitting on newline and returning the correct value.
- `load_and_clean_data(filepath)`: Loads data from a CSV file, cleans it, and returns a DataFrame and the Ethereum address.
- `aggregate_amounts(df, ETH_address)`: Aggregates the buy and sell amounts for each token and returns a DataFrame with the aggregated values.
- `calculate_win_ratio(result, file_name)`: Calculates the win ratio, saves the results to a CSV file, and prints the number of tokens bought, number of wins, and win ratio.
- The script runs the above functions for each CSV file in the 'csv' folder.

# 2. Ethereum Address Link Finder

This Python script finds connections between a given Ethereum address and a list of target addresses. It traverses the Ethereum transaction graph, finding the shortest path (in terms of transaction hops) from the input address to each of the target addresses.

## Requirements

- Python 3.7 or higher.
- Python packages: requests, pyyaml

## Setup

1. Clone the repository and navigate into it:
```bash
git clone https://github.com/Kendhal7/Defi.git
cd your_repository
```

2. Install the required Python packages:
```bash
pip install -r requirements.txt
```

3. Obtain an Etherscan API key by signing up at etherscan.io.
4. Create a credentials.yml file in the same directory as the script and insert your Etherscan API key:
````yaml
Etherscan:
  API_KEY: "your_etherscan_api_key_here"
````

## Usage

Modify the start_address and target_addresses variables in the main() function in address_link_finder.py script according to your needs.

To run the script, use the following command in your terminal:

```bash
python3 address_link_finder.py
```

## Output

The script outputs the shortest path (in terms of transaction hops) from the input address to each of the target addresses, along with the transaction hash of each hop.

Here is an example output:

```vbnet
0x047B572a5b30E469B74A5947CAf3491801599e9a linked to 0x047B572a5b30E469B74A5947CAf3491801599e9b after 3 hops 

The path is:

Address: 0x047B572a5b30E469B74A5947CAf3491801599e9a - Transaction Hash: None
Address: 0x047B572a5b30E469B74A5947CAf3491801599e9x - Transaction Hash: 0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
Address: 0x047B572a5b30E469B74A5947CAf3491801599e9q - Transaction Hash: 0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
Address: 0x047B572a5b30E469B74A5947CAf3491801599e9b - Transaction Hash: 0xcccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc
```

## Notes

- The performance of this script heavily depends on the complexity of the Ethereum transaction graph and the number of hops it has to traverse. If the number of hops or target addresses is large, the script can slow down significantly.
- To overcome the limitations of the free tier of the Etherscan API, the script includes a limit on the maximum number of transactions processed for each address, which can be adjusted in the find_hops function.