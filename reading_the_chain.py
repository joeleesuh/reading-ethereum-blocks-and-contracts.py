import random
import json
from web3 import Web3
from web3.middleware import geth_poa_middleware
from web3.providers.rpc import HTTPProvider

def connect_to_eth():
	infura_token = "3e2fa60f9efc4d79a7353ea9811da8aa"
	url = f"https://mainnet.infura.io/v3/{infura_token}"
	w3 = Web3(HTTPProvider(url))
	assert w3.is_connected(), f"Failed to connect to provider at {url}"
	return w3

def connect_with_middleware(contract_json):
	with open(contract_json, "r") as f:
		d = json.load(f)
		address = d['bsc']['address']
		abi = d['bsc']['abi']
	bnb_testnet_url = "https://data-seed-prebsc-1-s1.binance.org:8545"
	w3 = Web3(HTTPProvider(bnb_testnet_url))
	w3.middleware_onion.inject(geth_poa_middleware, layer=0)
	contract = w3.eth.contract(address=Web3.to_checksum_address(address), abi=abi)
	return w3, contract

def is_ordered_block(w3, block_num):
    block = w3.eth.get_block(block_num, full_transactions=True)
    transactions = block['transactions']
    base_fee_per_gas = block.get('baseFeePerGas', 0)
    fees = []
    
    for tx in transactions:
        if tx.type == "0x0":
            priority_fee = tx.gasPrice
        elif tx.type == "0x2":
            priority_fee = min(tx.maxPriorityFeePerGas, tx.maxFeePerGas - base_fee_per_gas)
        else:
            continue
        fees.append(priority_fee)
    
    is_ordered = fees == sorted(fees, reverse=True)
    
    if not is_ordered:
        print(f"Block {block_num} failed ordering check. Fees: {fees}")
        
    return is_ordered

def get_contract_values(contract, admin_address, owner_address):
	onchain_root = contract.functions.merkleRoot().call()
	default_admin_role = int.to_bytes(0, 32, byteorder="big")
	has_role = contract.functions.hasRole(default_admin_role, admin_address).call()
	prime = contract.functions.getPrimeByOwner(owner_address).call()
	return onchain_root, has_role, prime

if __name__ == "__main__":
	admin_address = "0xAC55e7d73A792fE1A9e051BDF4A010c33962809A"
	owner_address = "0x793A37a85964D96ACD6368777c7C7050F05b11dE"
	contract_file = "contract_info.json"

	eth_w3 = connect_to_eth()
	cont_w3, contract = connect_with_middleware(contract_file)

	latest_block = eth_w3.eth.get_block_number()
	london_hard_fork_block_num = 12965000
	assert latest_block > london_hard_fork_block_num, f"Error: the chain never got past the London Hard Fork"
	n = 5
	for _ in range(n):
		block_num = random.randint(1, london_hard_fork_block_num - 1)
		ordered = is_ordered_block(eth_w3, block_num)
		if ordered:
			print(f"Block {block_num} is ordered")
		else:
			print(f"Block {block_num} is not ordered")
