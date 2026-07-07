import re
from decimal import Decimal, InvalidOperation
from urllib.parse import urlencode

import requests

try:
    import base58 as _base58
except Exception:  # pragma: no cover - base58 is an optional hardening dep
    _base58 = None


LIFI_BASE_URL = "https://li.quest/v1"
NATIVE_TOKEN_ADDRESSES = {
    "0x0000000000000000000000000000000000000000",
    "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
    "11111111111111111111111111111111",
}

# Per-ecosystem placeholder addresses used when the caller has not supplied a
# real wallet of the matching type. LI.FI validates that fromAddress/toAddress
# are well-formed for their chain, so a quote across ecosystems (e.g. BTC -> ETH
# or SOL -> USDC) fails with "Invalid fromAddress" unless each side gets an
# address of the correct format. These are valid, well-known placeholder
# addresses good enough to *price* a route; real execution still requires the
# user's own addresses (passed through as from_address / to_address).
ECOSYSTEM_PLACEHOLDER = {
    "EVM": "0x000000000000000000000000000000000000dEaD",
    "SVM": "11111111111111111111111111111111",
    "UTXO": "bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mdq",
}
DEFAULT_WALLET = ECOSYSTEM_PLACEHOLDER["EVM"]

# Non-EVM chains LI.FI supports. Everything else is treated as EVM.
SVM_CHAIN_IDS = {"1151111081099710", "sol", "solana", "sol-mainnet"}
UTXO_CHAIN_IDS = {"20000000000001", "btc", "bitcoin"}


class SwapError(Exception):
    """A swap failure with a safe, user-facing message (no internal details)."""

    def __init__(self, message, status=400):
        super().__init__(message)
        self.message = message
        self.status = status


def _headers(api_key=None):
    headers = {"Accept": "application/json"}
    if api_key:
        headers["x-lifi-api-key"] = api_key
    return headers


def _friendly_lifi_message(message, status):
    """Translate a raw LI.FI error into a safe, user-facing message.

    Never echoes the request URL or parameters (which contain wallet
    addresses) back to the client.
    """
    text = str(message or "").lower()
    if status == 429:
        return "The swap service is busy right now. Please try again in a moment."
    if "same token" in text or "both the source and destination" in text:
        return "Source and destination are the same token. Pick two different tokens."
    if any(s in text for s in ("no available", "no route", "could not find a", "no quote")):
        return "No swap route is available for this pair and amount right now."
    if "invalid fromaddress" in text or "invalid toaddress" in text or "extended address" in text:
        return "A wallet address for one of the selected networks is missing or invalid."
    if "amount" in text:
        return "The amount is too small or invalid for this swap."
    if any(s in text for s in ("token not found", "token is invalid", "invalid token", "unknown token", "token unknown")):
        return "One of the selected tokens is not supported on its network."
    if status == 404:
        return "No swap route is available for this pair right now."
    return "Unable to get a swap quote for this pair right now. Please try again."


def _lifi_get(path, params, api_key=None, timeout=20):
    """GET a LI.FI endpoint and translate failures into SwapError.

    Returns the parsed JSON body on success. On any HTTP/network error raises
    SwapError with a message that is safe to show to end users.
    """
    try:
        response = requests.get(
            f"{LIFI_BASE_URL}{path}",
            params=params,
            headers=_headers(api_key),
            timeout=timeout,
        )
    except requests.Timeout:
        raise SwapError("The swap service timed out. Please try again.", 504)
    except requests.RequestException:
        raise SwapError("Could not reach the swap service. Please try again.", 502)

    if response.status_code == 429:
        raise SwapError(_friendly_lifi_message(None, 429), 429)

    if not response.ok:
        lifi_message = None
        try:
            lifi_message = response.json().get("message")
        except ValueError:
            lifi_message = None
        raise SwapError(_friendly_lifi_message(lifi_message, response.status_code), 400)

    try:
        return response.json()
    except ValueError:
        raise SwapError("The swap service returned an invalid response. Please try again.", 502)


def get_lifi_chains(api_key=None, timeout=20):
    # Include UTXO (Bitcoin) and SVM (Solana) so any supported network can be
    # selected as a source or destination, not just EVM chains.
    data = _lifi_get("/chains", {"chainTypes": "EVM,SVM,UTXO"}, api_key, timeout)
    chains = data.get("chains", [])
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
        {"id": 1151111081099710, "key": "sol", "name": "Solana", "coin": "SOL"},
        {"id": 20000000000001, "key": "btc", "name": "Bitcoin", "coin": "BTC"},
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


def chain_ecosystem(chain_id):
    """Classify a chain as EVM, SVM (Solana) or UTXO (Bitcoin)."""
    cid = str(chain_id or "").strip().lower()
    if cid in SVM_CHAIN_IDS:
        return "SVM"
    if cid in UTXO_CHAIN_IDS:
        return "UTXO"
    return "EVM"


_EVM_ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
_BTC_ADDRESS_RE = re.compile(r"^(bc1[02-9ac-hj-np-z]{6,87}|[13][a-km-zA-HJ-NP-Z1-9]{25,34})$")
_SVM_ADDRESS_RE = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$")


def _is_evm_address(address):
    return bool(_EVM_ADDRESS_RE.match(str(address or "").strip()))


def _is_utxo_address(address):
    return bool(_BTC_ADDRESS_RE.match(str(address or "").strip()))


def _is_svm_address(address):
    a = str(address or "").strip()
    # Solana pubkeys are base58 that decode to exactly 32 bytes. Decoding (not
    # just a length regex) is what reliably rejects Bitcoin base58 addresses,
    # which decode to ~25 bytes and would otherwise be accepted for an SVM leg.
    if not _SVM_ADDRESS_RE.match(a) or a.startswith(("bc1", "tb1")):
        return False
    if _base58 is not None:
        try:
            return len(_base58.b58decode(a)) == 32
        except Exception:
            return False
    # Fallback if base58 is unavailable: never accept something that also parses
    # as a Bitcoin address.
    return not _is_utxo_address(a)


_ADDRESS_VALIDATORS = {
    "EVM": _is_evm_address,
    "SVM": _is_svm_address,
    "UTXO": _is_utxo_address,
}


def _pick_address(explicit, ecosystem):
    """Return (address, is_real) for a chain leg.

    The caller-supplied address is used only when it is a valid address for
    *this leg's specific ecosystem* (so a real wallet enables an executable
    quote). Otherwise a valid per-ecosystem placeholder is returned and
    is_real is False — meaning the quote can only be used for pricing, never
    for execution (executing with a placeholder destination would send funds
    to an address the user does not control).
    """
    address = str(explicit or "").strip()
    validator = _ADDRESS_VALIDATORS[ecosystem]
    if address and validator(address):
        return address, True
    return ECOSYSTEM_PLACEHOLDER[ecosystem], False


def resolve_quote_addresses(intent):
    """Choose fromAddress/toAddress matching each leg's ecosystem.

    Accepts an intent that may carry `from_address`, `to_address`, and/or the
    legacy single `wallet`. Returns (from_address, to_address, from_is_real,
    to_is_real); a placeholder is substituted (is_real=False) when no valid
    address for that leg's ecosystem was supplied, so any-network-to-any-network
    quotes still *price* while only fully-addressed quotes are executable.
    """
    from_eco = chain_ecosystem(intent.get("from_chain_id"))
    to_eco = chain_ecosystem(intent.get("to_chain_id"))
    wallet = intent.get("wallet")
    explicit_from = intent.get("from_address") or wallet
    explicit_to = intent.get("to_address") or wallet
    from_address, from_real = _pick_address(explicit_from, from_eco)
    to_address, to_real = _pick_address(explicit_to, to_eco)
    return from_address, to_address, from_real, to_real


# LI.FI-verified default stablecoins per chain (used when the client sends
# generic aliases like "usdc"/"usdt" or omits a chain-specific contract).
CHAIN_DEFAULT_STABLE = {
    "1": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",  # Ethereum USDC
    "56": "0x55d398326f99059fF775485246999027B3197955",  # BSC USDT
    "137": "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359",  # Polygon USDC
    "8453": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",  # Base USDC
    "43114": "0xB97EF9Ef8734C71904D8002F8b6Bc66Dd9c48a6E",  # Avalanche USDC
    "1151111081099710": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",  # Solana USDC
}


def resolve_stable_token(chain_id, preferred="usdc"):
    """Return the default stablecoin address for a chain."""
    cid = str(chain_id or "").strip()
    if preferred.lower() == "usdt" and cid == "56":
        return CHAIN_DEFAULT_STABLE["56"]
    return CHAIN_DEFAULT_STABLE.get(cid) or CHAIN_DEFAULT_STABLE.get("1")


def normalize_token_input(token, chain_id=None):
    token = str(token or "").strip()
    lowered = token.lower()
    is_native = lowered in {"native", "eth", "bnb", "matic", "avax", "sol", "btc"}
    if is_native:
        ecosystem = chain_ecosystem(chain_id) if chain_id is not None else "EVM"
        if ecosystem == "SVM":
            return "11111111111111111111111111111111"
        if ecosystem == "UTXO":
            return "bitcoin"
        return "0x0000000000000000000000000000000000000000"
    if lowered in {"usdc", "usdt", "stable", "stablecoin"}:
        if chain_id is not None:
            resolved = resolve_stable_token(chain_id, preferred=lowered)
            if resolved:
                return resolved
    return token


def fetch_token(chain_id, token, api_key=None, timeout=20):
    params = {"chain": str(chain_id), "token": normalize_token_input(token, chain_id)}
    return _lifi_get("/token", params, api_key, timeout)


def summarize_token_info(token_data):
    """Return a compact, client-safe token descriptor from LI.FI /token."""
    if not isinstance(token_data, dict):
        return {}
    return {
        "address": token_data.get("address"),
        "symbol": token_data.get("symbol"),
        "name": token_data.get("name"),
        "decimals": token_data.get("decimals"),
        "logoURI": token_data.get("logoURI"),
        "priceUSD": token_data.get("priceUSD"),
        "chainId": token_data.get("chainId"),
    }


def fetch_token_price_usd(chain_id, token, api_key=None, timeout=20):
    """Return the live USD price of a token as a Decimal (LI.FI /token priceUSD)."""
    info = fetch_token(chain_id, token, api_key=api_key, timeout=timeout)
    price = info.get("priceUSD")
    if price in (None, ""):
        raise ValueError("priceUSD not available for this token")
    try:
        return Decimal(str(price))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError("Invalid priceUSD value") from exc


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
    if (
        str(intent["from_chain_id"]) == str(intent["to_chain_id"])
        and str(from_token.get("address") or "").lower() == str(to_token.get("address") or "").lower()
    ):
        raise SwapError("Source and destination are the same token. Pick two different tokens.", 400)
    from_amount_raw = decimal_amount_to_raw(intent["amount"], from_token["decimals"])
    order = "FASTEST" if intent.get("preference") == "fastest" else "CHEAPEST"
    from_address, to_address, from_real, to_real = resolve_quote_addresses(intent)
    params = {
        "fromChain": str(intent["from_chain_id"]),
        "toChain": str(intent["to_chain_id"]),
        "fromToken": from_token["address"],
        "toToken": to_token["address"],
        "fromAmount": from_amount_raw,
        "fromAddress": from_address,
        "toAddress": to_address,
        "slippage": str(intent.get("slippage") or 0.005),
        "order": order,
        # Enable true multi-leg routing: allow mid-route chain switches and
        # multi-step (chained) swaps so any asset can convert to any other
        # (e.g. BTC -> ETH) in a single quote. We intentionally do NOT pass
        # allowBridges=[] or otherwise force single-hop, so LI.FI keeps the
        # cheapest/fastest route across all bridges and DEXs.
        "allowSwitchChain": "true",
    }
    quote = _lifi_get("/quote", params, api_key, timeout)
    quote["_fromTokenInfo"] = from_token
    quote["_toTokenInfo"] = to_token
    # A quote is only executable when BOTH legs used a real, ecosystem-matched
    # address. With any placeholder in play the returned transactionRequest
    # would send funds to an address the user does not control, so it must be
    # treated as pricing-only by callers.
    quote["_executable"] = bool(from_real and to_real)
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
    # Only expose signable transaction fields when the quote was built with real
    # source AND destination addresses. Default True so any other caller of this
    # helper keeps its previous behaviour; quote_lifi always sets the flag.
    executable = bool(quote.get("_executable", True))
    summary = {
        "tool": quote.get("toolDetails", {}).get("name") or quote.get("tool") or "LI.FI",
        "from_symbol": from_token.get("symbol") or "from token",
        "to_symbol": to_token.get("symbol") or "to token",
        "to_amount": to_amount,
        "to_min": to_min,
        "gas_usd": format(gas_usd, "f"),
        "fee_usd": format(fee_usd, "f"),
        "duration": duration,
        "executable": executable,
        "approval_needed": approval_needed if executable else False,
        "approval_address": approval_address if executable else None,
        "tx_to": tx.get("to") if executable else None,
        "tx_value": tx.get("value") if executable else None,
        "tx_data": tx.get("data") if executable else None,
        "chain_id": tx.get("chainId") if executable else None,
    }
    if not executable:
        summary["pricing_only"] = True
        summary["execution_note"] = (
            "Price estimate only. Provide a wallet address for both the source "
            "and destination networks to get an executable swap."
        )
    return summary


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


CHAIN_ID_TO_NETWORK = {
    "1": "ethereum",
    "56": "bsc",
    "137": "polygon",
    "43114": "avalanche",
    "8453": "base",
    "42161": "arbitrum",
    "10": "optimism",
    "1151111081099710": "solana",
}


def lifi_chain_to_network(chain):
    """Map a LI.FI chain descriptor to an internal network key, if known."""
    if not chain:
        return None
    cid = str(chain.get("id"))
    if cid in CHAIN_ID_TO_NETWORK:
        return CHAIN_ID_TO_NETWORK[cid]
    chain_type = str(chain.get("chainType") or "").upper()
    key = str(chain.get("key") or "").lower()
    if chain_type == "SVM" or key == "sol":
        return "solana"
    if chain_type == "EVM":
        return None
    return None


def chain_rpc_url(chain):
    metamask = (chain or {}).get("metamask") or {}
    urls = metamask.get("rpcUrls") or []
    return urls[0] if urls else None


def chain_explorer_url(chain):
    metamask = (chain or {}).get("metamask") or {}
    urls = metamask.get("blockExplorerUrls") or []
    base = urls[0] if urls else ""
    if base and not base.endswith("/"):
        base = f"{base}/"
    return base


def execute_lifi_swap(intent, private_key, from_chain, api_key=None):
    """Sign and broadcast a LI.FI swap entirely on the server (in-bot style)."""
    import time

    from crypto_manager import (
        get_wallet_address,
        send_raw_evm_transaction,
        send_raw_solana_transaction,
    )

    from_chain_id = str(intent.get("from_chain_id"))
    chain_type = str((from_chain or {}).get("chainType") or "").upper()
    if chain_ecosystem(from_chain_id) == "UTXO":
        raise SwapError(
            "Bitcoin source swaps are not supported in-site yet. Choose an EVM or Solana source network.",
            400,
        )

    network = lifi_chain_to_network(from_chain)
    rpc_url = chain_rpc_url(from_chain)
    addr_network = network or ("solana" if chain_type == "SVM" else "ethereum")
    signer = get_wallet_address(addr_network, private_key)

    exec_intent = dict(intent)
    exec_intent["from_address"] = signer
    exec_intent["wallet"] = signer

    quote = quote_lifi(exec_intent, api_key=api_key)
    summary = summarize_quote(quote)
    if not summary.get("executable"):
        raise SwapError(
            "Enter a valid receiving address on the destination network to execute this swap.",
            400,
        )

    if summary.get("approval_needed"):
        action = quote.get("action") or {}
        from_token = action.get("fromToken") or {}
        approval = fetch_lifi_approval(
            from_chain_id,
            from_token.get("address"),
            action.get("fromAmount"),
            api_key=api_key,
        )
        if chain_type != "SVM" and from_chain_id != "1151111081099710":
            send_raw_evm_transaction(
                network,
                private_key,
                approval["to"],
                approval["data"],
                rpc_url=rpc_url,
            )
            time.sleep(15)

    tx = quote.get("transactionRequest") or {}
    if chain_type == "SVM" or from_chain_id == "1151111081099710":
        tx_hash = send_raw_solana_transaction(private_key, tx.get("data"), rpc_url=rpc_url)
    elif chain_type == "EVM" or network is None:
        if not rpc_url and not network:
            raise SwapError("This EVM network is not supported for in-site swaps yet.", 400)
        tx_hash = send_raw_evm_transaction(
            network,
            private_key,
            tx["to"],
            tx["data"],
            value=tx.get("value", 0),
            rpc_url=rpc_url,
        )
    else:
        raise SwapError("This source network is not supported for in-site swaps.", 400)

    explorer = chain_explorer_url(from_chain)
    return {
        "tx_hash": tx_hash,
        "summary": summary,
        "explorer_url": f"{explorer}{tx_hash}" if explorer else None,
    }
