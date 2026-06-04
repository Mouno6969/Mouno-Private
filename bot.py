import asyncio
import json
import logging
import math
import os
import re
import secrets
import string
import tempfile
import threading
import unicodedata
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from io import BytesIO

import requests
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice, Update
from telegram.constants import ChatAction
from telegram.ext import (
    Application,
    BaseUpdateProcessor,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    PreCheckoutQueryHandler,
    filters,
)
from telegram.request import HTTPXRequest

try:
    from telethon import TelegramClient
    from telethon.errors import FloodWaitError, SessionPasswordNeededError
    from telethon.sessions import StringSession
    from telethon import utils as telethon_utils
except Exception:
    TelegramClient = None
    FloodWaitError = None
    SessionPasswordNeededError = None
    StringSession = None
    telethon_utils = None


def is_command_update(update):
    message = getattr(update, "effective_message", None)
    text = getattr(message, "text", None)
    return isinstance(text, str) and text.lstrip().startswith("/")


class ChatScopedUpdateProcessor(BaseUpdateProcessor):
    def __init__(self, max_concurrent_updates=8):
        super().__init__(max_concurrent_updates)
        self._locks = {}

    async def do_process_update(self, update, coroutine):
        if is_command_update(update):
            await coroutine
            return

        chat = getattr(update, "effective_chat", None)
        user = getattr(update, "effective_user", None)
        key = (getattr(chat, "id", None), getattr(user, "id", None))
        if key == (None, None):
            key = ("global", "global")
        entry = self._locks.setdefault(key, {"lock": asyncio.Lock(), "active": 0})
        entry["active"] += 1
        try:
            async with entry["lock"]:
                await coroutine
        finally:
            entry["active"] -= 1
            if entry["active"] <= 0:
                self._locks.pop(key, None)

    async def initialize(self):
        pass

    async def shutdown(self):
        self._locks.clear()

from balance import GAS_META, check_sufficient, get_all_balances, get_native_gas_balances
from bsc_sender import send_bsc_usdt
from config import (
    ADMIN_ID,
    AI_PROVIDER_ORDER,
    BACKUP_UPLOAD_URL,
    CEREBRAS_API_KEY,
    CEREBRAS_MODEL,
    BKASH_NUMBER,
    BOT_TOKEN,
    COHERE_API_KEY,
    COHERE_MODEL,
    GEMINI_API_KEY,
    GEMINI_MODEL,
    GROQ_API_KEY,
    GROQ_MODEL,
    HUGGINGFACE_API_KEY,
    HUGGINGFACE_MODEL,
    LOW_BALANCE_THRESHOLD,
    LIFI_API_KEY,
    MISTRAL_API_KEY,
    MISTRAL_MODEL,
    NVIDIA_DEEPSEEK_API_KEY,
    NVIDIA_DEEPSEEK_MODEL,
    NVIDIA_GEMMA_API_KEY,
    NVIDIA_GEMMA_MODEL,
    NVIDIA_KIMI_API_KEY,
    NVIDIA_KIMI_MODEL,
    NVIDIA_LLAMA4_SCOUT_API_KEY,
    NVIDIA_LLAMA4_SCOUT_MODEL,
    NVIDIA_LLAMA_8B_API_KEY,
    NVIDIA_LLAMA_8B_MODEL,
    NVIDIA_MISTRAL_SMALL_API_KEY,
    NVIDIA_MISTRAL_SMALL_MODEL,
    NVIDIA_NEMOTRON_NANO_API_KEY,
    NVIDIA_NEMOTRON_NANO_MODEL,
    NVIDIA_QWEN_7B_API_KEY,
    NVIDIA_QWEN_7B_MODEL,
    OPENROUTER_API_KEY,
    OPENROUTER_MODEL,
    RATE,
    RELAY_API_KEY,
    SCB_FORWARDER_APP_URL,
    SCB_FORWARDER_SERVER_URL,
    SELLER_WALLET_MASTER_KEY,
    SOCKET_API_KEY,
    STAR_RATE,
    SUPPORT_USERNAME,
    TELEGRAM_AUTH_BASE_URL,
    WEBHOOK_STALE_MINUTES,
)
from crypto_manager import (
    delete_user_wallet,
    decrypt_key,
    decrypt_seller_key,
    encrypt_key,
    encrypt_seller_key,
    get_user_balance,
    get_user_wallet,
    get_user_evm_wallet,
    get_user_solana_wallet,
    get_wallet_address,
    save_user_wallet,
    send_from_seller_wallet,
    send_from_user_wallet,
    send_with_private_key,
    send_raw_evm_transaction,
    send_raw_solana_transaction,
)
from db import (
    claim_giveaway_code,
    create_code,
    add_audit,
    bind_stock_reservation_trx,
    consume_stock_reservation,
    create_giveaway_codes,
    create_giveaway_session,
    create_stock_reservation,
    delete_pending_order,
    disable_code,
    get_all_active_codes,
    get_code,
    get_giveaway_session,
    get_network_rate,
    get_active_reserved_amount,
    get_all_cost_rates,
    get_pending_order,
    get_pending_orders,
    get_recent_transactions,
    get_sms,
    get_star_order,
    get_failed_transactions,
    get_setting,
    get_report_stats,
    get_seller_status,
    get_seller_public_stats,
    get_users_paged,
    get_all_users_for_export,
    get_user_analytics,
    get_profit_summary,
    get_webhook_health,
    find_order,
    create_payout_request,
    get_payout_request,
    list_payout_requests,
    list_audit,
    list_seller_profiles,
    list_stock_reservations,
    get_transaction,
    get_transaction_stats,
    get_user_language,
    get_wallet,
    mark_sms_used,
    release_stock_reservation,
    save_pending_order,
    save_sms,
    save_transaction,
    save_user_info,
    save_wallet,
    set_user_language,
    set_network_rate,
    set_cost_rate,
    set_setting,
    record_ai_provider_result,
    list_ai_provider_stats,
    sms_exists,
    trx_exists,
    save_star_order,
    set_seller_status,
    touch_webhook_notice,
    update_payout_request,
    update_transaction,
    update_star_order_status,
    use_code,
    approve_seller,
    bind_referral,
    create_or_update_seller_application,
    create_referral_withdrawal,
    create_seller_order,
    create_seller_star_ledger,
    credit_referral_reward,
    complete_referral_withdrawal,
    fail_referral_withdrawal,
    disable_seller,
    disable_seller_wallet,
    find_waiting_seller_order_by_trx,
    get_completed_seller_order_by_trx,
    get_seller,
    get_seller_by_sms_token,
    get_seller_order,
    get_seller_order_by_trx,
    get_seller_payment_notice,
    get_seller_payment_notice_owner,
    get_seller_rate,
    get_or_create_referral_code,
    get_referrer_for_user,
    list_approved_sellers,
    list_enabled_seller_wallets,
    list_pending_seller_orders,
    list_pending_seller_payouts,
    list_referral_ledger,
    list_seller_rates,
    list_seller_star_ledger,
    list_seller_wallets,
    list_sellers_by_status,
    mark_seller_payment_notice_used,
    mark_seller_payout_status,
    mark_referral_withdrawal,
    referral_admin_stats,
    referral_balance,
    referral_stats,
    reserve_referral_withdrawal,
    reject_seller,
    save_seller_payment_notice,
    save_seller_wallet,
    set_seller_rate,
    update_seller_order,
)
from evm_sender import send_evm_token
from polygon_sender import send_polygon_usdc
from sender import send_usdc
from solana_refund import close_refundable_atas, find_refundable_atas
from swap_service import (
    build_lifi_widget_url,
    chain_label,
    fallback_chains,
    find_chain,
    get_lifi_chains,
    quote_lifi,
    short_tx_data,
    summarize_quote,
    fetch_lifi_approval,
    get_lifi_status,
)


def lifi_chain_to_network(chain):
    if not chain:
        return None
    cid = str(chain.get("id"))
    mapping = {
        "1": "ethereum",
        "56": "bsc",
        "137": "polygon",
        "43114": "avalanche",
        "8453": "base",
        "1151111081099710": "solana",
    }
    if cid in mapping:
        return mapping[cid]
    chain_type = str(chain.get("chainType") or "").upper()
    if chain_type == "SVM" or str(chain.get("key")) == "sol":
        return "solana"
    return None
from ton_sender import send_ton
from tron_sender import send_trc20_usdt
from user_guide import GUIDE, NETWORK_GUIDE
from webhook import parse_bkash_payment_notice, parse_bkash_sms, run_webhook, set_callback
from personal_auth import (
    PERSONAL_FORWARD_CONNECTIONS,
    create_personal_auth_session,
    personal_auth_available,
    set_personal_auth_runtime,
)

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[logging.FileHandler("bot.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

WAITING_WALLET = 1
WAITING_AMOUNT = 2
WAITING_RATE = 4
SETUP_NETWORK = 10
SETUP_KEY = 11
SETUP_PASSWORD = 12
SEND_W_DEST = 13
SEND_W_AMOUNT = 14
SEND_W_PASSWORD = 15
DEL_PASSWORD = 17
GEN_CUSTOM_AMOUNT = 20
GEN_CUSTOM_DURATION = 21
WAITING_STAR_WALLET = 30
WAITING_STAR_AMOUNT = 31
ADMIN_SEND_WALLET = 40
ADMIN_SEND_AMOUNT = 41
AI_SUPPORT = 50
SELLER_APP_NAME = 60
SELLER_APP_BKASH = 61
SELLER_APP_SUPPORT = 62
SELLER_SETUP_KEY = 63
SELLER_SET_RATE = 64
SELLER_BUY_WALLET = 65
SELLER_BUY_AMOUNT = 66
FREE_FORWARD_MAX_TARGETS = 25
FREE_FORWARD_MIN_INTERVAL_MINUTES = 1
PERSONAL_FORWARD_MAX_TARGETS = 45
PERSONAL_FORWARD_MIN_INTERVAL_MINUTES = 15
PERSONAL_FORWARD_TARGET_DELAY_SECONDS = 3
PERSONAL_FORWARD_DIALOG_PAGE_SIZE = 8
PERSONAL_FORWARD_DIALOG_FETCH_LIMIT = 200

RATE_FILE = "rate.json"
DIVIDER = "────────────────"
RECEIPT_LOGO_PATH = os.path.join(os.path.dirname(__file__), "assets", "mouno_logo.jpg")
RECEIPT_FONT_DIR = os.path.join(os.path.dirname(__file__), "assets", "fonts")
WELCOME_VIDEO_PATH = os.path.join(os.path.dirname(__file__), "assets", "welcome_video.mp4")
TELEGRAM_VIDEO_CAPTION_LIMIT = 1024
FREE_FORWARD_CONNECTIONS = {}
FREE_FORWARD_TASKS = {}
PERSONAL_FORWARD_PENDING = {}
SWAP_CHAIN_PAGE_SIZE = 8

NETWORKS = {
    "solana": {"name": "Solana (SOL)", "symbol": "USDC", "explorer": "https://solscan.io/tx/"},
    "polygon": {"name": "Polygon USDC", "symbol": "USDC", "explorer": "https://polygonscan.com/tx/"},
    "bsc": {"name": "BSC USDT (BEP20)", "symbol": "USDT", "explorer": "https://bscscan.com/tx/"},
    "avalanche": {"name": "Avalanche USDT", "symbol": "USDT", "explorer": "https://snowtrace.io/tx/"},
    "ethereum": {"name": "Ethereum USDT (ERC20)", "symbol": "USDT", "explorer": "https://etherscan.io/tx/"},
    "ethereum_usdc": {"name": "Ethereum USDC (ERC20)", "symbol": "USDC", "explorer": "https://etherscan.io/tx/"},
    "base": {"name": "Base USDC", "symbol": "USDC", "explorer": "https://basescan.org/tx/"},
    "trc20": {"name": "Tron USDT (TRC20)", "symbol": "USDT", "explorer": "https://tronscan.org/#/transaction/"},
    "ton": {"name": "TON", "symbol": "TON", "explorer": "https://tonviewer.com/transaction/"},
}

LANGUAGES = {
    "bn": "বাংলা",
    "en": "English",
}

TEXT = {
    "choose_language": {
        "bn": "🌐 ভাষা নির্বাচন করুন\n\nআপনার পছন্দের ভাষা বেছে নিন।",
        "en": "🌐 Choose your language\n\nSelect the language you prefer.",
    },
    "language_saved": {"bn": "✅ ভাষা সেট করা হয়েছে।", "en": "✅ Language saved."},
    "buy": {"bn": "💱 কিনুন", "en": "💱 Buy"},
    "swap": {"bn": "🔁 Swap/Bridge", "en": "🔁 Swap/Bridge"},
    "gift": {"bn": "🎁 গিফট কোড", "en": "🎁 Gift Code"},
    "giveaway": {"bn": "🎉 Giveaway", "en": "🎉 Giveaway"},
    "stars": {"bn": "⭐ Telegram Stars", "en": "⭐ Telegram Stars"},
    "rate": {"bn": "📊 রেট", "en": "📊 Rates"},
    "balance": {"bn": "💰 ব্যালেন্স", "en": "💰 Balance"},
    "txlog": {"bn": "📜 TX লগ", "en": "📜 TX Log"},
    "help": {"bn": "❓ সাহায্য", "en": "❓ Help"},
    "support": {"bn": "📞 Support", "en": "📞 Support"},
    "ai_support": {"bn": "🤖 AI Support", "en": "🤖 AI Support"},
    "faq": {"bn": "FAQ", "en": "FAQ"},
    "free_service": {"bn": "🆓 ফ্রী সার্ভিস", "en": "🆓 Free Service"},
    "sellers": {"bn": "🛍️ Sellers", "en": "🛍️ Sellers"},
    "seller_center": {"bn": "🏪 Seller Center", "en": "🏪 Seller Center"},
    "order_status": {"bn": "🔎 Order Status", "en": "🔎 Order Status"},
    "seller_dashboard": {"bn": "🏪 Seller Dashboard", "en": "🏪 Seller Dashboard"},
    "referral": {"bn": "👥 Referral", "en": "👥 Referral"},
    "terms": {"bn": "📜 Terms", "en": "📜 Terms"},
    "wallet": {"bn": "🔐 আমার Wallet", "en": "🔐 My Wallet"},
    "language": {"bn": "🌐 ভাষা", "en": "🌐 Language"},
    "set_rate": {"bn": "⚙️ রেট পরিবর্তন", "en": "⚙️ Set Rates"},
    "gen_code": {"bn": "🎟️ কোড তৈরি", "en": "🎟️ Generate Code"},
    "disable_code": {"bn": "🚫 কোড বাতিল", "en": "🚫 Disable Code"},
    "admin_send": {"bn": "🚀 Admin Send", "en": "🚀 Admin Send"},
    "swap_setup": {"bn": "🔁 Swap API Setup", "en": "🔁 Swap API Setup"},
    "back": {"bn": "🔙 ফিরে যান", "en": "🔙 Back"},
    "cancel": {"bn": "❌ বাতিল", "en": "❌ Cancel"},
    "home_title": {"bn": "Smart Crypto Buy", "en": "Smart Crypto Buy"},
    "welcome": {"bn": "স্বাগতম", "en": "Welcome"},
    "current_rates": {"bn": "বর্তমান রেট", "en": "Current rates"},
    "select_action": {"bn": "নিচের মেনু থেকে একটি অপশন বেছে নিন।", "en": "Select an option from the menu."},
    "select_network": {"bn": "💱 নেটওয়ার্ক বেছে নিন", "en": "💱 Select a network"},
    "enter_wallet": {"bn": "আপনার {network} Wallet Address দিন", "en": "Enter your {network} wallet address"},
    "example": {"bn": "উদাহরণ", "en": "Example"},
    "wallet_saved": {"bn": "✅ Wallet সংরক্ষিত!", "en": "✅ Wallet saved!"},
    "enter_amount_bdt": {"bn": "কত টাকার {symbol} কিনতে চান?", "en": "How much {symbol} do you want to buy in BDT?"},
    "numbers_only": {"bn": "শুধু সংখ্যা লিখুন (যেমন: 500)", "en": "Enter numbers only (example: 500)"},
    "invalid_wallet": {"bn": "❌ ভুল wallet address!", "en": "❌ Invalid wallet address!"},
    "invalid_amount": {"bn": "❌ ভুল পরিমাণ! সংখ্যা লিখুন।", "en": "❌ Invalid amount. Send a number."},
    "confirm": {"bn": "✅ কনফার্ম", "en": "✅ Confirm"},
    "order_summary": {"bn": "📊 অর্ডার সারসংক্ষেপ", "en": "📊 Order Summary"},
    "send_bdt": {"bn": "পাঠাবেন", "en": "You pay"},
    "receive_crypto": {"bn": "পাবেন", "en": "You receive"},
    "confirm_prompt": {"bn": "নিশ্চিত করতে Confirm চাপুন 👇", "en": "Tap Confirm to continue 👇"},
    "code_select_network": {"bn": "🎟️ গিফট কোড তৈরি\n\n১/৩: নেটওয়ার্ক বেছে নিন", "en": "🎟️ Generate Gift Code\n\nStep 1/3: Select network"},
    "code_select_amount": {"bn": "২/৩: কত {symbol} এর কোড তৈরি করবেন?", "en": "Step 2/3: Choose {symbol} amount"},
    "code_select_duration": {"bn": "৩/৩: কোডের মেয়াদ বেছে নিন", "en": "Step 3/3: Choose expiry time"},
    "custom_amount": {"bn": "✏️ Custom Amount", "en": "✏️ Custom Amount"},
    "custom_duration": {"bn": "✏️ Custom Time", "en": "✏️ Custom Time"},
    "enter_custom_amount": {"bn": "পরিমাণ লিখুন। যেমন: 1.5", "en": "Send the amount. Example: 1.5"},
    "enter_custom_duration": {"bn": "মিনিট লিখুন। যেমন: 60", "en": "Send minutes. Example: 60"},
    "code_created": {"bn": "✅ গিফট কোড তৈরি হয়েছে!", "en": "✅ Gift code generated!"},
    "stars_intro": {"bn": "⭐ Telegram Stars দিয়ে কিনুন\n\nনেটওয়ার্ক বেছে নিন।", "en": "⭐ Pay with Telegram Stars\n\nSelect a network."},
    "stars_enter_amount": {"bn": "কত {symbol} কিনতে চান?\n\nRate: 1 {symbol} = {rate} Stars", "en": "How many {symbol} do you want to buy?\n\nRate: 1 {symbol} = {rate} Stars"},
    "stars_invoice_title": {"bn": "Crypto Order", "en": "Crypto Order"},
    "stars_invoice_description": {"bn": "{amount} {symbol} on {network}", "en": "{amount} {symbol} on {network}"},
    "stars_pay_prompt": {"bn": "Invoice পাঠানো হয়েছে। Telegram Stars দিয়ে payment complete করুন।", "en": "Invoice sent. Complete payment with Telegram Stars."},
    "stars_paid_sending": {"bn": "✅ Stars payment received. Crypto পাঠানো হচ্ছে...", "en": "✅ Stars payment received. Sending crypto..."},
    "stars_completed": {"bn": "🎉 Stars payment verified এবং crypto পাঠানো হয়েছে!", "en": "🎉 Stars payment verified and crypto sent!"},
    "admin_send_intro": {"bn": "🚀 Admin Send\n\nকোন network থেকে asset পাঠাবেন?", "en": "🚀 Admin Send\n\nSelect the network to send from."},
    "admin_send_wallet": {"bn": "Destination wallet address দিন", "en": "Send destination wallet address"},
    "admin_send_amount": {"bn": "কত {symbol} পাঠাবেন?", "en": "Enter the {symbol} amount to send."},
    "admin_send_confirm": {"bn": "নিশ্চিত করলে asset পাঠানো হবে।", "en": "Confirm to send the asset."},
    "admin_send_done": {"bn": "✅ Admin transfer complete!", "en": "✅ Admin transfer complete!"},
    "maintenance_on": {"bn": "🛑 Maintenance mode ON", "en": "🛑 Maintenance mode ON"},
    "maintenance_off": {"bn": "✅ Maintenance mode OFF", "en": "✅ Maintenance mode OFF"},
    "ai_support_intro": {"bn": "🤖 AI Support\n\nআপনার প্রশ্ন লিখুন। Payment, wallet, network, bKash, Stars বা order problem সম্পর্কে সাহায্য করতে পারি।\n\nOrder চেক: /order ORD-XXXXXX বা /status TRXID\nবন্ধ করতে /cancel লিখুন।", "en": "🤖 AI Support\n\nSend your question. I can help with payment, wallet, network, bKash, Stars, or order issues.\n\nCheck order: /order ORD-XXXXXX or /status TRXID\nSend /cancel to close."},
    "ai_unavailable": {"bn": "❌ AI Support এখন unavailable. Admin-কে জানান।", "en": "❌ AI Support is unavailable. Please contact admin."},
    "ai_thinking": {"bn": "🤖 উত্তর তৈরি করছি...", "en": "🤖 Thinking..."},
    "user_analytics": {"bn": "📊 User Analytics", "en": "📊 User Analytics"},
    "enter_user_id_analytics": {"bn": "বিশ্লেষণের জন্য User ID দিন:", "en": "Enter User ID for analytics:"},
    "user_not_found": {"bn": "❌ ব্যবহারকারী পাওয়া যায়নি।", "en": "❌ User not found."},
}


def is_admin(user_id) -> bool:
    return str(user_id) == str(ADMIN_ID)


def is_maintenance_enabled():
    return get_setting("maintenance_mode", "off") == "on"


def maintenance_message(lang="bn"):
    if lang == "en":
        return "🛑 Orders are temporarily paused for maintenance. Please try again later."
    return "🛑 Maintenance চলছে। অর্ডার সাময়িকভাবে বন্ধ আছে। কিছুক্ষণ পর চেষ্টা করুন।"


def gas_warning(network, lang="bn"):
    native = {
        "solana": "SOL",
        "polygon": "MATIC/POL",
        "bsc": "BNB",
        "avalanche": "AVAX",
        "ethereum": "ETH",
        "ethereum_usdc": "ETH",
        "base": "ETH",
        "trc20": "TRX",
        "ton": "TON",
    }.get(network, "native gas")
    if lang == "en":
        return f"⚠️ Make sure the sender wallet has enough {native} for network gas/fees. Wrong network transfers cannot be reversed."
    return f"⚠️ Sender wallet-এ gas/fee এর জন্য পর্যাপ্ত {native} থাকতে হবে। ভুল network transfer ফেরত আনা যায় না।"


def failure_reason_text(error, network=None, lang="bn"):
    text = str(error or "").lower()
    network_text = str(network or "").lower()
    gas_words = ["gas", "fee", "bnb", "sol", "trx", "eth", "matic", "pol", "avax", "ton", "native"]
    if any(word in text for word in ["not configured", "missing", "env", "api key", "private key", "mnemonic", "rpc not set"]):
        en = "Likely sender/API/RPC configuration is missing. Admin should check environment keys, RPC URL, and sender wallet setup before retrying."
        bn = "সম্ভবত sender/API/RPC configuration missing. Retry করার আগে admin-এর env key, RPC URL এবং sender wallet setup চেক করা উচিত।"
    elif any(word in text for word in gas_words) or network_text in {"bsc", "solana", "trc20", "ethereum", "ethereum_usdc", "polygon", "avalanche", "base", "ton"} and any(word in text for word in ["fund", "funds", "pay", "transaction underpriced"]):
        en = "Likely insufficient native gas/chain fee at send time. Check the sender wallet's native gas token and retry only after topping up."
        bn = "সম্ভবত send করার সময় native gas/chain fee কম ছিল। Sender wallet-এর native gas token top up করে তারপর retry করুন।"
    elif any(word in text for word in ["insufficient", "অপর্যাপ্ত", "stock", "balance", "not enough"]):
        en = "Likely insufficient token stock/balance. Admin should check available stock and reserved amounts before retrying."
        bn = "সম্ভবত token stock/balance পর্যাপ্ত নেই। Retry করার আগে admin-এর available stock ও reserved amount চেক করা উচিত।"
    elif any(word in text for word in ["rpc", "timeout", "timed out", "connection", "network", "temporarily", "503", "502", "504"]):
        en = "Likely temporary RPC/network issue. Check RPC health/explorer and retry after confirming the payment and no duplicate send occurred."
        bn = "সম্ভবত temporary RPC/network issue. Payment confirm এবং duplicate send হয়নি নিশ্চিত করে RPC/explorer চেক করে retry করুন।"
    elif any(word in text for word in ["invalid", "address", "wallet", "checksum", "wrong network"]):
        en = "Likely invalid wallet address or network mismatch. Confirm the destination wallet matches the selected network before retrying."
        bn = "সম্ভবত wallet address ভুল বা network mismatch. Retry করার আগে destination wallet নির্বাচিত network-এর কিনা নিশ্চিত করুন।"
    elif any(word in text for word in ["receipt.status != 1", "reverted", "transaction failed", "execution reverted", "revert"]):
        en = "The chain likely rejected/reverted the transaction. Check explorer, gas, token contract, and wallet state before retrying."
        bn = "সম্ভবত chain transaction reject/revert করেছে। Retry করার আগে explorer, gas, token contract এবং wallet state চেক করুন।"
    elif any(word in text for word in ["payment verification mismatch", "amount mismatch", "user mismatch", "invoice", "stars payment verification"]):
        en = "Likely payment amount/user mismatch. Admin should verify the bKash/Stars receipt, exact amount, payer/order, and TrxID manually."
        bn = "সম্ভবত payment amount/user mismatch. Admin-এর bKash/Stars receipt, exact amount, payer/order এবং TrxID manually verify করা উচিত।"
    elif any(word in text for word in ["duplicate", "already used", "trxid"]):
        en = "Likely duplicate or incorrect TrxID. Check whether the TrxID was already used or typed incorrectly."
        bn = "সম্ভবত duplicate বা ভুল TrxID. TrxID আগে ব্যবহার হয়েছে কিনা বা ভুল টাইপ হয়েছে কিনা চেক করুন।"
    elif any(word in text for word in ["seller not approved", "seller wallet", "not enabled"]):
        en = "Likely seller setup issue. The assigned seller may need approval, an enabled delivery wallet, stock, and gas."
        bn = "সম্ভবত seller setup issue. Assigned seller-এর approval, enabled delivery wallet, stock এবং gas দরকার হতে পারে।"
    else:
        en = "Exact cause is unknown. Admin should check /failed, /audit, bot logs, balances, gas, payment receipt, and retry only after verifying no duplicate send happened."
        bn = "নির্দিষ্ট কারণ অজানা। Admin-এর /failed, /audit, bot logs, balances, gas, payment receipt চেক করে duplicate send হয়নি নিশ্চিত করে retry করা উচিত।"
    return en if lang == "en" else bn


def terms_text(lang="bn"):
    if lang == "en":
        return (
            "📜 Terms & Risk Warning\n\n"
            "• Always choose the correct network.\n"
            "• Wrong wallet/network transfers cannot be reversed.\n"
            "• Keep enough native gas token for wallet sends.\n"
            "• Payments may require manual review if bKash/notification data is delayed or mismatched.\n"
            "• Contact support if a payment is stuck."
        )
    return (
        "📜 Terms & Risk Warning\n\n"
        "• সবসময় সঠিক network বেছে নিন।\n"
        "• ভুল wallet/network transfer ফেরত আনা যায় না।\n"
        "• নিজের wallet থেকে পাঠাতে native gas token থাকতে হবে।\n"
        "• bKash/SMS/notification delay বা mismatch হলে manual review লাগতে পারে।\n"
        "• Payment stuck হলে support-এ যোগাযোগ করুন।"
    )


BOT_KNOWLEDGE_BASE = """
SCB-Forwarder and Telegram bot knowledge base for AI Support:
- Identity and scope: SCB-Forwarder is the Android app used with this Telegram crypto buy/sell/support bot. The bot handles orders, payments, crypto delivery, sellers, referrals, wallet tools, and support; SCB-Forwarder forwards trusted bKash SMS/app-notification payment notices from Android phones to the bot server. AI Support is read-only: it explains app/bot features, crypto/network/wallet/gas basics, payment/order problems, guides users step-by-step, interprets sanitized order context, and suggests the safest next action. It cannot approve payments, change balances/rates, send crypto, access wallets, verify a payment without bot/admin evidence, give investment advice, or guarantee token prices/profit.
- Language behavior: answer in Bengali when the user's question is Bengali/Bangla, answer in English when the user's question is English, and only use another language if the user explicitly asks. Keep command names, network names, TrxID/order IDs, wallet addresses, and support usernames unchanged.
- Main menu: Buy, Telegram Stars, Gift Code, Giveaway, Swap/Bridge, Rates, My Wallet, Balance, TX Log, Order Status, Referral, Sellers, Seller Center, Seller Dashboard, AI Support, FAQ, Support, Terms, and Language. Admins also see rate/code/send/report/backup/health/restart/reservation/profit/gas/audit/seller/AI/payout/test/maintenance tools.
- Normal user commands: /start opens home/language, /help lists commands, /guide shows the full user guide, /terms shows risk warnings, /ai opens AI Support, /order ORD-XXXXXX checks an order ID, /status TRXID_OR_ORDERID checks a TrxID/order, /receipt ORD_OR_TRX shows a completed receipt, /seller USER_ID shows seller profile/stats, /seller_center opens seller tools/application, /seller_dashboard opens seller dashboard, /seller_guide explains seller setup, /referral shows referral link/balance, /setup connects an encrypted personal wallet, /changekey replaces saved wallet key, /deletekey deletes saved wallet key, /mybalance checks personal wallet balance, /send_wallet sends from personal wallet, and /payout starts eligible payout/withdraw flow.
- Admin commands, never expose sensitive internals to normal users: /send, /gencode, /pending, /failed, /stats, /balances, /maintenance, /backup, /report, /profit, /costrate, /gas, /reservations, /audit, /payouts, /webhook_health, /bot_health, /restart_help, /test_sms, /test_seller_sms, /seller_badge, /aiadmin, /ai_usage. Web dashboard exists only when admin web access is configured.
- Language, help, FAQ, terms: first-time users choose Bengali or English and the preference is stored; later messages can update the saved language when clearly Bengali/English. /help lists typed commands, /guide explains wallet/order/security usage, FAQ answers common buy/pending/Stars/help questions, and Terms warns about wrong networks, irreversible transfers, gas, and manual review.
- Supported buyer assets/networks: Solana USDC, Polygon USDC, BSC USDT BEP20, Avalanche USDT, Ethereum USDT ERC20, Ethereum USDC ERC20, Base USDC, Tron USDT TRC20, and TON. Wallet formats: Solana addresses are usually 32-44 chars, TRC20 starts with T and is 34 chars, TON starts with UQ or EQ, and EVM networks use 0x 42-char addresses. Wrong network/wallet transfers cannot be reversed.
- Rates and buy amounts: Rates shows the current BDT price for each network/asset. Buy amounts are entered in BDT for bKash and converted by the selected network rate; Telegram Stars uses the Stars rate. Users must pay the exact shown amount and submit the correct TrxID/order identifier.
- Gas/native fee rules: sending tokens needs native gas even when token balance exists. Solana uses SOL, Polygon uses MATIC/POL, BSC uses BNB, Avalanche uses AVAX, Ethereum uses ETH, Base uses ETH, Tron uses TRX/Energy/Bandwidth, and TON uses TON. Low gas can cause delivery or personal-wallet sends to fail.
- Buy with bKash flow: user taps Buy, selects network, enters receiving wallet, enters BDT amount, reviews summary, confirms, pays the exact bKash amount to the shown bKash number, submits TrxID, then the bot matches the TrxID with SMS/app-notification/webhook data and sends crypto automatically when verified. User should save Order ID and TrxID.
- SCB-Forwarder Android app: install it on the Android phone that receives bKash SMS or official bKash app notifications. The app has a fixed server URL shown in the UI, supports main/admin mode and seller mode, saves only the selected mode and token on the phone, and posts notices to the bot. Setup steps: save the correct admin/seller token, tap Check server, allow SMS permission, enable Notification Access for SCB-Forwarder, start the background service, keep the persistent SCB-Forwarder running notification visible, and disable battery/autostart restrictions.
- SCB-Forwarder reliability/status: it forwards trusted bKash SMS senders (bKash/16247) and known official bKash app packages, can parse matching notices on the phone while offline, queues notices if internet/server is unavailable, retries queued uploads automatically, and has a Retry queued notices now button. Status screen shows successful forwards, failed/queued attempts, last forwarded time, last SMS/notification source, queue count, and last error. Forwarding both SMS and notification is safe because the bot deduplicates by TrxID.
- SCB-Forwarder setup troubleshooting by step: if setup is stuck at token save, ask whether the phone is in Seller mode or main/admin mode and whether the correct Seller token/Admin token was pasted. If Check server fails, ask for the three displayed lines: Internet, Server reachable, Token, plus Details. Internet FAILED means fix phone internet/VPN/DNS first; Server reachable FAILED means check network/server availability and the fixed server shown in the app; Token FAILED usually means wrong mode or wrong/old token, so copy the token again from Seller Center or ask admin for the correct admin token. If SMS permission fails, open Android app settings and allow SMS/notification permissions manually. If Notification Access fails, open Android Notification access settings and enable SCB-Forwarder. If background service will not stay running, start it again, keep the persistent notification visible, disable battery optimization, allow autostart/auto launch/background activity, and lock the app in recent apps if the phone supports it.
- SCB-Forwarder forwarding/error troubleshooting: when a user reports any SCB-Forwarder error, first ask for the exact screen/step, phone brand/model, selected mode, Check server result, Status screen values (Forwarded count, Failed/queued attempts, Last source, Last phone event, Queue count, Last error message), Payment outcome if shown, whether SMS permission and Notification Access are enabled, and whether the SCB-Forwarder running notification is visible. Then explain likely causes: Not ready means token not saved; Save the required token first means setup incomplete; No active internet connection means phone internet is down; HTTP 401/403 or Token FAILED means wrong token/mode; HTTP 404 means server endpoint/app-server version mismatch; timeout/connection errors mean internet/server/firewall issue; Queue count above 0 means notices are saved locally and need internet/server retry; Last source none means no supported bKash SMS/notification has been captured yet; ignored means the forwarded text was not a supported payment notice; parsed means payment was read but no matching waiting order existed yet; duplicate means TrxID was already recorded; manual_review means admin/seller must verify; matched_order means server matched and processed the order.
- Free Service forwarding: Free Service is a user-facing bot menu with a Telegram Message Forwarder button. Inside Telegram Message Forwarder, a user can connect either their own @BotFather Telegram bot token or their own personal Telegram account session and send the same message to approved Telegram groups/channels. It supports numeric chat IDs such as -1001234567890, @usernames, and public t.me/telegram.me links as targets; private invite links are not accepted. Bot-token mode requires the connected bot to already be added to every target and may need admin permission to post in channels or restricted groups. Personal-account mode requires the user's own Telegram API ID/API hash/phone/login code through the secure web login link, never inside Telegram chat, stores the session only in bot memory, is limited to explicit allowlisted targets where the account is already a member and has permission/consent to post, and uses lower target/interval limits to reduce spam/account risk. Flow: tap Free Service, tap Telegram Message Forwarder, connect Telegram token or Connect personal account, open the secure web login link for personal account login, choose Forward with bot token or Forward with personal account, choose One-time forward or Forward repeatedly, then either select targets from the connected account's group/channel list or enter target IDs/usernames/links manually; for repeated forwarding enter the interval in minutes, then send the message to forward. Telegram API ID/API hash source: go to https://my.telegram.org, log in with the same Telegram phone number, open API development tools, create an app if needed, then copy api_id and api_hash. Target/group ID source: for personal-account mode the built-in group/channel picker can show private groups/channels where the connected account is already a member; public group/channel targets can also use @username or public t.me link; private group/channel manual targets need a numeric chat ID copied from a trusted Telegram ID bot, admin tool, or your own bot update/log after the bot/account is added; supergroup/channel IDs usually start with -100. Supported message types include text, photo, video, document, audio, voice, animation, and sticker. Users can stop scheduled forwarding with Stop scheduled forward and remove the connected token/session with Disconnect. If sending fails, likely causes are invalid token/session, bot/account not in the target, missing post permission, private/invalid link, blocked bot/account, or Telegram rate limits. AI Support must explain these steps in Bengali for Bengali questions and English for English questions. AI Support must also explain these steps and benefits, including where to get API ID/API hash and target group/chat ID, and must discourage spam or forwarding to groups without permission.
- Free Service Solana ATA Refund: Free Service also has a Solana ATA Refund button. It lets a user connect their own Solana wallet for this refund flow, checks empty Associated Token Accounts (ATAs), shows how much rent SOL is estimated to be refundable, and after confirmation closes only empty ATA accounts so the rent SOL returns to the same wallet. ATAs with token balances must be skipped and never auto-closed. Explain that Solana network fee applies, signatures may be returned, and the user should only connect their own wallet. AI Support must explain the Solana ATA refund steps in Bengali for Bengali questions and English for English questions.
- Free Service Telegram ID Finder: Free Service also has a Telegram ID Finder button. It helps users find Telegram user/account, group, supergroup, or channel IDs by sending a public @username, public t.me/telegram.me link, numeric chat ID, or a forwarded message from the target. If used in a group/channel where the bot can read messages, it can show the current chat ID. Public usernames/links are resolved with bot access; private chats/channels usually require bot access or a forwarded message with visible origin. If Telegram hides the forward sender because of privacy settings, AI Support must explain that the hidden ID cannot be revealed by the bot. AI Support must explain Telegram ID Finder steps in Bengali for Bengali questions and English for English questions.
- Swap/Bridge: the bot integrates LI.FI for cross-chain swaps and bridges between EVM chains (Ethereum, BSC, Polygon, Avalanche, Base, Arbitrum, Optimism, etc.) and SVM (Solana). Users can start a swap from the "Swap/Bridge" menu, select source and destination chains/tokens, enter amount, and get a quote. The "In-Bot Swap" flow allows users to execute swaps directly by signing with their connected "Personal Wallet" (private key required). Solana native token address '11111111111111111111111111111111' is supported. Users can also swap on the jumper.exchange website via an external link. AI Support should explain these steps and benefits in Bengali for Bengali questions and English for English questions.
- bKash automation details: webhook/SCB-Forwarder accepts trusted bKash SMS and bKash app notifications. Supported payment text must include amount with Tk/BDT/৳ and TrxID/TxnID/Transaction ID. If SMS and app notification both arrive for one TrxID, duplicate protection processes only the first. One TrxID cannot complete more than one transaction.
- Pending/manual bKash cases: pending can happen when SMS/notification has not reached the server, user submitted TrxID before notice arrived, amount does not match, TrxID is wrong/duplicate/already used, payer/order does not match, selected wallet/network is invalid, stock is low, gas is low, or RPC/network is busy. User action: check /order or /status, wait if webhook is delayed, and contact support with Order ID + TrxID. Admin action: verify via /pending before approving/rejecting.
- Order status and receipts: /order or /status can check order ID/TrxID. Normal users can only see their own orders; admins can inspect all. Completed orders support /receipt. Receipts include proof/explorer URL or compact receipt details and QR when available. Never tell a user an order is paid/completed unless context says verified/completed.
- Telegram Stars flow: user taps Telegram Stars, selects network, enters wallet, enters crypto amount, receives a Telegram invoice, pays in XTR Stars, bot verifies payload/order ID, Telegram user ID, currency XTR, and exact Stars amount, then sends crypto. STAR_RATE means how many Stars equal 1 USDC/USDT/asset, with optional per-network overrides. If paid Stars delivery fails, bot marks failed and notifies admin; admin may manually send crypto or refund using Telegram tools.
- Gift Code and Giveaway: admins can create one-time gift codes with network, amount, and expiry; admins can disable active codes. Users redeem a gift code with a destination wallet, and a used/expired/invalid code cannot be reused. Giveaways create a session with network, recipient count, base amount, expiry, codes, and optional early-claimer bonus. Admin giveaways use bot/admin stock; non-admin giveaways are funded by the user's connected wallet and require the wallet password. User wallet-funded TON giveaways are not supported. Claimers must use a valid unused giveaway code before expiry.
- Personal wallet: /setup lets a user connect an encrypted wallet key (private key only; seed phrases/mnemonics are not supported) for supported networks, then use /mybalance and /send_wallet with password protection. /changekey replaces the saved key and /deletekey removes it. /send_wallet asks destination, amount, password, and confirmation; wrong password, insufficient token balance, insufficient gas, invalid wallet, or RPC errors can fail the send. The bot cannot recover a forgotten password. Never ask for or reveal private keys, seed phrases, mnemonics, or wallet passwords; support/admin should never ask for them either.
- Seller marketplace: approved sellers appear under Sellers. Buyers can use seller bKash or Stars routes where available. Sellers apply from Seller Center, submit display name, seller bKash number, and support contact, then wait for admin approval. Approved sellers configure encrypted delivery wallets, rates, stock, and dashboard tools. Sellers/admins handle assigned pending seller orders. Seller Stars ledger and payout review exist. TON seller auto-delivery is not supported; seller auto-delivery supports Solana, Polygon, BSC, Avalanche, Ethereum, Base, and TRC20.
- Referral and payouts: /referral gives a personal code/link, referral count, ledger, balance, total earned/withdrawn, and minimum withdrawal. Referral rewards may be OFF; users can still share links but rewards/withdrawals only work when admin enables them. Eligible completed orders can credit referrals. Referral withdraw asks payout method/details and creates a request for admin review. Admin can enable/disable referral, set reward percent, set minimum withdrawal, and review payout requests.
- Rates, balances, stock, reservations: Admin can set network sale rates and cost rates. Balance/stock checks account for active reservations, so available stock can be lower than raw wallet balance. Confirmed buyer/Stars orders reserve stock until completed, rejected, cancelled, failed, or expired. Low stock or low gas warnings mean orders may fail or need admin top-up.
- TX Log, receipts, and failed sends: TX Log shows user-visible transaction history and order IDs. Completed orders support receipt text/image with explorer proof/QR when available. Failed delivery can be caused by low stock, low native gas, RPC timeout, invalid wallet/network, chain revert, missing sender/API/RPC config, duplicate TrxID, or seller setup issue. Admin should check /failed, /audit, /balances, /gas, payment receipt, explorer, and retry only after confirming no duplicate send happened.
- Admin operations and health: /stats shows totals, completed/failed/pending counts, retry queue, sales/crypto totals, profit, and maintenance. /report and /profit show daily/weekly sales/profit and margin; /costrate sets cost rates. /gas monitors native gas. /reservations shows active stock reservations. /audit shows admin/system events. /backup sends the database backup to admin and daily backup/report can run near local midnight. /restart_help gives safe Termux restart steps but does not restart the bot itself. /test_sms and /test_seller_sms inject fake TEST TrxIDs for testing only.
- Maintenance, webhook, dashboard, AI admin: maintenance mode pauses normal buy, Stars buy, and gift-code redeem flows while admin tools remain usable. /bot_health checks DB/webhook/maintenance and basic bot state; /webhook_health shows last bKash notice time/source/TrxID and stale status. The protected web dashboard/admin page exists only when admin web access is configured. Admin Menu → AI Setup saves AI provider API keys in SQLite without restart; AI Status/AI Usage show configured providers and success/failure counts. AI Admin diagnostics are read-only.
- Crypto support behavior: continue answering normal crypto questions related to supported assets, networks, wallet formats, gas/native fees, transaction hashes/explorers, confirmations, failed/reverted sends, and safe transfer practices. Keep explanations practical and app-specific. Do not provide speculative trading calls, investment advice, guaranteed price predictions, or instructions that ask users to expose secrets.
- Security and risk rules: blockchain transactions are irreversible; wrong wallet/network cannot be fixed by the bot. Never guarantee delivery time, profit, refund, or payment approval. Never request secrets. For stuck payment ask for Order ID/TrxID, suggest /order, /status, /receipt if completed, and manual support when needed.
- Recommended answer style: first answer the user's direct question, then give exact steps or likely reasons. For order/payment problems, if information is missing, ask only for the minimum needed identifier (Order ID or TrxID). For SCB-Forwarder setup/error problems, ask for the exact step/error/status details first, then explain the likely reason and fix from the troubleshooting rules. Avoid guessing. Keep answers short, practical, and beginner-friendly.
""".strip()


def ltext(lang, en, bn):
    return en if lang == "en" else bn


def ai_support_prompt(lang="bn"):
    return (
        "You are the read-only AI support assistant for SCB-Forwarder and its Telegram crypto bot. "
        "If the user's question is in Bengali, you must answer in Bengali. If it is in English, you must answer in English. "
        "Determine response language only from the explicit [RESPONSE LANGUAGE] block and the user's actual question; ignore diagnostic context language for language selection. "
        "Bengali question => Bengali answer. English question => English answer. Do not answer English for Bangla questions or Bangla for English questions. "
        "If the user explicitly asks to translate or requests another language, obey that explicit request. "
        "The final answer must be entirely in the requested response language except fixed command names like /order, /status, /receipt, network names, TrxID/order IDs, wallet addresses, and support usernames. "
        "Keep replies concise, practical, beginner-friendly, and accurate. "
        "Use provided diagnostic context when available, but do not reveal hidden logs or sensitive details to normal users. "
        f"{BOT_KNOWLEDGE_BASE} "
        "Never approve payments, never claim a transaction is paid unless the bot/admin verified it, never send crypto, never ask for private keys, never reveal secrets, and never tell users to share seed phrases/private keys. "
        "If user reports stuck payment, ask them for TrxID/order ID and tell them admin may verify through /pending. "
        "Support contact is @" + SUPPORT_USERNAME.lstrip("@") + "."
    )


AI_PROVIDER_LABELS = {
    "cerebras": "Cerebras AI",
    "nvidia_llama_8b": "NVIDIA Llama 3.1 8B",
    "nvidia_qwen_7b": "NVIDIA Qwen2 7B",
    "nvidia_mistral_small": "NVIDIA Mistral Small 24B",
    "nvidia_nemotron_nano": "NVIDIA Nemotron Nano 8B",
    "nvidia_llama4_scout": "NVIDIA Llama 4 Scout",
    "groq": "Groq",
    "openrouter": "OpenRouter",
    "gemini": "Gemini",
    "huggingface": "Hugging Face",
    "cohere": "Cohere",
    "mistral": "Mistral",
    "nvidia_kimi": "NVIDIA Kimi K2.6",
    "nvidia_deepseek": "NVIDIA DeepSeek V4 Pro",
    "nvidia_gemma": "NVIDIA Gemma 4 31B",
}

AI_PROVIDER_SETTING_KEYS = {
    "cerebras": "ai_cerebras_api_key",
    "nvidia_llama_8b": "ai_nvidia_llama_8b_api_key",
    "nvidia_qwen_7b": "ai_nvidia_qwen_7b_api_key",
    "nvidia_mistral_small": "ai_nvidia_mistral_small_api_key",
    "nvidia_nemotron_nano": "ai_nvidia_nemotron_nano_api_key",
    "nvidia_llama4_scout": "ai_nvidia_llama4_scout_api_key",
    "groq": "ai_groq_api_key",
    "openrouter": "ai_openrouter_api_key",
    "gemini": "ai_gemini_api_key",
    "huggingface": "ai_huggingface_api_key",
    "cohere": "ai_cohere_api_key",
    "mistral": "ai_mistral_api_key",
    "nvidia_kimi": "ai_nvidia_kimi_api_key",
    "nvidia_deepseek": "ai_nvidia_deepseek_api_key",
    "nvidia_gemma": "ai_nvidia_gemma_api_key",
}

FAST_NVIDIA_PROVIDER_ORDER = ["cerebras", "nvidia_llama_8b", "nvidia_qwen_7b", "nvidia_mistral_small", "nvidia_nemotron_nano", "nvidia_llama4_scout"]
STANDARD_PROVIDER_ORDER = ["groq", "openrouter", "gemini", "huggingface", "cohere", "mistral"]
SLOW_NVIDIA_PROVIDER_ORDER = ["nvidia_kimi", "nvidia_deepseek", "nvidia_gemma"]


def _clean_ai_key(value):
    value = str(value or "").strip()
    return value or None


def ai_provider_order():
    known_order = SLOW_NVIDIA_PROVIDER_ORDER + STANDARD_PROVIDER_ORDER + FAST_NVIDIA_PROVIDER_ORDER
    order = ["cerebras", "groq", "gemini"]
    for provider in AI_PROVIDER_ORDER.split(","):
        provider = provider.strip().lower()
        if provider in AI_PROVIDER_LABELS and provider not in order:
            order.append(provider)
    for provider in known_order:
        if provider in AI_PROVIDER_LABELS and provider not in order:
            order.append(provider)
    return order


def ai_provider_env_keys():
    return {
        "cerebras": CEREBRAS_API_KEY,
        "nvidia_llama_8b": NVIDIA_LLAMA_8B_API_KEY,
        "nvidia_qwen_7b": NVIDIA_QWEN_7B_API_KEY,
        "nvidia_mistral_small": NVIDIA_MISTRAL_SMALL_API_KEY,
        "nvidia_nemotron_nano": NVIDIA_NEMOTRON_NANO_API_KEY,
        "nvidia_llama4_scout": NVIDIA_LLAMA4_SCOUT_API_KEY,
        "groq": GROQ_API_KEY,
        "openrouter": OPENROUTER_API_KEY,
        "gemini": GEMINI_API_KEY,
        "huggingface": HUGGINGFACE_API_KEY,
        "cohere": COHERE_API_KEY,
        "mistral": MISTRAL_API_KEY,
        "nvidia_kimi": NVIDIA_KIMI_API_KEY,
        "nvidia_deepseek": NVIDIA_DEEPSEEK_API_KEY,
        "nvidia_gemma": NVIDIA_GEMMA_API_KEY,
    }


def ai_provider_key_sources():
    env_keys = ai_provider_env_keys()
    sources = {}
    for provider, setting_key in AI_PROVIDER_SETTING_KEYS.items():
        db_key = _clean_ai_key(get_setting(setting_key))
        env_key = _clean_ai_key(env_keys.get(provider))
        if db_key:
            sources[provider] = (db_key, "bot")
        elif env_key:
            sources[provider] = (env_key, "env")
        else:
            sources[provider] = (None, None)
    return sources


def ai_provider_keys():
    return {provider: key for provider, (key, _source) in ai_provider_key_sources().items()}


def ai_provider_key(provider):
    return ai_provider_keys().get(provider)


def ai_provider_models():
    return {
        "cerebras": CEREBRAS_MODEL,
        "nvidia_llama_8b": NVIDIA_LLAMA_8B_MODEL,
        "nvidia_qwen_7b": NVIDIA_QWEN_7B_MODEL,
        "nvidia_mistral_small": NVIDIA_MISTRAL_SMALL_MODEL,
        "nvidia_nemotron_nano": NVIDIA_NEMOTRON_NANO_MODEL,
        "nvidia_llama4_scout": NVIDIA_LLAMA4_SCOUT_MODEL,
        "groq": GROQ_MODEL,
        "openrouter": OPENROUTER_MODEL,
        "gemini": GEMINI_MODEL,
        "huggingface": HUGGINGFACE_MODEL,
        "cohere": COHERE_MODEL,
        "mistral": MISTRAL_MODEL,
        "nvidia_kimi": NVIDIA_KIMI_MODEL,
        "nvidia_deepseek": NVIDIA_DEEPSEEK_MODEL,
        "nvidia_gemma": NVIDIA_GEMMA_MODEL,
    }


def configured_ai_providers():
    keys = ai_provider_keys()
    return [provider for provider in ai_provider_order() if keys.get(provider)]


def _safe_ai_error(exc):
    if isinstance(exc, requests.HTTPError) and exc.response is not None:
        return f"{type(exc).__name__} status={exc.response.status_code}"
    if isinstance(exc, requests.RequestException):
        return type(exc).__name__
    return type(exc).__name__


def record_ai_provider_result_safe(provider, success, error=None):
    try:
        record_ai_provider_result(provider, success, error)
    except Exception as exc:
        logger.warning("AI stats recording failed for %s: %s", provider, type(exc).__name__)


def _validate_ai_response_text(text):
    text = "" if text is None else str(text).strip()
    if not text or text.lower() in {"none", "null", "undefined", "nil", "[]", "{}"}:
        raise RuntimeError("Empty AI response returned")
    return text


def _extract_openai_chat_text(data):
    choices = data.get("choices", [])
    if not choices:
        raise RuntimeError("No AI response returned")
    content = choices[0].get("message", {}).get("content", "")
    if isinstance(content, list):
        text = "".join(part.get("text", "") for part in content if isinstance(part, dict))
    else:
        text = content
    return _validate_ai_response_text(text)


AI_USER_MESSAGE_LIMIT = 6000
AI_CONTEXT_LIMIT = 8000
AI_SUPPORT_HISTORY_TURNS = 12
AI_SUPPORT_HISTORY_LIMIT = 4000
AI_PROVIDER_TIMEOUT_SECONDS = 6
ORDER_AI_CALLBACK_PREFIX = "aiorder_"
TRACK_ORDER_CALLBACK_PREFIX = "trackorder_"


def sanitize_diagnostic_text(value):
    text = str(value or "")
    patterns = [
        r"(?i)(bot_token|api[_-]?key|private[_-]?key|secret|token|mnemonic|seed|password|authorization)\s*[:=]\s*\S+",
        r"\b\d{7,12}:[A-Za-z0-9_-]{20,}\b",
        r"\b(?:sk|pk|xox|ghp|glpat|hf|nvapi|AIza)[A-Za-z0-9_\-]{16,}\b",
        r"\b[A-Za-z0-9+/]{48,}={0,2}\b",
        r"0x[a-fA-F0-9]{64}\b",
    ]
    for pattern in patterns:
        text = re.sub(pattern, "[REDACTED]", text)
    return text[:1000]


def extract_support_identifiers(question):
    text = str(question or "")
    pattern = r"\b(?:ORD[-_][A-Z0-9]{4,}|STAR[-_][A-Z0-9_]{6,}|SO[-_][A-Z0-9_]{6,}|PAY[A-Z0-9_-]{4,}|TEST[A-Z0-9]{4,}|[A-Z0-9]{8,24})\b"
    found = []
    for match in re.findall(pattern, text.upper()):
        if match not in found:
            found.append(match)
    return found[:5]


def _order_context_line(identifier, user_id, admin=False):
    kind, row = find_order(identifier)
    if not row:
        seller_order = get_seller_order(identifier)
        if seller_order:
            order_id, seller_id, buyer_id, _buyer_username, method, trx_id, network, wallet, amount_bdt, amount_crypto, stars_amount, status, tx_sig, error, created, updated = seller_order
            if not admin and str(user_id) not in {str(buyer_id), str(seller_id)}:
                return f"{identifier}: permission denied; requester is not buyer/seller/admin."
            ni = NETWORKS.get(network, {"name": network, "symbol": "?"})
            reason = failure_reason_text(error, network, "en") if error else "No stored error."
            return sanitize_diagnostic_text(
                f"Seller order {order_id}: status={status}, seller={seller_id}, buyer={buyer_id}, method={method}, trx={trx_id or 'N/A'}, "
                f"network={ni['name']}, amount={amount_crypto} {ni['symbol']}, BDT={amount_bdt or 0}, stars={stars_amount or 0}, "
                f"wallet={short_wallet(wallet)}, tx={bool(tx_sig)}, error={error or 'none'}, created={created}, updated={updated}. Likely: {reason}"
            )
        return f"{identifier}: no matching order/TrxID found."
    if kind == "transaction":
        trx_id, bdt, crypto, network, wallet, status, created, order_id, owner_id, sig = row[:10]
        if not admin and str(owner_id) != str(user_id):
            return f"{identifier}: permission denied; requester is not the order owner."
        updated = row[10] if len(row) > 10 and row[10] else created
        ni = NETWORKS.get(network or "solana", {"name": network, "symbol": "?"})
        reason = failure_reason_text("transaction failed", network, "en") if status == "failed" else "No failure stored."
        return sanitize_diagnostic_text(
            f"Transaction order {order_id or 'N/A'} / TrxID {trx_id}: owner={owner_id}, status={status}, network={ni['name']}, "
            f"BDT={bdt}, amount={crypto} {ni['symbol']}, wallet={short_wallet(wallet)}, tx={bool(sig)}, created={created}, updated={updated}. {reason}"
        )
    if kind == "pending":
        trx_id, owner_id, bdt, crypto, wallet, network, created = row[:7]
        if not admin and str(owner_id) != str(user_id):
            return f"{identifier}: permission denied; requester is not the order owner."
        order_id = row[7] if len(row) > 7 else "N/A"
        updated = row[8] if len(row) > 8 else created
        sms = get_sms(trx_id)
        ni = NETWORKS.get(network or "solana", {"name": network, "symbol": "?"})
        reason = "bKash notice exists but order is pending/manual" if sms else "bKash notice missing/delayed, wrong TrxID, duplicate TrxID, or webhook/forwarder delay"
        return sanitize_diagnostic_text(
            f"Pending order {order_id} / TrxID {trx_id}: owner={owner_id}, network={ni['name']}, BDT={bdt}, amount={crypto} {ni['symbol']}, "
            f"wallet={short_wallet(wallet)}, created={created}, updated={updated}. Likely: {reason}."
        )
    order_id, owner_id, username, network, wallet, amount, stars, status, tg, prov, tx_sig, error, created, updated = row
    if not admin and str(owner_id) != str(user_id):
        return f"{identifier}: permission denied; requester is not the order owner."
    ni = NETWORKS.get(network or "solana", {"name": network, "symbol": "?"})
    reason = failure_reason_text(error or status, network, "en") if status == "failed" or error else "No failure stored."
    return sanitize_diagnostic_text(
        f"Stars order {order_id}: owner={owner_id}, username=@{username}, status={status}, network={ni['name']}, amount={amount} {ni['symbol']}, "
        f"stars={stars}, wallet={short_wallet(wallet)}, tg_charge={bool(tg)}, provider_charge={bool(prov)}, tx={bool(tx_sig)}, error={error or 'none'}, created={created}, updated={updated}. {reason}"
    )


def _audit_context_lines(limit=10):
    lines = []
    for _aid, actor, action, target_type, target_id, details, created in list_audit(limit):
        lines.append(sanitize_diagnostic_text(f"{str(created)[:19]} | actor={actor} | {action} | {target_type or '-'}:{target_id or '-'} | {details or ''}"))
    return lines


def _ai_provider_context_lines():
    lines = []
    stats = {row[0]: row for row in list_ai_provider_stats()}
    for provider in ai_provider_order():
        row = stats.get(provider)
        if not row:
            continue
        label = AI_PROVIDER_LABELS.get(provider, provider)
        lines.append(sanitize_diagnostic_text(f"{label}: ok={row[1]} fail={row[2]} last_ok={row[3] or '-'} last_fail={row[4] or '-'} last_error={row[5] or '-'}"))
    return lines


def _tail_file_lines(path, line_count=60):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as file:
            lines = file.readlines()[-line_count:]
        return [sanitize_diagnostic_text(line.rstrip()) for line in lines if line.strip()]
    except OSError:
        return []


def _bot_log_context_lines():
    paths = []
    for path in ("bot.log", os.path.join(os.path.dirname(__file__), "bot.log")):
        if path not in paths:
            paths.append(path)
    lines = []
    for path in paths:
        tail = _tail_file_lines(path, 60)
        if tail:
            lines.append(f"Log tail from {os.path.basename(path)}:")
            lines.extend(tail[-60:])
            break
    return lines


def normalize_order_context_identifier(identifier):
    value = re.sub(r"[^A-Za-z0-9_-]", "", str(identifier or "").strip())
    return value[:40]


def is_order_context_available(identifier, viewer_id):
    identifier = normalize_order_context_identifier(identifier)
    if not identifier:
        return False
    context_line = _order_context_line(identifier, viewer_id, admin=is_admin(viewer_id))
    return "permission denied" not in context_line and "no matching order/TrxID found" not in context_line


def build_ai_support_context(question, user_id, lang="bn", admin=False, order_identifiers=None):
    sections = ["AI SUPPORT CONTEXT (sanitized, read-only):"]
    identifiers = []
    for identifier in order_identifiers or []:
        normalized = normalize_order_context_identifier(identifier)
        if normalized and normalized not in identifiers:
            identifiers.append(normalized)
    for identifier in extract_support_identifiers(question):
        if identifier not in identifiers:
            identifiers.append(identifier)
    if identifiers:
        sections.append("Order/TrxID context:")
        for identifier in identifiers:
            sections.append("- " + _order_context_line(identifier, user_id, admin))
            if admin:
                sections.append("  Local failure explainer: " + sanitize_diagnostic_text(explain_order_failure(identifier)))
    if admin:
        audit = _audit_context_lines(10)
        if audit:
            sections.append("Recent audit:")
            sections.extend("- " + line for line in audit)
        provider = _ai_provider_context_lines()
        if provider:
            sections.append("AI provider usage:")
            sections.extend("- " + line for line in provider)
        logs = _bot_log_context_lines()
        if logs:
            sections.append("Recent bot log tail (sanitized):")
            sections.extend("- " + line for line in logs)
    if len(sections) == 1:
        return ""
    return "\n".join(sections)[:AI_CONTEXT_LIMIT]


def format_ai_support_history(history):
    lines = []
    for turn in list(history or [])[-AI_SUPPORT_HISTORY_TURNS:]:
        user = sanitize_diagnostic_text(str(turn.get("user", ""))).strip()
        assistant = sanitize_diagnostic_text(str(turn.get("assistant", ""))).strip()
        if user:
            lines.append("Previous user: " + user)
        if assistant:
            lines.append("Previous AI: " + assistant)
    if not lines:
        return ""
    return ("Conversation memory for this AI Support session only:\n" + "\n".join(lines))[:AI_SUPPORT_HISTORY_LIMIT]


def combine_ai_support_context(*parts):
    text = "\n\n".join(str(part).strip() for part in parts if str(part or "").strip())
    return text[:AI_CONTEXT_LIMIT]


def append_ai_support_history(user_data, question, answer):
    history = list(user_data.get("ai_support_history") or [])
    history.append({"user": str(question or "")[:1000], "assistant": str(answer or "")[:1000]})
    user_data["ai_support_history"] = history[-AI_SUPPORT_HISTORY_TURNS:]


def ai_order_status_question(identifier, lang="bn"):
    identifier = normalize_order_context_identifier(identifier)
    if lang == "en":
        return (
            f"Explain the current status of order {identifier} in simple English. "
            "Include the status, amount, network, wallet summary, likely reason if it is pending/failed/manual review, and what the user should do next. "
            "Keep it concise and easy for a beginner."
        )
    return (
        f"Order {identifier} এর current status সহজ বাংলায় বুঝিয়ে দিন। "
        "Status, amount, network, wallet summary, pending/failed/manual review হলে সম্ভাব্য কারণ, এবং user-এর next step লিখুন। "
        "নতুন user যেন সহজে বুঝতে পারে, সংক্ষেপে বলুন।"
    )


def select_ai_response_language(question, lang="bn"):
    question = str(question or "")
    bengali_chars = sum(1 for char in question if "\u0980" <= char <= "\u09FF")
    english_letters = sum(1 for char in question if ("a" <= char.lower() <= "z"))
    fallback_language = "English" if lang == "en" else "Bengali"
    if bengali_chars:
        if english_letters >= 24 and english_letters >= bengali_chars * 6:
            return "English"
        return "Bengali"
    if english_letters:
        letter_tokens = [token.strip("`'\".,!?()[]{}<>") for token in question.split() if any("a" <= char.lower() <= "z" for char in token)]
        if letter_tokens and all(any(char.isdigit() for char in token) or any(char in token for char in ":/-_.#@") for token in letter_tokens):
            return fallback_language
        return "English"
    return fallback_language


def compose_ai_user_message(question, context=None, lang="bn"):
    question = str(question or "")
    response_language = select_ai_response_language(question, lang)
    language_instruction = (
        f"[RESPONSE LANGUAGE]\n{response_language}\n\n"
        "[LANGUAGE RULE]\n"
        "Use only the language named in [RESPONSE LANGUAGE] for the final answer. "
        "Ignore diagnostic context language when choosing response language; use the actual user question and explicit language requests only. "
        "Exceptions allowed unchanged: fixed command names (/order, /status, /receipt), network names, TrxID/order IDs, wallet addresses, and support usernames.\n"
    )
    question_block = f"\n[USER QUESTION]\n{question}"
    if context:
        context_header = "\n[BEGIN DIAGNOSTIC CONTEXT]\n"
        context_footer = "\n[END DIAGNOSTIC CONTEXT]\n"
        available_context = AI_USER_MESSAGE_LIMIT - len(language_instruction) - len(context_header) - len(context_footer) - len(question_block)
        if available_context < 0:
            available_question = max(0, AI_USER_MESSAGE_LIMIT - len(language_instruction) - len("\n[USER QUESTION]\n"))
            return (language_instruction + f"\n[USER QUESTION]\n{question[:available_question]}")[:AI_USER_MESSAGE_LIMIT]
        return (language_instruction + context_header + str(context or "")[:available_context] + context_footer + question_block)[:AI_USER_MESSAGE_LIMIT]
    return (language_instruction + question_block)[:AI_USER_MESSAGE_LIMIT]


def _ask_gemini(question, lang="bn", timeout=AI_PROVIDER_TIMEOUT_SECONDS):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
    payload = {
        "systemInstruction": {"parts": [{"text": ai_support_prompt(lang)}]},
        "contents": [{"role": "user", "parts": [{"text": question[:AI_USER_MESSAGE_LIMIT]}]}],
        "generationConfig": {"temperature": 0.2, "maxOutputTokens": 850},
    }
    response = requests.post(url, params={"key": ai_provider_key("gemini")}, json=payload, timeout=timeout)
    response.raise_for_status()
    data = response.json()
    candidates = data.get("candidates", [])
    if not candidates:
        raise RuntimeError("No AI response returned")
    parts = candidates[0].get("content", {}).get("parts", [])
    text = "".join(part.get("text", "") for part in parts)
    return _validate_ai_response_text(text)


def _ask_openai_compatible(endpoint, api_key, model, question, lang="bn", extra_headers=None, extra_payload=None, timeout=AI_PROVIDER_TIMEOUT_SECONDS):
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    if extra_headers:
        headers.update(extra_headers)
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": ai_support_prompt(lang)},
            {"role": "user", "content": question[:AI_USER_MESSAGE_LIMIT]},
        ],
        "temperature": 0.2,
        "max_tokens": 850,
    }
    if extra_payload:
        payload.update(extra_payload)
    response = requests.post(endpoint, headers=headers, json=payload, timeout=timeout)
    response.raise_for_status()
    return _extract_openai_chat_text(response.json())


def _ask_cerebras(question, lang="bn", timeout=AI_PROVIDER_TIMEOUT_SECONDS):
    return _ask_openai_compatible(
        "https://api.cerebras.ai/v1/chat/completions",
        ai_provider_key("cerebras"),
        CEREBRAS_MODEL,
        question,
        lang,
        timeout=timeout,
    )


def _ask_groq(question, lang="bn", timeout=AI_PROVIDER_TIMEOUT_SECONDS):
    return _ask_openai_compatible(
        "https://api.groq.com/openai/v1/chat/completions",
        ai_provider_key("groq"),
        GROQ_MODEL,
        question,
        lang,
        timeout=timeout,
    )


def _ask_nvidia_llama_8b(question, lang="bn", timeout=AI_PROVIDER_TIMEOUT_SECONDS):
    return _ask_openai_compatible(
        "https://integrate.api.nvidia.com/v1/chat/completions",
        ai_provider_key("nvidia_llama_8b"),
        NVIDIA_LLAMA_8B_MODEL,
        question,
        lang,
        timeout=timeout,
    )


def _ask_nvidia_qwen_7b(question, lang="bn", timeout=AI_PROVIDER_TIMEOUT_SECONDS):
    return _ask_openai_compatible(
        "https://integrate.api.nvidia.com/v1/chat/completions",
        ai_provider_key("nvidia_qwen_7b"),
        NVIDIA_QWEN_7B_MODEL,
        question,
        lang,
        timeout=timeout,
    )


def _ask_nvidia_mistral_small(question, lang="bn", timeout=AI_PROVIDER_TIMEOUT_SECONDS):
    return _ask_openai_compatible(
        "https://integrate.api.nvidia.com/v1/chat/completions",
        ai_provider_key("nvidia_mistral_small"),
        NVIDIA_MISTRAL_SMALL_MODEL,
        question,
        lang,
        timeout=timeout,
    )


def _ask_nvidia_nemotron_nano(question, lang="bn", timeout=AI_PROVIDER_TIMEOUT_SECONDS):
    return _ask_openai_compatible(
        "https://integrate.api.nvidia.com/v1/chat/completions",
        ai_provider_key("nvidia_nemotron_nano"),
        NVIDIA_NEMOTRON_NANO_MODEL,
        question,
        lang,
        timeout=timeout,
    )


def _ask_nvidia_llama4_scout(question, lang="bn", timeout=AI_PROVIDER_TIMEOUT_SECONDS):
    return _ask_openai_compatible(
        "https://integrate.api.nvidia.com/v1/chat/completions",
        ai_provider_key("nvidia_llama4_scout"),
        NVIDIA_LLAMA4_SCOUT_MODEL,
        question,
        lang,
        timeout=timeout,
    )


def _ask_nvidia_deepseek(question, lang="bn", timeout=AI_PROVIDER_TIMEOUT_SECONDS):
    return _ask_openai_compatible(
        "https://integrate.api.nvidia.com/v1/chat/completions",
        ai_provider_key("nvidia_deepseek"),
        NVIDIA_DEEPSEEK_MODEL,
        question,
        lang,
        timeout=timeout,
    )


def _ask_nvidia_kimi(question, lang="bn", timeout=AI_PROVIDER_TIMEOUT_SECONDS):
    return _ask_openai_compatible(
        "https://integrate.api.nvidia.com/v1/chat/completions",
        ai_provider_key("nvidia_kimi"),
        NVIDIA_KIMI_MODEL,
        question,
        lang,
        extra_payload={"chat_template_kwargs": {"thinking": True}},
        timeout=timeout,
    )


def _ask_nvidia_gemma(question, lang="bn", timeout=AI_PROVIDER_TIMEOUT_SECONDS):
    return _ask_openai_compatible(
        "https://integrate.api.nvidia.com/v1/chat/completions",
        ai_provider_key("nvidia_gemma"),
        NVIDIA_GEMMA_MODEL,
        question,
        lang,
        timeout=timeout,
    )


def _ask_openrouter(question, lang="bn", timeout=AI_PROVIDER_TIMEOUT_SECONDS):
    return _ask_openai_compatible(
        "https://openrouter.ai/api/v1/chat/completions",
        ai_provider_key("openrouter"),
        OPENROUTER_MODEL,
        question,
        lang,
        {"HTTP-Referer": "https://t.me/", "X-Title": "Mouno Private Telegram Bot"},
        timeout=timeout,
    )


def _ask_huggingface(question, lang="bn", timeout=AI_PROVIDER_TIMEOUT_SECONDS):
    return _ask_openai_compatible(
        "https://router.huggingface.co/v1/chat/completions",
        ai_provider_key("huggingface"),
        HUGGINGFACE_MODEL,
        question,
        lang,
        timeout=timeout,
    )


def _ask_cohere(question, lang="bn", timeout=AI_PROVIDER_TIMEOUT_SECONDS):
    headers = {"Authorization": f"Bearer {ai_provider_key('cohere')}", "Content-Type": "application/json"}
    payload = {
        "model": COHERE_MODEL,
        "messages": [
            {"role": "system", "content": ai_support_prompt(lang)},
            {"role": "user", "content": question[:AI_USER_MESSAGE_LIMIT]},
        ],
        "temperature": 0.2,
        "max_tokens": 850,
    }
    response = requests.post("https://api.cohere.com/v2/chat", headers=headers, json=payload, timeout=timeout)
    response.raise_for_status()
    data = response.json()
    content = data.get("message", {}).get("content", [])
    text = "".join(part.get("text", "") for part in content if isinstance(part, dict))
    return _validate_ai_response_text(text)


def _ask_mistral(question, lang="bn", timeout=AI_PROVIDER_TIMEOUT_SECONDS):
    return _ask_openai_compatible(
        "https://api.mistral.ai/v1/chat/completions",
        ai_provider_key("mistral"),
        MISTRAL_MODEL,
        question,
        lang,
        timeout=timeout,
    )


def ask_ai_support(question, lang="bn", context=None):
    question = compose_ai_user_message(question, context, lang)
    providers = configured_ai_providers()
    if not providers:
        if not any(ai_provider_keys().values()):
            raise RuntimeError("No AI provider API key is configured")
        raise RuntimeError("No configured AI provider is enabled in AI_PROVIDER_ORDER")
    askers = {
        "cerebras": _ask_cerebras,
        "nvidia_llama_8b": _ask_nvidia_llama_8b,
        "nvidia_qwen_7b": _ask_nvidia_qwen_7b,
        "nvidia_mistral_small": _ask_nvidia_mistral_small,
        "nvidia_nemotron_nano": _ask_nvidia_nemotron_nano,
        "nvidia_llama4_scout": _ask_nvidia_llama4_scout,
        "groq": _ask_groq,
        "openrouter": _ask_openrouter,
        "gemini": _ask_gemini,
        "huggingface": _ask_huggingface,
        "cohere": _ask_cohere,
        "mistral": _ask_mistral,
        "nvidia_kimi": _ask_nvidia_kimi,
        "nvidia_deepseek": _ask_nvidia_deepseek,
        "nvidia_gemma": _ask_nvidia_gemma,
    }
    tried = []
    for provider in providers:
        tried.append(AI_PROVIDER_LABELS[provider])
        try:
            timeout = 4 if provider in FAST_NVIDIA_PROVIDER_ORDER else AI_PROVIDER_TIMEOUT_SECONDS
            answer = askers[provider](question, lang, timeout=timeout)
            record_ai_provider_result_safe(provider, True)
            return answer
        except Exception as exc:
            safe_error = _safe_ai_error(exc)
            record_ai_provider_result_safe(provider, False, safe_error)
            logger.warning("AI provider %s failed: %s", AI_PROVIDER_LABELS[provider], safe_error)
    raise RuntimeError("All configured AI providers failed: " + ", ".join(tried))


async def _send_ai_support_answer(bot, chat_id, user_id, question, lang, pending_token, user_data):
    typing_task = None

    async def _keep_typing():
        try:
            while True:
                await bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
                await asyncio.sleep(4)
        except asyncio.CancelledError:
            pass
        except Exception:
            pass

    try:
        typing_task = asyncio.create_task(_keep_typing())
        order_identifier = user_data.get("ai_order_context_identifier")
        memory_context = format_ai_support_history(user_data.get("ai_support_history"))
        diagnostic_context = build_ai_support_context(question, user_id, lang, admin=is_admin(user_id), order_identifiers=[order_identifier] if order_identifier else None)
        loop = asyncio.get_running_loop()
        answer = await loop.run_in_executor(
            None,
            lambda: ask_ai_support(
                question,
                lang,
                combine_ai_support_context(memory_context, diagnostic_context),
            ),
        )
    except Exception as exc:
        logger.error("AI support failed: %s", exc)
        answer = tr("ai_unavailable", lang)
    finally:
        if typing_task:
            typing_task.cancel()
    try:
        if user_data.get("ai_support") and user_data.get("ai_support_pending") == pending_token:
            await bot.send_message(chat_id=chat_id, text=answer)
            append_ai_support_history(user_data, question, answer)
    except Exception as exc:
        logger.error("AI support answer send failed: %s", exc)
    finally:
        if user_data.get("ai_support_pending") == pending_token:
            user_data.pop("ai_support_pending", None)


def ai_status_lines():
    sources = ai_provider_key_sources()
    models = ai_provider_models()
    lines = []
    for provider in AI_PROVIDER_LABELS:
        _key, source = sources[provider]
        if source == "bot":
            status = "✅ Bot setup"
        elif source == "env":
            status = "✅ .env"
        else:
            status = "❌ Missing"
        lines.append(f"{AI_PROVIDER_LABELS[provider]}: {status} | model: {models[provider]}")
    return lines


def ai_status_text(lang="bn"):
    keys = ai_provider_keys()
    order = ai_provider_order()
    lines = [
        "Provider order: " + (" → ".join(AI_PROVIDER_LABELS[p] for p in order) if order else "none"),
        "Fallback: tries next configured provider if one fails/empty",
        *ai_status_lines(),
        "User AI Support button: ✅ Enabled",
        "Admin diagnostic: /aiadmin why order failed ORD-XXXXXX",
    ]
    if not any(keys.values()):
        lines.append(ltext(lang, "Add an API key from Admin Menu → ⚙️ AI Setup, or set a .env key and restart.", "Admin Menu → ⚙️ AI Setup থেকে key দিন, অথবা .env key সেট করে restart করুন।"))
    return panel("🤖 AI Status", "\n".join(lines))


def ai_setup_text(lang="bn"):
    order = ai_provider_order()
    lines = [
        ltext(lang, "Tap a provider button, then send only the API key.", "Provider button চাপুন, তারপর শুধু API key পাঠান।"),
        ltext(lang, "Bot setup keys are saved to SQLite immediately; no restart is required.", "Bot setup key সাথে সাথে SQLite-এ save হবে; restart লাগবে না।"),
        ltext(lang, ".env keys still work; a bot setup key takes priority when present.", ".env key এখনও কাজ করবে; Bot setup key থাকলে সেটাই আগে ব্যবহার হবে।"),
        ltext(lang, "Full keys are never shown in status.", "Full key কখনো status-এ দেখানো হবে না।"),
        "",
        "Current status:",
        *ai_status_lines(),
        "",
        "Fallback order: " + (" → ".join(AI_PROVIDER_LABELS[p] for p in order) if order else "none"),
    ]
    return panel("⚙️ AI Setup", "\n".join(lines))


def ai_usage_text():
    sources = ai_provider_key_sources()
    models = ai_provider_models()
    stats = {row[0]: row for row in list_ai_provider_stats()}
    order = ai_provider_order()
    lines = [
        "Fallback order: " + (" → ".join(AI_PROVIDER_LABELS[p] for p in order) if order else "none"),
        "Counts update after each provider attempt. Keys/prompts/responses are hidden.",
        "",
    ]
    for provider, label in AI_PROVIDER_LABELS.items():
        _key, source = sources[provider]
        source_label = source or "missing"
        row = stats.get(provider)
        success_count = row[1] if row else 0
        failure_count = row[2] if row else 0
        last_success = short_datetime(row[3]) if row else "-"
        last_failure = short_datetime(row[4]) if row else "-"
        last_error = row[5] if row and row[5] else "-"
        lines.append(f"{label}")
        lines.append(f"  model: {models[provider]}")
        lines.append(f"  source: {source_label} | ok: {success_count} | fail: {failure_count}")
        lines.append(f"  last ok: {last_success} | last fail: {last_failure}")
        if last_error != "-":
            lines.append(f"  last error: {last_error}")
    return panel("📊 AI Usage", "\n".join(lines)[:3900])


def ai_setup_keyboard(lang="bn"):
    providers = list(AI_PROVIDER_LABELS.items())
    keyboard = []
    for idx in range(0, len(providers), 2):
        keyboard.append([
            InlineKeyboardButton(label, callback_data=f"ai_setup_{provider}")
            for provider, label in providers[idx:idx + 2]
        ])
    keyboard.append([InlineKeyboardButton("❌ Cancel" if lang == "en" else "❌ বাতিল", callback_data="ai_setup_cancel"), InlineKeyboardButton(tr("back", lang), callback_data="back")])
    return InlineKeyboardMarkup(keyboard)


def ai_setup_provider_prompt(provider, lang="bn"):
    label = AI_PROVIDER_LABELS[provider]
    return panel("🔑 AI API Key", ltext(lang, f"Send the {label} API key.\n\nSend only the key; your next message will be saved.\nTo cancel, send /cancel or cancel.", f"{label} API key পাঠান।\n\nশুধু key পাঠান; next message save হবে।\nCancel করতে /cancel, cancel, অথবা বাতিল লিখুন।"))


SWAP_PROVIDER_LABELS = {"lifi": "LI.FI", "relay": "Relay", "socket": "Socket"}
SWAP_PROVIDER_SETTING_KEYS = {"lifi": "swap_lifi_api_key", "relay": "swap_relay_api_key", "socket": "swap_socket_api_key"}


def _clean_swap_key(value):
    value = str(value or "").strip()
    return value or None


def swap_provider_env_keys():
    return {"lifi": LIFI_API_KEY, "relay": RELAY_API_KEY, "socket": SOCKET_API_KEY}


def swap_provider_key_sources():
    env_keys = swap_provider_env_keys()
    sources = {}
    for provider, setting_key in SWAP_PROVIDER_SETTING_KEYS.items():
        db_key = _clean_swap_key(get_setting(setting_key))
        env_key = _clean_swap_key(env_keys.get(provider))
        if db_key:
            sources[provider] = (db_key, "bot")
        elif env_key:
            sources[provider] = (env_key, "env")
        else:
            sources[provider] = (None, None)
    return sources


def swap_provider_key(provider):
    return swap_provider_key_sources().get(provider, (None, None))[0]


def swap_status_lines():
    lines = []
    for provider, label in SWAP_PROVIDER_LABELS.items():
        _key, source = swap_provider_key_sources()[provider]
        status = "✅ Bot setup" if source == "bot" else "✅ .env" if source == "env" else "⚪ Optional/missing"
        note = "quotes enabled" if provider == "lifi" else "key saved for future provider integration"
        lines.append(f"{label}: {status} | {note}")
    return lines


def swap_setup_text(lang="bn"):
    lines = [
        ltext(lang, "Tap a provider, then send only the API key.", "Provider button চাপুন, তারপর শুধু API key পাঠান।"),
        ltext(lang, "Keys are saved in SQLite immediately; no restart required.", "Key SQLite-এ সাথে সাথে save হবে; restart লাগবে না।"),
        ltext(lang, "LI.FI is used for live quotes now. Relay/Socket keys are stored so they can be enabled later without changing .env.", "Live quote এখন LI.FI দিয়ে চলে। Relay/Socket key save থাকবে, পরে .env ছাড়া enable করা যাবে।"),
        ltext(lang, "Full keys are never shown in status.", "Full key status-এ কখনো দেখানো হবে না।"),
        "",
        *swap_status_lines(),
    ]
    return panel("🔁 Swap API Setup", "\n".join(lines))


def swap_setup_keyboard(lang="bn"):
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("LI.FI", callback_data="swap_setup_lifi"), InlineKeyboardButton("Relay", callback_data="swap_setup_relay")],
            [InlineKeyboardButton("Socket", callback_data="swap_setup_socket")],
            [InlineKeyboardButton("❌ Cancel" if lang == "en" else "❌ বাতিল", callback_data="swap_setup_cancel"), InlineKeyboardButton(tr("back", lang), callback_data="back")],
        ]
    )


def swap_setup_provider_prompt(provider, lang="bn"):
    label = SWAP_PROVIDER_LABELS[provider]
    return panel("🔑 Swap API Key", ltext(lang, f"Send the {label} API key.\n\nSend only the key; your next message will be saved.\nTo cancel, send /cancel or cancel.", f"{label} API key পাঠান।\n\nশুধু key পাঠান; next message save হবে।\nCancel করতে /cancel, cancel, অথবা বাতিল লিখুন।"))


def swap_chains(context):
    chains = context.application.bot_data.get("swap_lifi_chains") if getattr(context, "application", None) else None
    if not chains:
        chains = fallback_chains()
    return chains


async def track_swap_status(bot, chat_id, chain_id, tx_hash, lang="bn"):
    await asyncio.sleep(15)
    for _ in range(10):
        try:
            status = await asyncio.get_running_loop().run_in_executor(None, lambda: get_lifi_status(chain_id, tx_hash))
            if status["status"] == "DONE":
                await bot.send_message(chat_id, ltext(lang, f"✅ Swap completed successfully!\nHash: `{tx_hash}`", f"✅ Swap সফলভাবে সম্পন্ন হয়েছে!\nHash: `{tx_hash}`"))
                return
            if status["status"] == "FAILED":
                await bot.send_message(chat_id, ltext(lang, f"❌ Swap failed on-chain.\nHash: `{tx_hash}`", f"❌ চেইনে Swap ব্যর্থ হয়েছে।\nHash: `{tx_hash}`"))
                return
        except Exception:
            pass
        await asyncio.sleep(30)


async def refresh_swap_chains(context):
    loop = asyncio.get_running_loop()
    try:
        chains = await loop.run_in_executor(None, lambda: get_lifi_chains(swap_provider_key("lifi")))
    except Exception as exc:
        logger.warning("LI.FI chains load failed: %s", exc)
        chains = fallback_chains()
    chains = sorted(chains, key=lambda c: (str(c.get("name") or "")))
    context.application.bot_data["swap_lifi_chains"] = chains
    return chains


def swap_chain_keyboard(chains, target="from", page=0, lang="bn"):
    total_pages = max(1, math.ceil(len(chains) / SWAP_CHAIN_PAGE_SIZE))
    page = max(0, min(int(page or 0), total_pages - 1))
    start = page * SWAP_CHAIN_PAGE_SIZE
    rows = []
    for chain in chains[start:start + SWAP_CHAIN_PAGE_SIZE]:
        rows.append([InlineKeyboardButton(chain_label(chain)[:45], callback_data=f"swap_{target}_{chain['id']}")])
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("◀️", callback_data=f"swap_{target}_page_{page - 1}"))
    nav.append(InlineKeyboardButton(f"{page + 1}/{total_pages}", callback_data="swap_noop"))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton("▶️", callback_data=f"swap_{target}_page_{page + 1}"))
    if nav:
        rows.append(nav)
    rows.append([InlineKeyboardButton("🔎 Search" if lang == "en" else "🔎 সার্চ", callback_data=f"swap_{target}_search")])
    rows.append([InlineKeyboardButton(tr("cancel", lang), callback_data="swap_cancel")])
    return InlineKeyboardMarkup(rows)


def swap_intro_text(lang="bn"):
    return panel(
        "🔁 Swap/Bridge",
        ltext(
            lang,
            "Choose the source chain. You can use the buttons or Search and type a chain name/id. After the quote, the bot opens a wallet-connect swap page; your wallet signs the final transaction.",
            "যে chain থেকে token পাঠাবেন সেটি বেছে নিন। Button ব্যবহার করতে পারেন, অথবা Search দিয়ে chain name/id লিখতে পারেন। Quote-এর পর bot wallet-connect swap page খুলবে; final transaction আপনার wallet sign করবে।",
        ),
    )


def swap_cancel_keyboard(lang="bn"):
    return InlineKeyboardMarkup([[InlineKeyboardButton(tr("cancel", lang), callback_data="swap_cancel")]])


def swap_quote_keyboard(lang="bn"):
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("⚡ Fastest" if lang == "en" else "⚡ Fastest", callback_data="swap_pref_fastest"), InlineKeyboardButton("💸 Cheapest" if lang == "en" else "💸 Cheapest", callback_data="swap_pref_cheapest")],
            [InlineKeyboardButton(tr("cancel", lang), callback_data="swap_cancel")],
        ]
    )


def swap_confirm_keyboard(context, user_id, lang="bn"):
    intent = context.user_data.get("swap_intent", {})
    from_chain_id = intent.get("from_chain_id")
    chains = swap_chains(context)
    from_chain = find_chain(chains, from_chain_id)
    chain_type = str((from_chain or {}).get("chainType") or "").upper()

    has_wallet = False
    if chain_type == "SVM" or str(from_chain_id) == "1151111081099710":
        has_wallet = bool(get_user_solana_wallet(user_id))
    elif chain_type == "EVM":
        has_wallet = bool(get_user_evm_wallet(user_id))

    rows = []
    if has_wallet:
        rows.append([InlineKeyboardButton("🚀 Execute In-Bot (Sign with Personal Wallet)" if lang == "en" else "🚀 বটের মাধ্যমে Swap করুন (Personal Wallet)", callback_data="swap_confirm_in_bot")])
        rows.append([InlineKeyboardButton("🔗 External Link (Jumper.exchange)" if lang == "en" else "🔗 External Link (Jumper.exchange)", callback_data="swap_confirm_external")])
    else:
        rows.append([InlineKeyboardButton("🔐 Setup Wallet (Enabled In-Bot Swap)" if lang == "en" else "🔐 Wallet Setup করুন (বটের মধ্যে Swap করতে)", callback_data="mw_setup")])
        rows.append([InlineKeyboardButton("🔗 Swap on Website (External)" if lang == "en" else "🔗 ওয়েবসাইটে Swap করুন (External)", callback_data="swap_confirm_external")])

    rows.append([InlineKeyboardButton("🔄 New Quote" if lang == "en" else "🔄 নতুন Quote", callback_data="swap_start"), InlineKeyboardButton(tr("cancel", lang), callback_data="swap_cancel")])
    return InlineKeyboardMarkup(rows)


def swap_quote_text(intent, quote, lang="bn"):
    summary = summarize_quote(quote)
    duration = f"{summary['duration']} sec" if summary.get("duration") else "N/A"
    approval = ltext(lang, "Yes", "হ্যাঁ") if summary["approval_needed"] else ltext(lang, "No", "না")
    body = [
        f"From: {intent['from_chain_name']} {summary['from_symbol']}",
        f"To: {intent['to_chain_name']} {summary['to_symbol']}",
        f"Amount: {intent['amount']} {summary['from_symbol']}",
        f"Estimated receive: {summary['to_amount']} {summary['to_symbol']}",
        f"Minimum receive: {summary['to_min']} {summary['to_symbol']}",
        f"Gas: ${summary['gas_usd']} | Bridge/DEX fee: ${summary['fee_usd']}",
        f"Estimated time: {duration}",
        f"Route: {summary['tool']}",
        f"Approval needed: {approval}",
        "",
        ltext(lang, "Confirm only if chain, token, amount, and wallet address are correct.", "Chain, token, amount এবং wallet address ঠিক থাকলেই Confirm চাপুন।"),
    ]
    return panel("🔁 Swap Quote", "\n".join(body))


def swap_launcher_text(quote, lang="bn"):
    summary = summarize_quote(quote)
    lines = [
        ltext(lang, "Connect your wallet with the button below to complete the swap/bridge automatically. The bot never asks for seed phrase or private key; your wallet signs the transaction.", "নিচের button দিয়ে wallet connect করে swap/bridge automatically complete করুন। Bot কখনো seed phrase বা private key চাইবে না; transaction আপনার wallet sign করবে।"),
        "",
    ]
    if summary["approval_needed"]:
        lines.extend([
            ltext(lang, "Approval may be required before swap/bridge.", "Swap/bridge-এর আগে approval লাগতে পারে।"),
            f"Spender: `{summary['approval_address']}`",
            "",
        ])
    lines.extend([
        ltext(lang, "Manual fallback transaction data:", "Manual fallback transaction data:"),
        f"Chain ID: `{summary['chain_id']}`",
        f"To: `{summary['tx_to']}`",
        f"Value: `{summary['tx_value']}`",
        f"Data: `{short_tx_data(summary['tx_data'])}`",
        "",
        ltext(lang, "After sending, paste the transaction hash here if you want to track it.", "Send করার পর track করতে চাইলে transaction hash এখানে পাঠান।"),
    ])
    return panel("🚀 Transaction Launcher", "\n".join(lines))


def swap_launcher_keyboard(intent, quote, lang="bn"):
    widget_url = build_lifi_widget_url(intent, quote)
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🔗 Connect Wallet & Swap" if lang == "en" else "🔗 Wallet Connect করে Swap", url=widget_url)],
            [InlineKeyboardButton("🔄 New Quote" if lang == "en" else "🔄 নতুন Quote", callback_data="swap_start")],
            [InlineKeyboardButton(tr("back", lang), callback_data="back")],
        ]
    )


async def start_swap_flow(update_or_query, context, lang="bn"):
    context.user_data.clear()
    context.user_data["swap_step"] = "from_chain"
    chains = await refresh_swap_chains(context)
    text = swap_intro_text(lang)
    markup = swap_chain_keyboard(chains, "from", 0, lang)
    if hasattr(update_or_query, "edit_message_text"):
        await update_or_query.edit_message_text(text, reply_markup=markup)
    else:
        await update_or_query.message.reply_text(text, reply_markup=markup)


def user_lang(user_id) -> str:
    return get_user_language(user_id) or "bn"


def tr(key, lang="bn", **kwargs):
    value = TEXT.get(key, {}).get(lang) or TEXT.get(key, {}).get("bn") or key
    return value.format(**kwargs) if kwargs else value


def panel(title, body=""):
    return f"{title}\n{DIVIDER}\n{body}".rstrip() if body else str(title).rstrip()


def command_help_text(user_id=None):
    user_commands = [
        ("/start", "মেইন মেনু/ভাষা খুলুন"),
        ("/help", "সব typed command দেখুন"),
        ("/guide", "পুরো user guide পড়ুন"),
        ("/terms", "terms ও risk warning"),
        ("/ai", "AI support chat শুরু"),
        ("/swap", "LI.FI quote দিয়ে swap/bridge launcher"),
        ("/order ORD-XXXXXX", "order ID দিয়ে status দেখুন"),
        ("/status TRXID_OR_ORDERID", "transaction/order status দেখুন"),
        ("/receipt ORD_OR_TRX", "completed order receipt দেখুন"),
        ("/seller USER_ID", "seller profile/stats দেখুন"),
        ("/seller_center", "seller menu/application/tools"),
        ("/seller_dashboard", "seller dashboard খুলুন"),
        ("/seller_guide", "seller guide পড়ুন"),
        ("/referral", "referral link/wallet দেখুন"),
        ("/setup", "personal wallet key connect/encrypt"),
        ("/changekey", "saved wallet key change"),
        ("/deletekey", "saved wallet key delete"),
        ("/mybalance", "personal wallet balance দেখুন"),
        ("/send_wallet", "personal wallet থেকে crypto send"),
        ("/payout", "payout request flow শুরু"),
    ]
    lines = ["Normal User Commands"] + [f"{cmd} — {desc}" for cmd, desc in user_commands]
    if is_admin(user_id):
        admin_commands = [
            ("/send", "admin send flow শুরু"),
            ("/gencode", "gift code generate"),
            ("/pending", "pending/manual verify orders"),
            ("/failed", "failed sends + retry button"),
            ("/stats", "bot/order stats দেখুন"),
            ("/balances", "admin stock balances দেখুন"),
            ("/maintenance [on|off]", "maintenance mode on/off"),
            ("/backup", "DB backup পাঠান"),
            ("/report [weekly]", "sales/order report দেখুন"),
            ("/profit [daily|weekly]", "profit summary দেখুন"),
            ("/costrate [NETWORK RATE]", "cost rates set/list"),
            ("/gas", "native gas monitor দেখুন"),
            ("/reservations", "active reservations দেখুন"),
            ("/audit", "audit log দেখুন"),
            ("/payouts", "payout review করুন"),
            ("/webhook_health", "bKash webhook health দেখুন"),
            ("/bot_health", "overall bot health panel"),
            ("/restart_help", "Termux safe restart guide"),
            ("/test_sms [amount]", "fake buyer SMS test"),
            ("/test_seller_sms [amount]", "fake seller SMS test"),
            ("/seller_badge USER_ID new|verified|trusted", "seller badge update"),
            ("/aiadmin why order failed ORD-123", "AI admin diagnostics"),
            ("/ai_usage", "AI model success/failure counts"),
        ]
        lines += ["", "Admin Commands"] + [f"{cmd} — {desc}" for cmd, desc in admin_commands]
    lines.append(f"\nSupport: @{SUPPORT_USERNAME.lstrip('@')}")
    return panel("📌 Command Help", "\n".join(lines))


def short_wallet(wallet):
    return f"{wallet[:8]}...{wallet[-6:]}" if wallet and len(wallet) > 18 else (wallet or "N/A")


def language_keyboard():
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("বাংলা 🇧🇩", callback_data="set_lang_bn"), InlineKeyboardButton("English 🇺🇸", callback_data="set_lang_en")]
        ]
    )


def welcome_video_available(path=WELCOME_VIDEO_PATH):
    return bool(path) and os.path.isfile(path) and os.path.getsize(path) > 0


def is_video_message(message):
    return bool(message and getattr(message, "video", None))


def language_saved_home_text(first_name, lang):
    return f"{tr('language_saved', lang)}\n\n{home_text(first_name, lang)}"


def fits_video_caption(text):
    return len(text or "") <= TELEGRAM_VIDEO_CAPTION_LIMIT


async def send_welcome_video_background(message):
    if not welcome_video_available():
        return
    try:
        with open(WELCOME_VIDEO_PATH, "rb") as video:
            await message.reply_video(video=video)
    except Exception as exc:
        logger.warning("Background welcome video send failed: %s", exc)


def back_keyboard(lang):
    return InlineKeyboardMarkup([[InlineKeyboardButton(tr("back", lang), callback_data="back")]])


def free_service_keyboard(lang):
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(ltext(lang, "📨 Telegram Message Forwarder", "📨 Telegram Message Forwarder"), callback_data="telegram_message_forwarder")],
            [InlineKeyboardButton(ltext(lang, "♻️ Solana ATA Refund", "♻️ Solana ATA Refund"), callback_data="solana_ata_refund")],
            [InlineKeyboardButton(ltext(lang, "🆔 Telegram ID Finder", "🆔 Telegram ID Finder"), callback_data="telegram_id_finder")],
            [InlineKeyboardButton(tr("back", lang), callback_data="back")],
        ]
    )


def free_service_text(lang):
    body = ltext(
        lang,
        "Choose a free tool below.\n\nTelegram Message Forwarder sends one message to approved Telegram groups/channels. Solana ATA Refund checks empty Associated Token Accounts and can close them to return refundable rent SOL to the same wallet. Telegram ID Finder helps find user/group/channel IDs from usernames, public links, forwarded messages, or the current chat.",
        "নিচের free tool বেছে নিন।\n\nTelegram Message Forwarder দিয়ে approved Telegram group/channel-এ message পাঠানো যায়। Solana ATA Refund empty Associated Token Account check করে closable rent SOL একই wallet-এ ফেরত দিতে পারে। Telegram ID Finder username, public link, forwarded message অথবা current chat থেকে user/group/channel ID বের করতে সাহায্য করে।",
    )
    return panel(tr("free_service", lang), body)


def telegram_id_finder_keyboard(lang):
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(ltext(lang, "🔎 Start ID Finder", "🔎 ID Finder শুরু করুন"), callback_data="tid_start")],
            [InlineKeyboardButton(ltext(lang, "🔙 Free Service", "🔙 Free Service"), callback_data="free_service")],
        ]
    )


def telegram_id_finder_text(lang):
    return panel(
        ltext(lang, "🆔 Telegram ID Finder", "🆔 Telegram ID Finder"),
        ltext(
            lang,
            "This tool helps you find Telegram user, group, or channel IDs.\n\nHow to use\n1. Tap Start ID Finder.\n2. Send a public @username or public t.me/telegram.me link.\n3. Or forward a message from the user/group/channel.\n4. Or use it inside a group/channel where the bot can read messages to see the current chat ID.\n\nNotes\n• Public usernames/links can be resolved directly.\n• Private group/channel IDs usually require the bot/account to have access, or a forwarded message with visible origin.\n• If Telegram hides the forward sender for privacy, the bot cannot reveal that hidden ID.",
            "এই tool দিয়ে Telegram user, group অথবা channel ID বের করতে পারবেন।\n\nকীভাবে ব্যবহার করবেন\n১. Start ID Finder চাপুন।\n২. Public @username অথবা public t.me/telegram.me link পাঠান।\n৩. অথবা user/group/channel থেকে কোনো message forward করুন।\n৪. অথবা bot যেখানে message পড়তে পারে এমন group/channel-এ ব্যবহার করলে current chat ID দেখা যাবে।\n\nনোট\n• Public username/link সরাসরি resolve করা যায়।\n• Private group/channel ID পেতে সাধারণত bot/account-এর access লাগবে, অথবা visible origin সহ forwarded message লাগবে।\n• Telegram privacy-এর কারণে forward sender hidden থাকলে bot সেই hidden ID বের করতে পারে না।",
        ),
    )


def normalize_telegram_lookup_target(value):
    raw = (value or "").strip().strip(",")
    if not raw:
        return None
    raw = raw.split("?", 1)[0].rstrip("/")
    match = re.match(r"^(?:https?://)?(?:www\.)?(?:t\.me|telegram\.me)/(.+)$", raw, re.IGNORECASE)
    if match:
        path = match.group(1).strip("/")
        if path.startswith("+") or path.lower().startswith("joinchat/"):
            return None
        if path.startswith("c/"):
            parts = path.split("/")
            if len(parts) >= 2 and parts[1].isdigit():
                return f"-100{parts[1]}"
            return None
        raw = path.split("/", 1)[0]
    if re.fullmatch(r"-?\d+", raw):
        return int(raw)
    raw = raw.lstrip("@")
    if re.fullmatch(r"[A-Za-z0-9_]{5,32}", raw):
        return f"@{raw}"
    return None


def telegram_chat_type_label(chat_type, lang):
    labels = {
        "private": ltext(lang, "User/account", "User/account"),
        "group": ltext(lang, "Group", "Group"),
        "supergroup": ltext(lang, "Supergroup", "Supergroup"),
        "channel": ltext(lang, "Channel", "Channel"),
    }
    return labels.get(chat_type, chat_type or ltext(lang, "Unknown", "Unknown"))


def telegram_id_result_text(lang, entries, note=None):
    lines = [ltext(lang, "🆔 Telegram ID Finder result", "🆔 Telegram ID Finder result")]
    for entry in entries:
        lines.extend(
            [
                "",
                f"{entry.get('label')}",
                f"ID: {entry.get('id')}",
            ]
        )
        if entry.get("type"):
            lines.append(ltext(lang, f"Type: {entry.get('type')}", f"Type: {entry.get('type')}"))
        if entry.get("title"):
            lines.append(ltext(lang, f"Name/title: {entry.get('title')}", f"Name/title: {entry.get('title')}"))
        if entry.get("username"):
            lines.append(f"Username: @{entry.get('username')}")
        if entry.get("message_id"):
            lines.append(f"Message ID: {entry.get('message_id')}")
    if note:
        lines.extend(["", note])
    return "\n".join(lines)


def forwarded_origin_entries(message, lang):
    entries = []
    origin = getattr(message, "forward_origin", None)
    if origin:
        sender_user = getattr(origin, "sender_user", None)
        sender_chat = getattr(origin, "sender_chat", None) or getattr(origin, "chat", None)
        if sender_user:
            entries.append(
                {
                    "label": ltext(lang, "Forwarded from user/account", "Forward করা user/account"),
                    "id": sender_user.id,
                    "type": ltext(lang, "User/account", "User/account"),
                    "title": getattr(sender_user, "full_name", None) or getattr(sender_user, "first_name", None),
                    "username": getattr(sender_user, "username", None),
                }
            )
        if sender_chat:
            entries.append(
                {
                    "label": ltext(lang, "Forwarded from chat/channel", "Forward করা chat/channel"),
                    "id": sender_chat.id,
                    "type": telegram_chat_type_label(getattr(sender_chat, "type", None), lang),
                    "title": getattr(sender_chat, "title", None) or getattr(sender_chat, "full_name", None),
                    "username": getattr(sender_chat, "username", None),
                    "message_id": getattr(origin, "message_id", None),
                }
            )
        hidden_name = getattr(origin, "sender_user_name", None)
        if hidden_name and not entries:
            return [], ltext(lang, f"Telegram hid the sender ID for privacy. Visible name: {hidden_name}", f"Telegram privacy-এর কারণে sender ID hidden। Visible name: {hidden_name}")
    forward_from = getattr(message, "forward_from", None)
    if forward_from:
        entries.append(
            {
                "label": ltext(lang, "Forwarded from user/account", "Forward করা user/account"),
                "id": forward_from.id,
                "type": ltext(lang, "User/account", "User/account"),
                "title": getattr(forward_from, "full_name", None) or getattr(forward_from, "first_name", None),
                "username": getattr(forward_from, "username", None),
            }
        )
    forward_chat = getattr(message, "forward_from_chat", None)
    if forward_chat:
        entries.append(
            {
                "label": ltext(lang, "Forwarded from chat/channel", "Forward করা chat/channel"),
                "id": forward_chat.id,
                "type": telegram_chat_type_label(getattr(forward_chat, "type", None), lang),
                "title": getattr(forward_chat, "title", None),
                "username": getattr(forward_chat, "username", None),
                "message_id": getattr(message, "forward_from_message_id", None),
            }
        )
    return entries, None


def solana_refund_keyboard(lang, connected=False, refundable=False):
    rows = []
    rows.append([InlineKeyboardButton(ltext(lang, "🔐 Connect Solana wallet", "🔐 Solana wallet connect করুন"), callback_data="sr_connect")])
    if connected:
        rows.append([InlineKeyboardButton(ltext(lang, "🔎 Check ATA accounts", "🔎 ATA account check করুন"), callback_data="sr_check")])
    if refundable:
        rows.append([InlineKeyboardButton(ltext(lang, "♻️ Refund SOL", "♻️ SOL refund করুন"), callback_data="sr_refund")])
    if connected:
        rows.append([InlineKeyboardButton(ltext(lang, "🔌 Disconnect wallet", "🔌 Wallet disconnect"), callback_data="sr_disconnect")])
    rows.append([InlineKeyboardButton(ltext(lang, "🔙 Free Service", "🔙 Free Service"), callback_data="free_service")])
    return InlineKeyboardMarkup(rows)


def solana_refund_text(lang, wallet=None, summary=None):
    lines = [
        ltext(lang, "♻️ Solana ATA Refund", "♻️ Solana ATA Refund"),
        "",
        ltext(
            lang,
            "This tool checks your Solana wallet for empty Associated Token Accounts (ATA). Empty ATAs can be closed to return their rent SOL to the same wallet.",
            "এই tool আপনার Solana wallet-এর empty Associated Token Account (ATA) check করে। Empty ATA close করলে rent SOL একই wallet-এ ফেরত আসে।",
        ),
        "",
        ltext(lang, "Important:", "গুরুত্বপূর্ণ:"),
        ltext(lang, "• Only your own Solana wallet should be connected.", "• শুধু নিজের Solana wallet connect করবেন।"),
        ltext(lang, "• ATAs with token balances will not be closed.", "• Token balance থাকা ATA close করা হবে না।"),
        ltext(lang, "• Solana network fee applies when refunding.", "• Refund করার সময় Solana network fee লাগবে।"),
    ]
    if wallet:
        lines.extend(["", ltext(lang, f"Connected wallet: `{short_wallet(wallet)}`", f"Connected wallet: `{short_wallet(wallet)}`")])
    if summary:
        lines.extend(
            [
                "",
                ltext(lang, "ATA check result:", "ATA check result:"),
                ltext(lang, f"• Refundable empty ATA: {summary.get('refundable_count', 0)}", f"• Refund করা যাবে এমন empty ATA: {summary.get('refundable_count', 0)}"),
                ltext(lang, f"• Estimated refundable SOL: {summary.get('total_sol', 0):.6f}", f"• আনুমানিক refundable SOL: {summary.get('total_sol', 0):.6f}"),
                ltext(lang, f"• Non-empty token accounts skipped: {summary.get('non_empty_count', 0)}", f"• Token balance থাকায় skip: {summary.get('non_empty_count', 0)}"),
            ]
        )
    return "\n".join(lines)


def free_forward_keyboard(lang, has_token=False, has_schedule=False, has_personal=False):
    rows = []
    rows.append([InlineKeyboardButton(ltext(lang, "🔐 Connect Telegram token", "🔐 Telegram token connect করুন"), callback_data="ff_connect_token")])
    rows.append([InlineKeyboardButton(ltext(lang, "👤 Connect personal account", "👤 Personal account connect করুন"), callback_data="pf_connect_account")])
    rows.append([InlineKeyboardButton(ltext(lang, "📣 Forward with bot token", "📣 Bot token দিয়ে forward"), callback_data="ff_forward")])
    rows.append([InlineKeyboardButton(ltext(lang, "👤 Forward with personal account", "👤 Personal account দিয়ে forward"), callback_data="pf_forward")])
    if has_schedule:
        rows.append([InlineKeyboardButton(ltext(lang, "🛑 Stop scheduled forward", "🛑 নির্দিষ্ট সময়ের forward বন্ধ"), callback_data="ff_cancel_schedule")])
    if has_token:
        rows.append([InlineKeyboardButton(ltext(lang, "🔌 Disconnect token", "🔌 Token disconnect"), callback_data="ff_disconnect_token")])
    if has_personal:
        rows.append([InlineKeyboardButton(ltext(lang, "🔌 Disconnect personal account", "🔌 Personal account disconnect"), callback_data="pf_disconnect_account")])
    rows.append([InlineKeyboardButton(ltext(lang, "🔙 Free Service", "🔙 Free Service"), callback_data="free_service")])
    return InlineKeyboardMarkup(rows)


def free_forward_mode_keyboard(lang, prefix="ff"):
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(ltext(lang, "⚡ One-time forward", "⚡ এককালীন forward"), callback_data=f"{prefix}_one_time")],
            [InlineKeyboardButton(ltext(lang, "⏰ Forward repeatedly", "⏰ নির্দিষ্ট সময় পরপর forward"), callback_data=f"{prefix}_schedule")],
            [InlineKeyboardButton(tr("cancel", lang), callback_data="ff_cancel_flow")],
        ]
    )


def personal_forward_target_source_keyboard(lang):
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(ltext(lang, "📋 Select from my groups/channels", "📋 আমার group/channel list থেকে select"), callback_data="pf_pick_list")],
            [InlineKeyboardButton(ltext(lang, "✍️ Enter target manually", "✍️ Target manually লিখুন"), callback_data="pf_manual_targets")],
            [InlineKeyboardButton(tr("cancel", lang), callback_data="ff_cancel_flow")],
        ]
    )


def free_forward_cancel_keyboard(lang):
    return InlineKeyboardMarkup([[InlineKeyboardButton(tr("cancel", lang), callback_data="ff_cancel_flow")]])


def personal_forward_dialog_title(dialog):
    title = (dialog.get("title") or "Telegram chat").strip()
    if len(title) > 34:
        title = title[:31].rstrip() + "…"
    username = dialog.get("username")
    return f"{title} (@{username})" if username else title


def personal_forward_picker_text(lang, page, dialogs, selected):
    total = len(dialogs)
    start = page * PERSONAL_FORWARD_DIALOG_PAGE_SIZE + 1 if total else 0
    end = min(total, (page + 1) * PERSONAL_FORWARD_DIALOG_PAGE_SIZE)
    selected_count = len(selected)
    return ltext(
        lang,
        f"Select target groups/channels from your connected account.\n\nShowing {start}-{end} of {total}. Selected: {selected_count}/{PERSONAL_FORWARD_MAX_TARGETS}.\n\nIf a private group/channel is missing, make sure your account is still a member.",
        f"Connected account থেকে target group/channel select করুন।\n\nদেখানো হচ্ছে {start}-{end}, মোট {total}। Selected: {selected_count}/{PERSONAL_FORWARD_MAX_TARGETS}.\n\nকোনো private group/channel না দেখালে নিশ্চিত করুন আপনার account সেখানে member আছে।",
    )


def personal_forward_picker_keyboard(lang, page, dialogs, selected):
    selected = {str(value) for value in selected}
    total_pages = max(1, math.ceil(len(dialogs) / PERSONAL_FORWARD_DIALOG_PAGE_SIZE))
    page = max(0, min(page, total_pages - 1))
    start = page * PERSONAL_FORWARD_DIALOG_PAGE_SIZE
    rows = []
    for index, dialog in enumerate(dialogs[start:start + PERSONAL_FORWARD_DIALOG_PAGE_SIZE], start=start):
        checked = "✅" if str(dialog.get("id")) in selected else "⬜"
        rows.append([InlineKeyboardButton(f"{checked} {personal_forward_dialog_title(dialog)}", callback_data=f"pf_pick_toggle_{index}")])
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("◀️", callback_data=f"pf_pick_page_{page - 1}"))
    nav.append(InlineKeyboardButton(f"{page + 1}/{total_pages}", callback_data="pf_pick_noop"))
    if page + 1 < total_pages:
        nav.append(InlineKeyboardButton("▶️", callback_data=f"pf_pick_page_{page + 1}"))
    rows.append(nav)
    rows.append([InlineKeyboardButton(ltext(lang, "✅ Done", "✅ Done"), callback_data="pf_pick_done")])
    rows.append([InlineKeyboardButton(ltext(lang, "🔄 Refresh list", "🔄 List refresh"), callback_data="pf_pick_list")])
    rows.append([InlineKeyboardButton(ltext(lang, "✍️ Enter manually", "✍️ Manually লিখুন"), callback_data="pf_manual_targets")])
    rows.append([InlineKeyboardButton(tr("cancel", lang), callback_data="ff_cancel_flow")])
    return InlineKeyboardMarkup(rows)


def free_forward_text(lang, has_token=False, bot_name=None, has_schedule=False, has_personal=False, personal_name=None):
    status = ltext(lang, "Connected", "Connected") if has_token else ltext(lang, "Not connected", "Connect করা নেই")
    if has_token and bot_name:
        status = f"{status}: @{bot_name}" if bot_name else status
    personal_status = ltext(lang, "Connected", "Connected") if has_personal else ltext(lang, "Not connected", "Connect করা নেই")
    if has_personal and personal_name:
        personal_status = f"{personal_status}: {personal_name}"
    schedule = ltext(lang, "Running", "চলছে") if has_schedule else ltext(lang, "Not running", "চলছে না")
    body = ltext(
        lang,
        "What is this?\n"
        "Send the same message to approved Telegram groups/channels using either your connected Telegram bot token or your own personal Telegram account session.\n\n"
        "Benefits\n"
        "• Bot-token mode is simple for groups/channels where your bot is added.\n"
        "• Personal-account mode can post as your own account in groups/channels where you are already a member and have permission.\n"
        "• One-time and repeated forwarding are supported, with rate limits to reduce spam/account risk.\n\n"
        "How to use\n"
        "1. Open Free Service, then tap Telegram Message Forwarder.\n"
        "2. Create or copy a bot token from @BotFather.\n"
        "3. Add that bot to every target group/channel. For channels or restricted groups, make it admin or allow it to post messages.\n"
        "4. Tap Connect Telegram token and send the token. The token message is deleted after checking.\n"
        "5. Or tap Connect personal account and open the secure web login link. Enter your Telegram API ID, API hash, phone number, login code, and 2FA password there if Telegram asks. Never send login codes in Telegram chat. The session is kept only in bot memory.\n"
        "6. Tap Forward with bot token or Forward with personal account.\n"
        "7. Choose One-time forward to send once, or Forward repeatedly to send after a fixed interval.\n"
        f"8. Send target chat IDs, @usernames, or public t.me links separated by space/comma/new line. In personal-account mode you can also select private groups/channels from your connected account list. Bot-token maximum: {FREE_FORWARD_MAX_TARGETS}; personal-account maximum: {PERSONAL_FORWARD_MAX_TARGETS}.\n"
        f"9. For repeated forwarding, send the interval in minutes. Personal account minimum interval: {PERSONAL_FORWARD_MIN_INTERVAL_MINUTES} minutes.\n"
        "10. Send the message you want to forward. Text, photo, video, document, audio, voice, animation, and sticker are supported.\n\n"
        "Where to get API ID/API hash\n"
        "• Visit https://my.telegram.org, log in with your Telegram phone number, open API development tools, create an app if needed, then copy api_id and api_hash.\n\n"
        "Where to get group/channel ID\n"
        "• Public group/channel: use its @username or public t.me link.\n"
        "• Private group/channel: add the bot/account first, then copy the numeric chat ID from a trusted Telegram ID bot/admin tool or your own bot update/log. Supergroup/channel IDs usually start with -100.\n\n"
        "Important\n"
        "• Private invite links do not work directly; use a chat ID after the bot is a member.\n"
        "• If a target fails, check that the bot is added and has permission to post.\n"
        "• Personal-account forwarding is only for groups/channels where your account is a member and you have permission/consent to post. It is rate-limited to reduce spam/account-risk.\n"
        "• Use Stop scheduled forward to stop repeats, and Disconnect token to remove the connected token from this session.\n\n"
        f"Bot token: {status}\nPersonal account: {personal_status}\nScheduled forward: {schedule}",
        "এটা কী?\n"
        "নিজের connected Telegram bot token অথবা নিজের personal Telegram account session দিয়ে approved group/channel-এ একই message পাঠানোর সার্ভিস।\n\n"
        "সুবিধাসমূহ\n"
        "• Bot-token mode সহজ—যেসব group/channel-এ আপনার bot add করা আছে সেখানে ব্যবহার করা যায়।\n"
        "• Personal-account mode-এ আপনার নিজের account দিয়ে সেই group/channel-এ post করা যায় যেখানে account member এবং permission আছে।\n"
        "• একবার forward এবং নির্দিষ্ট সময় পরপর forward—দুটিই supported; spam/account-risk কমাতে rate-limit আছে।\n\n"
        "কীভাবে ব্যবহার করবেন\n"
        "১. Free Service খুলে Telegram Message Forwarder চাপুন।\n"
        "২. @BotFather থেকে bot token তৈরি/copy করুন।\n"
        "৩. যেসব group/channel-এ পাঠাতে চান, সেসব জায়গায় ওই bot add করুন। Channel বা restricted group হলে bot-কে admin করুন অথবা post করার permission দিন।\n"
        "৪. Connect Telegram token চাপুন এবং token পাঠান। Check করার পর token message delete করা হবে।\n"
        "৫. অথবা Connect personal account চাপুন এবং secure web login link খুলুন। Telegram API ID, API hash, phone number, login code এবং Telegram চাইলে 2FA password সেখানে দিন। Telegram chat-এ login code কখনো পাঠাবেন না। Session শুধু bot memory-তে থাকবে।\n"
        "৬. Forward with bot token অথবা Forward with personal account চাপুন।\n"
        "৭. একবার পাঠাতে One-time forward, আর নির্দিষ্ট সময় পরপর পাঠাতে Forward repeatedly বেছে নিন।\n"
        f"৮. Target chat ID, @username অথবা public t.me link পাঠান। Personal-account mode-এ connected account list থেকেও private group/channel select করা যাবে। Space/comma/new line দিয়ে আলাদা করুন। Bot-token maximum {FREE_FORWARD_MAX_TARGETS}, personal-account maximum {PERSONAL_FORWARD_MAX_TARGETS} target।\n"
        f"৯. নির্দিষ্ট সময় পরপর পাঠালে interval কত মিনিট হবে সেটা লিখুন। Personal account minimum {PERSONAL_FORWARD_MIN_INTERVAL_MINUTES} মিনিট।\n"
        "১০. যে message পাঠাতে চান সেটি পাঠান। Text, photo, video, document, audio, voice, animation এবং sticker supported।\n\n"
        "API ID/API hash কোথা থেকে পাবেন\n"
        "• https://my.telegram.org এ যান, নিজের Telegram phone number দিয়ে login করুন, API development tools খুলুন, দরকার হলে app create করুন, তারপর api_id এবং api_hash copy করুন।\n\n"
        "Group/channel ID কোথা থেকে পাবেন\n"
        "• Public group/channel হলে @username বা public t.me link ব্যবহার করুন।\n"
        "• Private group/channel হলে আগে bot/account add করুন, তারপর trusted Telegram ID bot/admin tool অথবা নিজের bot update/log থেকে numeric chat ID copy করুন। Supergroup/channel ID সাধারণত -100 দিয়ে শুরু হয়।\n\n"
        "গুরুত্বপূর্ণ\n"
        "• Private invite link সরাসরি কাজ করে না; bot member হওয়ার পর chat ID ব্যবহার করুন।\n"
        "• কোনো target fail করলে check করুন bot add আছে কি না এবং post করার permission আছে কি না।\n"
        "• Personal account forwarding শুধু সেই group/channel-এর জন্য যেখানে আপনার account member এবং post করার permission/consent আছে। Spam/account-risk কমাতে rate-limit আছে।\n"
        "• বারবার forward বন্ধ করতে Stop scheduled forward, token/session সরাতে Disconnect ব্যবহার করুন।\n\n"
        f"Bot token: {status}\nPersonal account: {personal_status}\nনির্দিষ্ট সময়ের forward: {schedule}",
    )
    return panel(ltext(lang, "📨 Telegram Message Forwarder", "📨 Telegram Message Forwarder"), body)


def normalize_free_forward_target(value):
    raw = (value or "").strip().strip(",")
    if not raw:
        return None
    raw = raw.split("?", 1)[0].rstrip("/")
    match = re.match(r"^(?:https?://)?(?:www\.)?(?:t\.me|telegram\.me)/(.+)$", raw, re.IGNORECASE)
    if match:
        path = match.group(1).strip("/")
        if path.startswith("+") or path.lower().startswith("joinchat/") or path.startswith("c/"):
            return None
        raw = path.split("/", 1)[0]
    if re.fullmatch(r"-?\d+", raw):
        return raw
    raw = raw.lstrip("@")
    if re.fullmatch(r"[A-Za-z0-9_]{5,32}", raw):
        return f"@{raw}"
    return None


def parse_free_forward_targets(text, max_targets=FREE_FORWARD_MAX_TARGETS):
    values = re.split(r"[\s,]+", text or "")
    targets = []
    invalid = []
    for value in values:
        if not value.strip():
            continue
        target = normalize_free_forward_target(value)
        if not target:
            invalid.append(value.strip())
            continue
        if target not in targets:
            targets.append(target)
    return targets[:max_targets], invalid


def safe_free_forward_error(exc):
    return re.sub(r"\b\d{5,}:[A-Za-z0-9_-]+\b", "[REDACTED_TOKEN]", str(exc))[:160]


def friendly_solana_error(exc, lang="bn"):
    text = str(exc).lower()
    if "attempt to debit an account" in text:
        if lang == "en":
            return "Insufficient balance for gas fees. Please add some SOL to your wallet and try again."
        return "ট্রানজ্যাকশন ফি (Gas Fee) এর জন্য পর্যাপ্ত ব্যালেন্স নেই। অনুগ্রহ করে আপনার ওয়ালেটে কিছু SOL জমা করুন এবং আবার চেষ্টা করুন।"
    return safe_free_forward_error(exc)


def personal_auth_link(token):
    base = (TELEGRAM_AUTH_BASE_URL or "").rstrip("/")
    return f"{base}/telegram-auth/{token}"


def free_forward_clear_flow(context):
    for key in [
        "free_forward_step",
        "free_forward_mode",
        "free_forward_sender",
        "free_forward_targets",
        "free_forward_interval_minutes",
        "personal_forward_api_id",
        "personal_forward_api_hash",
        "personal_forward_phone",
        "personal_forward_dialogs",
        "personal_forward_selected_targets",
        "personal_forward_picker_page",
    ]:
        context.user_data.pop(key, None)


async def personal_forward_disconnect_pending(user_id):
    pending = PERSONAL_FORWARD_PENDING.pop(str(user_id), None)
    client = pending.get("client") if pending else None
    if client:
        try:
            await client.disconnect()
        except Exception:
            pass


async def validate_free_forward_token(token):
    async with Bot(token=token) as connected_bot:
        return await connected_bot.get_me()


def personal_forward_available():
    return personal_auth_available()


def personal_forward_connection(user_id):
    return PERSONAL_FORWARD_CONNECTIONS.get(str(user_id), {})


def personal_forward_connected(user_id):
    return bool(personal_forward_connection(user_id).get("session"))


def personal_forward_display_name(me):
    username = getattr(me, "username", None)
    if username:
        return f"@{username}"
    first = getattr(me, "first_name", None) or ""
    last = getattr(me, "last_name", None) or ""
    name = f"{first} {last}".strip()
    return name or str(getattr(me, "id", "Telegram account"))


async def personal_forward_client(connection):
    client = TelegramClient(
        StringSession(connection.get("session") or ""),
        int(connection.get("api_id")),
        connection.get("api_hash") or "",
    )
    await client.connect()
    return client


def personal_forward_dialog_peer_id(entity):
    if telethon_utils:
        return str(telethon_utils.get_peer_id(entity))
    return str(getattr(entity, "id", ""))


async def list_personal_forward_dialogs(connection, limit=PERSONAL_FORWARD_DIALOG_FETCH_LIMIT):
    dialogs = []
    client = await personal_forward_client(connection)
    try:
        if not await client.is_user_authorized():
            raise RuntimeError("personal account session expired")
        async for dialog in client.iter_dialogs(limit=limit):
            if not (getattr(dialog, "is_group", False) or getattr(dialog, "is_channel", False)):
                continue
            entity = getattr(dialog, "entity", None)
            if not entity:
                continue
            peer_id = personal_forward_dialog_peer_id(entity)
            if not peer_id:
                continue
            username = getattr(entity, "username", None)
            title = getattr(dialog, "title", None) or getattr(entity, "title", None) or username or peer_id
            dialogs.append({
                "id": peer_id,
                "title": title,
                "username": username,
                "type": "channel" if getattr(dialog, "is_channel", False) else "group",
            })
    finally:
        await client.disconnect()
    return dialogs


async def personal_forward_store_connection(user_id, client, api_id, api_hash):
    me = await client.get_me()
    session = client.session.save()
    PERSONAL_FORWARD_CONNECTIONS[str(user_id)] = {
        "session": session,
        "api_id": str(api_id),
        "api_hash": api_hash,
        "display_name": personal_forward_display_name(me),
        "account_id": str(getattr(me, "id", "")),
    }
    return me


async def free_forward_message_spec(update, context):
    message = update.message
    text = (getattr(message, "text", None) or getattr(message, "caption", None) or "").strip()
    if getattr(message, "text", None):
        return {"type": "text", "text": text}

    media = None
    media_type = None
    filename = None
    if getattr(message, "photo", None):
        media = message.photo[-1]
        media_type = "photo"
        filename = "photo.jpg"
    elif getattr(message, "video", None):
        media = message.video
        media_type = "video"
        filename = getattr(media, "file_name", None) or "video.mp4"
    elif getattr(message, "document", None):
        media = message.document
        media_type = "document"
        filename = getattr(media, "file_name", None) or "document"
    elif getattr(message, "animation", None):
        media = message.animation
        media_type = "animation"
        filename = getattr(media, "file_name", None) or "animation.gif"
    elif getattr(message, "audio", None):
        media = message.audio
        media_type = "audio"
        filename = getattr(media, "file_name", None) or "audio"
    elif getattr(message, "voice", None):
        media = message.voice
        media_type = "voice"
        filename = "voice.ogg"
    elif getattr(message, "sticker", None):
        media = message.sticker
        media_type = "sticker"
        filename = "sticker.webp"

    if not media or not media_type:
        return None
    buffer = BytesIO()
    tg_file = await context.bot.get_file(media.file_id)
    await tg_file.download_to_memory(buffer)
    return {"type": media_type, "bytes": buffer.getvalue(), "caption": text, "filename": filename}


async def send_free_forward_message(connected_bot, target, spec):
    message_type = spec.get("type")
    if message_type == "text":
        await connected_bot.send_message(chat_id=target, text=spec.get("text") or "")
        return
    data = BytesIO(spec.get("bytes") or b"")
    data.name = spec.get("filename") or "message"
    caption = spec.get("caption") or None
    if message_type == "photo":
        await connected_bot.send_photo(chat_id=target, photo=data, caption=caption)
    elif message_type == "video":
        await connected_bot.send_video(chat_id=target, video=data, caption=caption)
    elif message_type == "document":
        await connected_bot.send_document(chat_id=target, document=data, caption=caption)
    elif message_type == "animation":
        await connected_bot.send_animation(chat_id=target, animation=data, caption=caption)
    elif message_type == "audio":
        await connected_bot.send_audio(chat_id=target, audio=data, caption=caption)
    elif message_type == "voice":
        await connected_bot.send_voice(chat_id=target, voice=data, caption=caption)
    elif message_type == "sticker":
        await connected_bot.send_sticker(chat_id=target, sticker=data)
    else:
        raise ValueError("unsupported message type")


async def send_personal_forward_message(client, target, spec):
    message_type = spec.get("type")
    entity_target = int(target) if re.fullmatch(r"-?\d+", str(target)) else target
    entity = await client.get_entity(entity_target)
    if message_type == "text":
        await client.send_message(entity, spec.get("text") or "")
        return
    data = BytesIO(spec.get("bytes") or b"")
    data.name = spec.get("filename") or "message"
    await client.send_file(entity, data, caption=spec.get("caption") or None)


async def free_forward_send_to_targets(token, targets, spec):
    ok = []
    failed = []
    async with Bot(token=token) as connected_bot:
        for target in targets:
            try:
                await send_free_forward_message(connected_bot, target, spec)
                ok.append(target)
            except Exception as exc:
                failed.append((target, safe_free_forward_error(exc)))
    return ok, failed


async def personal_forward_send_to_targets(connection, targets, spec):
    ok = []
    failed = []
    client = await personal_forward_client(connection)
    try:
        if not await client.is_user_authorized():
            raise RuntimeError("personal account session expired")
        for target in targets:
            try:
                await send_personal_forward_message(client, target, spec)
                ok.append(target)
                await asyncio.sleep(PERSONAL_FORWARD_TARGET_DELAY_SECONDS)
            except Exception as exc:
                if FloodWaitError and isinstance(exc, FloodWaitError):
                    failed.append((target, f"Telegram rate limit: wait {getattr(exc, 'seconds', 'some')} seconds"))
                    break
                failed.append((target, safe_free_forward_error(exc)))
    finally:
        await client.disconnect()
    return ok, failed


def free_forward_result_text(lang, ok, failed, scheduled=False, interval_minutes=None):
    lines = []
    if scheduled:
        lines.append(ltext(lang, f"⏰ Scheduled forward started. Interval: {interval_minutes} minute(s).", f"⏰ নির্দিষ্ট সময়ের forward শুরু হয়েছে। Interval: {interval_minutes} মিনিট।"))
    lines.append(ltext(lang, f"✅ Sent: {len(ok)}", f"✅ পাঠানো হয়েছে: {len(ok)}"))
    if failed:
        lines.append(ltext(lang, f"❌ Failed: {len(failed)}", f"❌ ব্যর্থ: {len(failed)}"))
        lines.extend([f"• {target}: {error}" for target, error in failed[:5]])
    if not failed:
        lines.append(ltext(lang, "All targets accepted the message.", "সব target message গ্রহণ করেছে।"))
    return "\n".join(lines)


async def free_forward_schedule_loop(application, user_id, chat_id, lang, token, targets, spec, interval_minutes):
    try:
        while True:
            ok, failed = await free_forward_send_to_targets(token, targets, spec)
            await application.bot.send_message(
                chat_id,
                free_forward_result_text(lang, ok, failed),
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(ltext(lang, "🛑 Stop scheduled forward", "🛑 নির্দিষ্ট সময়ের forward বন্ধ"), callback_data="ff_cancel_schedule")]]),
            )
            await asyncio.sleep(float(interval_minutes) * 60)
    except asyncio.CancelledError:
        raise
    except Exception as exc:
        FREE_FORWARD_TASKS.pop(str(user_id), None)
        error = safe_free_forward_error(exc)
        await application.bot.send_message(chat_id, ltext(lang, f"❌ Scheduled forward stopped: {error}", f"❌ নির্দিষ্ট সময়ের forward বন্ধ হয়েছে: {error}"), reply_markup=free_forward_keyboard(lang, has_token=True, has_schedule=False))


async def personal_forward_schedule_loop(application, user_id, chat_id, lang, connection, targets, spec, interval_minutes):
    try:
        while True:
            ok, failed = await personal_forward_send_to_targets(connection, targets, spec)
            await application.bot.send_message(
                chat_id,
                free_forward_result_text(lang, ok, failed),
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(ltext(lang, "🛑 Stop scheduled forward", "🛑 নির্দিষ্ট সময়ের forward বন্ধ"), callback_data="ff_cancel_schedule")]]),
            )
            await asyncio.sleep(float(interval_minutes) * 60)
    except asyncio.CancelledError:
        raise
    except Exception as exc:
        FREE_FORWARD_TASKS.pop(str(user_id), None)
        error = safe_free_forward_error(exc)
        await application.bot.send_message(
            chat_id,
            ltext(lang, f"❌ Personal scheduled forward stopped: {error}", f"❌ Personal নির্দিষ্ট সময়ের forward বন্ধ হয়েছে: {error}"),
            reply_markup=free_forward_keyboard(lang, free_forward_connected(user_id), False, personal_forward_connected(user_id)),
        )


def free_forward_task_running(user_id):
    task = FREE_FORWARD_TASKS.get(str(user_id))
    return bool(task and not task.done())


def free_forward_cancel_schedule(user_id):
    task = FREE_FORWARD_TASKS.pop(str(user_id), None)
    if task and not task.done():
        task.cancel()
        return True
    return False


def free_forward_connection(user_id):
    return FREE_FORWARD_CONNECTIONS.get(str(user_id), {})


def free_forward_connected(user_id):
    return bool(free_forward_connection(user_id).get("token"))


def get_rate(network="solana"):
    db_rate = get_network_rate(network)
    if db_rate:
        return db_rate
    if os.path.exists(RATE_FILE):
        with open(RATE_FILE, encoding="utf-8") as file:
            return float(json.load(file).get("rate", RATE))
    return float(RATE)


def get_star_rate(network="solana"):
    env_key = f"STAR_RATE_{network.upper()}"
    return float(os.getenv(env_key, STAR_RATE))


def get_all_rates():
    return {net: get_rate(net) for net in NETWORKS}


def gen_code(length=8):
    chars = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(chars) for _ in range(length))


def gen_timestamp_id(prefix="STAR"):
    return f"{prefix}_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{gen_code(6)}"


def wallet_hint(network):
    if network == "solana":
        return "8Qvz2XBZ821N7fkT6DxPGs..."
    if network == "trc20":
        return "TXyz1234..."
    if network == "ton":
        return "UQCd... or EQCd..."
    return "0x1234abcd..."


def valid_wallet(network, wallet):
    if network == "solana":
        return 32 <= len(wallet) <= 44
    if network == "trc20":
        return wallet.startswith("T") and len(wallet) == 34
    if network == "ton":
        return (wallet.startswith("UQ") or wallet.startswith("EQ")) and 48 <= len(wallet) <= 60
    return wallet.startswith("0x") and len(wallet) == 42


SELLER_BADGES = {"new": "🆕 New", "verified": "✅ Verified", "trusted": "⭐ Trusted"}


def detect_language(text, current=None):
    text = text or ""
    bn_chars = sum(1 for ch in text if "\u0980" <= ch <= "\u09ff")
    ascii_letters = sum(1 for ch in text if ch.isascii() and ch.isalpha())
    if bn_chars >= 2:
        return "bn"
    if ascii_letters >= 8 and bn_chars == 0:
        return "en"
    return current or "bn"


def maybe_update_language(user_id, text):
    current = user_lang(user_id)
    if text and len(text.strip()) >= 6:
        ident_pattern = r"^(ORD|STAR|SO|PAY|TEST|REFWD|GIFT|SL|RES|AUD|ST|RWD)[-_][A-Z0-9_]{4,48}$"
        clean_text = text.strip().upper()
        if re.match(ident_pattern, clean_text):
            return current
    detected = detect_language(text, current)
    if detected != current:
        set_user_language(user_id, detected)
    return detected


def seller_badge(user_id=None):
    row = get_seller_status(user_id or ADMIN_ID)
    status = row[1] if row else "new"
    return SELLER_BADGES.get(status, SELLER_BADGES["new"])


def low_balance_threshold(network):
    value = get_setting(f"low_balance_threshold_{network}") or os.getenv(f"LOW_BALANCE_THRESHOLD_{network.upper()}")
    try:
        return float(value) if value is not None else float(LOW_BALANCE_THRESHOLD)
    except Exception:
        return float(LOW_BALANCE_THRESHOLD)


def balance_warning_lines(balances):
    lines = []
    for network, info in NETWORKS.items():
        bal = balances.get(network)
        threshold = low_balance_threshold(network)
        if bal is not None and float(bal) < threshold:
            lines.append(f"⚠️ Your {info['name']} balance is low. Orders may fail. Stock: {bal} {info['symbol']} (threshold {threshold}).")
    return lines


def stock_detail(network, amount, current_bal):
    info = NETWORKS.get(network, {"name": network, "symbol": "?"})
    if current_bal is None:
        return f"⚠️ {info['name']} stock could not be checked."
    reserved = get_active_reserved_amount(network)
    reserve_line = f"\n🔒 Reserved: {round(reserved, 6)} {info['symbol']}" if reserved else ""
    return f"📦 Stock available after reserves: {current_bal} {info['symbol']}{reserve_line}\nNeed: {amount} {info['symbol']}."


def gas_status_text():
    balances = get_native_gas_balances()
    lines = ["⛽ Gas Monitor", DIVIDER]
    for network, info in NETWORKS.items():
        symbol, _threshold = GAS_META.get(network, ("native", 0))
        balance = balances.get(network)
        label = info["name"]
        value = "N/A" if balance is None else balance
        lines.append(f"ℹ️ {label}: {value} {symbol}")
    return "\n".join(lines)


def reservations_text():
    rows = list_stock_reservations("active", 30)
    totals = {}
    for row in rows:
        _rid, _oid, _trx, _uid, _seller, network, amount, *_ = row
        totals[network] = totals.get(network, 0) + float(amount or 0)
    lines = ["📦 Active Reservations", DIVIDER]
    if totals:
        lines.append("Totals:")
        for network, amount in totals.items():
            ni = NETWORKS.get(network, {"name": network, "symbol": "?"})
            lines.append(f"• {ni['name']}: {round(amount, 6)} {ni['symbol']}")
        lines.append(DIVIDER)
    if not rows:
        lines.append("✅ No active reservations.")
    for rid, oid, trx, uid, _seller, network, amount, status, reason, created, expires, _updated in rows[:20]:
        ni = NETWORKS.get(network, {"name": network, "symbol": "?"})
        lines.append(f"🔒 {rid}\n🧾 {oid or 'N/A'} | 🔑 {trx or 'waiting'}\n👤 {uid} | {amount} {ni['symbol']} on {ni['name']}\n⏰ expires {str(expires)[:16]} | {reason or status}")
    return "\n".join(lines)


def audit_text(limit=20):
    rows = list_audit(limit)
    if not rows:
        return panel("🧾 Audit Log", "No audit events yet.")
    lines = []
    for _aid, actor, action, target_type, target_id, details, created in rows:
        lines.append(f"{str(created)[:16]} | {actor} | {action}\n{target_type or '-'}:{target_id or '-'} {details or ''}")
    return panel("🧾 Audit Log", f"\n{DIVIDER}\n".join(lines))


def profit_text(period="daily"):
    data = get_profit_summary(period)
    count, sale_bdt, crypto, profit, margin = data["overall"]
    lines = [f"💹 Profit Summary ({period})", DIVIDER, f"✅ Completed: {count or 0}", f"💰 Sales: {round(sale_bdt or 0, 2)} BDT", f"💵 Crypto: {round(crypto or 0, 6)}", f"📈 Profit: {round(profit or 0, 2)} BDT", f"📊 Margin: {round(margin or 0, 2)}%", DIVIDER]
    for network, n_count, bdt, vol, net_profit, net_margin in data["by_network"]:
        ni = NETWORKS.get(network, {"name": network, "symbol": "?"})
        lines.append(f"• {ni['name']}: {n_count} orders, {round(net_profit or 0, 2)} BDT profit, {round(net_margin or 0, 2)}%")
    rates = get_all_cost_rates(NETWORKS.keys())
    lines.append(DIVIDER)
    lines.append("Cost rates: " + ", ".join(f"{net}={rate}" for net, rate in rates.items() if rate))
    return "\n".join(lines)


def webhook_health_text():
    health = get_webhook_health()
    last = health.get("last_notice_at")
    source = health.get("source") or "unknown"
    trx = health.get("trx_id") or "N/A"
    if not last:
        age = "unknown"
        active = "❔ unknown/stale"
    else:
        try:
            dt = datetime.fromisoformat(str(last))
            minutes = int((datetime.now() - dt).total_seconds() // 60)
            age = f"{minutes} min ago"
            active = "✅ active" if minutes <= WEBHOOK_STALE_MINUTES else "⚠️ stale"
        except Exception:
            age = str(last)
            active = "❔ unknown"
    return panel("🩺 Webhook Health", f"Status: {active}\nLast bKash notice received: {age}\nSource: {source}\nLast TrxID: {trx}\nWindow: {WEBHOOK_STALE_MINUTES} minutes")


def restart_help_text():
    commands = """cd ~/mouno
git pull origin main
source .venv/bin/activate
python -m py_compile bot.py db.py balance.py webhook.py config.py
kill $(cat bot.pid) 2>/dev/null || true
pkill -f "python.*bot.py" 2>/dev/null || true
nohup .venv/bin/python bot.py > bot.out 2>&1 &
echo $! > bot.pid
sleep 5
tail -50 bot.out"""
    return (
        "♻️ Safe Restart Guide\n"
        f"{DIVIDER}\n"
        "⚠️ Bot থেকে restart command execute করা হবে না; safety guide only.\n"
        "✅ Restart করার আগে অবশ্যই `git pull origin main` চালান।\n"
        "❌ `py_compile` fail করলে bot start করবেন না; আগে error fix করুন।\n"
        "✅ Start এর পর `bot.out` এ `Bot started!` বা polling/webhook logs দেখা উচিত।\n\n"
        f"```bash\n{commands}\n```"
    )


def bot_health_text():
    lines = ["🟢 Bot Health", DIVIDER, f"🕒 Now: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"]
    try:
        maintenance = get_setting("maintenance_mode", "off") or "off"
        lines.append(f"🛠️ Maintenance: {maintenance.upper()}")
    except Exception as exc:
        lines.append(f"🛠️ Maintenance: error {type(exc).__name__}")
    try:
        from db import DB_PATH

        get_setting("health_check", "ok")
        get_webhook_health()
        lines.append(f"🗄️ DB: {'✅ OK' if os.path.exists(DB_PATH) else '⚠️ file missing'}")
    except Exception as exc:
        lines.append(f"🗄️ DB: ❌ {type(exc).__name__}")
    lines.extend([
        f"📞 Support: @{SUPPORT_USERNAME.lstrip('@')}",
        f"☁️ Backup upload: {'✅ yes' if BACKUP_UPLOAD_URL else '❌ no'}",
        f"🔐 Seller master key: {'✅ yes' if SELLER_WALLET_MASTER_KEY else '❌ no'}",
        DIVIDER,
    ])
    try:
        health = get_webhook_health()
        last = health.get("last_notice_at")
        source = health.get("source") or "unknown"
        trx = health.get("trx_id") or "N/A"
        if last:
            try:
                dt = datetime.fromisoformat(str(last))
                minutes = int((datetime.now() - dt).total_seconds() // 60)
                active = "✅ active" if minutes <= WEBHOOK_STALE_MINUTES else "⚠️ stale"
                age = f"{minutes} min ago"
            except Exception:
                active = "❔ unknown"
                age = str(last)
        else:
            active = "❔ unknown/stale"
            age = "unknown"
        lines.append(f"🩺 Webhook: {active} | {age} | {source} | {trx} | {WEBHOOK_STALE_MINUTES}m")
    except Exception as exc:
        lines.append(f"🩺 Webhook: ❌ {type(exc).__name__}")
    try:
        sources = ai_provider_key_sources()
        configured = [(p, src) for p, (_key, src) in sources.items() if src]
        summary = ", ".join(f"{AI_PROVIDER_LABELS[p]}:{src}" for p, src in configured) or "none"
        lines.append(f"🤖 AI: {len(configured)}/{len(sources)} configured | {summary}")
    except Exception as exc:
        lines.append(f"🤖 AI: ❌ {type(exc).__name__}")
    lines.append(DIVIDER)
    try:
        balances, _evm_addr = get_all_balances()
        warnings = balance_warning_lines(balances)
        if warnings:
            lines.append(f"📦 Stock: ⚠️ {len(warnings)} warning(s)")
            lines.extend(warnings[:5])
            if len(warnings) > 5:
                lines.append(f"…+{len(warnings) - 5} more")
        else:
            lines.append("📦 Stock: ✅ Stock OK")
    except Exception as exc:
        lines.append(f"📦 Stock: ❌ {type(exc).__name__}")
    try:
        gas_balances = get_native_gas_balances()
        gas_lines = []
        for network, info in NETWORKS.items():
            symbol, _threshold = GAS_META.get(network, ("native", 0))
            balance = gas_balances.get(network)
            value = "N/A" if balance is None else balance
            gas_lines.append(f"{info['name']}: {value} {symbol}")
        lines.append("⛽ Gas: info only")
        lines.extend(gas_lines[:5])
        if len(gas_lines) > 5:
            lines.append(f"…+{len(gas_lines) - 5} more")
    except Exception as exc:
        lines.append(f"⛽ Gas: ❌ {type(exc).__name__}")
    return "\n".join(lines)


def receipt_block(order_id, trx_id, network, amount, wallet, sig, seller_id=None):
    info = NETWORKS.get(network or "solana", {"name": network or "N/A", "symbol": "?", "explorer": ""})
    tx_line = f"🔗 TX: {info.get('explorer', '')}{sig}" if sig else "🔗 TX: N/A"
    return (
        "✅ Receipt\n"
        f"🧾 Order: {order_id or 'N/A'}\n"
        f"🌐 Network: {info['name']}\n"
        f"💵 Amount: {amount} {info['symbol']}\n"
        f"👛 Wallet: {short_wallet(wallet)}\n"
        f"🔑 TrxID: {trx_id or 'N/A'}\n"
        f"🏷 Seller: {seller_badge(seller_id)}\n"
        f"👤 Seller profile: /seller {seller_id or ADMIN_ID}\n"
        f"{tx_line}"
    )


def receipt_value(value, default="N/A"):
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def receipt_amount(value):
    if value is None or value == "":
        return None
    try:
        number = float(value)
        if number == 0:
            return "0"
        return f"{number:.8f}".rstrip("0").rstrip(".")
    except Exception:
        return str(value)


def receipt_explorer_url(network, sig):
    info = NETWORKS.get(network or "solana", {"explorer": ""})
    return f"{info.get('explorer', '')}{sig}" if sig else ""


def receipt_chat_id(chat_id):
    if chat_id is None or str(chat_id).strip() == "":
        return None
    text = str(chat_id).strip()
    try:
        return int(text)
    except Exception:
        return text


def receipt_user_label(username=None, name=None, user_id=None):
    username = receipt_value(username, "")
    name = receipt_value(name, "")
    if username:
        username = username if username.startswith("@") else f"@{username}"
    label = username or name or "N/A"
    return f"{label} ({receipt_value(user_id)})"


async def chat_display(bot, user_id, fallback_username=None, fallback_name=None):
    username = fallback_username
    name = fallback_name
    try:
        chat = await bot.get_chat(int(user_id))
        username = getattr(chat, "username", None) or username
        first = getattr(chat, "first_name", None) or ""
        last = getattr(chat, "last_name", None) or ""
        full = " ".join(part for part in [first, last] if part).strip()
        name = full or getattr(chat, "title", None) or name
    except Exception as exc:
        logger.debug("Could not load chat display for %s: %s", user_id, exc)
    return receipt_user_label(username, name, user_id)


async def make_receipt_data(bot, order_id, payment_id, network, crypto_amount, wallet, sig, buyer_id, buyer_username=None, seller_id=None, seller_username=None, seller_name=None, bdt_amount=None, stars_amount=None, title="Smart Crypto Buy"):
    seller_id = seller_id or ADMIN_ID
    if str(seller_id) == str(ADMIN_ID) and not seller_name:
        seller_name = "Main Admin"
    info = NETWORKS.get(network or "solana", {"name": network or "N/A", "symbol": "?", "explorer": ""})
    return {
        "title": title,
        "status": "SUCCESSFUL / COMPLETED",
        "order_id": order_id,
        "payment_id": payment_id,
        "network": network,
        "network_name": info["name"],
        "crypto_symbol": info["symbol"],
        "crypto_amount": crypto_amount,
        "bdt_amount": bdt_amount,
        "stars_amount": stars_amount,
        "buyer_id": buyer_id,
        "buyer_username": buyer_username,
        "buyer_label": await chat_display(bot, buyer_id, buyer_username),
        "seller_id": seller_id,
        "seller_username": seller_username,
        "seller_name": seller_name,
        "seller_label": await chat_display(bot, seller_id, seller_username, seller_name),
        "wallet": wallet,
        "tx_hash": sig,
        "explorer_url": receipt_explorer_url(network, sig),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def receipt_text_from_data(data):
    network = data.get("network")
    info = NETWORKS.get(network or "solana", {"name": network or "N/A", "symbol": data.get("crypto_symbol") or "?", "explorer": ""})
    sig = data.get("tx_hash") or data.get("signature")
    explorer = data.get("explorer_url") or receipt_explorer_url(network, sig)
    lines = [
        f"✅ {data.get('title') or 'Smart Crypto Buy'} Receipt",
        f"📌 Status: {data.get('status') or 'Completed'}",
        f"🧾 Order: {data.get('order_id') or 'N/A'}",
        f"🔑 Payment ID: {data.get('payment_id') or 'N/A'}",
        f"🌐 Network: {info['name']}",
        f"💵 Amount: {receipt_amount(data.get('crypto_amount')) or 'N/A'} {data.get('crypto_symbol') or info['symbol']}",
    ]
    if data.get("bdt_amount") is not None:
        lines.append(f"💰 BDT: {receipt_amount(data.get('bdt_amount'))} BDT")
    if data.get("stars_amount") is not None:
        lines.append(f"⭐ Stars: {receipt_amount(data.get('stars_amount'))} Stars")
    lines.extend([
        f"👤 Buyer: {data.get('buyer_label') or receipt_user_label(data.get('buyer_username'), data.get('buyer_name'), data.get('buyer_id'))}",
        f"🏪 Seller: {data.get('seller_label') or receipt_user_label(data.get('seller_username'), data.get('seller_name'), data.get('seller_id'))}",
        f"👛 Wallet: {short_wallet(data.get('wallet'))}",
        f"🔗 TX: {explorer or 'N/A'}",
        f"🕒 Timestamp: {data.get('timestamp') or datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
    ])
    return "\n".join(lines)


def load_receipt_font(size, names):
    from PIL import ImageFont
    for name in names:
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            pass
    return ImageFont.load_default()


def receipt_font(size, bold=False):
    return load_receipt_font(size, [
        os.path.join(RECEIPT_FONT_DIR, "NotoSans-Bold.ttf" if bold else "NotoSans-Regular.ttf"),
        "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ])


def receipt_bengali_font(size, bold=False):
    return load_receipt_font(size, [
        os.path.join(RECEIPT_FONT_DIR, "NotoSansBengali-Bold.ttf" if bold else "NotoSansBengali-Regular.ttf"),
        "/usr/share/fonts/truetype/noto/NotoSansBengali-Bold.ttf" if bold else "/usr/share/fonts/truetype/noto/NotoSansBengali-Regular.ttf",
        os.path.join(RECEIPT_FONT_DIR, "NotoSans-Bold.ttf" if bold else "NotoSans-Regular.ttf"),
        "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
    ])


def receipt_image_text(value):
    text = receipt_value(value, "")
    cleaned = []
    for ch in text:
        category = unicodedata.category(ch)
        if category in {"Cc", "Cf", "Cs", "Co", "Cn", "So"}:
            continue
        cleaned.append(ch)
    return "".join(cleaned) or "N/A"


def draw_receipt_text(draw, xy, text, font, fill, max_width, line_gap=6):
    x, y = xy
    lines = []
    current = ""

    def split_long_token(token):
        chunks = []
        chunk = ""
        for ch in token:
            candidate = f"{chunk}{ch}"
            if draw.textlength(candidate, font=font) <= max_width or not chunk:
                chunk = candidate
            else:
                chunks.append(chunk)
                chunk = ch
        if chunk:
            chunks.append(chunk)
        return chunks or [""]

    for word in str(text).split():
        pieces = split_long_token(word) if draw.textlength(word, font=font) > max_width else [word]
        for piece in pieces:
            candidate = f"{current} {piece}".strip()
            if draw.textlength(candidate, font=font) <= max_width or not current:
                current = candidate
            else:
                lines.append(current)
                current = piece
    if current:
        lines.append(current)
    if not lines:
        lines = [""]
    for line in lines:
        draw.text((x, y), line, font=font, fill=fill)
        y += font.size + line_gap
    return y


def paste_receipt_seal(image):
    from PIL import Image, ImageDraw
    seal_size = 190
    x = image.width - seal_size - 70
    y = 70
    seal = Image.new("RGBA", (seal_size, seal_size), (0, 0, 0, 0))
    mask = Image.new("L", (seal_size, seal_size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.ellipse((0, 0, seal_size - 1, seal_size - 1), fill=150)
    if os.path.exists(RECEIPT_LOGO_PATH):
        logo = Image.open(RECEIPT_LOGO_PATH).convert("RGBA")
        side = min(logo.size)
        left = (logo.width - side) // 2
        top = (logo.height - side) // 2
        logo = logo.crop((left, top, left + side, top + side)).resize((seal_size, seal_size))
        logo.putalpha(mask)
        seal.alpha_composite(logo)
    else:
        seal_draw = ImageDraw.Draw(seal)
        seal_draw.ellipse((0, 0, seal_size - 1, seal_size - 1), fill=(129, 72, 40, 42))
        seal_draw.text((seal_size // 2 - 48, seal_size // 2 - 12), "MOUNO", fill=(129, 72, 40, 145), font=receipt_font(24, True))
    seal_draw = ImageDraw.Draw(seal)
    seal_draw.ellipse((6, 6, seal_size - 7, seal_size - 7), outline=(129, 72, 40, 190), width=5)
    seal_draw.ellipse((20, 20, seal_size - 21, seal_size - 21), outline=(129, 72, 40, 110), width=2)
    image.alpha_composite(seal, (x, y))


def receipt_qr_payload(data):
    network = data.get("network")
    sig = data.get("tx_hash") or data.get("signature")
    explorer = receipt_value(data.get("explorer_url"), "")
    if not explorer:
        generated = receipt_explorer_url(network, sig)
        if str(generated).startswith(("http://", "https://")):
            explorer = generated
    if explorer:
        return explorer, "Transaction proof link"

    info = NETWORKS.get(network or "solana", {"name": network or "N/A", "symbol": data.get("crypto_symbol") or "?", "explorer": ""})
    wallet = receipt_value(data.get("wallet"))
    tx = receipt_value(sig, "")
    parts = [
        f"order={receipt_value(data.get('order_id'))}",
        f"payment={receipt_value(data.get('payment_id'))}",
        f"network={receipt_value(network or info.get('name'))}",
        f"amount={receipt_amount(data.get('crypto_amount')) or 'N/A'} {data.get('crypto_symbol') or info.get('symbol') or '?'}",
        f"wallet={short_wallet(wallet)}",
    ]
    if tx:
        parts.append(f"tx={short_wallet(tx)}")
    parts.append(f"time={receipt_value(data.get('timestamp'))}")
    return "Mouno receipt|" + "|".join(parts), "Encoded receipt details"


def build_receipt_qr(data, size=190):
    import qrcode
    from PIL import Image
    payload, detail_label = receipt_qr_payload(data)
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=8, border=2)
    qr.add_data(payload)
    qr.make(fit=True)
    qr_image = qr.make_image(fill_color=(63, 39, 28), back_color=(255, 252, 242)).convert("RGBA")
    qr_image = qr_image.resize((size, size), Image.Resampling.NEAREST)
    return qr_image, detail_label


def paste_receipt_qr(image, data, top=1060):
    from PIL import ImageDraw
    draw = ImageDraw.Draw(image)
    box = (705, top, image.width - 90, top + 290)
    draw.rounded_rectangle(box, radius=28, fill=(255, 252, 242, 245), outline=(184, 137, 82, 220), width=3)
    qr_image, detail_label = build_receipt_qr(data, size=170)
    content_width = box[2] - box[0] - 44
    center_x = (box[0] + box[2]) // 2

    label_font = receipt_font(24, True)
    label = "Scan for proof"
    label_width = draw.textlength(label, font=label_font)
    draw.text((center_x - label_width / 2, box[1] + 22), label, font=label_font, fill=(63, 39, 28, 255))

    qr_x = center_x - qr_image.width // 2
    qr_y = box[1] + 64
    image.alpha_composite(qr_image, (qr_x, qr_y))

    detail_font = receipt_font(19)
    detail_width = min(draw.textlength(detail_label, font=detail_font), content_width)
    if detail_width == draw.textlength(detail_label, font=detail_font):
        draw.text((center_x - detail_width / 2, box[1] + 246), detail_label, font=detail_font, fill=(129, 72, 40, 230))
    else:
        draw_receipt_text(draw, (box[0] + 22, box[1] + 242), detail_label, detail_font, (129, 72, 40, 230), content_width, 2)


def build_receipt_image(data):
    from PIL import Image, ImageDraw
    width, height = 1100, 1750
    image = Image.new("RGBA", (width, height), (246, 238, 220, 255))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((45, 45, width - 45, height - 45), radius=36, fill=(255, 252, 242, 255), outline=(184, 137, 82, 255), width=4)
    for y in range(90, height - 80, 70):
        draw.line((70, y, width - 70, y), fill=(231, 216, 190, 75), width=1)
    paste_receipt_seal(image)

    title_font = receipt_font(54, True)
    status_font = receipt_font(30, True)
    label_font = receipt_font(25, True)
    value_font = receipt_font(29)
    small_font = receipt_font(23)
    title = receipt_image_text(data.get("title") or "Smart Crypto Buy")
    draw.text((80, 78), title, font=title_font, fill=(63, 39, 28, 255))
    status_text = "COMPLETED"
    status_width = int(draw.textlength(status_text, font=status_font))
    draw.rounded_rectangle((82, 155, 122 + status_width, 205), radius=20, fill=(31, 129, 73, 255))
    draw.text((105, 163), status_text, font=status_font, fill=(255, 255, 255, 255))
    draw.text((80, 225), f"Generated: {data.get('timestamp') or datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", font=small_font, fill=(113, 95, 76, 255))

    network = data.get("network")
    info = NETWORKS.get(network or "solana", {"name": network or "N/A", "symbol": data.get("crypto_symbol") or "?", "explorer": ""})
    sig = data.get("tx_hash") or data.get("signature")
    explorer = data.get("explorer_url") or receipt_explorer_url(network, sig)
    rows = [
        ("Order ID", data.get("order_id") or "N/A"),
        ("Payment / Transaction ID", data.get("payment_id") or "N/A"),
        ("Network", f"{info['name']} ({data.get('crypto_symbol') or info['symbol']})"),
        ("Crypto Amount", f"{receipt_amount(data.get('crypto_amount')) or 'N/A'} {data.get('crypto_symbol') or info['symbol']}"),
    ]
    if data.get("bdt_amount") is not None:
        rows.append(("BDT Amount", f"{receipt_amount(data.get('bdt_amount'))} BDT"))
    if data.get("stars_amount") is not None:
        rows.append(("Stars Amount", f"{receipt_amount(data.get('stars_amount'))} Stars"))
    rows.extend([
        ("Buyer", data.get("buyer_label") or receipt_user_label(data.get("buyer_username"), data.get("buyer_name"), data.get("buyer_id"))),
        ("Seller", data.get("seller_label") or receipt_user_label(data.get("seller_username"), data.get("seller_name"), data.get("seller_id"))),
        ("Destination Wallet", short_wallet(data.get("wallet"))),
        ("Transaction Hash / Signature", sig or "N/A"),
        ("Explorer URL", explorer or "N/A"),
    ])

    y = 315
    qr_pasted = False
    proof_column_labels = {"Transaction Hash / Signature", "Explorer URL"}
    for label, value in rows:
        reserve_proof_column = label in proof_column_labels
        if reserve_proof_column and not qr_pasted:
            paste_receipt_qr(image, data, max(y + 18, 1060))
            qr_pasted = True
        max_width = width - 180
        if reserve_proof_column:
            max_width = 570
        draw.text((90, y), receipt_image_text(label).upper(), font=label_font, fill=(129, 72, 40, 255))
        y = draw_receipt_text(draw, (90, y + 34), receipt_image_text(value), value_font, (35, 35, 35, 255), max_width)
        y += 24
        line_end = 660 if reserve_proof_column else width - 90
        draw.line((90, y, line_end, y), fill=(224, 203, 171, 160), width=2)
        y += 24

    draw.rounded_rectangle((120, height - 135, width - 120, height - 78), radius=24, outline=(129, 72, 40, 160), width=3)
    draw.text((155, height - 120), "এই রিসিপ্টটি সফল ট্রাঞ্জেকশনের স্বয়ংক্রিয় প্রমাণ", font=receipt_bengali_font(28), fill=(129, 72, 40, 220))
    output = BytesIO()
    image.convert("RGB").save(output, format="PNG", optimize=True)
    output.seek(0)
    output.name = f"receipt-{receipt_value(data.get('order_id'), 'order')}.png"
    return output


async def send_transaction_receipt(bot, recipients, receipt_data):
    sent = set()
    try:
        loop = asyncio.get_running_loop()
        photo_bytes = await loop.run_in_executor(None, lambda: build_receipt_image(receipt_data).getvalue())
    except Exception as exc:
        logger.exception("Receipt image generation failed: %s", exc)
        photo_bytes = None
    for recipient in recipients:
        chat_id = receipt_chat_id(recipient)
        if chat_id is None:
            continue
        key = str(chat_id)
        if key in sent:
            continue
        sent.add(key)
        try:
            if photo_bytes is None:
                raise RuntimeError("receipt image unavailable")
            with tempfile.NamedTemporaryFile(suffix=".png") as temp_file:
                temp_file.write(photo_bytes)
                temp_file.flush()
                with open(temp_file.name, "rb") as file:
                    await bot.send_photo(chat_id=chat_id, photo=file)
        except Exception as exc:
            logger.exception("Receipt photo delivery failed for %s: %s", chat_id, exc)
            try:
                await bot.send_message(chat_id, receipt_text_from_data(receipt_data))
            except Exception as fallback_exc:
                logger.warning("Receipt fallback text delivery failed for %s: %s", chat_id, fallback_exc)


def order_status_text(identifier, viewer_id, lang="bn"):
    kind, row = find_order(identifier)
    if not row:
        seller_order = get_seller_order(normalize_order_context_identifier(identifier))
        if not seller_order:
            return "❌ Order/TrxID পাওয়া যায়নি।" if lang == "bn" else "❌ Order/TrxID not found."
        order_id, seller_id, buyer_id, _buyer_username, method, trx_id, network, wallet, amount_bdt, amount_crypto, stars_amount, status, tx_sig, error, created, updated = seller_order
        admin = is_admin(viewer_id)
        if not admin and str(viewer_id) not in {str(buyer_id), str(seller_id)}:
            return "🚫 এই অর্ডার দেখার অনুমতি নেই।" if lang == "bn" else "🚫 You can only view your own order."
        info = NETWORKS.get(network or "solana", {"name": network, "symbol": "?", "explorer": ""})
        hint = error or ("Seller is verifying/payment delivery is pending." if status in {"waiting_payment", "pending_manual", "paid"} else "Seller order processed.")
        link = f"\n🔗 {info.get('explorer', '')}{tx_sig}" if tx_sig else ""
        payment = f"\n💰 BDT: {amount_bdt}" if method == "bkash" else f"\n⭐ Stars: {stars_amount}"
        return panel("🔎 Seller Order Status", f"Status: {status}\n🧾 Order: {order_id}\n🔑 TrxID: {trx_id or 'N/A'}\n🌐 {info['name']}{payment}\n💵 Amount: {amount_crypto} {info['symbol']}\n👛 Wallet: {short_wallet(wallet)}\n🏷 Seller: {seller_badge(seller_id)}\n🕒 Created: {str(created)[:19]}\n♻️ Updated: {str(updated)[:19]}\n💡 {hint}{link}")
    admin = is_admin(viewer_id)
    if kind == "transaction":
        trx_id, bdt, crypto, network, wallet, status, created, order_id, user_id, sig = row[:10]
        updated = row[10] if len(row) > 10 and row[10] else created
        if not admin and str(user_id) != str(viewer_id):
            return "🚫 এই অর্ডার দেখার অনুমতি নেই।" if lang == "bn" else "🚫 You can only view your own order."
        info = NETWORKS.get(network or "solana", {"name": network, "symbol": "?", "explorer": ""})
        hint = "✅ Completed. Receipt available with /receipt." if status == "completed" else ("❌ Send failed; admin can retry from /failed." if status == "failed" else "⏳ Processing.")
        link = f"\n🔗 {info.get('explorer', '')}{sig}" if sig else ""
        return panel("🔎 Order Status", f"Status: {status}\n🧾 Order: {order_id or 'N/A'}\n🔑 TrxID: {trx_id}\n🌐 {info['name']}\n💰 BDT: {bdt}\n💵 Amount: {crypto} {info['symbol']}\n👛 Wallet: {short_wallet(wallet)}\n🏷 Seller: {seller_badge()}\n🕒 Created: {str(created)[:19]}\n♻️ Updated: {str(updated)[:19]}\n💡 {hint}{link}")
    if kind == "pending":
        trx_id, user_id, bdt, crypto, wallet, network, created = row[:7]
        order_id = row[7] if len(row) > 7 else None
        updated = row[8] if len(row) > 8 else created
        if not admin and str(user_id) != str(viewer_id):
            return "🚫 এই অর্ডার দেখার অনুমতি নেই।" if lang == "bn" else "🚫 You can only view your own order."
        info = NETWORKS.get(network or "solana", {"name": network, "symbol": "?"})
        return panel("🔎 Order Status", f"Status: pending/manual review\n🧾 Order: {order_id or 'N/A'}\n🔑 TrxID: {trx_id}\n🌐 {info['name']}\n💰 BDT: {bdt}\n💵 Amount: {crypto} {info['symbol']}\n👛 Wallet: {short_wallet(wallet)}\n🕒 Created: {str(created)[:19]}\n♻️ Updated: {str(updated)[:19]}\n💡 bKash notice missing/delayed or manual admin verification required.")
    order_id, user_id, username, network, wallet, amount_crypto, stars_amount, status, _tg, _prov, tx_sig, error, created, updated = row
    if not admin and str(user_id) != str(viewer_id):
        return "🚫 এই অর্ডার দেখার অনুমতি নেই।" if lang == "bn" else "🚫 You can only view your own order."
    info = NETWORKS.get(network or "solana", {"name": network, "symbol": "?", "explorer": ""})
    hint = error or ("Waiting for Stars payment/payout." if status in {"pending", "paid"} else "Stars order processed.")
    link = f"\n🔗 {info.get('explorer', '')}{tx_sig}" if tx_sig else ""
    return panel("🔎 Stars Order Status", f"Status: {status}\n🧾 Order: {order_id}\n⭐ Stars: {stars_amount}\n🌐 {info['name']}\n💵 Amount: {amount_crypto} {info['symbol']}\n👛 Wallet: {short_wallet(wallet)}\n👤 @{username}\n🕒 Created: {str(created)[:19]}\n♻️ Updated: {str(updated)[:19]}\n💡 {hint}{link}")


def order_status_ai_keyboard(identifier, viewer_id, lang="bn", include_menu=True):
    identifier = normalize_order_context_identifier(identifier)
    if not is_order_context_available(identifier, viewer_id):
        return None
    rows = [[InlineKeyboardButton(ltext(lang, "🤖 Ask AI about this order", "🤖 এই order নিয়ে AI-কে জিজ্ঞেস করুন"), callback_data=f"{ORDER_AI_CALLBACK_PREFIX}{identifier}")]]
    if include_menu:
        rows.append([InlineKeyboardButton("🏠 Menu" if lang == "en" else "🏠 মেনু", callback_data="back")])
    return InlineKeyboardMarkup(rows)


def track_order_keyboard(identifier, viewer_id, lang="bn", include_menu=False):
    identifier = normalize_order_context_identifier(identifier)
    if not is_order_context_available(identifier, viewer_id):
        return None
    rows = [[InlineKeyboardButton(ltext(lang, "🔎 Track Order", "🔎 Order Track করুন"), callback_data=f"{TRACK_ORDER_CALLBACK_PREFIX}{identifier}")]]
    if include_menu:
        rows.append([InlineKeyboardButton("🏠 Menu" if lang == "en" else "🏠 মেনু", callback_data="back")])
    return InlineKeyboardMarkup(rows)


def completed_receipt_text(identifier, viewer_id):
    kind, row = find_order(identifier)
    if kind == "transaction" and row:
        trx_id, _bdt, crypto, network, wallet, status, _created, order_id, user_id, sig = row[:10]
        if not is_admin(viewer_id) and str(user_id) != str(viewer_id):
            return "🚫 You can only view your own receipt."
        if status != "completed":
            return "❌ Receipt is available only for completed orders."
        return receipt_block(order_id, trx_id, network, crypto, wallet, sig)
    if kind == "star" and row:
        order_id, user_id, _username, network, wallet, amount_crypto, _stars, status, tg, _prov, tx_sig, *_ = row
        if not is_admin(viewer_id) and str(user_id) != str(viewer_id):
            return "🚫 You can only view your own receipt."
        if status != "completed":
            return "❌ Receipt is available only for completed orders."
        return receipt_block(order_id, f"STAR-{tg or order_id}", network, amount_crypto, wallet, tx_sig)
    return "❌ Completed order not found."


def report_text(period="daily"):
    data = get_report_stats(period)
    total, completed, failed, other, total_bdt, total_crypto, total_profit = data["transactions"]
    top = "\n".join(f"• {NETWORKS.get(net, {'name': net})['name']}: {count} orders, {round(crypto or 0, 6)} crypto, {round(bdt or 0, 2)} BDT" for net, count, crypto, bdt in data["top_networks"]) or "No completed networks."
    stars_count, stars_amount = data["stars_pending"]
    payout_count, payout_amount = data["payouts_pending"]
    ref_credited, ref_withdrawn, ref_liability = data.get("referrals", (0, 0, 0))
    ref_failed = data.get("referral_failed_withdrawals", 0)
    new_users = data.get("new_users", 0)
    return panel("📈 Admin Report", f"Period: {period}\n👥 New users: {new_users}\n🧾 Total orders: {total or 0}\n✅ Completed: {completed or 0}\n❌ Failed: {failed or 0}\n⏳ Pending/other: {(other or 0) + data['pending_orders']}\n💰 Completed BDT volume: {round(total_bdt or 0, 2)}\n💵 Completed crypto volume: {round(total_crypto or 0, 6)}\n💹 Profit: {round(total_profit or 0, 2)} BDT\n⭐ Stars ledger pending payout: {stars_count or 0} orders / {stars_amount or 0} Stars\n💸 Seller payout requests: {payout_count or 0} / {payout_amount or 0}\n👥 Referral liability: {round(ref_liability or 0, 6)} USD | credited {round(ref_credited or 0, 6)} | withdrawn {round(ref_withdrawn or 0, 6)} | failed wd {ref_failed}\n\nTop networks:\n{top}")


def user_analytics_text(user_id, lang="bn"):
    data = get_user_analytics(user_id)
    if not data or not data.get("joined_at"):
        return tr("user_not_found", lang)

    joined_at = str(data["joined_at"])[:16]
    last_order = str(data["last_order_at"])[:16] if data["last_order_at"] else (ltext(lang, "Never", "কখনো নয়"))
    inactive = f"{data['inactive_days']} days" if data["inactive_days"] is not None else "N/A"
    avg_size = f"{data['avg_bdt']} BDT"
    total_spent = f"{data['total_bdt']} BDT"
    fav_net = NETWORKS.get(data["fav_network"], {}).get("name", data["fav_network"]) if data["fav_network"] else "N/A"

    body = ltext(lang,
        f"👤 User: {user_id}\n"
        f"📅 Joined: {joined_at}\n"
        f"🛒 Total Orders: {data['total_orders']}\n"
        f"💰 Total Spent: {total_spent}\n"
        f"📊 Avg Order Size: {avg_size}\n"
        f"🌐 Favorite Network: {fav_net}\n"
        f"🕒 Last Order: {last_order}\n"
        f"💤 Inactive: {inactive}",
        f"👤 ব্যবহারকারী: {user_id}\n"
        f"📅 প্রথম দেখা: {joined_at}\n"
        f"🛒 মোট অর্ডার: {data['total_orders']}\n"
        f"💰 মোট খরচ: {total_spent}\n"
        f"📊 গড় অর্ডারের সাইজ: {avg_size}\n"
        f"🌐 প্রিয় নেটওয়ার্ক: {fav_net}\n"
        f"🕒 শেষ অর্ডার: {last_order}\n"
        f"💤 ইনঅ্যাক্টিভ: {inactive}"
    )
    return panel(tr("user_analytics", lang), body)


def seller_dashboard_text():
    balances, evm_addr = get_all_balances()
    lines = ["🏪 Seller Dashboard", DIVIDER]
    for net, info in NETWORKS.items():
        lines.append(f"{info['name']}: {balances.get(net, 'N/A')} {info['symbol']}")
    warnings = balance_warning_lines(balances)
    lines.append(DIVIDER)
    lines.extend(warnings or ["✅ No low-balance warnings."])
    lines.append(DIVIDER)
    lines.append(webhook_health_text())
    lines.append(DIVIDER)
    lines.append(gas_status_text())
    lines.append(DIVIDER)
    summary = get_profit_summary("daily")["overall"]
    lines.append(f"💹 Today profit: {round(summary[3] or 0, 2)} BDT | Sales: {round(summary[1] or 0, 2)} BDT")
    lines.append(f"🔑 EVM: {short_wallet(evm_addr)}")
    return "\n".join(lines)


def faq_text(lang="bn"):
    if lang == "en":
        body = (
            "1. How do I buy crypto?\n"
            "Choose Buy, select a network, enter your receiving wallet, enter the BDT amount, pay the exact bKash amount, then submit your TrxID.\n\n"
            "2. Which networks are supported?\n"
            "Solana USDC, Polygon USDC, BSC USDT, Avalanche USDT, Ethereum USDT/USDC, Base USDC, Tron USDT, and TON. Always send the correct wallet for the selected network.\n\n"
            "3. How long does delivery take?\n"
            "Most verified orders are delivered within a few minutes. Delivery can take longer if bKash notice is delayed, the TrxID is wrong, stock is low, or the network/RPC is busy.\n\n"
            "4. What should I check before payment?\n"
            "Confirm the selected network, wallet address, BDT amount, and bKash number before sending payment. Wrong network or wrong wallet transfers cannot be reversed.\n\n"
            "5. What if my order is pending?\n"
            "Save your Order ID and TrxID. Use Order Status, /order ORD-XXXXXX, or /status TRXID. If needed, admin will manually verify the payment.\n\n"
            "6. Can I pay with Telegram Stars?\n"
            "Yes. Choose Telegram Stars, select a network, enter wallet and amount, then complete the Telegram invoice.\n\n"
            "7. Where can I get help?\n"
            f"Use AI Support for quick guidance or contact @{SUPPORT_USERNAME.lstrip('@')} for manual help. Never share private keys, seed phrases, or wallet passwords."
        )
        return panel("FAQ", body)

    body = (
        "১. Crypto কীভাবে কিনব?\n"
        "Buy চাপুন, network বেছে নিন, receiving wallet দিন, BDT amount লিখুন, exact bKash amount pay করুন, তারপর TrxID submit করুন।\n\n"
        "২. কোন network support করে?\n"
        "Solana USDC, Polygon USDC, BSC USDT, Avalanche USDT, Ethereum USDT/USDC, Base USDC, Tron USDT এবং TON support করে। Selected network অনুযায়ী সঠিক wallet দিন।\n\n"
        "৩. Delivery কত সময় লাগে?\n"
        "Payment verify হলে সাধারণত কয়েক মিনিটের মধ্যে delivery হয়। bKash notice delay, ভুল TrxID, stock কম, অথবা network/RPC busy থাকলে সময় বেশি লাগতে পারে।\n\n"
        "৪. Payment করার আগে কী check করব?\n"
        "Selected network, wallet address, BDT amount এবং bKash number ভালোভাবে মিলিয়ে নিন। ভুল network বা ভুল wallet transfer reverse করা যায় না।\n\n"
        "৫. Order pending থাকলে কী করব?\n"
        "Order ID এবং TrxID সংরক্ষণ করুন। Order Status, /order ORD-XXXXXX অথবা /status TRXID ব্যবহার করুন। দরকার হলে admin manually payment verify করবেন।\n\n"
        "৬. Telegram Stars দিয়ে payment করা যাবে?\n"
        "হ্যাঁ। Telegram Stars বেছে নিন, network select করুন, wallet ও amount দিন, তারপর Telegram invoice complete করুন।\n\n"
        "৭. Help কোথায় পাব?\n"
        f"Quick guidance-এর জন্য AI Support ব্যবহার করুন অথবা manual help-এর জন্য @{SUPPORT_USERNAME.lstrip('@')} এ contact করুন। Private key, seed phrase বা wallet password কখনো share করবেন না।"
    )
    return panel("FAQ", body)


def main_menu(user_id, lang=None):
    lang = lang or user_lang(user_id)
    keyboard = [
        [InlineKeyboardButton(tr("buy", lang), callback_data="buy"), InlineKeyboardButton(tr("swap", lang), callback_data="swap_start")],
        [InlineKeyboardButton(tr("stars", lang), callback_data="star_buy")],
        [InlineKeyboardButton(tr("gift", lang), callback_data="redeem_menu"), InlineKeyboardButton(tr("giveaway", lang), callback_data="giveaway_menu")],
        [InlineKeyboardButton(tr("rate", lang), callback_data="rate"), InlineKeyboardButton(tr("wallet", lang), callback_data="my_wallet_menu")],
        [InlineKeyboardButton(tr("balance", lang), callback_data="balance"), InlineKeyboardButton(tr("txlog", lang), callback_data="txlog")],
        [InlineKeyboardButton(tr("order_status", lang), callback_data="order_status"), InlineKeyboardButton(tr("referral", lang), callback_data="referral_menu")],
        [InlineKeyboardButton(tr("sellers", lang), callback_data="sellers_market"), InlineKeyboardButton(tr("seller_center", lang), callback_data="seller_center")],
        [InlineKeyboardButton(tr("free_service", lang), callback_data="free_service")],
        [InlineKeyboardButton(tr("ai_support", lang), callback_data="ai_support"), InlineKeyboardButton(tr("faq", lang), callback_data="faq")],
        [InlineKeyboardButton(tr("seller_dashboard", lang), callback_data="seller_dashboard")],
        [InlineKeyboardButton(tr("support", lang), url=f"https://t.me/{SUPPORT_USERNAME.lstrip('@')}")],
        [InlineKeyboardButton(tr("terms", lang), callback_data="terms"), InlineKeyboardButton(tr("language", lang), callback_data="language_menu")],
    ]
    if is_admin(user_id):
        keyboard.append([InlineKeyboardButton(tr("set_rate", lang), callback_data="setrate_menu"), InlineKeyboardButton(tr("gen_code", lang), callback_data="gencode_menu")])
        keyboard.append([InlineKeyboardButton(tr("admin_send", lang), callback_data="admin_send"), InlineKeyboardButton(tr("disable_code", lang), callback_data="disable_code_menu")])
        keyboard.append([InlineKeyboardButton("📈 Report", callback_data="admin_report_daily"), InlineKeyboardButton("💾 Backup Now", callback_data="backup_now")])
        keyboard.append([InlineKeyboardButton("🟢 Bot Health", callback_data="bot_health"), InlineKeyboardButton("♻️ Restart Help", callback_data="restart_help")])
        keyboard.append([InlineKeyboardButton("📦 Reserves", callback_data="admin_reservations"), InlineKeyboardButton("💹 Profit", callback_data="admin_profit")])
        keyboard.append([InlineKeyboardButton("⛽ Gas Monitor", callback_data="admin_gas"), InlineKeyboardButton("🧾 Audit Log", callback_data="admin_audit")])
        keyboard.append([InlineKeyboardButton("🏷 Seller Badges", callback_data="seller_badges"), InlineKeyboardButton("🤖 AI Admin", callback_data="ai_admin_help")])
        keyboard.append([InlineKeyboardButton("🤖 AI Status", callback_data="ai_status"), InlineKeyboardButton("⚙️ AI Setup", callback_data="ai_setup")])
        keyboard.append([InlineKeyboardButton("🔁 Swap Status", callback_data="swap_status"), InlineKeyboardButton("🔁 Swap API Setup", callback_data="swap_setup")])
        keyboard.append([InlineKeyboardButton("📊 AI Usage", callback_data="ai_usage"), InlineKeyboardButton(tr("user_analytics", lang), callback_data="admin_user_analytics")])
        keyboard.append([InlineKeyboardButton("🏪 Seller Apps", callback_data="admin_sellers"), InlineKeyboardButton("⭐ Seller Stars", callback_data="seller_payouts")])
        keyboard.append([InlineKeyboardButton("💸 Payouts", callback_data="admin_payouts"), InlineKeyboardButton("👥 Referral Admin", callback_data="referral_admin")])
        keyboard.append([InlineKeyboardButton("🧪 Test Tools", callback_data="test_tools")])
        keyboard.append([InlineKeyboardButton("🛑 Maintenance ON", callback_data="maintenance_on"), InlineKeyboardButton("✅ Maintenance OFF", callback_data="maintenance_off")])
    return InlineKeyboardMarkup(keyboard)


def network_menu(prefix, lang="bn"):
    cancel_callback = {
        "network": "cancel",
        "uw": "uw_cancel",
        "setrate": "back",
        "gencode": "back",
        "giveaway": "cancel",
        "star_network": "back",
        "admin_send_network": "back",
    }.get(prefix, "back")
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("⬡ Solana USDC", callback_data=f"{prefix}_solana"), InlineKeyboardButton("⬡ Polygon USDC", callback_data=f"{prefix}_polygon")],
            [InlineKeyboardButton("⬡ BSC USDT", callback_data=f"{prefix}_bsc"), InlineKeyboardButton("⬡ Avax USDT", callback_data=f"{prefix}_avalanche")],
            [InlineKeyboardButton("⬡ ETH USDT", callback_data=f"{prefix}_ethereum"), InlineKeyboardButton("⬡ ETH USDC", callback_data=f"{prefix}_ethereum_usdc")],
            [InlineKeyboardButton("⬡ Base USDC", callback_data=f"{prefix}_base"), InlineKeyboardButton("⬡ TRC20 USDT", callback_data=f"{prefix}_trc20")],
            [InlineKeyboardButton("⬡ TON", callback_data=f"{prefix}_ton")],
            [InlineKeyboardButton(tr("cancel", lang), callback_data=cancel_callback)],
        ]
    )


def user_network_menu(lang="bn"):
    return network_menu("uw", lang)


def rates_text(title=None, lang="bn"):
    rates = get_all_rates()
    title = title if title is not None else tr("current_rates", lang)
    lines = [
        f"{title}",
        DIVIDER,
        f"• Solana USDC: 1 USDC = {rates.get('solana', 0)} BDT",
        f"• Polygon USDC: 1 USDC = {rates.get('polygon', 0)} BDT",
        f"• BSC USDT: 1 USDT = {rates.get('bsc', 0)} BDT",
        f"• Avalanche USDT: 1 USDT = {rates.get('avalanche', 0)} BDT",
        f"• Ethereum USDT: 1 USDT = {rates.get('ethereum', 0)} BDT",
        f"• Ethereum USDC: 1 USDC = {rates.get('ethereum_usdc', 0)} BDT",
        f"• Base USDC: 1 USDC = {rates.get('base', 0)} BDT",
        f"• Tron USDT: 1 USDT = {rates.get('trc20', 0)} BDT",
        f"• TON: 1 TON = {rates.get('ton', 0)} BDT",
    ]
    return "\n".join(lines)


def home_text(user_name=None, lang="bn"):
    greeting = f"{tr('welcome', lang)}, {user_name}." if user_name else f"{tr('welcome', lang)}."
    intro = "Buy and receive crypto through supported networks." if lang == "en" else "নির্ধারিত নেটওয়ার্কে crypto কিনুন ও গ্রহণ করুন।"
    safety = "Verify the network and wallet before payment." if lang == "en" else "Payment করার আগে network ও wallet যাচাই করুন।"
    body = (
        f"{greeting}\n"
        f"{intro}\n\n"
        f"{rates_text(lang=lang)}\n\n"
        f"Payment\n{DIVIDER}\n"
        f"• bKash: `{BKASH_NUMBER}`\n"
        f"• {safety}\n\n"
        f"{tr('select_action', lang)}"
    )
    return panel(tr("home_title", lang), body)


async def send_first_time_language_selection(update):
    text = tr("choose_language", "bn")
    reply_markup = language_keyboard()
    await update.message.reply_text(text, reply_markup=reply_markup)
    if welcome_video_available():
        asyncio.create_task(send_welcome_video_background(update.message))


async def complete_language_selection_message(query, user_id, lang):
    user = query.from_user
    save_user_info(user.id, user.username, user.first_name)
    text = language_saved_home_text(query.from_user.first_name, lang)
    reply_markup = main_menu(user_id, lang)
    if is_video_message(getattr(query, "message", None)):
        try:
            await query.edit_message_caption(caption=tr("language_saved", lang))
        except Exception as exc:
            logger.warning("Welcome video caption edit failed, sending text home: %s", exc)
        await query.message.reply_text(home_text(query.from_user.first_name, lang), reply_markup=reply_markup)
        return
    await query.edit_message_text(text, reply_markup=reply_markup)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    save_user_info(user.id, user.username, user.first_name)
    args = getattr(context, "args", None) or []
    if args:
        raw_code = str(args[0]).strip()
        code = raw_code[4:] if raw_code.startswith("ref_") else raw_code
        if re.fullmatch(r"[A-Za-z0-9]{6,32}", code):
            try:
                bind_referral(user.id, code)
            except Exception as exc:
                logger.error("Referral bind failed: %s", exc)
    lang = get_user_language(user.id)
    if not lang:
        await send_first_time_language_selection(update)
        return
    await update.message.reply_text(home_text(user.first_name, lang), reply_markup=main_menu(user.id, lang))


async def send_crypto(network, wallet, amount):
    loop = asyncio.get_running_loop()
    if network == "solana":
        return await loop.run_in_executor(None, lambda: send_usdc(wallet, amount))
    if network == "polygon":
        return await loop.run_in_executor(None, lambda: send_polygon_usdc(wallet, amount))
    if network == "bsc":
        return await loop.run_in_executor(None, lambda: send_bsc_usdt(wallet, amount))
    if network == "avalanche":
        return await loop.run_in_executor(None, lambda: send_evm_token("avalanche", "usdt", wallet, amount))
    if network == "ethereum":
        return await loop.run_in_executor(None, lambda: send_evm_token("ethereum", "usdt", wallet, amount))
    if network == "ethereum_usdc":
        return await loop.run_in_executor(None, lambda: send_evm_token("ethereum", "usdc", wallet, amount))
    if network == "base":
        return await loop.run_in_executor(None, lambda: send_evm_token("base", "usdc", wallet, amount))
    if network == "trc20":
        return await loop.run_in_executor(None, lambda: send_trc20_usdt(wallet, amount))
    if network == "ton":
        return await loop.run_in_executor(None, lambda: send_ton(wallet, amount))
    raise ValueError(f"Unsupported network: {network}")


SELLER_NETWORKS = ["solana", "polygon", "bsc", "avalanche", "ethereum", "ethereum_usdc", "base", "trc20"]
STABLE_REFERRAL_NETWORKS = ["solana", "polygon", "bsc", "avalanche", "ethereum", "ethereum_usdc", "base", "trc20"]


def short_datetime(value):
    return str(value or "")[:16]


def referral_enabled():
    return get_setting("referral_enabled", "off") == "on"


def referral_percent_value():
    try:
        return float(get_setting("referral_percent", "0") or 0)
    except Exception:
        return 0.0


def referral_min_withdraw_value():
    try:
        return float(get_setting("referral_min_withdraw_usd", "1") or 1)
    except Exception:
        return 1.0


def stable_network_menu(prefix="refwd_net", lang="bn"):
    rows = []
    for i in range(0, len(STABLE_REFERRAL_NETWORKS), 2):
        row = []
        for network in STABLE_REFERRAL_NETWORKS[i:i + 2]:
            row.append(InlineKeyboardButton(NETWORKS[network]["name"][:24], callback_data=f"{prefix}_{network}"))
        rows.append(row)
    rows.append([InlineKeyboardButton(tr("cancel", lang), callback_data="referral_menu")])
    return InlineKeyboardMarkup(rows)


async def bot_referral_username(bot):
    username = getattr(bot, "username", None)
    if username:
        return username
    me = await bot.get_me()
    return me.username


def referral_link(username, code):
    return f"https://t.me/{username}?start=ref_{code}"


def referral_summary_text(user_id, code, link, lang="bn"):
    stats = referral_stats(user_id)
    enabled = referral_enabled()
    percent = referral_percent_value()
    min_withdraw = referral_min_withdraw_value()
    rows = list_referral_ledger(user_id, 5)
    recent = []
    for _lid, typ, amount, source_type, source_id, _ref_uid, status, _details, created in rows:
        sign = "+" if float(amount or 0) >= 0 else ""
        recent.append(f"{short_datetime(created)} | {typ} {sign}{round(float(amount or 0), 6)} USD | {status} | {source_type}:{source_id}")
    recent_text = "\n".join(recent) or ltext(lang, "No referral ledger entries yet.", "এখনও কোনো referral ledger entry নেই।")
    status = ltext(lang, "ON", "চালু") if enabled else ltext(lang, "OFF", "বন্ধ")
    disabled_line = "" if enabled else "\n⚠️ " + ltext(lang, "Referral rewards and withdrawals are currently off. You can still share your link.", "Referral reward এবং withdrawal বর্তমানে বন্ধ। Link share করতে পারবেন।")
    return panel(
        tr("referral", lang),
        f"Status: {status}\n"
        f"Reward percent: {percent}%\n"
        f"Wallet balance: {round(stats['balance'], 6)} USD\n"
        f"Minimum withdrawal: {min_withdraw} USD\n"
        f"Referrals: {stats['referral_count']}\n"
        f"Total earned: {round(stats['total_earned'], 6)} USD\n"
        f"Total withdrawn: {round(stats['total_withdrawn'], 6)} USD\n"
        f"{disabled_line}\n\n"
        f"Your code: {code}\n"
        f"Your link: {link}\n\n"
        f"Recent ledger:\n{recent_text}",
    )


def referral_keyboard(lang="bn", admin=False):
    rows = [
        [InlineKeyboardButton("🔗 My Link", callback_data="referral_link"), InlineKeyboardButton("💸 Withdraw", callback_data="referral_withdraw")],
        [InlineKeyboardButton("🔄 Refresh", callback_data="referral_menu"), InlineKeyboardButton(tr("back", lang), callback_data="back")],
    ]
    if admin:
        rows.insert(1, [InlineKeyboardButton("👥 Referral Admin", callback_data="referral_admin")])
    return InlineKeyboardMarkup(rows)


async def show_referral_menu(target, context, user_id, lang, edit=False):
    code = get_or_create_referral_code(user_id)
    username = await bot_referral_username(context.bot)
    text = referral_summary_text(user_id, code, referral_link(username, code), lang)
    markup = referral_keyboard(lang, is_admin(user_id))
    if edit and hasattr(target, "edit_message_text"):
        await target.edit_message_text(text, reply_markup=markup)
    else:
        await target.reply_text(text, reply_markup=markup)


def referral_admin_text():
    stats = referral_admin_stats()
    return panel(
        "👥 Referral Admin",
        f"Status: {get_setting('referral_enabled', 'off').upper()}\n"
        f"Percent: {referral_percent_value()}%\n"
        f"Min withdraw: {referral_min_withdraw_value()} USD\n"
        f"Relationships: {stats['relationships']}\n"
        f"Total credited: {round(stats['credited'], 6)} USD\n"
        f"Total withdrawn: {round(stats['withdrawn'], 6)} USD\n"
        f"Liability: {round(stats['liability'], 6)} USD\n"
        f"Failed withdrawals: {stats['failed_withdrawals']}",
    )


def referral_admin_keyboard(lang="bn"):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Enable", callback_data="refadmin_enable"), InlineKeyboardButton("🛑 Disable", callback_data="refadmin_disable")],
        [InlineKeyboardButton("% Set Percent", callback_data="refadmin_set_percent"), InlineKeyboardButton("💸 Set Min Withdraw", callback_data="refadmin_set_min")],
        [InlineKeyboardButton(tr("back", lang), callback_data="referral_menu")],
    ])


def referral_eligible_usd(network, amount_crypto, amount_bdt=0):
    try:
        bdt = float(amount_bdt or 0)
    except Exception:
        bdt = 0
    if bdt > 0:
        try:
            rate = float(get_rate("solana") or 0)
            if rate > 0:
                return bdt / rate
        except Exception:
            pass
    if network in STABLE_REFERRAL_NETWORKS:
        try:
            return float(amount_crypto or 0)
        except Exception:
            return 0
    return 0


def record_referral_reward_for_transaction(user_id, source_type, source_id, network, amount_crypto, amount_bdt=0, details=None):
    try:
        if not referral_enabled():
            return None
        percent = referral_percent_value()
        if percent <= 0:
            return None
        eligible = referral_eligible_usd(network, amount_crypto, amount_bdt)
        result = credit_referral_reward(user_id, source_type, source_id, eligible, percent, details)
        if result:
            add_audit("system", "referral_credit", "referral_ledger", result["id"], f"user={result['user_id']} amount={result['amount_usd']} source={source_type}:{source_id}")
        return result
    except Exception as exc:
        logger.error("Referral credit failed: %s", exc)
        return None


def seller_network_menu(prefix, seller_id=None, lang="bn"):
    networks = SELLER_NETWORKS
    if seller_id:
        networks = [row[1] for row in list_enabled_seller_wallets(seller_id) if row[5]]
    if not networks:
        return InlineKeyboardMarkup([[InlineKeyboardButton(tr("back", lang), callback_data="back")]])
    rows = []
    for i in range(0, len(networks), 2):
        row = []
        for network in networks[i:i + 2]:
            ni = NETWORKS[network]
            row.append(InlineKeyboardButton(ni["name"][:24], callback_data=f"{prefix}_{network}"))
        rows.append(row)
    rows.append([InlineKeyboardButton(tr("cancel", lang), callback_data="cancel")])
    return InlineKeyboardMarkup(rows)


def seller_public_name(row):
    return row[2] or row[1] or f"Seller {row[0]}"


def seller_guide_text(seller=None, lang="bn"):
    token = seller[6] if seller else "YOUR_SMS_TOKEN"
    if lang == "en":
        return (
            "🏪 Seller Setup Guide\n\n"
            f"App link: {SCB_FORWARDER_APP_URL}\n"
            f"Fixed server: {SCB_FORWARDER_SERVER_URL}\n"
            f"Seller token: {token}\n\n"
            "1️⃣ Install SCB-Forwarder on the Android phone that receives your seller bKash SMS or bKash app notifications.\n"
            "2️⃣ Open SCB-Forwarder and confirm the fixed server shown in the app. You cannot edit the server URL inside the app.\n"
            "3️⃣ Turn on Seller mode. Do not use admin/main mode for a seller phone.\n"
            "4️⃣ Paste your Seller token, then tap Save setup. The app should show Ready to forward.\n"
            "5️⃣ Tap Check server. Internet, server reachable, and token should all show OK. If token fails, copy the token from Seller Center again and save setup.\n"
            "6️⃣ Tap Allow SMS Permission. Then tap Enable Notification Access and enable SCB-Forwarder. Keeping both SMS and notification forwarding on is safe because the bot removes duplicate TrxID notices.\n"
            "7️⃣ Tap Start Background Service and keep the SCB-Forwarder running notification visible.\n"
            "8️⃣ Open Battery/autostart guide and disable battery restrictions/autostart blocking for SCB-Forwarder. On Samsung add it to Never sleeping apps; on Xiaomi/Redmi/Poco enable Autostart and No restrictions.\n"
            "9️⃣ In Seller Center → Delivery Wallet, add/update the private key for each network you sell. Keep native gas token in each seller wallet.\n"
            "🔟 Set seller rates if you want custom rates; 0 uses the global/admin rate.\n\n"
            "Supported seller auto-delivery: Solana, Polygon, BSC, Avalanche, Ethereum, Base, and TRC20. TON seller auto-delivery is not supported. Telegram Stars seller sales create a pending payout ledger that admin marks paid manually."
        )
    return (
        "🏪 Seller Setup Guide\n\n"
        f"অ্যাপ লিংক: {SCB_FORWARDER_APP_URL}\n"
        f"Fixed server: {SCB_FORWARDER_SERVER_URL}\n"
        f"Seller token: {token}\n\n"
        "1️⃣ যে Android ফোনে আপনার seller bKash SMS বা bKash app notification আসে, সেই ফোনে SCB-Forwarder install করুন।\n"
        "2️⃣ SCB-Forwarder খুলে app-এ দেখানো fixed server মিলিয়ে নিন। App থেকে server URL change করা যাবে না।\n"
        "3️⃣ Seller mode অন করুন। Seller ফোনে admin/main mode ব্যবহার করবেন না।\n"
        "4️⃣ আপনার Seller token paste করে Save setup চাপুন। সব ঠিক থাকলে app দেখাবে Ready to forward।\n"
        "5️⃣ Check server চাপুন। Internet, server reachable, token — তিনটাই OK হওয়া দরকার। Token fail হলে Seller Center থেকে token আবার copy করে setup save করুন।\n"
        "6️⃣ Allow SMS Permission চাপুন। তারপর Enable Notification Access চাপুন এবং SCB-Forwarder enable করুন। SMS ও notification দুইটাই on রাখলে সমস্যা নেই, bot TrxID দিয়ে duplicate বাদ দেয়।\n"
        "7️⃣ Start Background Service চাপুন এবং SCB-Forwarder running notification visible রাখুন।\n"
        "8️⃣ Battery/autostart guide খুলে SCB-Forwarder-এর battery restriction/autostart blocking off করুন। Samsung হলে Never sleeping apps-এ add করুন; Xiaomi/Redmi/Poco হলে Autostart on ও No restrictions দিন।\n"
        "9️⃣ Seller Center → Delivery Wallet এ আপনি যে network sell করবেন, প্রতিটির private key add/update করুন। প্রতিটি seller wallet-এ native gas token রাখুন।\n"
        "🔟 Custom rate চাইলে seller rate set করুন; 0 দিলে global/admin rate use হবে।\n\n"
        "Supported seller auto-delivery: Solana, Polygon, BSC, Avalanche, Ethereum, Base, TRC20। TON seller auto-delivery supported না। Telegram Stars seller sale হলে pending payout ledger তৈরি হয়, admin manual paid mark করবেন।"
    )


def seller_approval_text(seller=None, lang="bn"):
    if lang == "en":
        return "🎉 Your seller account has been approved.\n\n" + seller_guide_text(seller, lang)
    return "🎉 আপনার seller account approved হয়েছে।\n\n" + seller_guide_text(seller, lang)


def seller_rate_or_global(seller_id, network):
    seller_rate = get_seller_rate(seller_id, network)
    return float(seller_rate) if seller_rate else get_rate(network)


def seller_order_summary(order):
    order_id, seller_id, buyer_id, buyer_username, method, trx_id, network, wallet, amount_bdt, amount_crypto, stars_amount, status, tx_sig, error, created_at, _updated = order
    ni = NETWORKS.get(network, {"name": network, "symbol": "?"})
    return (
        f"🧾 Order: {order_id}\n"
        f"🏪 Seller: {seller_id}\n"
        f"👤 Buyer: @{buyer_username or buyer_id} ({buyer_id})\n"
        f"💳 Method: {method}\n"
        f"🔑 TrxID: {trx_id or 'N/A'}\n"
        f"🌐 {ni['name']}\n"
        f"💰 {amount_bdt or 0} BDT / {stars_amount or 0} Stars\n"
        f"💵 {amount_crypto} {ni['symbol']}\n"
        f"👛 {short_wallet(wallet)}\n"
        f"📌 Status: {status}\n"
        f"🕒 {short_datetime(created_at)}"
    )


async def show_seller_center(target, context, user_id, username, edit=True):
    lang = user_lang(user_id)
    seller = get_seller(user_id)
    if not seller:
        text = panel("🏪 Seller Center", "Seller হিসেবে crypto sell করতে apply করুন। Admin approval দরকার।")
        markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("📝 Apply", callback_data="seller_apply")],
            [InlineKeyboardButton("📖 Guide", callback_data="seller_guide"), InlineKeyboardButton(tr("back", lang), callback_data="back")],
        ])
    else:
        status = seller[5]
        if status == "approved":
            wallets = list_enabled_seller_wallets(user_id)
            pending = list_pending_seller_orders(user_id, 5)
            ledger = list_seller_star_ledger(user_id, "pending_payout", 20)
            stars = sum(int(row[3] or 0) for row in ledger)
            nets = ", ".join(NETWORKS.get(row[1], {"name": row[1]})["name"] for row in wallets) or "None"
            text = panel(
                "🏪 Seller Dashboard",
                f"✅ Approved\n🏷️ {seller_public_name(seller)}\n📲 bKash: {seller[3]}\n🔐 SMS Token: `{seller[6]}`\n🌐 Networks: {nets}\n⏳ Pending/manual: {len(pending)}\n⭐ Pending Stars ledger: {stars}\n\nForwarder endpoint guide only seller can see.",
            )
            markup = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔐 Delivery Wallet", callback_data="seller_wallet"), InlineKeyboardButton("📈 Rates", callback_data="seller_rates")],
                [InlineKeyboardButton("🧾 Pending Orders", callback_data="seller_pending"), InlineKeyboardButton("⭐ Ledger", callback_data="seller_ledger")],
                [InlineKeyboardButton("📖 Guide", callback_data="seller_guide"), InlineKeyboardButton(tr("back", lang), callback_data="back")],
            ])
        elif status == "pending":
            text = panel("🏪 Seller Center", f"⏳ Application pending.\n🏷️ {seller_public_name(seller)}\nAdmin approve করলে dashboard চালু হবে।")
            markup = InlineKeyboardMarkup([[InlineKeyboardButton("📖 Guide", callback_data="seller_guide")], [InlineKeyboardButton(tr("back", lang), callback_data="back")]])
        else:
            text = panel("🏪 Seller Center", f"📌 Status: {status}\nSupport/admin: @{SUPPORT_USERNAME.lstrip('@')}")
            markup = InlineKeyboardMarkup([[InlineKeyboardButton("📖 Guide", callback_data="seller_guide")], [InlineKeyboardButton(tr("back", lang), callback_data="back")]])
    if edit and hasattr(target, "edit_message_text"):
        await target.edit_message_text(text, reply_markup=markup, parse_mode="Markdown")
    else:
        await target.reply_text(text, reply_markup=markup, parse_mode="Markdown")


async def show_seller_marketplace(query, lang):
    sellers = list_approved_sellers(20)
    if not sellers:
        await query.edit_message_text(ltext(lang, "🛍️ No approved sellers are available right now.", "🛍️ এখন কোনো approved seller নেই।"), reply_markup=back_keyboard(lang))
        return
    keyboard = [[InlineKeyboardButton(f"🏪 {seller_public_name(s)[:28]}", callback_data=f"sellerpick_{s[0]}")] for s in sellers]
    keyboard.append([InlineKeyboardButton(tr("back", lang), callback_data="back")])
    await query.edit_message_text(panel("🛍️ Seller Marketplace", ltext(lang, "Choose one seller. Payment will use that seller's bKash or Stars route.", "Seller বেছে নিন। Payment seller-এর bKash/Stars ledger route হবে।")), reply_markup=InlineKeyboardMarkup(keyboard))


async def show_seller_rates(query, seller_id, lang):
    wallets = list_enabled_seller_wallets(seller_id)
    if not wallets:
        await query.edit_message_text("প্রথমে delivery wallet add করুন।", reply_markup=back_keyboard(lang))
        return
    lines = []
    keyboard = []
    for row in wallets:
        network = row[1]
        ni = NETWORKS[network]
        sr = get_seller_rate(seller_id, network)
        lines.append(f"{ni['name']}: {sr or get_rate(network)} BDT ({'seller' if sr else 'global'})")
        keyboard.append([InlineKeyboardButton(f"Set {ni['name'][:20]}", callback_data=f"sellerrate_{network}")])
    keyboard.append([InlineKeyboardButton(tr("back", lang), callback_data="seller_center")])
    await query.edit_message_text(panel("📈 Seller Rates", "\n".join(lines)), reply_markup=InlineKeyboardMarkup(keyboard))


async def show_seller_pending(query, seller_id, lang):
    rows = list_pending_seller_orders(seller_id, 10)
    if not rows:
        await query.edit_message_text("✅ Pending/manual seller order নেই।", reply_markup=back_keyboard(lang))
        return
    for row in rows:
        order_id = row[0]
        keyboard = [[InlineKeyboardButton("✅ Approve/send", callback_data=f"sordera_{order_id}"), InlineKeyboardButton("❌ Reject", callback_data=f"sorderr_{order_id}")]]
        await query.message.reply_text(seller_order_summary(row), reply_markup=InlineKeyboardMarkup(keyboard))
    await query.edit_message_text("🧾 Pending/manual seller orders sent above.", reply_markup=back_keyboard(lang))


async def complete_seller_order(app_or_bot, order_id, actor_id=None, notice_amount=None):
    order = get_seller_order(order_id)
    if not order:
        return False, "Order not found"
    order_id, seller_id, buyer_id, buyer_username, method, trx_id, network, wallet, amount_bdt, amount_crypto, stars_amount, status, *_ = order
    seller = get_seller(seller_id)
    if not seller or seller[5] != "approved":
        update_seller_order(order_id, status="failed", error="seller not approved")
        return False, "Seller not approved"
    if status == "completed":
        return True, "already completed"
    conflict = seller_trx_conflict(seller_id, trx_id, order_id) if method == "bkash" and trx_id else None
    if conflict:
        reason = seller_trx_conflict_text(conflict)
        update_seller_order(order_id, status="rejected", error=reason)
        return False, reason
    if notice_amount is not None and amount_bdt and abs(float(notice_amount) - float(amount_bdt)) > 0.01:
        update_seller_order(order_id, status="pending_manual", error="amount mismatch")
        return False, "Amount mismatch"
    ni = NETWORKS.get(network, {"name": network, "symbol": "?", "explorer": ""})
    bot = app_or_bot.bot if hasattr(app_or_bot, "bot") else app_or_bot
    try:
        sig = await asyncio.get_running_loop().run_in_executor(None, lambda: send_from_seller_wallet(seller_id, network, wallet, float(amount_crypto)))
        update_seller_order(order_id, status="completed", tx_sig=sig, error="")
        if trx_id:
            mark_seller_payment_notice_used(seller_id, trx_id)
        source = "seller_stars" if method == "stars" else "seller_bkash"
        save_transaction(f"SELLER-{order_id}", buyer_id, amount_bdt or 0, amount_crypto, wallet, sig, "completed", network, order_id=order_id, source=source, seller_id=seller_id)
        record_referral_reward_for_transaction(buyer_id, "seller_buy", f"{order_id}:buyer", network, amount_crypto, amount_bdt or 0, f"seller={seller_id} method={method}")
        record_referral_reward_for_transaction(seller_id, "seller_sale", f"{order_id}:seller", network, amount_crypto, amount_bdt or 0, f"buyer={buyer_id} method={method}")
        if method == "stars" and stars_amount:
            create_seller_star_ledger(gen_timestamp_id("SL"), seller_id, order_id, stars_amount)
        receipt_data = await make_receipt_data(
            bot,
            order_id,
            f"SELLER-{order_id}",
            network,
            amount_crypto,
            wallet,
            sig,
            buyer_id,
            buyer_username=buyer_username,
            seller_id=seller_id,
            seller_name=seller_public_name(seller),
            bdt_amount=amount_bdt if method != "stars" else None,
            stars_amount=stars_amount if method == "stars" else None,
            title="Smart Crypto Buy",
        )
        await send_transaction_receipt(bot, [buyer_id, seller_id, ADMIN_ID], receipt_data)
        return True, sig
    except Exception as exc:
        reason = failure_reason_text(exc, network, "en")
        update_seller_order(order_id, status="failed", error=str(exc)[:500])
        try:
            await bot.send_message(int(seller_id), f"🚨 Seller order send failed.\n\n🧾 {order_id}\n❌ {exc}\n💡 {reason}")
            await bot.send_message(ADMIN_ID, f"🚨 Seller order send failed.\n\n{seller_order_summary(order)}\n❌ {exc}\n💡 {reason}")
            await bot.send_message(int(buyer_id), f"✅ Payment received but seller delivery failed. Seller/admin has been notified.\n🧾 {order_id}\n💡 Likely cause: {reason}", reply_markup=track_order_keyboard(order_id, buyer_id, user_lang(buyer_id)))
        except Exception:
            pass
        return False, f"{exc} | {reason}"


def seller_trx_conflict(seller_id, trx_id, order_id=None):
    if not trx_id:
        return None
    seller_id = str(seller_id)
    owner_notice = get_seller_payment_notice_owner(trx_id)
    if owner_notice and str(owner_notice[0]) != seller_id:
        return {"kind": "notice", "seller_id": str(owner_notice[0]), "trx_id": trx_id}
    completed_order = get_completed_seller_order_by_trx(trx_id)
    if completed_order and str(completed_order[1]) != seller_id and str(completed_order[0]) != str(order_id or ""):
        return {"kind": "completed_order", "seller_id": str(completed_order[1]), "order_id": completed_order[0], "trx_id": trx_id}
    return None


def seller_trx_conflict_text(conflict):
    if not conflict:
        return ""
    if conflict.get("kind") == "notice":
        return f"TrxID already belongs to another seller payment notice: seller={conflict.get('seller_id')}"
    if conflict.get("kind") == "completed_order":
        return f"TrxID already completed for another seller order: seller={conflict.get('seller_id')} order={conflict.get('order_id')}"
    return "TrxID already belongs to another seller"


async def handle_seller_order_trx(update, context, user_id, username):
    order_id = context.user_data.get("seller_order_id")
    order = get_seller_order(order_id)
    if not order:
        await update.message.reply_text("❌ Seller order session expired.")
        context.user_data.clear()
        return
    trx_id = update.message.text.strip().upper()
    lang = user_lang(user_id)
    if len(trx_id) < 4:
        await update.message.reply_text(ltext(lang, "❌ Invalid TrxID. Please enter it again.", "❌ ভুল TrxID! আবার দিন।"))
        return
    if get_seller_order_by_trx(order[1], trx_id):
        await update.message.reply_text(ltext(lang, "⚠️ This TrxID was already used for this seller.", "⚠️ এই seller-এর জন্য TrxID আগে ব্যবহার হয়েছে।"))
        return
    conflict = seller_trx_conflict(order[1], trx_id, order_id)
    if conflict:
        reason = seller_trx_conflict_text(conflict)
        update_seller_order(order_id, status="rejected", error=reason)
        try:
            await update.get_bot().send_message(ADMIN_ID, f"🚫 Cross-seller TrxID blocked.\nOrder: {order_id}\nSeller: {order[1]}\nTrxID: {trx_id}\nReason: {reason}")
        except Exception:
            pass
        await update.message.reply_text(ltext(lang, "🚫 This TrxID belongs to another seller/payment and cannot be used here.", "🚫 এই TrxID অন্য seller/payment-এর সাথে যুক্ত, তাই এখানে ব্যবহার করা যাবে না।"))
        context.user_data.clear()
        return
    update_seller_order(order_id, trx_id=trx_id)
    notice = get_seller_payment_notice(order[1], trx_id)
    if notice:
        ok, result = await complete_seller_order(update.get_bot(), order_id, user_id, notice[2])
        context.user_data.clear()
        if ok:
            await update.message.reply_text(ltext(lang, "✅ Payment notice matched. Crypto has been sent.", "✅ Payment notice matched. Crypto পাঠানো হয়েছে।"))
        else:
            await update.message.reply_text(ltext(lang, f"⏳ Seller manual verification is required.\n🧾 {order_id}\nReason: {result}", f"⏳ Seller manual verification লাগবে।\n🧾 {order_id}\nReason: {result}"), reply_markup=track_order_keyboard(order_id, user_id, lang))
        return
    update_seller_order(order_id, status="pending_manual")
    seller_id = order[1]
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("✅ Approve/send", callback_data=f"sordera_{order_id}"), InlineKeyboardButton("❌ Reject", callback_data=f"sorderr_{order_id}")]])
    try:
        await update.get_bot().send_message(int(seller_id), f"⚠️ Buyer TrxID দিল কিন্তু forwarder notice মেলেনি। Manual verify করুন।\n\n{seller_order_summary(get_seller_order(order_id))}", reply_markup=keyboard)
    except Exception as exc:
        logger.error(exc)
    context.user_data.clear()
    await update.message.reply_text(ltext(lang, f"⏳ The seller is verifying your TrxID.\n\n🧾 Order: {order_id}\n🔑 TrxID: {trx_id}", f"⏳ TrxID seller যাচাই করছেন।\n\n🧾 Order: {order_id}\n🔑 TrxID: {trx_id}"), reply_markup=track_order_keyboard(order_id, user_id, lang))


async def process_seller_bkash(app, text, sender, meta):
    parsed = parse_bkash_payment_notice(text)
    if not parsed:
        return {"payment_status": "ignored", "message": "Seller notice was not a supported bKash payment."}
    token = (meta or {}).get("seller_token")
    admin_parse_alert_sent = bool((meta or {}).get("admin_parse_alert_sent"))
    seller = get_seller_by_sms_token(token) if token else None
    trx_id = parsed["trx_id"]
    amount_bdt = parsed["amount_bdt"]
    if not seller or seller[5] != "approved":
        logger.warning("Seller bKash notice rejected for unknown/unapproved token: %s", token)
        if not admin_parse_alert_sent:
            await notify_admin_parsed_bkash(app, parsed, sender, text, "seller", "unknown/unapproved")
        if ADMIN_ID:
            await app.bot.send_message(ADMIN_ID, f"⚠️ Seller bKash notice rejected. Unknown/unapproved token.\nSource: {sender}\nTrxID: {trx_id}\nAmount: {amount_bdt}")
        return {"payment_status": "ignored", "trx_id": trx_id, "amount_bdt": amount_bdt, "message": "Seller token is unknown or not approved."}
    seller_id = seller[0]
    conflict = seller_trx_conflict(seller_id, trx_id)
    if conflict:
        reason = seller_trx_conflict_text(conflict)
        if ADMIN_ID:
            await app.bot.send_message(ADMIN_ID, f"🚫 Cross-seller bKash notice blocked.\nSeller: {seller_id}\nTrxID: {trx_id}\nAmount: {amount_bdt}\nReason: {reason}")
        return {"payment_status": "duplicate", "duplicate": True, "trx_id": trx_id, "amount_bdt": amount_bdt, "message": reason}
    saved_new = save_seller_payment_notice(seller_id, trx_id, amount_bdt, sender, "seller_bkash", text)
    touch_webhook_notice(f"seller_{sender}", trx_id, amount_bdt)
    if not admin_parse_alert_sent:
        await notify_admin_parsed_bkash(app, parsed, sender, text, "seller", seller_id)
    order = find_waiting_seller_order_by_trx(seller_id, trx_id)
    if order:
        if trx_id.startswith("TEST") or str(sender).startswith("test"):
            await app.bot.send_message(ADMIN_ID, f"🧪 Test seller bKash notice matched order but auto-send blocked.\nSeller: {seller_id}\nOrder: {order[0]}\nTrxID: {trx_id}\nAmount: {amount_bdt}")
            return {"payment_status": "manual_review", "manual_review": True, "matched_order": True, "order_id": order[0], "trx_id": trx_id, "amount_bdt": amount_bdt, "message": "Seller payment matched an order, but test notices require manual review."}
        ok, result = await complete_seller_order(app, order[0], "seller_sms", amount_bdt)
        if not ok:
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("✅ Approve/send", callback_data=f"sordera_{order[0]}"), InlineKeyboardButton("❌ Reject", callback_data=f"sorderr_{order[0]}")]])
            await app.bot.send_message(int(seller_id), f"⚠️ Seller payment notice needs manual verification.\nReason: {result}\n\n{seller_order_summary(get_seller_order(order[0]))}", reply_markup=keyboard)
            return {"payment_status": "manual_review", "manual_review": True, "matched_order": True, "order_id": order[0], "trx_id": trx_id, "amount_bdt": amount_bdt, "message": f"Seller payment matched an order but needs manual review: {result}"}
        return {"payment_status": "matched_order", "matched_order": True, "order_id": order[0], "trx_id": trx_id, "amount_bdt": amount_bdt, "message": "Seller payment matched and order processing started."}
    if saved_new:
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🧾 Pending Orders", callback_data="seller_pending")]])
        await app.bot.send_message(int(seller_id), f"💰 Seller bKash notice received but no waiting order matched yet.\n\n🔑 TrxID: {trx_id}\n💵 {amount_bdt} BDT", reply_markup=keyboard)
        if ADMIN_ID:
            await app.bot.send_message(ADMIN_ID, f"💰 Unmatched seller bKash notice.\nSeller: {seller_public_name(seller)} ({seller_id})\nTrxID: {trx_id}\nAmount: {amount_bdt}")
    if not saved_new:
        return {"payment_status": "duplicate", "duplicate": True, "trx_id": trx_id, "amount_bdt": amount_bdt, "message": "Seller payment notice was already recorded."}
    return {"payment_status": "parsed", "trx_id": trx_id, "amount_bdt": amount_bdt, "message": "Seller payment parsed, but no waiting order matched yet."}


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)
    username = query.from_user.username or query.from_user.first_name
    lang = user_lang(user_id)
    if query.data != "tid_start":
        context.user_data.pop("telegram_id_finder", None)

    if query.data == "language_menu":
        await query.edit_message_text(tr("choose_language", lang), reply_markup=language_keyboard())

    elif query.data.startswith("set_lang_"):
        lang = query.data.replace("set_lang_", "", 1)
        set_user_language(user_id, lang)
        context.user_data["lang"] = lang
        await complete_language_selection_message(query, user_id, lang)

    elif query.data == "rate":
        await query.edit_message_text(
            panel("📊 Rates", f"{rates_text('', lang)}\n{DIVIDER}\n📲 bKash: `{BKASH_NUMBER}`\n⚡ {'Delivery: usually 1-3 minutes' if lang == 'en' else 'সাধারণত ১-৩ মিনিটে পাঠানো হয়'}"),
            reply_markup=back_keyboard(lang),
        )

    elif query.data == "terms":
        await query.edit_message_text(terms_text(lang), reply_markup=back_keyboard(lang))

    elif query.data == "faq":
        await query.edit_message_text(faq_text(lang), reply_markup=back_keyboard(lang))

    elif query.data.startswith("us_"):
        if not is_admin(user_id):
            return

        if query.data == "us_export":
            return await export_users(update, context)

        if query.data.startswith("us_f_"):
            filter_type = query.data.replace("us_f_", "")
            if filter_type == "search":
                context.user_data["admin_user_analytics_lookup"] = True # reusing this flag for searching
                context.user_data["user_search_active"] = True
                await query.edit_message_text("🔍 Send User ID, Name, or Username to search:", reply_markup=back_keyboard(lang))
                return

            rows, total = get_users_paged(filter_type, 0)
            total_pages = math.ceil(total / 10) if total > 0 else 1
            await query.edit_message_text(users_list_text(rows, total, filter_type, 0), reply_markup=users_keyboard(filter_type, 0, total_pages))

        elif query.data.startswith("us_p_"):
            parts = query.data.split("_", 4)
            filter_type = parts[2]
            page_part = parts[3]
            suffix = parts[4] if len(parts) > 4 else ""
            show_filters = suffix == "show"
            # Ignore hide suffix; page is always numeric
            page = int(page_part) if page_part.isdigit() else 0
            # Recover search query from server-side storage; never from callback_data
            search_query = context.user_data.get("user_search_query") if filter_type == "search" else None

            rows, total = get_users_paged(filter_type, page, search_query)
            total_pages = math.ceil(total / 10) if total > 0 else 1
            await query.edit_message_text(users_list_text(rows, total, filter_type, page), reply_markup=users_keyboard(filter_type, page, total_pages, search_query, show_filters))

    elif query.data == "free_service":
        context.user_data.pop("telegram_id_finder", None)
        await query.edit_message_text(free_service_text(lang), reply_markup=free_service_keyboard(lang))

    elif query.data == "telegram_id_finder":
        await query.edit_message_text(telegram_id_finder_text(lang), reply_markup=telegram_id_finder_keyboard(lang))

    elif query.data == "tid_start":
        context.user_data["telegram_id_finder"] = True
        await query.edit_message_text(
            ltext(
                lang,
                "🆔 ID Finder is ready.\n\nSend one of these:\n• Public @username\n• Public t.me/telegram.me link\n• Numeric chat ID\n• Forwarded message from a user/group/channel\n\nSend /cancel to stop.",
                "🆔 ID Finder ready.\n\nএগুলোর যেকোনো একটি পাঠান:\n• Public @username\n• Public t.me/telegram.me link\n• Numeric chat ID\n• User/group/channel থেকে forwarded message\n\nবন্ধ করতে /cancel লিখুন।",
            ),
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(tr("cancel", lang), callback_data="tid_cancel")]]),
        )

    elif query.data == "tid_cancel":
        context.user_data.pop("telegram_id_finder", None)
        await query.edit_message_text(ltext(lang, "✅ Telegram ID Finder closed.", "✅ Telegram ID Finder বন্ধ হয়েছে।"), reply_markup=telegram_id_finder_keyboard(lang))

    elif query.data == "solana_ata_refund":
        context.user_data.pop("telegram_id_finder", None)
        wallet = context.user_data.get("solana_refund_wallet")
        summary = context.user_data.get("solana_refund_summary")
        await query.edit_message_text(
            solana_refund_text(lang, wallet, summary),
            parse_mode="Markdown",
            reply_markup=solana_refund_keyboard(lang, bool(wallet), bool(summary and summary.get("refundable_count"))),
        )

    elif query.data == "sr_connect":
        context.user_data["solana_refund_step"] = "private_key"
        await query.edit_message_text(
            ltext(
                lang,
                "🔐 Send your Solana private key for ATA refund check.\n\nThe message will be deleted after verification. This wallet is used only for this Free Service refund flow. Send /cancel to stop.",
                "🔐 ATA refund check করার জন্য আপনার Solana private key পাঠান।\n\nVerify করার পর message delete করা হবে। এই wallet শুধু এই Free Service refund flow-এর জন্য ব্যবহার হবে। বন্ধ করতে /cancel লিখুন।",
            ),
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(tr("cancel", lang), callback_data="sr_disconnect")]]),
        )

    elif query.data == "sr_check":
        private_key = context.user_data.get("solana_refund_private_key")
        wallet = context.user_data.get("solana_refund_wallet")
        if not private_key:
            context.user_data["solana_refund_step"] = "private_key"
            await query.edit_message_text(ltext(lang, "🔐 Connect your Solana wallet first. Send the private key now.", "🔐 আগে Solana wallet connect করুন। এখন private key পাঠান।"), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(tr("cancel", lang), callback_data="sr_disconnect")]]))
            return ConversationHandler.END
        await query.edit_message_text(ltext(lang, "🔎 Checking ATA accounts...", "🔎 ATA account check হচ্ছে..."))
        try:
            loop = asyncio.get_running_loop()
            summary = await loop.run_in_executor(None, lambda: find_refundable_atas(private_key))
            context.user_data["solana_refund_summary"] = summary
            await query.edit_message_text(
                solana_refund_text(lang, wallet or summary.get("wallet"), summary),
                parse_mode="Markdown",
                reply_markup=solana_refund_keyboard(lang, True, bool(summary.get("refundable_count"))),
            )
        except Exception as exc:
            await query.edit_message_text(ltext(lang, f"❌ ATA check failed: {friendly_solana_error(exc, lang)}", f"❌ ATA check ব্যর্থ: {friendly_solana_error(exc, lang)}"), reply_markup=solana_refund_keyboard(lang, bool(wallet), False))

    elif query.data == "sr_refund":
        summary = context.user_data.get("solana_refund_summary")
        if not context.user_data.get("solana_refund_private_key"):
            await query.edit_message_text(ltext(lang, "🔐 Connect your Solana wallet first.", "🔐 আগে Solana wallet connect করুন।"), reply_markup=solana_refund_keyboard(lang))
            return ConversationHandler.END
        if not summary or not summary.get("refundable_count"):
            await query.edit_message_text(ltext(lang, "No refundable empty ATA found. Run Check ATA accounts first.", "Refund করা যাবে এমন empty ATA পাওয়া যায়নি। আগে Check ATA accounts চালান।"), reply_markup=solana_refund_keyboard(lang, True, False))
            return ConversationHandler.END
        await query.edit_message_text(
            ltext(
                lang,
                f"♻️ Refund {summary.get('total_sol', 0):.6f} SOL by closing {summary.get('refundable_count', 0)} empty ATA account(s)?\n\nNetwork fee will be paid from the same wallet.",
                f"♻️ {summary.get('refundable_count', 0)}টি empty ATA close করে {summary.get('total_sol', 0):.6f} SOL refund করবেন?\n\nNetwork fee একই wallet থেকে কাটবে।",
            ),
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton(ltext(lang, "✅ Yes, refund SOL", "✅ হ্যাঁ, SOL refund করুন"), callback_data="sr_refund_confirm")],
                    [InlineKeyboardButton(ltext(lang, "❌ No", "❌ না"), callback_data="solana_ata_refund")],
                ]
            ),
        )

    elif query.data == "sr_refund_confirm":
        private_key = context.user_data.get("solana_refund_private_key")
        if not private_key:
            await query.edit_message_text(ltext(lang, "🔐 Refund session expired. Connect your Solana wallet again.", "🔐 Refund session expire হয়েছে। আবার Solana wallet connect করুন।"), reply_markup=solana_refund_keyboard(lang))
            return ConversationHandler.END
        await query.edit_message_text(ltext(lang, "♻️ Refunding SOL from empty ATA accounts...", "♻️ Empty ATA account থেকে SOL refund হচ্ছে..."))
        try:
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(None, lambda: close_refundable_atas(private_key))
            context.user_data.pop("solana_refund_summary", None)
            signatures = result.get("signatures") or []
            sig_lines = "\n".join([f"• `{sig}`" for sig in signatures[:5]])
            await query.edit_message_text(
                ltext(
                    lang,
                    f"✅ Refund submitted.\n\nClosed ATA accounts: {result.get('refundable_count', 0)}\nEstimated SOL returned: {result.get('total_sol', 0):.6f}\nTransactions:\n{sig_lines or 'N/A'}",
                    f"✅ Refund submit হয়েছে।\n\nClosed ATA account: {result.get('refundable_count', 0)}\nআনুমানিক ফেরত SOL: {result.get('total_sol', 0):.6f}\nTransaction:\n{sig_lines or 'N/A'}",
                ),
                parse_mode="Markdown",
                reply_markup=solana_refund_keyboard(lang, True, False),
            )
        except Exception as exc:
            await query.edit_message_text(ltext(lang, f"❌ Refund failed: {friendly_solana_error(exc, lang)}", f"❌ Refund ব্যর্থ: {friendly_solana_error(exc, lang)}"), reply_markup=solana_refund_keyboard(lang, True, False))

    elif query.data == "sr_disconnect":
        for key in ["solana_refund_step", "solana_refund_private_key", "solana_refund_wallet", "solana_refund_summary"]:
            context.user_data.pop(key, None)
        await query.edit_message_text(ltext(lang, "🔌 Solana refund wallet disconnected.", "🔌 Solana refund wallet disconnect হয়েছে।"), reply_markup=solana_refund_keyboard(lang))

    elif query.data == "telegram_message_forwarder":
        context.user_data.pop("telegram_id_finder", None)
        connection = free_forward_connection(user_id)
        personal_connection = personal_forward_connection(user_id)
        await query.edit_message_text(
            free_forward_text(lang, bool(connection.get("token")), connection.get("bot_username"), free_forward_task_running(user_id), bool(personal_connection.get("session")), personal_connection.get("display_name")),
            reply_markup=free_forward_keyboard(lang, bool(connection.get("token")), free_forward_task_running(user_id), bool(personal_connection.get("session"))),
        )

    elif query.data == "ff_connect_token":
        context.user_data["free_forward_step"] = "token"
        await query.edit_message_text(
            ltext(
                lang,
                "🔐 Send your Telegram bot token from @BotFather.\n\nYour next message will be deleted after checking. The token is kept only in this bot session. Send /cancel to stop.",
                "🔐 @BotFather থেকে পাওয়া Telegram bot token পাঠান।\n\nCheck করার পর আপনার next message delete করা হবে। Token শুধু এই bot session-এ রাখা হবে। বন্ধ করতে /cancel লিখুন।",
            ),
            reply_markup=free_forward_cancel_keyboard(lang),
        )

    elif query.data == "ff_forward":
        if not free_forward_connected(user_id):
            context.user_data["free_forward_step"] = "token"
            await query.edit_message_text(
                ltext(lang, "🔐 Connect a Telegram bot token first. Send the token now.", "🔐 আগে Telegram bot token connect করুন। এখন token পাঠান।"),
                reply_markup=free_forward_cancel_keyboard(lang),
            )
        else:
            context.user_data["free_forward_sender"] = "bot"
            await query.edit_message_text(ltext(lang, "Choose forwarding type:", "Forward type বেছে নিন:"), reply_markup=free_forward_mode_keyboard(lang, "ff"))

    elif query.data == "pf_connect_account":
        if not personal_forward_available():
            await query.edit_message_text(
                ltext(lang, "❌ Personal account forwarding needs Telethon installed on the server.", "❌ Personal account forwarding চালাতে server-এ Telethon install থাকতে হবে।"),
                reply_markup=free_forward_keyboard(lang, free_forward_connected(user_id), free_forward_task_running(user_id), personal_forward_connected(user_id)),
            )
            return ConversationHandler.END
        await personal_forward_disconnect_pending(user_id)
        free_forward_clear_flow(context)
        token = create_personal_auth_session(user_id, lang)
        link = personal_auth_link(token)
        await query.edit_message_text(
            ltext(
                lang,
                "👤 Personal account login\n\nOnly connect your own Telegram account. Use this only for groups/channels where you have permission to post.\n\nOpen the secure web login link below. Enter the Telegram login code only on that web page—never in Telegram chat. The link expires in 10 minutes.",
                "👤 Personal account login\n\nশুধু নিজের Telegram account connect করুন। শুধু সেই group/channel-এ ব্যবহার করুন যেখানে post করার permission আছে।\n\nনিচের secure web login link খুলুন। Telegram login code শুধু ওই web page-এ দিন—Telegram chat-এ কখনো নয়। Link ১০ মিনিট পর expire হবে।",
            ),
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton(ltext(lang, "🌐 Open secure web login", "🌐 Secure web login খুলুন"), url=link)],
                    [InlineKeyboardButton(tr("cancel", lang), callback_data="ff_cancel_flow")],
                ]
            ),
        )

    elif query.data == "pf_forward":
        if not personal_forward_connected(user_id):
            token = create_personal_auth_session(user_id, lang)
            link = personal_auth_link(token)
            await query.edit_message_text(
                ltext(lang, "👤 Connect your personal Telegram account first. Open the secure web login link below.", "👤 আগে personal Telegram account connect করুন। নিচের secure web login link খুলুন।"),
                reply_markup=InlineKeyboardMarkup(
                    [
                        [InlineKeyboardButton(ltext(lang, "🌐 Open secure web login", "🌐 Secure web login খুলুন"), url=link)],
                        [InlineKeyboardButton(tr("cancel", lang), callback_data="ff_cancel_flow")],
                    ]
                ),
            )
        else:
            context.user_data["free_forward_sender"] = "personal"
            await query.edit_message_text(ltext(lang, "Choose personal-account forwarding type:", "Personal-account forward type বেছে নিন:"), reply_markup=free_forward_mode_keyboard(lang, "pf"))

    elif query.data in {"ff_one_time", "ff_schedule"}:
        if not free_forward_connected(user_id):
            await query.edit_message_text(ltext(lang, "🔐 Token is not connected. Connect token first.", "🔐 Token connect করা নেই। আগে token connect করুন।"), reply_markup=free_forward_keyboard(lang))
            return ConversationHandler.END
        context.user_data["free_forward_sender"] = "bot"
        context.user_data["free_forward_mode"] = "schedule" if query.data == "ff_schedule" else "one_time"
        context.user_data["free_forward_step"] = "targets"
        await query.edit_message_text(
            ltext(
                lang,
                f"Send target group/channel IDs, @usernames, or public t.me links.\n\nSeparate by space, comma, or new line. Maximum {FREE_FORWARD_MAX_TARGETS} targets. The connected bot must be added to every target.",
                f"Target group/channel ID, @username অথবা public t.me link পাঠান।\n\nSpace, comma অথবা new line দিয়ে আলাদা করুন। সর্বোচ্চ {FREE_FORWARD_MAX_TARGETS} target। Connected bot প্রত্যেক target-এ add থাকতে হবে।",
            ),
            reply_markup=free_forward_cancel_keyboard(lang),
        )

    elif query.data in {"pf_one_time", "pf_schedule"}:
        if not personal_forward_connected(user_id):
            await query.edit_message_text(
                ltext(lang, "👤 Personal account is not connected. Connect it first.", "👤 Personal account connect করা নেই। আগে connect করুন।"),
                reply_markup=free_forward_keyboard(lang, free_forward_connected(user_id), free_forward_task_running(user_id), False),
            )
            return ConversationHandler.END
        context.user_data["free_forward_sender"] = "personal"
        context.user_data["free_forward_mode"] = "schedule" if query.data == "pf_schedule" else "one_time"
        context.user_data.pop("free_forward_step", None)
        await query.edit_message_text(
            ltext(
                lang,
                "Choose how to select target groups/channels for your personal account.",
                "Personal account-এর target group/channel কীভাবে select করবেন বেছে নিন।",
            ),
            reply_markup=personal_forward_target_source_keyboard(lang),
        )

    elif query.data == "pf_manual_targets":
        if not personal_forward_connected(user_id):
            await query.edit_message_text(
                ltext(lang, "👤 Personal account is not connected. Connect it first.", "👤 Personal account connect করা নেই। আগে connect করুন।"),
                reply_markup=free_forward_keyboard(lang, free_forward_connected(user_id), free_forward_task_running(user_id), False),
            )
            return ConversationHandler.END
        context.user_data["free_forward_sender"] = "personal"
        context.user_data["free_forward_step"] = "targets"
        await query.edit_message_text(
            ltext(
                lang,
                f"Send allowlisted target group/channel IDs, @usernames, or public t.me links.\n\nSeparate by space, comma, or new line. Maximum {PERSONAL_FORWARD_MAX_TARGETS} targets. Your personal account must already be a member and allowed to post.",
                f"Allowlisted target group/channel ID, @username অথবা public t.me link পাঠান।\n\nSpace, comma অথবা new line দিয়ে আলাদা করুন। সর্বোচ্চ {PERSONAL_FORWARD_MAX_TARGETS} target। আপনার personal account member এবং post permission থাকতে হবে।",
            ),
            reply_markup=free_forward_cancel_keyboard(lang),
        )

    elif query.data == "pf_pick_list":
        if not personal_forward_connected(user_id):
            await query.edit_message_text(
                ltext(lang, "👤 Personal account is not connected. Connect it first.", "👤 Personal account connect করা নেই। আগে connect করুন।"),
                reply_markup=free_forward_keyboard(lang, free_forward_connected(user_id), free_forward_task_running(user_id), False),
            )
            return ConversationHandler.END
        await query.edit_message_text(ltext(lang, "📋 Loading your groups/channels...", "📋 আপনার group/channel list loading হচ্ছে..."))
        try:
            dialogs = await list_personal_forward_dialogs(personal_forward_connection(user_id))
        except Exception as exc:
            await query.edit_message_text(
                ltext(lang, f"❌ Could not load groups/channels: {safe_free_forward_error(exc)}", f"❌ Group/channel list load করা যায়নি: {safe_free_forward_error(exc)}"),
                reply_markup=personal_forward_target_source_keyboard(lang),
            )
            return ConversationHandler.END
        context.user_data["personal_forward_dialogs"] = dialogs
        context.user_data["personal_forward_selected_targets"] = []
        context.user_data["personal_forward_picker_page"] = 0
        if not dialogs:
            await query.edit_message_text(
                ltext(lang, "No groups/channels were found on your connected account. You can enter a target manually instead.", "Connected account-এ কোনো group/channel পাওয়া যায়নি। চাইলে target manually লিখতে পারেন।"),
                reply_markup=personal_forward_target_source_keyboard(lang),
            )
            return ConversationHandler.END
        await query.edit_message_text(
            personal_forward_picker_text(lang, 0, dialogs, []),
            reply_markup=personal_forward_picker_keyboard(lang, 0, dialogs, []),
        )

    elif query.data.startswith("pf_pick_page_"):
        dialogs = context.user_data.get("personal_forward_dialogs") or []
        selected = context.user_data.get("personal_forward_selected_targets") or []
        try:
            page = int(query.data.rsplit("_", 1)[1])
        except Exception:
            page = 0
        context.user_data["personal_forward_picker_page"] = page
        await query.edit_message_text(
            personal_forward_picker_text(lang, page, dialogs, selected),
            reply_markup=personal_forward_picker_keyboard(lang, page, dialogs, selected),
        )

    elif query.data.startswith("pf_pick_toggle_"):
        dialogs = context.user_data.get("personal_forward_dialogs") or []
        selected = [str(value) for value in (context.user_data.get("personal_forward_selected_targets") or [])]
        page = int(context.user_data.get("personal_forward_picker_page") or 0)
        try:
            index = int(query.data.rsplit("_", 1)[1])
            dialog = dialogs[index]
        except Exception:
            await query.answer(ltext(lang, "That item is no longer available.", "এই item আর available নেই।"), show_alert=True)
            return ConversationHandler.END
        target = str(dialog.get("id"))
        if target in selected:
            selected.remove(target)
        elif len(selected) >= PERSONAL_FORWARD_MAX_TARGETS:
            await query.answer(ltext(lang, f"Maximum {PERSONAL_FORWARD_MAX_TARGETS} targets.", f"সর্বোচ্চ {PERSONAL_FORWARD_MAX_TARGETS} target."), show_alert=True)
            return ConversationHandler.END
        else:
            selected.append(target)
        context.user_data["personal_forward_selected_targets"] = selected
        await query.edit_message_text(
            personal_forward_picker_text(lang, page, dialogs, selected),
            reply_markup=personal_forward_picker_keyboard(lang, page, dialogs, selected),
        )

    elif query.data == "pf_pick_done":
        selected = [str(value) for value in (context.user_data.get("personal_forward_selected_targets") or [])]
        if not selected:
            await query.answer(ltext(lang, "Select at least one target.", "কমপক্ষে একটি target select করুন।"), show_alert=True)
            return ConversationHandler.END
        context.user_data["free_forward_sender"] = "personal"
        context.user_data["free_forward_targets"] = selected
        dialogs_by_id = {str(dialog.get("id")): dialog for dialog in (context.user_data.get("personal_forward_dialogs") or [])}
        names = [personal_forward_dialog_title(dialogs_by_id.get(target, {"title": target})) for target in selected[:5]]
        if context.user_data.get("free_forward_mode") == "schedule":
            context.user_data["free_forward_step"] = "interval"
            await query.edit_message_text(
                ltext(
                    lang,
                    f"✅ Selected {len(selected)} target(s): {', '.join(names)}\n\nSend interval in minutes. Minimum {PERSONAL_FORWARD_MIN_INTERVAL_MINUTES} minute(s).",
                    f"✅ {len(selected)} target select হয়েছে: {', '.join(names)}\n\nকত মিনিট পরপর পাঠাবেন লিখুন। Minimum {PERSONAL_FORWARD_MIN_INTERVAL_MINUTES} মিনিট।",
                ),
                reply_markup=free_forward_cancel_keyboard(lang),
            )
        else:
            context.user_data["free_forward_step"] = "message"
            await query.edit_message_text(
                ltext(
                    lang,
                    f"✅ Selected {len(selected)} target(s): {', '.join(names)}\n\nNow send the message to forward. Text, photo, video, document, audio, voice, animation, or sticker is supported.",
                    f"✅ {len(selected)} target select হয়েছে: {', '.join(names)}\n\nএখন যে message forward/send করতে চান সেটি পাঠান। Text, photo, video, document, audio, voice, animation বা sticker supported।",
                ),
                reply_markup=free_forward_cancel_keyboard(lang),
            )

    elif query.data == "pf_pick_noop":
        await query.answer()

    elif query.data == "ff_cancel_flow":
        await personal_forward_disconnect_pending(user_id)
        free_forward_clear_flow(context)
        connection = free_forward_connection(user_id)
        personal_connection = personal_forward_connection(user_id)
        await query.edit_message_text(
            free_forward_text(lang, bool(connection.get("token")), connection.get("bot_username"), free_forward_task_running(user_id), bool(personal_connection.get("session")), personal_connection.get("display_name")),
            reply_markup=free_forward_keyboard(lang, bool(connection.get("token")), free_forward_task_running(user_id), bool(personal_connection.get("session"))),
        )

    elif query.data == "ff_cancel_schedule":
        stopped = free_forward_cancel_schedule(user_id)
        await query.edit_message_text(
            ltext(lang, "🛑 Scheduled forward stopped." if stopped else "No scheduled forward is running.", "🛑 নির্দিষ্ট সময়ের forward বন্ধ হয়েছে।" if stopped else "কোনো নির্দিষ্ট সময়ের forward চলছে না।"),
            reply_markup=free_forward_keyboard(lang, free_forward_connected(user_id), False, personal_forward_connected(user_id)),
        )

    elif query.data == "ff_disconnect_token":
        free_forward_cancel_schedule(user_id)
        free_forward_clear_flow(context)
        FREE_FORWARD_CONNECTIONS.pop(user_id, None)
        for key in ["free_forward_token", "free_forward_bot_username", "free_forward_bot_id"]:
            context.user_data.pop(key, None)
        await query.edit_message_text(ltext(lang, "🔌 Token disconnected.", "🔌 Token disconnect হয়েছে।"), reply_markup=free_forward_keyboard(lang, False, False, personal_forward_connected(user_id)))

    elif query.data == "pf_disconnect_account":
        free_forward_cancel_schedule(user_id)
        await personal_forward_disconnect_pending(user_id)
        free_forward_clear_flow(context)
        PERSONAL_FORWARD_CONNECTIONS.pop(str(user_id), None)
        await query.edit_message_text(ltext(lang, "🔌 Personal account disconnected.", "🔌 Personal account disconnect হয়েছে।"), reply_markup=free_forward_keyboard(lang, free_forward_connected(user_id), False, False))

    elif query.data == "order_status":
        context.user_data.clear()
        context.user_data["order_status_lookup"] = True
        await query.edit_message_text(ltext(lang, "🔎 Order Status\n\nSend your Order ID or TrxID.\nExample: ORD-ABC123 or your bKash TrxID\n\nCommands: /order ORD-XXXXXX or /status TRXID", "🔎 Order Status\n\nOrder ID বা TrxID পাঠান।\nউদাহরণ: ORD-ABC123 অথবা TrxID\n\nCommand: /order ORD-XXXXXX বা /status TRXID"), reply_markup=back_keyboard(lang))

    elif query.data.startswith(TRACK_ORDER_CALLBACK_PREFIX):
        identifier = normalize_order_context_identifier(query.data.replace(TRACK_ORDER_CALLBACK_PREFIX, "", 1))
        await query.edit_message_text(
            order_status_text(identifier, user_id, lang),
            reply_markup=order_status_ai_keyboard(identifier, user_id, lang) or back_keyboard(lang),
        )

    elif query.data in {"referral_menu", "referral_link"}:
        context.user_data.clear()
        await show_referral_menu(query, context, user_id, lang, edit=True)

    elif query.data == "referral_withdraw":
        context.user_data.clear()
        if not referral_enabled():
            await query.edit_message_text(ltext(lang, "⚠️ Referral withdrawals are currently disabled by admin. Your link still works for relationship tracking.", "⚠️ Referral withdrawal বর্তমানে admin বন্ধ রেখেছেন। Relationship tracking-এর জন্য link কাজ করবে।"), reply_markup=referral_keyboard(lang, is_admin(user_id)))
            return ConversationHandler.END
        balance = referral_balance(user_id)
        min_withdraw = referral_min_withdraw_value()
        if balance + 1e-9 < min_withdraw:
            await query.edit_message_text(ltext(lang, f"💸 Referral balance too low.\n\nBalance: {round(balance, 6)} USD\nMinimum: {min_withdraw} USD", f"💸 Referral balance কম।\n\nBalance: {round(balance, 6)} USD\nMinimum: {min_withdraw} USD"), reply_markup=referral_keyboard(lang, is_admin(user_id)))
            return ConversationHandler.END
        context.user_data["ref_withdraw_step"] = "network"
        await query.edit_message_text(ltext(lang, f"💸 Referral withdrawal\n\nBalance: {round(balance, 6)} USD\nChoose a stablecoin network:", f"💸 Referral withdrawal\n\nBalance: {round(balance, 6)} USD\nStablecoin network বেছে নিন:"), reply_markup=stable_network_menu("refwd_net", lang))

    elif query.data.startswith("refwd_net_"):
        network = query.data.replace("refwd_net_", "", 1)
        if network not in STABLE_REFERRAL_NETWORKS:
            return ConversationHandler.END
        if not referral_enabled():
            await query.edit_message_text(ltext(lang, "⚠️ Referral withdrawals are currently disabled.", "⚠️ Referral withdrawal বর্তমানে বন্ধ।"), reply_markup=referral_keyboard(lang, is_admin(user_id)))
            return ConversationHandler.END
        context.user_data.clear()
        context.user_data.update({"ref_withdraw_step": "amount", "ref_withdraw_network": network})
        balance = referral_balance(user_id)
        min_withdraw = referral_min_withdraw_value()
        ni = NETWORKS[network]
        await query.edit_message_text(ltext(lang, f"💸 {ni['name']} withdrawal\n\nBalance: {round(balance, 6)} USD\nMinimum: {min_withdraw} USD\n\nSend amount in USD/{ni['symbol']}:", f"💸 {ni['name']} withdrawal\n\nBalance: {round(balance, 6)} USD\nMinimum: {min_withdraw} USD\n\nUSD/{ni['symbol']} amount লিখুন:"))

    elif query.data == "referral_admin":
        if not is_admin(user_id):
            return ConversationHandler.END
        context.user_data.clear()
        await query.edit_message_text(referral_admin_text(), reply_markup=referral_admin_keyboard(lang))

    elif query.data in {"refadmin_enable", "refadmin_disable"}:
        if not is_admin(user_id):
            return ConversationHandler.END
        value = "on" if query.data == "refadmin_enable" else "off"
        set_setting("referral_enabled", value)
        add_audit(user_id, "referral_setting_changed", "setting", "referral_enabled", value)
        await query.edit_message_text(referral_admin_text(), reply_markup=referral_admin_keyboard(lang))

    elif query.data in {"refadmin_set_percent", "refadmin_set_min"}:
        if not is_admin(user_id):
            return ConversationHandler.END
        context.user_data.clear()
        context.user_data["ref_admin_set"] = "percent" if query.data.endswith("percent") else "min"
        prompt = "Send referral percent from 0 to 20. This will not auto-enable referrals." if query.data.endswith("percent") else "Send minimum withdrawal amount in USD/stablecoin."
        await query.edit_message_text(prompt, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(tr("cancel", lang), callback_data="referral_admin")]]))

    elif query.data == "sellers_market":
        await show_seller_marketplace(query, lang)

    elif query.data == "seller_center":
        await show_seller_center(query, context, user_id, username)

    elif query.data == "seller_apply":
        context.user_data.clear()
        context.user_data["seller_apply_step"] = "name"
        await query.edit_message_text("🏪 Shop/display name লিখুন:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(tr("cancel", lang), callback_data="cancel")]]))
        return SELLER_APP_NAME

    elif query.data == "seller_guide":
        await query.edit_message_text(seller_guide_text(get_seller(user_id), lang), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(tr("back", lang), callback_data="seller_center")]]))

    elif query.data == "seller_wallet":
        seller = get_seller(user_id)
        if not seller or seller[5] != "approved":
            await query.edit_message_text("❌ Seller approved নয়।", reply_markup=back_keyboard(lang))
            return ConversationHandler.END
        if not SELLER_WALLET_MASTER_KEY:
            await query.edit_message_text("❌ SELLER_WALLET_MASTER_KEY missing. Admin .env এ set করলে automated seller wallet setup চালু হবে।", reply_markup=back_keyboard(lang))
            return ConversationHandler.END
        context.user_data.clear()
        await query.edit_message_text("🔐 Seller delivery wallet network বেছে নিন।\n\n⚠️ এই wallet থেকে automated delivery হবে; gas token রাখতে হবে।", reply_markup=seller_network_menu("sellerwallet", lang=lang))

    elif query.data == "seller_rates":
        await show_seller_rates(query, user_id, lang)

    elif query.data == "seller_pending":
        await show_seller_pending(query, user_id, lang)

    elif query.data == "seller_ledger":
        rows = list_seller_star_ledger(user_id, None, 10)
        if not rows:
            await query.edit_message_text("⭐ Ledger empty.", reply_markup=back_keyboard(lang))
        else:
            msg = "⭐ Seller Stars Ledger\n\n" + "\n".join(f"{r[0]} | {r[2]} | {r[3]} Stars | {r[4]}" for r in rows)
            await query.edit_message_text(msg, reply_markup=back_keyboard(lang))

    elif query.data == "admin_sellers":
        if not is_admin(user_id):
            return ConversationHandler.END
        pending = list_sellers_by_status("pending", 20)
        if not pending:
            await query.edit_message_text("✅ No pending seller applications.", reply_markup=back_keyboard(lang))
        else:
            for seller in pending:
                keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("✅ Approve", callback_data=f"sellerapp_a_{seller[0]}"), InlineKeyboardButton("❌ Reject", callback_data=f"sellerapp_r_{seller[0]}")]])
                await query.message.reply_text(f"🏪 Seller application\n\nID: {seller[0]}\n@{seller[1]}\nName: {seller[2]}\nbKash: {seller[3]}\nSupport: {seller[4]}", reply_markup=keyboard)
            await query.edit_message_text("Pending seller applications sent above.", reply_markup=back_keyboard(lang))

    elif query.data == "seller_payouts":
        if not is_admin(user_id):
            return ConversationHandler.END
        rows = list_pending_seller_payouts(20)
        if not rows:
            await query.edit_message_text("✅ No pending seller Stars payouts.", reply_markup=back_keyboard(lang))
        else:
            for r in rows:
                await query.message.reply_text(f"⭐ Pending seller payout\n\nLedger: {r[0]}\nSeller: {r[1]}\nOrder: {r[2]}\nStars: {r[3]}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ Mark paid", callback_data=f"payoutpaid_{r[0]}")]]))
            await query.edit_message_text("Pending payout entries sent above.", reply_markup=back_keyboard(lang))

    elif query.data.startswith("sellerapp_a_") or query.data.startswith("sellerapp_r_"):
        if not is_admin(user_id):
            return ConversationHandler.END
        action, seller_id = query.data.replace("sellerapp_", "", 1).split("_", 1)
        if action == "a":
            approve_seller(seller_id)
            seller = get_seller(seller_id)
            seller_lang = user_lang(seller_id)
            text = "✅ Seller approved."
            notify = seller_approval_text(seller, seller_lang)
        else:
            reject_seller(seller_id)
            text = "❌ Seller rejected."
            notify = ltext(user_lang(seller_id), f"❌ Seller application rejected. Support: @{SUPPORT_USERNAME.lstrip('@')}", f"❌ Seller application rejected হয়েছে। Support: @{SUPPORT_USERNAME.lstrip('@')}")
        add_audit(user_id, "seller_application_decision", "seller", seller_id, action)
        await query.edit_message_text(f"{text}\nSeller: {seller_id}")
        try:
            await query.get_bot().send_message(int(seller_id), notify)
        except Exception:
            pass

    elif query.data.startswith("payoutpaid_"):
        if not is_admin(user_id):
            return ConversationHandler.END
        ledger_id = query.data.replace("payoutpaid_", "", 1)
        mark_seller_payout_status(ledger_id, "paid_out", f"marked by {user_id}")
        add_audit(user_id, "seller_stars_payout_paid", "seller_star_ledger", ledger_id)
        await query.edit_message_text(f"✅ Payout marked paid.\nLedger: {ledger_id}", reply_markup=back_keyboard(lang))

    elif query.data.startswith("sellerpick_"):
        seller_id = query.data.replace("sellerpick_", "", 1)
        seller = get_seller(seller_id)
        if not seller or seller[5] != "approved":
            await query.edit_message_text("❌ Seller unavailable.", reply_markup=back_keyboard(lang))
            return ConversationHandler.END
        wallets = list_enabled_seller_wallets(seller_id)
        if not wallets:
            await query.edit_message_text(ltext(lang, "❌ This seller has not enabled any delivery network yet.", "❌ এই seller এখন কোনো network enable করেননি।"), reply_markup=back_keyboard(lang))
            return ConversationHandler.END
        await query.edit_message_text(
            panel("🛍️ Seller Order", f"🏪 {seller_public_name(seller)}\n📲 bKash: {seller[3]}\n\n{ltext(lang, 'Choose a payment method.', 'Payment method বেছে নিন।')}"),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📲 bKash", callback_data=f"sellerpay_bkash_{seller_id}"), InlineKeyboardButton("⭐ Stars", callback_data=f"sellerpay_stars_{seller_id}")],
                [InlineKeyboardButton(tr("back", lang), callback_data="sellers_market")],
            ]),
        )

    elif query.data.startswith("sellerpay_"):
        parts = query.data.split("_", 2)
        method, seller_id = parts[1], parts[2]
        seller = get_seller(seller_id)
        if not seller or seller[5] != "approved":
            await query.edit_message_text("❌ Seller unavailable.", reply_markup=back_keyboard(lang))
            return ConversationHandler.END
        context.user_data.clear()
        context.user_data.update({"seller_buy_seller_id": seller_id, "seller_buy_method": method, "seller_buy_username": username})
        await query.edit_message_text(f"🏪 {seller_public_name(seller)}\n\n{ltext(lang, 'Select a network:', 'Network বেছে নিন:')}", reply_markup=seller_network_menu("sellerbuy", seller_id, lang))

    elif query.data.startswith("sellerbuy_"):
        network = query.data.replace("sellerbuy_", "", 1)
        seller_id = context.user_data.get("seller_buy_seller_id")
        if not seller_id or network not in [row[1] for row in list_enabled_seller_wallets(seller_id)]:
            await query.edit_message_text("❌ Seller buy session expired.", reply_markup=back_keyboard(lang))
            return ConversationHandler.END
        context.user_data["seller_buy_network"] = network
        ni = NETWORKS[network]
        rate = seller_rate_or_global(seller_id, network)
        await query.edit_message_text(f"🌐 {ni['name']}\n💵 Rate: 1 {ni['symbol']} = {rate} BDT\n\n{ltext(lang, 'Enter the buyer destination wallet:', 'Buyer destination wallet দিন:')}\n{wallet_hint(network)}")
        return SELLER_BUY_WALLET

    elif query.data.startswith("sellerwallet_"):
        network = query.data.replace("sellerwallet_", "", 1)
        seller = get_seller(user_id)
        if not seller or seller[5] != "approved":
            await query.edit_message_text("❌ Seller approved নয়।", reply_markup=back_keyboard(lang))
            return ConversationHandler.END
        context.user_data.clear()
        context.user_data["seller_wallet_network"] = network
        await query.edit_message_text(f"🔐 {NETWORKS[network]['name']} delivery private key পাঠান।\n\n⚠️ Message auto-delete হবে। এই wallet থেকে seller orders auto delivery হবে। Gas token রাখবেন।")
        return SELLER_SETUP_KEY

    elif query.data.startswith("sellerrate_"):
        network = query.data.replace("sellerrate_", "", 1)
        context.user_data.clear()
        context.user_data["seller_rate_network"] = network
        await query.edit_message_text(f"📈 {NETWORKS[network]['name']} seller rate লিখুন (BDT per 1 {NETWORKS[network]['symbol']}).\n\n0 লিখলে global rate use হবে।")
        return SELLER_SET_RATE

    elif query.data.startswith("sordera_") or query.data.startswith("sorderr_"):
        order_id = query.data.split("_", 1)[1]
        order = get_seller_order(order_id)
        if not order:
            await query.edit_message_text("❌ Order not found.")
            return ConversationHandler.END
        if str(order[1]) != user_id:
            await query.edit_message_text("🚫 Only the assigned seller can approve this order.")
            return ConversationHandler.END
        if query.data.startswith("sorderr_"):
            update_seller_order(order_id, status="rejected")
            add_audit(user_id, "seller_order_rejected", "seller_order", order_id)
            await query.edit_message_text(f"❌ Seller order rejected.\n🧾 {order_id}")
            try:
                await query.get_bot().send_message(int(order[2]), f"❌ Seller order rejected.\n🧾 {order_id}\nSupport: @{SUPPORT_USERNAME.lstrip('@')}")
            except Exception:
                pass
            return ConversationHandler.END
        await query.edit_message_text(f"⏳ Approving seller order and sending crypto...\n🧾 {order_id}")
        ok, result = await complete_seller_order(query.get_bot(), order_id, user_id)
        add_audit(user_id, "seller_order_approved", "seller_order", order_id, str(result))
        await query.edit_message_text(("✅ Seller order completed." if ok else f"❌ Seller order failed: {result}") + f"\n🧾 {order_id}")

    elif query.data in {"seller_dashboard", "seller_dashboard_refresh"}:
        await query.edit_message_text("⏳ Loading seller dashboard...", reply_markup=back_keyboard(lang))
        try:
            text = seller_dashboard_text()
        except Exception as exc:
            text = f"❌ Dashboard failed: {exc}"
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Refresh", callback_data="seller_dashboard_refresh"), InlineKeyboardButton("💸 Request Payout", callback_data="request_payout")], [InlineKeyboardButton("🩺 Webhook Health", callback_data="webhook_health")], [InlineKeyboardButton(tr("back", lang), callback_data="back")]]))

    elif query.data == "webhook_health":
        await query.edit_message_text(webhook_health_text(), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Refresh", callback_data="webhook_health")], [InlineKeyboardButton(tr("back", lang), callback_data="back")]]))

    elif query.data == "bot_health":
        if not is_admin(user_id):
            return ConversationHandler.END
        await query.edit_message_text(bot_health_text(), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Refresh", callback_data="bot_health")], [InlineKeyboardButton(tr("back", lang), callback_data="back")]]))

    elif query.data == "restart_help":
        if not is_admin(user_id):
            return ConversationHandler.END
        await query.edit_message_text(restart_help_text(), reply_markup=back_keyboard(lang))

    elif query.data == "request_payout":
        context.user_data.clear()
        context.user_data["payout_request"] = True
        await query.edit_message_text("💸 Payout request\n\nAmount এবং method/details পাঠান।\nExample: 5000 bKash 01XXXXXXXXX Stars payout", reply_markup=back_keyboard(lang))

    elif query.data == "admin_report_daily":
        if not is_admin(user_id):
            return ConversationHandler.END
        await query.edit_message_text(report_text("daily"), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📈 Weekly", callback_data="admin_report_weekly"), InlineKeyboardButton(tr("back", lang), callback_data="back")]]))

    elif query.data == "admin_report_weekly":
        if not is_admin(user_id):
            return ConversationHandler.END
        await query.edit_message_text(report_text("weekly"), reply_markup=back_keyboard(lang))

    elif query.data == "backup_now":
        if not is_admin(user_id):
            return ConversationHandler.END
        await send_backup_document(query.get_bot(), ADMIN_ID)
        add_audit(user_id, "backup_requested", "database", "mouno.db", "telegram backup button")
        await query.edit_message_text("✅ Backup sent.", reply_markup=back_keyboard(lang))

    elif query.data == "admin_reservations":
        if not is_admin(user_id):
            return ConversationHandler.END
        await query.edit_message_text(reservations_text(), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Refresh", callback_data="admin_reservations"), InlineKeyboardButton(tr("back", lang), callback_data="back")]]))

    elif query.data == "admin_profit":
        if not is_admin(user_id):
            return ConversationHandler.END
        await query.edit_message_text(profit_text("daily"), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📈 Weekly", callback_data="admin_profit_weekly"), InlineKeyboardButton(tr("back", lang), callback_data="back")]]))

    elif query.data == "admin_profit_weekly":
        if not is_admin(user_id):
            return ConversationHandler.END
        await query.edit_message_text(profit_text("weekly"), reply_markup=back_keyboard(lang))

    elif query.data == "admin_gas":
        if not is_admin(user_id):
            return ConversationHandler.END
        await query.edit_message_text(gas_status_text(), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Refresh", callback_data="admin_gas"), InlineKeyboardButton(tr("back", lang), callback_data="back")]]))

    elif query.data == "admin_audit":
        if not is_admin(user_id):
            return ConversationHandler.END
        await query.edit_message_text(audit_text(), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Refresh", callback_data="admin_audit"), InlineKeyboardButton(tr("back", lang), callback_data="back")]]))

    elif query.data == "seller_badges":
        if not is_admin(user_id):
            return ConversationHandler.END
        sellers = list_seller_profiles(10)
        body = "Usage: /seller_badge USER_ID new|verified|trusted\n/seller USER_ID\n\n" + ("\n".join(f"{uid}: {SELLER_BADGES.get(status, status)} ({str(updated)[:16]})" for uid, status, updated in sellers) or "No seller profiles yet.")
        await query.edit_message_text(panel("🏷 Seller Badges", body), reply_markup=back_keyboard(lang))

    elif query.data == "ai_admin_help":
        if not is_admin(user_id):
            return ConversationHandler.END
        await query.edit_message_text("🤖 AI Admin\n\nUsage:\n/aiadmin why order failed ORD-123\n/aiadmin TRXID\n\nRead-only diagnostics only.", reply_markup=back_keyboard(lang))

    elif query.data == "ai_status":
        if not is_admin(user_id):
            return ConversationHandler.END
        await query.edit_message_text(ai_status_text(lang), reply_markup=back_keyboard(lang))

    elif query.data == "ai_usage":
        if not is_admin(user_id):
            return ConversationHandler.END
        await query.edit_message_text(ai_usage_text(), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Refresh", callback_data="ai_usage")], [InlineKeyboardButton(tr("back", lang), callback_data="back")]]))

    elif query.data == "ai_setup":
        if not is_admin(user_id):
            return ConversationHandler.END
        context.user_data.pop("ai_setup_provider", None)
        await query.edit_message_text(ai_setup_text(lang), reply_markup=ai_setup_keyboard(lang))
    elif query.data.startswith("ai_setup_"):
        if not is_admin(user_id):
            return ConversationHandler.END
        provider = query.data.replace("ai_setup_", "", 1)
        if provider == "cancel":
            context.user_data.pop("ai_setup_provider", None)
            await query.edit_message_text(ai_setup_text(lang), reply_markup=ai_setup_keyboard(lang))
            return ConversationHandler.END
        if provider not in AI_PROVIDER_LABELS:
            return ConversationHandler.END
        context.user_data["ai_setup_provider"] = provider
        await query.edit_message_text(ai_setup_provider_prompt(provider, lang), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel" if lang == "en" else "❌ বাতিল", callback_data="ai_setup_cancel")]]))

    elif query.data == "admin_payouts":
        if not is_admin(user_id):
            return ConversationHandler.END
        await show_payouts_to_target(query)

    elif query.data == "admin_user_analytics":
        if not is_admin(user_id):
            return ConversationHandler.END
        context.user_data.clear()
        context.user_data["admin_user_analytics_lookup"] = True
        await query.edit_message_text(tr("enter_user_id_analytics", lang), reply_markup=back_keyboard(lang))

    elif query.data.startswith("payout_paid_") or query.data.startswith("payout_reject_"):
        if not is_admin(user_id):
            return ConversationHandler.END
        await handle_payout_decision(query)

    elif query.data == "test_tools":
        if not is_admin(user_id):
            return ConversationHandler.END
        await query.edit_message_text("🧪 Test Tools\n\n/test_sms [amount]\n/test_seller_sms [amount]\n\nFake TEST* TrxID only. No real crypto is sent for matched pending orders.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🧪 Fake SMS 10 BDT", callback_data="test_sms_10")], [InlineKeyboardButton(tr("back", lang), callback_data="back")]]))

    elif query.data.startswith("test_sms_"):
        if not is_admin(user_id):
            return ConversationHandler.END
        amount = float(query.data.replace("test_sms_", "", 1))
        trx_id = f"TEST{gen_code(8)}"
        await process_bkash(context.application, f"bKash Payment Received Tk {amount} TrxID {trx_id}", "test_sms")
        add_audit(user_id, "test_sms_injected", "sms", trx_id, f"amount={amount}")
        await query.edit_message_text(f"✅ Fake SMS injected.\nTrxID: {trx_id}\nAmount: {amount} BDT", reply_markup=back_keyboard(lang))

    elif query.data == "ai_support":
        history = context.user_data.get("ai_support_history", [])
        order_context = context.user_data.get("ai_order_context_identifier")
        context.user_data.clear()
        context.user_data["ai_support"] = True
        context.user_data["ai_support_history"] = history
        if order_context:
            context.user_data["ai_order_context_identifier"] = order_context
        await query.edit_message_text(tr("ai_support_intro", lang), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(tr("cancel", lang), callback_data="ai_support_cancel")]]))

    elif query.data == "ai_support_cancel":
        history = context.user_data.get("ai_support_history", [])
        order_context = context.user_data.get("ai_order_context_identifier")
        context.user_data.clear()
        context.user_data["ai_support_history"] = history
        if order_context:
            context.user_data["ai_order_context_identifier"] = order_context
        await query.edit_message_text(home_text(lang=lang), reply_markup=main_menu(user_id, lang))

    elif query.data == "swap_start":
        await start_swap_flow(query, context, lang)

    elif query.data == "swap_cancel":
        context.user_data.clear()
        await query.edit_message_text(ltext(lang, "✅ Swap flow cancelled.", "✅ Swap flow বাতিল হয়েছে।"), reply_markup=main_menu(user_id, lang))

    elif query.data == "swap_noop":
        return ConversationHandler.END

    elif query.data.startswith("swap_from_page_") or query.data.startswith("swap_to_page_"):
        target = "from" if query.data.startswith("swap_from_page_") else "to"
        page = int(query.data.rsplit("_", 1)[1])
        context.user_data["swap_step"] = f"{target}_chain"
        await query.edit_message_reply_markup(reply_markup=swap_chain_keyboard(swap_chains(context), target, page, lang))

    elif query.data in {"swap_from_search", "swap_to_search"}:
        target = "from" if query.data == "swap_from_search" else "to"
        context.user_data["swap_step"] = f"{target}_chain_search"
        await query.edit_message_text(ltext(lang, "Type the chain name, key, or chain ID.", "Chain name, key, অথবা chain ID লিখুন।"), reply_markup=swap_cancel_keyboard(lang))

    elif query.data.startswith("swap_from_") or query.data.startswith("swap_to_"):
        target = "from" if query.data.startswith("swap_from_") else "to"
        chain_id = query.data.rsplit("_", 1)[1]
        chain = find_chain(swap_chains(context), chain_id)
        if not chain:
            await query.edit_message_text(ltext(lang, "❌ Chain not found. Start again.", "❌ Chain পাওয়া যায়নি। আবার শুরু করুন।"), reply_markup=main_menu(user_id, lang))
            return ConversationHandler.END
        context.user_data[f"swap_{target}_chain_id"] = int(chain["id"])
        context.user_data[f"swap_{target}_chain_name"] = chain_label(chain)
        if target == "from":
            context.user_data["swap_step"] = "from_token"
            await query.edit_message_text(ltext(lang, f"Source chain: {chain_label(chain)}\n\nSend source token contract address or symbol (example: USDC). For native coin, send native.", f"Source chain: {chain_label(chain)}\n\nSource token contract address অথবা symbol পাঠান (যেমন: USDC)। Native coin হলে native লিখুন।"), reply_markup=swap_cancel_keyboard(lang))
        else:
            context.user_data["swap_step"] = "to_token"
            await query.edit_message_text(ltext(lang, f"Destination chain: {chain_label(chain)}\n\nSend receive token contract address or symbol (example: USDC). For native coin, send native.", f"Destination chain: {chain_label(chain)}\n\nReceive token contract address অথবা symbol পাঠান (যেমন: USDC)। Native coin হলে native লিখুন।"), reply_markup=swap_cancel_keyboard(lang))

    elif query.data.startswith("swap_pref_"):
        preference = query.data.replace("swap_pref_", "", 1)
        intent = {
            "from_chain_id": context.user_data.get("swap_from_chain_id"),
            "from_chain_name": context.user_data.get("swap_from_chain_name"),
            "to_chain_id": context.user_data.get("swap_to_chain_id"),
            "to_chain_name": context.user_data.get("swap_to_chain_name"),
            "from_token": context.user_data.get("swap_from_token"),
            "to_token": context.user_data.get("swap_to_token"),
            "amount": context.user_data.get("swap_amount"),
            "wallet": context.user_data.get("swap_wallet"),
            "preference": preference,
        }
        if not all(intent.values()):
            context.user_data.clear()
            await query.edit_message_text(ltext(lang, "❌ Swap session expired. Start again.", "❌ Swap session expire হয়েছে। আবার শুরু করুন।"), reply_markup=main_menu(user_id, lang))
            return ConversationHandler.END
        await query.edit_message_text(ltext(lang, "⏳ Fetching live route quote...", "⏳ Live route quote আনা হচ্ছে..."))
        try:
            loop = asyncio.get_running_loop()
            quote = await loop.run_in_executor(None, lambda: quote_lifi(intent, api_key=swap_provider_key("lifi")))
        except requests.exceptions.RequestException as exc:
            logger.warning("Swap quote API error: %s", exc)
            error_msg = str(exc)
            if exc.response is not None:
                try:
                    data = exc.response.json()
                    error_msg = data.get("message") or data.get("errors", [{}])[0].get("message") or error_msg
                except Exception:
                    pass
            await query.edit_message_text(ltext(lang, f"❌ Quote failed: {error_msg}", f"❌ Quote আনা যায়নি: {error_msg}"), reply_markup=main_menu(user_id, lang))
            return ConversationHandler.END
        except Exception as exc:
            logger.warning("Swap quote failed: %s", exc)
            await query.edit_message_text(ltext(lang, f"❌ Quote failed: {exc}", f"❌ Quote আনা যায়নি: {exc}"), reply_markup=main_menu(user_id, lang))
            return ConversationHandler.END
        context.user_data["swap_intent"] = intent
        context.user_data["swap_quote"] = quote
        context.user_data["swap_step"] = "quoted"
        await query.edit_message_text(swap_quote_text(intent, quote, lang), reply_markup=swap_confirm_keyboard(context, user_id, lang))

    elif query.data == "swap_confirm_external":
        quote = context.user_data.get("swap_quote")
        intent = context.user_data.get("swap_intent")
        if not quote:
            await query.edit_message_text(ltext(lang, "❌ Quote expired. Start again.", "❌ Quote expire হয়েছে। আবার শুরু করুন।"), reply_markup=main_menu(user_id, lang))
            return ConversationHandler.END
        if not intent:
            await query.edit_message_text(ltext(lang, "❌ Swap session expired. Start again.", "❌ Swap session expire হয়েছে। আবার শুরু করুন।"), reply_markup=main_menu(user_id, lang))
            return ConversationHandler.END
        context.user_data["swap_step"] = "track_hash"
        await query.edit_message_text(swap_launcher_text(quote, lang), reply_markup=swap_launcher_keyboard(intent, quote, lang))

    elif query.data == "swap_confirm_in_bot":
        if not context.user_data.get("swap_quote"):
            await query.edit_message_text(ltext(lang, "❌ Quote expired. Start again.", "❌ Quote expire হয়েছে। আবার শুরু করুন।"), reply_markup=main_menu(user_id, lang))
            return ConversationHandler.END
        context.user_data["swap_step"] = "in_bot_password"
        await query.edit_message_text(ltext(lang, "🔐 Enter your Personal Wallet password to confirm and sign the swap/bridge transaction.", "🔐 Personal Wallet password দিন। এটি swap/bridge transaction sign করতে ব্যবহার হবে।"), reply_markup=swap_cancel_keyboard(lang))

    elif query.data == "swap_status":
        if not is_admin(user_id):
            return ConversationHandler.END
        await query.edit_message_text(panel("🔁 Swap Status", "\n".join(swap_status_lines())), reply_markup=back_keyboard(lang))

    elif query.data == "swap_setup":
        if not is_admin(user_id):
            return ConversationHandler.END
        context.user_data.pop("swap_setup_provider", None)
        await query.edit_message_text(swap_setup_text(lang), reply_markup=swap_setup_keyboard(lang))

    elif query.data.startswith("swap_setup_"):
        if not is_admin(user_id):
            return ConversationHandler.END
        provider = query.data.replace("swap_setup_", "", 1)
        if provider == "cancel":
            context.user_data.pop("swap_setup_provider", None)
            await query.edit_message_text(swap_setup_text(lang), reply_markup=swap_setup_keyboard(lang))
            return ConversationHandler.END
        if provider not in SWAP_PROVIDER_LABELS:
            return ConversationHandler.END
        context.user_data["swap_setup_provider"] = provider
        await query.edit_message_text(swap_setup_provider_prompt(provider, lang), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel" if lang == "en" else "❌ বাতিল", callback_data="swap_setup_cancel")]]))

    elif query.data.startswith(ORDER_AI_CALLBACK_PREFIX):
        identifier = normalize_order_context_identifier(query.data.replace(ORDER_AI_CALLBACK_PREFIX, "", 1))
        if not identifier:
            await query.edit_message_text(ltext(lang, "❌ Invalid order context.", "❌ Order context ভুল।"), reply_markup=back_keyboard(lang))
            return ConversationHandler.END
        context_line = _order_context_line(identifier, user_id, admin=is_admin(user_id))
        if "permission denied" in context_line or "no matching order/TrxID found" in context_line:
            await query.edit_message_text(ltext(lang, "🚫 This order is not available for AI support.", "🚫 এই order AI Support-এর জন্য পাওয়া যায়নি।"), reply_markup=back_keyboard(lang))
            return ConversationHandler.END
        context.user_data.clear()
        context.user_data["ai_support"] = True
        context.user_data["ai_support_history"] = []
        context.user_data["ai_order_context_identifier"] = identifier
        initial_question = ai_order_status_question(identifier, lang)
        pending_token = secrets.token_hex(8)
        context.user_data["ai_support_pending"] = pending_token
        await query.edit_message_text(
            ltext(
                lang,
                f"🤖 AI Support\n\nOrder context loaded: {identifier}\nPreparing a simple status explanation...\n\nAfter the answer, you can ask follow-up questions without typing the order ID again. Send /cancel to close.",
                f"🤖 AI Support\n\nOrder context loaded: {identifier}\nসহজ status explanation তৈরি করছি...\n\nউত্তর পাওয়ার পর follow-up প্রশ্ন করতে পারবেন; TrxID/Order ID আবার লিখতে হবে না। বন্ধ করতে /cancel লিখুন।",
            ),
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(tr("cancel", lang), callback_data="ai_support_cancel")]]),
        )
        chat_id = query.message.chat_id if query.message else query.from_user.id
        context.application.create_task(
            _send_ai_support_answer(context.bot, chat_id, user_id, initial_question, lang, pending_token, context.user_data)
        )

    elif query.data == "balance":
        await query.edit_message_text("⏳ Loading balance..." if lang == "en" else "⏳ ব্যালেন্স লোড হচ্ছে...", reply_markup=back_keyboard(lang))
        try:
            balances, evm_addr = get_all_balances()
            msg = panel(
                "💰 Live Balance",
                f"🔹 Solana USDC: {balances.get('solana', 'N/A')}\n"
                f"🔸 Polygon USDC: {balances.get('polygon', 'N/A')}\n"
                f"🟡 BSC USDT: {balances.get('bsc', 'N/A')}\n"
                f"🔺 Avalanche USDT: {balances.get('avalanche', 'N/A')}\n"
                f"🔷 ETH USDT: {balances.get('ethereum', 'N/A')}\n"
                f"🔷 ETH USDC: {balances.get('ethereum_usdc', 'N/A')}\n"
                f"🔵 Base USDC: {balances.get('base', 'N/A')}\n"
                f"🔴 Tron USDT: {balances.get('trc20', 'N/A')}\n"
                f"💎 TON: {balances.get('ton', 'N/A')}\n"
                f"{DIVIDER}\n🔑 EVM: `{short_wallet(evm_addr)}`\n⚡ Real-time balance"
            )
        except Exception as exc:
            msg = f"❌ ব্যালেন্স লোড ব্যর্থ!\n{exc}"
        await query.edit_message_text(
            msg,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Refresh" if lang == "en" else "🔄 রিফ্রেশ", callback_data="balance")], [InlineKeyboardButton(tr("back", lang), callback_data="back")]]),
        )

    elif query.data == "txlog":
        await show_txlog(query)

    elif query.data == "help":
        await query.edit_message_text(
            panel(
                "❓ Help Center",
                "🛒 Buy crypto\n"
                "1️⃣ Select network\n2️⃣ Send wallet address\n3️⃣ Enter amount\n4️⃣ Pay bKash or Stars\n5️⃣ Receive crypto automatically\n\n"
                "🎁 Gift code\nEnter code → wallet → receive asset\n\n"
                "🔐 My Wallet\nConnect wallet to check balance or send crypto\n\n"
                "⌨️ সব typed command দেখতে /help লিখুন\nType /help for all commands\n\n"
                f"📞 Support: @{SUPPORT_USERNAME.lstrip('@')}"
            ),
            reply_markup=back_keyboard(lang),
        )

    elif query.data == "my_wallet_menu":
        await show_my_wallet_menu(query, user_id)

    elif query.data in {"mw_setup", "mw_change"}:
        if query.data == "mw_change":
            delete_user_wallet(user_id)
        context.user_data.clear()
        await query.edit_message_text(ltext(lang, "🔐 Wallet Setup\n\nSelect your network:", "🔐 Wallet Setup\n\nআপনার Network বেছে নিন:"), reply_markup=user_network_menu(lang))
        return SETUP_NETWORK

    elif query.data == "mw_send":
        row = get_user_wallet(user_id)
        if not row:
            await query.edit_message_text(ltext(lang, "❌ No wallet found. Set it up first.", "❌ Wallet নেই! আগে setup করুন।"))
            return ConversationHandler.END
        network = row[2]
        net_info = NETWORKS.get(network, {"name": network})
        await query.edit_message_text(ltext(lang, f"💸 Send Crypto\n\n🌐 Network: {net_info['name']}\n👛 Your address: {row[3]}\n\nEnter the destination wallet address:\n📋 Example: {wallet_hint(network)}", f"💸 Crypto পাঠানো\n\n🌐 Network: {net_info['name']}\n👛 আপনার address: {row[3]}\n\nDestination wallet address দিন:\n📋 উদাহরণ: {wallet_hint(network)}"))
        return SEND_W_DEST

    elif query.data == "mw_delete":
        await query.edit_message_text(
            ltext(lang, "⚠️ Warning!\n\nYour wallet key will be deleted. This cannot be undone.\n\nAre you sure?", "⚠️ সতর্কতা!\n\nWallet key মুছে দেওয়া হবে।\nUndo করা যাবে না!\n\nনিশ্চিত?"),
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(ltext(lang, "✅ Yes, delete it", "✅ হ্যাঁ, মুছে দাও"), callback_data="del_confirm"), InlineKeyboardButton(ltext(lang, "❌ No", "❌ না"), callback_data="my_wallet_menu")]]),
        )

    elif query.data == "show_guide":
        await query.edit_message_text(GUIDE, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 ফিরে যান", callback_data="my_wallet_menu")]]))

    elif query.data == "check_mybal":
        context.user_data["uw_waiting_bal_password"] = True
        await query.edit_message_text(ltext(lang, "🔐 Enter your password:\n\n⚠️ Your message will be deleted after you send it.", "🔐 আপনার Password দিন:\n\n⚠️ Message পাঠানোর পর মুছে যাবে।"))
    elif query.data == "back":
        await query.edit_message_text(home_text(lang=lang), reply_markup=main_menu(query.from_user.id, lang))

    elif query.data == "buy":
        if is_maintenance_enabled() and not is_admin(user_id):
            await query.edit_message_text(maintenance_message(lang), reply_markup=back_keyboard(lang))
            return ConversationHandler.END
        await query.edit_message_text(panel("🛒 Buy Crypto", f"{tr('select_network', lang)}\n\n{rates_text('', lang)}"), reply_markup=network_menu("network", lang))

    elif query.data == "star_buy":
        if is_maintenance_enabled() and not is_admin(user_id):
            await query.edit_message_text(maintenance_message(lang), reply_markup=back_keyboard(lang))
            return ConversationHandler.END
        context.user_data.clear()
        context.user_data["star_step"] = "network"
        await query.edit_message_text(tr("stars_intro", lang), reply_markup=network_menu("star_network", lang))

    elif query.data == "admin_send":
        if not is_admin(user_id):
            return ConversationHandler.END
        context.user_data.clear()
        context.user_data["admin_send_step"] = "network"
        await query.edit_message_text(tr("admin_send_intro", lang), reply_markup=network_menu("admin_send_network", lang))

    elif query.data == "maintenance_on":
        if not is_admin(user_id):
            return ConversationHandler.END
        set_setting("maintenance_mode", "on")
        add_audit(user_id, "maintenance_on", "setting", "maintenance_mode")
        await query.edit_message_text(tr("maintenance_on", lang), reply_markup=back_keyboard(lang))

    elif query.data == "maintenance_off":
        if not is_admin(user_id):
            return ConversationHandler.END
        set_setting("maintenance_mode", "off")
        add_audit(user_id, "maintenance_off", "setting", "maintenance_mode")
        await query.edit_message_text(tr("maintenance_off", lang), reply_markup=back_keyboard(lang))

    elif query.data.startswith("admin_send_network_"):
        if not is_admin(user_id):
            return ConversationHandler.END
        network = query.data.replace("admin_send_network_", "")
        context.user_data["admin_send_network"] = network
        net_info = NETWORKS[network]
        await query.edit_message_text(
            f"🚀 {net_info['name']}\n\n{tr('admin_send_wallet', lang)}:\n\n📋 {tr('example', lang)}: {wallet_hint(network)}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(tr("cancel", lang), callback_data="admin_send_cancel")]]),
        )
        return ADMIN_SEND_WALLET

    elif query.data == "admin_send_confirm":
        if not is_admin(user_id):
            return ConversationHandler.END
        await complete_admin_send(query, context, user_id, lang)
        return ConversationHandler.END

    elif query.data == "admin_send_cancel":
        context.user_data.clear()
        await query.edit_message_text("❌ Cancelled." if lang == "en" else "❌ বাতিল হয়েছে।", reply_markup=back_keyboard(lang))
        return ConversationHandler.END

    elif query.data.startswith("retrytx_"):
        if not is_admin(user_id):
            return ConversationHandler.END
        trx_id = query.data.replace("retrytx_", "", 1)
        await retry_failed_transaction(query, trx_id, lang)
        return ConversationHandler.END

    elif query.data.startswith("star_network_"):
        network = query.data.replace("star_network_", "")
        context.user_data["star_network"] = network
        context.user_data["star_username"] = username
        net_info = NETWORKS[network]
        await query.edit_message_text(
            f"⭐ {net_info['name']}\n\n{tr('enter_wallet', lang, network=net_info['name'])}:\n\n📋 {tr('example', lang)}: {wallet_hint(network)}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(tr("cancel", lang), callback_data="cancel")]]),
        )
        return WAITING_STAR_WALLET

    elif query.data.startswith("network_"):
        network = query.data.replace("network_", "")
        context.user_data["network"] = network
        context.user_data["username"] = username
        net_info = NETWORKS[network]
        await query.edit_message_text(
            panel(
                f"✅ {net_info['name']}",
                f"💵 Rate: 1 {net_info['symbol']} = {get_rate(network)} BDT\n{DIVIDER}\n"
                f"👛 {tr('enter_wallet', lang, network=net_info['name'])}\n\n📋 {tr('example', lang)}: `{wallet_hint(network)}`"
            ),
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(tr("cancel", lang), callback_data="cancel")]]),
        )
        return WAITING_WALLET

    elif query.data == "confirm_buy":
        await confirm_buy(query, context, user_id, username)

    elif query.data == "cancel":
        if context.user_data.get("order_id"):
            release_stock_reservation(order_id=context.user_data.get("order_id"), reason="buyer_cancel", actor_id=user_id)
        context.user_data.clear()
        await query.edit_message_text("❌ বাতিল হয়েছে!\n\nআবার শুরু করতে /start দিন.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 মেনু", callback_data="back")]]))
        return ConversationHandler.END

    elif query.data == "setrate_menu":
        if not is_admin(user_id):
            return ConversationHandler.END
        await query.edit_message_text(f"⚙️ কোন নেটওয়ার্কের রেট পরিবর্তন করবেন?\n\n{rates_text('')}", reply_markup=network_menu("setrate"))

    elif query.data.startswith("setrate_"):
        if not is_admin(user_id):
            return ConversationHandler.END
        network = query.data.replace("setrate_", "")
        context.user_data["rate_network"] = network
        net_info = NETWORKS[network]
        await query.edit_message_text(f"⚙️ {net_info['name']} রেট পরিবর্তন\n\nবর্তমান রেট: 1 {net_info['symbol']} = {get_rate(network)} BDT\n\nনতুন রেট লিখুন (যেমন: 140):")
        return WAITING_RATE

    elif query.data == "redeem_menu":
        if is_maintenance_enabled() and not is_admin(user_id):
            await query.edit_message_text(maintenance_message(lang), reply_markup=back_keyboard(lang))
            return ConversationHandler.END
        context.user_data["redeem_step"] = "code"
        await query.edit_message_text(ltext(lang, "🎁 Redeem Gift Code\n\nEnter your gift code:\n\n📋 Example: ABC12345", "🎁 গিফট কোড রিডিম\n\nআপনার গিফট কোড লিখুন:\n\n📋 উদাহরণ: ABC12345"))

    elif query.data == "giveaway_menu":
        if is_maintenance_enabled() and not is_admin(user_id):
            await query.edit_message_text(maintenance_message(lang), reply_markup=back_keyboard(lang))
            return ConversationHandler.END
        await start_giveaway_flow(query, context, user_id, lang, edit=True)

    elif query.data.startswith("giveaway_"):
        if query.data.startswith("giveaway_duration_"):
            value = query.data.replace("giveaway_duration_", "", 1)
            if value == "custom":
                context.user_data["giveaway_step"] = "custom_duration"
                await query.edit_message_text(tr("enter_custom_duration", lang), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(tr("cancel", lang), callback_data="cancel")]]))
                return
            minutes = int(value)
            if context.user_data.get("giveaway_source") == "user_wallet":
                context.user_data["giveaway_minutes"] = minutes
                context.user_data["giveaway_step"] = "password"
                await query.edit_message_text(ltext(lang, "🔐 Enter your wallet password to confirm.\n\n⚠️ Your message will be deleted after you send it.", "🔐 Confirm করতে wallet password দিন।\n\n⚠️ Message পাঠানোর পর মুছে যাবে।"))
                return
            await create_giveaway_from_context(query, context, user_id, lang, minutes)
            return
        if query.data.startswith("giveaway_bonus_"):
            value = query.data.replace("giveaway_bonus_", "", 1)
            if value == "no":
                context.user_data["giveaway_bonus_count"] = 0
                context.user_data["giveaway_bonus_amount"] = 0
                context.user_data["giveaway_step"] = "duration"
                await query.edit_message_text(ltext(lang, "⏰ Choose giveaway duration:", "⏰ Giveaway মেয়াদ বেছে নিন:"), reply_markup=giveaway_duration_keyboard(lang))
                return
            context.user_data["giveaway_step"] = "bonus_count"
            await query.edit_message_text(ltext(lang, "🎯 How many early successful claimers get a bonus?", "🎯 প্রথম কতজন successful claimer bonus পাবে?"), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(tr("cancel", lang), callback_data="cancel")]]))
            return
        network = query.data.replace("giveaway_", "", 1)
        if not is_admin(user_id):
            return ConversationHandler.END
        if network not in NETWORKS:
            await query.edit_message_text("❌ Invalid network.", reply_markup=back_keyboard(lang))
            return
        context.user_data.update({"giveaway_step": "count", "giveaway_source": "admin_stock", "giveaway_network": network})
        await query.edit_message_text(ltext(lang, f"🎉 Giveaway on {NETWORKS[network]['name']}\n\nHow many recipients? Max 100.", f"🎉 {NETWORKS[network]['name']} Giveaway\n\nকতজন recipient? Max 100।"), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(tr("cancel", lang), callback_data="cancel")]]))

    elif query.data == "gencode_menu":
        if not is_admin(user_id):
            return ConversationHandler.END
        context.user_data.clear()
        context.user_data["gencode_step"] = "network"
        await query.edit_message_text(tr("code_select_network", lang), reply_markup=network_menu("gencode", lang))

    elif query.data.startswith("gencode_"):
        if not is_admin(user_id):
            return ConversationHandler.END
        network = query.data.replace("gencode_", "")
        context.user_data["gencode_network"] = network
        context.user_data["gencode_step"] = "amount"
        net_info = NETWORKS[network]
        await query.edit_message_text(
            f"🎟️ {net_info['name']}\n\n{tr('code_select_amount', lang, symbol=net_info['symbol'])}",
            reply_markup=gencode_amount_keyboard(lang),
        )

    elif query.data.startswith("gc_amount_"):
        if not is_admin(user_id):
            return ConversationHandler.END
        value = query.data.replace("gc_amount_", "")
        if value == "custom":
            context.user_data["gencode_step"] = "custom_amount"
            await query.edit_message_text(tr("enter_custom_amount", lang), reply_markup=back_keyboard(lang))
            return GEN_CUSTOM_AMOUNT
        context.user_data["gencode_amount"] = float(value)
        context.user_data["gencode_step"] = "duration"
        await query.edit_message_text(tr("code_select_duration", lang), reply_markup=gencode_duration_keyboard(lang))

    elif query.data.startswith("gc_duration_"):
        if not is_admin(user_id):
            return ConversationHandler.END
        value = query.data.replace("gc_duration_", "")
        if value == "custom":
            context.user_data["gencode_step"] = "custom_duration"
            await query.edit_message_text(tr("enter_custom_duration", lang), reply_markup=back_keyboard(lang))
            return GEN_CUSTOM_DURATION
        await create_gift_code_from_context(query, context, int(value), lang)

    elif query.data == "disable_code_menu":
        await show_disable_code_menu(query, user_id)

    elif query.data.startswith("docode_"):
        if not is_admin(user_id):
            return ConversationHandler.END
        code = query.data.replace("docode_", "")
        disable_code(code)
        await query.edit_message_text(f"✅ কোড বাতিল!\n\n🚫 Code: {code}\n\nএই কোড আর ব্যবহার করা যাবে না।", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 ফিরে যান", callback_data="back")]]))

    elif query.data.startswith("approve_"):
        await approve_order(query, user_id)

    elif query.data.startswith("reject_"):
        await reject_order(query, user_id)

    elif query.data == "sw_confirm":
        await query.edit_message_text(ltext(lang, "🔐 Enter your password:\n\n⚠️ Your message will be deleted after you send it.", "🔐 আপনার Password দিন:\n\n⚠️ Message পাঠানোর পর মুছে যাবে।"))
        return SEND_W_PASSWORD

    elif query.data == "sw_cancel":
        context.user_data.clear()
        await query.edit_message_text(ltext(lang, "❌ Cancelled.", "❌ বাতিল হয়েছে।"))
        return ConversationHandler.END

    elif query.data == "del_confirm":
        await query.edit_message_text(ltext(lang, "🔐 Enter your password to confirm:", "🔐 Password দিন নিশ্চিত করতে:"))
        return DEL_PASSWORD

    elif query.data == "del_cancel":
        await query.edit_message_text(ltext(lang, "❌ Cancelled.", "❌ বাতিল হয়েছে।"))
        return ConversationHandler.END


async def show_txlog(query):
    try:
        msg = txlog_text()
    except Exception as exc:
        msg = f"❌ লোড ব্যর্থ!\n{exc}"
    await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔄 রিফ্রেশ", callback_data="txlog")], [InlineKeyboardButton("🔙 ফিরে যান", callback_data="back")]]))


def txlog_text(limit=10):
    rows = get_recent_transactions(limit)
    if not rows:
        return panel("📜 TX Log", "No transactions yet.")
    msg = ""
    for row in rows:
        trx_id, bdt, crypto, network, wallet, status, created = row[:7]
        order_id = row[7] if len(row) > 7 else None
        ni = NETWORKS.get(network or "solana", {"name": network, "symbol": "?"})
        icon = "✅" if status == "completed" else "❌"
        sw = f"{wallet[:6]}...{wallet[-4:]}" if wallet else "N/A"
        sd = str(created)[:16] if created else "N/A"
        if trx_id.startswith("STAR-"):
            source = "⭐ Stars"
        elif trx_id.startswith("GIFT-"):
            source = "🎁 Gift Code"
        elif trx_id.startswith("ADMIN-"):
            source = "🛠️ Admin Send"
        elif trx_id.startswith("WALLET-"):
            source = "🔐 User Wallet"
        else:
            source = f"💰 {bdt} BDT"
        order_line = f"🧾 {order_id}\n" if order_id else ""
        msg += f"{icon} {sd}\n{order_line}{source}\n💵 {crypto} {ni['symbol']}\n🌐 {ni['name']}\n👛 `{sw}`\n🔑 `{trx_id}`\n{DIVIDER}\n"
    return panel("📜 TX Log", msg.rstrip(DIVIDER + "\n"))


async def txlog_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.reply_text(txlog_text())
    except Exception as exc:
        await update.message.reply_text(f"❌ লোড ব্যর্থ!\n{exc}")


async def ai_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = user_lang(update.effective_user.id)
    history = context.user_data.get("ai_support_history", [])
    order_context = context.user_data.get("ai_order_context_identifier")
    context.user_data.clear()
    context.user_data["ai_support"] = True
    context.user_data["ai_support_history"] = history
    if order_context:
        context.user_data["ai_order_context_identifier"] = order_context
    await update.message.reply_text(tr("ai_support_intro", lang))


async def swap_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = user_lang(update.effective_user.id)
    await start_swap_flow(update, context, lang)


async def cancel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = user_lang(update.effective_user.id)
    if context.user_data.get("swap_setup_provider"):
        context.user_data.pop("swap_setup_provider", None)
        await update.message.reply_text("✅ Swap API Setup cancelled." if lang == "en" else "✅ Swap API Setup বাতিল হয়েছে।", reply_markup=swap_setup_keyboard(lang))
        return ConversationHandler.END
    if context.user_data.get("swap_step"):
        context.user_data.clear()
        await update.message.reply_text("✅ Swap flow cancelled." if lang == "en" else "✅ Swap flow বাতিল হয়েছে।", reply_markup=main_menu(update.effective_user.id, lang))
        return ConversationHandler.END
    if context.user_data.get("ai_setup_provider"):
        context.user_data.pop("ai_setup_provider", None)
        await update.message.reply_text("✅ AI Setup cancelled." if lang == "en" else "✅ AI Setup বাতিল হয়েছে।", reply_markup=ai_setup_keyboard(lang))
        return ConversationHandler.END
    if context.user_data.get("ai_support"):
        history = context.user_data.get("ai_support_history", [])
        order_context = context.user_data.get("ai_order_context_identifier")
        context.user_data.clear()
        context.user_data["ai_support_history"] = history
        if order_context:
            context.user_data["ai_order_context_identifier"] = order_context
        await update.message.reply_text("✅ AI Support closed." if lang == "en" else "✅ AI Support বন্ধ হয়েছে।", reply_markup=main_menu(update.effective_user.id, lang))
        return ConversationHandler.END
    await update.message.reply_text("✅ Cancelled." if lang == "en" else "✅ বাতিল হয়েছে।", reply_markup=main_menu(update.effective_user.id, lang))
    return ConversationHandler.END


def users_keyboard(filter_type, page, total_pages, search_query=None, show_filters=False):
    rows = []
    # Pagination — search query is stored server-side, not in callback_data
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("⬅️ আগের পাতা", callback_data=f"us_p_{filter_type}_{page-1}"))
    nav.append(InlineKeyboardButton(f"{page+1}/{total_pages}", callback_data="us_noop"))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton("পরের পাতা ➡️", callback_data=f"us_p_{filter_type}_{page+1}"))
    if nav:
        rows.append(nav)

    if show_filters:
        rows.append([
            InlineKeyboardButton("🆕 New", callback_data="us_f_new"),
            InlineKeyboardButton("🏆 Top", callback_data="us_f_top"),
            InlineKeyboardButton("💤 Inactive", callback_data="us_f_inactive")
        ])
        rows.append([
            InlineKeyboardButton("🔎 Search", callback_data="us_f_search"),
            InlineKeyboardButton("📋 All", callback_data="us_f_all"),
            InlineKeyboardButton("🔙 Hide Filters", callback_data=f"us_p_{filter_type}_{page}_hide")
        ])
    else:
        rows.append([
            InlineKeyboardButton("📂 Filters 🔍", callback_data=f"us_p_{filter_type}_{page}_show"),
            InlineKeyboardButton("📤 Export CSV", callback_data="us_export")
        ])

    return InlineKeyboardMarkup(rows)

def users_list_text(rows, total, filter_type, page, limit=10):
    lines = [f"👥 Total Users: {total}"]
    if filter_type != "all":
        lines.append(f"🔍 Filter: {filter_type.capitalize()}")
    lines.append("")

    start_idx = page * limit + 1
    for i, row in enumerate(rows):
        user_id, username, first_name, joined_at, order_count, total_spent = row
        uname = f"@{username}" if username else (first_name or "no username")
        join_date = str(joined_at)[:10] if joined_at else "N/A"
        lines.append(f"{start_idx + i}. {uname}")
        lines.append(f"   🆔 ID: {user_id}")
        lines.append(f"   📅 Join: {join_date}")
        lines.append(f"   🛒 Orders: {order_count or 0}")
        lines.append(f"   💰 Total Spent: {round(total_spent or 0, 2)} BDT")
        lines.append("")

    if not rows:
        lines.append("No users found.")

    return "\n".join(lines)

async def export_users(update, context):
    if not is_admin(update.effective_user.id):
        return

    import csv
    from io import StringIO

    users = get_all_users_for_export()
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["User ID", "Username", "First Name", "Joined At", "Orders", "Total Spent BDT"])
    for row in users:
        writer.writerow(row)

    output.seek(0)
    bio = BytesIO(output.read().encode("utf-8-sig"))
    bio.name = f"users_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    await context.bot.send_document(
        chat_id=update.effective_chat.id,
        document=bio,
        caption="👥 User Data Export"
    )

async def users_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    args = context.args
    filter_type = "all"
    search_query = None

    if args:
        cmd = args[0].lower()
        if cmd == "export":
            return await export_users(update, context)
        elif cmd in ["new", "top", "inactive"]:
            filter_type = cmd
        elif cmd == "search":
            if len(args) > 1:
                filter_type = "search"
                search_query = " ".join(args[1:])
                # Store server-side so pagination callbacks stay within 64-byte limit
                context.user_data["user_search_query"] = search_query
            else:
                await update.message.reply_text("Usage: /users search <ID/Name/Username>")
                return

    rows, total = get_users_paged(filter_type, 0, search_query)
    total_pages = math.ceil(total / 10) if total > 0 else 1
    text = users_list_text(rows, total, filter_type, 0)
    markup = users_keyboard(filter_type, 0, total_pages, search_query)
    await update.message.reply_text(text, reply_markup=markup)

async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    total, completed, failed, total_bdt, total_crypto, total_profit, total_users, new_users_today = get_transaction_stats()
    pending_count = len(get_pending_orders(100))
    failed_count = len(get_failed_transactions(100))
    maintenance = "ON" if is_maintenance_enabled() else "OFF"
    await update.message.reply_text(
        "📊 Admin Dashboard\n\n"
        f"👥 Total Users: {total_users or 0}\n"
        f"🆕 New Users (Today): {new_users_today or 0}\n"
        "━━━━━━━━━━━━━━━\n"
        f"🧾 Total TX: {total or 0}\n"
        f"✅ Completed: {completed or 0}\n"
        f"❌ Failed: {failed or 0}\n"
        f"⏳ Pending bKash: {pending_count}\n"
        f"🔁 Retry queue: {failed_count}\n"
        f"💰 Completed BDT: {round(total_bdt or 0, 4)}\n"
        f"💵 Completed crypto total: {round(total_crypto or 0, 6)}\n"
        f"💹 Profit: {round(total_profit or 0, 2)} BDT\n"
        f"🛠️ Maintenance: {maintenance}"
    )


async def balances_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    await update.message.reply_text("⏳ Loading balances...")
    balances, evm_addr = get_all_balances()
    msg = "💰 Admin Balances\n\n"
    for network, info in NETWORKS.items():
        msg += f"🌐 {info['name']}: {balances.get(network, 'N/A')} {info['symbol']}\n"
    msg += f"\n🔑 EVM Address: {evm_addr}"
    await update.message.reply_text(msg)


async def maintenance_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    arg = context.args[0].lower() if context.args else "status"
    if arg in {"on", "enable", "enabled"}:
        set_setting("maintenance_mode", "on")
        add_audit(update.effective_user.id, "maintenance_on", "setting", "maintenance_mode")
        await update.message.reply_text("🛑 Maintenance mode ON")
    elif arg in {"off", "disable", "disabled"}:
        set_setting("maintenance_mode", "off")
        add_audit(update.effective_user.id, "maintenance_off", "setting", "maintenance_mode")
        await update.message.reply_text("✅ Maintenance mode OFF")
    else:
        await update.message.reply_text(f"🛠️ Maintenance: {'ON' if is_maintenance_enabled() else 'OFF'}\n\nUse /maintenance on or /maintenance off")


async def terms_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(terms_text(user_lang(update.effective_user.id)))


async def backup_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    await send_backup_document(update.get_bot(), ADMIN_ID)
    add_audit(update.effective_user.id, "backup_requested", "database", "mouno.db", "telegram command")


async def restart_help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    await update.message.reply_text(restart_help_text())


async def bot_health_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    await update.message.reply_text(bot_health_text())


async def send_backup_document(bot, chat_id):
    from db import DB_PATH

    if not os.path.exists(DB_PATH):
        await bot.send_message(chat_id, "❌ Database file not found.")
        return
    filename = f"mouno-backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}.db"
    with open(DB_PATH, "rb") as file:
        await bot.send_document(chat_id=chat_id, document=file, filename=filename)
    if BACKUP_UPLOAD_URL:
        try:
            with open(DB_PATH, "rb") as file:
                requests.post(BACKUP_UPLOAD_URL, files={"file": (filename, file)}, timeout=30)
        except Exception as exc:
            logger.error("Backup upload webhook failed: %s", exc)


async def show_payouts_to_target(target):
    rows = list_payout_requests("pending", 10)
    if not rows:
        await target.edit_message_text("✅ No pending payout requests.", reply_markup=back_keyboard("bn")) if hasattr(target, "edit_message_text") else await target.reply_text("✅ No pending payout requests.")
        return
    for req_id, order_id, user_id, amount, method, details, status, _note, created, _updated in rows:
        text = f"💸 Payout Request\n\nID: {req_id}\nOrder: {order_id or 'N/A'}\nUser: {user_id}\nAmount: {amount}\nMethod: {method}\nDetails: {details}\nStatus: {status}\nCreated: {str(created)[:16]}"
        markup = InlineKeyboardMarkup([[InlineKeyboardButton("✅ Mark Paid", callback_data=f"payout_paid_{req_id}"), InlineKeyboardButton("❌ Reject", callback_data=f"payout_reject_{req_id}")]])
        if hasattr(target, "message"):
            await target.message.reply_text(text, reply_markup=markup)
        elif hasattr(target, "reply_text"):
            await target.reply_text(text, reply_markup=markup)
        else:
            await target.edit_message_text(text, reply_markup=markup)


async def handle_payout_decision(query):
    if query.data.startswith("payout_paid_"):
        req_id = query.data.replace("payout_paid_", "", 1)
        status = "paid"
    else:
        req_id = query.data.replace("payout_reject_", "", 1)
        status = "rejected"
    row = get_payout_request(req_id)
    if not row:
        await query.edit_message_text("❌ Payout request not found.")
        return
    update_payout_request(req_id, status, "updated from Telegram")
    add_audit(query.from_user.id, f"payout_{status}", "payout", req_id)
    _id, _order, user_id, amount, method, details, *_ = row
    await query.edit_message_text(f"✅ Payout {status}.\n\nID: {req_id}\nUser: {user_id}\nAmount: {amount}\nMethod: {method}\nDetails: {details}")
    try:
        await query.get_bot().send_message(int(user_id), f"💸 আপনার payout request {status}.\n\nID: {req_id}\nAmount: {amount}\nMethod: {method}")
    except Exception:
        pass


async def order_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    lang = maybe_update_language(user_id, " ".join(context.args))
    if not context.args:
        await update.message.reply_text("Usage: /order ORD-XXXXXX\n/status TRXID_OR_ORDERID")
        return
    identifier = context.args[0]
    await update.message.reply_text(order_status_text(identifier, user_id, lang), reply_markup=order_status_ai_keyboard(identifier, user_id, lang, include_menu=False))


async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await order_cmd(update, context)


async def receipt_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if not context.args:
        await update.message.reply_text("Usage: /receipt ORD_OR_TRX")
        return
    await update.message.reply_text(completed_receipt_text(context.args[0], user_id))


async def seller_badge_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    if len(context.args) != 2 or context.args[1] not in SELLER_BADGES:
        await update.message.reply_text("Usage: /seller_badge USER_ID new|verified|trusted")
        return
    set_seller_status(context.args[0], context.args[1])
    add_audit(update.effective_user.id, "seller_badge_changed", "seller", context.args[0], context.args[1])
    await update.message.reply_text(f"✅ Seller badge updated.\nUser: {context.args[0]}\nBadge: {SELLER_BADGES[context.args[1]]}")


async def seller_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target = context.args[0] if context.args else str(update.effective_user.id)
    stats = get_seller_public_stats(target)
    total_done = (stats["completed_orders"] or 0) + (stats["failed_orders"] or 0)
    success = (stats["completed_orders"] / total_done * 100) if total_done else 0
    avg = stats.get("avg_delivery_seconds")
    avg_text = f"{round(avg / 60, 1)} min" if avg else "N/A"
    body = (
        f"User ID: {target}\n"
        f"Badge: {SELLER_BADGES.get(stats['status'], stats['status'])}\n"
        f"✅ Completed: {stats['completed_orders']}\n"
        f"❌ Failed: {stats['failed_orders']}\n"
        f"📊 Success rate: {round(success, 2)}%\n"
        f"💰 Volume: {round(stats['completed_bdt'], 2)} BDT / {round(stats['completed_crypto'], 6)} crypto\n"
        f"⚡ Avg delivery: {avg_text}\n"
        f"🕒 Last completed: {str(stats.get('last_completed_at') or 'N/A')[:19]}\n"
        f"🔒 Active reserves: {stats['active_reservations']} / {round(stats['reserved_crypto'], 6)} crypto"
    )
    await update.message.reply_text(panel("🏷 Seller Profile", body))


async def seller_dashboard_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ Loading seller dashboard...")
    await update.message.reply_text(seller_dashboard_text(), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Refresh", callback_data="seller_dashboard_refresh"), InlineKeyboardButton("💸 Request Payout", callback_data="request_payout")]]))


async def webhook_health_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    await update.message.reply_text(webhook_health_text())


async def report_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    period = context.args[0].lower() if context.args else "daily"
    if period not in {"daily", "weekly"}:
        period = "daily"
    await update.message.reply_text(report_text(period))


async def profit_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    period = context.args[0].lower() if context.args else "daily"
    if period not in {"daily", "weekly"}:
        period = "daily"
    await update.message.reply_text(profit_text(period))


async def costrate_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    if len(context.args) == 2:
        network = context.args[0].lower()
        if network not in NETWORKS:
            await update.message.reply_text("❌ Unknown network.")
            return
        try:
            rate = float(context.args[1])
        except Exception:
            await update.message.reply_text("Usage: /costrate NETWORK RATE")
            return
        set_cost_rate(network, rate)
        add_audit(update.effective_user.id, "cost_rate_changed", "network", network, f"rate={rate}")
        await update.message.reply_text(f"✅ Cost rate updated.\n{network}: {rate} BDT")
        return
    rates = get_all_cost_rates(NETWORKS.keys())
    await update.message.reply_text("💹 Cost Rates\n\n" + "\n".join(f"{net}: {rates.get(net) or 0} BDT" for net in NETWORKS) + "\n\nSet: /costrate NETWORK RATE")


async def gas_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    await update.message.reply_text(gas_status_text())


async def reservations_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    await update.message.reply_text(reservations_text())


async def audit_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    await update.message.reply_text(audit_text())


async def payout_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if context.args:
        await create_payout_from_text(update, user_id, " ".join(context.args))
        return
    context.user_data.clear()
    context.user_data["payout_request"] = True
    await update.message.reply_text("💸 Payout request\n\nAmount এবং method/details পাঠান।\nExample: 5000 bKash 01XXXXXXXXX Stars payout")


async def create_payout_from_text(update, user_id, text):
    parts = text.strip().split(maxsplit=1)
    try:
        amount = float(parts[0])
        if amount <= 0:
            raise ValueError
    except Exception:
        await update.message.reply_text("❌ Invalid amount. Example: 5000 bKash 01XXXXXXXXX")
        return
    details = parts[1] if len(parts) > 1 else "No details"
    method = details.split()[0] if details else "manual"
    req_id = create_payout_request(user_id, amount, method, details)
    await update.message.reply_text(f"✅ Payout request submitted.\nID: {req_id}\nAmount: {amount}\nMethod: {method}")
    try:
        await update.get_bot().send_message(ADMIN_ID, f"💸 New payout request\n\nID: {req_id}\nUser: {user_id}\nAmount: {amount}\nMethod/details: {details}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ Mark Paid", callback_data=f"payout_paid_{req_id}"), InlineKeyboardButton("❌ Reject", callback_data=f"payout_reject_{req_id}")]]))
    except Exception:
        pass


async def payouts_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    await show_payouts_to_target(update)


async def inject_test_sms(update: Update, context: ContextTypes.DEFAULT_TYPE, source="test_sms"):
    if not is_admin(update.effective_user.id):
        return
    try:
        amount = float(context.args[0]) if context.args else 10.0
    except Exception:
        amount = 10.0
    trx_id = f"TEST{gen_code(8)}"
    text = f"bKash Payment Received Tk {amount} TrxID {trx_id}"
    await process_bkash(context.application, text, source)
    add_audit(update.effective_user.id, "test_sms_injected", "sms", trx_id, f"source={source} amount={amount}")
    await update.message.reply_text(f"✅ Fake bKash notice injected.\nSource: {source}\nTrxID: {trx_id}\nAmount: {amount} BDT\n\nTEST TrxIDs are never auto-sent if matched to a pending order.")


async def test_sms_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await inject_test_sms(update, context, "test_sms")


async def test_seller_sms_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await inject_test_sms(update, context, "test_seller_sms")


def explain_order_failure(identifier):
    kind, row = find_order(identifier)
    if not row:
        return "No order found. Likely wrong Order ID/TrxID or user never submitted it."
    if kind == "pending":
        trx_id, _uid, bdt, crypto, _wallet, network, created = row[:7]
        sms = get_sms(trx_id)
        reason = "bKash notice exists but order is still pending; admin approval may be required." if sms else "Payment notice missing/delayed; webhook/SMS forwarder may be stale or TrxID may be wrong."
        return f"Pending order {row[7] if len(row)>7 else 'N/A'} / {trx_id}. Expected {bdt} BDT → {crypto} on {network}. Created {created}. Likely cause: {reason}"
    if kind == "transaction":
        trx_id, bdt, crypto, network, wallet, status, created, order_id, user_id, sig = row[:10]
        if status == "completed":
            return f"Order {order_id} is completed. TX signature exists: {bool(sig)}. No failure detected."
        if status == "failed":
            reason = failure_reason_text("transaction failed", network, "en")
            return f"Order {order_id} failed after payment context was saved. Network={network}, amount={crypto}, wallet={short_wallet(wallet)}. {reason} Check /failed and retry if safe."
        return f"Order {order_id} status is {status}. Check pending order/SMS log and seller balance. Created {created}."
    order_id, user_id, _username, network, wallet, amount, stars, status, _tg, _prov, tx_sig, error, created, updated = row
    if status == "failed":
        return f"Stars order {order_id} failed. Error: {error or 'unknown'}. {failure_reason_text(error, network, 'en')}"
    if status in {"pending", "paid"}:
        return f"Stars order {order_id} is {status}. Pending means invoice not paid; paid means Telegram payment arrived but crypto completion may still be waiting/failed."
    return f"Stars order {order_id} is {status}. TX={bool(tx_sig)}."


async def aiadmin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    if not context.args:
        await update.message.reply_text("Usage: /aiadmin why order failed ORD-123")
        return
    question = " ".join(context.args)
    identifiers = extract_support_identifiers(question)
    identifier = identifiers[0] if identifiers else next((arg for arg in reversed(context.args) if arg.upper().startswith(("ORD", "STAR", "TEST", "PAY", "SO")) or len(arg) >= 6), context.args[-1])
    local = explain_order_failure(identifier)
    ai_context = build_ai_support_context(question, update.effective_user.id, "en", admin=True)
    if configured_ai_providers():
        try:
            prompt = f"Read-only admin diagnostic. Explain likely order/payment/send failure causes and next safe checks. User asked: {question}"
            local = await asyncio.get_running_loop().run_in_executor(None, lambda: ask_ai_support(prompt, "en", ai_context))
        except Exception:
            pass
    await update.message.reply_text(f"🤖 AI Admin diagnostic\n\n{local}")


async def ai_usage_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    await update.message.reply_text(ai_usage_text())


async def daily_admin_jobs(app):
    while True:
        now = datetime.now()
        next_midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        await asyncio.sleep(max(60, (next_midnight - now).total_seconds()))
        try:
            await app.bot.send_message(ADMIN_ID, report_text("daily"))
            await send_backup_document(app.bot, ADMIN_ID)
        except Exception as exc:
            logger.error("Daily admin jobs failed: %s", exc)


def failed_retry_keyboard(trx_id):
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔁 Retry Send", callback_data=f"retrytx_{trx_id}")]])


def order_admin_summary(order_id, target_uid, trx_id, amount_bdt, crypto_amount, network, wallet, status):
    ni = NETWORKS.get(network, {"name": network, "symbol": "?"})
    lines = [
        f"📌 Status: {status}",
        f"🧾 Order: {order_id or 'N/A'}",
        f"👤 User: {target_uid}",
        f"🔑 TrxID: {trx_id}",
        f"🌐 {ni['name']}",
        f"💰 {amount_bdt or 0} BDT",
        f"💵 {crypto_amount or 0} {ni['symbol']}",
        f"👛 {short_wallet(wallet)}",
    ]
    return "\n".join(lines)


async def send_order_user_message(bot, target_uid, text, **kwargs):
    try:
        await bot.send_message(int(target_uid), text, **kwargs)
        return True
    except Exception as exc:
        logger.warning("Order user notification failed for %s: %s", target_uid, exc)
        return False


async def failed_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    rows = get_failed_transactions(10)
    if not rows:
        await update.message.reply_text("✅ No failed sends.")
        return
    for trx_id, bdt, crypto, network, wallet, _status, created, order_id, user_id, _sig in rows:
        ni = NETWORKS.get(network, {"name": network, "symbol": "?"})
        await update.message.reply_text(
            f"❌ Failed Send\n\n🧾 {order_id or 'N/A'}\n🔑 {trx_id}\n👤 {user_id}\n🌐 {ni['name']}\n💵 {crypto} {ni['symbol']}\n👛 {wallet}\n🕒 {str(created)[:16]}",
            reply_markup=failed_retry_keyboard(trx_id),
        )


async def retry_failed_transaction(query, trx_id, lang):
    row = get_transaction(trx_id)
    if not row:
        await query.edit_message_text("❌ Transaction not found.")
        return
    _trx_id, _bdt, crypto, network, wallet, status, _created, _order_id, _user_id, _old_sig = row[:10]
    source = row[10] if len(row) > 10 else None
    if status != "failed":
        await query.edit_message_text("⚠️ This transaction is not failed anymore.")
        return
    ni = NETWORKS.get(network, {"name": network, "symbol": "?", "explorer": ""})
    sufficient, current_bal = check_sufficient(network, crypto)
    if not sufficient and current_bal is not None:
        await query.edit_message_text(f"❌ Retry blocked: insufficient stock.\n\n{stock_detail(network, crypto, current_bal)}", reply_markup=failed_retry_keyboard(trx_id))
        return
    await query.edit_message_text("⏳ Retrying crypto send...")
    try:
        sig = await send_crypto(network, wallet, crypto)
        update_transaction(trx_id, sig=sig, status="completed")
        if source not in {"admin_send", "gift", "giveaway", "referral_withdrawal"}:
            record_referral_reward_for_transaction(_user_id, source or "retry", f"retry:{trx_id}", network, crypto, _bdt, f"order={_order_id} retry_source={source}")
        add_audit(query.from_user.id, "retry_send_completed", "transaction", trx_id)
        await query.edit_message_text("✅ Retry successful. Receipt image sent.", reply_markup=back_keyboard(lang))
        if _user_id:
            receipt_data = await make_receipt_data(
                query.get_bot(),
                _order_id,
                trx_id,
                network,
                crypto,
                wallet,
                sig,
                _user_id,
                bdt_amount=_bdt,
                title="Smart Crypto Buy",
            )
            await send_transaction_receipt(query.get_bot(), [_user_id, ADMIN_ID], receipt_data)
    except Exception as exc:
        reason = failure_reason_text(exc, network, lang)
        add_audit(query.from_user.id, "retry_send_failed", "transaction", trx_id, str(exc))
        await query.edit_message_text(f"❌ Retry failed again.\n\n{exc}\n\n💡 {reason}", reply_markup=failed_retry_keyboard(trx_id))
        if _user_id:
            user_reason = failure_reason_text(exc, network, user_lang(_user_id))
            await send_order_user_message(query.get_bot(), _user_id, f"⚠️ Admin retry failed again.\n\n🧾 Order: {_order_id or 'N/A'}\n🔑 TrxID: {trx_id}\n💡 {user_reason}\n\nSupport/admin will handle it. 📞 @{SUPPORT_USERNAME.lstrip('@')}")


def pending_order_keyboard(row):
    trx_id, user_id, _amount_bdt, _amount_usdc, _wallet, network, _created_at = row[:7]
    return [
        InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user_id}_{trx_id}_{network}"),
        InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user_id}_{trx_id}"),
    ]


def pending_orders_text(rows):
    if not rows:
        return "✅ No pending bKash orders."
    msg = "🧾 Pending bKash Orders\n\n"
    for row in rows:
        trx_id, user_id, amount_bdt, amount_usdc, wallet, network, created_at = row[:7]
        order_id = row[7] if len(row) > 7 else None
        net_info = NETWORKS.get(network, {"name": network, "symbol": "?"})
        short_wallet = f"{wallet[:8]}...{wallet[-6:]}" if wallet else "N/A"
        msg += (
            f"🔑 {trx_id}\n"
            f"🧾 {order_id or 'N/A'}\n"
            f"👤 User: {user_id}\n"
            f"🌐 {net_info['name']}\n"
            f"💰 {amount_bdt} BDT → {amount_usdc} {net_info['symbol']}\n"
            f"👛 {short_wallet}\n"
            f"🕒 {str(created_at)[:16]}\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
        )
    return msg


async def pending_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    rows = get_pending_orders(10)
    if not rows:
        await update.message.reply_text("✅ No pending bKash orders.")
        return
    await update.message.reply_text(pending_orders_text(rows))
    for row in rows:
        trx_id, user_id, amount_bdt, amount_usdc, _wallet, network, _created_at = row[:7]
        order_id = row[7] if len(row) > 7 else None
        net_info = NETWORKS.get(network, {"name": network, "symbol": "?"})
        await update.message.reply_text(
            f"Verify in bKash app:\n\n🧾 Order: {order_id or 'N/A'}\n🔑 TrxID: {trx_id}\n👤 User: {user_id}\n🌐 {net_info['name']}\n💰 {amount_bdt} BDT\n💵 {amount_usdc} {net_info['symbol']}",
            reply_markup=InlineKeyboardMarkup([pending_order_keyboard(row)]),
        )


async def show_my_wallet_menu(query, user_id):
    lang = user_lang(user_id)
    row = get_user_wallet(user_id)
    if row:
        network = row[2]
        net_info = NETWORKS.get(network, {"name": network, "symbol": "?"})
        keyboard = [
            [InlineKeyboardButton(ltext(lang, "💰 My Balance", "💰 আমার Balance"), callback_data="check_mybal"), InlineKeyboardButton(ltext(lang, "💸 Send Crypto", "💸 Crypto পাঠাও"), callback_data="mw_send")],
            [InlineKeyboardButton(ltext(lang, "🔄 Change Wallet", "🔄 Wallet পরিবর্তন"), callback_data="mw_change"), InlineKeyboardButton(ltext(lang, "🗑️ Delete Wallet", "🗑️ Wallet মুছো"), callback_data="mw_delete")],
            [InlineKeyboardButton(ltext(lang, "📖 User Guide", "📖 ব্যবহার গাইড"), callback_data="show_guide")],
            [InlineKeyboardButton(tr("back", lang), callback_data="back")],
        ]
        await query.edit_message_text(
            panel("🔐 My Wallet", f"✅ Connected\n\n🌐 Network: {net_info['name']}\n👛 Address: `{short_wallet(row[3])}`\n\n👇 Choose an action"),
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
    else:
        keyboard = [[InlineKeyboardButton(ltext(lang, "🔐 Connect Wallet", "🔐 Wallet সংযুক্ত করুন"), callback_data="mw_setup")], [InlineKeyboardButton(ltext(lang, "📖 User Guide", "📖 ব্যবহার গাইড"), callback_data="show_guide")], [InlineKeyboardButton(tr("back", lang), callback_data="back")]]
        await query.edit_message_text(panel("🔐 My Wallet", ltext(lang, "❌ No wallet connected yet.\n\nConnect a wallet to check balance and send crypto securely.", "❌ এখনো wallet connected নেই।\n\nBalance check ও crypto send করতে wallet connect করুন।")), reply_markup=InlineKeyboardMarkup(keyboard))


async def confirm_buy(query, context, user_id, username):
    lang = user_lang(user_id)
    amount_bdt = context.user_data.get("amount_bdt")
    crypto_amount = context.user_data.get("usdc_amount")
    wallet = context.user_data.get("wallet")
    network = context.user_data.get("network", "solana")
    if not all([amount_bdt, crypto_amount, wallet]):
        await query.edit_message_text("❌ Session expired. Send /start again." if lang == "en" else "❌ সেশন শেষ! /start দিয়ে আবার শুরু করুন।")
        return
    net_info = NETWORKS[network]
    sufficient, current_bal = check_sufficient(network, crypto_amount)
    if not sufficient and current_bal is not None:
        await query.edit_message_text(
            f"❌ Insufficient seller stock.\n\n{stock_detail(network, crypto_amount, current_bal)}\nPlease try a smaller amount or contact @{SUPPORT_USERNAME.lstrip('@')}.",
            reply_markup=back_keyboard(lang),
        )
        return
    order_id = context.user_data.get("order_id") or f"ORD-{gen_code(6)}"
    _res_id, order_id = create_stock_reservation(order_id, user_id, network, crypto_amount, ttl_minutes=15, reason="bkash_order")
    context.user_data["order_id"] = order_id
    context.user_data["waiting_trxid"] = True
    context.user_data["trx_deadline"] = asyncio.get_event_loop().time() + 900
    await query.edit_message_text(
        (
            f"🎯 {'Order Confirmed' if lang == 'en' else 'অর্ডার কনফার্ম'}!\n{DIVIDER}\n"
            f"🧾 Order: {order_id}\n"
            f"🌐 Network: {net_info['name']}\n"
            f"💰 {'Send exactly' if lang == 'en' else 'ঠিক'} {amount_bdt} BDT\n\n"
            f"📲 bKash: {BKASH_NUMBER}\n\n"
            f"✅ {'After payment, send your TrxID' if lang == 'en' else 'পাঠানোর পর TrxID লিখুন'}\n"
            f"⏰ {'Time limit: 15 minutes' if lang == 'en' else 'সময়সীমা: ১৫ মিনিট'}"
        ),
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(tr("cancel", lang), callback_data="cancel")]]),
    )
    try:
        await query.get_bot().send_message(ADMIN_ID, f"🛎️ নতুন অর্ডার!\n\n👤 @{username} ({user_id})\n🌐 {net_info['name']}\n💰 {amount_bdt} BDT\n💵 {crypto_amount} {net_info['symbol']}\n👛 {wallet}\n\n⏳ TrxID অপেক্ষায়...")
    except Exception as exc:
        logger.error(exc)


def gencode_amount_keyboard(lang):
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("0.5", callback_data="gc_amount_0.5"), InlineKeyboardButton("1", callback_data="gc_amount_1")],
            [InlineKeyboardButton("2", callback_data="gc_amount_2"), InlineKeyboardButton("5", callback_data="gc_amount_5")],
            [InlineKeyboardButton("10", callback_data="gc_amount_10"), InlineKeyboardButton(tr("custom_amount", lang), callback_data="gc_amount_custom")],
            [InlineKeyboardButton(tr("back", lang), callback_data="gencode_menu")],
        ]
    )


def gencode_duration_keyboard(lang):
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("15 min", callback_data="gc_duration_15"), InlineKeyboardButton("30 min", callback_data="gc_duration_30")],
            [InlineKeyboardButton("1 hour", callback_data="gc_duration_60"), InlineKeyboardButton("6 hours", callback_data="gc_duration_360")],
            [InlineKeyboardButton("24 hours", callback_data="gc_duration_1440"), InlineKeyboardButton(tr("custom_duration", lang), callback_data="gc_duration_custom")],
            [InlineKeyboardButton(tr("back", lang), callback_data="gencode_menu")],
        ]
    )


async def create_gift_code_from_context(target, context, minutes, lang):
    network = context.user_data.get("gencode_network", "solana")
    amount = float(context.user_data.get("gencode_amount", 0))
    if amount <= 0 or minutes <= 0:
        await target.edit_message_text("❌ Invalid amount or time." if lang == "en" else "❌ ভুল পরিমাণ বা সময়!")
        return
    code = gen_code()
    expires_at = (datetime.now() + timedelta(minutes=minutes)).isoformat()
    create_code(code, amount, expires_at, network)
    net_info = NETWORKS[network]
    hours, mins = divmod(minutes, 60)
    time_str = f"{hours}h {mins}m" if lang == "en" and hours else (f"{mins}m" if lang == "en" else (f"{hours} ঘণ্টা {mins} মিনিট" if hours > 0 else f"{mins} মিনিট"))
    context.user_data.clear()
    message = (
        f"{tr('code_created', lang)}\n\n"
        f"🎟️ Code: `{code}`\n"
        f"🌐 {net_info['name']}\n"
        f"💵 {amount} {net_info['symbol']}\n"
        f"⏰ {time_str}\n\n"
        f"⚠️ {'Single use only.' if lang == 'en' else 'শুধুমাত্র একজন ব্যবহার করতে পারবে!'}"
    )
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton(tr("gen_code", lang), callback_data="gencode_menu"), InlineKeyboardButton(tr("back", lang), callback_data="back")]])
    if hasattr(target, "edit_message_text"):
        await target.edit_message_text(message, parse_mode="Markdown", reply_markup=reply_markup)
    else:
        await target.reply_text(message, parse_mode="Markdown", reply_markup=reply_markup)


def giveaway_duration_keyboard(lang):
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("15 min", callback_data="giveaway_duration_15"), InlineKeyboardButton("30 min", callback_data="giveaway_duration_30")],
            [InlineKeyboardButton("1 hour", callback_data="giveaway_duration_60"), InlineKeyboardButton("6 hours", callback_data="giveaway_duration_360")],
            [InlineKeyboardButton("24 hours", callback_data="giveaway_duration_1440"), InlineKeyboardButton(tr("custom_duration", lang), callback_data="giveaway_duration_custom")],
            [InlineKeyboardButton(tr("cancel", lang), callback_data="cancel")],
        ]
    )


def giveaway_bonus_keyboard(lang):
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(ltext(lang, "No bonus", "Bonus নেই"), callback_data="giveaway_bonus_no"), InlineKeyboardButton(ltext(lang, "Set bonus", "Bonus সেট করুন"), callback_data="giveaway_bonus_set")],
            [InlineKeyboardButton(tr("cancel", lang), callback_data="cancel")],
        ]
    )


def giveaway_total_max(recipient_count, base_amount, early_bonus_count=0, early_bonus_amount=0):
    return round((int(recipient_count) * float(base_amount)) + (min(int(recipient_count), int(early_bonus_count or 0)) * float(early_bonus_amount or 0)), 8)


def giveaway_summary_text(lang, session_id, network, recipient_count, base_amount, early_bonus_count, early_bonus_amount, minutes, total_max, codes):
    ni = NETWORKS.get(network, {"name": network, "symbol": "?"})
    expires_at = (datetime.now() + timedelta(minutes=minutes)).strftime("%Y-%m-%d %H:%M")
    bonus_line = ltext(lang, "No early bonus.", "Early bonus নেই।")
    if int(early_bonus_count or 0) > 0 and float(early_bonus_amount or 0) > 0:
        bonus_line = ltext(lang, f"First {early_bonus_count} successful claimers get +{early_bonus_amount} {ni['symbol']} extra.", f"প্রথম {early_bonus_count} জন successful claimer +{early_bonus_amount} {ni['symbol']} extra পাবে।")
    code_lines = "\n".join(f"{i}. `{code}`" for i, code in enumerate(codes, 1))
    return (
        f"✅ {tr('giveaway', lang)} {ltext(lang, 'created!', 'তৈরি হয়েছে!')}\n{DIVIDER}\n"
        f"🧾 Session: `{session_id}`\n"
        f"🌐 {ni['name']}\n"
        f"👥 {ltext(lang, 'Recipients', 'প্রাপক')}: {recipient_count}\n"
        f"💵 {ltext(lang, 'Base', 'Base')}: {base_amount} {ni['symbol']}\n"
        f"🎯 {bonus_line}\n"
        f"⏰ {ltext(lang, 'Expires', 'মেয়াদ')}: {expires_at}\n"
        f"💰 {ltext(lang, 'Max payout', 'সর্বোচ্চ payout')}: {total_max} {ni['symbol']}\n{DIVIDER}\n"
        f"🎟️ Codes:\n{code_lines}"
    )


async def send_giveaway_summary(target, context, lang, text):
    chunks = []
    while len(text) > 3900:
        split_at = text.rfind("\n", 0, 3900)
        if split_at < 1:
            split_at = 3900
        chunks.append(text[:split_at])
        text = text[split_at:].lstrip()
    chunks.append(text)
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton(tr("giveaway", lang), callback_data="giveaway_menu"), InlineKeyboardButton(tr("back", lang), callback_data="back")]])
    first = True
    for chunk in chunks:
        if first and hasattr(target, "edit_message_text"):
            await target.edit_message_text(chunk, parse_mode="Markdown", reply_markup=reply_markup if len(chunks) == 1 else None)
        else:
            await context.bot.send_message(chat_id=target.message.chat_id if hasattr(target, "message") else target.chat_id, text=chunk, parse_mode="Markdown", reply_markup=reply_markup if chunk == chunks[-1] else None)
        first = False


async def giveaway_target_text(target, text, reply_markup=None):
    if hasattr(target, "edit_message_text"):
        await target.edit_message_text(text, reply_markup=reply_markup)
    else:
        await target.reply_text(text, reply_markup=reply_markup)


async def start_giveaway_flow(target, context, user_id, lang, edit=False):
    context.user_data.clear()
    if is_admin(user_id):
        context.user_data.update({"giveaway_step": "network", "giveaway_source": "admin_stock"})
        text = ltext(lang, "🎉 Giveaway\n\nSelect payout network. Admin giveaways use bot/admin stock.", "🎉 Giveaway\n\nPayout network বেছে নিন। Admin giveaway bot/admin stock থেকে যাবে।")
        if edit:
            await target.edit_message_text(text, reply_markup=network_menu("giveaway", lang))
        else:
            await target.reply_text(text, reply_markup=network_menu("giveaway", lang))
        return
    row = get_user_wallet(user_id)
    if not row:
        text = ltext(lang, "❌ Connect your wallet first via /setup or My Wallet. Non-admin giveaways are funded only from your connected wallet.", "❌ আগে /setup বা My Wallet থেকে wallet connect করুন। Non-admin giveaway শুধু আপনার connected wallet থেকে fund হবে।")
        if edit:
            await target.edit_message_text(text, reply_markup=back_keyboard(lang))
        else:
            await target.reply_text(text, reply_markup=back_keyboard(lang))
        return
    network = row[2]
    if network == "ton":
        text = ltext(lang, "❌ TON wallet-funded giveaways are not available yet because automatic private-key sending is not supported for TON.", "❌ TON wallet-funded giveaway এখন available নয়, কারণ TON private-key auto-send এখনও support করে না।")
        if edit:
            await target.edit_message_text(text, reply_markup=back_keyboard(lang))
        else:
            await target.reply_text(text, reply_markup=back_keyboard(lang))
        return
    if not SELLER_WALLET_MASTER_KEY:
        text = ltext(lang, "❌ Wallet-funded giveaways are temporarily unavailable. Admin must configure SELLER_WALLET_MASTER_KEY.", "❌ Wallet-funded giveaway আপাতত unavailable। Admin-কে SELLER_WALLET_MASTER_KEY configure করতে হবে।")
        if edit:
            await target.edit_message_text(text, reply_markup=back_keyboard(lang))
        else:
            await target.reply_text(text, reply_markup=back_keyboard(lang))
        return
    context.user_data.update({"giveaway_step": "count", "giveaway_source": "user_wallet", "giveaway_network": network})
    ni = NETWORKS.get(network, {"name": network, "symbol": "?"})
    text = ltext(lang, f"🎉 Giveaway\n\nFunding source: your connected wallet\n🌐 {ni['name']}\n👛 {row[3]}\n\nHow many recipients? Max 100.", f"🎉 Giveaway\n\nFunding source: আপনার connected wallet\n🌐 {ni['name']}\n👛 {row[3]}\n\nকতজন recipient? Max 100।")
    if edit:
        await target.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(tr("cancel", lang), callback_data="cancel")]]))
    else:
        await target.reply_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(tr("cancel", lang), callback_data="cancel")]]))


async def create_giveaway_from_context(target, context, user_id, lang, minutes, password=None):
    network = context.user_data.get("giveaway_network")
    source = context.user_data.get("giveaway_source")
    recipient_count = int(context.user_data.get("giveaway_count", 0))
    base_amount = float(context.user_data.get("giveaway_base_amount", 0))
    early_bonus_count = int(context.user_data.get("giveaway_bonus_count", 0) or 0)
    early_bonus_amount = float(context.user_data.get("giveaway_bonus_amount", 0) or 0)
    total_max = giveaway_total_max(recipient_count, base_amount, early_bonus_count, early_bonus_amount)
    if not network or source not in {"admin_stock", "user_wallet"} or recipient_count <= 0 or recipient_count > 100 or base_amount <= 0 or minutes <= 0:
        await giveaway_target_text(target, ltext(lang, "❌ Giveaway session invalid. Start again with /giveaway.", "❌ Giveaway session invalid। /giveaway দিয়ে আবার শুরু করুন।"))
        context.user_data.clear()
        return
    encrypted_key = salt = wallet_address = None
    if source == "admin_stock":
        sufficient, current_bal = check_sufficient(network, total_max)
        if not sufficient and current_bal is not None:
            await giveaway_target_text(target, ltext(lang, f"❌ Insufficient admin stock for max payout.\n\n{stock_detail(network, total_max, current_bal)}", f"❌ Max payout এর জন্য admin stock পর্যাপ্ত নয়।\n\n{stock_detail(network, total_max, current_bal)}"))
            return
    else:
        if not SELLER_WALLET_MASTER_KEY:
            await giveaway_target_text(target, ltext(lang, "❌ Wallet-funded giveaways are unavailable: SELLER_WALLET_MASTER_KEY is missing.", "❌ Wallet-funded giveaway unavailable: SELLER_WALLET_MASTER_KEY missing."))
            return
        bal, balance_network, error = get_user_balance(user_id, password or "")
        if error == "wrong_password":
            await giveaway_target_text(target, ltext(lang, "❌ Wrong password. Giveaway not created.", "❌ ভুল Password। Giveaway তৈরি হয়নি।"))
            return
        if error:
            await giveaway_target_text(target, ltext(lang, f"❌ Could not verify wallet balance.\n{error}", f"❌ Wallet balance verify করা যায়নি।\n{error}"))
            return
        if balance_network != network:
            await giveaway_target_text(target, ltext(lang, "❌ Wallet network changed. Start again.", "❌ Wallet network পরিবর্তন হয়েছে। আবার শুরু করুন।"))
            context.user_data.clear()
            return
        if bal is not None and total_max > float(bal):
            ni = NETWORKS.get(network, {"symbol": "?"})
            await giveaway_target_text(target, ltext(lang, f"❌ Insufficient wallet balance.\nNeed: {total_max} {ni['symbol']}\nBalance: {bal} {ni['symbol']}", f"❌ Wallet balance পর্যাপ্ত নয়।\nNeed: {total_max} {ni['symbol']}\nBalance: {bal} {ni['symbol']}"))
            return
        row = get_user_wallet(user_id)
        if not row or row[2] != network:
            await giveaway_target_text(target, ltext(lang, "❌ Wallet not found. Start again with /setup.", "❌ Wallet পাওয়া যায়নি। /setup দিয়ে শুরু করুন।"))
            return
        private_key = decrypt_key(row[0], row[1], password or "")
        encrypted_key, salt = encrypt_seller_key(private_key)
        wallet_address = row[3]
    session_id = f"GIVE-{gen_code(6)}"
    while get_giveaway_session(session_id):
        session_id = f"GIVE-{gen_code(6)}"
    codes = []
    while len(codes) < recipient_count:
        code = gen_code()
        if code not in codes and not get_code(code):
            codes.append(code)
    expires_at = (datetime.now() + timedelta(minutes=minutes)).isoformat()
    create_giveaway_session(session_id, user_id, source, network, base_amount, recipient_count, early_bonus_count, early_bonus_amount, expires_at, encrypted_key, salt, wallet_address)
    create_giveaway_codes(session_id, codes)
    context.user_data.clear()
    text = giveaway_summary_text(lang, session_id, network, recipient_count, base_amount, early_bonus_count, early_bonus_amount, minutes, total_max, codes)
    await send_giveaway_summary(target, context, lang, text)


async def show_disable_code_menu(query, user_id):
    if not is_admin(user_id):
        return
    active_codes = get_all_active_codes()
    if not active_codes:
        await query.edit_message_text("✅ কোনো সক্রিয় কোড নেই।", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 ফিরে যান", callback_data="back")]]))
        return
    keyboard = []
    for code, amount, network, _expires_at in active_codes:
        ni = NETWORKS.get(network, {"symbol": "?"})
        keyboard.append([InlineKeyboardButton(f"🚫 {code} | {amount} {ni['symbol']} | {network}", callback_data=f"docode_{code}")])
    keyboard.append([InlineKeyboardButton("🔙 ফিরে যান", callback_data="back")])
    await query.edit_message_text("🚫 কোন কোড বাতিল করবেন?", reply_markup=InlineKeyboardMarkup(keyboard))


async def approve_order(query, user_id):
    if not is_admin(user_id):
        return
    _prefix, target_uid, trx_id, network = query.data.split("_", 3)
    if trx_id.startswith("TEST"):
        add_audit(user_id, "test_order_approve_blocked", "pending_order", trx_id)
        await query.edit_message_text("🧪 Test TrxID approval blocked. Fake SMS notices never send real crypto.")
        return
    net_info = NETWORKS.get(network, {"name": network, "symbol": "?", "explorer": ""})
    pending = get_pending_order(trx_id)
    target_wallet = pending[4] if pending and pending[4] else get_wallet(target_uid)
    if not target_wallet:
        await query.edit_message_text(f"❌ User এর wallet পাওয়া যায়নি!\nUser ID: {target_uid}")
        return

    sms_row = get_sms(trx_id)
    if sms_row:
        amount_bdt = sms_row[1]
        crypto_amount = round(amount_bdt / get_rate(network), 6)
    else:
        amount_bdt = 0
        crypto_amount = 0

    order_id = None
    if pending:
        amount_bdt = pending[2]
        crypto_amount = pending[3]
        target_wallet = pending[4] or target_wallet
        order_id = pending[7] if len(pending) > 7 else None

    await query.edit_message_text(
        "✅ Approved!\n\n⏳ Crypto পাঠানো হচ্ছে...\n\n"
        + order_admin_summary(order_id, target_uid, trx_id, amount_bdt, crypto_amount, network, target_wallet, "manual verified/sending")
    )

    sufficient, current_bal = check_sufficient(network, crypto_amount, exclude_order_id=order_id, exclude_trx_id=trx_id)
    if not sufficient and current_bal is not None:
        await query.edit_message_text(f"❌ Insufficient stock.\n\n{stock_detail(network, crypto_amount, current_bal)}")
        return

    try:
        sig = await send_crypto(network, target_wallet, crypto_amount)
        order_id = save_transaction(trx_id, target_uid, amount_bdt, crypto_amount, target_wallet, sig, "completed", network, order_id=order_id, source="bkash")
        record_referral_reward_for_transaction(target_uid, "bkash", trx_id, network, crypto_amount, amount_bdt, f"order={order_id}")
        consume_stock_reservation(order_id=order_id, trx_id=trx_id)
        delete_pending_order(trx_id)
        add_audit(user_id, "order_approved", "transaction", trx_id, f"order={order_id}")
        await query.edit_message_text("✅ Crypto sent. Receipt image sent.")
        receipt_data = await make_receipt_data(query.get_bot(), order_id, trx_id, network, crypto_amount, target_wallet, sig, target_uid, bdt_amount=amount_bdt, title="Smart Crypto Buy")
        await send_transaction_receipt(query.get_bot(), [target_uid, ADMIN_ID], receipt_data)
    except Exception as exc:
        reason = failure_reason_text(exc, network, lang)
        order_id = save_transaction(trx_id, target_uid, amount_bdt, crypto_amount, target_wallet, "", "failed", network, order_id=order_id, source="bkash")
        release_stock_reservation(order_id=order_id, trx_id=trx_id, reason="admin_approve_send_failed", actor_id="system")
        add_audit(user_id, "order_approve_send_failed", "transaction", trx_id, str(exc))
        await query.edit_message_text(f"❌ Payment verified, but crypto send failed.\n\n{order_admin_summary(order_id, target_uid, trx_id, amount_bdt, crypto_amount, network, target_wallet, 'send failed/retry needed')}\n\nError: {exc}\n\n💡 {reason}", reply_markup=failed_retry_keyboard(trx_id))
        target_lang = user_lang(target_uid)
        user_reason = failure_reason_text(exc, network, target_lang)
        await send_order_user_message(
            query.get_bot(),
            target_uid,
            f"✅ Your payment was manually verified by admin.\n\n⚠️ Crypto delivery hit a temporary issue. Admin will retry or contact you.\n\n🧾 Order: {order_id or 'N/A'}\n🔑 TrxID: {trx_id}\n💡 {user_reason}\n📞 Support: @{SUPPORT_USERNAME.lstrip('@')}"
            if target_lang == "en"
            else f"✅ আপনার payment admin manually verified করেছেন।\n\n⚠️ Crypto পাঠাতে temporary সমস্যা হয়েছে। Admin retry করবেন বা support contact করবেন।\n\n🧾 Order: {order_id or 'N/A'}\n🔑 TrxID: {trx_id}\n💡 {user_reason}\n📞 Support: @{SUPPORT_USERNAME.lstrip('@')}",
        )
        logger.error("Admin approve send failed: %s", exc)


async def reject_order(query, user_id):
    if not is_admin(user_id):
        return
    _prefix, target_uid, trx_id = query.data.split("_", 2)
    pending = get_pending_order(trx_id)
    order_id = pending[7] if pending and len(pending) > 7 else None
    if pending:
        amount_bdt, crypto_amount, wallet, network = pending[2], pending[3], pending[4], pending[5]
    else:
        amount_bdt, crypto_amount, wallet, network = 0, 0, get_wallet(target_uid), "solana"
    delete_pending_order(trx_id)
    release_stock_reservation(order_id=order_id, trx_id=trx_id, reason="admin_reject", actor_id=user_id)
    add_audit(user_id, "order_rejected", "pending_order", trx_id, f"order={order_id}")
    await query.edit_message_text(f"❌ Rejected!\n\n{order_admin_summary(order_id, target_uid, trx_id, amount_bdt, crypto_amount, network, wallet, 'rejected/manual verify failed')}")
    await send_order_user_message(query.get_bot(), target_uid, f"❌ আপনার পেমেন্ট verify করা যায়নি।\n\n🧾 Order: {order_id or 'N/A'}\n🔑 TrxID: {trx_id}\n\nসঠিক TrxID নিশ্চিত করুন অথবা যোগাযোগ করুন:\n📞 @{SUPPORT_USERNAME.lstrip('@')}")


async def waiting_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    wallet = update.message.text.strip()
    user_id = str(update.effective_user.id)
    lang = user_lang(user_id)
    network = context.user_data.get("network", "solana")
    net_info = NETWORKS[network]
    if not valid_wallet(network, wallet):
        await update.message.reply_text(f"{tr('invalid_wallet', lang)}\n\n{tr('enter_wallet', lang, network=net_info['name'])}.")
        return WAITING_WALLET
    save_wallet(user_id, wallet)
    context.user_data["wallet"] = wallet
    await update.message.reply_text(panel("👛 Wallet Saved", f"🌐 {net_info['name']}\n👛 `{short_wallet(wallet)}`\n{DIVIDER}\n{tr('enter_amount_bdt', lang, symbol=net_info['symbol'])}\n\n💵 Rate: 1 {net_info['symbol']} = {get_rate(network)} BDT\n✍️ {tr('numbers_only', lang)}"))
    return WAITING_AMOUNT


async def waiting_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = user_lang(update.effective_user.id)
    try:
        amount_bdt = float(update.message.text.strip())
        if amount_bdt <= 0:
            raise ValueError
    except Exception:
        await update.message.reply_text(f"{tr('invalid_amount', lang)}\n{tr('numbers_only', lang)}")
        return WAITING_AMOUNT

    network = context.user_data.get("network", "solana")
    net_info = NETWORKS[network]
    rate = get_rate(network)
    crypto_amount = round(amount_bdt / rate, 6)
    sufficient, current_bal = check_sufficient(network, crypto_amount)
    if not sufficient and current_bal is not None:
        await update.message.reply_text(f"😔 দুঃখিত! এই মুহূর্তে অর্ডার পূরণ সম্ভব নয়।\n\n🌐 {net_info['name']}\n💵 আপনি চাইছেন: {crypto_amount} {net_info['symbol']}\n{stock_detail(network, crypto_amount, current_bal)}\n\nঅনুগ্রহ করে কম পরিমাণে অর্ডার করুন।\n❓ @MdMouno")
        return ConversationHandler.END
    context.user_data["amount_bdt"] = amount_bdt
    context.user_data["usdc_amount"] = crypto_amount
    keyboard = [[InlineKeyboardButton(tr("confirm", lang), callback_data="confirm_buy"), InlineKeyboardButton(tr("cancel", lang), callback_data="cancel")]]
    await update.message.reply_text(
        panel(
            tr('order_summary', lang),
            f"🌐 Network: {net_info['name']}\n"
            f"💰 {tr('send_bdt', lang)}: {amount_bdt} BDT\n"
            f"💵 {tr('receive_crypto', lang)}: {crypto_amount} {net_info['symbol']}\n"
            f"📈 Rate: 1 {net_info['symbol']} = {rate} BDT\n"
            f"👛 Wallet: `{short_wallet(context.user_data['wallet'])}`\n{DIVIDER}\n"
            f"{gas_warning(network, lang)}\n\n{tr('confirm_prompt', lang)}"
        ),
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return ConversationHandler.END


async def waiting_star_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    wallet = update.message.text.strip()
    user_id = str(update.effective_user.id)
    lang = user_lang(user_id)
    network = context.user_data.get("star_network", "solana")
    net_info = NETWORKS[network]
    if not valid_wallet(network, wallet):
        await update.message.reply_text(f"{tr('invalid_wallet', lang)}\n\n{tr('enter_wallet', lang, network=net_info['name'])}.")
        return WAITING_STAR_WALLET
    context.user_data["star_wallet"] = wallet
    await update.message.reply_text(
        tr("stars_enter_amount", lang, symbol=net_info["symbol"], rate=get_star_rate(network))
        + f"\n\n{tr('numbers_only', lang).replace('500', '1.5')}"
    )
    return WAITING_STAR_AMOUNT


async def waiting_star_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = user_lang(user.id)
    try:
        amount_crypto = float(update.message.text.strip())
        if amount_crypto <= 0:
            raise ValueError
    except Exception:
        await update.message.reply_text(f"{tr('invalid_amount', lang)}\nExample: 1.5")
        return WAITING_STAR_AMOUNT

    network = context.user_data.get("star_network", "solana")
    wallet = context.user_data.get("star_wallet")
    net_info = NETWORKS[network]
    star_rate = get_star_rate(network)
    stars_amount = max(1, math.ceil(amount_crypto * star_rate))

    sufficient, current_bal = check_sufficient(network, amount_crypto)
    if not sufficient and current_bal is not None:
        await update.message.reply_text(
            f"❌ Insufficient {net_info['symbol']} stock.\n\nNeed: {amount_crypto}\n{stock_detail(network, amount_crypto, current_bal)}"
            if lang == "en"
            else f"❌ পর্যাপ্ত {net_info['symbol']} নেই।\n\nদরকার: {amount_crypto}\n{stock_detail(network, amount_crypto, current_bal)}"
        )
        return ConversationHandler.END
    order_id = gen_timestamp_id("STAR")
    create_stock_reservation(order_id, user.id, network, amount_crypto, ttl_minutes=30, reason="stars_invoice")
    username = user.username or user.first_name or ""
    save_star_order(order_id, user.id, username, network, wallet, amount_crypto, stars_amount)
    title = tr("stars_invoice_title", lang)
    description = tr("stars_invoice_description", lang, amount=amount_crypto, symbol=net_info["symbol"], network=net_info["name"])
    prices = [LabeledPrice(label=f"{amount_crypto} {net_info['symbol']}", amount=stars_amount)]

    await update.message.reply_invoice(
        title=title,
        description=description,
        payload=order_id,
        provider_token="",
        currency="XTR",
        prices=prices,
    )
    await update.message.reply_text(
        f"{tr('stars_pay_prompt', lang)}\n\n"
        f"🌐 {net_info['name']}\n"
        f"💵 {amount_crypto} {net_info['symbol']}\n"
        f"⭐ {stars_amount} Stars\n"
        f"👤 @{username}\n"
        f"👛 {wallet}\n\n"
        f"{gas_warning(network, lang)}"
    )
    context.user_data.clear()
    return ConversationHandler.END


async def admin_send_wallet_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    lang = user_lang(user_id)
    if not is_admin(user_id):
        return ConversationHandler.END
    wallet = update.message.text.strip()
    network = context.user_data.get("admin_send_network", "solana")
    net_info = NETWORKS[network]
    if not valid_wallet(network, wallet):
        await update.message.reply_text(f"{tr('invalid_wallet', lang)}\n\n{tr('admin_send_wallet', lang)}.")
        return ADMIN_SEND_WALLET
    context.user_data["admin_send_wallet"] = wallet
    await update.message.reply_text(
        f"✅ Destination saved\n\n🌐 {net_info['name']}\n👛 {wallet}\n\n{tr('admin_send_amount', lang, symbol=net_info['symbol'])}\n\nExample: 1.5"
    )
    return ADMIN_SEND_AMOUNT


async def admin_send_amount_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    lang = user_lang(user_id)
    if not is_admin(user_id):
        return ConversationHandler.END
    try:
        amount = float(update.message.text.strip())
        if amount <= 0:
            raise ValueError
    except Exception:
        await update.message.reply_text(f"{tr('invalid_amount', lang)}\nExample: 1.5")
        return ADMIN_SEND_AMOUNT

    network = context.user_data.get("admin_send_network", "solana")
    wallet = context.user_data.get("admin_send_wallet")
    net_info = NETWORKS[network]
    context.user_data["admin_send_amount"] = amount
    sufficient, current_bal = check_sufficient(network, amount)
    stock_line = ""
    if current_bal is not None:
        stock_line = f"\n💰 Available: {current_bal} {net_info['symbol']}"
    if not sufficient and current_bal is not None:
        await update.message.reply_text(
            f"❌ Insufficient {net_info['symbol']} stock.{stock_line}\nNeed: {amount} {net_info['symbol']}"
            if lang == "en"
            else f"❌ পর্যাপ্ত {net_info['symbol']} নেই।{stock_line}\nদরকার: {amount} {net_info['symbol']}"
        )
        return ConversationHandler.END

    keyboard = [[InlineKeyboardButton(tr("confirm", lang), callback_data="admin_send_confirm"), InlineKeyboardButton(tr("cancel", lang), callback_data="admin_send_cancel")]]
    await update.message.reply_text(
        f"🚀 Admin Send Summary\n━━━━━━━━━━━━━━━━━━━━━\n"
        f"🌐 {net_info['name']}\n"
        f"💵 {amount} {net_info['symbol']}\n"
        f"👛 {wallet}{stock_line}\n━━━━━━━━━━━━━━━━━━━━━\n"
        f"{gas_warning(network, lang)}\n\n{tr('admin_send_confirm', lang)}",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return ConversationHandler.END


async def complete_admin_send(query, context, user_id, lang):
    network = context.user_data.get("admin_send_network")
    wallet = context.user_data.get("admin_send_wallet")
    amount = context.user_data.get("admin_send_amount")
    if not all([network, wallet, amount]):
        await query.edit_message_text("❌ Session expired. Start again." if lang == "en" else "❌ সেশন শেষ। আবার শুরু করুন।")
        return
    net_info = NETWORKS[network]
    await query.edit_message_text("⏳ Sending asset..." if lang == "en" else "⏳ Asset পাঠানো হচ্ছে...")
    try:
        sig = await send_crypto(network, wallet, amount)
        explorer = f"{net_info['explorer']}{sig}"
        order_id = save_transaction(f"ADMIN-{sig[:24]}", user_id, 0, amount, wallet, sig, "completed", network, source="admin_send")
        add_audit(user_id, "admin_send_completed", "transaction", f"ADMIN-{sig[:24]}", f"network={network} amount={amount}")
        context.user_data.clear()
        await query.edit_message_text(
            f"{tr('admin_send_done', lang)}\n\n"
            f"{receipt_block(order_id, f'ADMIN-{sig[:24]}', network, amount, wallet, sig)}",
            reply_markup=back_keyboard(lang),
        )
    except Exception as exc:
        failed_id = f"ADMIN-FAILED-{gen_code(8)}"
        save_transaction(failed_id, user_id, 0, amount, wallet, "", "failed", network, source="admin_send")
        add_audit(user_id, "admin_send_failed", "transaction", failed_id, str(exc))
        context.user_data.clear()
        await query.edit_message_text(f"❌ Send failed.\n\n{exc}\n\n💡 {failure_reason_text(exc, network, lang)}", reply_markup=back_keyboard(lang))


async def seller_center_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await show_seller_center(update.message, context, str(user.id), user.username or user.first_name, edit=False)


async def referral_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await show_referral_menu(update.message, context, str(user.id), user_lang(user.id), edit=False)


async def seller_guide_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = user_lang(update.effective_user.id)
    await update.message.reply_text(seller_guide_text(get_seller(str(update.effective_user.id)), lang))


async def seller_apply_name_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()[:80]
    if len(name) < 2:
        await update.message.reply_text("Shop/display name আরেকটু স্পষ্ট লিখুন।")
        return SELLER_APP_NAME
    context.user_data["seller_apply_name"] = name
    await update.message.reply_text("📲 Seller bKash number লিখুন:")
    return SELLER_APP_BKASH


async def seller_apply_bkash_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    number = update.message.text.strip()[:40]
    if len(number) < 8:
        await update.message.reply_text("সঠিক bKash number লিখুন।")
        return SELLER_APP_BKASH
    context.user_data["seller_apply_bkash"] = number
    await update.message.reply_text("📞 Support contact দিন (Telegram username/phone):")
    return SELLER_APP_SUPPORT


async def seller_apply_support_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    support = update.message.text.strip()[:80]
    seller = create_or_update_seller_application(user.id, user.username or user.first_name or "", context.user_data.get("seller_apply_name"), context.user_data.get("seller_apply_bkash"), support)
    context.user_data.clear()
    await update.message.reply_text(f"✅ Seller application জমা হয়েছে।\n\n🏷️ {seller[2]}\n📲 {seller[3]}\n⏳ Admin approval লাগবে।\n\n/seller_guide দেখে forwarder/setup প্রস্তুত রাখুন।")
    try:
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("✅ Approve", callback_data=f"sellerapp_a_{seller[0]}"), InlineKeyboardButton("❌ Reject", callback_data=f"sellerapp_r_{seller[0]}")]])
        await update.get_bot().send_message(ADMIN_ID, f"🏪 New seller application\n\nID: {seller[0]}\n@{seller[1]}\nName: {seller[2]}\nbKash: {seller[3]}\nSupport: {seller[4]}", reply_markup=keyboard)
    except Exception as exc:
        logger.error(exc)
    return ConversationHandler.END


async def seller_wallet_key_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    network = context.user_data.get("seller_wallet_network")
    private_key = update.message.text.strip()
    try:
        await update.message.delete()
    except Exception:
        pass
    if not SELLER_WALLET_MASTER_KEY:
        await update.message.reply_text("❌ SELLER_WALLET_MASTER_KEY missing. Admin .env এ set করুন।")
        return ConversationHandler.END
    if not network:
        await update.message.reply_text("❌ Session expired.")
        return ConversationHandler.END
    try:
        wallet_address = get_wallet_address(network, private_key)
        encrypted_key, salt = encrypt_seller_key(private_key)
        save_seller_wallet(user_id, network, encrypted_key, salt, wallet_address)
    except Exception as exc:
        await update.message.reply_text(f"❌ Wallet key setup failed.\n{exc}\n\nআবার private key পাঠান:")
        return SELLER_SETUP_KEY
    context.user_data["seller_rate_network"] = network
    context.user_data.pop("seller_wallet_network", None)
    ni = NETWORKS[network]
    await update.message.reply_text(f"✅ Delivery wallet saved.\n\n🌐 {ni['name']}\n👛 {wallet_address}\n\nএখন seller rate লিখুন BDT per 1 {ni['symbol']}. 0 লিখলে global rate use হবে।")
    return SELLER_SET_RATE


async def seller_rate_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    network = context.user_data.get("seller_rate_network")
    if not network:
        await update.message.reply_text("❌ Session expired.")
        return ConversationHandler.END
    try:
        rate = float(update.message.text.strip())
        if rate < 0:
            raise ValueError
    except Exception:
        await update.message.reply_text("শুধু সংখ্যা লিখুন। 0 দিলে global rate।")
        return SELLER_SET_RATE
    set_seller_rate(user_id, network, None if rate == 0 else rate)
    context.user_data.clear()
    await update.message.reply_text(f"✅ Seller rate updated.\n🌐 {NETWORKS[network]['name']}\n💵 {'global/admin rate' if rate == 0 else str(rate) + ' BDT'}")
    return ConversationHandler.END


async def seller_buy_wallet_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    wallet = update.message.text.strip()
    lang = user_lang(update.effective_user.id)
    network = context.user_data.get("seller_buy_network")
    seller_id = context.user_data.get("seller_buy_seller_id")
    if not network or not seller_id:
        await update.message.reply_text("❌ Session expired.")
        return ConversationHandler.END
    if not valid_wallet(network, wallet):
        await update.message.reply_text(ltext(lang, f"❌ Invalid wallet.\nExample: {wallet_hint(network)}", f"❌ ভুল wallet.\nExample: {wallet_hint(network)}"))
        return SELLER_BUY_WALLET
    context.user_data["seller_buy_wallet"] = wallet
    ni = NETWORKS[network]
    rate = seller_rate_or_global(seller_id, network)
    await update.message.reply_text(ltext(lang, f"How much {ni['symbol']} do you want to buy in BDT?\n\nRate: 1 {ni['symbol']} = {rate} BDT", f"কত BDT-এর {ni['symbol']} কিনবেন?\n\nRate: 1 {ni['symbol']} = {rate} BDT"))
    return SELLER_BUY_AMOUNT


async def seller_buy_amount_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = user_lang(user.id)
    seller_id = context.user_data.get("seller_buy_seller_id")
    method = context.user_data.get("seller_buy_method")
    network = context.user_data.get("seller_buy_network")
    wallet = context.user_data.get("seller_buy_wallet")
    if not all([seller_id, method, network, wallet]):
        await update.message.reply_text("❌ Session expired.")
        return ConversationHandler.END
    try:
        amount_bdt = float(update.message.text.strip())
        if amount_bdt <= 0:
            raise ValueError
    except Exception:
        await update.message.reply_text(ltext(lang, "Enter numbers only.", "শুধু সংখ্যা লিখুন।"))
        return SELLER_BUY_AMOUNT
    seller = get_seller(seller_id)
    if not seller or seller[5] != "approved":
        await update.message.reply_text("❌ Seller unavailable.")
        return ConversationHandler.END
    rate = seller_rate_or_global(seller_id, network)
    amount_crypto = round(amount_bdt / rate, 6)
    ni = NETWORKS[network]
    order_id = gen_timestamp_id("SO")
    username = user.username or user.first_name or ""
    if method == "stars":
        stars_amount = max(1, math.ceil(amount_crypto * get_star_rate(network)))
        create_seller_order(order_id, seller_id, user.id, username, "stars", network, wallet, amount_bdt, amount_crypto, stars_amount, status="waiting_payment")
        await update.message.reply_invoice(
            title="Seller Crypto Order",
            description=f"{seller_public_name(seller)}: {amount_crypto} {ni['symbol']} on {ni['name']}",
            payload=order_id,
            provider_token="",
            currency="XTR",
            prices=[LabeledPrice(label=f"{amount_crypto} {ni['symbol']}", amount=stars_amount)],
        )
        await update.message.reply_text(ltext(lang, f"⭐ Invoice sent.\n\n🧾 {order_id}\n🏪 {seller_public_name(seller)}\n💵 {amount_crypto} {ni['symbol']}\n⭐ {stars_amount} Stars\n\nSeller Stars earnings will be recorded for manual payout.", f"⭐ Invoice sent.\n\n🧾 {order_id}\n🏪 {seller_public_name(seller)}\n💵 {amount_crypto} {ni['symbol']}\n⭐ {stars_amount} Stars\n\nSeller Stars earnings ledger/manual payout হবে।"))
        context.user_data.clear()
        return ConversationHandler.END
    create_seller_order(order_id, seller_id, user.id, username, "bkash", network, wallet, amount_bdt, amount_crypto, None, status="waiting_payment")
    context.user_data.clear()
    context.user_data.update({"waiting_seller_trxid": True, "seller_order_id": order_id, "trx_deadline": asyncio.get_event_loop().time() + 900})
    await update.message.reply_text(ltext(lang, f"🎯 Seller order created.\n\n🧾 Order: {order_id}\n🏪 {seller_public_name(seller)}\n📲 bKash: {seller[3]}\n💰 Send exactly: {amount_bdt} BDT\n💵 Receive: {amount_crypto} {ni['symbol']}\n👛 {wallet}\n\nAfter payment, send the TrxID.", f"🎯 Seller order created.\n\n🧾 Order: {order_id}\n🏪 {seller_public_name(seller)}\n📲 bKash: {seller[3]}\n💰 Send exactly: {amount_bdt} BDT\n💵 Receive: {amount_crypto} {ni['symbol']}\n👛 {wallet}\n\nPayment করার পর TrxID লিখুন।"))
    try:
        await update.get_bot().send_message(int(seller_id), f"🛎️ New seller bKash order waiting TrxID.\n\n{seller_order_summary(get_seller_order(order_id))}")
    except Exception:
        pass
    return ConversationHandler.END


async def waiting_rate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return ConversationHandler.END
    try:
        new_rate = float(update.message.text.strip())
        if new_rate <= 0:
            raise ValueError
    except Exception:
        await update.message.reply_text("❌ ভুল রেট! সংখ্যা লিখুন।")
        return WAITING_RATE
    network = context.user_data.get("rate_network", "solana")
    set_network_rate(network, new_rate)
    add_audit(update.effective_user.id, "rate_changed", "network", network, f"rate={new_rate}")
    net_info = NETWORKS[network]
    await update.message.reply_text(f"✅ রেট আপডেট!\n\n🌐 {net_info['name']}\n💵 1 {net_info['symbol']} = {new_rate} BDT")
    return ConversationHandler.END


async def handle_referral_withdraw_text(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id, lang, incoming_text):
    if not referral_enabled():
        context.user_data.clear()
        await update.message.reply_text(ltext(lang, "⚠️ Referral withdrawals are currently disabled.", "⚠️ Referral withdrawal বর্তমানে বন্ধ।"), reply_markup=main_menu(user_id, lang))
        return
    step = context.user_data.get("ref_withdraw_step")
    network = context.user_data.get("ref_withdraw_network")
    if network not in STABLE_REFERRAL_NETWORKS:
        context.user_data.clear()
        await update.message.reply_text("❌ Withdrawal session expired.", reply_markup=main_menu(user_id, lang))
        return
    balance = referral_balance(user_id)
    min_withdraw = referral_min_withdraw_value()
    ni = NETWORKS[network]
    if step == "amount":
        try:
            amount = round(float(incoming_text), 6)
            if amount <= 0 or amount + 1e-9 < min_withdraw or amount - balance > 1e-9:
                raise ValueError
        except Exception:
            await update.message.reply_text(ltext(lang, f"❌ Invalid amount. Send an amount between {min_withdraw} and {round(balance, 6)}.", f"❌ ভুল amount। {min_withdraw} থেকে {round(balance, 6)} এর মধ্যে লিখুন।"))
            return
        context.user_data["ref_withdraw_amount"] = amount
        context.user_data["ref_withdraw_step"] = "wallet"
        await update.message.reply_text(ltext(lang, f"Send your {ni['name']} destination wallet:\nExample: {wallet_hint(network)}", f"আপনার {ni['name']} destination wallet দিন:\nExample: {wallet_hint(network)}"))
        return
    wallet = incoming_text.strip()
    amount = float(context.user_data.get("ref_withdraw_amount") or 0)
    if amount <= 0:
        context.user_data.clear()
        await update.message.reply_text("❌ Withdrawal session expired.", reply_markup=main_menu(user_id, lang))
        return
    if not valid_wallet(network, wallet):
        await update.message.reply_text(ltext(lang, f"❌ Invalid wallet. Example: {wallet_hint(network)}", f"❌ ভুল wallet। Example: {wallet_hint(network)}"))
        return
    balance = referral_balance(user_id)
    if amount - balance > 1e-9:
        context.user_data.clear()
        await update.message.reply_text(ltext(lang, f"❌ Balance changed. Current balance: {round(balance, 6)} USD", f"❌ Balance পরিবর্তন হয়েছে। Current balance: {round(balance, 6)} USD"), reply_markup=main_menu(user_id, lang))
        return
    sufficient, current_bal = check_sufficient(network, amount)
    if not sufficient and current_bal is not None:
        context.user_data.clear()
        await update.message.reply_text(ltext(lang, f"❌ Bot stock is insufficient right now.\n{stock_detail(network, amount, current_bal)}", f"❌ Bot stock এখন পর্যাপ্ত নয়।\n{stock_detail(network, amount, current_bal)}"), reply_markup=main_menu(user_id, lang))
        return
    withdrawal_id = create_referral_withdrawal(user_id, amount, network, wallet)
    reserved = reserve_referral_withdrawal(user_id, withdrawal_id, amount, network, wallet)
    if not reserved:
        mark_referral_withdrawal(withdrawal_id, "failed", error="insufficient unreserved referral balance")
        context.user_data.clear()
        await update.message.reply_text(ltext(lang, "❌ Balance is already reserved or insufficient. Please refresh and try again.", "❌ Balance ইতিমধ্যে reserved অথবা পর্যাপ্ত নয়। Refresh করে আবার চেষ্টা করুন।"), reply_markup=main_menu(user_id, lang))
        return
    await update.message.reply_text(ltext(lang, f"⏳ Sending {amount} {ni['symbol']} referral withdrawal...", f"⏳ {amount} {ni['symbol']} referral withdrawal পাঠানো হচ্ছে..."))
    try:
        sig = await send_crypto(network, wallet, amount)
        complete_referral_withdrawal(withdrawal_id, sig)
        trx_id = f"REFWD-{withdrawal_id}"
        order_id = save_transaction(trx_id, user_id, 0, amount, wallet, sig, "completed", network, order_id=withdrawal_id, source="referral_withdrawal")
        add_audit("system", "referral_withdrawal_completed", "referral_withdrawal", withdrawal_id, f"user={user_id} amount={amount} network={network}")
        context.user_data.clear()
        receipt = receipt_block(order_id, trx_id, network, amount, wallet, sig)
        await update.message.reply_text(ltext(lang, f"✅ Referral withdrawal complete!\n\n{receipt}", f"✅ Referral withdrawal সম্পন্ন!\n\n{receipt}"), reply_markup=main_menu(user_id, lang))
        try:
            await update.get_bot().send_message(ADMIN_ID, f"✅ Referral withdrawal complete.\nUser: {user_id}\nAmount: {amount} {ni['symbol']}\nNetwork: {ni['name']}\nTX: {sig}")
        except Exception:
            pass
    except Exception as exc:
        fail_referral_withdrawal(withdrawal_id, str(exc)[:500])
        add_audit("system", "referral_withdrawal_failed", "referral_withdrawal", withdrawal_id, str(exc))
        context.user_data.clear()
        reason = failure_reason_text(exc, network, lang)
        await update.message.reply_text(ltext(lang, f"❌ Referral withdrawal failed. Your referral balance was not debited.\n\n💡 {reason}", f"❌ Referral withdrawal failed. আপনার referral balance কাটা হয়নি।\n\n💡 {reason}"), reply_markup=main_menu(user_id, lang))
        try:
            await update.get_bot().send_message(ADMIN_ID, f"🚨 Referral withdrawal failed.\nUser: {user_id}\nWithdrawal: {withdrawal_id}\nAmount: {amount}\nNetwork: {network}\nError: {exc}")
        except Exception:
            pass


async def handle_solana_refund_text(update, context, user_id, lang, incoming_text):
    step = context.user_data.get("solana_refund_step")
    if not step:
        return False
    if incoming_text.lower() in {"/cancel", "cancel", "close", "stop", "বন্ধ", "বাতিল"}:
        for key in ["solana_refund_step", "solana_refund_private_key", "solana_refund_wallet", "solana_refund_summary"]:
            context.user_data.pop(key, None)
        await update.message.reply_text(ltext(lang, "✅ Solana refund flow cancelled.", "✅ Solana refund flow বাতিল হয়েছে।"), reply_markup=solana_refund_keyboard(lang))
        return True
    if step != "private_key":
        return False
    private_key = incoming_text.strip()
    try:
        await update.message.delete()
    except Exception:
        pass
    try:
        wallet = get_wallet_address("solana", private_key)
    except Exception as exc:
        await update.message.reply_text(ltext(lang, f"❌ Invalid Solana private key: {friendly_solana_error(exc, lang)}\n\nSend the correct private key, or /cancel.", f"❌ Solana private key invalid: {friendly_solana_error(exc, lang)}\n\nসঠিক private key পাঠান, অথবা /cancel লিখুন।"), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(tr("cancel", lang), callback_data="sr_disconnect")]]))
        return True
    context.user_data["solana_refund_private_key"] = private_key
    context.user_data["solana_refund_wallet"] = wallet
    context.user_data.pop("solana_refund_step", None)
    await update.message.reply_text(ltext(lang, "✅ Solana wallet connected. Checking ATA accounts...", "✅ Solana wallet connected। ATA account check হচ্ছে..."))
    try:
        loop = asyncio.get_running_loop()
        summary = await loop.run_in_executor(None, lambda: find_refundable_atas(private_key))
        context.user_data["solana_refund_summary"] = summary
        await update.message.reply_text(
            solana_refund_text(lang, wallet, summary),
            parse_mode="Markdown",
            reply_markup=solana_refund_keyboard(lang, True, bool(summary.get("refundable_count"))),
        )
    except Exception as exc:
        await update.message.reply_text(ltext(lang, f"❌ ATA check failed: {friendly_solana_error(exc, lang)}", f"❌ ATA check ব্যর্থ: {friendly_solana_error(exc, lang)}"), reply_markup=solana_refund_keyboard(lang, True, False))
    return True


async def handle_telegram_id_finder_message(update, context, user_id, lang, incoming_text):
    if not context.user_data.get("telegram_id_finder"):
        return False
    message = update.message
    if incoming_text.lower() in {"/cancel", "cancel", "close", "stop", "বন্ধ", "বাতিল"}:
        context.user_data.pop("telegram_id_finder", None)
        await message.reply_text(ltext(lang, "✅ Telegram ID Finder closed.", "✅ Telegram ID Finder বন্ধ হয়েছে।"), reply_markup=telegram_id_finder_keyboard(lang))
        return True

    entries, note = forwarded_origin_entries(message, lang)
    if entries:
        await message.reply_text(telegram_id_result_text(lang, entries), reply_markup=telegram_id_finder_keyboard(lang))
        return True
    if note:
        await message.reply_text(note, reply_markup=telegram_id_finder_keyboard(lang))
        return True

    target = normalize_telegram_lookup_target(incoming_text)
    if target is not None:
        try:
            chat = await context.bot.get_chat(target)
            entries = [
                {
                    "label": ltext(lang, "Resolved from username/link/ID", "Username/link/ID থেকে পাওয়া"),
                    "id": chat.id,
                    "type": telegram_chat_type_label(getattr(chat, "type", None), lang),
                    "title": getattr(chat, "title", None) or getattr(chat, "full_name", None) or getattr(chat, "first_name", None),
                    "username": getattr(chat, "username", None),
                }
            ]
            await message.reply_text(telegram_id_result_text(lang, entries), reply_markup=telegram_id_finder_keyboard(lang))
            return True
        except Exception as exc:
            await message.reply_text(
                ltext(
                    lang,
                    f"❌ Could not resolve that username/link/ID: {safe_free_forward_error(exc)}\n\nTry forwarding a message from the target, or add the bot where it can access the chat.",
                    f"❌ ওই username/link/ID resolve করা যায়নি: {safe_free_forward_error(exc)}\n\nTarget থেকে message forward করুন, অথবা bot-কে এমন জায়গায় add করুন যেখানে chat access করতে পারে।",
                ),
                reply_markup=telegram_id_finder_keyboard(lang),
            )
            return True

    chat = update.effective_chat
    if chat:
        entries = [
            {
                "label": ltext(lang, "Current chat", "Current chat"),
                "id": chat.id,
                "type": telegram_chat_type_label(getattr(chat, "type", None), lang),
                "title": getattr(chat, "title", None) or getattr(chat, "full_name", None) or getattr(chat, "first_name", None),
                "username": getattr(chat, "username", None),
            }
        ]
        await message.reply_text(
            telegram_id_result_text(
                lang,
                entries,
                ltext(lang, "Tip: send a public @username/link or forward a message to find another chat's ID.", "Tip: অন্য chat-এর ID পেতে public @username/link পাঠান অথবা message forward করুন।"),
            ),
            reply_markup=telegram_id_finder_keyboard(lang),
        )
        return True

    await message.reply_text(ltext(lang, "Send a public @username/link, numeric ID, or forwarded message.", "Public @username/link, numeric ID অথবা forwarded message পাঠান।"), reply_markup=telegram_id_finder_keyboard(lang))
    return True


async def handle_free_forward_text(update, context, user_id, lang, incoming_text):
    step = context.user_data.get("free_forward_step")
    if not step:
        return False
    if incoming_text.lower() in {"/cancel", "cancel", "close", "stop", "বন্ধ", "বাতিল"}:
        await personal_forward_disconnect_pending(user_id)
        free_forward_clear_flow(context)
        await update.message.reply_text(
            ltext(lang, "✅ Free forwarding flow cancelled.", "✅ Free forwarding flow বাতিল হয়েছে।"),
            reply_markup=free_forward_keyboard(lang, free_forward_connected(user_id), free_forward_task_running(user_id), personal_forward_connected(user_id)),
        )
        return True

    if step == "personal_api_id":
        try:
            api_id = int(incoming_text.strip())
            if api_id <= 0:
                raise ValueError
        except Exception:
            await update.message.reply_text(ltext(lang, "❌ Send a numeric Telegram API ID.", "❌ Numeric Telegram API ID পাঠান।"), reply_markup=free_forward_cancel_keyboard(lang))
            return True
        context.user_data["personal_forward_api_id"] = str(api_id)
        context.user_data["free_forward_step"] = "personal_api_hash"
        try:
            await update.message.delete()
        except Exception:
            pass
        await update.message.reply_text(ltext(lang, "✅ API ID saved. Now send your Telegram API hash.", "✅ API ID save হয়েছে। এখন Telegram API hash পাঠান।"), reply_markup=free_forward_cancel_keyboard(lang))
        return True

    if step == "personal_api_hash":
        api_hash = incoming_text.strip()
        if not re.fullmatch(r"[A-Fa-f0-9]{32}", api_hash):
            await update.message.reply_text(ltext(lang, "❌ API hash looks invalid. Send the 32-character API hash from my.telegram.org.", "❌ API hash invalid মনে হচ্ছে। my.telegram.org থেকে পাওয়া 32-character API hash পাঠান।"), reply_markup=free_forward_cancel_keyboard(lang))
            return True
        context.user_data["personal_forward_api_hash"] = api_hash
        context.user_data["free_forward_step"] = "personal_phone"
        try:
            await update.message.delete()
        except Exception:
            pass
        await update.message.reply_text(ltext(lang, "✅ API hash saved. Now send your Telegram phone number with country code, e.g. +8801XXXXXXXXX.", "✅ API hash save হয়েছে। এখন country code সহ Telegram phone number পাঠান, যেমন +8801XXXXXXXXX।"), reply_markup=free_forward_cancel_keyboard(lang))
        return True

    if step == "personal_phone":
        if not personal_forward_available():
            free_forward_clear_flow(context)
            await update.message.reply_text(ltext(lang, "❌ Telethon is not installed on this server.", "❌ এই server-এ Telethon install নেই।"), reply_markup=free_forward_keyboard(lang, free_forward_connected(user_id), free_forward_task_running(user_id), personal_forward_connected(user_id)))
            return True
        phone = incoming_text.strip().replace(" ", "")
        if not re.fullmatch(r"\+?\d{8,16}", phone):
            await update.message.reply_text(ltext(lang, "❌ Send a valid phone number with country code.", "❌ Country code সহ valid phone number পাঠান।"), reply_markup=free_forward_cancel_keyboard(lang))
            return True
        api_id = int(context.user_data.get("personal_forward_api_id") or 0)
        api_hash = context.user_data.get("personal_forward_api_hash") or ""
        try:
            await personal_forward_disconnect_pending(user_id)
            client = TelegramClient(StringSession(), api_id, api_hash)
            await client.connect()
            sent_code = await client.send_code_request(phone)
            PERSONAL_FORWARD_PENDING[str(user_id)] = {"client": client, "phone": phone, "phone_code_hash": getattr(sent_code, "phone_code_hash", None)}
        except Exception as exc:
            await personal_forward_disconnect_pending(user_id)
            await update.message.reply_text(ltext(lang, f"❌ Could not send login code: {safe_free_forward_error(exc)}", f"❌ Login code পাঠানো যায়নি: {safe_free_forward_error(exc)}"), reply_markup=free_forward_cancel_keyboard(lang))
            return True
        context.user_data["personal_forward_phone"] = phone
        context.user_data["free_forward_step"] = "personal_code"
        try:
            await update.message.delete()
        except Exception:
            pass
        await update.message.reply_text(ltext(lang, "✅ Telegram sent a login code. Send the code here. If Telegram shows it as 1 2 3 4 5, send 12345.", "✅ Telegram login code পাঠিয়েছে। Code এখানে পাঠান। Telegram যদি 1 2 3 4 5 দেখায়, 12345 পাঠান।"), reply_markup=free_forward_cancel_keyboard(lang))
        return True

    if step == "personal_code":
        pending = PERSONAL_FORWARD_PENDING.get(str(user_id))
        if not pending:
            free_forward_clear_flow(context)
            await update.message.reply_text(ltext(lang, "❌ Login session expired. Start again from Free Service.", "❌ Login session expire হয়েছে। Free Service থেকে আবার শুরু করুন।"), reply_markup=free_forward_keyboard(lang, free_forward_connected(user_id), free_forward_task_running(user_id), personal_forward_connected(user_id)))
            return True
        code = re.sub(r"\D", "", incoming_text)
        try:
            await update.message.delete()
        except Exception:
            pass
        try:
            await pending["client"].sign_in(pending["phone"], code=code, phone_code_hash=pending.get("phone_code_hash"))
        except Exception as exc:
            if SessionPasswordNeededError and isinstance(exc, SessionPasswordNeededError):
                context.user_data["free_forward_step"] = "personal_password"
                await update.message.reply_text(ltext(lang, "🔐 Two-step verification is enabled. Send your Telegram 2FA password.", "🔐 Two-step verification enabled। আপনার Telegram 2FA password পাঠান।"), reply_markup=free_forward_cancel_keyboard(lang))
                return True
            await update.message.reply_text(ltext(lang, f"❌ Login code failed: {safe_free_forward_error(exc)}", f"❌ Login code failed: {safe_free_forward_error(exc)}"), reply_markup=free_forward_cancel_keyboard(lang))
            return True
        api_id = context.user_data.get("personal_forward_api_id")
        api_hash = context.user_data.get("personal_forward_api_hash")
        me = await personal_forward_store_connection(user_id, pending["client"], api_id, api_hash)
        await personal_forward_disconnect_pending(user_id)
        free_forward_clear_flow(context)
        await update.message.reply_text(
            ltext(lang, f"✅ Personal account connected: {personal_forward_display_name(me)}\n\nNow choose forwarding type.", f"✅ Personal account connected: {personal_forward_display_name(me)}\n\nএখন forward type বেছে নিন।"),
            reply_markup=free_forward_mode_keyboard(lang, "pf"),
        )
        return True

    if step == "personal_password":
        pending = PERSONAL_FORWARD_PENDING.get(str(user_id))
        if not pending:
            free_forward_clear_flow(context)
            await update.message.reply_text(ltext(lang, "❌ Login session expired. Start again from Free Service.", "❌ Login session expire হয়েছে। Free Service থেকে আবার শুরু করুন।"), reply_markup=free_forward_keyboard(lang, free_forward_connected(user_id), free_forward_task_running(user_id), personal_forward_connected(user_id)))
            return True
        try:
            await update.message.delete()
        except Exception:
            pass
        try:
            await pending["client"].sign_in(password=incoming_text.strip())
        except Exception as exc:
            await update.message.reply_text(ltext(lang, f"❌ 2FA password failed: {safe_free_forward_error(exc)}", f"❌ 2FA password failed: {safe_free_forward_error(exc)}"), reply_markup=free_forward_cancel_keyboard(lang))
            return True
        api_id = context.user_data.get("personal_forward_api_id")
        api_hash = context.user_data.get("personal_forward_api_hash")
        me = await personal_forward_store_connection(user_id, pending["client"], api_id, api_hash)
        await personal_forward_disconnect_pending(user_id)
        free_forward_clear_flow(context)
        await update.message.reply_text(
            ltext(lang, f"✅ Personal account connected: {personal_forward_display_name(me)}\n\nNow choose forwarding type.", f"✅ Personal account connected: {personal_forward_display_name(me)}\n\nএখন forward type বেছে নিন।"),
            reply_markup=free_forward_mode_keyboard(lang, "pf"),
        )
        return True

    if step == "token":
        token = incoming_text.strip()
        try:
            me = await validate_free_forward_token(token)
        except Exception:
            await update.message.reply_text(ltext(lang, "❌ Token check failed. Send a valid @BotFather bot token, or send /cancel.", "❌ Token check ব্যর্থ। সঠিক @BotFather bot token পাঠান, অথবা /cancel লিখুন।"), reply_markup=free_forward_cancel_keyboard(lang))
            return True
        try:
            await update.message.delete()
        except Exception:
            pass
        FREE_FORWARD_CONNECTIONS[str(user_id)] = {
            "token": token,
            "bot_username": getattr(me, "username", None),
            "bot_id": str(getattr(me, "id", "")),
        }
        free_forward_clear_flow(context)
        await update.message.reply_text(
            ltext(lang, f"✅ Token connected: @{getattr(me, 'username', 'bot')}\n\nNow choose forwarding type.", f"✅ Token connected: @{getattr(me, 'username', 'bot')}\n\nএখন forward type বেছে নিন।"),
            reply_markup=free_forward_mode_keyboard(lang),
        )
        return True

    if step == "targets":
        sender = context.user_data.get("free_forward_sender") or "bot"
        max_targets = PERSONAL_FORWARD_MAX_TARGETS if sender == "personal" else FREE_FORWARD_MAX_TARGETS
        targets, invalid = parse_free_forward_targets(incoming_text, max_targets)
        if not targets:
            await update.message.reply_text(ltext(lang, "❌ No valid target found. Send numeric chat IDs, @usernames, or public t.me links.", "❌ কোনো valid target পাওয়া যায়নি। Numeric chat ID, @username অথবা public t.me link পাঠান।"), reply_markup=free_forward_cancel_keyboard(lang))
            return True
        context.user_data["free_forward_targets"] = targets
        ignored = ""
        if invalid:
            ignored = ltext(lang, f"\n\nIgnored invalid/private targets: {', '.join(invalid[:5])}", f"\n\nInvalid/private target বাদ দেওয়া হয়েছে: {', '.join(invalid[:5])}")
        if context.user_data.get("free_forward_mode") == "schedule":
            context.user_data["free_forward_step"] = "interval"
            min_interval = PERSONAL_FORWARD_MIN_INTERVAL_MINUTES if sender == "personal" else FREE_FORWARD_MIN_INTERVAL_MINUTES
            await update.message.reply_text(
                ltext(lang, f"✅ Targets saved: {len(targets)}{ignored}\n\nSend interval in minutes. Minimum {min_interval} minute(s).", f"✅ Target save হয়েছে: {len(targets)}{ignored}\n\nকত মিনিট পরপর পাঠাবেন লিখুন। Minimum {min_interval} মিনিট।"),
                reply_markup=free_forward_cancel_keyboard(lang),
            )
        else:
            context.user_data["free_forward_step"] = "message"
            await update.message.reply_text(
                ltext(lang, f"✅ Targets saved: {len(targets)}{ignored}\n\nNow send the message to forward. Text, photo, video, document, audio, voice, animation, or sticker is supported.", f"✅ Target save হয়েছে: {len(targets)}{ignored}\n\nএখন যে message forward/send করতে চান সেটি পাঠান। Text, photo, video, document, audio, voice, animation বা sticker supported।"),
                reply_markup=free_forward_cancel_keyboard(lang),
            )
        return True

    if step == "interval":
        sender = context.user_data.get("free_forward_sender") or "bot"
        min_interval = PERSONAL_FORWARD_MIN_INTERVAL_MINUTES if sender == "personal" else FREE_FORWARD_MIN_INTERVAL_MINUTES
        try:
            interval_minutes = float(incoming_text.strip())
            if interval_minutes < min_interval:
                raise ValueError
        except Exception:
            await update.message.reply_text(ltext(lang, f"❌ Send a number of minutes. Minimum {min_interval}.", f"❌ মিনিট সংখ্যা লিখুন। Minimum {min_interval}।"), reply_markup=free_forward_cancel_keyboard(lang))
            return True
        context.user_data["free_forward_interval_minutes"] = interval_minutes
        context.user_data["free_forward_step"] = "message"
        await update.message.reply_text(
            ltext(lang, "✅ Interval saved. Now send the message to repeat.", "✅ Interval save হয়েছে। এখন যে message বারবার পাঠাবেন সেটি পাঠান।"),
            reply_markup=free_forward_cancel_keyboard(lang),
        )
        return True

    if step == "message":
        spec = await free_forward_message_spec(update, context)
        if not spec or (spec.get("type") == "text" and not spec.get("text")):
            await update.message.reply_text(ltext(lang, "❌ Unsupported or empty message. Send text, photo, video, document, audio, voice, animation, or sticker.", "❌ Unsupported/খালি message। Text, photo, video, document, audio, voice, animation বা sticker পাঠান।"), reply_markup=free_forward_cancel_keyboard(lang))
            return True
        token = free_forward_connection(user_id).get("token")
        personal_connection = personal_forward_connection(user_id)
        sender = context.user_data.get("free_forward_sender") or "bot"
        targets = context.user_data.get("free_forward_targets") or []
        if (sender == "bot" and not token) or (sender == "personal" and not personal_connection.get("session")) or not targets:
            free_forward_clear_flow(context)
            await update.message.reply_text(ltext(lang, "❌ Session expired. Start again from Free Service.", "❌ Session expire হয়েছে। Free Service থেকে আবার শুরু করুন।"), reply_markup=free_forward_keyboard(lang, bool(token), free_forward_task_running(user_id), bool(personal_connection.get("session"))))
            return True
        if context.user_data.get("free_forward_mode") == "schedule":
            interval_minutes = context.user_data.get("free_forward_interval_minutes") or (PERSONAL_FORWARD_MIN_INTERVAL_MINUTES if sender == "personal" else FREE_FORWARD_MIN_INTERVAL_MINUTES)
            free_forward_cancel_schedule(user_id)
            schedule_coro = personal_forward_schedule_loop(context.application, user_id, update.effective_chat.id, lang, dict(personal_connection), list(targets), dict(spec), interval_minutes) if sender == "personal" else free_forward_schedule_loop(context.application, user_id, update.effective_chat.id, lang, token, list(targets), dict(spec), interval_minutes)
            task = context.application.create_task(
                schedule_coro
            )
            FREE_FORWARD_TASKS[str(user_id)] = task
            free_forward_clear_flow(context)
            await update.message.reply_text(
                ltext(lang, f"⏰ Scheduled forward saved. It will send now and then every {interval_minutes} minute(s).", f"⏰ নির্দিষ্ট সময়ের forward save হয়েছে। এখন পাঠাবে, এরপর প্রতি {interval_minutes} মিনিট পরপর পাঠাবে।"),
                reply_markup=free_forward_keyboard(lang, bool(token), True, bool(personal_connection.get("session"))),
            )
            return True
        try:
            if sender == "personal":
                ok, failed = await personal_forward_send_to_targets(personal_connection, targets, spec)
            else:
                ok, failed = await free_forward_send_to_targets(token, targets, spec)
        except Exception as exc:
            free_forward_clear_flow(context)
            error = safe_free_forward_error(exc)
            await update.message.reply_text(ltext(lang, f"❌ Forward failed before sending: {error}", f"❌ Forward পাঠানোর আগেই ব্যর্থ: {error}"), reply_markup=free_forward_keyboard(lang, bool(token), free_forward_task_running(user_id), bool(personal_connection.get("session"))))
            return True
        free_forward_clear_flow(context)
        await update.message.reply_text(free_forward_result_text(lang, ok, failed), reply_markup=free_forward_keyboard(lang, bool(token), free_forward_task_running(user_id), bool(personal_connection.get("session"))))
        return True

    return False


async def handle_swap_text(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id, lang, incoming_text):
    setup_provider = context.user_data.get("swap_setup_provider")
    if setup_provider:
        if not is_admin(user_id):
            context.user_data.pop("swap_setup_provider", None)
            return True
        text = incoming_text.strip()
        if text.lower() in {"/cancel", "cancel", "close", "stop", "বন্ধ", "বাতিল"}:
            context.user_data.pop("swap_setup_provider", None)
            await update.message.reply_text("✅ Swap API Setup cancelled." if lang == "en" else "✅ Swap API Setup বাতিল হয়েছে।", reply_markup=swap_setup_keyboard(lang))
            return True
        if setup_provider not in SWAP_PROVIDER_SETTING_KEYS:
            context.user_data.pop("swap_setup_provider", None)
            await update.message.reply_text("❌ Invalid swap provider.", reply_markup=swap_setup_keyboard(lang))
            return True
        api_key = _clean_swap_key(text)
        if not api_key or len(api_key) < 8:
            await update.message.reply_text(ltext(lang, "❌ API key is too short or empty. Send the correct key, or send /cancel.", "❌ API key খুব ছোট/খালি। সঠিক key পাঠান, অথবা /cancel লিখুন।"), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel" if lang == "en" else "❌ বাতিল", callback_data="swap_setup_cancel")]]))
            return True
        try:
            await update.message.delete()
        except Exception:
            pass
        set_setting(SWAP_PROVIDER_SETTING_KEYS[setup_provider], api_key)
        context.user_data.pop("swap_setup_provider", None)
        add_audit(user_id, "swap_api_key_updated", "swap_provider", setup_provider, "configured via bot setup")
        await update.message.reply_text(f"✅ {SWAP_PROVIDER_LABELS[setup_provider]} API key saved. {'No restart required.' if lang == 'en' else 'Restart লাগবে না।'}\n\n{swap_setup_text(lang)}", reply_markup=swap_setup_keyboard(lang))
        return True

    step = context.user_data.get("swap_step")
    if not step:
        return False
    text = incoming_text.strip()
    if text.lower() in {"/cancel", "cancel", "close", "stop", "বন্ধ", "বাতিল"}:
        context.user_data.clear()
        await update.message.reply_text(ltext(lang, "✅ Swap flow cancelled.", "✅ Swap flow বাতিল হয়েছে।"), reply_markup=main_menu(user_id, lang))
        return True

    if step in {"from_chain_search", "to_chain_search"}:
        chains = swap_chains(context)
        chain = find_chain(chains, text)
        if not chain:
            await update.message.reply_text(ltext(lang, "❌ Chain not found. Try a chain name, key, or chain ID.", "❌ Chain পাওয়া যায়নি। Chain name, key, অথবা chain ID লিখুন।"), reply_markup=swap_cancel_keyboard(lang))
            return True
        target = "from" if step.startswith("from") else "to"
        context.user_data[f"swap_{target}_chain_id"] = int(chain["id"])
        context.user_data[f"swap_{target}_chain_name"] = chain_label(chain)
        if target == "from":
            context.user_data["swap_step"] = "from_token"
            await update.message.reply_text(ltext(lang, f"Source chain: {chain_label(chain)}\n\nSend source token contract address or symbol (example: USDC). For native coin, send native.", f"Source chain: {chain_label(chain)}\n\nSource token contract address অথবা symbol পাঠান (যেমন: USDC)। Native coin হলে native লিখুন।"), reply_markup=swap_cancel_keyboard(lang))
        else:
            context.user_data["swap_step"] = "to_token"
            await update.message.reply_text(ltext(lang, f"Destination chain: {chain_label(chain)}\n\nSend receive token contract address or symbol (example: USDC). For native coin, send native.", f"Destination chain: {chain_label(chain)}\n\nReceive token contract address অথবা symbol পাঠান (যেমন: USDC)। Native coin হলে native লিখুন।"), reply_markup=swap_cancel_keyboard(lang))
        return True

    if step == "from_token":
        context.user_data["swap_from_token"] = text
        context.user_data["swap_step"] = "to_chain"
        await update.message.reply_text(ltext(lang, "Now choose destination chain.", "এবার destination chain বেছে নিন।"), reply_markup=swap_chain_keyboard(swap_chains(context), "to", 0, lang))
        return True

    if step == "to_token":
        context.user_data["swap_to_token"] = text
        context.user_data["swap_step"] = "amount"
        await update.message.reply_text(ltext(lang, "Enter amount to swap/bridge.", "কত amount swap/bridge করবেন লিখুন।"), reply_markup=swap_cancel_keyboard(lang))
        return True

    if step == "amount":
        amount_text = text.strip()
        try:
            amount = Decimal(amount_text)
            if amount <= 0 or not amount.is_finite():
                raise ValueError
        except (InvalidOperation, ValueError):
            await update.message.reply_text(ltext(lang, "❌ Invalid amount. Send a number greater than 0.", "❌ Amount ভুল। 0-এর বেশি সংখ্যা লিখুন।"), reply_markup=swap_cancel_keyboard(lang))
            return True
        context.user_data["swap_amount"] = amount_text
        context.user_data["swap_step"] = "wallet"
        target_chain_id = context.user_data.get("swap_to_chain_id")
        target_chain = find_chain(swap_chains(context), target_chain_id)
        network = lifi_chain_to_network(target_chain)
        await update.message.reply_text(
            ltext(
                lang,
                f"Send your wallet address. This address will sign and receive the swap/bridge.\n\nExample: {wallet_hint(network)}",
                f"আপনার wallet address পাঠান। এই address transaction sign করবে এবং receive করবে।\n\nউদাহরণ: {wallet_hint(network)}"
            ),
            reply_markup=swap_cancel_keyboard(lang)
        )
        return True

    if step == "wallet":
        target_chain_id = context.user_data.get("swap_to_chain_id")
        target_chain = find_chain(swap_chains(context), target_chain_id)
        network = lifi_chain_to_network(target_chain)
        if not valid_wallet(network, text):
            chain_name = (target_chain or {}).get("name") or "destination"
            msg = ltext(
                lang,
                f"❌ Invalid wallet address for {chain_name}. Example: {wallet_hint(network)}",
                f"❌ {chain_name}-এর জন্য wallet address ভুল। উদাহরণ: {wallet_hint(network)}"
            )
            await update.message.reply_text(msg, reply_markup=swap_cancel_keyboard(lang))
            return True
        context.user_data["swap_wallet"] = text
        context.user_data["swap_step"] = "preference"
        await update.message.reply_text(ltext(lang, "Choose routing preference.", "Route preference বেছে নিন।"), reply_markup=swap_quote_keyboard(lang))
        return True

    if step == "in_bot_password":
        password = text
        chat_id = update.effective_chat.id
        try:
            await update.message.delete()
        except Exception:
            pass

        quote = context.user_data.get("swap_quote")
        intent = context.user_data.get("swap_intent")
        if not quote or not intent:
            await context.bot.send_message(chat_id, "❌ Quote expired.")
            return True

        from_chain_id = intent.get("from_chain_id")
        chains = swap_chains(context)
        from_chain = find_chain(chains, from_chain_id)
        chain_type = str((from_chain or {}).get("chainType") or "").upper()
        network = lifi_chain_to_network(from_chain)

        if chain_type == "SVM" or str(from_chain_id) == "1151111081099710":
            wallet_row = get_user_solana_wallet(user_id)
        elif chain_type == "EVM":
            wallet_row = get_user_evm_wallet(user_id)
        else:
            wallet_row = get_user_wallet(user_id)

        if not wallet_row:
            await context.bot.send_message(chat_id, "❌ No personal wallet found for this chain type.")
            return True

        try:
            private_key = decrypt_key(wallet_row[0], wallet_row[1], password)
        except Exception:
            await context.bot.send_message(chat_id, ltext(lang, "❌ Invalid password. Please try again.", "❌ ভুল পাসওয়ার্ড। আবার চেষ্টা করুন।"), reply_markup=swap_cancel_keyboard(lang))
            return True

        signer_address = get_wallet_address(network, private_key)
        intent["wallet"] = signer_address  # fromAddress must match the signer
        quote = await asyncio.get_running_loop().run_in_executor(
            None, lambda: quote_lifi(intent, api_key=swap_provider_key("lifi"))
        )
        summary = summarize_quote(quote)
        await context.bot.send_message(chat_id, ltext(lang, "⏳ Processing in-bot swap... Please wait.", "⏳ বটের মাধ্যমে Swap করা হচ্ছে... অনুগ্রহ করে অপেক্ষা করুন।"))

        try:
            rpc_url = None
            explorer_url = ""
            if from_chain:
                metamask = from_chain.get("metamask", {})
                rpc_url = (metamask.get("rpcUrls") or [None])[0]
                explorer_url = (metamask.get("blockExplorerUrls") or [""])[0]

            # 1. Handle Approval if needed
            if summary["approval_needed"]:
                await context.bot.send_message(chat_id, ltext(lang, f"🔓 Approving {summary['from_symbol']}...", f"🔓 {summary['from_symbol']} অ্যাপ্রুভ করা হচ্ছে..."))
                approval_data = await asyncio.get_running_loop().run_in_executor(None, lambda: fetch_lifi_approval(from_chain_id, quote["action"]["fromToken"]["address"], quote["action"]["fromAmount"], api_key=swap_provider_key("lifi")))
                if chain_type == "SVM" or str(from_chain_id) == "1151111081099710":
                    # Solana usually doesn't need explicit approval in this way, LI.FI handles it in the swap TX
                    pass
                else:
                    if not network and not rpc_url:
                        raise ValueError(f"Unknown network and no RPC URL available for chain {from_chain_id}. Cannot send approval transaction.")
                    approve_hash = await asyncio.get_running_loop().run_in_executor(None, lambda: send_raw_evm_transaction(network, private_key, approval_data["to"], approval_data["data"], rpc_url=rpc_url))
                    await context.bot.send_message(chat_id, ltext(lang, f"✅ Approval sent: `{approve_hash}`\nWaiting 15s for confirmation...", f"✅ Approval সম্পন্ন: `{approve_hash}`\n১৫ সেকেন্ড অপেক্ষা করুন..."))
                    await asyncio.sleep(15)

            # 2. Execute Swap
            await context.bot.send_message(chat_id, ltext(lang, "🔁 Executing swap/bridge transaction...", "🔁 Swap/bridge ট্রানজ্যাকশন করা হচ্ছে..."))
            tx = quote.get("transactionRequest")
            if chain_type == "SVM" or str(from_chain_id) == "1151111081099710":
                swap_hash = await asyncio.get_running_loop().run_in_executor(None, lambda: send_raw_solana_transaction(private_key, tx["data"], rpc_url=rpc_url))
            else:
                if not network and not rpc_url:
                    raise ValueError(f"Unknown network and no RPC URL available for chain {from_chain_id}. Cannot send swap transaction.")
                swap_hash = await asyncio.get_running_loop().run_in_executor(None, lambda: send_raw_evm_transaction(network, private_key, tx["to"], tx["data"], value=tx.get("value", 0), rpc_url=rpc_url))

            await context.bot.send_message(
                chat_id,
                panel(
                    "🎉 In-Bot Swap Successful",
                    ltext(
                        lang,
                        f"Your swap/bridge transaction has been broadcasted.\n\nHash: `{swap_hash}`\n\nTrack it here: {explorer_url}{swap_hash}",
                        f"আপনার swap/bridge ট্রানজ্যাকশন সম্পন্ন হয়েছে।\n\nHash: `{swap_hash}`\n\nলিংক: {explorer_url}{swap_hash}"
                    )
                ),
                reply_markup=main_menu(user_id, lang)
            )

            # Start tracking task
            asyncio.create_task(track_swap_status(context.bot, chat_id, from_chain_id, swap_hash, lang))

            for k in ("swap_intent", "swap_quote", "swap_step", "swap_wallet",
                      "swap_from_chain_id", "swap_to_chain_id", "swap_amount"):
                context.user_data.pop(k, None)
        except Exception as exc:
            logger.error("In-bot swap failed: %s", exc)
            await context.bot.send_message(chat_id, ltext(lang, "❌ In-bot swap failed. Please try again later.", "❌ বটের মাধ্যমে Swap ব্যর্থ হয়েছে।"), reply_markup=main_menu(user_id, lang))
            context.user_data.clear()
        return True

    if step == "track_hash":
        from_chain_id = context.user_data.get("swap_from_chain_id")
        from_chain = find_chain(swap_chains(context), from_chain_id)
        from_network = lifi_chain_to_network(from_chain)
        if from_network != "solana" and (not text.startswith("0x") or len(text) < 30):
            await update.message.reply_text(ltext(lang, "Paste a transaction hash, or use /start to close.", "Transaction hash পাঠান, অথবা বন্ধ করতে /start দিন।"))
            return True
        if from_network == "solana" and len(text) < 32:
            await update.message.reply_text(ltext(lang, "Paste a valid Solana transaction hash, or use /start to close.", "সঠিক Solana transaction hash পাঠান, অথবা বন্ধ করতে /start দিন।"))
            return True
        intent = context.user_data.get("swap_intent") or {}
        await update.message.reply_text(
            panel(
                "🔎 Swap Tracking",
                ltext(
                    lang,
                    f"Hash received: `{text}`\n\nTrack it in the source-chain explorer for now. LI.FI route: {intent.get('from_chain_name', 'source')} → {intent.get('to_chain_name', 'destination')}.",
                    f"Hash received: `{text}`\n\nএখন source-chain explorer-এ track করুন। LI.FI route: {intent.get('from_chain_name', 'source')} → {intent.get('to_chain_name', 'destination')}।",
                ),
            ),
            reply_markup=main_menu(user_id, lang),
        )
        context.user_data.clear()
        return True

    return True


async def waiting_trxid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    username = update.effective_user.username or update.effective_user.first_name
    incoming_text = (update.message.text or update.message.caption or "").strip()
    lang = user_lang(user_id)

    if await handle_telegram_id_finder_message(update, context, user_id, lang, incoming_text):
        return

    if await handle_solana_refund_text(update, context, user_id, lang, incoming_text):
        return

    if await handle_free_forward_text(update, context, user_id, lang, incoming_text):
        return

    if await handle_swap_text(update, context, user_id, lang, incoming_text):
        return

    lang = maybe_update_language(user_id, incoming_text)

    if context.user_data.get("order_status_lookup"):
        context.user_data.clear()
        await update.message.reply_text(
            order_status_text(incoming_text, user_id, lang),
            reply_markup=order_status_ai_keyboard(incoming_text, user_id, lang) or main_menu(user_id, lang),
        )
        return

    if context.user_data.get("payout_request"):
        context.user_data.clear()
        await create_payout_from_text(update, user_id, incoming_text)
        return

    if context.user_data.get("admin_user_analytics_lookup"):
        if not is_admin(user_id):
            context.user_data.pop("admin_user_analytics_lookup", None)
            context.user_data.pop("user_search_active", None)
            return

        target_query = incoming_text.strip()
        if context.user_data.get("user_search_active"):
            context.user_data.pop("user_search_active", None)
            context.user_data.pop("admin_user_analytics_lookup", None)
            # Store query server-side so pagination callbacks don't embed it
            context.user_data["user_search_query"] = target_query
            filter_type = "search"
            rows, total = get_users_paged(filter_type, 0, target_query)
            total_pages = math.ceil(total / 10) if total > 0 else 1
            await update.message.reply_text(users_list_text(rows, total, filter_type, 0), reply_markup=users_keyboard(filter_type, 0, total_pages, target_query))
        else:
            await update.message.reply_text(user_analytics_text(target_query, lang), reply_markup=back_keyboard(lang))
            context.user_data.pop("admin_user_analytics_lookup", None)
        return

    ref_admin_set = context.user_data.get("ref_admin_set")
    if ref_admin_set:
        if not is_admin(user_id):
            context.user_data.pop("ref_admin_set", None)
            return
        try:
            value = float(incoming_text)
            if ref_admin_set == "percent" and not (0 <= value <= 20):
                raise ValueError
            if ref_admin_set == "min" and value < 0:
                raise ValueError
        except Exception:
            await update.message.reply_text("❌ Invalid value. Percent must be 0-20; min withdraw must be non-negative.", reply_markup=referral_admin_keyboard(lang))
            return
        key = "referral_percent" if ref_admin_set == "percent" else "referral_min_withdraw_usd"
        set_setting(key, value)
        add_audit(user_id, "referral_setting_changed", "setting", key, str(value))
        context.user_data.clear()
        await update.message.reply_text(referral_admin_text(), reply_markup=referral_admin_keyboard(lang))
        return

    if context.user_data.get("ref_withdraw_step"):
        await handle_referral_withdraw_text(update, context, user_id, lang, incoming_text)
        return

    setup_provider = context.user_data.get("ai_setup_provider")
    if setup_provider:
        if not is_admin(user_id):
            context.user_data.pop("ai_setup_provider", None)
            return
        text = incoming_text.strip()
        if text.lower() in {"/cancel", "cancel", "close", "stop", "বন্ধ", "বাতিল"}:
            context.user_data.pop("ai_setup_provider", None)
            await update.message.reply_text("✅ AI Setup cancelled." if lang == "en" else "✅ AI Setup বাতিল হয়েছে।", reply_markup=ai_setup_keyboard(lang))
            return
        if setup_provider not in AI_PROVIDER_SETTING_KEYS:
            context.user_data.pop("ai_setup_provider", None)
            await update.message.reply_text("❌ Invalid AI provider.", reply_markup=ai_setup_keyboard(lang))
            return
        api_key = _clean_ai_key(text)
        if not api_key or len(api_key) < 12:
            await update.message.reply_text(ltext(lang, "❌ API key is too short or empty. Send the correct key, or send /cancel.", "❌ API key খুব ছোট/খালি। সঠিক key পাঠান, অথবা /cancel লিখুন।"), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel" if lang == "en" else "❌ বাতিল", callback_data="ai_setup_cancel")]]))
            return
        try:
            await update.message.delete()
        except Exception:
            pass
        set_setting(AI_PROVIDER_SETTING_KEYS[setup_provider], api_key)
        context.user_data.pop("ai_setup_provider", None)
        add_audit(user_id, "ai_api_key_updated", "ai_provider", setup_provider, "configured via bot setup")
        await update.message.reply_text(f"✅ {AI_PROVIDER_LABELS[setup_provider]} API key saved. {'No restart required.' if lang == 'en' else 'Restart লাগবে না।'}\n\n{ai_setup_text(lang)}", reply_markup=ai_setup_keyboard(lang))
        return

    if context.user_data.get("ai_support"):
        text = incoming_text
        if text.lower() in {"/cancel", "cancel", "বন্ধ", "বাতিল"}:
            history = context.user_data.get("ai_support_history", [])
            order_context = context.user_data.get("ai_order_context_identifier")
            context.user_data.clear()
            context.user_data["ai_support_history"] = history
            if order_context:
                context.user_data["ai_order_context_identifier"] = order_context
            await update.message.reply_text("✅ AI Support closed." if lang == "en" else "✅ AI Support বন্ধ হয়েছে।", reply_markup=main_menu(user_id, lang))
            return
        if context.user_data.get("ai_support_pending"):
            await update.message.reply_text(
                "⏳ Previous AI answer is still being prepared. Please wait a moment."
                if lang == "en"
                else "⏳ আগের AI উত্তর এখনও তৈরি হচ্ছে। একটু অপেক্ষা করুন।"
            )
            return AI_SUPPORT
        pending_token = secrets.token_hex(8)
        context.user_data["ai_support_pending"] = pending_token
        await update.message.reply_text(tr("ai_thinking", lang))
        chat_id = update.effective_chat.id if update.effective_chat else update.message.chat_id
        context.application.create_task(
            _send_ai_support_answer(context.bot, chat_id, user_id, text, lang, pending_token, context.user_data)
        )
        return AI_SUPPORT

    if context.user_data.get("waiting_seller_trxid"):
        deadline = context.user_data.get("trx_deadline", 0)
        if asyncio.get_event_loop().time() > deadline:
            context.user_data.clear()
            await update.message.reply_text("⏰ Seller order time expired. আবার order করুন।")
            return
        return await handle_seller_order_trx(update, context, user_id, username)

    if is_admin(user_id) and context.user_data.get("gencode_step") == "custom_amount":
        try:
            amount = float(update.message.text.strip())
            if amount <= 0:
                raise ValueError
        except Exception:
            await update.message.reply_text(tr("invalid_amount", lang))
            return GEN_CUSTOM_AMOUNT
        context.user_data["gencode_amount"] = amount
        context.user_data["gencode_step"] = "duration"
        await update.message.reply_text(tr("code_select_duration", lang), reply_markup=gencode_duration_keyboard(lang))
        return

    if is_admin(user_id) and context.user_data.get("gencode_step") == "custom_duration":
        try:
            minutes = int(update.message.text.strip())
            if minutes <= 0:
                raise ValueError
        except Exception:
            await update.message.reply_text(tr("enter_custom_duration", lang))
            return GEN_CUSTOM_DURATION
        await create_gift_code_from_context(update.message, context, minutes, lang)
        return

    if context.user_data.get("giveaway_step"):
        return await handle_giveaway_text(update, context, user_id)

    if context.user_data.get("redeem_step"):
        return await handle_redeem(update, context, user_id, username)
    if context.user_data.get("uw_waiting_bal_password"):
        return await handle_balance_password(update, context, user_id)
    if not context.user_data.get("waiting_trxid"):
        return

    deadline = context.user_data.get("trx_deadline", 0)
    if asyncio.get_event_loop().time() > deadline:
        if context.user_data.get("order_id"):
            release_stock_reservation(order_id=context.user_data.get("order_id"), reason="buyer_timeout", actor_id="system")
        context.user_data.clear()
        await update.message.reply_text(ltext(lang, f"⏰ Time limit expired.\n\nPlease create a new order with /start.\n\n📞 @{SUPPORT_USERNAME.lstrip('@')}", f"⏰ সময়সীমা শেষ!\n\nআবার অর্ডার করুন /start দিয়ে\n\n📞 @{SUPPORT_USERNAME.lstrip('@')}"))
        return

    trx_id = incoming_text.upper()
    if len(trx_id) < 4:
        await update.message.reply_text(ltext(lang, "❌ Invalid TrxID. Please try again.", "❌ ভুল TrxID! আবার চেষ্টা করুন।"))
        return
    if trx_exists(trx_id):
        await update.message.reply_text(ltext(lang, f"⚠️ This TrxID has already been used.\n\n📞 @{SUPPORT_USERNAME.lstrip('@')}", f"⚠️ এই TrxID আগেই ব্যবহার হয়েছে!\n\n📞 @{SUPPORT_USERNAME.lstrip('@')}"))
        return

    wallet = get_wallet(user_id)
    network = context.user_data.get("network", "solana")
    net_info = NETWORKS[network]
    if not wallet:
        await update.message.reply_text(ltext(lang, "❌ Wallet not found.\n\nPlease start again with /start.", "❌ Wallet পাওয়া যায়নি!\n\n/start দিয়ে আবার শুরু করুন।"))
        return

    sms_row = get_sms(trx_id)
    if not sms_row:
        amount_bdt = context.user_data.get("amount_bdt", 0)
        crypto_amount = context.user_data.get("usdc_amount", 0)
        order_id = context.user_data.get("order_id") or f"ORD-{gen_code(6)}"
        order_id = save_pending_order(trx_id, user_id, amount_bdt, crypto_amount, wallet, network, order_id=order_id)
        bind_stock_reservation_trx(order_id, trx_id)
        keyboard = [[InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user_id}_{trx_id}_{network}"), InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user_id}_{trx_id}")]]
        try:
            await update.get_bot().send_message(
                ADMIN_ID,
                f"⚠️ Manual Verify দরকার\n{DIVIDER}\n"
                "📌 Status: bKash SMS/notice পাওয়া যায়নি\n"
                f"🧾 Order: {order_id}\n"
                f"👤 User: @{username} ({user_id})\n"
                f"🔑 TrxID: {trx_id}\n"
                f"💰 Amount: {amount_bdt} BDT\n"
                f"💵 Est: {crypto_amount} {net_info['symbol']}\n"
                f"🌐 Network: {net_info['name']}\n"
                f"👛 Wallet short: {short_wallet(wallet)}\n"
                f"👛 Wallet full: {wallet}\n\n"
                "Action: bKash app-এ TrxID/amount verify করে Approve বা Reject চাপুন।",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
        except Exception as exc:
            logger.error(exc)
        await update.message.reply_text(
            ltext(lang, f"⏳ Checking your TrxID.\n\n🔑 TrxID: {trx_id}\n\nAdmin will verify it manually. Please wait.", f"⏳ TrxID যাচাই করা হচ্ছে।\n\n🔑 TrxID: {trx_id}\n\nAdmin যাচাই করছেন, একটু অপেক্ষা করুন..."),
            reply_markup=track_order_keyboard(order_id, user_id, lang),
        )
        return

    amount_bdt = sms_row[1]
    crypto_amount = round(amount_bdt / get_rate(network), 6)
    order_id = context.user_data.get("order_id") or f"ORD-{gen_code(6)}"
    bind_stock_reservation_trx(order_id, trx_id)
    sufficient, current_bal = check_sufficient(network, crypto_amount, exclude_order_id=order_id)
    if not sufficient and current_bal is not None:
        await update.message.reply_text(ltext(lang, f"❌ Insufficient {net_info['symbol']} stock.\n\n🌐 {net_info['name']}\n💵 Requested: {crypto_amount}\n{stock_detail(network, crypto_amount, current_bal)}\n\n📞 @{SUPPORT_USERNAME.lstrip('@')}", f"❌ পর্যাপ্ত {net_info['symbol']} নেই!\n\n🌐 {net_info['name']}\n💵 চান: {crypto_amount}\n{stock_detail(network, crypto_amount, current_bal)}\n\n📞 @{SUPPORT_USERNAME.lstrip('@')}"))
        return

    await update.message.reply_text(ltext(lang, f"✅ Payment verified!\n\n🌐 {net_info['name']}\n💰 {amount_bdt} BDT = {crypto_amount} {net_info['symbol']}\n👛 {wallet}\n\n⏳ Sending...", f"✅ পেমেন্ট যাচাই সফল!\n\n🌐 {net_info['name']}\n💰 {amount_bdt} BDT = {crypto_amount} {net_info['symbol']}\n👛 {wallet}\n\n⏳ পাঠানো হচ্ছে..."))
    try:
        sig = await send_crypto(network, wallet, crypto_amount)
        mark_sms_used(trx_id)
        order_id = save_transaction(trx_id, user_id, amount_bdt, crypto_amount, wallet, sig, "completed", network, order_id=order_id, source="bkash")
        record_referral_reward_for_transaction(user_id, "bkash", trx_id, network, crypto_amount, amount_bdt, f"order={order_id}")
        consume_stock_reservation(order_id=order_id, trx_id=trx_id)
        context.user_data.clear()
        receipt_data = await make_receipt_data(update.get_bot(), order_id, trx_id, network, crypto_amount, wallet, sig, user_id, buyer_username=username, bdt_amount=amount_bdt, title="Smart Crypto Buy")
        await send_transaction_receipt(update.get_bot(), [user_id, ADMIN_ID], receipt_data)
    except Exception as exc:
        save_transaction(trx_id, user_id, amount_bdt, crypto_amount, wallet, "", "failed", network, order_id=order_id, source="bkash")
        release_stock_reservation(order_id=order_id, trx_id=trx_id, reason="send_failed", actor_id="system")
        add_audit("system", "send_failed", "transaction", trx_id, str(exc))
        context.user_data.clear()
        logger.error("Send failed: %s", exc)
        reason = failure_reason_text(exc, network, lang)
        await update.message.reply_text(
            f"❌ Delivery failed after payment verification.\n\n💡 {reason}\n\nSave your TrxID: {trx_id}\n📞 @{SUPPORT_USERNAME.lstrip('@')}"
            if lang == "en"
            else f"❌ পাঠাতে সমস্যা!\n\n💡 {reason}\n\nআপনার TrxID: {trx_id}\nসংরক্ষণ করুন।\n📞 @{SUPPORT_USERNAME.lstrip('@')}"
        )


async def free_forward_media_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    incoming_text = (update.message.text or update.message.caption or "").strip()
    if await handle_telegram_id_finder_message(update, context, user_id, user_lang(user_id), incoming_text):
        return
    if not context.user_data.get("free_forward_step"):
        return
    await handle_free_forward_text(update, context, user_id, user_lang(user_id), incoming_text)


async def handle_giveaway_text(update, context, user_id):
    lang = user_lang(user_id)
    step = context.user_data.get("giveaway_step")
    text = update.message.text.strip()
    if text.lower() in {"/cancel", "cancel", "বন্ধ", "বাতিল"}:
        context.user_data.clear()
        await update.message.reply_text(ltext(lang, "✅ Giveaway cancelled.", "✅ Giveaway বাতিল হয়েছে।"), reply_markup=main_menu(user_id, lang))
        return
    if step == "count":
        try:
            count = int(text)
            if count <= 0 or count > 100:
                raise ValueError
        except Exception:
            await update.message.reply_text(ltext(lang, "❌ Enter a recipient count between 1 and 100.", "❌ 1 থেকে 100 এর মধ্যে recipient count লিখুন।"))
            return
        context.user_data["giveaway_count"] = count
        context.user_data["giveaway_step"] = "base_amount"
        network = context.user_data.get("giveaway_network", "solana")
        ni = NETWORKS.get(network, {"symbol": "?"})
        await update.message.reply_text(ltext(lang, f"💵 Base amount per winner? Send {ni['symbol']} amount.", f"💵 প্রতি winner base amount কত? {ni['symbol']} amount লিখুন।"))
        return
    if step == "base_amount":
        try:
            amount = float(text)
            if amount <= 0:
                raise ValueError
        except Exception:
            await update.message.reply_text(tr("invalid_amount", lang))
            return
        context.user_data["giveaway_base_amount"] = amount
        context.user_data["giveaway_step"] = "bonus_choice"
        await update.message.reply_text(ltext(lang, "🎯 Add an early-claimer bonus?", "🎯 Early claimer bonus যোগ করবেন?"), reply_markup=giveaway_bonus_keyboard(lang))
        return
    if step == "bonus_count":
        try:
            count = int(text)
            if count <= 0 or count > int(context.user_data.get("giveaway_count", 0)):
                raise ValueError
        except Exception:
            await update.message.reply_text(ltext(lang, "❌ Enter a bonus count from 1 up to recipient count.", "❌ 1 থেকে recipient count পর্যন্ত bonus count লিখুন।"))
            return
        context.user_data["giveaway_bonus_count"] = count
        context.user_data["giveaway_step"] = "bonus_amount"
        network = context.user_data.get("giveaway_network", "solana")
        ni = NETWORKS.get(network, {"symbol": "?"})
        await update.message.reply_text(ltext(lang, f"💵 Bonus amount per early claimer? Send extra {ni['symbol']} amount.", f"💵 প্রতি early claimer bonus amount কত? Extra {ni['symbol']} amount লিখুন।"))
        return
    if step == "bonus_amount":
        try:
            amount = float(text)
            if amount <= 0:
                raise ValueError
        except Exception:
            await update.message.reply_text(tr("invalid_amount", lang))
            return
        context.user_data["giveaway_bonus_amount"] = amount
        context.user_data["giveaway_step"] = "duration"
        await update.message.reply_text(ltext(lang, "⏰ Choose giveaway duration:", "⏰ Giveaway মেয়াদ বেছে নিন:"), reply_markup=giveaway_duration_keyboard(lang))
        return
    if step == "custom_duration":
        try:
            minutes = int(text)
            if minutes <= 0:
                raise ValueError
        except Exception:
            await update.message.reply_text(tr("enter_custom_duration", lang))
            return
        if context.user_data.get("giveaway_source") == "user_wallet":
            context.user_data["giveaway_minutes"] = minutes
            context.user_data["giveaway_step"] = "password"
            await update.message.reply_text(ltext(lang, "🔐 Enter your wallet password to confirm.\n\n⚠️ Your message will be deleted after you send it.", "🔐 Confirm করতে wallet password দিন।\n\n⚠️ Message পাঠানোর পর মুছে যাবে।"))
            return
        await create_giveaway_from_context(update.message, context, user_id, lang, minutes)
        return
    if step == "password":
        password = text
        try:
            await update.message.delete()
        except Exception:
            pass
        minutes = int(context.user_data.get("giveaway_minutes", 0))
        await create_giveaway_from_context(update.message, context, user_id, lang, minutes, password=password)
        return


async def handle_redeem(update, context, user_id, username):
    lang = user_lang(user_id)
    if context.user_data.get("redeem_step") == "code":
        code = update.message.text.strip().upper()
        row = get_code(code)
        if not row:
            await update.message.reply_text(ltext(lang, "❌ Code not found.\n\nEnter the correct code.", "❌ কোড পাওয়া যায়নি!\n\nসঠিক কোড লিখুন।"))
            return
        _code_val, amount_crypto, expires_at, used, _used_by, _created_at, code_network, giveaway_id, _creator_id, _claim_number, _claimed_amount = row
        if used:
            await update.message.reply_text(ltext(lang, f"⚠️ This code has already been used.\n\n📞 @{SUPPORT_USERNAME.lstrip('@')}", f"⚠️ এই কোড আগেই ব্যবহার হয়েছে!\n\n📞 @{SUPPORT_USERNAME.lstrip('@')}"))
            context.user_data.clear()
            return
        if datetime.now() > datetime.fromisoformat(expires_at):
            await update.message.reply_text(ltext(lang, f"⏰ This code has expired.\n\n📞 @{SUPPORT_USERNAME.lstrip('@')}", f"⏰ এই কোডের মেয়াদ শেষ!\n\n📞 @{SUPPORT_USERNAME.lstrip('@')}"))
            context.user_data.clear()
            return
        net_info = NETWORKS.get(code_network, NETWORKS["solana"])
        context.user_data.update({"redeem_code": code, "redeem_usdc": amount_crypto, "redeem_network": code_network, "redeem_giveaway_id": giveaway_id, "redeem_step": "wallet"})
        if giveaway_id:
            session = get_giveaway_session(giveaway_id)
            if not session:
                await update.message.reply_text(ltext(lang, "❌ Giveaway session not found. Contact support.", "❌ Giveaway session পাওয়া যায়নি। Support-এ যোগাযোগ করুন।"))
                context.user_data.clear()
                return
            bonus_line = ltext(lang, "No early bonus.", "Early bonus নেই।")
            if int(session[6] or 0) > 0 and float(session[7] or 0) > 0:
                bonus_line = ltext(lang, f"First {session[6]} successful claimers get +{session[7]} {net_info['symbol']} extra if still available.", f"প্রথম {session[6]} জন successful claimer +{session[7]} {net_info['symbol']} extra পাবে, slot থাকলে।")
            await update.message.reply_text(ltext(lang, f"✅ Giveaway code verified!\n\n🧾 Session: {giveaway_id}\n🎁 Base: {session[4]} {net_info['symbol']}\n🎯 {bonus_line}\n🌐 Network: {net_info['name']}\n\nEnter your {net_info['name']} wallet address:\n\n📋 Example: {wallet_hint(code_network)}", f"✅ Giveaway code যাচাই সফল!\n\n🧾 Session: {giveaway_id}\n🎁 Base: {session[4]} {net_info['symbol']}\n🎯 {bonus_line}\n🌐 Network: {net_info['name']}\n\nআপনার {net_info['name']} Wallet Address দিন:\n\n📋 উদাহরণ: {wallet_hint(code_network)}"))
        else:
            await update.message.reply_text(ltext(lang, f"✅ Code verified!\n\n🎁 You receive: {amount_crypto} {net_info['symbol']}\n🌐 Network: {net_info['name']}\n\nEnter your {net_info['name']} wallet address:\n\n📋 Example: {wallet_hint(code_network)}", f"✅ কোড যাচাই সফল!\n\n🎁 পাবেন: {amount_crypto} {net_info['symbol']}\n🌐 নেটওয়ার্ক: {net_info['name']}\n\nআপনার {net_info['name']} Wallet Address দিন:\n\n📋 উদাহরণ: {wallet_hint(code_network)}"))
        return

    wallet = update.message.text.strip()
    network = context.user_data.get("redeem_network", "solana")
    net_info = NETWORKS[network]
    if not valid_wallet(network, wallet):
        await update.message.reply_text(ltext(lang, f"❌ Invalid {net_info['name']} wallet.\n\nEnter the correct address.", f"❌ ভুল {net_info['name']} wallet!\n\nসঠিক address দিন।"))
        return
    code = context.user_data["redeem_code"]
    amount_crypto = context.user_data["redeem_usdc"]
    giveaway_id = context.user_data.get("redeem_giveaway_id")
    context.user_data.clear()
    if giveaway_id:
        claim = claim_giveaway_code(code, user_id)
        if not claim.get("ok"):
            reason = claim.get("reason")
            messages = {
                "used": ltext(lang, f"⚠️ This code has already been claimed.\n\n📞 @{SUPPORT_USERNAME.lstrip('@')}", f"⚠️ এই code আগেই claim হয়েছে!\n\n📞 @{SUPPORT_USERNAME.lstrip('@')}"),
                "expired": ltext(lang, f"⏰ This code has expired.\n\n📞 @{SUPPORT_USERNAME.lstrip('@')}", f"⏰ এই code-এর মেয়াদ শেষ!\n\n📞 @{SUPPORT_USERNAME.lstrip('@')}"),
                "fully_claimed": ltext(lang, f"⚠️ Giveaway is already fully claimed.\n\n📞 @{SUPPORT_USERNAME.lstrip('@')}", f"⚠️ Giveaway ইতিমধ্যে fully claimed।\n\n📞 @{SUPPORT_USERNAME.lstrip('@')}"),
            }
            await update.message.reply_text(messages.get(reason, ltext(lang, f"❌ Could not claim this giveaway code.\nCode: {code}\n📞 @{SUPPORT_USERNAME.lstrip('@')}", f"❌ এই giveaway code claim করা যায়নি।\nCode: {code}\n📞 @{SUPPORT_USERNAME.lstrip('@')}")))
            return
        network = claim["network"]
        net_info = NETWORKS[network]
        amount_crypto = claim["amount"]
        claim_line = f"#{claim['claim_number']}/{claim['recipient_count']}"
        await update.message.reply_text(ltext(lang, f"⏳ Giveaway claim reserved {claim_line}. Sending {amount_crypto} {net_info['symbol']}...\n\n🌐 {net_info['name']}\n👛 {wallet}", f"⏳ Giveaway claim reserved {claim_line}. {amount_crypto} {net_info['symbol']} পাঠানো হচ্ছে...\n\n🌐 {net_info['name']}\n👛 {wallet}"))
        try:
            if claim["source"] == "admin_stock":
                sig = await send_crypto(network, wallet, amount_crypto)
            else:
                private_key = decrypt_seller_key(claim["encrypted_key"], claim["salt"])
                loop = asyncio.get_running_loop()
                sig = await loop.run_in_executor(None, lambda: send_with_private_key(network, private_key, wallet, amount_crypto))
            order_id = save_transaction(f"GIFT-{code}", user_id, 0, amount_crypto, wallet, sig, "completed", network, order_id=claim["session_id"], source="giveaway", seller_id=claim.get("creator_id") if claim["source"] == "user_wallet" else None)
            seller_id = claim.get("creator_id") if claim["source"] == "user_wallet" else ADMIN_ID
            receipt_data = await make_receipt_data(update.get_bot(), order_id, f"GIFT-{code}", network, amount_crypto, wallet, sig, user_id, buyer_username=username, seller_id=seller_id, bdt_amount=0, title="Smart Crypto Buy")
            await send_transaction_receipt(update.get_bot(), [user_id, seller_id, ADMIN_ID], receipt_data)
        except Exception as exc:
            save_transaction(f"GIFT-{code}", user_id, 0, amount_crypto, wallet, "", "failed", network, order_id=claim["session_id"], source="giveaway", seller_id=claim.get("creator_id") if claim["source"] == "user_wallet" else None)
            add_audit("system", "giveaway_send_failed", "gift_code", code, f"session={claim['session_id']} error={exc}")
            msg = ltext(lang, f"❌ Giveaway delivery failed after claim was reserved.\n\nCode: {code}\nSession: {claim['session_id']}\n💡 {failure_reason_text(exc, network, lang)}\n📞 @{SUPPORT_USERNAME.lstrip('@')}", f"❌ Claim reserve হওয়ার পর giveaway delivery failed।\n\nCode: {code}\nSession: {claim['session_id']}\n💡 {failure_reason_text(exc, network, lang)}\n📞 @{SUPPORT_USERNAME.lstrip('@')}")
            await update.message.reply_text(msg)
            fail_msg = f"❌ Giveaway delivery failed\n\nSession: {claim['session_id']}\nCode: {code}\nUser: @{username} ({user_id})\nAmount: {amount_crypto} {net_info['symbol']}\nWallet: {wallet}\nError: {exc}"
            try:
                await update.get_bot().send_message(ADMIN_ID, fail_msg)
            except Exception:
                pass
            if claim["source"] == "user_wallet" and str(claim.get("creator_id")) != str(ADMIN_ID):
                try:
                    await update.get_bot().send_message(int(claim["creator_id"]), fail_msg)
                except Exception:
                    pass
            logger.error("Giveaway redeem failed: %s", exc)
        return

    sufficient, current_bal = check_sufficient(network, amount_crypto)
    if not sufficient and current_bal is not None:
        await update.message.reply_text(ltext(lang, f"❌ Insufficient stock.\n\n{stock_detail(network, amount_crypto, current_bal)}", f"❌ পর্যাপ্ত stock নেই।\n\n{stock_detail(network, amount_crypto, current_bal)}"))
        return
    await update.message.reply_text(ltext(lang, f"⏳ Sending {net_info['symbol']}...\n\n🌐 {net_info['name']}\n💵 {amount_crypto} {net_info['symbol']}\n👛 {wallet}", f"⏳ {net_info['symbol']} পাঠানো হচ্ছে...\n\n🌐 {net_info['name']}\n💵 {amount_crypto} {net_info['symbol']}\n👛 {wallet}"))
    try:
        sig = await send_crypto(network, wallet, amount_crypto)
        use_code(code, user_id)
        order_id = save_transaction(f"GIFT-{code}", user_id, 0, amount_crypto, wallet, sig, "completed", network, source="gift")
        receipt_data = await make_receipt_data(update.get_bot(), order_id, f"GIFT-{code}", network, amount_crypto, wallet, sig, user_id, buyer_username=username, seller_id=ADMIN_ID, bdt_amount=0, title="Smart Crypto Buy")
        await send_transaction_receipt(update.get_bot(), [user_id, ADMIN_ID], receipt_data)
    except Exception as exc:
        await update.message.reply_text(
            f"❌ Gift delivery failed.\n\n💡 {failure_reason_text(exc, network, lang)}\n📞 @{SUPPORT_USERNAME.lstrip('@')}"
            if lang == "en"
            else f"❌ পাঠাতে সমস্যা!\n\n💡 {failure_reason_text(exc, network, lang)}\n📞 @{SUPPORT_USERNAME.lstrip('@')}"
        )
        logger.error("Redeem failed: %s", exc)


async def handle_balance_password(update, context, user_id):
    password = update.message.text.strip()
    try:
        await update.message.delete()
    except Exception:
        pass
    context.user_data.pop("uw_waiting_bal_password", None)
    bal, network, error = get_user_balance(user_id, password)
    if error == "wrong_password":
        await update.message.reply_text("❌ ভুল Password!")
        return
    if error:
        await update.message.reply_text(f"❌ Error: {error}")
        return
    row = get_user_wallet(user_id)
    net_info = NETWORKS.get(network, {"name": network, "symbol": "?"})
    await update.message.reply_text(f"💰 আপনার Balance:\n\n🌐 {net_info['name']}\n👛 {row[3]}\n💵 {bal} {net_info['symbol']}\n\n💸 পাঠাতে: /send_wallet")


async def gencode_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    lang = user_lang(update.effective_user.id)
    context.user_data.clear()
    context.user_data["gencode_step"] = "network"
    await update.message.reply_text(tr("code_select_network", lang), reply_markup=network_menu("gencode", lang))


async def giveaway_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = user_lang(update.effective_user.id)
    await start_giveaway_flow(update.message, context, str(update.effective_user.id), lang)


async def send_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    if len(context.args) != 2:
        await update.message.reply_text("Usage: /send amount wallet")
        return
    try:
        amount = float(context.args[0])
        if amount <= 0:
            raise ValueError
    except Exception:
        await update.message.reply_text("❌ Invalid amount.")
        return
    wallet = context.args[1].strip()
    sufficient, current_bal = check_sufficient("solana", amount)
    if not sufficient and current_bal is not None:
        await update.message.reply_text(f"❌ Insufficient stock.\n\n{stock_detail('solana', amount, current_bal)}")
        return
    await update.message.reply_text(f"⏳ Sending {amount} USDC (Solana)...")
    try:
        sig = await send_crypto("solana", wallet, amount)
        save_transaction(f"ADMIN-{sig[:24]}", update.effective_user.id, 0, amount, wallet, sig, "completed", "solana", source="admin_send")
        add_audit(update.effective_user.id, "admin_send_completed", "transaction", f"ADMIN-{sig[:24]}", f"network=solana amount={amount}")
        text = f"✅ Sent!\n\n💵 {amount} USDC\n👛 {wallet}\n🔗 https://solscan.io/tx/{sig}"
    except Exception as exc:
        failed_id = f"ADMIN-FAILED-{gen_code(8)}"
        save_transaction(failed_id, update.effective_user.id, 0, amount, wallet, "", "failed", "solana", source="admin_send")
        add_audit(update.effective_user.id, "admin_send_failed", "transaction", failed_id, str(exc))
        text = f"❌ Failed!\n{exc}\n\n💡 {failure_reason_text(exc, 'solana', 'en')}"
    await update.message.reply_text(text)


async def setup_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = user_lang(update.effective_user.id)
    await update.message.reply_text(ltext(lang, "🔐 Wallet Setup\n\nSelect your network:\n\n⚠️ Your private key will be encrypted with AES-256.\n❓ Guide: /guide", "🔐 Wallet Setup\n\nআপনার Network বেছে নিন:\n\n⚠️ Private Key AES-256 দিয়ে encrypt হবে\n❓ গাইড: /guide"), reply_markup=user_network_menu(lang))
    return SETUP_NETWORK


async def setup_network_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = user_lang(query.from_user.id)
    if query.data == "uw_cancel":
        await query.edit_message_text(ltext(lang, "❌ Cancelled.", "❌ বাতিল হয়েছে।"))
        return ConversationHandler.END
    network = query.data.replace("uw_", "")
    context.user_data["uw_network"] = network
    net_info = NETWORKS.get(network, {"name": network, "symbol": "?"})
    net_guide = NETWORK_GUIDE.get(network, "")
    await query.edit_message_text(ltext(lang, f"✅ Network: {net_info['name']}\n\n{net_guide}\n━━━━━━━━━━━━━━━━━━━━━\nNow send your private key.\n\n⚠️ The bot will delete your message after receiving it.", f"✅ নেটওয়ার্ক: {net_info['name']}\n\n{net_guide}\n━━━━━━━━━━━━━━━━━━━━━\nএখন আপনার Private Key পাঠান:\n\n⚠️ Message পাঠানোর পর bot স্বয়ংক্রিয়ভাবে মুছে দেবে।"))
    return SETUP_KEY


async def setup_key_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    private_key = update.message.text.strip()
    lang = user_lang(update.effective_user.id)
    network = context.user_data.get("uw_network", "solana")
    try:
        await update.message.delete()
    except Exception:
        pass
    try:
        wallet_address = get_wallet_address(network, private_key)
    except Exception as exc:
        await update.message.reply_text(ltext(lang, f"❌ Invalid private key.\n\n{exc}\n\nPlease try again:", f"❌ Invalid Private Key!\n\n{exc}\n\nআবার চেষ্টা করুন:"))
        return SETUP_KEY
    context.user_data["uw_private_key"] = private_key
    context.user_data["uw_wallet_address"] = wallet_address
    await update.message.reply_text(ltext(lang, f"✅ Key verified!\n\n👛 {wallet_address}\n\nCreate a strong password now:\n\n• At least 8 characters\n• Use letters and numbers\n• If you forget it, the key cannot be recovered\n\nEnter your password:", f"✅ Key যাচাই সফল!\n\n👛 {wallet_address}\n\nএখন একটি শক্তিশালী Password তৈরি করুন:\n\n• কমপক্ষে ৮ character\n• সংখ্যা ও অক্ষর মিলিয়ে দিন\n• Password ভুললে key recover হবে না!\n\nআপনার password লিখুন:"))
    return SETUP_PASSWORD


async def setup_password_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    password = update.message.text.strip()
    user_id = str(update.effective_user.id)
    lang = user_lang(user_id)
    private_key = context.user_data.get("uw_private_key")
    network = context.user_data.get("uw_network")
    wallet_addr = context.user_data.get("uw_wallet_address")
    try:
        await update.message.delete()
    except Exception:
        pass
    if len(password) < 8:
        await update.message.reply_text(ltext(lang, "❌ Password must be at least 8 characters.\n\nEnter it again:", "❌ Password কমপক্ষে ৮ character!\n\nআবার লিখুন:"))
        return SETUP_PASSWORD
    try:
        encrypted_key, salt = encrypt_key(private_key, password)
        save_user_wallet(user_id, encrypted_key, salt, network, wallet_addr)
        context.user_data.clear()
        net_info = NETWORKS.get(network, {"name": network, "symbol": "?"})
        await update.message.reply_text(ltext(lang, f"🎉 Wallet setup complete!\n\n🌐 {net_info['name']}\n👛 {wallet_addr}\n\n💰 /mybalance → Check balance\n💸 /send_wallet → Send crypto\n🔑 /changekey → Change key\n🗑️ /deletekey → Delete key\n📖 /guide → User guide\n\n⚠️ Remember your password!", f"🎉 Wallet Setup সফল!\n\n🌐 {net_info['name']}\n👛 {wallet_addr}\n\n💰 /mybalance → Balance দেখুন\n💸 /send_wallet → Crypto পাঠান\n🔑 /changekey → Key পরিবর্তন\n🗑️ /deletekey → Key মুছুন\n📖 /guide → ব্যবহার বিধি\n\n⚠️ Password মনে রাখুন!"))
    except Exception as exc:
        await update.message.reply_text(ltext(lang, f"❌ Setup failed.\n{exc}", f"❌ Setup ব্যর্থ!\n{exc}"))
    return ConversationHandler.END


async def mybalance_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    lang = user_lang(user_id)
    if not get_user_wallet(user_id):
        await update.message.reply_text(ltext(lang, "❌ No wallet is set up.\n\nStart with: /setup", "❌ Wallet setup নেই!\n\nপ্রথমে: /setup"))
        return
    context.user_data["uw_waiting_bal_password"] = True
    await update.message.reply_text(ltext(lang, "🔐 Enter your password:\n\n⚠️ Your message will be deleted after you send it.", "🔐 আপনার Password দিন:\n\n⚠️ Message পাঠানোর পর মুছে যাবে।"))


async def send_wallet_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    lang = user_lang(user_id)
    row = get_user_wallet(user_id)
    if not row:
        await update.message.reply_text(ltext(lang, "❌ No wallet is set up.\n\nStart with: /setup", "❌ Wallet setup নেই!\n\nপ্রথমে: /setup"))
        return ConversationHandler.END
    network = row[2]
    net_info = NETWORKS.get(network, {"name": network})
    await update.message.reply_text(ltext(lang, f"💸 Send Crypto\n\n🌐 {net_info['name']}\n👛 {row[3]}\n\nEnter the destination wallet address:\n\n📋 Example: {wallet_hint(network)}", f"💸 Crypto পাঠানো\n\n🌐 {net_info['name']}\n👛 {row[3]}\n\nDestination wallet address দিন:\n\n📋 উদাহরণ: {wallet_hint(network)}"))
    return SEND_W_DEST


async def send_wallet_dest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dest = update.message.text.strip()
    user_id = str(update.effective_user.id)
    lang = user_lang(user_id)
    row = get_user_wallet(user_id)
    network = row[2]
    if not valid_wallet(network, dest):
        net_info = NETWORKS.get(network, {"name": network})
        await update.message.reply_text(ltext(lang, f"❌ Invalid {net_info['name']} address.\n\nEnter it again:", f"❌ ভুল {net_info['name']} address!\n\nআবার দিন:"))
        return SEND_W_DEST
    context.user_data["sw_dest"] = dest
    net_info = NETWORKS.get(network, {"symbol": "?"})
    await update.message.reply_text(ltext(lang, f"✅ Destination: {dest}\n\nHow much {net_info['symbol']} do you want to send?\n\nNumbers only (example: 10.5)", f"✅ Destination: {dest}\n\nকত {net_info['symbol']} পাঠাবেন?\n\nশুধু সংখ্যা (যেমন: 10.5)"))
    return SEND_W_AMOUNT


async def send_wallet_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = user_lang(update.effective_user.id)
    try:
        amount = float(update.message.text.strip())
        if amount <= 0:
            raise ValueError
    except Exception:
        await update.message.reply_text(ltext(lang, "❌ Invalid amount. Enter a number:", "❌ ভুল পরিমাণ! সংখ্যা লিখুন:"))
        return SEND_W_AMOUNT
    user_id = str(update.effective_user.id)
    row = get_user_wallet(user_id)
    network = row[2]
    net_info = NETWORKS.get(network, {"name": network, "symbol": "?"})
    dest = context.user_data.get("sw_dest")
    context.user_data["sw_amount"] = amount
    keyboard = [[InlineKeyboardButton(tr("confirm", lang), callback_data="sw_confirm"), InlineKeyboardButton(tr("cancel", lang), callback_data="sw_cancel")]]
    await update.message.reply_text(ltext(lang, f"📊 Transaction Summary:\n\n🌐 {net_info['name']}\n💵 {amount} {net_info['symbol']}\n👛 Sender: {row[3]}\n📤 Recipient: {dest}\n\n⚠️ Transactions are irreversible. Confirm to continue:", f"📊 Transaction সারসংক্ষেপ:\n\n🌐 {net_info['name']}\n💵 {amount} {net_info['symbol']}\n👛 প্রেরক: {row[3]}\n📤 প্রাপক: {dest}\n\n⚠️ Transaction irreversible!\nনিশ্চিত করুন:"), reply_markup=InlineKeyboardMarkup(keyboard))
    return SEND_W_PASSWORD


async def send_wallet_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    password = update.message.text.strip()
    user_id = str(update.effective_user.id)
    try:
        await update.message.delete()
    except Exception:
        pass
    dest = context.user_data.get("sw_dest")
    amount = context.user_data.get("sw_amount")
    row = get_user_wallet(user_id)
    network = row[2]
    net_info = NETWORKS.get(network, {"name": network, "symbol": "?", "explorer": ""})
    lang = user_lang(user_id)
    await update.message.reply_text(ltext(lang, "⏳ Sending...", "⏳ পাঠানো হচ্ছে..."))
    try:
        sig = await asyncio.get_running_loop().run_in_executor(None, lambda: send_from_user_wallet(user_id, password, dest, amount))
        save_transaction(f"WALLET-{sig[:24]}", user_id, 0, amount, dest, sig, "completed", network, source="wallet")
        record_referral_reward_for_transaction(user_id, "wallet", f"WALLET-{sig[:24]}", network, amount, 0, "user_wallet_transfer")
        context.user_data.clear()
        await update.message.reply_text(ltext(lang, f"🎉 Sent successfully!\n\n🌐 {net_info['name']}\n💵 {amount} {net_info['symbol']}\n📤 {dest}\n🔗 {net_info['explorer']}{sig}", f"🎉 সফলভাবে পাঠানো হয়েছে!\n\n🌐 {net_info['name']}\n💵 {amount} {net_info['symbol']}\n📤 {dest}\n🔗 {net_info['explorer']}{sig}"))
    except Exception as exc:
        context.user_data.clear()
        reason = failure_reason_text(exc, network, lang)
        await update.message.reply_text(ltext(lang, "❌ Wrong password!", "❌ ভুল Password!") if "ভুল password" in str(exc) or "wrong_password" in str(exc).lower() else ltext(lang, f"❌ Send failed!\n\n{exc}\n\n💡 {reason}\n\n📞 @{SUPPORT_USERNAME.lstrip('@')}", f"❌ পাঠাতে ব্যর্থ!\n\n{exc}\n\n💡 {reason}\n\n📞 @{SUPPORT_USERNAME.lstrip('@')}"))
    return ConversationHandler.END


async def precheckout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.pre_checkout_query
    order = get_star_order(query.invoice_payload)
    if not order:
        seller_order = get_seller_order(query.invoice_payload)
        if seller_order:
            order_id, _seller_id, buyer_id, _buyer_username, method, _trx_id, network, _wallet, _amount_bdt, amount_crypto, stars_amount, status, *_rest = seller_order
            if method != "stars" or status != "waiting_payment":
                await query.answer(ok=False, error_message="This seller order is not payable by Stars.")
                return
            if str(query.from_user.id) != str(buyer_id):
                await query.answer(ok=False, error_message="This invoice belongs to another user.")
                return
            if query.currency != "XTR" or int(query.total_amount) != int(stars_amount):
                await query.answer(ok=False, error_message="Payment amount mismatch.")
                return
            await query.answer(ok=True)
            return
        await query.answer(ok=False, error_message="Order expired. Please create a new order.")
        return
    order_id, user_id, _username, network, _wallet, amount_crypto, stars_amount, status, *_rest = order
    if status != "pending":
        await query.answer(ok=False, error_message="This order was already processed.")
        return
    if str(query.from_user.id) != str(user_id):
        await query.answer(ok=False, error_message="This invoice belongs to another user.")
        return
    if query.currency != "XTR" or int(query.total_amount) != int(stars_amount):
        await query.answer(ok=False, error_message="Payment amount mismatch.")
        return
    sufficient, current_bal = check_sufficient(network, amount_crypto, exclude_order_id=order_id)
    if not sufficient and current_bal is not None:
        await query.answer(ok=False, error_message=f"Seller stock is low after reserves: {current_bal} available, {amount_crypto} needed.")
        return
    await query.answer(ok=True)


async def successful_seller_star_payment(update: Update, context: ContextTypes.DEFAULT_TYPE, order, payment):
    order_id, seller_id, buyer_id, buyer_username, method, _trx_id, network, wallet, amount_bdt, amount_crypto, stars_amount, status, *_ = order
    if status == "completed":
        await update.message.reply_text("✅ This seller Stars order is already completed.")
        return
    if method != "stars" or str(update.effective_user.id) != str(buyer_id) or int(payment.total_amount) != int(stars_amount):
        update_seller_order(order_id, status="failed", error="stars payment verification mismatch")
        await update.message.reply_text("❌ Seller Stars payment verification mismatch. Contact admin.")
        return
    update_seller_order(order_id, status="paid")
    lang = user_lang(buyer_id)
    await update.message.reply_text(ltext(lang, "✅ Stars payment received. Seller crypto delivery is in progress...", "✅ Stars payment received. Seller crypto delivery চলছে..."), reply_markup=track_order_keyboard(order_id, buyer_id, lang))
    ok, result = await complete_seller_order(update.get_bot(), order_id, "seller_stars")
    if ok:
        await update.message.reply_text(f"🎉 Seller Stars order completed.\n🧾 {order_id}\n⭐ {stars_amount} Stars\nSeller payout ledger created for admin manual payout.")
    else:
        lang = user_lang(buyer_id)
        reason = failure_reason_text(result, network, lang)
        await update.message.reply_text(
            f"✅ Stars payment received, but seller crypto delivery failed and needs manual review.\n🧾 {order_id}\n💡 {reason}"
            if lang == "en"
            else f"✅ Stars payment received, কিন্তু seller crypto delivery failed/manual review দরকার।\n🧾 {order_id}\n💡 {reason}",
            reply_markup=track_order_keyboard(order_id, buyer_id, lang),
        )
        try:
            await update.get_bot().send_message(ADMIN_ID, f"🚨 Seller Stars delivery failed.\nOrder: {order_id}\nSeller: {seller_id}\nBuyer: {buyer_id}\nReason: {result}\nLikely: {failure_reason_text(result, network, 'en')}")
        except Exception:
            pass


async def successful_star_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    payment = update.message.successful_payment
    if payment.currency != "XTR":
        return
    order = get_star_order(payment.invoice_payload)
    if not order:
        seller_order = get_seller_order(payment.invoice_payload)
        if seller_order:
            await successful_seller_star_payment(update, context, seller_order, payment)
            return
        await update.message.reply_text("❌ Order not found. Contact admin with your payment receipt.")
        try:
            await update.get_bot().send_message(ADMIN_ID, f"🚨 Stars payment received but order was not found.\nPayload: {payment.invoice_payload}\nCharge: {payment.telegram_payment_charge_id}")
        except Exception:
            pass
        return

    order_id, user_id, username, network, wallet, amount_crypto, stars_amount, status, *_rest = order
    lang = user_lang(user_id)
    net_info = NETWORKS.get(network, {"name": network, "symbol": "?", "explorer": ""})

    if status == "completed":
        await update.message.reply_text("✅ This Stars order is already completed.")
        return
    if str(update.effective_user.id) != str(user_id) or int(payment.total_amount) != int(stars_amount):
        update_star_order_status(order_id, "failed", payment.telegram_payment_charge_id, payment.provider_payment_charge_id, error="payment verification mismatch")
        release_stock_reservation(order_id=order_id, reason="stars_payment_mismatch", actor_id="system")
        add_audit("system", "stars_payment_mismatch", "star_order", order_id)
        await update.message.reply_text("❌ Payment verification mismatch. Contact admin.")
        return

    update_star_order_status(order_id, "paid", payment.telegram_payment_charge_id, payment.provider_payment_charge_id)
    await update.message.reply_text(tr("stars_paid_sending", lang))

    try:
        sig = await send_crypto(network, wallet, amount_crypto)
        update_star_order_status(order_id, "completed", payment.telegram_payment_charge_id, payment.provider_payment_charge_id, sig)
        save_transaction(f"STAR-{payment.telegram_payment_charge_id}", user_id, 0, amount_crypto, wallet, sig, "completed", network, order_id=order_id, source="stars")
        record_referral_reward_for_transaction(user_id, "stars", f"STAR-{payment.telegram_payment_charge_id}", network, amount_crypto, 0, f"order={order_id}")
        consume_stock_reservation(order_id=order_id)
        receipt_data = await make_receipt_data(update.get_bot(), order_id, f"STAR-{payment.telegram_payment_charge_id}", network, amount_crypto, wallet, sig, user_id, buyer_username=username, seller_id=ADMIN_ID, stars_amount=stars_amount, title="Smart Crypto Buy")
        await send_transaction_receipt(update.get_bot(), [user_id, ADMIN_ID], receipt_data)
    except Exception as exc:
        update_star_order_status(order_id, "failed", payment.telegram_payment_charge_id, payment.provider_payment_charge_id, error=str(exc))
        save_transaction(f"STAR-{payment.telegram_payment_charge_id}", user_id, 0, amount_crypto, wallet, "", "failed", network, order_id=order_id, source="stars")
        release_stock_reservation(order_id=order_id, reason="stars_send_failed", actor_id="system")
        add_audit("system", "stars_send_failed", "star_order", order_id, str(exc))
        reason = failure_reason_text(exc, network, lang)
        await update.message.reply_text(
            f"✅ Stars payment received, but crypto sending failed. Admin has been notified.\n\n💡 {reason}"
            if lang == "en"
            else f"✅ Stars payment received, কিন্তু crypto পাঠাতে সমস্যা হয়েছে। Admin-কে জানানো হয়েছে।\n\n💡 {reason}",
            reply_markup=track_order_keyboard(order_id, user_id, lang),
        )
        try:
            await update.get_bot().send_message(
                ADMIN_ID,
                f"🚨 Stars payment received but crypto send failed.\n\n"
                f"👤 @{username} ({user_id})\n"
                f"🧾 Order: {order_id}\n"
                f"⭐ Charge: {payment.telegram_payment_charge_id}\n"
                f"🌐 {net_info['name']}\n"
                f"💵 {amount_crypto} {net_info['symbol']}\n"
                f"👛 {wallet}\n"
                f"❌ {exc}\n"
                f"💡 {failure_reason_text(exc, network, 'en')}",
            )
        except Exception:
            pass
        logger.error("Stars order send failed: %s", exc)


async def deletekey_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    lang = user_lang(user_id)
    if not get_user_wallet(user_id):
        await update.message.reply_text(ltext(lang, "❌ No wallet found.", "❌ কোনো wallet নেই!"))
        return ConversationHandler.END
    keyboard = [[InlineKeyboardButton(ltext(lang, "✅ Yes, delete it", "✅ হ্যাঁ, মুছে দাও"), callback_data="del_confirm"), InlineKeyboardButton(ltext(lang, "❌ No", "❌ না"), callback_data="del_cancel")]]
    await update.message.reply_text(ltext(lang, "⚠️ Warning!\n\nYour wallet key will be deleted. This cannot be undone.\n\nAre you sure?", "⚠️ সতর্কতা!\n\nWallet key মুছে দেওয়া হবে।\nUndo করা যাবে না!\n\nনিশ্চিত?"), reply_markup=InlineKeyboardMarkup(keyboard))
    return DEL_PASSWORD


async def deletekey_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    password = update.message.text.strip()
    user_id = str(update.effective_user.id)
    lang = user_lang(user_id)
    try:
        await update.message.delete()
    except Exception:
        pass
    _bal, _network, error = get_user_balance(user_id, password)
    if error == "wrong_password":
        await update.message.reply_text(ltext(lang, "❌ Wrong password. Key was not deleted.", "❌ ভুল Password! Key মুছা হয়নি।"))
        return ConversationHandler.END
    delete_user_wallet(user_id)
    await update.message.reply_text(ltext(lang, "✅ Wallet key deleted.\n\nSet up a new wallet: /setup", "✅ Wallet key মুছে দেওয়া হয়েছে!\n\nনতুন setup: /setup"))
    return ConversationHandler.END


async def guide_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(GUIDE)


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(command_help_text(update.effective_user.id))


async def changekey_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = user_lang(update.effective_user.id)
    delete_user_wallet(str(update.effective_user.id))
    await update.message.reply_text(ltext(lang, "🔄 Old key deleted.\n\nSet up a new wallet:", "🔄 পুরনো key মুছে দেওয়া হয়েছে!\n\nনতুন wallet setup করুন:"))
    return await setup_cmd(update, context)


def short_bkash_notice_text(text):
    value = " ".join(str(text or "").split())
    if not value:
        return "N/A"
    return value[:700] + ("..." if len(value) > 700 else "")


async def notify_admin_parsed_bkash(app, parsed, sender, text, scope="main", seller_id=None):
    if not ADMIN_ID:
        return
    try:
        seller_line = f"\n🏪 Seller: {seller_id}" if seller_id else ""
        await app.bot.send_message(
            ADMIN_ID,
            "📲 bKash notice parsed by app/webhook\n\n"
            f"📩 Source: {sender}\n"
            f"🔎 Scope: {scope}{seller_line}\n"
            f"💵 Amount: {parsed['amount_bdt']} BDT\n"
            f"🔑 TrxID: {parsed['trx_id']}\n"
            f"📝 Message: {short_bkash_notice_text(text)}",
        )
    except Exception as exc:
        logger.error(exc)


async def process_bkash(app, text, sender, meta=None):
    parsed = parse_bkash_payment_notice(text)
    if not parsed:
        return {"payment_status": "ignored", "message": "Notice was not a supported bKash payment."}
    if meta and meta.get("seller_token"):
        return await process_seller_bkash(app, text, sender, meta)
    trx_id = parsed["trx_id"]
    amount_bdt = parsed["amount_bdt"]
    touch_webhook_notice(sender, trx_id, amount_bdt)
    if not (meta or {}).get("admin_parse_alert_sent"):
        await notify_admin_parsed_bkash(app, parsed, sender, text)

    if trx_exists(trx_id):
        logger.info("Duplicate bKash notice ignored because transaction already exists: %s", trx_id)
        return {"payment_status": "duplicate", "duplicate": True, "trx_id": trx_id, "amount_bdt": amount_bdt, "message": "Transaction already exists; duplicate notice ignored."}

    already_saved = sms_exists(trx_id)
    saved_new = save_sms(trx_id, amount_bdt, sender, text)
    logger.info("bKash notice saved: %s BDT | TrxID: %s | source: %s | new: %s", amount_bdt, trx_id, sender, saved_new)

    pending = get_pending_order(trx_id)
    if pending:
        if trx_id.startswith("TEST") or str(sender).startswith("test"):
            await app.bot.send_message(ADMIN_ID, f"🧪 Test bKash notice matched pending order but auto-send was blocked.\n\nTrxID: {trx_id}\nAmount: {amount_bdt} BDT\nUse manual approve only if this is intentional.")
            order_id = pending[7] if len(pending) > 7 else None
            return {"payment_status": "manual_review", "manual_review": True, "matched_order": True, "order_id": order_id, "trx_id": trx_id, "amount_bdt": amount_bdt, "message": "Payment matched an order, but test notices require manual review."}
        return await complete_pending_order_from_sms(app, pending, amount_bdt)

    if already_saved:
        logger.info("Duplicate bKash notice ignored because TrxID was already saved: %s", trx_id)
        return {"payment_status": "duplicate", "duplicate": True, "trx_id": trx_id, "amount_bdt": amount_bdt, "message": "SMS notice already exists; duplicate ignored."}

    return {"payment_status": "parsed", "trx_id": trx_id, "amount_bdt": amount_bdt, "message": "Payment parsed, but no pending order matched yet."}


async def complete_pending_order_from_sms(app, pending, sms_amount_bdt):
    trx_id, user_id, expected_bdt, expected_crypto, wallet, network, _created_at = pending[:7]
    order_id = pending[7] if len(pending) > 7 else None
    net_info = NETWORKS.get(network, {"name": network, "symbol": "?", "explorer": ""})

    if expected_bdt and abs(float(sms_amount_bdt) - float(expected_bdt)) > 0.01:
        keyboard = [[
            InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user_id}_{trx_id}_{network}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user_id}_{trx_id}"),
        ]]
        await app.bot.send_message(
            ADMIN_ID,
            "⚠️ bKash SMS matched a pending order, but amount is different.\n\n"
            f"🔑 TrxID: {trx_id}\n"
            f"👤 User: {user_id}\n"
            f"🌐 {net_info['name']}\n"
            f"🧾 Expected: {expected_bdt} BDT\n"
            f"📩 SMS Received: {sms_amount_bdt} BDT\n\n"
            "Please verify manually.",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return {"payment_status": "manual_review", "manual_review": True, "matched_order": True, "order_id": order_id, "trx_id": trx_id, "amount_bdt": sms_amount_bdt, "message": "Payment matched an order, but amount differs and needs manual review."}

    crypto_amount = expected_crypto or round(float(sms_amount_bdt) / get_rate(network), 6)
    sufficient, current_bal = check_sufficient(network, crypto_amount, exclude_order_id=order_id, exclude_trx_id=trx_id)
    if not sufficient and current_bal is not None:
        await app.bot.send_message(
            ADMIN_ID,
            f"❌ Payment verified but insufficient {net_info['symbol']}.\n\n"
            f"🔑 TrxID: {trx_id}\n"
            f"👤 User: {user_id}\n"
            f"💵 Need: {crypto_amount}\n"
            f"💰 Available: {current_bal}",
        )
        return {"payment_status": "manual_review", "manual_review": True, "matched_order": True, "order_id": order_id, "trx_id": trx_id, "amount_bdt": sms_amount_bdt, "message": "Payment matched an order, but stock is insufficient and needs manual review."}

    try:
        sig = await send_crypto(network, wallet, crypto_amount)
        mark_sms_used(trx_id)
        order_id = save_transaction(trx_id, user_id, sms_amount_bdt, crypto_amount, wallet, sig, "completed", network, order_id=order_id, source="bkash")
        record_referral_reward_for_transaction(user_id, "bkash", trx_id, network, crypto_amount, sms_amount_bdt, f"order={order_id}")
        consume_stock_reservation(order_id=order_id, trx_id=trx_id)
        delete_pending_order(trx_id)
        receipt_data = await make_receipt_data(app.bot, order_id, trx_id, network, crypto_amount, wallet, sig, user_id, bdt_amount=sms_amount_bdt, title="Smart Crypto Buy")
        await send_transaction_receipt(app.bot, [user_id, ADMIN_ID], receipt_data)
        return {"payment_status": "matched_order", "matched_order": True, "order_id": order_id, "trx_id": trx_id, "amount_bdt": sms_amount_bdt, "tx_sig": sig, "message": "Payment matched an order and crypto delivery completed."}
    except Exception as exc:
        save_transaction(trx_id, user_id, sms_amount_bdt, crypto_amount, wallet, "", "failed", network, order_id=order_id, source="bkash")
        release_stock_reservation(order_id=order_id, trx_id=trx_id, reason="auto_complete_send_failed", actor_id="system")
        add_audit("system", "auto_complete_send_failed", "transaction", trx_id, str(exc))
        reason = failure_reason_text(exc, network, "en")
        await app.bot.send_message(
            ADMIN_ID,
            f"🚨 Auto-complete failed after bKash SMS verification.\n\n"
            f"👤 User: {user_id}\n🔑 TrxID: {trx_id}\n🌐 {net_info['name']}\n❌ {exc}\n💡 {reason}",
        )
        try:
            target_lang = user_lang(user_id)
            await app.bot.send_message(
                int(user_id),
                f"✅ Payment verified, but crypto delivery failed. Admin has been notified.\n\n🧾 Order: {order_id or 'N/A'}\n🔑 TrxID: {trx_id}\n💡 {failure_reason_text(exc, network, target_lang)}\n📞 @{SUPPORT_USERNAME.lstrip('@')}"
                if target_lang == "en"
                else f"✅ Payment verified, কিন্তু crypto পাঠাতে সমস্যা হয়েছে। Admin-কে জানানো হয়েছে।\n\n🧾 Order: {order_id or 'N/A'}\n🔑 TrxID: {trx_id}\n💡 {failure_reason_text(exc, network, target_lang)}\n📞 @{SUPPORT_USERNAME.lstrip('@')}",
                reply_markup=track_order_keyboard(order_id or trx_id, user_id, target_lang),
            )
        except Exception:
            pass
        logger.error("Auto-complete pending order failed: %s", exc)
        return {"payment_status": "manual_review", "manual_review": True, "matched_order": True, "order_id": order_id, "trx_id": trx_id, "amount_bdt": sms_amount_bdt, "message": "Payment matched an order, but auto delivery failed and needs manual review.", "error": str(exc)}


def sms_handler(app, loop, text, sender, meta=None):
    return asyncio.run_coroutine_threadsafe(process_bkash(app, text, sender, meta), loop)


async def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is not configured")

    request = HTTPXRequest(connection_pool_size=8, read_timeout=60, write_timeout=60, connect_timeout=60, pool_timeout=60)
    app = Application.builder().token(BOT_TOKEN).request(request).concurrent_updates(ChatScopedUpdateProcessor(8)).build()

    buy_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_handler, pattern="^network_(solana|polygon|bsc|avalanche|ethereum|ethereum_usdc|base|trc20|ton)$")],
        states={WAITING_WALLET: [MessageHandler(filters.TEXT & ~filters.COMMAND, waiting_wallet)], WAITING_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, waiting_amount)]},
        fallbacks=[CommandHandler("start", start), CallbackQueryHandler(button_handler, pattern="^cancel$")],
    )
    star_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_handler, pattern="^star_network_(solana|polygon|bsc|avalanche|ethereum|ethereum_usdc|base|trc20|ton)$")],
        states={
            WAITING_STAR_WALLET: [MessageHandler(filters.TEXT & ~filters.COMMAND, waiting_star_wallet)],
            WAITING_STAR_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, waiting_star_amount)],
        },
        fallbacks=[CommandHandler("start", start), CallbackQueryHandler(button_handler, pattern="^cancel$")],
    )
    admin_send_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_handler, pattern="^admin_send_network_(solana|polygon|bsc|avalanche|ethereum|ethereum_usdc|base|trc20|ton)$")],
        states={
            ADMIN_SEND_WALLET: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_send_wallet_received)],
            ADMIN_SEND_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_send_amount_received)],
        },
        fallbacks=[CommandHandler("start", start), CallbackQueryHandler(button_handler, pattern="^admin_send_cancel$")],
    )
    rate_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_handler, pattern="^setrate_(solana|polygon|bsc|avalanche|ethereum|ethereum_usdc|base|trc20|ton)$")],
        states={WAITING_RATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, waiting_rate)]},
        fallbacks=[CommandHandler("start", start), CallbackQueryHandler(button_handler, pattern="^back$")],
    )
    setup_conv = ConversationHandler(
        entry_points=[CommandHandler("setup", setup_cmd), CommandHandler("changekey", changekey_cmd), CallbackQueryHandler(button_handler, pattern="^mw_(setup|change)$")],
        states={SETUP_NETWORK: [CallbackQueryHandler(setup_network_selected, pattern="^uw_")], SETUP_KEY: [MessageHandler(filters.TEXT & ~filters.COMMAND, setup_key_received)], SETUP_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, setup_password_received)]},
        fallbacks=[CommandHandler("start", start)],
    )
    send_wallet_conv = ConversationHandler(
        entry_points=[CommandHandler("send_wallet", send_wallet_cmd), CallbackQueryHandler(button_handler, pattern="^mw_send$")],
        states={SEND_W_DEST: [MessageHandler(filters.TEXT & ~filters.COMMAND, send_wallet_dest)], SEND_W_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, send_wallet_amount)], SEND_W_PASSWORD: [CallbackQueryHandler(button_handler, pattern="^sw_(confirm|cancel)$"), MessageHandler(filters.TEXT & ~filters.COMMAND, send_wallet_password)]},
        fallbacks=[CommandHandler("start", start)],
    )
    delete_conv = ConversationHandler(
        entry_points=[CommandHandler("deletekey", deletekey_cmd), CallbackQueryHandler(button_handler, pattern="^del_confirm$")],
        states={DEL_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, deletekey_password)]},
        fallbacks=[CallbackQueryHandler(button_handler, pattern="^del_cancel$"), CommandHandler("start", start)],
    )
    seller_app_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_handler, pattern="^seller_apply$")],
        states={
            SELLER_APP_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, seller_apply_name_received)],
            SELLER_APP_BKASH: [MessageHandler(filters.TEXT & ~filters.COMMAND, seller_apply_bkash_received)],
            SELLER_APP_SUPPORT: [MessageHandler(filters.TEXT & ~filters.COMMAND, seller_apply_support_received)],
        },
        fallbacks=[CallbackQueryHandler(button_handler, pattern="^cancel$"), CommandHandler("start", start)],
    )
    seller_wallet_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_handler, pattern="^sellerwallet_(solana|polygon|bsc|avalanche|ethereum|ethereum_usdc|base|trc20)$")],
        states={SELLER_SETUP_KEY: [MessageHandler(filters.TEXT & ~filters.COMMAND, seller_wallet_key_received)], SELLER_SET_RATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, seller_rate_received)]},
        fallbacks=[CallbackQueryHandler(button_handler, pattern="^cancel$"), CommandHandler("start", start)],
    )
    seller_rate_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_handler, pattern="^sellerrate_(solana|polygon|bsc|avalanche|ethereum|ethereum_usdc|base|trc20)$")],
        states={SELLER_SET_RATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, seller_rate_received)]},
        fallbacks=[CallbackQueryHandler(button_handler, pattern="^cancel$"), CommandHandler("start", start)],
    )
    seller_buy_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_handler, pattern="^sellerbuy_(solana|polygon|bsc|avalanche|ethereum|ethereum_usdc|base|trc20)$")],
        states={SELLER_BUY_WALLET: [MessageHandler(filters.TEXT & ~filters.COMMAND, seller_buy_wallet_received)], SELLER_BUY_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, seller_buy_amount_received)]},
        fallbacks=[CallbackQueryHandler(button_handler, pattern="^cancel$"), CommandHandler("start", start)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("send", send_cmd))
    app.add_handler(CommandHandler("gencode", gencode_cmd))
    app.add_handler(CommandHandler("giveaway", giveaway_cmd))
    app.add_handler(CommandHandler("pending", pending_cmd))
    app.add_handler(CommandHandler("failed", failed_cmd))
    app.add_handler(CommandHandler("stats", stats_cmd))
    app.add_handler(CommandHandler("users", users_cmd))
    app.add_handler(CommandHandler("balances", balances_cmd))
    app.add_handler(CommandHandler("maintenance", maintenance_cmd))
    app.add_handler(CommandHandler("terms", terms_cmd))
    app.add_handler(CommandHandler("backup", backup_cmd))
    app.add_handler(CommandHandler("restart_help", restart_help_cmd))
    app.add_handler(CommandHandler("bot_health", bot_health_cmd))
    app.add_handler(CommandHandler("txlog", txlog_cmd))
    app.add_handler(CommandHandler("order", order_cmd))
    app.add_handler(CommandHandler("status", status_cmd))
    app.add_handler(CommandHandler("receipt", receipt_cmd))
    app.add_handler(CommandHandler("seller", seller_cmd))
    app.add_handler(CommandHandler("seller_center", seller_center_cmd))
    app.add_handler(CommandHandler("seller_guide", seller_guide_cmd))
    app.add_handler(CommandHandler("seller_badge", seller_badge_cmd))
    app.add_handler(CommandHandler("seller_dashboard", seller_dashboard_cmd))
    app.add_handler(CommandHandler("referral", referral_cmd))
    app.add_handler(CommandHandler("report", report_cmd))
    app.add_handler(CommandHandler("profit", profit_cmd))
    app.add_handler(CommandHandler("costrate", costrate_cmd))
    app.add_handler(CommandHandler("gas", gas_cmd))
    app.add_handler(CommandHandler("reservations", reservations_cmd))
    app.add_handler(CommandHandler("audit", audit_cmd))
    app.add_handler(CommandHandler("payout", payout_cmd))
    app.add_handler(CommandHandler("payouts", payouts_cmd))
    app.add_handler(CommandHandler("webhook_health", webhook_health_cmd))
    app.add_handler(CommandHandler("test_sms", test_sms_cmd))
    app.add_handler(CommandHandler("test_seller_sms", test_seller_sms_cmd))
    app.add_handler(CommandHandler("aiadmin", aiadmin_cmd))
    app.add_handler(CommandHandler("ai_usage", ai_usage_cmd))
    app.add_handler(CommandHandler("mybalance", mybalance_cmd))
    app.add_handler(CommandHandler("guide", guide_cmd))
    app.add_handler(CommandHandler("ai", ai_cmd))
    app.add_handler(CommandHandler("swap", swap_cmd))
    app.add_handler(buy_conv)
    app.add_handler(star_conv)
    app.add_handler(admin_send_conv)
    app.add_handler(rate_conv)
    app.add_handler(setup_conv)
    app.add_handler(send_wallet_conv)
    app.add_handler(delete_conv)
    app.add_handler(seller_app_conv)
    app.add_handler(seller_wallet_conv)
    app.add_handler(seller_rate_conv)
    app.add_handler(seller_buy_conv)
    app.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_star_payment))
    app.add_handler(CallbackQueryHandler(button_handler))
    free_forward_media_filter = filters.PHOTO | filters.VIDEO | filters.Document.ALL | filters.AUDIO | filters.VOICE | filters.ANIMATION | filters.Sticker.ALL
    app.add_handler(MessageHandler(free_forward_media_filter & ~filters.COMMAND, free_forward_media_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, waiting_trxid))
    app.add_handler(CommandHandler("cancel", cancel_cmd), group=1)

    await app.initialize()
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True)

    loop = asyncio.get_running_loop()
    set_personal_auth_runtime(loop, app)
    set_callback(lambda txt, sndr, meta=None: sms_handler(app, loop, txt, sndr, meta))
    threading.Thread(target=run_webhook, daemon=True).start()
    asyncio.create_task(daily_admin_jobs(app))
    logger.info("Bot started!")

    try:
        await asyncio.Event().wait()
    finally:
        await app.updater.stop()
        await app.stop()
        await app.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
