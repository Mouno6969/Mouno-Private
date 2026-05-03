import base64
import os
import sqlite3
from contextlib import closing

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

DB_PATH = os.path.join(os.path.dirname(__file__), "mouno.db")


def _seller_master_key():
    from config import SELLER_WALLET_MASTER_KEY

    if not SELLER_WALLET_MASTER_KEY:
        raise RuntimeError("SELLER_WALLET_MASTER_KEY is not configured. Admin must set it in .env before seller automated delivery can be enabled.")
    return SELLER_WALLET_MASTER_KEY


def init_user_wallets():
    with closing(sqlite3.connect(DB_PATH)) as con:
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS user_wallets (
                user_id TEXT PRIMARY KEY,
                encrypted_key TEXT,
                salt TEXT,
                network TEXT DEFAULT 'solana',
                wallet_address TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        con.commit()


def make_fernet(password: str, salt: bytes) -> Fernet:
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=100000)
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return Fernet(key)


def encrypt_key(private_key: str, password: str) -> tuple[str, str]:
    salt = os.urandom(16)
    encrypted = make_fernet(password, salt).encrypt(private_key.encode())
    return base64.b64encode(encrypted).decode(), base64.b64encode(salt).decode()


def decrypt_key(encrypted_key: str, salt: str, password: str) -> str:
    salt_bytes = base64.b64decode(salt)
    enc_bytes = base64.b64decode(encrypted_key)
    return make_fernet(password, salt_bytes).decrypt(enc_bytes).decode()


def encrypt_seller_key(private_key: str) -> tuple[str, str]:
    return encrypt_key(private_key, _seller_master_key())


def decrypt_seller_key(encrypted_key: str, salt: str) -> str:
    return decrypt_key(encrypted_key, salt, _seller_master_key())


def save_user_wallet(user_id, encrypted_key, salt, network, wallet_address):
    with closing(sqlite3.connect(DB_PATH)) as con:
        con.execute(
            """
            INSERT OR REPLACE INTO user_wallets
            (user_id, encrypted_key, salt, network, wallet_address)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, encrypted_key, salt, network, wallet_address),
        )
        con.commit()


def get_user_wallet(user_id):
    with closing(sqlite3.connect(DB_PATH)) as con:
        return con.execute(
            "SELECT encrypted_key, salt, network, wallet_address FROM user_wallets WHERE user_id=?",
            (user_id,),
        ).fetchone()


def delete_user_wallet(user_id):
    with closing(sqlite3.connect(DB_PATH)) as con:
        con.execute("DELETE FROM user_wallets WHERE user_id=?", (user_id,))
        con.commit()


def get_wallet_address(network, private_key):
    try:
        if network == "solana":
            import base58
            from solders.keypair import Keypair

            keypair = Keypair.from_bytes(base58.b58decode(private_key))
            return str(keypair.pubkey())
        if network == "trc20":
            from tron_utils import tron_private_key

            key = tron_private_key(private_key)
            return key.public_key.to_base58check_address()

        from web3 import Web3

        return Web3().eth.account.from_key(private_key).address
    except Exception as exc:
        raise RuntimeError(f"Invalid private key: {exc}") from exc


def get_user_balance(user_id, password):
    row = get_user_wallet(user_id)
    if not row:
        return None, None, None

    encrypted_key, salt, network, _wallet_address = row
    try:
        private_key = decrypt_key(encrypted_key, salt, password)
    except Exception:
        return None, None, "wrong_password"

    try:
        from balance import get_evm_balance, get_solana_balance, get_tron_balance

        if network == "solana":
            return get_solana_balance(private_key), network, None
        if network == "trc20":
            return get_tron_balance(private_key), network, None
        return get_evm_balance(network, private_key), network, None
    except Exception as exc:
        return None, network, str(exc)


def send_from_user_wallet(user_id, password, dest_wallet, amount):
    row = get_user_wallet(user_id)
    if not row:
        raise RuntimeError("Wallet setup করা নেই!")

    encrypted_key, salt, network, _wallet_address = row
    try:
        private_key = decrypt_key(encrypted_key, salt, password)
    except Exception as exc:
        raise RuntimeError("ভুল password!") from exc

    if network == "solana":
        return _send_solana_usdc(private_key, dest_wallet, amount)
    if network == "trc20":
        return _send_trc20_usdt(private_key, dest_wallet, amount)
    return _send_evm_token(private_key, network, dest_wallet, amount)


def send_with_private_key(network, private_key, dest_wallet, amount):
    if network == "solana":
        return _send_solana_usdc(private_key, dest_wallet, amount)
    if network == "trc20":
        return _send_trc20_usdt(private_key, dest_wallet, amount)
    if network == "ton":
        raise RuntimeError("TON seller automated delivery is not supported by private-key helper yet.")
    return _send_evm_token(private_key, network, dest_wallet, amount)


def send_from_seller_wallet(seller_id, network, dest_wallet, amount):
    from db import get_seller_wallet

    row = get_seller_wallet(seller_id, network)
    if not row or not row[5]:
        raise RuntimeError("Seller delivery wallet is not enabled for this network.")
    _seller_id, _network, encrypted_key, salt, _wallet_address, _enabled, *_rest = row
    private_key = decrypt_seller_key(encrypted_key, salt)
    return send_with_private_key(network, private_key, dest_wallet, amount)


def _send_solana_usdc(private_key, dest_wallet, amount):
    import base64

    import base58
    import requests
    from solders.hash import Hash
    from solders.keypair import Keypair
    from solders.message import Message
    from solders.pubkey import Pubkey
    from solders.transaction import Transaction
    from spl.token.constants import TOKEN_PROGRAM_ID
    from spl.token.instructions import (
        TransferCheckedParams,
        create_associated_token_account,
        get_associated_token_address,
        transfer_checked,
    )

    usdc_mint = Pubkey.from_string("EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v")
    solana_rpc = "https://api.mainnet-beta.solana.com"
    keypair = Keypair.from_bytes(base58.b58decode(private_key))
    admin_pub = keypair.pubkey()
    dest_pub = Pubkey.from_string(dest_wallet)
    admin_ata = get_associated_token_address(admin_pub, usdc_mint)
    dest_ata = get_associated_token_address(dest_pub, usdc_mint)

    blockhash_resp = requests.post(
        solana_rpc,
        json={"jsonrpc": "2.0", "id": 1, "method": "getLatestBlockhash", "params": [{"commitment": "confirmed"}]},
        timeout=30,
    ).json()
    recent_blockhash = Hash.from_string(blockhash_resp["result"]["value"]["blockhash"])

    instructions = []
    dest_info = requests.post(
        solana_rpc,
        json={"jsonrpc": "2.0", "id": 1, "method": "getAccountInfo", "params": [str(dest_ata)]},
        timeout=10,
    ).json()
    if not dest_info["result"]["value"]:
        instructions.append(create_associated_token_account(payer=admin_pub, owner=dest_pub, mint=usdc_mint))

    instructions.append(
        transfer_checked(
            TransferCheckedParams(
                program_id=TOKEN_PROGRAM_ID,
                source=admin_ata,
                mint=usdc_mint,
                dest=dest_ata,
                owner=admin_pub,
                amount=int(amount * 10**6),
                decimals=6,
                signers=[],
            )
        )
    )
    msg = Message.new_with_blockhash(instructions, admin_pub, recent_blockhash)
    tx = Transaction([keypair], msg, recent_blockhash)
    result = requests.post(
        solana_rpc,
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "sendTransaction",
            "params": [base64.b64encode(bytes(tx)).decode(), {"encoding": "base64", "preflightCommitment": "confirmed"}],
        },
        timeout=30,
    ).json()
    if "error" in result:
        raise RuntimeError(result["error"])
    return result["result"]


def _send_trc20_usdt(private_key, dest_wallet, amount):
    from tron_utils import tron_client, tron_private_key

    client = tron_client()
    key = tron_private_key(private_key)
    addr = key.public_key.to_base58check_address()
    contract = client.get_contract("TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t")
    txn = (
        contract.functions.transfer(dest_wallet, int(amount * 10**6))
        .with_owner(addr)
        .fee_limit(10_000_000)
        .build()
        .sign(key)
    )
    result = txn.broadcast().wait()
    if result.get("receipt", {}).get("result") != "SUCCESS":
        raise RuntimeError(f"TRC20 failed: {result}")
    return result["id"]


def _send_evm_token(private_key, network, dest_wallet, amount):
    from web3 import Web3

    from balance import CONTRACTS, RPCS
    from token_abi import ERC20_ABI

    chain_ids = {"polygon": 137, "bsc": 56, "avalanche": 43114, "ethereum": 1, "ethereum_usdc": 1, "base": 8453}
    rpc = RPCS.get(network)
    contract_info = CONTRACTS.get(network)
    if not rpc or not contract_info:
        raise RuntimeError(f"Unsupported network: {network}")

    w3 = Web3(Web3.HTTPProvider(rpc))
    account = w3.eth.account.from_key(private_key)
    admin = account.address
    contract = w3.eth.contract(address=Web3.to_checksum_address(contract_info["address"]), abi=ERC20_ABI)
    amount_raw = int(amount * 10 ** contract_info["decimals"])
    txn = contract.functions.transfer(Web3.to_checksum_address(dest_wallet), amount_raw).build_transaction(
        {
            "from": admin,
            "nonce": w3.eth.get_transaction_count(admin),
            "gasPrice": w3.eth.gas_price,
            "gas": 100000,
            "chainId": chain_ids.get(network, 1),
        }
    )
    signed = w3.eth.account.sign_transaction(txn, private_key)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
    if receipt.status != 1:
        raise RuntimeError("Transaction failed!")
    return tx_hash.hex()


init_user_wallets()
