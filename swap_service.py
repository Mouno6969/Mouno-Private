from decimal import Decimal, InvalidOperation
from urllib.parse import urlencode

import requests


LIFI_BASE_URL = "https://li.quest/v1"
NATIVE_TOKEN_ADDRESSES = {
    "0x0000000000000000000000000000000000000000",
    "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
    "11111111111111111111111111111111",
}
DEFAULT_WALLET = "0x0000000000000000000000000000000000000001"


def _headers(api_key=None):
    headers = {"Accept": "application/json"}
    if api_key:
        headers["x-lifi-api-key"] = api_key
    return headers


def get_lifi_chains(api_key=None, timeout=20):
    params = {"chainTypes": "EVM,SVM"}
    response = requests.get(f"{LIFI_BASE_URL}/chains", params=params, headers=_headers(api_key), timeout=timeout)
    response.raise_for_status()
    chains = response.json().get("chains", [])
    return [chain for chain in chains if chain.get("mainnet") and chain.get("id")]


def fallback_chains():
    return [
        {"id": 1, "key": "eth", "name": "Ethereum", "coin": "ETH"},
        {"id": 8453, "key": "bas", "name": "Base", "coin": "ETH"},
        {"id": 137, "key": "pol", "name": "Polygon", "coin": "MATIC"},
        {"id": 56, "key": "bsc", "name": "BSC", "coin": "BNB"},
        {"id": 42161, "key": "arb", "name": "Arbitrum", "coin": "ETH"},
        {"id": 10, "key": "opt", "name": "Optimism", "coin": "ETH"},
        {"id": 43114, "key": "ava", "name": "Avalanche", "coin": "AVAX"},
        {"id": 100, "key": "dai", "name": "Gnosis", "coin": "xDAI"},
        {"id": 324, "key": "era", "name": "zkSync Era", "coin": "ETH"},
        {"id": 59144, "key": "lna", "name": "Linea", "coin": "ETH"},
        {"id": 534352, "key": "scl", "name": "Scroll", "coin": "ETH"},
        {"id": 81457, "key": "bls", "name": "Blast", "coin": "ETH"},
    ]


def chain_label(chain):
    name = chain.get("name") or chain.get("key") or str(chain.get("id"))
    coin = chain.get("coin")
    return f"{name} ({coin})" if coin else name


def find_chain(chains, query):
    query = str(query or "").strip().lower()
    if not query:
        return None
    for chain in chains:
        if query == str(chain.get("id")):
            return chain
    for chain in chains:
        values = [chain.get("key"), chain.get("name"), chain.get("coin")]
        if any(query == str(value or "").lower() for value in values):
            return chain
    for chain in chains:
        values = [chain.get("key"), chain.get("name"), chain.get("coin")]
        if any(query in str(value or "").lower() for value in values):
            return chain
    return None


def normalize_token_input(token, chain_id=None):
    token = str(token or "").strip()
    is_native = token.lower() in {"native", "eth", "bnb", "matic", "avax", "sol"}
    if is_native:
        sol_identifiers = {"1151111081099710", "sol"}
        if chain_id and str(chain_id).lower() in sol_identifiers:
            return "11111111111111111111111111111111"
        return "0x0000000000000000000000000000000000000000"
    return token


def fetch_token(chain_id, token, api_key=None, timeout=20):
    params = {"chain": str(chain_id), "token": normalize_token_input(token, chain_id)}
    response = requests.get(f"{LIFI_BASE_URL}/token", params=params, headers=_headers(api_key), timeout=timeout)
    response.raise_for_status()
    return response.json()


def decimal_amount_to_raw(amount, decimals):
    try:
        value = Decimal(str(amount).strip())
    except (InvalidOperation, AttributeError) as exc:
        raise ValueError("Invalid amount") from exc
    if value <= 0:
        raise ValueError("Invalid amount")
    raw = value * (Decimal(10) ** int(decimals))
    if raw != raw.to_integral_value():
        raise ValueError(f"Amount has more than {decimals} decimal places")
    return str(int(raw))


def raw_amount_to_decimal(amount, decimals):
    try:
        value = Decimal(str(amount or "0")) / (Decimal(10) ** int(decimals or 0))
    except Exception:
        return "0"
    text = format(value.normalize(), "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


def fetch_lifi_approval(chain_id, token_address, amount, api_key=None):
    params = {
        "chain": str(chain_id),
        "token": token_address,
        "amount": str(amount),
    }
    response = requests.get(f"{LIFI_BASE_URL}/contractCalls/approve/transaction", params=params, headers=_headers(api_key))
    response.raise_for_status()
    return response.json()


def get_lifi_status(chain_id, tx_hash, api_key=None):
    params = {"chain": str(chain_id), "txHash": tx_hash}
    response = requests.get(f"{LIFI_BASE_URL}/status", params=params, headers=_headers(api_key))
    response.raise_for_status()
    return response.json()


def quote_lifi(intent, api_key=None, timeout=35):
    from_token = fetch_token(intent["from_chain_id"], intent["from_token"], api_key=api_key)
    to_token = fetch_token(intent["to_chain_id"], intent["to_token"], api_key=api_key)
    from_amount_raw = decimal_amount_to_raw(intent["amount"], from_token["decimals"])
    order = "FASTEST" if intent.get("preference") == "fastest" else "CHEAPEST"
    wallet = intent.get("wallet") or DEFAULT_WALLET
    params = {
        "fromChain": str(intent["from_chain_id"]),
        "toChain": str(intent["to_chain_id"]),
        "fromToken": from_token["address"],
        "toToken": to_token["address"],
        "fromAmount": from_amount_raw,
        "fromAddress": wallet,
        "toAddress": wallet,
        "slippage": str(intent.get("slippage") or 0.005),
        "order": order,
    }
    response = requests.get(f"{LIFI_BASE_URL}/quote", params=params, headers=_headers(api_key), timeout=timeout)
    response.raise_for_status()
    quote = response.json()
    quote["_fromTokenInfo"] = from_token
    quote["_toTokenInfo"] = to_token
    return quote


def summarize_quote(quote):
    action = quote.get("action", {})
    estimate = quote.get("estimate", {})
    from_token = quote.get("_fromTokenInfo") or action.get("fromToken", {})
    to_token = quote.get("_toTokenInfo") or action.get("toToken", {})
    to_amount = raw_amount_to_decimal(estimate.get("toAmount"), to_token.get("decimals"))
    to_min = raw_amount_to_decimal(estimate.get("toAmountMin"), to_token.get("decimals"))
    gas_usd = sum(Decimal(str(cost.get("amountUSD") or "0")) for cost in estimate.get("gasCosts", []) if isinstance(cost, dict))
    fee_usd = sum(Decimal(str(cost.get("amountUSD") or "0")) for cost in estimate.get("feeCosts", []) if isinstance(cost, dict))
    duration = estimate.get("executionDuration")
    approval_address = estimate.get("approvalAddress")
    from_addr = str(from_token.get("address") or "").lower()
    approval_needed = bool(approval_address and from_addr not in NATIVE_TOKEN_ADDRESSES)
    tx = quote.get("transactionRequest") or {}
    return {
        "tool": quote.get("toolDetails", {}).get("name") or quote.get("tool") or "LI.FI",
        "from_symbol": from_token.get("symbol") or "from token",
        "to_symbol": to_token.get("symbol") or "to token",
        "to_amount": to_amount,
        "to_min": to_min,
        "gas_usd": format(gas_usd, "f"),
        "fee_usd": format(fee_usd, "f"),
        "duration": duration,
        "approval_needed": approval_needed,
        "approval_address": approval_address,
        "tx_to": tx.get("to"),
        "tx_value": tx.get("value"),
        "tx_data": tx.get("data"),
        "chain_id": tx.get("chainId"),
    }


def build_lifi_widget_url(intent, quote=None, base_url="https://jumper.exchange/"):
    quote = quote or {}
    action = quote.get("action") or {}
    from_token = quote.get("_fromTokenInfo") or action.get("fromToken") or {}
    to_token = quote.get("_toTokenInfo") or action.get("toToken") or {}
    from_token_address = from_token.get("address") or intent.get("from_token")
    to_token_address = to_token.get("address") or intent.get("to_token")
    wallet = intent.get("wallet")
    params = {
        "fromAmount": intent.get("amount"),
        "fromChain": intent.get("from_chain_id"),
        "fromToken": normalize_token_input(from_token_address, intent.get("from_chain_id")),
        "toChain": intent.get("to_chain_id"),
        "toToken": normalize_token_input(to_token_address, intent.get("to_chain_id")),
        "toAddress": wallet,
        "slippage": intent.get("slippage") or 0.005,
    }
    clean_params = {key: value for key, value in params.items() if value not in (None, "")}
    separator = "&" if "?" in base_url else "?"
    return f"{base_url}{separator}{urlencode(clean_params)}"


def short_tx_data(data, limit=180):
    data = str(data or "")
    if len(data) <= limit:
        return data
    return f"{data[:limit]}…"
