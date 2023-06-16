import os
import requests
import json
from datetime import datetime, timedelta
import yaml
from tqdm import tqdm

# Upload the config file
file = open(f"credentials.yml", 'r')
config = yaml.load(file, Loader=yaml.FullLoader)

# Get Twitter Credentials
ETHERSCAN_API_KEY = config['Etherscan']["API_KEY"]
ADDRESS = config['FixedFloat']["ADDRESS"]

API_URL = f"https://api.etherscan.io/api?module=account&action=txlist&address={ADDRESS}&startblock=0&endblock=99999999&sort=desc&apikey={ETHERSCAN_API_KEY}"

# Conversion factor from wei to Ether
WEI_TO_ETHER = 10 ** 18


# Function to retrieve transactions from Etherscan API
def get_transactions(url):
    response = requests.get(url)
    data = response.json()
    # print(data)
    return data['result'] if 'result' in data else []


# Function to check balance of an Ethereum address
def check_balance(address):
    url = f"https://api.etherscan.io/api?module=account&action=balance&address={address}&tag=latest&apikey={ETHERSCAN_API_KEY}"
    response = requests.get(url)
    data = response.json()
    if data['message'] == 'OK':
        balance_wei = int(data['result'])
        balance_ether = balance_wei / WEI_TO_ETHER
        return balance_ether
    else:
        print(f"Failed to get balance for address {address}. Error message: {data['message']}")
        return None


# Fetch transactions
transactions = get_transactions(API_URL)

filtered_transactions = []

# Get the date 7 days ago
seven_days_ago = datetime.now() - timedelta(days=7)

# Filter transactions
for tx in transactions:
    tx_time = datetime.utcfromtimestamp(int(tx['timeStamp']))
    if tx['from'].lower() == ADDRESS.lower() and tx_time >= seven_days_ago:
        value_ether = int(tx['value']) / WEI_TO_ETHER
        if 0.5 <= value_ether <= 5:
            filtered_transactions.append(tx['to'])

# Get unique addresses
unique_addresses = set(filtered_transactions)

# Filter addresses with balance over 0.5 ETH
addresses_with_balance = []
for address in tqdm(unique_addresses, desc="Checking balances"):
    balance = check_balance(address)
    if balance is not None and balance >= 0.5:
        addresses_with_balance.append(address)

# Ensure 'fixedfloat' directory exists
os.makedirs('fixedfloat', exist_ok=True)

# Write the filtered addresses to a file
with open('fixedfloat/filtered_addresses.json', 'w') as f:
    json.dump(addresses_with_balance, f, indent=2)

print("Addresses written to 'fixedfloat/filtered_addresses.json'")
