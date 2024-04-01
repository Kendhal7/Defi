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


def find_hops(start_address, target_addresses, max_hops=2, max_transactions=100):
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
        '0x18d044d8c82360c5834e220e8c1ad624fb7b9e03': 'PAI',
        '0xd7d82568bd2cdaa4d8a1049c535ab8e6827728c1': 'PAI',
        '0xc18b0fbd997dc057acd5d19c0bd62e93bed14c49': 'PAI',
        '0xbab7fc41e5be0bd9ab4c7de22062892baa7efb41': 'PAI',
        '0x8f92604ad3986c9525714d4b5537bef96be3374b': 'PAI',
        '0x36e0e846de855be68668b3bdbc7431334c59e482': 'PAI',
        '0x3a25e5a551475320c119319a56ad756ae63241d4': 'PAI',
        '0xfbb4e3cf04ed6588e64563aa0dbf2e958118c0ed': 'PAI',
        '0x7aab0681c4c53fc22638e4597d4a5ed3038fafdd': 'PAI',
        '0x40b1762268218b8cd0e8ee3615d6f8ed44f797c8': 'PAI',
        '0x2d2f29d6c07fef876b481ad0556e7c058220e041': 'PAI',
        '0xcd0e05ac572e56bf278729c41793ad88424db4ef': 'PAI',
        '0x9f1652df4c46616702a0005795bb4bb32a65f6ea': 'PAI',
        '0xdf839f2d5bbde84d6534e828d2f9ad8923a2d0c5': 'PAI',
        '0xa32f583c7f5bc0d9c06633c2f3cfc338e78d12bd': 'PAI',
        '0xd4c0b06ee3df6c2b93b8cc2e118c5b093905aa6c': 'PAI',
        '0x4734798424bffcf252d46b2e4af91dc06bdbf79c': 'PAI',
        '0xc9163a208fae2f99125587b0b232f2dd3de94e5a': 'PAI',
        '0x1ce754ab1a8cf61892d803aea9ee1a2b348195e7': 'PAI',
        '0x252c76dba68aa739974d860ca4d7dc844abe4707': 'PAI',
        '0x8c5c7fc9140c1bcb12b18becbbf29ff3e537f9c1': 'PAI',
        '0xf453e3b803ee9bc07172b80ddf384cd00e8d489f': 'PAI',
        '0x60b8d1badbf1a3fdf34c552de8e1d7189c2bc807': 'PAI',
        '0xe3e22035eb0b40a8fe0422e9eaf4768f9b44eb28': 'PAI',
        '0x6931dc457303d13d0a05cd31ee751f0f518dad88': 'PAI',
        '0x5ba30bde3c747579acbeec21094c4397ade467d2': 'PAI',
        '0x78263c287f840f6ed12c7d779591a90b5619a009': 'PAI',
        '0x9541631e8079e294f09031757e3229046bda90f0': 'PAI',
        '0x00be25bd6d560f48379a309d010c997745ead382': 'PAI',
        '0x1eba5bdc74b9421823c11fece470a2177a6b5ead': 'PAI',
        '0xd7286234d05a3746f2fcd083d9e218ce2268db77': 'PAI',
        '0x358e21d9601b31d52390943fccb72c197beb3ea3': 'PAI',
        '0x8f3bb68716856373a2615155417fe92f2f556989': 'PAI',
        '0xf959df6a6427a4920dd6c0ac9484e3ee0b6f08d0': 'PAI',
        '0x43071f98ee53439e14816af7c2f2cc59733d130d': 'PAI',
        '0xeb3ba847938ebe91c66f79a20062ba0f24f31920': 'PAI',
        '0x9d94e8b052a80f2f013c43e4e8d4a55dee4806d9': 'PAI',
        '0xca9baa26f5a7386494371b217cb8629e30c9bcb8': 'PAI',
        '0xeef69cf172a9f546dc808e5eef0c66e0fe3b7582': 'PAI',
        '0xa45614f1b3078063fe84794319c3e6860a048707': 'PAI',
        '0xf87c00900176804708ea2909af86c561e6bcb021': 'PAI',
        '0xdec8d8fa51fa161700175a86ca1f068e669fefb7': 'PAI',
        '0xd493fdb7ad5970b796b7d5459b0f6db617268a5e': 'PAI',
        '0x289a4dc7401927fcc12aac836403730835ad0065': 'PAI',
        '0xf037c76c285d7d1771f8e014ab0a7f647e845b33': 'PAI',
        '0x8862a6c968625f24d5e35a82eee6ab16305f3016': 'PAI',
        '0xad6600b8177ce88f1b8fd2c1d6eea93c9f27aa85': 'PAI',
        '0xfdef6c90eaae50f0cea69bb1108411d2e7d6a13d': 'PAI',
        '0xf9cdd61e08cee88deb31a5127cee26da30b97c60': 'PAI',
        '0xe780d5f1d8e0153edd5684ad0e0be8a987a2cf0f': 'PAI',
    }

    start_addresses = {address.lower(): name for address, name in start_addresses.items()}

    for start_address, start_name in start_addresses.items():
        target_addresses = {
            # '0xc9E170d9C62b7765F624459C3fdDf23de9f4CeC3': 'TEST_1',
            # '0xd6BDF425640032b949aeB2130a9ACB9a3181B58b': 'TEST_1',
            # '0x50eD4D3e48B27681371b0c9F375Eb12a85e241Dc': "TEST_1",
            # '0x58203347923ef9751748D098084611FF4473d1Cd': 'TEST_4',
            # '0xbdb4BeeF21efC8AE04A6Bf11e685954BEc015125': 'TEST_5',
            # '0x80C94d637F5F51758D5935284F3B3091ceEf2a8C': 'TEST_6',
            # '0x7322f9932d68FB99a84fb9F89375c8cB7EBb9bB9': 'TEST_7',
            # '0x32Fd0f2853dd29b479c4879D7683d81e5C3cC3c1': 'TEST_8',
            # '0x4730d108aC076973373155932a465ed438C7b1a2': 'TEST_9',
            # '0x82ea7840441c4B4E16Ce4A9c58364dc7FBe19048': 'TEST_10',
            # '0x861193dF5007fDE8DC8F2B72dB746DFf226Cea68': 'TEST_11',
            # '0x743CB013D459c358ed571A21cC105E35c284C385': 'TEST_12',
            # '0x9822E23558c2837a499541Bf22433B0F820F213A': 'TEST_13',
            # '0x5440cC69CB31CA46decf34C246FC395378D731b4': 'TEST_14',
            # '0xC78d8F4493B5A1455152DE575deE50D986871eC9': 'TEST_15',
            # '0xc863E595C3b56F142CF71682c74B25F719EE85E2': 'TEST_1',
            # '0xF9c336825Ebb7C8fC2c96856912364d8a35E8145': 'TEST_1',
            # '0x234a3bA2dd72d82853974aB185439761Ec391db7': 'TEST_1',
            # '0xeDAf179d5436dE9eF5e0052F3E13De963976c5B2': 'TEST_1',
            # '0x3641677dB54a774B8C2be96268aBf7a052E15985': 'TEST_1',
            # '0xa9A6747E4B17122359684C8D6c491A0098d832F8': 'TEST_1',
            # '0x11238CD54755895718d03880b6d28D04aB628263': 'TEST_1',
            # '0xac617d90C4ce370fC7bCb216d66eA6f809830f82': 'TEST_1',
            # '0x3EB109Be82C6C20f5dbbF91dbc19Dd22C4550AaF': 'TEST_1',
            # '0x514854B5E7BF04Fd9996483bB028cb054bE19637': 'TEST_1',
            # '0x69889BEA959641b8ef932C3C969810bEe21E5AfA': 'TEST_1',
            # '0xA7CE0C0BDeC1ce84575daBECB38F362f171B6235': 'TEST_1',
            # '0xa484F156526f2377Be2f93327640F45B6BDcB8f1': 'TEST_1',
            # '0x50171E875BC1Af9Af749fE88057220675d107013': 'TEST_1',

            '0x4ad434b8CDC3AA5AC97932D6BD18b5d313aB0f6f': 'EVERMOON',
            '0x590f00eDc668D5af987c6076c7302C42B6FE9DD3': 'SCAM',
            '0x370DE5fEeb723a92d8ef7d269620Ea3736268520': 'AUDITUS',
            '0xE08eF9206a8a7C9337cC6611b4f5226Fdafc4772': 'MESSI',

            '0x5D39957Fc88566F14AE7E8aB8971d7c603f0ce5e': 'EYE',
            '0x3db045814D0a29d831fe38055CB97a956eF7cAfb': 'REMIT',
            '0x85225Ed797fd4128Ac45A992C46eA4681a7A15dA': 'HYPE',
            '0x3486b751a36F731A1bEbFf779374baD635864919': 'INEDIBLE',
            '0xF68415bE72377611e95d59bc710CcbBbf94C4Fa2': 'AAI',
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
