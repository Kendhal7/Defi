import requests
import yaml
import time

# Upload the config file
file = open(f"credentials.yml", 'r')
config = yaml.load(file, Loader=yaml.FullLoader)

# Get Twitter Credentials
ETHERSCAN_API_KEY = config['Etherscan']["API_KEY"]
API_URL = "https://api.etherscan.io/api?module=account&action=txlist&address={}&startblock=0&endblock=99999999&sort=asc&apikey={}"

# Upload the addresses file
with open("addresses.yaml", 'r') as file:
    addresses = yaml.load(file, Loader=yaml.FullLoader)

# Get Addresses
TARGET_ADDRESSES = {address.lower(): name for address, name in addresses['TARGET_ADDRESSES'].items()}
START_ADDRESSES = {address.lower(): name for address, name in addresses['START_ADDRESSES'].items()}
EXCLUDE_ADDRESSES = [address.lower() for address in addresses['EXCLUDE_ADDRESSES']]


def get_transactions(address, retries=3, delay=5):
    url = API_URL.format(address, ETHERSCAN_API_KEY)
    for i in range(retries):
        try:
            response = requests.get(url)
            response.raise_for_status()  # raises an HTTPError if one occurred
            data = response.json()
            return data['result'] if 'result' in data else []
        except requests.HTTPError as e:
            if i < retries - 1:  # i is zero indexed
                time.sleep(delay)  # wait before trying again
                continue
            else:
                print(f"Failed to fetch transactions for address {address} after {retries} attempts.")
                raise e


def find_hops(start_address, target_addresses, exclude_addresses=None, max_hops=2, max_transactions=100):
    if exclude_addresses is None:
        exclude_addresses = set()
    else:
        exclude_addresses = set([address.lower() for address in exclude_addresses])
    visited = set()
    queue = [(start_address.lower(), [], None, 0)]
    enqueued = set([start_address.lower()])
    paths = []
    while queue:
        address, path, prev_tx_hash, hops = queue.pop(0)
        path = path + [(address, prev_tx_hash)]
        transactions = get_transactions(address)
        print(path)
        for transaction in transactions:
            new_addresses = [transaction['to'].lower(), transaction['from'].lower()]
            tx_hash = transaction['hash']
            for new_address in new_addresses:
                if new_address and new_address not in visited and new_address not in enqueued and new_address not in exclude_addresses:
                    if new_address in target_addresses.keys():
                        paths.append((path + [(new_address, tx_hash)], hops + 1))
                    elif hops < max_hops and len(transactions) <= max_transactions:
                        queue.append((new_address.lower(), path, tx_hash, hops + 1))
                        enqueued.add(new_address)
                    visited.add(new_address)
    return paths


def main():
    start_addresses = {address.lower(): name for address, name in addresses['START_ADDRESSES'].items()}
    target_addresses = {address.lower(): name for address, name in addresses['TARGET_ADDRESSES'].items()}
    exclude_addresses = [address.lower() for address in addresses['EXCLUDE_ADDRESSES']]

    for start_address, start_name in start_addresses.items():
        paths = find_hops(start_address, target_addresses, exclude_addresses)
        if paths:
            for path, hops in paths:
                print(
                    f'\n{start_addresses[path[0][0]]} ({path[0][0]}) linked to {target_addresses[path[-1][0]]} ({path[-1][0]}) after {hops} hops')
                print('\nThe path is:')
                for addr, tx_hash in path:
                    if addr in start_addresses:
                        print(f'Address: {start_addresses[addr]} ({addr}) - Transaction Hash: {tx_hash}')
                    elif addr in target_addresses:
                        print(f'Address: {target_addresses[addr]} ({addr}) - Transaction Hash: {tx_hash}')
                    else:
                        print(f'Address: {addr} - Transaction Hash: {tx_hash}')
                print()
        else:
            print(
                f"No link found between {start_addresses[start_address]} ({start_address}) and the target_addresses within the specified max hop limit.")


if __name__ == "__main__":
    main()
