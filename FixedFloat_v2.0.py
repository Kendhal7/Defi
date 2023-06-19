from datetime import datetime, timedelta
from dataclasses import dataclass
from operator import getitem
from functools import reduce
from pathlib import Path
from typing import List
from tqdm import tqdm
import requests
import schedule
import sqlite3
import yaml
import json
import time


@dataclass
class Config:
    file_path: str

    def __post_init__(self):
        self.data = self.load_config()

    def load_config(self) -> dict:
        with open(self.file_path, 'r') as file:
            return yaml.safe_load(file)

    def get_value(self, key: str) -> str:
        """Get a nested value from the config file using a dot-separated string."""
        return reduce(getitem, key.split('.'), self.data)


@dataclass
class EtherscanAPI:
    api_key: str
    WEI_TO_ETHER = 10 ** 18

    def get_transactions(self, address: str) -> List[dict]:
        url = f"https://api.etherscan.io/api?module=account&action=txlist&address={address}&startblock=0&endblock=99999999&sort=desc&apikey={self.api_key}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            return data.get('result', [])
        response.raise_for_status()

    def was_address_active_before(self, address: str, timestamp: datetime, txhash: str) -> bool:
        transactions = self.get_transactions(address)
        for tx in transactions:
            if tx['hash'] == txhash:
                continue
            tx_time = datetime.utcfromtimestamp(int(tx['timeStamp']))
            if tx_time < timestamp:
                return True
        return False

    def did_address_create_contract(self, address: str) -> bool:
        transactions = self.get_transactions(address)
        for tx in transactions:
            if tx['to'] == '':
                return True
        return False

    def did_address_swap(self, address: str) -> bool:
        transactions = self.get_transactions(address)
        for tx in transactions:
            if 'functionName' in tx and 'swapExactETHForTokens' in tx['functionName']:
                return True
        return False


class FileManager:
    @staticmethod
    def create_dir(path: str) -> None:
        Path(path).mkdir(parents=True, exist_ok=True)

    @staticmethod
    def write_to_file(file_path: str, data: dict) -> None:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)


class DBManager:
    def __init__(self, db_file):
        self.conn = sqlite3.connect(db_file)
        self.c = self.conn.cursor()
        self.c.execute('''CREATE TABLE IF NOT EXISTS addresses
                     (address text UNIQUE)''')

    def insert_address(self, address):
        try:
            self.c.execute("INSERT INTO addresses VALUES (?)", (address,))
        except sqlite3.IntegrityError:
            pass  # address already exists in the database

    def get_all_addresses(self):
        return [record[0] for record in self.c.execute('SELECT address FROM addresses')]

    def remove_address(self, address: str):
        self.c.execute("DELETE FROM addresses WHERE address=?", (address,))

    def close_connection(self):
        self.conn.commit()
        self.conn.close()


def check_swaps():
    db = DBManager('addresses.db')
    addresses = db.get_all_addresses()

    etherscan = EtherscanAPI(Config("credentials.yml").get_value('Etherscan.API_KEY'))

    addresses_with_swap = []
    for address in tqdm(addresses, desc="Checking swaps"):
        if etherscan.did_address_swap(address):
            addresses_with_swap.append(address)
        elif etherscan.did_address_create_contract(address):  # Check for contract creation
            db.remove_address(address)  # Remove address from DB if contract was created

    print(f"\nAddresses that performed a swap: {addresses_with_swap}")

    db.close_connection()


def main():
    # Load the config file
    config = Config("credentials.yml")

    # Get credentials
    ETHERSCAN_API_KEY = config.get_value('Etherscan.API_KEY')
    ADDRESS = config.get_value('FixedFloat.ADDRESS')

    # Instantiate the EtherscanAPI
    etherscan = EtherscanAPI(ETHERSCAN_API_KEY)

    # Fetch transactions
    transactions = etherscan.get_transactions(ADDRESS)

    filtered_transactions = []
    print(datetime.now())
    time_threshold = datetime.now() - timedelta(minutes=30)

    # Filter transactions
    for tx in transactions:
        tx_time = datetime.utcfromtimestamp(int(tx['timeStamp']))
        if tx['from'].lower() == ADDRESS.lower() and tx_time >= (time_threshold - timedelta(hours=2)):
            value_ether = int(tx['value']) / EtherscanAPI.WEI_TO_ETHER
            if 0.1 <= value_ether <= 10:
                filtered_transactions.append(tx)

    # Filter addresses with no activity before the transaction from the target wallet
    addresses_with_no_prior_activity = []
    for tx in tqdm(filtered_transactions, desc="Checking prior activity"):
        address = tx['to']
        tx_time = datetime.utcfromtimestamp(int(tx['timeStamp']))
        tx_hash = tx['hash']
        if not etherscan.was_address_active_before(address, tx_time, tx_hash):
            addresses_with_no_prior_activity.append(address)

    print('\nNo Prior Activity:\n', addresses_with_no_prior_activity, '\n')

    # Filter addresses that created contracts
    addresses_without_contracts = []
    for address in tqdm(addresses_with_no_prior_activity, desc="Checking contract creation"):
        if not etherscan.did_address_create_contract(address):
            addresses_without_contracts.append(address)

    print('\nAddresses without contract creation:\n', addresses_without_contracts, '\n')

    # Write the filtered addresses to a SQLite database
    db = DBManager('addresses.db')
    for address in addresses_without_contracts:
        db.insert_address(address)
    db.close_connection()

    print("\nAddresses written to 'addresses.db'")


def job():
    main()


if __name__ == "__main__":
    schedule.every(1).minutes.do(job)
    schedule.every(1).minutes.do(check_swaps)

    while True:
        schedule.run_pending()
        time.sleep(1)
