from web3 import Web3

web3 = Web3(Web3.HTTPProvider('https://mainnet.infura.io/v3/YOUR_INFURA_PROJECT_ID'))

def check_balance(address):
    balance = web3.eth.get_balance(address)
    return web3.fromWei(balance, 'ether')
