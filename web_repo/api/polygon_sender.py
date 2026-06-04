from web3 import Web3

from config import POLYGON_PRIVATE_KEY, POLYGON_RPC
from token_abi import ERC20_ABI

USDC_CONTRACT = "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359"
USDC_DECIMALS = 6


def send_polygon_usdc(dest_wallet: str, usdc_amount: float) -> str:
    if not POLYGON_PRIVATE_KEY:
        raise RuntimeError("POLYGON_PRIVATE_KEY is not configured")

    w3 = Web3(Web3.HTTPProvider(POLYGON_RPC))
    if not w3.is_connected():
        raise RuntimeError("Polygon RPC সংযোগ ব্যর্থ!")

    account = w3.eth.account.from_key(POLYGON_PRIVATE_KEY)
    admin = account.address
    contract = w3.eth.contract(address=Web3.to_checksum_address(USDC_CONTRACT), abi=ERC20_ABI)
    dest = Web3.to_checksum_address(dest_wallet)
    amount_raw = int(usdc_amount * 10**USDC_DECIMALS)

    balance = contract.functions.balanceOf(admin).call()
    if balance < amount_raw:
        raise RuntimeError(f"অপর্যাপ্ত USDC! আছে: {balance / 10**USDC_DECIMALS}, দরকার: {usdc_amount}")

    txn = contract.functions.transfer(dest, amount_raw).build_transaction(
        {
            "from": admin,
            "nonce": w3.eth.get_transaction_count(admin),
            "gasPrice": w3.eth.gas_price,
            "gas": 100000,
            "chainId": 137,
        }
    )
    signed = w3.eth.account.sign_transaction(txn, POLYGON_PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
    if receipt.status != 1:
        raise RuntimeError("Transaction failed on chain!")
    return tx_hash.hex()
