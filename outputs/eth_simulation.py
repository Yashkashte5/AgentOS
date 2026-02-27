import requests

def get_eth_price():
    response = requests.get('https://min-api.cryptocompare.com/data/price?fsym=ETH&tsyms=USD')
    data = response.json()
    return data['USD']

def simulate_buy(eth_price, amount):
    total_cost = eth_price * amount
    return total_cost

def calculate_profit_loss(initial_price, final_price, amount):
    initial_value = initial_price * amount
    final_value = final_price * amount
    profit_loss = final_value - initial_value
    return profit_loss

def main():
    eth_price = get_eth_price()
    amount = 10
    total_cost = simulate_buy(eth_price, amount)
    print(f'Current ETH price: ${eth_price}')
    print(f'Total cost of buying {amount} ETH: ${total_cost}')

    price_increases = [0.05, 0.10, 0.20]
    for increase in price_increases:
        new_price = eth_price * (1 + increase)
        profit_loss = calculate_profit_loss(eth_price, new_price, amount)
        print(f'If ETH price increases by {increase*100}%, profit/loss: ${profit_loss}')

if __name__ == '__main__':
    main()

# Execution output:
# Current ETH price: $1942.51
# Total cost of buying 10 ETH: $19425.1
# If ETH price increases by 5.0%, profit/loss: $971.255000000001
# If ETH price increases by 10.0%, profit/loss: $1942.510000000002
# If ETH price increases by 20.0%, profit/loss: $3885.019999999997