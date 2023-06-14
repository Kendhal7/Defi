import requests
import pandas as pd
from collections import defaultdict
import yaml

# Upload the config file
file = open(f"credentials.yml", 'r')
config = yaml.load(file, Loader=yaml.FullLoader)

# Get Twitter Credentials
ETHERSCAN_API_KEY = config['Etherscan']["API_KEY"]


def get_transactions(wallet_address, api_key):
    url = f"https://api.etherscan.io/api?module=account&action=tokentx&address={wallet_address}&startblock=0&endblock=99999999&sort=asc&apikey={api_key}"
    response = requests.get(url)
    data = response.json()
    return data["result"]


def parse_transactions(transactions, wallet_address):
    buy_dict = defaultdict(float)
    sell_dict = defaultdict(float)

    for tx in transactions:
        if tx['from'].lower() == wallet_address.lower():
            # This is a sell transaction
            if tx['tokenSymbol'] != 'ETH':
                print(tx)
                breakpoint()
                sell_dict[tx['tokenSymbol']] += float(tx['value']) / 10**int(tx['tokenDecimal'])
        elif tx['to'].lower() == wallet_address.lower():
            # This is a buy transaction
            if tx['tokenSymbol'] != 'ETH':
                print(tx)
                breakpoint()
                buy_dict[tx['tokenSymbol']] += float(tx['value']) / 10**int(tx['tokenDecimal'])

    return buy_dict, sell_dict


def calculate_win_ratio(buy_dict, sell_dict):
    number_of_coins_bought = len(buy_dict)
    win = 0

    for token in buy_dict.keys():
        if sell_dict[token] > buy_dict[token]:
            win += 1

    # Check if number_of_coins_bought is not zero before calculating win_ratio
    if number_of_coins_bought != 0:
        win_ratio = str(round((win / number_of_coins_bought) * 100, 2)) + '%'
    else:
        win_ratio = 'No Token Bought'

    print(buy_dict)
    print(sell_dict)
    print(f'\nNumber of Tokens Bought: {number_of_coins_bought}')
    print(f'Number of Win: {win}')
    print(f'Win Ratio: {win_ratio}')


if __name__ == '__main__':
    wallet_address = '0xa0ed5bCb30f4dC2574B20948cAbF84D58634b745'
    transactions = get_transactions(wallet_address, ETHERSCAN_API_KEY)
    buy_dict, sell_dict = parse_transactions(transactions, wallet_address)
    calculate_win_ratio(buy_dict, sell_dict)
