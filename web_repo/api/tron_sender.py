from config import TRON_PRIVATE_KEY
from tron_utils import tron_client, tron_private_key

USDT_CONTRACT = "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"
USDT_DECIMALS = 6


def send_trc20_usdt(dest_wallet: str, usdt_amount: float) -> str:
    if not TRON_PRIVATE_KEY:
        raise RuntimeError("TRON_PRIVATE_KEY is not configured")

    client = tron_client()
    key = tron_private_key(TRON_PRIVATE_KEY)
    admin = key.public_key.to_base58check_address()
    amount_raw = int(usdt_amount * 10**USDT_DECIMALS)
    contract = client.get_contract(USDT_CONTRACT)

    txn = (
        contract.functions.transfer(dest_wallet, amount_raw)
        .with_owner(admin)
        .fee_limit(10_000_000)
        .build()
        .sign(key)
    )
    result = txn.broadcast().wait()
    if result.get("receipt", {}).get("result") != "SUCCESS":
        raise RuntimeError(f"TRC20 Transaction failed: {result}")
    return result["id"]
