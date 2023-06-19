import json
import os
from datetime import datetime, timedelta
from typing import List

import requests
import yaml
from tqdm import tqdm


class Config:
    def __init__(self, file_path: str) -> None:
        self.file_path = file_path
        self.data = self.load_config()

    def load_config(self) -> dict:
        with open(self.file_path, 'r') as file:
            return yaml.safe_load(file)

    def get_value(self, key: str) -> str:
        keys = key.split('.')
        value = self.data
        for k in keys:
            value = value[k]
        return value


class EtherscanAPI:
    WEI_TO_ETHER = 10 ** 18

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    def get_transactions(self, address: str) -> List[dict]:
        url = f"https://api.etherscan.io/api?module=account&action=txlist&address={address}&startblock=0&endblock=99999999&sort=desc&apikey={self.api_key}"
        response = requests.get(url)
        data = response.json()
        return data.get('result', [])

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
            # A contract creation transaction has its `to` field as null
            # and `input` field contains the contract creation code
            if tx['to'] == '':  # `input` is '0x' for non-contract creation transactions
                return True
        return False


class FileManager:
    @staticmethod
    def create_dir(path: str) -> None:
        os.makedirs(path, exist_ok=True)

    @staticmethod
    def write_to_file(file_path: str, data: dict) -> None:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)


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
    time_threshold = datetime.now() - timedelta(hours=5)

    # Filter transactions
    for tx in transactions:
        tx_time = datetime.utcfromtimestamp(int(tx['timeStamp']))
        if tx['from'].lower() == ADDRESS.lower() and tx_time >= (time_threshold - timedelta(hours=2)):
            value_ether = int(tx['value']) / EtherscanAPI.WEI_TO_ETHER
            if 0.5 <= value_ether <= 5:
                filtered_transactions.append(tx)

    # Filter addresses with no activity before the transaction from the target wallet
    addresses_with_no_prior_activity = []
    for tx in tqdm(filtered_transactions, desc="Checking prior activity"):
        address = tx['to']
        tx_time = datetime.utcfromtimestamp(int(tx['timeStamp']))
        tx_hash = tx['hash']
        if not etherscan.was_address_active_before(address, tx_time, tx_hash):
            addresses_with_no_prior_activity.append(address)

    print(addresses_with_no_prior_activity)

    # Filter addresses that created contracts
    addresses_without_contracts = []
    for address in tqdm(addresses_with_no_prior_activity, desc="Checking contract creation"):
        if not etherscan.did_address_create_contract(address):
            addresses_without_contracts.append(address)

    print(addresses_without_contracts)

    # Ensure 'fixedfloat' directory exists
    FileManager.create_dir('fixedfloat')

    # Write the filtered addresses to a file
    FileManager.write_to_file('fixedfloat/filtered_addresses.json', addresses_without_contracts)

    print("Addresses written to 'fixedfloat/filtered_addresses.json'")


if __name__ == "__main__":
    main()
