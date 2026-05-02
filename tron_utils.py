def normalize_tron_private_key(private_key: str) -> str:
    key = private_key.strip()
    if key.startswith("0x"):
        key = key[2:]
    if len(key) != 64:
        raise ValueError("TRON private key must be 64 hex characters")
    bytes.fromhex(key)
    return key


def tron_private_key(private_key: str):
    from tronpy.keys import PrivateKey

    return PrivateKey(bytes.fromhex(normalize_tron_private_key(private_key)))


def tron_client():
    from tronpy import Tron

    return Tron(network="mainnet")
