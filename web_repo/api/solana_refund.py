import base64

import base58
import requests
from solders.hash import Hash
from solders.keypair import Keypair
from solders.message import Message
from solders.pubkey import Pubkey
from solders.transaction import Transaction


SOLANA_RPC = "https://api.mainnet-beta.solana.com"
LAMPORTS_PER_SOL = 1_000_000_000
MAX_CLOSE_INSTRUCTIONS = 8


def _rpc(method, params):
    response = requests.post(
        SOLANA_RPC,
        json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params},
        timeout=30,
    ).json()
    if "error" in response:
        raise RuntimeError(response["error"])
    return response.get("result")


def _keypair(private_key):
    return Keypair.from_bytes(base58.b58decode(private_key))


def _token_accounts(owner):
    result = _rpc(
        "getTokenAccountsByOwner",
        [str(owner), {"programId": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"}, {"encoding": "jsonParsed"}],
    )
    return result.get("value", []) if result else []


def find_refundable_atas(private_key):
    from spl.token.instructions import get_associated_token_address

    owner = _keypair(private_key).pubkey()
    refundable = []
    non_empty_count = 0
    non_ata_count = 0
    accounts = _token_accounts(owner)
    for item in accounts:
        pubkey = item.get("pubkey")
        account = item.get("account") or {}
        parsed = ((account.get("data") or {}).get("parsed") or {}).get("info") or {}
        mint = parsed.get("mint")
        token_amount = (parsed.get("tokenAmount") or {}).get("amount")
        if not pubkey or not mint:
            continue
        if str(token_amount) != "0":
            non_empty_count += 1
            continue
        ata = get_associated_token_address(owner, Pubkey.from_string(mint))
        if str(ata) != pubkey:
            non_ata_count += 1
            continue
        lamports = int(account.get("lamports") or 0)
        if lamports <= 0:
            continue
        refundable.append({"pubkey": pubkey, "mint": mint, "lamports": lamports, "sol": lamports / LAMPORTS_PER_SOL})
    total_lamports = sum(item["lamports"] for item in refundable)
    return {
        "wallet": str(owner),
        "token_account_count": len(accounts),
        "refundable": refundable,
        "refundable_count": len(refundable),
        "total_lamports": total_lamports,
        "total_sol": total_lamports / LAMPORTS_PER_SOL,
        "non_empty_count": non_empty_count,
        "non_ata_count": non_ata_count,
    }


def close_refundable_atas(private_key):
    from spl.token.constants import TOKEN_PROGRAM_ID
    from spl.token.instructions import CloseAccountParams, close_account

    keypair = _keypair(private_key)
    owner = keypair.pubkey()
    summary = find_refundable_atas(private_key)
    accounts = summary["refundable"]
    signatures = []
    for start in range(0, len(accounts), MAX_CLOSE_INSTRUCTIONS):
        batch = accounts[start : start + MAX_CLOSE_INSTRUCTIONS]
        blockhash_resp = _rpc("getLatestBlockhash", [{"commitment": "confirmed"}])
        recent_blockhash = Hash.from_string(blockhash_resp["value"]["blockhash"])
        instructions = [
            close_account(
                CloseAccountParams(
                    program_id=TOKEN_PROGRAM_ID,
                    account=Pubkey.from_string(item["pubkey"]),
                    dest=owner,
                    owner=owner,
                    signers=[],
                )
            )
            for item in batch
        ]
        msg = Message.new_with_blockhash(instructions, owner, recent_blockhash)
        tx = Transaction([keypair], msg, recent_blockhash)
        result = _rpc(
            "sendTransaction",
            [base64.b64encode(bytes(tx)).decode(), {"encoding": "base64", "preflightCommitment": "confirmed"}],
        )
        signatures.append(result)
    summary["signatures"] = signatures
    return summary
