import os
from concurrent.futures import ThreadPoolExecutor, as_completed

import base58
import requests
from solders.keypair import Keypair
from web3 import Web3

from config import (
    AVALANCHE_RPC,
    BASE_RPC,
    BSC_PRIVATE_KEY,
    BSC_RPC,
    ETHEREUM_RPC,
    LOW_GAS_THRESHOLD_AVALANCHE,
    LOW_GAS_THRESHOLD_BASE,
    LOW_GAS_THRESHOLD_BSC,
    LOW_GAS_THRESHOLD_ETHEREUM,
    LOW_GAS_THRESHOLD_ETHEREUM_USDC,
    LOW_GAS_THRESHOLD_POLYGON,
    LOW_GAS_THRESHOLD_SOLANA,
    LOW_GAS_THRESHOLD_TON,
    LOW_GAS_THRESHOLD_TRC20,
    POLYGON_PRIVATE_KEY,
    POLYGON_RPC,
    SOLANA_KEY,
    TRON_PRIVATE_KEY,
)
from ton_sender import get_ton_balance
from token_abi import ERC20_ABI
from tron_utils import tron_client, tron_private_key

CONTRACTS = {
    "polygon": {"token": "usdc", "address": "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359", "decimals": 6},
    "bsc": {"token": "usdt", "address": "0x55d398326f99059fF775485246999027B3197955", "decimals": 18},
    "avalanche": {"token": "usdt", "address": "0x9702230A8Ea53601f5cD2dc00fDBc13d4dF4A8c7", "decimals": 6},
    "ethereum": {"token": "usdt", "address": "0xdAC17F958D2ee523a2206206994597C13D831ec7", "decimals": 6},
    "ethereum_usdc": {"token": "usdc", "address": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48", "decimals": 6},
    "base": {"token": "usdc", "address": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913", "decimals": 6},
}

RPCS = {
    "polygon": POLYGON_RPC,
    "bsc": BSC_RPC,
    "avalanche": AVALANCHE_RPC,
    "ethereum": ETHEREUM_RPC,
    "ethereum_usdc": ETHEREUM_RPC,
    "base": BASE_RPC,
}


def get_evm_address(private_key=None):
    try:
        key = private_key or BSC_PRIVATE_KEY
        if not key:
            return None
        w3 = Web3(Web3.HTTPProvider(BSC_RPC))
        return w3.eth.account.from_key(key).address
    except Exception:
        return None


def get_evm_balance(network, private_key=None):
    try:
        key = private_key or _evm_private_key(network)
        rpc = RPCS.get(network)
        contract_info = CONTRACTS.get(network)
        if not key or not rpc or not contract_info:
            return None

        w3 = Web3(Web3.HTTPProvider(rpc))
        account = w3.eth.account.from_key(key).address
        contract = w3.eth.contract(address=Web3.to_checksum_address(contract_info["address"]), abi=ERC20_ABI)
        balance = contract.functions.balanceOf(account).call()
        return round(balance / 10 ** contract_info["decimals"], 4)
    except Exception:
        return None


def _evm_private_key(network):
    if network == "polygon":
        return POLYGON_PRIVATE_KEY or BSC_PRIVATE_KEY
    return BSC_PRIVATE_KEY


def get_evm_native_balance(network, private_key=None):
    try:
        key = private_key or _evm_private_key(network)
        rpc = RPCS.get(network)
        if not key or not rpc:
            return None
        w3 = Web3(Web3.HTTPProvider(rpc))
        account = w3.eth.account.from_key(key).address
        return round(float(w3.from_wei(w3.eth.get_balance(account), "ether")), 6)
    except Exception:
        return None


def get_solana_balance(private_key=None):
    try:
        key = private_key or SOLANA_KEY
        if not key:
            return None
        keypair = Keypair.from_bytes(base58.b58decode(key))
        wallet = str(keypair.pubkey())
        usdc_mint = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
        response = requests.post(
            "https://api.mainnet-beta.solana.com",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getTokenAccountsByOwner",
                "params": [wallet, {"mint": usdc_mint}, {"encoding": "jsonParsed"}],
            },
            timeout=10,
        ).json()
        accounts = response.get("result", {}).get("value", [])
        if accounts:
            amount = accounts[0]["account"]["data"]["parsed"]["info"]["tokenAmount"]["uiAmount"]
            return round(float(amount), 4)
        return 0.0
    except Exception:
        return None


def get_solana_native_balance(private_key=None):
    try:
        key = private_key or SOLANA_KEY
        if not key:
            return None
        keypair = Keypair.from_bytes(base58.b58decode(key))
        response = requests.post(
            "https://api.mainnet-beta.solana.com",
            json={"jsonrpc": "2.0", "id": 1, "method": "getBalance", "params": [str(keypair.pubkey())]},
            timeout=10,
        ).json()
        value = response.get("result", {}).get("value")
        return round(value / 10**9, 6) if value is not None else None
    except Exception:
        return None


def get_tron_balance(private_key=None):
    try:
        key_hex = private_key or TRON_PRIVATE_KEY
        if not key_hex:
            return None
        client = tron_client()
        key = tron_private_key(key_hex)
        addr = key.public_key.to_base58check_address()
        contract = client.get_contract("TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t")
        balance = contract.functions.balanceOf(addr)
        return round(balance / 10**6, 4)
    except Exception:
        return None


def get_tron_native_balance(private_key=None):
    try:
        key_hex = private_key or TRON_PRIVATE_KEY
        if not key_hex:
            return None
        client = tron_client()
        key = tron_private_key(key_hex)
        addr = key.public_key.to_base58check_address()
        return round(float(client.get_account_balance(addr)), 6)
    except Exception:
        return None


def get_all_balances():
    evm_addr = get_evm_address()
    tasks = {
        "solana": get_solana_balance,
        "polygon": lambda: get_evm_balance("polygon"),
        "bsc": lambda: get_evm_balance("bsc"),
        "avalanche": lambda: get_evm_balance("avalanche"),
        "ethereum": lambda: get_evm_balance("ethereum"),
        "ethereum_usdc": lambda: get_evm_balance("ethereum_usdc"),
        "base": lambda: get_evm_balance("base"),
        "trc20": get_tron_balance,
        "ton": get_ton_balance,
    }
    balances = {}
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(fn): net for net, fn in tasks.items()}
        for future in as_completed(futures):
            net = futures[future]
            try:
                balances[net] = future.result(timeout=8)
            except Exception:
                balances[net] = None
    return balances, evm_addr


GAS_META = {
    "solana": ("SOL", LOW_GAS_THRESHOLD_SOLANA),
    "polygon": ("MATIC/POL", LOW_GAS_THRESHOLD_POLYGON),
    "bsc": ("BNB", LOW_GAS_THRESHOLD_BSC),
    "avalanche": ("AVAX", LOW_GAS_THRESHOLD_AVALANCHE),
    "ethereum": ("ETH", LOW_GAS_THRESHOLD_ETHEREUM),
    "ethereum_usdc": ("ETH", LOW_GAS_THRESHOLD_ETHEREUM_USDC),
    "base": ("ETH", LOW_GAS_THRESHOLD_BASE),
    "trc20": ("TRX", LOW_GAS_THRESHOLD_TRC20),
    "ton": ("TON", LOW_GAS_THRESHOLD_TON),
}


def get_native_gas_balances():
    tasks = {
        "solana": get_solana_native_balance,
        "polygon": lambda: get_evm_native_balance("polygon"),
        "bsc": lambda: get_evm_native_balance("bsc"),
        "avalanche": lambda: get_evm_native_balance("avalanche"),
        "ethereum": lambda: get_evm_native_balance("ethereum"),
        "ethereum_usdc": lambda: get_evm_native_balance("ethereum_usdc"),
        "base": lambda: get_evm_native_balance("base"),
        "trc20": get_tron_native_balance,
        "ton": get_ton_balance,
    }
    balances = {}
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(fn): net for net, fn in tasks.items()}
        for future in as_completed(futures):
            net = futures[future]
            try:
                balances[net] = future.result(timeout=8)
            except Exception:
                balances[net] = None
    return balances


def check_gas_sufficient(network):
    symbol, threshold = GAS_META.get(network, ("native", 0))
    return True, None, threshold, symbol


def check_sufficient(network, amount, exclude_order_id=None, exclude_trx_id=None):
    balances, _ = get_all_balances()
    bal = balances.get(network)
    if bal is None:
        return True, None
    try:
        from db import get_active_reserved_amount

        reserved = get_active_reserved_amount(network, exclude_order_id=exclude_order_id, exclude_trx_id=exclude_trx_id)
    except Exception:
        reserved = 0
    available = float(bal) - float(reserved or 0)
    return available >= float(amount), round(available, 6)
