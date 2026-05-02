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

from config import SOLANA_KEY

SOLANA_RPC = "https://api.mainnet-beta.solana.com"
USDC_MINT = Pubkey.from_string("EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v")
USDC_DECIMALS = 6


def rpc(method, params):
    response = requests.post(
        SOLANA_RPC,
        json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params},
        timeout=30,
    ).json()
    if "error" in response:
        raise RuntimeError(response["error"])
    return response.get("result")


def get_ata(wallet_str, mint_str):
    result = rpc("getTokenAccountsByOwner", [wallet_str, {"mint": mint_str}, {"encoding": "jsonParsed"}])
    accounts = result.get("value", []) if result else []
    return accounts[0]["pubkey"] if accounts else None


def send_usdc(dest_wallet_str, usdc_amount):
    if not SOLANA_KEY:
        raise RuntimeError("SOLANA_KEY is not configured")

    private_key_bytes = base58.b58decode(SOLANA_KEY)
    keypair = Keypair.from_bytes(private_key_bytes)
    admin_pub = keypair.pubkey()
    dest_pub = Pubkey.from_string(dest_wallet_str)

    admin_ata_str = get_ata(str(admin_pub), str(USDC_MINT))
    if not admin_ata_str:
        raise RuntimeError("Admin wallet has no USDC account!")

    admin_ata = Pubkey.from_string(admin_ata_str)
    dest_ata = get_associated_token_address(dest_pub, USDC_MINT)
    dest_ata_str = get_ata(dest_wallet_str, str(USDC_MINT))
    blockhash_resp = rpc("getLatestBlockhash", [{"commitment": "confirmed"}])
    recent_blockhash = Hash.from_string(blockhash_resp["value"]["blockhash"])

    instructions = []
    if not dest_ata_str:
        instructions.append(create_associated_token_account(payer=admin_pub, owner=dest_pub, mint=USDC_MINT))

    amount_raw = int(usdc_amount * 10**USDC_DECIMALS)
    instructions.append(
        transfer_checked(
            TransferCheckedParams(
                program_id=TOKEN_PROGRAM_ID,
                source=admin_ata,
                mint=USDC_MINT,
                dest=dest_ata,
                owner=admin_pub,
                amount=amount_raw,
                decimals=USDC_DECIMALS,
                signers=[],
            )
        )
    )

    msg = Message.new_with_blockhash(instructions, admin_pub, recent_blockhash)
    tx = Transaction([keypair], msg, recent_blockhash)
    result = requests.post(
        SOLANA_RPC,
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "sendTransaction",
            "params": [
                base64.b64encode(bytes(tx)).decode(),
                {"encoding": "base64", "preflightCommitment": "confirmed"},
            ],
        },
        timeout=30,
    ).json()
    if "error" in result:
        raise RuntimeError(result["error"])
    return result["result"]
