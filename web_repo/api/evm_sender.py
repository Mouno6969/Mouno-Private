from web3 import Web3

from config import AVALANCHE_RPC, BASE_RPC, BSC_PRIVATE_KEY, ETHEREUM_RPC
from token_abi import ERC20_ABI

EVM_KEY = BSC_PRIVATE_KEY

NETWORKS = {
    "avalanche": {
        "rpc": AVALANCHE_RPC,
        "chain_id": 43114,
        "usdt": "0x9702230A8Ea53601f5cD2dc00fDBc13d4dF4A8c7",
        "usdc": "0xB97EF9Ef8734C71904D8002F8b6Bc66Dd9c48a6E",
        "decimals": {"usdt": 6, "usdc": 6},
    },
    "ethereum": {
        "rpc": ETHEREUM_RPC,
        "chain_id": 1,
        "usdt": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
        "usdc": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        "decimals": {"usdt": 6, "usdc": 6},
    },
    "base": {
        "rpc": BASE_RPC,
        "chain_id": 8453,
        "usdt": "",
        "usdc": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
        "decimals": {"usdt": 6, "usdc": 6},
    },
}


def send_evm_token(network: str, token: str, dest_wallet: str, amount: float) -> str:
    if not EVM_KEY:
        raise RuntimeError("BSC_PRIVATE_KEY is not configured")

    config = NETWORKS[network]
    w3 = Web3(Web3.HTTPProvider(config["rpc"]))
    if not w3.is_connected():
        raise RuntimeError(f"{network} RPC সংযোগ ব্যর্থ!")

    account = w3.eth.account.from_key(EVM_KEY)
    admin = account.address
    token_lower = token.lower()
    contract_addr = config[token_lower]
    if not contract_addr:
        raise RuntimeError(f"{network} এ {token} সাপোর্ট নেই!")

    decimals = config["decimals"][token_lower]
    contract = w3.eth.contract(address=Web3.to_checksum_address(contract_addr), abi=ERC20_ABI)
    dest = Web3.to_checksum_address(dest_wallet)
    amount_raw = int(amount * 10**decimals)

    balance = contract.functions.balanceOf(admin).call()
    if balance < amount_raw:
        raise RuntimeError(f"অপর্যাপ্ত {token}! আছে: {balance / 10**decimals}, দরকার: {amount}")

    txn = contract.functions.transfer(dest, amount_raw).build_transaction(
        {
            "from": admin,
            "nonce": w3.eth.get_transaction_count(admin),
            "gasPrice": w3.eth.gas_price,
            "gas": 100000,
            "chainId": config["chain_id"],
        }
    )
    signed = w3.eth.account.sign_transaction(txn, EVM_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
    if receipt.status != 1:
        raise RuntimeError("Transaction failed on chain!")
    return tx_hash.hex()
