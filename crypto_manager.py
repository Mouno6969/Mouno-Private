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
    # Ensure the multi-wallet tables exist and any legacy single wallet is
    # migrated into them (idempotent, non-destructive).
    init_user_wallets_v2()
    migrate_legacy_wallets()


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


# ===========================================================================
# Multi-wallet support (user_wallets_v2 + wallet_master)
# ---------------------------------------------------------------------------
# A user may now connect MANY wallets across any network (and several wallets
# on the same network). Every wallet's private key is encrypted with ONE
# master password per user. The master password is validated against a stored
# verifier (a known probe string encrypted with the same scheme). Balances are
# read from public addresses and never need the master password; only sending
# (which decrypts a key) requires it.
# ===========================================================================

_MASTER_PROBE = "mouno-master-ok"
MIN_MASTER_PASSWORD_LEN = 8


def init_user_wallets_v2():
    with closing(sqlite3.connect(DB_PATH)) as con:
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS user_wallets_v2 (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                network TEXT NOT NULL,
                label TEXT,
                wallet_address TEXT,
                encrypted_key TEXT NOT NULL,
                salt TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        con.execute("CREATE INDEX IF NOT EXISTS idx_user_wallets_v2_user ON user_wallets_v2(user_id)")
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS wallet_master (
                user_id TEXT PRIMARY KEY,
                verifier TEXT NOT NULL,
                salt TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        con.commit()


def migrate_legacy_wallets():
    """Idempotently copy single-wallet rows from the legacy user_wallets table
    into user_wallets_v2. Never destroys legacy data so rollback stays safe."""
    with closing(sqlite3.connect(DB_PATH)) as con:
        try:
            legacy = con.execute(
                "SELECT user_id, encrypted_key, salt, network, wallet_address FROM user_wallets"
            ).fetchall()
        except Exception:
            legacy = []
        for user_id, encrypted_key, salt, network, wallet_address in legacy:
            if not encrypted_key or not salt:
                continue
            exists = con.execute(
                "SELECT 1 FROM user_wallets_v2 WHERE user_id=? AND network=? AND IFNULL(wallet_address,'')=IFNULL(?,'')",
                (str(user_id), network, wallet_address),
            ).fetchone()
            if exists:
                continue
            con.execute(
                "INSERT INTO user_wallets_v2 (user_id, network, label, wallet_address, encrypted_key, salt) VALUES (?,?,?,?,?,?)",
                (str(user_id), network, None, wallet_address, encrypted_key, salt),
            )
        con.commit()


def _v2_rows(user_id):
    with closing(sqlite3.connect(DB_PATH)) as con:
        con.row_factory = sqlite3.Row
        return con.execute(
            "SELECT * FROM user_wallets_v2 WHERE user_id=? ORDER BY id ASC", (str(user_id),)
        ).fetchall()


def _get_v2_wallet(user_id, wallet_id):
    with closing(sqlite3.connect(DB_PATH)) as con:
        con.row_factory = sqlite3.Row
        return con.execute(
            "SELECT * FROM user_wallets_v2 WHERE id=? AND user_id=?",
            (int(wallet_id), str(user_id)),
        ).fetchone()


# ─── Master password ───
def get_master_record(user_id):
    with closing(sqlite3.connect(DB_PATH)) as con:
        return con.execute(
            "SELECT verifier, salt FROM wallet_master WHERE user_id=?", (str(user_id),)
        ).fetchone()


def set_master_password(user_id, password):
    if not password or len(password) < MIN_MASTER_PASSWORD_LEN:
        raise RuntimeError(f"Master password must be at least {MIN_MASTER_PASSWORD_LEN} characters.")
    verifier, salt = encrypt_key(_MASTER_PROBE, password)
    with closing(sqlite3.connect(DB_PATH)) as con:
        con.execute(
            "INSERT OR REPLACE INTO wallet_master (user_id, verifier, salt) VALUES (?,?,?)",
            (str(user_id), verifier, salt),
        )
        con.commit()


def has_master_password(user_id):
    """True if the user has a master password (explicit verifier OR migrated
    wallets whose password is effectively the master password)."""
    if get_master_record(user_id):
        return True
    return bool(_v2_rows(user_id))


def verify_master_password(user_id, password):
    rec = get_master_record(user_id)
    if rec:
        try:
            return decrypt_key(rec[0], rec[1], password) == _MASTER_PROBE
        except Exception:
            return False
    # Lazy-adopt: migrated/legacy user without a verifier yet. If the password
    # decrypts any existing wallet, adopt it as the master password.
    for row in _v2_rows(user_id):
        try:
            decrypt_key(row["encrypted_key"], row["salt"], password)
            set_master_password(user_id, password)
            return True
        except Exception:
            continue
    return False


# ─── New-wallet key generation ───
def create_private_key(network):
    net = (network or "").lower()
    if net.startswith("solana"):
        import base58
        from solders.keypair import Keypair

        return base58.b58encode(bytes(Keypair())).decode()
    if net == "trc20":
        from tronpy.keys import PrivateKey

        return PrivateKey.random().hex()
    if net == "ton":
        raise RuntimeError("Creating a new TON wallet is not supported yet. Please import an existing wallet.")
    # Everything else (ethereum, ethereum_usdc, erc20, bsc, polygon, base, etc.)
    # is an EVM chain. Mirror get_wallet_address's EVM fallthrough so token
    # variants like "ethereum_usdc" are handled instead of being rejected.
    from web3 import Web3

    return Web3().eth.account.create().key.hex()


# ─── Multi-wallet CRUD ───
def add_user_wallet(user_id, network, private_key_or_create, master_password, label=None):
    """Create or import a wallet for `network`, encrypt the key with the user's
    master password and store it. Sets the master password on the very first
    wallet; verifies it for every subsequent wallet."""
    user_id = str(user_id)
    if not master_password:
        raise RuntimeError("Master password is required.")

    is_first_wallet = not has_master_password(user_id)
    if is_first_wallet:
        if len(master_password) < MIN_MASTER_PASSWORD_LEN:
            raise RuntimeError(f"Master password must be at least {MIN_MASTER_PASSWORD_LEN} characters.")
    else:
        if not verify_master_password(user_id, master_password):
            raise RuntimeError("Wrong master password.")

    if not private_key_or_create or private_key_or_create == "create":
        private_key = create_private_key(network)
    else:
        private_key = str(private_key_or_create).strip()

    wallet_address = get_wallet_address(network, private_key)
    encrypted_key, salt = encrypt_key(private_key, master_password)
    label = (label or "").strip() or None

    # Persist the master-password verifier (on first wallet) and the wallet row
    # inside a single transaction so we never end up with a verifier but no
    # wallet (or vice-versa) if something fails midway.
    with closing(sqlite3.connect(DB_PATH)) as con:
        try:
            if is_first_wallet:
                verifier, master_salt = encrypt_key(_MASTER_PROBE, master_password)
                con.execute(
                    "INSERT OR REPLACE INTO wallet_master (user_id, verifier, salt) VALUES (?,?,?)",
                    (user_id, verifier, master_salt),
                )
            cur = con.execute(
                "INSERT INTO user_wallets_v2 (user_id, network, label, wallet_address, encrypted_key, salt) VALUES (?,?,?,?,?,?)",
                (user_id, network, label, wallet_address, encrypted_key, salt),
            )
            con.commit()
            wallet_id = cur.lastrowid
        except Exception:
            con.rollback()
            raise
    return {"id": wallet_id, "network": network, "label": label, "wallet_address": wallet_address}


def list_user_wallets(user_id):
    """All wallets for a user WITHOUT decrypting keys."""
    return [
        {
            "id": r["id"],
            "network": r["network"],
            "label": r["label"],
            "wallet_address": r["wallet_address"],
            "created_at": r["created_at"],
        }
        for r in _v2_rows(user_id)
    ]


def get_user_wallets_by_network(user_id, network):
    return [w for w in list_user_wallets(user_id) if w["network"] == network]


def delete_user_wallet_by_id(user_id, wallet_id, master_password=None):
    user_id = str(user_id)
    if has_master_password(user_id):
        if not verify_master_password(user_id, master_password or ""):
            raise RuntimeError("Wrong master password.")
    with closing(sqlite3.connect(DB_PATH)) as con:
        cur = con.execute(
            "DELETE FROM user_wallets_v2 WHERE id=? AND user_id=?", (int(wallet_id), user_id)
        )
        con.commit()
        deleted = cur.rowcount
    # If no wallets remain, drop the master verifier so the user can start fresh.
    if not _v2_rows(user_id):
        with closing(sqlite3.connect(DB_PATH)) as con:
            con.execute("DELETE FROM wallet_master WHERE user_id=?", (user_id,))
            con.commit()
    return deleted > 0


def send_from_wallet(user_id, wallet_id, master_password, to_address, amount, asset=None):
    """Decrypt the chosen wallet's key (transiently) and send, reusing the
    existing per-network transfer logic."""
    user_id = str(user_id)
    row = _get_v2_wallet(user_id, wallet_id)
    if not row:
        raise RuntimeError("Wallet not found.")
    if not verify_master_password(user_id, master_password):
        raise RuntimeError("Wrong master password.")
    private_key = decrypt_key(row["encrypted_key"], row["salt"], master_password)
    return send_with_private_key(row["network"], private_key, to_address, amount)


def list_wallet_balances(user_id):
    """Balances for ALL of the user's wallets, fetched from public addresses
    (no master password needed)."""
    wallets = list_user_wallets(user_id)
    from balance import get_wallet_balances

    items = [{"network": w["network"], "address": w["wallet_address"]} for w in wallets]
    balances = get_wallet_balances(items)
    out = []
    for w, b in zip(wallets, balances):
        entry = dict(w)
        entry["balance"] = b.get("balance")
        entry["native_balance"] = b.get("native")
        entry["asset"] = b.get("asset")
        out.append(entry)
    return out


# ===========================================================================
# Legacy single-wallet API — kept working as thin wrappers over the v2 table
# so existing call sites in bot.py / app.py keep functioning. These operate on
# the user's PRIMARY (first) wallet.
# ===========================================================================
def save_user_wallet(user_id, encrypted_key, salt, network, wallet_address):
    """Legacy save. Stores the wallet in user_wallets_v2 (de-duplicated by
    address) so there is a single source of truth."""
    user_id = str(user_id)
    with closing(sqlite3.connect(DB_PATH)) as con:
        con.execute(
            "DELETE FROM user_wallets_v2 WHERE user_id=? AND network=? AND IFNULL(wallet_address,'')=IFNULL(?,'')",
            (user_id, network, wallet_address),
        )
        con.execute(
            "INSERT INTO user_wallets_v2 (user_id, network, label, wallet_address, encrypted_key, salt) VALUES (?,?,?,?,?,?)",
            (user_id, network, None, wallet_address, encrypted_key, salt),
        )
        con.commit()


def get_user_wallet(user_id):
    rows = _v2_rows(user_id)
    if not rows:
        return None
    r = rows[0]
    return (r["encrypted_key"], r["salt"], r["network"], r["wallet_address"])


def get_user_evm_wallet(user_id):
    for r in _v2_rows(user_id):
        net = r["network"]
        if not net.startswith("solana") and net not in ("trc20", "ton"):
            return (r["encrypted_key"], r["salt"], net, r["wallet_address"])
    return None


def get_user_solana_wallet(user_id):
    for r in _v2_rows(user_id):
        if r["network"].startswith("solana"):
            return (r["encrypted_key"], r["salt"], r["network"], r["wallet_address"])
    return None


def delete_user_wallet(user_id):
    """Legacy: delete ALL wallets for the user plus the master verifier."""
    user_id = str(user_id)
    with closing(sqlite3.connect(DB_PATH)) as con:
        con.execute("DELETE FROM user_wallets_v2 WHERE user_id=?", (user_id,))
        con.execute("DELETE FROM wallet_master WHERE user_id=?", (user_id,))
        con.commit()


def get_wallet_address(network, private_key):
    try:
        if network.startswith("solana"):
            import base58
            from solders.keypair import Keypair

            keypair = Keypair.from_bytes(base58.b58decode(private_key))
            return str(keypair.pubkey())
        if network == "ton":
            # TON keys/addresses are managed externally; the import flow stores
            # the address the user provides, so derivation is best-effort.
            return None
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
        raise RuntimeError("Wallet setup করা ন��ই!")

    encrypted_key, salt, network, _wallet_address = row
    try:
        private_key = decrypt_key(encrypted_key, salt, password)
    except Exception as exc:
        raise RuntimeError("ভুল password!") from exc

    if network == "solana":
        return _send_solana_token(private_key, dest_wallet, amount)
    if network == "solana_usdt":
        return _send_solana_token(private_key, dest_wallet, amount, mint="Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB")
    if network == "trc20":
        return _send_trc20_usdt(private_key, dest_wallet, amount)
    return _send_evm_token(private_key, network, dest_wallet, amount)


def send_with_private_key(network, private_key, dest_wallet, amount):
    if network == "solana":
        return _send_solana_token(private_key, dest_wallet, amount)
    if network == "solana_usdt":
        return _send_solana_token(private_key, dest_wallet, amount, mint="Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB")
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


def _send_solana_token(private_key, dest_wallet, amount, mint="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v", decimals=6):
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

    token_mint = Pubkey.from_string(mint)
    solana_rpc = "https://api.mainnet-beta.solana.com"
    keypair = Keypair.from_bytes(base58.b58decode(private_key))
    admin_pub = keypair.pubkey()
    dest_pub = Pubkey.from_string(dest_wallet)
    admin_ata = get_associated_token_address(admin_pub, token_mint)
    dest_ata = get_associated_token_address(dest_pub, token_mint)

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
        instructions.append(create_associated_token_account(payer=admin_pub, owner=dest_pub, mint=token_mint))

    instructions.append(
        transfer_checked(
            TransferCheckedParams(
                program_id=TOKEN_PROGRAM_ID,
                source=admin_ata,
                mint=token_mint,
                dest=dest_ata,
                owner=admin_pub,
                amount=int(amount * 10**decimals),
                decimals=decimals,
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


def send_raw_evm_transaction(network, private_key, to_address, data, value=0, gas_limit=None, rpc_url=None):
    from web3 import Web3

    from balance import RPCS

    def _to_int(v):
        if isinstance(v, str):
            return int(v, 16) if v.startswith("0x") else int(v or 0)
        return int(v or 0)

    rpc = rpc_url or RPCS.get(network)
    if not rpc:
        raise RuntimeError(f"Unsupported network: {network}")
    w3 = Web3(Web3.HTTPProvider(rpc))
    account = w3.eth.account.from_key(private_key)
    tx = {
        "from": account.address,
        "to": Web3.to_checksum_address(to_address),
        "value": _to_int(value),
        "data": data,
        "nonce": w3.eth.get_transaction_count(account.address, "pending"),
        "chainId": w3.eth.chain_id,
    }
    try:
        tx["gasPrice"] = w3.eth.gas_price
    except Exception:
        pass

    if gas_limit:
        tx["gas"] = int(gas_limit)
    else:
        try:
            tx["gas"] = int(w3.eth.estimate_gas(tx) * 1.2)
        except Exception:
            tx["gas"] = 400000

    signed = w3.eth.account.sign_transaction(tx, private_key)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    return tx_hash.hex()


def send_raw_solana_transaction(private_key, base64_tx, rpc_url=None):
    import base64

    import base58
    import requests
    from solders.keypair import Keypair
    from solders.transaction import VersionedTransaction

    keypair = Keypair.from_bytes(base58.b58decode(private_key))
    user_pubkey = keypair.pubkey()

    raw_tx = base64.b64decode(base64_tx)
    vtx = VersionedTransaction.from_bytes(raw_tx)

    # Find the user's index in static_account_keys
    # LI.FI Solana transactions often require multiple signers (e.g. for bridges)
    # We must only sign our part and preserve other existing signatures.
    try:
        user_index = vtx.message.static_account_keys.index(user_pubkey)
    except ValueError:
        raise RuntimeError(f"User pubkey {user_pubkey} not found in transaction required signers.") from None

    if user_index >= vtx.message.header.num_required_signatures:
        raise RuntimeError(f"User pubkey {user_pubkey} is not a required signer for this transaction.")

    # Sign the message with the user's keypair
    signature = keypair.sign_message(bytes(vtx.message))

    # Update only the user's signature in the signatures list
    new_signatures = list(vtx.signatures)
    new_signatures[user_index] = signature

    # Reconstruct from message + signatures (constructor expects signers, not signatures)
    vtx = VersionedTransaction.populate(vtx.message, new_signatures)

    solana_rpc = rpc_url or "https://api.mainnet-beta.solana.com"
    result = requests.post(
        solana_rpc,
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "sendTransaction",
            "params": [base64.b64encode(bytes(vtx)).decode(), {"encoding": "base64", "preflightCommitment": "confirmed"}],
        },
        timeout=30,
    ).json()
    if "error" in result:
        raise RuntimeError(result["error"])
    return result["result"]


init_user_wallets()
