import asyncio
import json
import logging
import math
import os
import secrets
import string
import threading
from datetime import datetime, timedelta

import requests
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    PreCheckoutQueryHandler,
    filters,
)
from telegram.request import HTTPXRequest

from balance import GAS_META, check_gas_sufficient, check_sufficient, get_all_balances, get_native_gas_balances
from bsc_sender import send_bsc_usdt
from config import ADMIN_ID, BKASH_NUMBER, BOT_TOKEN, RATE, STAR_RATE, SUPPORT_USERNAME, AI_PROVIDER_ORDER, GEMINI_API_KEY, GEMINI_MODEL, GROQ_API_KEY, GROQ_MODEL, OPENROUTER_API_KEY, OPENROUTER_MODEL, LOW_BALANCE_THRESHOLD, WEBHOOK_STALE_MINUTES, BACKUP_UPLOAD_URL, SELLER_WALLET_MASTER_KEY
from crypto_manager import (
    delete_user_wallet,
    encrypt_key,
    encrypt_seller_key,
    get_user_balance,
    get_user_wallet,
    get_wallet_address,
    save_user_wallet,
    send_from_seller_wallet,
    send_from_user_wallet,
)
from db import (
    create_code,
    add_audit,
    bind_stock_reservation_trx,
    consume_stock_reservation,
    create_stock_reservation,
    delete_pending_order,
    disable_code,
    get_all_active_codes,
    get_code,
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
    save_wallet,
    set_user_language,
    set_network_rate,
    set_cost_rate,
    set_setting,
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
    create_or_update_seller_application,
    create_seller_order,
    create_seller_star_ledger,
    disable_seller,
    disable_seller_wallet,
    find_waiting_seller_order_by_trx,
    get_seller,
    get_seller_by_sms_token,
    get_seller_order,
    get_seller_order_by_trx,
    get_seller_payment_notice,
    get_seller_rate,
    list_approved_sellers,
    list_enabled_seller_wallets,
    list_pending_seller_orders,
    list_pending_seller_payouts,
    list_seller_rates,
    list_seller_star_ledger,
    list_seller_wallets,
    list_sellers_by_status,
    mark_seller_payment_notice_used,
    mark_seller_payout_status,
    reject_seller,
    save_seller_payment_notice,
    save_seller_wallet,
    set_seller_rate,
    update_seller_order,
)
from evm_sender import send_evm_token
from polygon_sender import send_polygon_usdc
from sender import send_usdc
from ton_sender import send_ton
from tron_sender import send_trc20_usdt
from user_guide import GUIDE, NETWORK_GUIDE
from webhook import parse_bkash_payment_notice, parse_bkash_sms, run_webhook, set_callback

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

RATE_FILE = "rate.json"
DIVIDER = "━━━━━━━━━━━━━━━━━━━━"

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
    "gift": {"bn": "🎁 গিফট কোড", "en": "🎁 Gift Code"},
    "stars": {"bn": "⭐ Telegram Stars", "en": "⭐ Telegram Stars"},
    "rate": {"bn": "📊 রেট", "en": "📊 Rates"},
    "balance": {"bn": "💰 ব্যালেন্স", "en": "💰 Balance"},
    "txlog": {"bn": "📜 TX লগ", "en": "📜 TX Log"},
    "help": {"bn": "❓ সাহায্য", "en": "❓ Help"},
    "support": {"bn": "📞 Support", "en": "📞 Support"},
    "ai_support": {"bn": "🤖 AI Support", "en": "🤖 AI Support"},
    "sellers": {"bn": "🛍️ Sellers", "en": "🛍️ Sellers"},
    "seller_center": {"bn": "🏪 Seller Center", "en": "🏪 Seller Center"},
    "order_status": {"bn": "🔎 Order Status", "en": "🔎 Order Status"},
    "seller_dashboard": {"bn": "🏪 Seller Dashboard", "en": "🏪 Seller Dashboard"},
    "terms": {"bn": "📜 Terms", "en": "📜 Terms"},
    "wallet": {"bn": "🔐 আমার Wallet", "en": "🔐 My Wallet"},
    "language": {"bn": "🌐 ভাষা", "en": "🌐 Language"},
    "set_rate": {"bn": "⚙️ রেট পরিবর্তন", "en": "⚙️ Set Rates"},
    "gen_code": {"bn": "🎟️ কোড তৈরি", "en": "🎟️ Generate Code"},
    "disable_code": {"bn": "🚫 কোড বাতিল", "en": "🚫 Disable Code"},
    "admin_send": {"bn": "🚀 Admin Send", "en": "🚀 Admin Send"},
    "back": {"bn": "🔙 ফিরে যান", "en": "🔙 Back"},
    "cancel": {"bn": "❌ বাতিল", "en": "❌ Cancel"},
    "home_title": {"bn": "💱 Crypto Seller Bot", "en": "💱 Crypto Seller Bot"},
    "welcome": {"bn": "স্বাগতম", "en": "Welcome"},
    "current_rates": {"bn": "বর্তমান রেট", "en": "Current Rates"},
    "select_action": {"bn": "নিচের মেনু থেকে শুরু করুন 👇", "en": "Choose an option below 👇"},
    "select_network": {"bn": "💱 নেটওয়ার্ক বেছে নিন", "en": "💱 Select a network"},
    "enter_wallet": {"bn": "আপনার {network} Wallet Address দিন", "en": "Send your {network} wallet address"},
    "example": {"bn": "উদাহরণ", "en": "Example"},
    "wallet_saved": {"bn": "✅ Wallet সংরক্ষিত!", "en": "✅ Wallet saved!"},
    "enter_amount_bdt": {"bn": "কত টাকার {symbol} কিনতে চান?", "en": "How many BDT of {symbol} do you want to buy?"},
    "numbers_only": {"bn": "শুধু সংখ্যা লিখুন (যেমন: 500)", "en": "Send numbers only (example: 500)"},
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
    "admin_send_amount": {"bn": "কত {symbol} পাঠাবেন?", "en": "How many {symbol} do you want to send?"},
    "admin_send_confirm": {"bn": "নিশ্চিত করলে asset পাঠানো হবে।", "en": "Confirm to send the asset."},
    "admin_send_done": {"bn": "✅ Admin transfer complete!", "en": "✅ Admin transfer complete!"},
    "maintenance_on": {"bn": "🛑 Maintenance mode ON", "en": "🛑 Maintenance mode ON"},
    "maintenance_off": {"bn": "✅ Maintenance mode OFF", "en": "✅ Maintenance mode OFF"},
    "ai_support_intro": {"bn": "🤖 AI Support\n\nআপনার প্রশ্ন লিখুন। Payment, wallet, network, bKash, Stars বা order problem সম্পর্কে সাহায্য করতে পারি।\n\nOrder চেক: /order ORD-XXXXXX বা /status TRXID\nবন্ধ করতে /cancel লিখুন।", "en": "🤖 AI Support\n\nSend your question. I can help with payment, wallet, network, bKash, Stars, or order issues.\n\nCheck order: /order ORD-XXXXXX or /status TRXID\nSend /cancel to close."},
    "ai_unavailable": {"bn": "❌ AI Support এখন unavailable. Admin-কে জানান।", "en": "❌ AI Support is unavailable. Please contact admin."},
    "ai_thinking": {"bn": "🤖 উত্তর তৈরি করছি...", "en": "🤖 Thinking..."},
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


def ai_support_prompt(lang="bn"):
    return (
        "You are the read-only AI support assistant for a Telegram crypto seller bot. "
        "Reply in Bengali if the user writes Bengali, otherwise reply in English. "
        "Keep replies short, practical, and beginner-friendly. "
        "You can explain bKash payment verification, app/SMS notification delays, Telegram Stars payments, wallet/network selection, gas fees, order IDs, pending orders, and contacting admin. "
        "Never approve payments, never claim a transaction is paid unless the bot/admin verified it, never send crypto, never ask for private keys, never reveal secrets, and never tell users to share seed phrases/private keys. "
        "If user reports stuck payment, ask them for TrxID/order ID and tell them admin may verify through /pending. "
        "Support contact is @" + SUPPORT_USERNAME.lstrip("@") + "."
    )


AI_PROVIDER_LABELS = {
    "gemini": "Gemini",
    "groq": "Groq",
    "openrouter": "OpenRouter",
}


def ai_provider_order():
    order = []
    for provider in AI_PROVIDER_ORDER.split(","):
        provider = provider.strip().lower()
        if provider in AI_PROVIDER_LABELS and provider not in order:
            order.append(provider)
    return order


def ai_provider_keys():
    return {
        "gemini": GEMINI_API_KEY,
        "groq": GROQ_API_KEY,
        "openrouter": OPENROUTER_API_KEY,
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


def _extract_openai_chat_text(data):
    choices = data.get("choices", [])
    if not choices:
        raise RuntimeError("No AI response returned")
    content = choices[0].get("message", {}).get("content", "")
    if isinstance(content, list):
        text = "".join(part.get("text", "") for part in content if isinstance(part, dict)).strip()
    else:
        text = str(content).strip()
    if not text:
        raise RuntimeError("Empty AI response returned")
    return text


def _ask_gemini(question, lang="bn"):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
    payload = {
        "systemInstruction": {"parts": [{"text": ai_support_prompt(lang)}]},
        "contents": [{"role": "user", "parts": [{"text": question[:3000]}]}],
        "generationConfig": {"temperature": 0.3, "maxOutputTokens": 500},
    }
    response = requests.post(url, params={"key": GEMINI_API_KEY}, json=payload, timeout=30)
    response.raise_for_status()
    data = response.json()
    candidates = data.get("candidates", [])
    if not candidates:
        raise RuntimeError("No AI response returned")
    parts = candidates[0].get("content", {}).get("parts", [])
    text = "".join(part.get("text", "") for part in parts).strip()
    if not text:
        raise RuntimeError("Empty AI response returned")
    return text


def _ask_openai_compatible(endpoint, api_key, model, question, lang="bn", extra_headers=None):
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    if extra_headers:
        headers.update(extra_headers)
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": ai_support_prompt(lang)},
            {"role": "user", "content": question[:3000]},
        ],
        "temperature": 0.3,
        "max_tokens": 500,
    }
    response = requests.post(endpoint, headers=headers, json=payload, timeout=30)
    response.raise_for_status()
    return _extract_openai_chat_text(response.json())


def _ask_groq(question, lang="bn"):
    return _ask_openai_compatible(
        "https://api.groq.com/openai/v1/chat/completions",
        GROQ_API_KEY,
        GROQ_MODEL,
        question,
        lang,
    )


def _ask_openrouter(question, lang="bn"):
    return _ask_openai_compatible(
        "https://openrouter.ai/api/v1/chat/completions",
        OPENROUTER_API_KEY,
        OPENROUTER_MODEL,
        question,
        lang,
        {"HTTP-Referer": "https://t.me/", "X-Title": "Mouno Private Telegram Bot"},
    )


def ask_ai_support(question, lang="bn"):
    providers = configured_ai_providers()
    if not providers:
        if not any(ai_provider_keys().values()):
            raise RuntimeError("No AI provider API key is configured")
        raise RuntimeError("No configured AI provider is enabled in AI_PROVIDER_ORDER")
    askers = {
        "gemini": _ask_gemini,
        "groq": _ask_groq,
        "openrouter": _ask_openrouter,
    }
    tried = []
    for provider in providers:
        tried.append(provider)
        try:
            return askers[provider](question, lang)
        except Exception as exc:
            logger.warning("AI provider %s failed: %s", provider, _safe_ai_error(exc))
    raise RuntimeError("All configured AI providers failed: " + ", ".join(tried))


def ai_status_text():
    keys = ai_provider_keys()
    models = {
        "gemini": GEMINI_MODEL,
        "groq": GROQ_MODEL,
        "openrouter": OPENROUTER_MODEL,
    }
    order = ai_provider_order()
    lines = [
        "Provider order: " + (" → ".join(order) if order else "none"),
        "Fallback: first configured provider that succeeds",
    ]
    for provider in ("gemini", "groq", "openrouter"):
        status = "✅ Configured" if keys.get(provider) else "❌ Missing"
        lines.append(f"{AI_PROVIDER_LABELS[provider]}: {status} | model: {models[provider]}")
    lines.extend([
        "User AI Support button: ✅ Enabled",
        "Admin diagnostic: /aiadmin why order failed ORD-XXXXXX",
    ])
    if not any(keys.values()):
        lines.append("Add one provider API key to .env and restart the bot.")
    return panel("🤖 AI Status", "\n".join(lines))


def ai_setup_text():
    return panel(
        "⚙️ AI Setup",
        "1. Edit .env\n"
        "2. Set one or more free/free-tier keys:\n"
        "   GEMINI_API_KEY=...\n"
        "   GROQ_API_KEY=...\n"
        "   OPENROUTER_API_KEY=...\n"
        "3. Optional models:\n"
        "   GEMINI_MODEL=gemini-1.5-flash\n"
        f"   GROQ_MODEL={GROQ_MODEL}\n"
        f"   OPENROUTER_MODEL={OPENROUTER_MODEL}\n"
        "4. Fallback order:\n"
        "   AI_PROVIDER_ORDER=gemini,groq,openrouter\n"
        "5. Restart bot. If one fails, next configured provider answers.\n\n"
        "Public user button: 🤖 AI Support\n"
        "Admin diagnostic: /aiadmin ...",
    )


def user_lang(user_id) -> str:
    return get_user_language(user_id) or "bn"


def tr(key, lang="bn", **kwargs):
    value = TEXT.get(key, {}).get(lang) or TEXT.get(key, {}).get("bn") or key
    return value.format(**kwargs) if kwargs else value


def panel(title, body=""):
    title_line = f"✦ {title} ✦"
    return f"╭─ {title_line}\n╰{'─' * min(len(title_line) + 3, 28)}\n{body}".rstrip()


def short_wallet(wallet):
    return f"{wallet[:8]}...{wallet[-6:]}" if wallet and len(wallet) > 18 else (wallet or "N/A")


def language_keyboard():
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("বাংলা 🇧🇩", callback_data="set_lang_bn"), InlineKeyboardButton("English 🇺🇸", callback_data="set_lang_en")]
        ]
    )


def back_keyboard(lang):
    return InlineKeyboardMarkup([[InlineKeyboardButton(tr("back", lang), callback_data="back")]])


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


def gen_order_id(prefix="STAR"):
    return f"{prefix}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{gen_code(6)}"


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
        symbol, threshold = GAS_META.get(network, ("native", 0))
        balance = balances.get(network)
        ok = True if balance is None else float(balance) >= float(threshold)
        label = info["name"]
        status = "✅" if ok else "⚠️ LOW"
        value = "N/A" if balance is None else balance
        lines.append(f"{status} {label}: {value} {symbol} (min {threshold})")
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


def order_status_text(identifier, viewer_id, lang="bn"):
    kind, row = find_order(identifier)
    if not row:
        return "❌ Order/TrxID পাওয়া যায়নি।" if lang == "bn" else "❌ Order/TrxID not found."
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
    return panel("📈 Admin Report", f"Period: {period}\n🧾 Total orders: {total or 0}\n✅ Completed: {completed or 0}\n❌ Failed: {failed or 0}\n⏳ Pending/other: {(other or 0) + data['pending_orders']}\n💰 Completed BDT volume: {round(total_bdt or 0, 2)}\n💵 Completed crypto volume: {round(total_crypto or 0, 6)}\n💹 Profit: {round(total_profit or 0, 2)} BDT\n⭐ Stars ledger pending payout: {stars_count or 0} orders / {stars_amount or 0} Stars\n💸 Seller payout requests: {payout_count or 0} / {payout_amount or 0}\n\nTop networks:\n{top}")


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


def main_menu(user_id, lang=None):
    lang = lang or user_lang(user_id)
    keyboard = [
        [InlineKeyboardButton(tr("buy", lang), callback_data="buy"), InlineKeyboardButton(tr("stars", lang), callback_data="star_buy")],
        [InlineKeyboardButton(tr("gift", lang), callback_data="redeem_menu"), InlineKeyboardButton(tr("rate", lang), callback_data="rate")],
        [InlineKeyboardButton(tr("balance", lang), callback_data="balance"), InlineKeyboardButton(tr("txlog", lang), callback_data="txlog")],
        [InlineKeyboardButton(tr("wallet", lang), callback_data="my_wallet_menu"), InlineKeyboardButton(tr("order_status", lang), callback_data="order_status")],
        [InlineKeyboardButton(tr("sellers", lang), callback_data="sellers_market"), InlineKeyboardButton(tr("seller_center", lang), callback_data="seller_center")],
        [InlineKeyboardButton(tr("ai_support", lang), callback_data="ai_support"), InlineKeyboardButton(tr("seller_dashboard", lang), callback_data="seller_dashboard")],
        [InlineKeyboardButton(tr("support", lang), url=f"https://t.me/{SUPPORT_USERNAME.lstrip('@')}")],
        [InlineKeyboardButton(tr("terms", lang), callback_data="terms"), InlineKeyboardButton(tr("language", lang), callback_data="language_menu")],
    ]
    if is_admin(user_id):
        keyboard.append([InlineKeyboardButton(tr("set_rate", lang), callback_data="setrate_menu"), InlineKeyboardButton(tr("gen_code", lang), callback_data="gencode_menu")])
        keyboard.append([InlineKeyboardButton(tr("admin_send", lang), callback_data="admin_send"), InlineKeyboardButton(tr("disable_code", lang), callback_data="disable_code_menu")])
        keyboard.append([InlineKeyboardButton("📈 Report", callback_data="admin_report_daily"), InlineKeyboardButton("💾 Backup Now", callback_data="backup_now")])
        keyboard.append([InlineKeyboardButton("📦 Reserves", callback_data="admin_reservations"), InlineKeyboardButton("💹 Profit", callback_data="admin_profit")])
        keyboard.append([InlineKeyboardButton("⛽ Gas Monitor", callback_data="admin_gas"), InlineKeyboardButton("🧾 Audit Log", callback_data="admin_audit")])
        keyboard.append([InlineKeyboardButton("🏷 Seller Badges", callback_data="seller_badges"), InlineKeyboardButton("🤖 AI Admin", callback_data="ai_admin_help")])
        keyboard.append([InlineKeyboardButton("🤖 AI Status", callback_data="ai_status"), InlineKeyboardButton("⚙️ AI Setup", callback_data="ai_setup")])
        keyboard.append([InlineKeyboardButton("🏪 Seller Apps", callback_data="admin_sellers"), InlineKeyboardButton("⭐ Seller Stars", callback_data="seller_payouts")])
        keyboard.append([InlineKeyboardButton("💸 Payouts", callback_data="admin_payouts"), InlineKeyboardButton("🧪 Test Tools", callback_data="test_tools")])
        keyboard.append([InlineKeyboardButton("🛑 Maintenance ON", callback_data="maintenance_on"), InlineKeyboardButton("✅ Maintenance OFF", callback_data="maintenance_off")])
    return InlineKeyboardMarkup(keyboard)


def network_menu(prefix, lang="bn"):
    cancel_callback = {
        "network": "cancel",
        "uw": "uw_cancel",
        "setrate": "back",
        "gencode": "back",
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


def user_network_menu():
    return network_menu("uw")


def rates_text(title=None, lang="bn"):
    rates = get_all_rates()
    title = title if title is not None else f"💸 {tr('current_rates', lang)}"
    lines = [
        f"{title}",
        DIVIDER,
        f"🔹 Solana USDC          1 = {rates.get('solana', 0)} BDT",
        f"🔸 Polygon USDC         1 = {rates.get('polygon', 0)} BDT",
        f"🟡 BSC USDT             1 = {rates.get('bsc', 0)} BDT",
        f"🔺 Avalanche USDT       1 = {rates.get('avalanche', 0)} BDT",
        f"🔷 Ethereum USDT        1 = {rates.get('ethereum', 0)} BDT",
        f"🔷 Ethereum USDC        1 = {rates.get('ethereum_usdc', 0)} BDT",
        f"🔵 Base USDC            1 = {rates.get('base', 0)} BDT",
        f"🔴 Tron USDT            1 = {rates.get('trc20', 0)} BDT",
        f"💎 TON                  1 = {rates.get('ton', 0)} BDT",
    ]
    return "\n".join(lines)


def home_text(user_name=None, lang="bn"):
    greeting = f"👋 {tr('welcome', lang)}, {user_name}!" if user_name else "👋 Welcome!"
    subtitle = "Fast • Secure • Multi-chain" if lang == "en" else "দ্রুত • নিরাপদ • Multi-chain"
    body = (
        f"{greeting}\n"
        f"⚡ {subtitle}\n\n"
        f"{rates_text(lang=lang)}\n{DIVIDER}\n"
        f"📲 bKash: `{BKASH_NUMBER}`\n"
        f"🛡️ {'Always check network and wallet before payment.' if lang == 'en' else 'Payment করার আগে network ও wallet যাচাই করুন।'}\n\n"
        f"👇 {tr('select_action', lang)}"
    )
    return panel(tr("home_title", lang), body)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = get_user_language(user.id)
    if not lang:
        await update.message.reply_text(tr("choose_language", "bn"), reply_markup=language_keyboard())
        return
    await update.message.reply_text(home_text(user.first_name, lang), reply_markup=main_menu(user.id, lang))


async def send_crypto(network, wallet, amount):
    gas_ok, gas_bal, gas_threshold, gas_symbol = check_gas_sufficient(network)
    if not gas_ok and gas_bal is not None:
        raise RuntimeError(f"Low gas: {gas_bal} {gas_symbol} available, minimum {gas_threshold} required")
    if gas_bal is None:
        logger.warning("Gas balance could not be checked for %s", network)
        add_audit("system", "gas_check_unknown", "network", network, "send not blocked")
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


def short_datetime(value):
    return str(value or "")[:16]


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


def seller_guide_text(seller=None):
    token = seller[6] if seller else "YOUR_SMS_TOKEN"
    return (
        "🏪 Seller Setup Guide\n\n"
        "1️⃣ Apply করুন এবং admin approval এর জন্য অপেক্ষা করুন।\n"
        "2️⃣ যে network sell করবেন তার আলাদা crypto wallet/private key প্রস্তুত রাখুন; gas token রাখবেন।\n"
        "3️⃣ Seller Center → Delivery Wallet এ private key add/update করুন। Server master key দিয়ে encrypt হবে; Telegram message delete হবে।\n"
        "4️⃣ Seller rate set করুন; 0 দিলে global/admin rate use হবে।\n"
        "5️⃣ bKash SMS/Notification forwarder endpoint set করুন।\n"
        f"SMS endpoint: http://YOUR_SERVER:5000/seller/{token}/sms\n"
        f"Notification endpoint: http://YOUR_SERVER:5000/seller/{token}/notification\n"
        f"Alternative: /sms?seller_token={token}\n"
        "6️⃣ TON seller auto-delivery unsupported; supported: Solana, Polygon, BSC, Avalanche, Ethereum, Base, TRC20.\n"
        "7️⃣ Telegram Stars seller sales create a pending payout ledger; admin marks payout paid manually."
    )


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
        await query.edit_message_text("🛍️ এখন কোনো approved seller নেই।", reply_markup=back_keyboard(lang))
        return
    keyboard = [[InlineKeyboardButton(f"🏪 {seller_public_name(s)[:28]}", callback_data=f"sellerpick_{s[0]}")] for s in sellers]
    keyboard.append([InlineKeyboardButton(tr("back", lang), callback_data="back")])
    await query.edit_message_text(panel("🛍️ Seller Marketplace", "Seller বেছে নিন। Payment seller-এর bKash/Stars ledger route হবে।"), reply_markup=InlineKeyboardMarkup(keyboard))


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
    rows = list_pending_seller_orders(None if is_admin(seller_id) else seller_id, 10)
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
        if method == "stars" and stars_amount:
            create_seller_star_ledger(gen_order_id("SL"), seller_id, order_id, stars_amount)
        explorer = f"{ni.get('explorer','')}{sig}"
        await bot.send_message(int(buyer_id), f"🎉 Seller order completed!\n\n🏪 {seller_public_name(seller)}\n🧾 {order_id}\n🌐 {ni['name']}\n💵 {amount_crypto} {ni['symbol']}\n👛 {wallet}\n🔗 {explorer}")
        await bot.send_message(int(seller_id), f"✅ Order delivered automatically.\n\n🧾 {order_id}\n👤 Buyer: @{buyer_username or buyer_id}\n💵 {amount_crypto} {ni['symbol']}\n🔗 {explorer}")
        if ADMIN_ID:
            await bot.send_message(ADMIN_ID, f"✅ Seller order completed.\n\n{seller_order_summary(get_seller_order(order_id))}\n🔗 {explorer}")
        return True, sig
    except Exception as exc:
        update_seller_order(order_id, status="failed", error=str(exc)[:500])
        try:
            await bot.send_message(int(seller_id), f"🚨 Seller order send failed.\n\n🧾 {order_id}\n❌ {exc}")
            await bot.send_message(ADMIN_ID, f"🚨 Seller order send failed.\n\n{seller_order_summary(order)}\n❌ {exc}")
            await bot.send_message(int(buyer_id), f"✅ Payment received but seller delivery failed. Seller/admin has been notified.\n🧾 {order_id}")
        except Exception:
            pass
        return False, str(exc)


async def handle_seller_order_trx(update, context, user_id, username):
    order_id = context.user_data.get("seller_order_id")
    order = get_seller_order(order_id)
    if not order:
        await update.message.reply_text("❌ Seller order session expired.")
        context.user_data.clear()
        return
    trx_id = update.message.text.strip().upper()
    if len(trx_id) < 4:
        await update.message.reply_text("❌ ভুল TrxID! আবার দিন।")
        return
    if get_seller_order_by_trx(order[1], trx_id):
        await update.message.reply_text("⚠️ এই seller-এর জন্য TrxID আগে ব্যবহার হয়েছে।")
        return
    update_seller_order(order_id, trx_id=trx_id)
    notice = get_seller_payment_notice(order[1], trx_id)
    if notice:
        ok, result = await complete_seller_order(update.get_bot(), order_id, user_id, notice[2])
        context.user_data.clear()
        if ok:
            await update.message.reply_text("✅ Payment notice matched. Crypto পাঠানো হয়েছে।")
        else:
            await update.message.reply_text(f"⏳ Seller manual verification লাগবে।\n🧾 {order_id}\nReason: {result}")
        return
    update_seller_order(order_id, status="pending_manual")
    seller_id = order[1]
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("✅ Approve/send", callback_data=f"sordera_{order_id}"), InlineKeyboardButton("❌ Reject", callback_data=f"sorderr_{order_id}")]])
    try:
        await update.get_bot().send_message(int(seller_id), f"⚠️ Buyer TrxID দিল কিন্তু forwarder notice মেলেনি। Manual verify করুন।\n\n{seller_order_summary(get_seller_order(order_id))}", reply_markup=keyboard)
        await update.get_bot().send_message(ADMIN_ID, f"⚠️ Seller order manual verify.\n\n{seller_order_summary(get_seller_order(order_id))}", reply_markup=keyboard)
    except Exception as exc:
        logger.error(exc)
    context.user_data.clear()
    await update.message.reply_text(f"⏳ TrxID seller যাচাই করছেন।\n\n🧾 Order: {order_id}\n🔑 TrxID: {trx_id}")


async def process_seller_bkash(app, text, sender, meta):
    parsed = parse_bkash_payment_notice(text)
    if not parsed:
        return True
    token = (meta or {}).get("seller_token")
    seller = get_seller_by_sms_token(token) if token else None
    trx_id = parsed["trx_id"]
    amount_bdt = parsed["amount_bdt"]
    if not seller or seller[5] != "approved":
        logger.warning("Seller bKash notice rejected for unknown/unapproved token: %s", token)
        if ADMIN_ID:
            await app.bot.send_message(ADMIN_ID, f"⚠️ Seller bKash notice rejected. Unknown/unapproved token.\nSource: {sender}\nTrxID: {trx_id}\nAmount: {amount_bdt}")
        return True
    seller_id = seller[0]
    saved_new = save_seller_payment_notice(seller_id, trx_id, amount_bdt, sender, "seller_bkash", text)
    touch_webhook_notice(f"seller_{sender}", trx_id, amount_bdt)
    order = find_waiting_seller_order_by_trx(seller_id, trx_id)
    if order:
        if trx_id.startswith("TEST") or str(sender).startswith("test"):
            await app.bot.send_message(ADMIN_ID, f"🧪 Test seller bKash notice matched order but auto-send blocked.\nSeller: {seller_id}\nOrder: {order[0]}\nTrxID: {trx_id}\nAmount: {amount_bdt}")
            return True
        ok, result = await complete_seller_order(app, order[0], "seller_sms", amount_bdt)
        if not ok:
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("✅ Approve/send", callback_data=f"sordera_{order[0]}"), InlineKeyboardButton("❌ Reject", callback_data=f"sorderr_{order[0]}")]])
            await app.bot.send_message(int(seller_id), f"⚠️ Seller payment notice needs manual verification.\nReason: {result}\n\n{seller_order_summary(get_seller_order(order[0]))}", reply_markup=keyboard)
            await app.bot.send_message(ADMIN_ID, f"⚠️ Seller payment notice needs manual verification.\nReason: {result}\n\n{seller_order_summary(get_seller_order(order[0]))}", reply_markup=keyboard)
        return True
    if saved_new:
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🧾 Pending Orders", callback_data="seller_pending")]])
        await app.bot.send_message(int(seller_id), f"💰 Seller bKash notice received but no waiting order matched yet.\n\n🔑 TrxID: {trx_id}\n💵 {amount_bdt} BDT", reply_markup=keyboard)
        if ADMIN_ID:
            await app.bot.send_message(ADMIN_ID, f"💰 Unmatched seller bKash notice.\nSeller: {seller_public_name(seller)} ({seller_id})\nTrxID: {trx_id}\nAmount: {amount_bdt}")
    return True


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)
    username = query.from_user.username or query.from_user.first_name
    lang = user_lang(user_id)

    if query.data == "language_menu":
        await query.edit_message_text(tr("choose_language", lang), reply_markup=language_keyboard())

    elif query.data.startswith("set_lang_"):
        lang = query.data.replace("set_lang_", "", 1)
        set_user_language(user_id, lang)
        context.user_data["lang"] = lang
        await query.edit_message_text(
            f"{tr('language_saved', lang)}\n\n{home_text(query.from_user.first_name, lang)}",
            reply_markup=main_menu(user_id, lang),
        )

    elif query.data == "rate":
        await query.edit_message_text(
            panel("📊 Rates", f"{rates_text('', lang)}\n{DIVIDER}\n📲 bKash: `{BKASH_NUMBER}`\n⚡ {'Delivery: usually 1-3 minutes' if lang == 'en' else 'সাধারণত ১-৩ মিনিটে পাঠানো হয়'}"),
            reply_markup=back_keyboard(lang),
        )

    elif query.data == "terms":
        await query.edit_message_text(terms_text(lang), reply_markup=back_keyboard(lang))

    elif query.data == "order_status":
        context.user_data.clear()
        context.user_data["order_status_lookup"] = True
        await query.edit_message_text("🔎 Order Status\n\nOrder ID বা TrxID পাঠান।\nউদাহরণ: ORD-ABC123 অথবা TrxID\n\nCommand: /order ORD-XXXXXX বা /status TRXID", reply_markup=back_keyboard(lang))

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
        await query.edit_message_text(seller_guide_text(get_seller(user_id)), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(tr("back", lang), callback_data="seller_center")]]))

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
            text = "✅ Seller approved."
            notify = "🎉 আপনার seller account approved হয়েছে। Seller Center খুলুন।"
        else:
            reject_seller(seller_id)
            text = "❌ Seller rejected."
            notify = f"❌ Seller application rejected. Support: @{SUPPORT_USERNAME.lstrip('@')}"
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
            await query.edit_message_text("❌ এই seller এখন কোনো network enable করেননি।", reply_markup=back_keyboard(lang))
            return ConversationHandler.END
        await query.edit_message_text(
            panel("🛍️ Seller Order", f"🏪 {seller_public_name(seller)}\n📲 bKash: {seller[3]}\n\nPayment method বেছে নিন।"),
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
        await query.edit_message_text(f"🏪 {seller_public_name(seller)}\n\nNetwork বেছে নিন:", reply_markup=seller_network_menu("sellerbuy", seller_id, lang))

    elif query.data.startswith("sellerbuy_"):
        network = query.data.replace("sellerbuy_", "", 1)
        seller_id = context.user_data.get("seller_buy_seller_id")
        if not seller_id or network not in [row[1] for row in list_enabled_seller_wallets(seller_id)]:
            await query.edit_message_text("❌ Seller buy session expired.", reply_markup=back_keyboard(lang))
            return ConversationHandler.END
        context.user_data["seller_buy_network"] = network
        ni = NETWORKS[network]
        rate = seller_rate_or_global(seller_id, network)
        await query.edit_message_text(f"🌐 {ni['name']}\n💵 Rate: 1 {ni['symbol']} = {rate} BDT\n\nBuyer destination wallet দিন:\n{wallet_hint(network)}")
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
        if not (is_admin(user_id) or str(order[1]) == user_id):
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
        await query.edit_message_text(ai_status_text(), reply_markup=back_keyboard(lang))

    elif query.data == "ai_setup":
        if not is_admin(user_id):
            return ConversationHandler.END
        await query.edit_message_text(ai_setup_text(), reply_markup=back_keyboard(lang))

    elif query.data == "admin_payouts":
        if not is_admin(user_id):
            return ConversationHandler.END
        await show_payouts_to_target(query)

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
        context.user_data.clear()
        context.user_data["ai_support"] = True
        await query.edit_message_text(tr("ai_support_intro", lang), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(tr("cancel", lang), callback_data="ai_support_cancel")]]))

    elif query.data == "ai_support_cancel":
        context.user_data.clear()
        await query.edit_message_text(home_text(lang=lang), reply_markup=main_menu(user_id, lang))

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
        await query.edit_message_text("🔐 Wallet Setup\n\nআপনার Network বেছে নিন:", reply_markup=user_network_menu())
        return SETUP_NETWORK

    elif query.data == "mw_send":
        row = get_user_wallet(user_id)
        if not row:
            await query.edit_message_text("❌ Wallet নেই! আগে setup করুন।")
            return ConversationHandler.END
        network = row[2]
        net_info = NETWORKS.get(network, {"name": network})
        await query.edit_message_text(f"💸 Crypto পাঠানো\n\n🌐 Network: {net_info['name']}\n👛 আপনার address: {row[3]}\n\nDestination wallet address দিন:\n📋 উদাহরণ: {wallet_hint(network)}")
        return SEND_W_DEST

    elif query.data == "mw_delete":
        await query.edit_message_text(
            "⚠️ সতর্কতা!\n\nWallet key মুছে দেওয়া হবে।\nUndo করা যাবে না!\n\nনিশ্চিত?",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ হ্যাঁ, মুছে দাও", callback_data="del_confirm"), InlineKeyboardButton("❌ না", callback_data="my_wallet_menu")]]),
        )

    elif query.data == "show_guide":
        await query.edit_message_text(GUIDE, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 ফিরে যান", callback_data="my_wallet_menu")]]))

    elif query.data == "check_mybal":
        context.user_data["uw_waiting_bal_password"] = True
        await query.edit_message_text("🔐 আপনার Password দিন:\n\n⚠️ Message পাঠানোর পর মুছে যাবে।")

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
        await query.edit_message_text("🎁 গিফট কোড রিডিম\n\nআপনার গিফট কোড লিখুন:\n\n📋 উদাহরণ: ABC12345")

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
        await query.edit_message_text("🔐 আপনার Password দিন:\n\n⚠️ Message পাঠানোর পর মুছে যাবে।")
        return SEND_W_PASSWORD

    elif query.data == "sw_cancel":
        context.user_data.clear()
        await query.edit_message_text("❌ বাতিল হয়েছে।")
        return ConversationHandler.END

    elif query.data == "del_confirm":
        await query.edit_message_text("🔐 Password দিন নিশ্চিত করতে:")
        return DEL_PASSWORD

    elif query.data == "del_cancel":
        await query.edit_message_text("❌ বাতিল হয়েছে।")
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
    context.user_data.clear()
    context.user_data["ai_support"] = True
    await update.message.reply_text(tr("ai_support_intro", lang))


async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    total, completed, failed, total_bdt, total_crypto, total_profit = get_transaction_stats()
    pending_count = len(get_pending_orders(100))
    failed_count = len(get_failed_transactions(100))
    maintenance = "ON" if is_maintenance_enabled() else "OFF"
    await update.message.reply_text(
        "📊 Admin Dashboard\n\n"
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
    await update.message.reply_text(order_status_text(context.args[0], user_id, lang))


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
            return f"Order {order_id} failed after payment context was saved. Likely crypto send failed due to low seller balance, gas, RPC, invalid wallet, or sender key issue. Network={network}, amount={crypto}, wallet={short_wallet(wallet)}. Check /failed and retry if safe."
        return f"Order {order_id} status is {status}. Check pending order/SMS log and seller balance. Created {created}."
    order_id, user_id, _username, network, wallet, amount, stars, status, _tg, _prov, tx_sig, error, created, updated = row
    if status == "failed":
        return f"Stars order {order_id} failed. Error: {error or 'unknown'}. Likely crypto send failure, payment mismatch, low stock, gas/RPC, or invalid wallet."
    if status in {"pending", "paid"}:
        return f"Stars order {order_id} is {status}. Pending means invoice not paid; paid means Telegram payment arrived but crypto completion may still be waiting/failed."
    return f"Stars order {order_id} is {status}. TX={bool(tx_sig)}."


async def aiadmin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    if not context.args:
        await update.message.reply_text("Usage: /aiadmin why order failed ORD-123")
        return
    identifier = next((arg for arg in reversed(context.args) if arg.upper().startswith(("ORD", "STAR", "TEST", "PAY")) or len(arg) >= 6), context.args[-1])
    local = explain_order_failure(identifier)
    if configured_ai_providers():
        try:
            prompt = f"Read-only admin diagnostic. Explain likely failure and next safe checks. DB context: {local}. User asked: {' '.join(context.args)}"
            local = await asyncio.get_running_loop().run_in_executor(None, lambda: ask_ai_support(prompt, "en"))
        except Exception:
            pass
    await update.message.reply_text(f"🤖 AI Admin diagnostic\n\n{local}")


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
    _trx_id, _bdt, crypto, network, wallet, status, _created, _order_id, _user_id, _old_sig = row
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
        add_audit(query.from_user.id, "retry_send_completed", "transaction", trx_id)
        await query.edit_message_text(f"✅ Retry successful!\n\n🌐 {ni['name']}\n💵 {crypto} {ni['symbol']}\n👛 {wallet}\n🔗 {ni['explorer']}{sig}", reply_markup=back_keyboard(lang))
    except Exception as exc:
        add_audit(query.from_user.id, "retry_send_failed", "transaction", trx_id, str(exc))
        await query.edit_message_text(f"❌ Retry failed again.\n\n{exc}", reply_markup=failed_retry_keyboard(trx_id))


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
    row = get_user_wallet(user_id)
    if row:
        network = row[2]
        net_info = NETWORKS.get(network, {"name": network, "symbol": "?"})
        keyboard = [
            [InlineKeyboardButton("💰 আমার Balance", callback_data="check_mybal"), InlineKeyboardButton("💸 Crypto পাঠাও", callback_data="mw_send")],
            [InlineKeyboardButton("🔄 Wallet পরিবর্তন", callback_data="mw_change"), InlineKeyboardButton("🗑️ Wallet মুছো", callback_data="mw_delete")],
            [InlineKeyboardButton("📖 ব্যবহার গাইড", callback_data="show_guide")],
            [InlineKeyboardButton("🔙 ফিরে যান", callback_data="back")],
        ]
        await query.edit_message_text(
            panel("🔐 My Wallet", f"✅ Connected\n\n🌐 Network: {net_info['name']}\n👛 Address: `{short_wallet(row[3])}`\n\n👇 Choose an action"),
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
    else:
        keyboard = [[InlineKeyboardButton("🔐 Wallet সংযুক্ত করুন", callback_data="mw_setup")], [InlineKeyboardButton("📖 ব্যবহার গাইড", callback_data="show_guide")], [InlineKeyboardButton("🔙 ফিরে যান", callback_data="back")]]
        await query.edit_message_text(panel("🔐 My Wallet", "❌ No wallet connected yet.\n\nConnect a wallet to check balance and send crypto securely."), reply_markup=InlineKeyboardMarkup(keyboard))


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
    gas_ok, gas_bal, gas_threshold, gas_symbol = check_gas_sufficient(network)
    if not gas_ok and gas_bal is not None:
        await query.edit_message_text(
            f"⛽ Network gas low. New orders paused for {net_info['name']}.\n\nAvailable: {gas_bal} {gas_symbol}\nMinimum: {gas_threshold} {gas_symbol}",
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
    await query.edit_message_text(f"✅ Approved!\n\n⏳ Crypto পাঠানো হচ্ছে...\n\n👤 User: {target_uid}\n🔑 TrxID: {trx_id}\n🌐 {net_info['name']}")

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

    sufficient, current_bal = check_sufficient(network, crypto_amount, exclude_order_id=order_id, exclude_trx_id=trx_id)
    if not sufficient and current_bal is not None:
        await query.edit_message_text(f"❌ Insufficient stock.\n\n{stock_detail(network, crypto_amount, current_bal)}")
        return

    try:
        sig = await send_crypto(network, target_wallet, crypto_amount)
        explorer = f"{net_info['explorer']}{sig}"
        order_id = save_transaction(trx_id, target_uid, amount_bdt, crypto_amount, target_wallet, sig, "completed", network, order_id=order_id, source="bkash")
        consume_stock_reservation(order_id=order_id, trx_id=trx_id)
        delete_pending_order(trx_id)
        add_audit(user_id, "order_approved", "transaction", trx_id, f"order={order_id}")
        await query.edit_message_text(f"✅ Crypto পাঠানো হয়েছে!\n\n👤 User: {target_uid}\n{receipt_block(order_id, trx_id, network, crypto_amount, target_wallet, sig)}")
        try:
            await query.get_bot().send_message(int(target_uid), f"🎉 পেমেন্ট confirm হয়েছে!\n\n{receipt_block(order_id, trx_id, network, crypto_amount, target_wallet, sig)}\n\nধন্যবাদ! 🙏")
        except Exception:
            pass
    except Exception as exc:
        save_transaction(trx_id, target_uid, amount_bdt, crypto_amount, target_wallet, "", "failed", network, order_id=order_id, source="bkash")
        release_stock_reservation(order_id=order_id, trx_id=trx_id, reason="admin_approve_send_failed", actor_id="system")
        add_audit(user_id, "order_approve_send_failed", "transaction", trx_id, str(exc))
        await query.edit_message_text(f"❌ পাঠাতে ব্যর্থ!\n\n{exc}")
        logger.error("Admin approve send failed: %s", exc)


async def reject_order(query, user_id):
    if not is_admin(user_id):
        return
    _prefix, target_uid, trx_id = query.data.split("_", 2)
    pending = get_pending_order(trx_id)
    order_id = pending[7] if pending and len(pending) > 7 else None
    delete_pending_order(trx_id)
    release_stock_reservation(order_id=order_id, trx_id=trx_id, reason="admin_reject", actor_id=user_id)
    add_audit(user_id, "order_rejected", "pending_order", trx_id, f"order={order_id}")
    await query.edit_message_text(f"❌ Rejected!\n\n👤 User: {target_uid}\n🔑 TrxID: {trx_id}")
    try:
        await query.get_bot().send_message(int(target_uid), f"❌ আপনার পেমেন্ট verify করা যায়নি!\n\n🔑 TrxID: {trx_id}\n\nসঠিক TrxID নিশ্চিত করুন অথবা যোগাযোগ করুন:\n📞 @MdMouno")
    except Exception:
        pass


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
    gas_ok, gas_bal, gas_threshold, gas_symbol = check_gas_sufficient(network)
    if not gas_ok and gas_bal is not None:
        await update.message.reply_text(f"⛽ {net_info['name']} gas low. নতুন order সাময়িক বন্ধ।\n\nAvailable: {gas_bal} {gas_symbol}\nMinimum: {gas_threshold} {gas_symbol}")
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
    gas_ok, gas_bal, gas_threshold, gas_symbol = check_gas_sufficient(network)
    if not gas_ok and gas_bal is not None:
        await update.message.reply_text(f"⛽ {net_info['name']} gas low. নতুন Stars order সাময়িক বন্ধ।\n\nAvailable: {gas_bal} {gas_symbol}\nMinimum: {gas_threshold} {gas_symbol}")
        return ConversationHandler.END

    order_id = gen_order_id("STAR")
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
    gas_ok, gas_bal, gas_threshold, gas_symbol = check_gas_sufficient(network)
    if not gas_ok and gas_bal is not None:
        await update.message.reply_text(f"⛽ Low gas: {gas_bal} {gas_symbol} available, minimum {gas_threshold} required.")
        return ConversationHandler.END
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
        await query.edit_message_text(f"❌ Send failed.\n\n{exc}", reply_markup=back_keyboard(lang))


async def seller_center_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await show_seller_center(update.message, context, str(user.id), user.username or user.first_name, edit=False)


async def seller_guide_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(seller_guide_text(get_seller(str(update.effective_user.id))))


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
    network = context.user_data.get("seller_buy_network")
    seller_id = context.user_data.get("seller_buy_seller_id")
    if not network or not seller_id:
        await update.message.reply_text("❌ Session expired.")
        return ConversationHandler.END
    if not valid_wallet(network, wallet):
        await update.message.reply_text(f"❌ ভুল wallet.\nExample: {wallet_hint(network)}")
        return SELLER_BUY_WALLET
    context.user_data["seller_buy_wallet"] = wallet
    ni = NETWORKS[network]
    rate = seller_rate_or_global(seller_id, network)
    await update.message.reply_text(f"কত BDT-এর {ni['symbol']} কিনবেন?\n\nRate: 1 {ni['symbol']} = {rate} BDT")
    return SELLER_BUY_AMOUNT


async def seller_buy_amount_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
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
        await update.message.reply_text("শুধু সংখ্যা লিখুন।")
        return SELLER_BUY_AMOUNT
    seller = get_seller(seller_id)
    if not seller or seller[5] != "approved":
        await update.message.reply_text("❌ Seller unavailable.")
        return ConversationHandler.END
    rate = seller_rate_or_global(seller_id, network)
    amount_crypto = round(amount_bdt / rate, 6)
    ni = NETWORKS[network]
    order_id = gen_order_id("SO")
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
        await update.message.reply_text(f"⭐ Invoice sent.\n\n🧾 {order_id}\n🏪 {seller_public_name(seller)}\n💵 {amount_crypto} {ni['symbol']}\n⭐ {stars_amount} Stars\n\nSeller Stars earnings ledger/manual payout হবে।")
        context.user_data.clear()
        return ConversationHandler.END
    create_seller_order(order_id, seller_id, user.id, username, "bkash", network, wallet, amount_bdt, amount_crypto, None, status="waiting_payment")
    context.user_data.clear()
    context.user_data.update({"waiting_seller_trxid": True, "seller_order_id": order_id, "trx_deadline": asyncio.get_event_loop().time() + 900})
    await update.message.reply_text(f"🎯 Seller order created.\n\n🧾 Order: {order_id}\n🏪 {seller_public_name(seller)}\n📲 bKash: {seller[3]}\n💰 Send exactly: {amount_bdt} BDT\n💵 Receive: {amount_crypto} {ni['symbol']}\n👛 {wallet}\n\nPayment করার পর TrxID লিখুন।")
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


async def waiting_trxid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    username = update.effective_user.username or update.effective_user.first_name
    incoming_text = update.message.text.strip()
    lang = maybe_update_language(user_id, incoming_text)

    if context.user_data.get("order_status_lookup"):
        context.user_data.clear()
        await update.message.reply_text(order_status_text(incoming_text, user_id, lang), reply_markup=main_menu(user_id, lang))
        return

    if context.user_data.get("payout_request"):
        context.user_data.clear()
        await create_payout_from_text(update, user_id, incoming_text)
        return

    if context.user_data.get("ai_support"):
        text = incoming_text
        if text.lower() in {"/cancel", "cancel", "বন্ধ", "বাতিল"}:
            context.user_data.clear()
            await update.message.reply_text("✅ AI Support closed." if lang == "en" else "✅ AI Support বন্ধ হয়েছে।", reply_markup=main_menu(user_id, lang))
            return
        await update.message.reply_text(tr("ai_thinking", lang))
        try:
            answer = await asyncio.get_running_loop().run_in_executor(None, lambda: ask_ai_support(text, lang))
        except Exception as exc:
            logger.error("AI support failed: %s", exc)
            answer = tr("ai_unavailable", lang)
        await update.message.reply_text(answer)
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
        await update.message.reply_text("⏰ সময়সীমা শেষ!\n\nআবার অর্ডার করুন /start দিয়ে\n\n❓ @MdMouno")
        return

    trx_id = incoming_text.upper()
    if len(trx_id) < 4:
        await update.message.reply_text("❌ ভুল TrxID! আবার চেষ্টা করুন।")
        return
    if trx_exists(trx_id):
        await update.message.reply_text("⚠️ এই TrxID আগেই ব্যবহার হয়েছে!\n\n❓ @MdMouno")
        return

    wallet = get_wallet(user_id)
    network = context.user_data.get("network", "solana")
    net_info = NETWORKS[network]
    if not wallet:
        await update.message.reply_text("❌ Wallet পাওয়া যায়নি!\n\n/start দিয়ে আবার শুরু করুন।")
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
            await update.get_bot().send_message(ADMIN_ID, f"⚠️ SMS পাওয়া যায়নি! Manual Verify দরকার।\n\n🧾 Order: {order_id}\n👤 User: @{username} ({user_id})\n🔑 TrxID: {trx_id}\n💰 Amount: {amount_bdt} BDT\n💵 Est: {crypto_amount} {net_info['symbol']}\n🌐 Network: {net_info['name']}\n👛 Wallet: {wallet}\n\nbKash এ TrxID যাচাই করে Approve বা Reject করুন:", reply_markup=InlineKeyboardMarkup(keyboard))
        except Exception as exc:
            logger.error(exc)
        await update.message.reply_text(f"⏳ TrxID যাচাই করা হচ্ছে।\n\n🔑 TrxID: {trx_id}\n\nAdmin যাচাই করছেন, একটু অপেক্ষা করুন...")
        return

    amount_bdt = sms_row[1]
    crypto_amount = round(amount_bdt / get_rate(network), 6)
    order_id = context.user_data.get("order_id") or f"ORD-{gen_code(6)}"
    bind_stock_reservation_trx(order_id, trx_id)
    sufficient, current_bal = check_sufficient(network, crypto_amount, exclude_order_id=order_id)
    if not sufficient and current_bal is not None:
        await update.message.reply_text(f"❌ পর্যাপ্ত {net_info['symbol']} নেই!\n\n🌐 {net_info['name']}\n💵 চান: {crypto_amount}\n{stock_detail(network, crypto_amount, current_bal)}\n\n📞 @MdMouno")
        return

    await update.message.reply_text(f"✅ পেমেন্ট যাচাই সফল!\n\n🌐 {net_info['name']}\n💰 {amount_bdt} BDT = {crypto_amount} {net_info['symbol']}\n👛 {wallet}\n\n⏳ পাঠানো হচ্ছে...")
    try:
        sig = await send_crypto(network, wallet, crypto_amount)
        explorer = f"{net_info['explorer']}{sig}"
        mark_sms_used(trx_id)
        order_id = save_transaction(trx_id, user_id, amount_bdt, crypto_amount, wallet, sig, "completed", network, order_id=order_id, source="bkash")
        consume_stock_reservation(order_id=order_id, trx_id=trx_id)
        context.user_data.clear()
        await update.message.reply_text(f"🎉 {net_info['symbol']} পাঠানো হয়েছে!\n\n{receipt_block(order_id, trx_id, network, crypto_amount, wallet, sig)}\n\nধন্যবাদ! 🙏")
    except Exception as exc:
        save_transaction(trx_id, user_id, amount_bdt, crypto_amount, wallet, "", "failed", network, order_id=order_id, source="bkash")
        release_stock_reservation(order_id=order_id, trx_id=trx_id, reason="send_failed", actor_id="system")
        add_audit("system", "send_failed", "transaction", trx_id, str(exc))
        context.user_data.clear()
        logger.error("Send failed: %s", exc)
        await update.message.reply_text(f"❌ পাঠাতে সমস্যা!\n\n📞 @MdMouno\n\nআপনার TrxID: {trx_id}\nসংরক্ষণ করুন।")


async def handle_redeem(update, context, user_id, username):
    if context.user_data.get("redeem_step") == "code":
        code = update.message.text.strip().upper()
        row = get_code(code)
        if not row:
            await update.message.reply_text("❌ কোড পাওয়া যায়নি!\n\nসঠিক কোড লিখুন।")
            return
        _code_val, amount_crypto, expires_at, used, _used_by, _created_at, code_network = row
        if used:
            await update.message.reply_text("⚠️ এই কোড আগেই ব্যবহার হয়েছে!\n\n❓ @MdMouno")
            context.user_data.clear()
            return
        if datetime.now() > datetime.fromisoformat(expires_at):
            await update.message.reply_text("⏰ এই কোডের মেয়াদ শেষ!\n\n❓ @MdMouno")
            context.user_data.clear()
            return
        net_info = NETWORKS.get(code_network, NETWORKS["solana"])
        context.user_data.update({"redeem_code": code, "redeem_usdc": amount_crypto, "redeem_network": code_network, "redeem_step": "wallet"})
        await update.message.reply_text(f"✅ কোড যাচাই সফল!\n\n🎁 পাবেন: {amount_crypto} {net_info['symbol']}\n🌐 নেটওয়ার্ক: {net_info['name']}\n\nআপনার {net_info['name']} Wallet Address দিন:\n\n📋 উদাহরণ: {wallet_hint(code_network)}")
        return

    wallet = update.message.text.strip()
    network = context.user_data.get("redeem_network", "solana")
    net_info = NETWORKS[network]
    if not valid_wallet(network, wallet):
        await update.message.reply_text(f"❌ ভুল {net_info['name']} wallet!\n\nসঠিক address দিন।")
        return
    code = context.user_data["redeem_code"]
    amount_crypto = context.user_data["redeem_usdc"]
    context.user_data.clear()
    sufficient, current_bal = check_sufficient(network, amount_crypto)
    if not sufficient and current_bal is not None:
        await update.message.reply_text(f"❌ পর্যাপ্ত stock নেই।\n\n{stock_detail(network, amount_crypto, current_bal)}")
        return
    await update.message.reply_text(f"⏳ {net_info['symbol']} পাঠানো হচ্ছে...\n\n🌐 {net_info['name']}\n💵 {amount_crypto} {net_info['symbol']}\n👛 {wallet}")
    try:
        sig = await send_crypto(network, wallet, amount_crypto)
        explorer = f"{net_info['explorer']}{sig}"
        use_code(code, user_id)
        order_id = save_transaction(f"GIFT-{code}", user_id, 0, amount_crypto, wallet, sig, "completed", network, source="gift")
        await update.message.reply_text(f"🎉 {net_info['symbol']} পাঠানো হয়েছে!\n\n{receipt_block(order_id, f'GIFT-{code}', network, amount_crypto, wallet, sig)}\n\nধন্যবাদ! 🙏")
        try:
            await update.get_bot().send_message(ADMIN_ID, f"🎁 গিফট কোড রিডিম!\n\n👤 @{username} ({user_id})\n🎟️ {code}\n🌐 {net_info['name']}\n💵 {amount_crypto} {net_info['symbol']}\n👛 {wallet}\n🔗 {explorer}")
        except Exception:
            pass
    except Exception as exc:
        await update.message.reply_text("❌ পাঠাতে সমস্যা!\n\n📞 @MdMouno")
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
        text = f"❌ Failed!\n{exc}"
    await update.message.reply_text(text)


async def setup_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔐 Wallet Setup\n\nআপনার Network বেছে নিন:\n\n⚠️ Private Key AES-256 দিয়ে encrypt হবে\n❓ গাইড: /guide", reply_markup=user_network_menu())
    return SETUP_NETWORK


async def setup_network_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "uw_cancel":
        await query.edit_message_text("❌ বাতিল হয়েছে।")
        return ConversationHandler.END
    network = query.data.replace("uw_", "")
    context.user_data["uw_network"] = network
    net_info = NETWORKS.get(network, {"name": network, "symbol": "?"})
    net_guide = NETWORK_GUIDE.get(network, "")
    await query.edit_message_text(f"✅ নেটওয়ার্ক: {net_info['name']}\n\n{net_guide}\n━━━━━━━━━━━━━━━━━━━━━\nএখন আপনার Private Key পাঠান:\n\n⚠️ Message পাঠানোর পর bot স্বয়ংক্রিয়ভাবে মুছে দেবে।")
    return SETUP_KEY


async def setup_key_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    private_key = update.message.text.strip()
    network = context.user_data.get("uw_network", "solana")
    try:
        await update.message.delete()
    except Exception:
        pass
    try:
        wallet_address = get_wallet_address(network, private_key)
    except Exception as exc:
        await update.message.reply_text(f"❌ Invalid Private Key!\n\n{exc}\n\nআবার চেষ্টা করুন:")
        return SETUP_KEY
    context.user_data["uw_private_key"] = private_key
    context.user_data["uw_wallet_address"] = wallet_address
    await update.message.reply_text(f"✅ Key যাচাই সফল!\n\n👛 {wallet_address}\n\nএখন একটি শক্তিশালী Password তৈরি করুন:\n\n• কমপক্ষে ৮ character\n• সংখ্যা ও অক্ষর মিলিয়ে দিন\n• Password ভুললে key recover হবে না!\n\nআপনার password লিখুন:")
    return SETUP_PASSWORD


async def setup_password_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    password = update.message.text.strip()
    user_id = str(update.effective_user.id)
    private_key = context.user_data.get("uw_private_key")
    network = context.user_data.get("uw_network")
    wallet_addr = context.user_data.get("uw_wallet_address")
    try:
        await update.message.delete()
    except Exception:
        pass
    if len(password) < 8:
        await update.message.reply_text("❌ Password কমপক্ষে ৮ character!\n\nআবার লিখুন:")
        return SETUP_PASSWORD
    try:
        encrypted_key, salt = encrypt_key(private_key, password)
        save_user_wallet(user_id, encrypted_key, salt, network, wallet_addr)
        context.user_data.clear()
        net_info = NETWORKS.get(network, {"name": network, "symbol": "?"})
        await update.message.reply_text(f"🎉 Wallet Setup সফল!\n\n🌐 {net_info['name']}\n👛 {wallet_addr}\n\n💰 /mybalance → Balance দেখুন\n💸 /send_wallet → Crypto পাঠান\n🔑 /changekey → Key পরিবর্তন\n🗑️ /deletekey → Key মুছুন\n📖 /guide → ব্যবহার বিধি\n\n⚠️ Password মনে রাখুন!")
    except Exception as exc:
        await update.message.reply_text(f"❌ Setup ব্যর্থ!\n{exc}")
    return ConversationHandler.END


async def mybalance_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if not get_user_wallet(user_id):
        await update.message.reply_text("❌ Wallet setup নেই!\n\nপ্রথমে: /setup")
        return
    context.user_data["uw_waiting_bal_password"] = True
    await update.message.reply_text("🔐 আপনার Password দিন:\n\n⚠️ Message পাঠানোর পর মুছে যাবে।")


async def send_wallet_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    row = get_user_wallet(user_id)
    if not row:
        await update.message.reply_text("❌ Wallet setup নেই!\n\nপ্রথমে: /setup")
        return ConversationHandler.END
    network = row[2]
    net_info = NETWORKS.get(network, {"name": network})
    await update.message.reply_text(f"💸 Crypto পাঠানো\n\n🌐 {net_info['name']}\n👛 {row[3]}\n\nDestination wallet address দিন:\n\n📋 উদাহরণ: {wallet_hint(network)}")
    return SEND_W_DEST


async def send_wallet_dest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dest = update.message.text.strip()
    user_id = str(update.effective_user.id)
    row = get_user_wallet(user_id)
    network = row[2]
    if not valid_wallet(network, dest):
        net_info = NETWORKS.get(network, {"name": network})
        await update.message.reply_text(f"❌ ভুল {net_info['name']} address!\n\nআবার দিন:")
        return SEND_W_DEST
    context.user_data["sw_dest"] = dest
    net_info = NETWORKS.get(network, {"symbol": "?"})
    await update.message.reply_text(f"✅ Destination: {dest}\n\nকত {net_info['symbol']} পাঠাবেন?\n\nশুধু সংখ্যা (যেমন: 10.5)")
    return SEND_W_AMOUNT


async def send_wallet_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = float(update.message.text.strip())
        if amount <= 0:
            raise ValueError
    except Exception:
        await update.message.reply_text("❌ ভুল পরিমাণ! সংখ্যা লিখুন:")
        return SEND_W_AMOUNT
    user_id = str(update.effective_user.id)
    row = get_user_wallet(user_id)
    network = row[2]
    net_info = NETWORKS.get(network, {"name": network, "symbol": "?"})
    dest = context.user_data.get("sw_dest")
    context.user_data["sw_amount"] = amount
    keyboard = [[InlineKeyboardButton("✅ কনফার্ম", callback_data="sw_confirm"), InlineKeyboardButton("❌ বাতিল", callback_data="sw_cancel")]]
    await update.message.reply_text(f"📊 Transaction সারসংক্ষেপ:\n\n🌐 {net_info['name']}\n💵 {amount} {net_info['symbol']}\n👛 প্রেরক: {row[3]}\n📤 প্রাপক: {dest}\n\n⚠️ Transaction irreversible!\nনিশ্চিত করুন:", reply_markup=InlineKeyboardMarkup(keyboard))
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
    await update.message.reply_text("⏳ পাঠানো হচ্ছে...")
    try:
        sig = await asyncio.get_running_loop().run_in_executor(None, lambda: send_from_user_wallet(user_id, password, dest, amount))
        save_transaction(f"WALLET-{sig[:24]}", user_id, 0, amount, dest, sig, "completed", network, source="wallet")
        context.user_data.clear()
        await update.message.reply_text(f"🎉 সফলভাবে পাঠানো হয়েছে!\n\n🌐 {net_info['name']}\n💵 {amount} {net_info['symbol']}\n📤 {dest}\n🔗 {net_info['explorer']}{sig}")
    except Exception as exc:
        context.user_data.clear()
        await update.message.reply_text("❌ ভুল Password!" if "ভুল password" in str(exc) else f"❌ পাঠাতে ব্যর্থ!\n\n{exc}\n\n❓ @MdMouno")
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
    await update.message.reply_text("✅ Stars payment received. Seller crypto delivery চলছে...")
    ok, result = await complete_seller_order(update.get_bot(), order_id, "seller_stars")
    if ok:
        await update.message.reply_text(f"🎉 Seller Stars order completed.\n🧾 {order_id}\n⭐ {stars_amount} Stars\nSeller payout ledger created for admin manual payout.")
    else:
        await update.message.reply_text(f"✅ Stars payment received, but seller crypto delivery failed/manual review দরকার।\n🧾 {order_id}")
        try:
            await update.get_bot().send_message(ADMIN_ID, f"🚨 Seller Stars delivery failed.\nOrder: {order_id}\nSeller: {seller_id}\nBuyer: {buyer_id}\nReason: {result}")
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
        explorer = f"{net_info['explorer']}{sig}"
        update_star_order_status(order_id, "completed", payment.telegram_payment_charge_id, payment.provider_payment_charge_id, sig)
        save_transaction(f"STAR-{payment.telegram_payment_charge_id}", user_id, 0, amount_crypto, wallet, sig, "completed", network, order_id=order_id, source="stars")
        consume_stock_reservation(order_id=order_id)
        await update.message.reply_text(
            f"{tr('stars_completed', lang)}\n\n"
            f"⭐ {stars_amount} Stars\n"
            f"{receipt_block(order_id, f'STAR-{payment.telegram_payment_charge_id}', network, amount_crypto, wallet, sig)}"
        )
        try:
            await update.get_bot().send_message(
                ADMIN_ID,
                f"✅ Telegram Stars order completed.\n\n"
                f"👤 @{username} ({user_id})\n"
                f"🧾 Order: {order_id}\n"
                f"🌐 {net_info['name']}\n"
                f"💵 {amount_crypto} {net_info['symbol']}\n"
                f"⭐ {stars_amount} Stars\n"
                f"👛 {wallet}\n"
                f"🔗 {explorer}",
            )
        except Exception:
            pass
    except Exception as exc:
        update_star_order_status(order_id, "failed", payment.telegram_payment_charge_id, payment.provider_payment_charge_id, error=str(exc))
        save_transaction(f"STAR-{payment.telegram_payment_charge_id}", user_id, 0, amount_crypto, wallet, "", "failed", network, order_id=order_id, source="stars")
        release_stock_reservation(order_id=order_id, reason="stars_send_failed", actor_id="system")
        add_audit("system", "stars_send_failed", "star_order", order_id, str(exc))
        await update.message.reply_text("✅ Stars payment received, but crypto sending failed. Admin has been notified.")
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
                f"❌ {exc}",
            )
        except Exception:
            pass
        logger.error("Stars order send failed: %s", exc)


async def deletekey_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if not get_user_wallet(user_id):
        await update.message.reply_text("❌ কোনো wallet নেই!")
        return ConversationHandler.END
    keyboard = [[InlineKeyboardButton("✅ হ্যাঁ, মুছে দাও", callback_data="del_confirm"), InlineKeyboardButton("❌ না", callback_data="del_cancel")]]
    await update.message.reply_text("⚠️ সতর্কতা!\n\nWallet key মুছে দেওয়া হবে।\nUndo করা যাবে না!\n\nনিশ্চিত?", reply_markup=InlineKeyboardMarkup(keyboard))
    return DEL_PASSWORD


async def deletekey_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    password = update.message.text.strip()
    user_id = str(update.effective_user.id)
    try:
        await update.message.delete()
    except Exception:
        pass
    _bal, _network, error = get_user_balance(user_id, password)
    if error == "wrong_password":
        await update.message.reply_text("❌ ভুল Password! Key মুছা হয়নি।")
        return ConversationHandler.END
    delete_user_wallet(user_id)
    await update.message.reply_text("✅ Wallet key মুছে দেওয়া হয়েছে!\n\nনতুন setup: /setup")
    return ConversationHandler.END


async def guide_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(GUIDE)


async def changekey_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    delete_user_wallet(str(update.effective_user.id))
    await update.message.reply_text("🔄 পুরনো key মুছে দেওয়া হয়েছে!\n\nনতুন wallet setup করুন:")
    return await setup_cmd(update, context)


async def process_bkash(app, text, sender, meta=None):
    parsed = parse_bkash_payment_notice(text)
    if not parsed:
        return
    if meta and meta.get("seller_token"):
        await process_seller_bkash(app, text, sender, meta)
        return
    trx_id = parsed["trx_id"]
    amount_bdt = parsed["amount_bdt"]
    touch_webhook_notice(sender, trx_id, amount_bdt)

    if trx_exists(trx_id):
        logger.info("Duplicate bKash notice ignored because transaction already exists: %s", trx_id)
        return

    already_saved = sms_exists(trx_id)
    saved_new = save_sms(trx_id, amount_bdt, sender, text)
    logger.info("bKash notice saved: %s BDT | TrxID: %s | source: %s | new: %s", amount_bdt, trx_id, sender, saved_new)

    pending = get_pending_order(trx_id)
    if pending:
        if trx_id.startswith("TEST") or str(sender).startswith("test"):
            await app.bot.send_message(ADMIN_ID, f"🧪 Test bKash notice matched pending order but auto-send was blocked.\n\nTrxID: {trx_id}\nAmount: {amount_bdt} BDT\nUse manual approve only if this is intentional.")
            return
        await complete_pending_order_from_sms(app, pending, amount_bdt)
        return

    if already_saved:
        logger.info("Duplicate bKash notice ignored because TrxID was already saved: %s", trx_id)
        return

    try:
        await app.bot.send_message(ADMIN_ID, f"💰 bKash payment notice!\n\n📩 Source: {sender}\n💵 {amount_bdt} BDT\n🔑 TrxID: {trx_id}")
    except Exception as exc:
        logger.error(exc)


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
        return

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
        return

    try:
        sig = await send_crypto(network, wallet, crypto_amount)
        explorer = f"{net_info['explorer']}{sig}"
        mark_sms_used(trx_id)
        order_id = save_transaction(trx_id, user_id, sms_amount_bdt, crypto_amount, wallet, sig, "completed", network, order_id=order_id, source="bkash")
        consume_stock_reservation(order_id=order_id, trx_id=trx_id)
        delete_pending_order(trx_id)
        await app.bot.send_message(
            int(user_id),
            f"🎉 Payment verified automatically!\n\n"
            f"{receipt_block(order_id, trx_id, network, crypto_amount, wallet, sig)}\n\n"
            "Thank you!",
        )
        await app.bot.send_message(
            ADMIN_ID,
            f"✅ Auto-completed delayed bKash order.\n\n"
            f"👤 User: {user_id}\n"
            f"🔑 TrxID: {trx_id}\n"
            f"🌐 {net_info['name']}\n"
            f"💰 {sms_amount_bdt} BDT\n"
            f"💵 {crypto_amount} {net_info['symbol']}\n"
            f"🔗 {explorer}",
        )
    except Exception as exc:
        save_transaction(trx_id, user_id, sms_amount_bdt, crypto_amount, wallet, "", "failed", network, order_id=order_id, source="bkash")
        release_stock_reservation(order_id=order_id, trx_id=trx_id, reason="auto_complete_send_failed", actor_id="system")
        add_audit("system", "auto_complete_send_failed", "transaction", trx_id, str(exc))
        await app.bot.send_message(
            ADMIN_ID,
            f"🚨 Auto-complete failed after bKash SMS verification.\n\n"
            f"👤 User: {user_id}\n🔑 TrxID: {trx_id}\n🌐 {net_info['name']}\n❌ {exc}",
        )
        logger.error("Auto-complete pending order failed: %s", exc)


def sms_handler(app, loop, text, sender, meta=None):
    asyncio.run_coroutine_threadsafe(process_bkash(app, text, sender, meta), loop)


async def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is not configured")

    request = HTTPXRequest(connection_pool_size=8, read_timeout=60, write_timeout=60, connect_timeout=60, pool_timeout=60)
    app = Application.builder().token(BOT_TOKEN).request(request).build()

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
    app.add_handler(CommandHandler("send", send_cmd))
    app.add_handler(CommandHandler("gencode", gencode_cmd))
    app.add_handler(CommandHandler("pending", pending_cmd))
    app.add_handler(CommandHandler("failed", failed_cmd))
    app.add_handler(CommandHandler("stats", stats_cmd))
    app.add_handler(CommandHandler("balances", balances_cmd))
    app.add_handler(CommandHandler("maintenance", maintenance_cmd))
    app.add_handler(CommandHandler("terms", terms_cmd))
    app.add_handler(CommandHandler("backup", backup_cmd))
    app.add_handler(CommandHandler("txlog", txlog_cmd))
    app.add_handler(CommandHandler("order", order_cmd))
    app.add_handler(CommandHandler("status", status_cmd))
    app.add_handler(CommandHandler("receipt", receipt_cmd))
    app.add_handler(CommandHandler("seller", seller_cmd))
    app.add_handler(CommandHandler("seller_center", seller_center_cmd))
    app.add_handler(CommandHandler("seller_guide", seller_guide_cmd))
    app.add_handler(CommandHandler("seller_badge", seller_badge_cmd))
    app.add_handler(CommandHandler("seller_dashboard", seller_dashboard_cmd))
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
    app.add_handler(CommandHandler("mybalance", mybalance_cmd))
    app.add_handler(CommandHandler("guide", guide_cmd))
    app.add_handler(CommandHandler("ai", ai_cmd))
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
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, waiting_trxid))

    await app.initialize()
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True)

    loop = asyncio.get_running_loop()
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
