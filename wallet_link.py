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
            new_addresses = [transaction['to'].lower(), transaction['from'].lower()]
            tx_hash = transaction['hash']
            for new_address in new_addresses:
                if new_address and new_address not in visited and new_address not in enqueued:
                    if new_address in target_addresses.keys():
                        paths.append((path + [(new_address, tx_hash)], hops + 1))
                    elif hops < max_hops and len(transactions) <= max_transactions:
                        queue.append((new_address.lower(), path, tx_hash, hops + 1))
                        enqueued.add(new_address)
                    visited.add(new_address)
    return paths


def main():
    start_addresses = {
        '0x50eD4D3e48B27681371b0c9F375Eb12a85e241Dc': 'TEST_1'
    }

    start_addresses = {address.lower(): name for address, name in start_addresses.items()}

    for start_address, start_name in start_addresses.items():
        target_addresses = {
            '0xc9E170d9C62b7765F624459C3fdDf23de9f4CeC3': 'CTM',
            '0xd6BDF425640032b949aeB2130a9ACB9a3181B58b': 'WJS',
            '0x50eD4D3e48B27681371b0c9F375Eb12a85e241Dc': "TEST_1",
            '0x58203347923ef9751748D098084611FF4473d1Cd': 'TEST_4',
            '0xbdb4BeeF21efC8AE04A6Bf11e685954BEc015125': 'TEST_5',
            '0x80C94d637F5F51758D5935284F3B3091ceEf2a8C': 'TEST_6',
            '0x7322f9932d68FB99a84fb9F89375c8cB7EBb9bB9': 'TEST_7',
            '0x32Fd0f2853dd29b479c4879D7683d81e5C3cC3c1': 'TEST_8',
            '0x4730d108aC076973373155932a465ed438C7b1a2': 'TEST_9',
            '0x82ea7840441c4B4E16Ce4A9c58364dc7FBe19048': 'TEST_10',
            '0x861193dF5007fDE8DC8F2B72dB746DFf226Cea68': 'TEST_11',
            '0x743CB013D459c358ed571A21cC105E35c284C385': 'TEST_12',
            '0x9822E23558c2837a499541Bf22433B0F820F213A': 'TEST_13',
            '0x5440cC69CB31CA46decf34C246FC395378D731b4': 'TEST_14',
            '0xC78d8F4493B5A1455152DE575deE50D986871eC9': 'TEST_15',
            '0xc863E595C3b56F142CF71682c74B25F719EE85E2': 'POE_1',
            '0xF9c336825Ebb7C8fC2c96856912364d8a35E8145': 'POE_10',
            '0x234a3bA2dd72d82853974aB185439761Ec391db7': 'POE_11',
            '0xeDAf179d5436dE9eF5e0052F3E13De963976c5B2': 'POE_12',
            '0x3641677dB54a774B8C2be96268aBf7a052E15985': 'POE_13',
            '0xa9A6747E4B17122359684C8D6c491A0098d832F8': 'POE_14',
            '0x11238CD54755895718d03880b6d28D04aB628263': 'POE_16',
            '0xac617d90C4ce370fC7bCb216d66eA6f809830f82': 'POE_17',
            '0x3EB109Be82C6C20f5dbbF91dbc19Dd22C4550AaF': 'POE_18',
            '0x514854B5E7BF04Fd9996483bB028cb054bE19637': 'POE_2',
            '0x69889BEA959641b8ef932C3C969810bEe21E5AfA': 'POE_3',
            '0xA7CE0C0BDeC1ce84575daBECB38F362f171B6235': 'POE_4',
            '0xa484F156526f2377Be2f93327640F45B6BDcB8f1': 'POE_5',
            '0x50171E875BC1Af9Af749fE88057220675d107013': 'POE_6',
        }
        target_addresses = {address.lower(): name for address, name in target_addresses.items()}
        paths = find_hops(start_address, target_addresses)
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
