from web3 import Web3

from config import BSC_PRIVATE_KEY, BSC_RPC
from token_abi import ERC20_ABI

USDT_CONTRACT = "0x55d398326f99059fF775485246999027B3197955"
USDT_DECIMALS = 18


def send_bsc_usdt(dest_wallet: str, usdt_amount: float) -> str:
    if not BSC_PRIVATE_KEY:
        raise RuntimeError("BSC_PRIVATE_KEY is not configured")

    w3 = Web3(Web3.HTTPProvider(BSC_RPC))
    if not w3.is_connected():
        raise RuntimeError("BSC RPC সংযোগ ব্যর্থ!")

    account = w3.eth.account.from_key(BSC_PRIVATE_KEY)
    admin = account.address
    contract = w3.eth.contract(address=Web3.to_checksum_address(USDT_CONTRACT), abi=ERC20_ABI)
    dest = Web3.to_checksum_address(dest_wallet)
    amount_raw = int(usdt_amount * 10**USDT_DECIMALS)

    balance = contract.functions.balanceOf(admin).call()
    if balance < amount_raw:
        raise RuntimeError(f"অপর্যাপ্ত USDT! আছে: {balance / 10**USDT_DECIMALS}, দরকার: {usdt_amount}")

    txn = contract.functions.transfer(dest, amount_raw).build_transaction(
        {
            "from": admin,
            "nonce": w3.eth.get_transaction_count(admin),
            "gasPrice": w3.eth.gas_price,
            "gas": 100000,
            "chainId": 56,
        }
    )
    signed = w3.eth.account.sign_transaction(txn, BSC_PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
    if receipt.status != 1:
        raise RuntimeError("Transaction failed on chain!")
    return tx_hash.hex()
