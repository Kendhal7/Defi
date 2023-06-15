import requests
import yaml
import time
import aiohttp
import asyncio

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

class TokenBucket:
    def __init__(self, tokens, fill_rate):
        """tokens is the total tokens in the bucket. fill_rate is the rate in tokens/second that the bucket will be refilled."""
        self.capacity = float(tokens)
        self._tokens = float(tokens)
        self.fill_rate = float(fill_rate)
        self.timestamp = time.time()

    def take(self, tokens):
        """Consume tokens from the bucket. Returns 0 if there were sufficient tokens, otherwise the expected time until enough tokens become available."""
        if tokens <= self._tokens:
            self._tokens -= tokens
            return 0
        else:
            deficit = tokens - self._tokens
            return deficit / self.fill_rate

    def refill(self):
        """Add new tokens to the bucket."""
        now = time.time()
        if self._tokens < self.capacity:
            delta = self.fill_rate * (now - self.timestamp)
            self._tokens = min(self.capacity, self._tokens + delta)
        self.timestamp = now


token_bucket = TokenBucket(tokens=5, fill_rate=1)

async def get_transactions(session, address, retries=3):
    url = API_URL.format(address, ETHERSCAN_API_KEY)
    for i in range(retries):
        wait_time = token_bucket.take(1)
        if wait_time > 0:
            await asyncio.sleep(wait_time)
        token_bucket.refill()
        async with session.get(url) as response:
            data = await response.json()
            if isinstance(data, dict) and 'status' in data and data['status'] == '0' and 'result' in data and data['result'] == 'Max rate limit reached':
                print("Rate limit exceeded. Retrying...")
                continue
            else:
                response.raise_for_status()  # raises an HTTPError if one occurred
                if isinstance(data, dict) and 'result' in data:
                    return data['result']
                else:
                    return []
        # If an error is not caught and handled above, raise an error after all retries.
        print(f"Failed to fetch transactions for address {address} after {retries} attempts.")
        raise Exception(f"API request failed after {retries} attempts.")
    return None  # add this line to return None when rate limit is exceeded





from collections import deque

async def find_hops(start_address, target_addresses, exclude_addresses=None, max_hops=5, max_transactions=100):
    if exclude_addresses is None:
        exclude_addresses = set()
    else:
        exclude_addresses = set([address.lower() for address in exclude_addresses])

    visited = set([start_address.lower()])
    queue = deque([(start_address.lower(), [], None, 0)])
    paths = []
    async with aiohttp.ClientSession() as session:
        while queue:
            address, path, prev_tx_hash, hops = queue.popleft()
            path = path + [(address, prev_tx_hash)]
            transactions = await get_transactions(session, address)
            print(path)
            if transactions is None:  # handle the None response here
                print("Rate limit exceeded. Skipping address.")
                continue
            for transaction in transactions:
                new_addresses = [transaction['to'].lower(), transaction['from'].lower()]
                tx_hash = transaction['hash']
                for new_address in new_addresses:
                    if new_address and new_address not in visited and new_address not in exclude_addresses:
                        visited.add(new_address)
                        if new_address in target_addresses.keys():
                            paths.append((path + [(new_address, tx_hash)], hops + 1))
                        elif hops < max_hops and len(transactions) <= max_transactions:
                            queue.append((new_address.lower(), path, tx_hash, hops + 1))
    return paths



def main():
    start_addresses = {address.lower(): name for address, name in addresses['START_ADDRESSES'].items()}
    target_addresses = {address.lower(): name for address, name in addresses['TARGET_ADDRESSES'].items()}
    exclude_addresses = [address.lower() for address in addresses['EXCLUDE_ADDRESSES']]

    for start_address, start_name in start_addresses.items():
        loop = asyncio.get_event_loop()
        paths = loop.run_until_complete(find_hops(start_address, target_addresses, exclude_addresses))
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
