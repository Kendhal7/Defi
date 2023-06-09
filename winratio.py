import pandas as pd

# Function to process each cell
def process_currency(currency):
    split_currency = currency.split('\n')
    if split_currency[0] == 'ETH':
        return split_currency[1] if len(split_currency) > 1 else split_currency[0]
    else:
        return split_currency[0]

def load_and_clean_data(filepath):
    df = pd.read_csv(filepath)
    df = df[(df['Transaction Type'] == 'trade') &
            (df['Status'] == 'Confirmed') &
            (df['Chain'] == 'ethereum')]

    # ETH coin address
    ETH_address = '0x7a250d5630b4cf539739df2c5dacb4c659f2488d'

    # Remove any typo from the currency names
    df['Buy Currency'] = df['Buy Currency'].apply(process_currency)
    df['Sell Currency'] = df['Sell Currency'].apply(process_currency)

    # Convert the 'Buy Amount', 'Sell Amount' and 'Fee Amount' columns to float
    for column in ['Buy Amount', 'Sell Amount', 'Fee Amount']:
        df[column] = pd.to_numeric(df[column], errors='coerce')

    return df, ETH_address


def aggregate_amounts(df, ETH_address):
    # Aggregating buy and sell amounts for each token
    buy_df = df[df['Sell Currency Address'] == ETH_address].groupby('Buy Currency')[['Sell Amount', 'Fee Amount']].sum()
    buy_df.columns = ['Total Bought', 'Buy Fee Amount']

    sell_df = df[df['Buy Currency Address'] == ETH_address].groupby('Sell Currency')[
        ['Buy Amount', 'Fee Amount']].sum()
    sell_df.columns = ['Total Sold', 'Sell Fee Amount']

    # Combine both dataframes
    result = pd.concat([buy_df, sell_df], axis=1).reset_index()
    result.columns = ['Token', 'Total Bought', 'Buy Fee Amount', 'Total Sold', 'Sell Fee Amount']

    # Create a single 'Fee Amount' column by summing 'Buy Fee Amount' and 'Sell Fee Amount'
    result['Fee Amount'] = result['Buy Fee Amount'].fillna(0) + result['Sell Fee Amount'].fillna(0)

    # Drop the 'Buy Fee Amount' and 'Sell Fee Amount' columns
    result = result.drop(['Buy Fee Amount', 'Sell Fee Amount'], axis=1)

    return result


def calculate_win_ratio(result):
    number_of_coins_bought = len(result)
    win = sum(result['Total Sold'] > (result['Total Bought'] + result['Fee Amount']))

    win_ratio = str(round((win / number_of_coins_bought) * 100, 2)) + '%'

    print(result)
    print(f'\nNumber of Tokens Bought: {number_of_coins_bought}')
    print(f'Number of Win: {win}')
    print(f'Win Ratio: {win_ratio}')

    result.to_csv('/Users/kendhalaltay/Downloads/results.csv')


if __name__ == "__main__":
    filepath = '/Users/kendhalaltay/Downloads/0x8f615808b2c93534f9ad1173a3d8d31b1ddd5065 transactions 06_09_2023 16_54 from Zerion.csv'
    df, ETH_address = load_and_clean_data(filepath)
    result = aggregate_amounts(df, ETH_address)
    calculate_win_ratio(result)
