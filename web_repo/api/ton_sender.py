import base64

import requests
from tonsdk.contract.wallet import WalletVersionEnum, Wallets
from tonsdk.utils import Address, to_nano

from config import TON_API_KEY, TON_MNEMONIC, TON_RPC


def _headers():
    return {"X-API-Key": TON_API_KEY} if TON_API_KEY else {}


def _api_url(method):
    return f"{TON_RPC.rstrip('/')}/api/v2/{method}"


def ton_wallet():
    if not TON_MNEMONIC:
        raise RuntimeError("TON_MNEMONIC is not configured")
    words = TON_MNEMONIC.replace(",", " ").split()
    if len(words) not in {12, 18, 24}:
        raise RuntimeError("TON_MNEMONIC must contain 12, 18, or 24 words")
    _mnemonics, _pub_k, _priv_k, wallet = Wallets.from_mnemonics(words, WalletVersionEnum.v4r2, workchain=0)
    return wallet


def get_ton_address():
    wallet = ton_wallet()
    return wallet.address.to_string(True, True, True)


def get_ton_balance(address=None):
    try:
        addr = address or get_ton_address()
        response = requests.get(_api_url("getAddressBalance"), params={"address": addr}, headers=_headers(), timeout=20)
        response.raise_for_status()
        data = response.json()
        if not data.get("ok"):
            return None
        return round(int(data["result"]) / 10**9, 6)
    except Exception:
        return None


def _seqno(address):
    response = requests.get(_api_url("getWalletInformation"), params={"address": address}, headers=_headers(), timeout=20)
    response.raise_for_status()
    data = response.json()
    if not data.get("ok"):
        raise RuntimeError(data)
    return int(data["result"].get("seqno") or 0)


def send_ton(dest_wallet: str, ton_amount: float) -> str:
    wallet = ton_wallet()
    from_address = wallet.address.to_string(True, True, True)
    dest = Address(dest_wallet)
    seqno = _seqno(from_address)
    transfer = wallet.create_transfer_message(
        to_addr=dest,
        amount=to_nano(float(ton_amount), "ton"),
        seqno=seqno,
        payload="",
    )
    boc = base64.b64encode(transfer["message"].to_boc(False)).decode()
    response = requests.post(_api_url("sendBoc"), json={"boc": boc}, headers=_headers(), timeout=30)
    response.raise_for_status()
    data = response.json()
    if not data.get("ok"):
        raise RuntimeError(data)
    return data.get("result", {}).get("hash") or data.get("result") or f"TON-{seqno}"
