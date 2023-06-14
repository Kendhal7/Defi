import requests
import yaml

# Upload the config file
file = open(f"credentials.yml", 'r')
config = yaml.load(file, Loader=yaml.FullLoader)

# Get Twitter Credentials
ETHERSCAN_API_KEY = config['Etherscan']["API_KEY"]
API_URL = "https://api.etherscan.io/api?module=account&action=txlist&address={}&startblock=0&endblock=99999999&sort=asc&apikey={}"


def get_transactions(address):
    url = API_URL.format(address, ETHERSCAN_API_KEY)
    response = requests.get(url)
    data = response.json()
    return data['result'] if 'result' in data else []


def find_hops(start_address, target_addresses, max_hops=5, max_transactions=100):
    visited = set()
    queue = [(start_address.lower(), [], None, 0)]
    enqueued = set([start_address.lower()])
    paths = []
    while queue:
        address, path, prev_tx_hash, hops = queue.pop(0)
        path = path + [(address, prev_tx_hash)]
        transactions = get_transactions(address)
        for transaction in transactions:
            new_addresses = [transaction['to'], transaction['from']]
            tx_hash = transaction['hash']
            for new_address in new_addresses:
                if new_address and new_address not in visited and new_address not in enqueued:
                    if new_address in target_addresses:
                        paths.append((path + [(new_address, tx_hash)], hops + 1))
                    elif hops < max_hops and len(transactions) <= max_transactions:
                        queue.append((new_address.lower(), path, tx_hash, hops + 1))
                        enqueued.add(new_address)
                    visited.add(new_address)
    return paths


def main():
    start_addresses = [
        '0x50eD4D3e48B27681371b0c9F375Eb12a85e241Dc',  # TEST_1
        '0x58203347923ef9751748D098084611FF4473d1Cd',  # TEST_4
        '0xbdb4BeeF21efC8AE04A6Bf11e685954BEc015125',  # TEST_5
        '0x80C94d637F5F51758D5935284F3B3091ceEf2a8C',  # TEST_6
        '0x7322f9932d68FB99a84fb9F89375c8cB7EBb9bB9',  # TEST_7
        '0x32Fd0f2853dd29b479c4879D7683d81e5C3cC3c1',  # TEST_8
        '0x4730d108aC076973373155932a465ed438C7b1a2',  # TEST_9
        '0x82ea7840441c4B4E16Ce4A9c58364dc7FBe19048',  # TEST_10
        '0x861193dF5007fDE8DC8F2B72dB746DFf226Cea68',  # TEST_11
        '0x743CB013D459c358ed571A21cC105E35c284C385',  # TEST_12
        '0x9822E23558c2837a499541Bf22433B0F820F213A',  # TEST_13
        '0x5440cC69CB31CA46decf34C246FC395378D731b4',  # TEST_14
        '0xC78d8F4493B5A1455152DE575deE50D986871eC9',  # TEST_15
    ]

    start_addresses = [address.lower() for address in start_addresses]

    for start_address in start_addresses:
        target_addresses = [
            '0x45dd43D67C4dC159017F14faCa48D231d3616fac',  # POE
            '0xc9E170d9C62b7765F624459C3fdDf23de9f4CeC3',  # CTM
            '0xd6BDF425640032b949aeB2130a9ACB9a3181B58b',  # WJS
            '0x58203347923ef9751748D098084611FF4473d1Cd',  # TEST_4
        ]
        target_addresses = [address.lower() for address in target_addresses]
        paths = find_hops(start_address, target_addresses)
        if paths:
            for path, hops in paths:
                print(f'\n{path[0][0]} linked to {path[-1][0]} after {hops} hops')
                print('\nThe path is:')
                for addr, tx_hash in path:
                    print(f'Address: {addr} - Transaction Hash: {tx_hash}')
                print()
        else:
            print(f"No link found between {start_address} and the target_addresses within the specified max hop limit.")


if __name__ == "__main__":
    main()
