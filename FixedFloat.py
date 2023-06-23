from datetime import datetime, timedelta
from dataclasses import dataclass
from operator import getitem
from functools import reduce
from pathlib import Path
from typing import List, Dict
from psycopg2 import sql
from tqdm import tqdm
import psycopg2
import requests
import schedule
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


class TelegramAlert:

    def __init__(self):
        config = Config("credentials.yml")
        self.token_id = config.get_value('Telegram.TOKEN_ID')
        self.chat_id = config.get_value('Telegram.CHAT_ID')

    def send_telegram_message(self, message):
        """Sends message via Telegram"""

        url = "https://api.telegram.org/bot" + self.token_id + "/sendMessage"
        data = {
            "chat_id": self.chat_id,
            "text": message
        }

        try:
            response = requests.request("POST", url, params=data)
            telegram_data = json.loads(response.text)
            return telegram_data["ok"]
        except Exception as e:
            print("An error occurred in sending the alert message via Telegram")
            print(e)
        return False


@dataclass
class CryptoInfo:
    api_key: str
    exclude = ["github.com", "proofpatform.io", "zeppelin", "instagram.com", "dapp.tools", "solidity", "eips.ethereum",
               "eth.wiki", "nomic-labs-blog", "etherscan", "Etherscan", 'tokenmint.io', 'hardhat']

    @staticmethod
    def clean_string(s: str) -> str:
        """Clean string by removing unwanted characters."""
        if '\\' in s:
            s = s.split('\\')[0]
        if s.startswith("-https://"):
            s = s.replace("-https://", "https://", 1) # replace only the first occurrence
        return s

    def scrap_contract_links(self, contract_address) -> Dict[str, str]:
        try:
            url = f"https://api.etherscan.io/api?module=contract&action=getsourcecode&apikey={self.api_key}&address={contract_address.lower()}"
            response = requests.get(url)
            response.raise_for_status()

            links = {}
            for info in response.json()["result"]:
                for word in info['SourceCode'].split():
                    if word.startswith("-http"):
                        word = word[1:]  # remove leading '-'
                    if word.startswith("http"):
                        if "twitter.com" in word:
                            links["twitter"] = word
                        elif "telegram.me" in word or "t.me" in word:
                            links["telegram"] = word
                        else:
                            if not any(substring in word for substring in self.exclude):
                                links["website"] = word
                    else:
                        if "twitter.com" in word:
                            links["twitter"] = "https://" + word
                        elif "telegram.me" in word or "t.me" in word:
                            links["telegram"] = "https://" + word
                        else:
                            if ".io" in word:
                                if not any(substring in word for substring in self.exclude):
                                    links["website"] = "https://" + word
            return links
        except Exception as e:
            return None

    def scrap_dexscreener(self, contract_address) -> Dict[str, str]:
        try:
            url = f"https://api.dexscreener.com/latest/dex/tokens/{contract_address.lower()}"
            response = requests.get(url)
            response.raise_for_status()

            info = response.json()['pairs'][0]
            infos = {"name": info['baseToken']['name'],
                     "symbol": info['baseToken']['symbol'],
                     "mc": self.format_number(info['fdv']),
                     "usd_price": info['priceUsd'],
                     "volume": self.format_number(info['volume']['h24']),
                     "priceChange": info['priceChange']['h24'],
                     "creation": info['pairCreatedAt']}
            return infos
        except Exception as e:
            return None

    @staticmethod
    def format_number(num: float) -> str:
        if num >= 1_000_000:
            return f"{round(num / 1_000_000, 1)}M"
        elif num >= 1_000:
            return f"{round(num / 1_000, 1)}K"
        else:
            return str(num)

    def create_and_print_message(self, contract_address):
        links = self.scrap_contract_links(contract_address)
        infos = self.scrap_dexscreener(contract_address)

        message = f"{infos['name']} - ${infos['symbol']} - {infos['mc']} MC\n" \
                  f"\n📩 {links.get('telegram', 'Not available')}\n" \
                  f"🐦 {links.get('twitter', 'Not available')}\n" \
                  f"🌐 {links.get('website', 'Not available')}\n" \
                  f"📈 https://dexscreener.com/ethereum/{contract_address}\n\n" \
                  f"Additional Information:\n" \
                  f"Price USD: ${infos['usd_price']}\n" \
                  f"Volume 24H: ${infos['volume']}\n" \
                  f"Price Change 24H: {infos['priceChange']}%\n" \
                  f"Pair Created: {datetime.fromtimestamp(int(infos['creation'] / 1000)) - timedelta(hours=1)} UTC"
        return message


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

    def was_address_active_before(self, transactions: List[dict], timestamp: datetime, txhash: str) -> bool:
        for tx in transactions:
            if tx['hash'] == txhash:
                continue
            tx_time = datetime.utcfromtimestamp(int(tx['timeStamp']))
            if tx_time < timestamp:
                return True
        return False

    def did_address_create_contract(self, transactions: List[dict]) -> bool:
        return any(isinstance(tx, dict) and tx['to'] == '' for tx in transactions)

    def did_address_swap(self, transactions: List[dict]) -> bool:
        db_manager = DBManager(db_name='kendhalaltay', user='kendhalaltay')
        processed_transactions = set(db_manager.get_all_transactions())  # Convert to set for quicker lookup

        functions_to_check = ['swapExactETHForTokens', 'unoswap', 'execute', 'swap']
        uniswap_router_address = "0x3fC91A3afd70395Cd496C647d5a6CC9D4B2b7FAD".lower()

        for tx in transactions:
            if isinstance(tx, dict) and (('functionName' in tx and any(func in tx['functionName'] for func in functions_to_check)) or tx.get('to', '').lower() == uniswap_router_address):
                if tx['hash'] not in processed_transactions:
                    telegram_alert = TelegramAlert()
                    telegram_alert.send_telegram_message(
                        f"A swap was performed, here's the link: https://etherscan.io/tx/{tx['hash']}")
                    try:
                        crypto_info = CryptoInfo(self.api_key)
                        for token in self.get_token_address(tx['hash']):
                            try:
                                telegram_alert.send_telegram_message(f"{crypto_info.create_and_print_message(token)}")
                            except TypeError as e:
                                continue
                    except IndexError as e:
                        continue
                    db_manager.insert_transaction(tx['hash'])
                    db_manager.close_connection()
                    return True

        db_manager.close_connection()  # Close the connection when done
        return False

    def get_balance(self, address: str) -> float:
        url = f"https://api.etherscan.io/api?module=account&action=balance&address={address}&tag=latest&apikey={self.api_key}"
        response = requests.get(url)
        if response.status_code != 200:
            response.raise_for_status()
        data = response.json()
        return int(data.get('result', 0)) / self.WEI_TO_ETHER

    def get_token_address(self, txhash: str):
        known_coins = [
            '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2',
        ]
        addresses = set()
        url = f"https://api.etherscan.io/api?module=proxy&action=eth_getTransactionReceipt&txhash={txhash}&apikey={self.api_key}"
        response = requests.get(url)
        if response.status_code != 200:
            response.raise_for_status()
        data = response.json()
        for i in data.get('result')['logs']:
            if i.get('address').lower() not in [coin.lower() for coin in known_coins]:
                addresses.add(i.get('address'))
        return addresses


class FileManager:
    @staticmethod
    def create_dir(path: str) -> None:
        Path(path).mkdir(parents=True, exist_ok=True)

    @staticmethod
    def write_to_file(file_path: str, data: dict) -> None:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)


class DBManager:
    def __init__(self, db_name, user, password=None, host="localhost"):
        self.conn = psycopg2.connect(dbname=db_name, user=user, password=password, host=host)
        self.c = self.conn.cursor()
        self.c.execute('''CREATE TABLE IF NOT EXISTS addresses
                     (address text PRIMARY KEY)''')
        self.c.execute('''CREATE TABLE IF NOT EXISTS transactions
                             (txhash text PRIMARY KEY)''')
        self.conn.commit()

    def insert_address(self, address):
        try:
            self.c.execute(sql.SQL("INSERT INTO addresses (address) VALUES (%s)"), (address,))
        except psycopg2.IntegrityError:
            self.conn.rollback()  # address already exists in the database
        else:
            self.conn.commit()

    def insert_transaction(self, txhash):
        try:
            self.c.execute(sql.SQL("INSERT INTO transactions (txhash) VALUES (%s)"), (txhash,))
            self.conn.commit()  # Commit changes
        except psycopg2.IntegrityError:
            self.conn.rollback()  # transaction already exists in the database

    def get_all_addresses(self):
        self.c.execute('SELECT address FROM addresses')
        return [record[0] for record in self.c.fetchall()]

    def get_all_transactions(self):
        self.c.execute('SELECT txhash FROM transactions')
        return [record[0] for record in self.c.fetchall()]

    def remove_address(self, address: str):
        self.c.execute("DELETE FROM addresses WHERE address=%s", (address,))
        self.conn.commit()

    def close_connection(self):
        self.conn.close()


def check_swaps():
    db = DBManager(db_name='kendhalaltay', user='kendhalaltay')
    addresses = db.get_all_addresses()

    etherscan = EtherscanAPI(Config("credentials.yml").get_value('Etherscan.API_KEY'))

    addresses_with_swap = []
    for address in tqdm(addresses, desc="Checking swaps"):
        transactions = etherscan.get_transactions(address)
        if etherscan.did_address_swap(transactions):
            addresses_with_swap.append(address)
        elif etherscan.did_address_create_contract(transactions):
            db.remove_address(address)
        elif etherscan.get_balance(address) < 0.1:
            db.remove_address(address)

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
    print('------------------------------------------------------------------')
    print('\nTIME:', datetime.now(), '\n')
    time_threshold = datetime.now() - timedelta(minutes=30)

    # Filter transactions
    for tx in transactions:
        tx_time = datetime.utcfromtimestamp(int(tx['timeStamp']))
        if tx['from'].lower() == ADDRESS.lower() and tx_time >= (time_threshold - timedelta(hours=2)):
            value_ether = int(tx['value']) / EtherscanAPI.WEI_TO_ETHER
            if 0.5 <= value_ether <= 10:
                filtered_transactions.append(tx)

    # Filter addresses with no activity before the transaction from the target wallet
    addresses_with_no_prior_activity = []
    for tx in tqdm(filtered_transactions, desc="Checking prior activity"):
        address = tx['to']
        tx_time = datetime.utcfromtimestamp(int(tx['timeStamp']))
        tx_hash = tx['hash']
        transactions = etherscan.get_transactions(address)
        if not etherscan.was_address_active_before(transactions, tx_time, tx_hash):
            addresses_with_no_prior_activity.append(address)

    # Filter addresses that created contracts
    addresses_without_contracts = []
    for address in tqdm(addresses_with_no_prior_activity, desc="Checking contract creation"):
        transactions = etherscan.get_transactions(address)
        if not etherscan.did_address_create_contract(transactions):
            addresses_without_contracts.append(address)

    print('\nNo Prior Activity:\n', addresses_with_no_prior_activity, '\n')
    print('\nAddresses without contract creation:\n', addresses_without_contracts, '\n')

    # Write the filtered addresses to a SQLite database
    db = DBManager(db_name='kendhalaltay', user='kendhalaltay')
    for address in addresses_without_contracts:
        db.insert_address(address)
    db.close_connection()

    print("Addresses written to database\n")


def job():
    main()


if __name__ == "__main__":
    schedule.every(1).minutes.do(job)
    schedule.every(1).minutes.do(check_swaps)

    while True:
        schedule.run_pending()
        time.sleep(1)
