import asyncio
import json
import logging
import math
import os
import re
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

from balance import check_sufficient, get_all_balances
from bsc_sender import send_bsc_usdt
from config import (
    ADMIN_ID,
    BKASH_NUMBER,
    BOT_TOKEN,
    AI_API_KEY,
    AI_BASE_URL,
    AI_MODEL,
    AI_PROVIDER,
    RATE,
    STAR_RATE,
    SUPPORT_USERNAME,
    GEMINI_API_KEY,
    GEMINI_MODEL,
    BSC_PRIVATE_KEY,
    POLYGON_PRIVATE_KEY,
    SOLANA_KEY,
    TRON_PRIVATE_KEY,
)
from crypto_manager import (
    delete_user_wallet,
    encrypt_key,
    get_user_balance,
    get_user_wallet,
    get_wallet_address,
    save_user_wallet,
    send_from_user_wallet,
)
from db import (
    create_code,
    delete_pending_order,
    disable_code,
    get_all_active_codes,
    get_code,
    get_network_rate,
    get_pending_order,
    get_pending_orders,
    get_recent_transactions,
    get_sms,
    get_star_order,
    get_failed_transactions,
    get_setting,
    get_transaction,
    get_transaction_stats,
    get_user_language,
    get_wallet,
    mark_sms_used,
    save_pending_order,
    save_sms,
    save_transaction,
    save_wallet,
    set_user_language,
    set_network_rate,
    set_setting,
    sms_exists,
    trx_exists,
    save_star_order,
    update_transaction,
    update_star_order_status,
    use_code,
)
from evm_sender import send_evm_token
from polygon_sender import send_polygon_usdc
from sender import send_usdc
from ton_sender import get_ton_address, send_ton
from tron_sender import send_trc20_usdt
from user_guide import GUIDE, NETWORK_GUIDE
from webhook import parse_bkash_payment_notice, parse_bkash_sms, parse_nigeria_payment_notice, run_webhook, set_callback

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
NG_SETUP_TEXT = 60
AI_SETUP_TEXT = 61

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
    "pcm": "Nigerian Pidgin 🇳🇬",
}

TEXT = {
    'choose_language': {
        "bn": '🌐 ভাষা নির্বাচন করুন\n\nআপনার পছন্দের ভাষা বেছে নিন।',
        "en": '🌐 Choose your language\n\nSelect the language you prefer.',
        "pcm": '🌐 Choose your language\n\nSelect the language wey you prefer.',
    },
    'language_saved': {"bn": '✅ ভাষা সেট করা হয়েছে।', "en": '✅ Language saved.', "pcm": '✅ Language don save.' },
    'buy': {"bn": '💱 কিনুন', "en": '💱 Buy', "pcm": '💱 Buy' },
    'gift': {"bn": '🎁 গিফট কোড', "en": '🎁 Gift Code', "pcm": '🎁 Gift Code' },
    'stars': {"bn": '⭐ Telegram Stars', "en": '⭐ Telegram Stars', "pcm": '⭐ Telegram Stars' },
    'rate': {"bn": '📊 রেট', "en": '📊 Rates', "pcm": '📊 Rates' },
    'balance': {"bn": '💰 ব্যালেন্স', "en": '💰 Balance', "pcm": '💰 Balance' },
    'txlog': {"bn": '📜 TX লগ', "en": '📜 TX Log', "pcm": '📜 TX Log' },
    'help': {"bn": '❓ সাহায্য', "en": '❓ Help', "pcm": '❓ Help' },
    'support': {"bn": '📞 Support', "en": '📞 Support', "pcm": '📞 Support' },
    'ai_support': {"bn": '🤖 AI Support', "en": '🤖 AI Support', "pcm": '🤖 AI Support' },
    'ai_setup': {"bn": '🤖 AI Setup', "en": '🤖 AI Setup', "pcm": '🤖 AI Setup' },
    'terms': {"bn": '📜 Terms', "en": '📜 Terms', "pcm": '📜 Terms' },
    'wallet': {"bn": '🔐 আমার Wallet', "en": '🔐 My Wallet', "pcm": '🔐 My Wallet' },
    'language': {"bn": '🌐 ভাষা', "en": '🌐 Language', "pcm": '🌐 Language' },
    'set_rate': {"bn": '⚙️ রেট পরিবর্তন', "en": '⚙️ Set Rates', "pcm": '⚙️ Set Rates' },
    'ng_setup': {"bn": '🇳🇬 Nigeria Pay Setup', "en": '🇳🇬 Nigeria Pay Setup', "pcm": '🇳🇬 Nigeria Pay Setup' },
    'gen_code': {"bn": '🎟️ কোড তৈরি', "en": '🎟️ Generate Code', "pcm": '🎟️ Generate Code' },
    'disable_code': {"bn": '🚫 কোড বাতিল', "en": '🚫 Disable Code', "pcm": '🚫 Disable Code' },
    'admin_send': {"bn": '🚀 Admin Send', "en": '🚀 Admin Send', "pcm": '🚀 Admin Send' },
    'back': {"bn": '🔙 ফিরে যান', "en": '🔙 Back', "pcm": '🔙 Back' },
    'cancel': {"bn": '❌ বাতিল', "en": '❌ Cancel', "pcm": '❌ Cancel' },
    'home_title': {"bn": '💱 Crypto Seller Bot', "en": '💱 Crypto Seller Bot', "pcm": '💱 Crypto Seller Bot' },
    'welcome': {"bn": 'স্বাগতম', "en": 'Welcome', "pcm": 'Welcome' },
    'current_rates': {"bn": 'বর্তমান রেট', "en": 'Current Rates', "pcm": 'Current Rates' },
    'select_action': {"bn": 'নিচের মেনু থেকে শুরু করুন 👇', "en": 'Choose an option below 👇', "pcm": 'Choose one option below 👇' },
    'select_network': {"bn": '💱 নেটওয়ার্ক বেছে নিন', "en": '💱 Select a network', "pcm": '💱 Choose network' },
    'enter_wallet': {"bn": 'আপনার {network} Wallet Address দিন', "en": 'Send your {network} wallet address', "pcm": 'Send your {network} wallet address' },
    'example': {"bn": 'উদাহরণ', "en": 'Example', "pcm": 'Example' },
    'wallet_saved': {"bn": '✅ Wallet সংরক্ষিত!', "en": '✅ Wallet saved!', "pcm": '✅ Wallet don save!' },
    'enter_amount_bdt': {"bn": 'কত টাকার {symbol} কিনতে চান?', "en": 'How many BDT of {symbol} do you want to buy?', "pcm": 'How much BDT of {symbol} you wan buy?' },
    'enter_fiat_amount': {
        "bn": 'কত fiat amount এর {symbol} কিনতে চান?\n\nপরের ধাপে bKash (BDT) বা Nigeria (NGN) বেছে নিতে পারবেন।',
        "en": 'How much fiat value of {symbol} do you want to buy?\n\nNext you can choose bKash (BDT) or Nigeria (NGN).',
        "pcm": 'How much fiat value of {symbol} you wan buy?\n\nNext step, you fit choose bKash (BDT) or Nigeria (NGN).',
    },
    'numbers_only': {"bn": 'শুধু সংখ্যা লিখুন (যেমন: 500)', "en": 'Send numbers only (example: 500)', "pcm": 'Send numbers only (example: 500)' },
    'invalid_wallet': {"bn": '❌ ভুল wallet address!', "en": '❌ Invalid wallet address!', "pcm": '❌ Wallet address no correct!' },
    'invalid_amount': {"bn": '❌ ভুল পরিমাণ! সংখ্যা লিখুন।', "en": '❌ Invalid amount. Send a number.', "pcm": '❌ Amount no correct. Send number.' },
    'confirm': {"bn": '✅ কনফার্ম', "en": '✅ Confirm', "pcm": '✅ Confirm' },
    'order_summary': {"bn": '📊 অর্ডার সারসংক্ষেপ', "en": '📊 Order Summary', "pcm": '📊 Order Summary' },
    'send_bdt': {"bn": 'পাঠাবেন', "en": 'You pay', "pcm": 'You go pay' },
    'receive_crypto': {"bn": 'পাবেন', "en": 'You receive', "pcm": 'You go receive' },
    'confirm_prompt': {"bn": 'নিশ্চিত করতে Confirm চাপুন 👇', "en": 'Tap Confirm to continue 👇', "pcm": 'Tap Confirm to continue 👇' },
    'choose_payment_method': {"bn": 'Payment method বেছে নিন 👇', "en": 'Choose payment method 👇', "pcm": 'Choose payment method 👇' },
    'bkash_payment': {"bn": '📲 bKash', "en": '📲 bKash', "pcm": '📲 bKash' },
    'nigeria_payment': {"bn": '🇳🇬 Nigerian Local Payment', "en": '🇳🇬 Nigerian Local Payment', "pcm": '🇳🇬 Nigerian Local Payment' },
    'code_select_network': {
        "bn": '🎟️ গিফট কোড তৈরি\n\n১/৩: নেটওয়ার্ক বেছে নিন',
        "en": '🎟️ Generate Gift Code\n\nStep 1/3: Select network',
        "pcm": '🎟️ Generate Gift Code\n\nStep 1/3: Choose network',
    },
    'code_select_amount': {"bn": '২/৩: কত {symbol} এর কোড তৈরি করবেন?', "en": 'Step 2/3: Choose {symbol} amount', "pcm": 'Step 2/3: Choose {symbol} amount' },
    'code_select_duration': {"bn": '৩/৩: কোডের মেয়াদ বেছে নিন', "en": 'Step 3/3: Choose expiry time', "pcm": 'Step 3/3: Choose expiry time' },
    'custom_amount': {"bn": '✏️ Custom Amount', "en": '✏️ Custom Amount', "pcm": '✏️ Custom Amount' },
    'custom_duration': {"bn": '✏️ Custom Time', "en": '✏️ Custom Time', "pcm": '✏️ Custom Time' },
    'enter_custom_amount': {"bn": 'পরিমাণ লিখুন। যেমন: 1.5', "en": 'Send the amount. Example: 1.5', "pcm": 'Send the amount. Example: 1.5' },
    'enter_custom_duration': {"bn": 'মিনিট লিখুন। যেমন: 60', "en": 'Send minutes. Example: 60', "pcm": 'Send minutes. Example: 60' },
    'code_created': {"bn": '✅ গিফট কোড তৈরি হয়েছে!', "en": '✅ Gift code generated!', "pcm": '✅ Gift code don generate!' },
    'stars_intro': {
        "bn": '⭐ Telegram Stars দিয়ে কিনুন\n\nনেটওয়ার্ক বেছে নিন।',
        "en": '⭐ Pay with Telegram Stars\n\nSelect a network.',
        "pcm": '⭐ Pay with Telegram Stars\n\nChoose network.',
    },
    'stars_enter_amount': {
        "bn": 'কত {symbol} কিনতে চান?\n\nRate: 1 {symbol} = {rate} Stars',
        "en": 'How many {symbol} do you want to buy?\n\nRate: 1 {symbol} = {rate} Stars',
        "pcm": 'How many {symbol} you wan buy?\n\nRate: 1 {symbol} = {rate} Stars',
    },
    'stars_invoice_title': {"bn": 'Crypto Order', "en": 'Crypto Order', "pcm": 'Crypto Order' },
    'stars_invoice_description': {"bn": '{amount} {symbol} on {network}', "en": '{amount} {symbol} on {network}', "pcm": '{amount} {symbol} on {network}' },
    'stars_pay_prompt': {"bn": 'Invoice পাঠানো হয়েছে। Telegram Stars দিয়ে payment complete করুন।', "en": 'Invoice sent. Complete payment with Telegram Stars.', "pcm": 'Invoice don send. Complete payment with Telegram Stars.' },
    'stars_paid_sending': {"bn": '✅ Stars payment received. Crypto পাঠানো হচ্ছে...', "en": '✅ Stars payment received. Sending crypto...', "pcm": '✅ Stars payment don enter. Crypto dey send...' },
    'stars_completed': {"bn": '🎉 Stars payment verified এবং crypto পাঠানো হয়েছে!', "en": '🎉 Stars payment verified and crypto sent!', "pcm": '🎉 Stars payment verified and crypto don send!' },
    'admin_send_intro': {
        "bn": '🚀 Admin Send\n\nকোন network থেকে asset পাঠাবেন?',
        "en": '🚀 Admin Send\n\nSelect the network to send from.',
        "pcm": '🚀 Admin Send\n\nChoose network to send from.',
    },
    'admin_send_wallet': {"bn": 'Destination wallet address দিন', "en": 'Send destination wallet address', "pcm": 'Send destination wallet address' },
    'admin_send_amount': {"bn": 'কত {symbol} পাঠাবেন?', "en": 'How many {symbol} do you want to send?', "pcm": 'How many {symbol} you wan send?' },
    'admin_send_confirm': {"bn": 'নিশ্চিত করলে asset পাঠানো হবে।', "en": 'Confirm to send the asset.', "pcm": 'Confirm to send the asset.' },
    'admin_send_done': {"bn": '✅ Admin transfer complete!', "en": '✅ Admin transfer complete!', "pcm": '✅ Admin transfer complete!' },
    'maintenance_on': {"bn": '🛑 Maintenance mode ON', "en": '🛑 Maintenance mode ON', "pcm": '🛑 Maintenance mode ON' },
    'maintenance_off': {"bn": '✅ Maintenance mode OFF', "en": '✅ Maintenance mode OFF', "pcm": '✅ Maintenance mode OFF' },
    'ai_support_intro': {
        "bn": '🤖 AI Support\n\nআপনার প্রশ্ন লিখুন। Payment, wallet, network, bKash, Stars বা order problem সম্পর্কে সাহায্য করতে পারি।\n\nবন্ধ করতে /cancel লিখুন।',
        "en": '🤖 AI Support\n\nSend your question. I can help with payment, wallet, network, bKash, Stars, or order issues.\n\nSend /cancel to close.',
        "pcm": '🤖 AI Support\n\nSend your question. I fit help with payment, wallet, network, bKash, Stars, or order issue.\n\nSend /cancel to close.',
    },
    'ai_unavailable': {"bn": '❌ AI Support এখন unavailable. Admin-কে জানান।', "en": '❌ AI Support is unavailable. Please contact admin.', "pcm": '❌ AI Support no dey available now. Please contact admin.' },
    'ai_thinking': {"bn": '🤖 উত্তর তৈরি করছি...', "en": '🤖 Thinking...', "pcm": '🤖 I dey think...' },
    'ai_setup_saved': {"bn": '✅ AI setting saved.', "en": '✅ AI setting saved.', "pcm": '✅ AI setting don save.' },
    'ai_setup_prompt_key': {"bn": 'Send AI API key. Message will be deleted after saving.', "en": 'Send AI API key. Message will be deleted after saving.', "pcm": 'Send AI API key. Message go delete after e save.' },
    'ai_setup_prompt_model': {"bn": 'Send AI model name. Example: openai/gpt-4o-mini', "en": 'Send AI model name. Example: openai/gpt-4o-mini', "pcm": 'Send AI model name. Example: openai/gpt-4o-mini' },
    'ai_setup_prompt_base_url': {"bn": 'Send OpenAI-compatible base URL. Example: https://openrouter.ai/api/v1/chat/completions', "en": 'Send OpenAI-compatible base URL. Example: https://openrouter.ai/api/v1/chat/completions', "pcm": 'Send OpenAI-compatible base URL. Example: https://openrouter.ai/api/v1/chat/completions' },
    'ai_test_running': {"bn": '🤖 Testing AI setup...', "en": '🤖 Testing AI setup...', "pcm": '🤖 Testing AI setup...' },
    'ai_test_ok': {"bn": '✅ AI test successful.', "en": '✅ AI test successful.', "pcm": '✅ AI test successful.' },
    'ai_test_failed': {"bn": '❌ AI test failed: {error}', "en": '❌ AI test failed: {error}', "pcm": '❌ AI test fail: {error}' },
}


def is_admin(user_id) -> bool:
    return str(user_id) == str(ADMIN_ID)


def is_maintenance_enabled():
    return get_setting("maintenance_mode", "off") == "on"


def lang_text(lang, bn, en, pcm=None):
    if lang == "en":
        return en
    if lang == "pcm":
        return pcm if pcm is not None else en
    return bn


def maintenance_message(lang="bn"):
    return lang_text(
        lang,
        "🛑 Maintenance চলছে। অর্ডার সাময়িকভাবে বন্ধ আছে। কিছুক্ষণ পর চেষ্টা করুন।",
        "🛑 Orders are temporarily paused for maintenance. Please try again later.",
        "🛑 Orders dey paused for maintenance now. Try again later.",
    )


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
    return lang_text(
        lang,
        f"⚠️ Sender wallet-এ gas/fee এর জন্য পর্যাপ্ত {native} থাকতে হবে। ভুল network transfer ফেরত আনা যায় না।",
        f"⚠️ Make sure the sender wallet has enough {native} for network gas/fees. Wrong network transfers cannot be reversed.",
        f"⚠️ Make sure sender wallet get enough {native} for network gas/fees. Wrong network transfer no fit reverse.",
    )


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
    if lang == "pcm":
        return (
            "📜 Terms & Risk Warning\n\n"
            "• Always choose correct network.\n"
            "• Wrong wallet/network transfer no fit reverse.\n"
            "• Keep enough native gas token for wallet sends.\n"
            "• Payment fit need manual review if bKash/Nigeria notification delay or amount no match.\n"
            "• Contact support if payment stuck."
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
    if lang == "bn":
        reply_language = "Reply in Bengali."
    elif lang == "pcm":
        reply_language = "Reply in Nigerian Pidgin."
    else:
        reply_language = "Reply in English."
    return (
        "You are the read-only AI support assistant for a Telegram crypto seller bot. "
        f"{reply_language} "
        "Keep replies short, practical, and beginner-friendly. "
        "You can explain bKash payment verification, Nigerian local payment/reference issues, app/SMS notification delays, Telegram Stars payments, wallet/network selection, gas fees, order IDs, pending orders, gift codes, connected wallets, and contacting admin. "
        "Never approve payments, never claim a transaction is paid unless the bot/admin verified it, never send crypto, never ask for private keys, never reveal secrets, and never tell users to share seed phrases/private keys. "
        "If user reports stuck payment, ask them for TrxID/order ID and tell them admin may verify through /pending. "
        "Support contact is @" + SUPPORT_USERNAME.lstrip("@") + "."
    )


OPENAI_COMPATIBLE_DEFAULT_URLS = {
    "openrouter": "https://openrouter.ai/api/v1/chat/completions",
    "openai": "https://api.openai.com/v1/chat/completions",
}
DEFAULT_AI_MODELS = {
    "openrouter": "openai/gpt-4o-mini",
    "openai": "gpt-4o-mini",
    "gemini": GEMINI_MODEL,
}
AI_PROVIDER_CHOICES = {"openrouter", "openai", "gemini", "off"}


def _setting_or_env(setting_key, env_value=""):
    value = get_setting(setting_key, None)
    if value is not None and str(value).strip():
        return str(value).strip()
    return str(env_value or "").strip()


def get_ai_config():
    provider = _setting_or_env("ai_provider", AI_PROVIDER).lower()
    if not provider:
        provider = "gemini" if GEMINI_API_KEY else "openrouter"
    if provider not in AI_PROVIDER_CHOICES:
        raise RuntimeError(f"Unsupported AI provider: {provider}")
    if provider == "off":
        return {"provider": "off", "api_key": "", "model": "", "base_url": "", "enabled": False}

    if provider == "gemini":
        api_key = _setting_or_env("ai_api_key", AI_API_KEY or GEMINI_API_KEY)
        model = _setting_or_env("ai_model", AI_MODEL or GEMINI_MODEL) or GEMINI_MODEL
        base_url = ""
    else:
        api_key = _setting_or_env("ai_api_key", AI_API_KEY)
        model = _setting_or_env("ai_model", AI_MODEL) or DEFAULT_AI_MODELS[provider]
        base_url = _setting_or_env("ai_base_url", AI_BASE_URL) or OPENAI_COMPATIBLE_DEFAULT_URLS[provider]
    return {"provider": provider, "api_key": api_key, "model": model, "base_url": base_url, "enabled": bool(api_key and model)}


def validate_ai_config(config):
    provider = config.get("provider")
    if provider == "off":
        raise RuntimeError("AI provider is off")
    if provider not in {"openrouter", "openai", "gemini"}:
        raise RuntimeError(f"Unsupported AI provider: {provider}")
    if not config.get("api_key"):
        raise RuntimeError(f"AI API key is not configured for {provider}")
    if not config.get("model"):
        raise RuntimeError(f"AI model is not configured for {provider}")
    if provider in {"openrouter", "openai"} and not config.get("base_url"):
        raise RuntimeError(f"AI base URL is not configured for {provider}")


def parse_openai_compatible_response(data):
    choices = data.get("choices") or []
    if not choices:
        raise RuntimeError("No AI response returned")
    message = choices[0].get("message") or {}
    content = message.get("content", "")
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict):
                parts.append(item.get("text") or item.get("content") or "")
            else:
                parts.append(str(item))
        content = "".join(parts)
    text = str(content or "").strip()
    if not text:
        raise RuntimeError("Empty AI response returned")
    return text


def call_openai_compatible(config, question, lang="bn"):
    headers = {
        "Authorization": f"Bearer {config['api_key']}",
        "Content-Type": "application/json",
    }
    if config["provider"] == "openrouter":
        headers["X-Title"] = "Mouno Private Telegram Bot"
        referer = os.getenv("OPENROUTER_HTTP_REFERER", "").strip()
        if referer:
            headers["HTTP-Referer"] = referer
    payload = {
        "model": config["model"],
        "messages": [
            {"role": "system", "content": ai_support_prompt(lang)},
            {"role": "user", "content": str(question)[:3000]},
        ],
        "temperature": 0.3,
        "max_tokens": 500,
    }
    response = requests.post(config["base_url"], headers=headers, json=payload, timeout=30)
    if response.status_code >= 400:
        try:
            message = response.json().get("error", {}).get("message") or response.text[:300]
        except Exception:
            message = response.text[:300]
        raise RuntimeError(f"{config['provider']} API error {response.status_code}: {message}")
    return parse_openai_compatible_response(response.json())


def call_gemini(config, question, lang="bn"):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{config['model']}:generateContent"
    payload = {
        "systemInstruction": {"parts": [{"text": ai_support_prompt(lang)}]},
        "contents": [{"role": "user", "parts": [{"text": str(question)[:3000]}]}],
        "generationConfig": {"temperature": 0.3, "maxOutputTokens": 500},
    }
    response = requests.post(url, params={"key": config["api_key"]}, json=payload, timeout=30)
    if response.status_code >= 400:
        try:
            message = response.json().get("error", {}).get("message") or response.text[:300]
        except Exception:
            message = response.text[:300]
        raise RuntimeError(f"gemini API error {response.status_code}: {message}")
    data = response.json()
    candidates = data.get("candidates", [])
    if not candidates:
        raise RuntimeError("No AI response returned")
    parts = candidates[0].get("content", {}).get("parts", [])
    text = "".join(part.get("text", "") for part in parts).strip()
    if not text:
        raise RuntimeError("Empty AI response returned")
    return text


def ask_ai_support(question, lang="bn"):
    config = get_ai_config()
    validate_ai_config(config)
    if config["provider"] in {"openrouter", "openai"}:
        return call_openai_compatible(config, question, lang)
    if config["provider"] == "gemini":
        return call_gemini(config, question, lang)
    raise RuntimeError(f"Unsupported AI provider: {config['provider']}")


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
            [InlineKeyboardButton("বাংলা 🇧🇩", callback_data="set_lang_bn"), InlineKeyboardButton("English 🇺🇸", callback_data="set_lang_en")],
            [InlineKeyboardButton("Nigerian Pidgin 🇳🇬", callback_data="set_lang_pcm")],
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


def get_ngn_rate(network="solana"):
    value = get_setting(f"ngn_rate_{network}")
    try:
        return float(value) if value else None
    except (TypeError, ValueError):
        return None


def is_nigeria_enabled():
    return get_setting("ng_enabled", "off") == "on"


def nigeria_configured(network=None):
    required = ["ng_provider", "ng_account", "ng_holder", "ng_bank"]
    if any(not get_setting(key, "").strip() for key in required):
        return False
    if network and not get_ngn_rate(network):
        return False
    return is_nigeria_enabled()


def mask_secret(value):
    if not value:
        return "Not set"
    value = str(value)
    if len(value) <= 8:
        return value[:1] + "***" + value[-1:]
    return value[:4] + "***" + value[-4:]


def ai_config_text(lang="bn"):
    try:
        config = get_ai_config()
        error = ""
    except Exception as exc:
        config = {"provider": _setting_or_env("ai_provider", AI_PROVIDER) or "openrouter", "api_key": "", "model": "", "base_url": "", "enabled": False}
        error = str(exc)
    provider = config.get("provider") or "openrouter"
    api_key = config.get("api_key") or ""
    model = config.get("model") or "Not set"
    base_url = config.get("base_url") or "Default/Not used"
    status = "OFF" if provider == "off" else ("READY" if config.get("enabled") else "NEEDS SETUP")
    source_key = get_setting("ai_api_key", "")
    key_source = "bot setting" if source_key else ("environment" if api_key else "not set")
    lines = [
        "🤖 AI Setup",
        DIVIDER,
        f"Status: {status}",
        f"Provider: {provider}",
        f"Model: {model}",
        f"API key: {mask_secret(api_key)} ({key_source})",
        f"Base URL: {base_url}",
        "",
        "Priority: bot app_settings → .env fallback.",
        "Use Test AI after changing provider/key/model.",
    ]
    if error:
        lines.append(f"Error: {error}")
    return "\n".join(lines)


def ai_setup_keyboard(lang="bn"):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("OpenRouter", callback_data="ai_provider_openrouter"), InlineKeyboardButton("OpenAI", callback_data="ai_provider_openai")],
        [InlineKeyboardButton("Gemini", callback_data="ai_provider_gemini"), InlineKeyboardButton("Off", callback_data="ai_provider_off")],
        [InlineKeyboardButton("🔐 Set API key", callback_data="ai_set_key"), InlineKeyboardButton("🧠 Set model", callback_data="ai_set_model")],
        [InlineKeyboardButton("🌐 Set base URL", callback_data="ai_set_base_url"), InlineKeyboardButton("🧹 Clear base URL", callback_data="ai_clear_base_url")],
        [InlineKeyboardButton("🧪 Test AI", callback_data="ai_test"), InlineKeyboardButton(tr("back", lang), callback_data="back")],
    ])


def ng_reference_key(reference):
    ref = re.sub(r"[^A-Za-z0-9-]", "", str(reference).strip().upper())
    if ref.startswith("NGN-"):
        return ref
    return f"NGN-{ref}"


def display_reference(trx_id):
    return trx_id[4:] if str(trx_id).startswith("NGN-") else trx_id


def payment_meta(trx_id):
    if str(trx_id).startswith("NGN-"):
        return {"method": "🇳🇬 Nigerian local payment", "currency": "NGN", "id_label": "Reference/Session ID", "verify": "Verify in Nigerian provider/bank app"}
    return {"method": "📲 bKash", "currency": "BDT", "id_label": "TrxID", "verify": "Verify in bKash app"}


def nigeria_config_text():
    lines = [
        "🇳🇬 Nigeria Pay Setup",
        DIVIDER,
        f"Status: {'ON' if is_nigeria_enabled() else 'OFF'}",
        f"Provider: {get_setting('ng_provider', 'Not set')}",
        f"Bank/Wallet: {get_setting('ng_bank', 'Not set')}",
        f"Holder: {get_setting('ng_holder', 'Not set')}",
        f"Account/Phone: {get_setting('ng_account', 'Not set')}",
        f"Webhook secret/token: {mask_secret(get_setting('ng_secret', ''))}",
        "",
        "NGN rates:",
    ]
    for network, info in NETWORKS.items():
        rate = get_ngn_rate(network)
        lines.append(f"• {info['name']}: {rate or 'not set'} NGN / 1 {info['symbol']}")
    return "\n".join(lines)


def nigeria_setup_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Enable", callback_data="ng_enable"), InlineKeyboardButton("⛔ Disable", callback_data="ng_disable")],
        [InlineKeyboardButton("🏦 Provider", callback_data="ng_provider_menu"), InlineKeyboardButton("📱 Account/Phone", callback_data="ng_set_account")],
        [InlineKeyboardButton("👤 Holder Name", callback_data="ng_set_holder"), InlineKeyboardButton("🏛️ Bank/Wallet", callback_data="ng_set_bank")],
        [InlineKeyboardButton("🔐 Optional Secret", callback_data="ng_set_secret"), InlineKeyboardButton("💱 NGN Rates", callback_data="ng_rates_menu")],
        [InlineKeyboardButton("👁️ View Config", callback_data="ng_view"), InlineKeyboardButton("🔙 Back", callback_data="back")],
    ])


def nigeria_provider_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("OPay", callback_data="ng_provider_OPay"), InlineKeyboardButton("PalmPay", callback_data="ng_provider_PalmPay")],
        [InlineKeyboardButton("Moniepoint", callback_data="ng_provider_Moniepoint"), InlineKeyboardButton("Bank Transfer", callback_data="ng_provider_Bank Transfer")],
        [InlineKeyboardButton("Other", callback_data="ng_provider_other")],
        [InlineKeyboardButton("🔙 Back", callback_data="ng_setup")],
    ])


def nigeria_rates_keyboard():
    rows = []
    items = list(NETWORKS.items())
    for idx in range(0, len(items), 2):
        row = []
        for network, info in items[idx:idx + 2]:
            row.append(InlineKeyboardButton(info["name"].split()[0], callback_data=f"ng_rate_{network}"))
        rows.append(row)
    rows.append([InlineKeyboardButton("🔙 Back", callback_data="ng_setup")])
    return InlineKeyboardMarkup(rows)


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


PIDGIN_GUIDE = """
╔══════════════════════════════╗
║   📖 User Guide              ║
╚══════════════════════════════╝

You fit use your own crypto wallet to send USDC/USDT safely from this bot.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔐 SETUP
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Tap My Wallet or send /setup
2. Choose network
3. Send your private key. Bot go delete the message and store only encrypted key.
4. Create strong password. If you forget password, key no fit recover.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💰 BALANCE / SEND
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

/mybalance → check wallet balance with password
/send_wallet → send crypto from your wallet

Always confirm destination wallet, network, amount, and gas token before sending. Transactions no fit reverse.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎁 GIFT CODE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

My Wallet → 🎁 Generate Gift Code
Choose amount and expiry, confirm, then enter wallet password. Funds go move to bot escrow and code fit be redeemed once.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📞 Support
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@MdMouno
"""


def guide_text(lang="bn"):
    return PIDGIN_GUIDE if lang == "pcm" else GUIDE


def network_guide_text(network, lang="bn"):
    if lang == "pcm":
        net_info = NETWORKS.get(network, {"name": network, "symbol": "?"})
        return (
            f"🌐 {net_info['name']} Network Guide:\n"
            f"• Token: {net_info['symbol']}\n"
            f"• Use the correct private key and wallet for this network.\n"
            f"• Keep native gas token for fees.\n"
            f"• Wrong network transfer no fit reverse."
        )
    return NETWORK_GUIDE.get(network, "")


def valid_wallet(network, wallet):
    if network == "solana":
        return 32 <= len(wallet) <= 44
    if network == "trc20":
        return wallet.startswith("T") and len(wallet) == 34
    if network == "ton":
        return (wallet.startswith("UQ") or wallet.startswith("EQ")) and 48 <= len(wallet) <= 60
    return wallet.startswith("0x") and len(wallet) == 42


def main_menu(user_id, lang=None):
    lang = lang or user_lang(user_id)
    keyboard = [
        [InlineKeyboardButton(tr("buy", lang), callback_data="buy"), InlineKeyboardButton(tr("stars", lang), callback_data="star_buy")],
        [InlineKeyboardButton(tr("gift", lang), callback_data="redeem_menu"), InlineKeyboardButton(tr("rate", lang), callback_data="rate")],
        [InlineKeyboardButton(tr("balance", lang), callback_data="balance"), InlineKeyboardButton(tr("txlog", lang), callback_data="txlog")],
        [InlineKeyboardButton(tr("wallet", lang), callback_data="my_wallet_menu"), InlineKeyboardButton(tr("ai_support", lang), callback_data="ai_support")],
        [InlineKeyboardButton(tr("support", lang), url=f"https://t.me/{SUPPORT_USERNAME.lstrip('@')}")],
        [InlineKeyboardButton(tr("terms", lang), callback_data="terms"), InlineKeyboardButton(tr("language", lang), callback_data="language_menu")],
    ]
    if is_admin(user_id):
        keyboard.append([InlineKeyboardButton(tr("set_rate", lang), callback_data="setrate_menu"), InlineKeyboardButton(tr("gen_code", lang), callback_data="gencode_menu")])
        keyboard.append([InlineKeyboardButton(tr("admin_send", lang), callback_data="admin_send"), InlineKeyboardButton(tr("disable_code", lang), callback_data="disable_code_menu")])
        keyboard.append([InlineKeyboardButton(tr("ng_setup", lang), callback_data="ng_setup"), InlineKeyboardButton(tr("ai_setup", lang), callback_data="ai_setup")])
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
    greeting = f"👋 {tr('welcome', lang)}, {user_name}!" if user_name else f"👋 {tr('welcome', lang)}!"
    subtitle = lang_text(lang, "দ্রুত • নিরাপদ • Multi-chain", "Fast • Secure • Multi-chain", "Fast • Secure • Multi-chain")
    body = (
        f"{greeting}\n"
        f"⚡ {subtitle}\n\n"
        f"{rates_text(lang=lang)}\n{DIVIDER}\n"
        f"📲 bKash: `{BKASH_NUMBER}`\n"
        f"🇳🇬 Nigeria Pay: {'ON' if is_nigeria_enabled() else 'OFF'}\n"
        f"🛡️ {lang_text(lang, 'Payment করার আগে network ও wallet যাচাই করুন।', 'Always check network and wallet before payment.', 'Always check network and wallet before payment.')}\n\n"
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


def get_admin_escrow_wallet(network):
    try:
        if network == "solana":
            if not SOLANA_KEY:
                return None, "SOLANA_KEY is not configured"
            return get_wallet_address("solana", SOLANA_KEY), None
        if network == "polygon":
            if not POLYGON_PRIVATE_KEY:
                return None, "POLYGON_PRIVATE_KEY is not configured"
            return get_wallet_address("polygon", POLYGON_PRIVATE_KEY), None
        if network in {"bsc", "avalanche", "ethereum", "ethereum_usdc", "base"}:
            if not BSC_PRIVATE_KEY:
                return None, "BSC_PRIVATE_KEY is not configured"
            return get_wallet_address(network, BSC_PRIVATE_KEY), None
        if network == "trc20":
            if not TRON_PRIVATE_KEY:
                return None, "TRON_PRIVATE_KEY is not configured"
            return get_wallet_address("trc20", TRON_PRIVATE_KEY), None
        if network == "ton":
            return get_ton_address(), None
        return None, f"Unsupported network: {network}"
    except Exception as exc:
        return None, str(exc)


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
            panel("📊 Rates", f"{rates_text('', lang)}\n{DIVIDER}\n📲 bKash: `{BKASH_NUMBER}`\n⚡ {lang_text(lang, 'সাধারণত ১-৩ মিনিটে পাঠানো হয়', 'Delivery: usually 1-3 minutes', 'Delivery: usually 1-3 minutes')}"),
            reply_markup=back_keyboard(lang),
        )

    elif query.data == "terms":
        await query.edit_message_text(terms_text(lang), reply_markup=back_keyboard(lang))

    elif query.data == "ai_support":
        context.user_data.clear()
        context.user_data["ai_support"] = True
        await query.edit_message_text(tr("ai_support_intro", lang), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(tr("cancel", lang), callback_data="ai_support_cancel")]]))

    elif query.data == "ai_support_cancel":
        context.user_data.clear()
        await query.edit_message_text(home_text(lang=lang), reply_markup=main_menu(user_id, lang))

    elif query.data == "ai_setup":
        if not is_admin(user_id):
            return ConversationHandler.END
        context.user_data.clear()
        await query.edit_message_text(ai_config_text(lang), reply_markup=ai_setup_keyboard(lang))

    elif query.data.startswith("ai_provider_"):
        if not is_admin(user_id):
            return ConversationHandler.END
        provider = query.data.replace("ai_provider_", "", 1)
        if provider not in AI_PROVIDER_CHOICES:
            await query.edit_message_text(f"Unsupported provider: {provider}", reply_markup=ai_setup_keyboard(lang))
            return ConversationHandler.END
        set_setting("ai_provider", provider)
        await query.edit_message_text(ai_config_text(lang), reply_markup=ai_setup_keyboard(lang))

    elif query.data in {"ai_set_key", "ai_set_model", "ai_set_base_url"}:
        if not is_admin(user_id):
            return ConversationHandler.END
        step = query.data.replace("ai_set_", "", 1)
        context.user_data["ai_setup_step"] = step
        prompt_key = {"key": "ai_setup_prompt_key", "model": "ai_setup_prompt_model", "base_url": "ai_setup_prompt_base_url"}[step]
        await query.edit_message_text(tr(prompt_key, lang), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(tr("cancel", lang), callback_data="ai_setup")]]))
        return AI_SETUP_TEXT

    elif query.data == "ai_clear_base_url":
        if not is_admin(user_id):
            return ConversationHandler.END
        set_setting("ai_base_url", "")
        await query.edit_message_text(ai_config_text(lang), reply_markup=ai_setup_keyboard(lang))

    elif query.data == "ai_test":
        if not is_admin(user_id):
            return ConversationHandler.END
        await query.edit_message_text(tr("ai_test_running", lang), reply_markup=ai_setup_keyboard(lang))
        try:
            answer = await asyncio.get_running_loop().run_in_executor(None, lambda: ask_ai_support("Reply with a short successful AI setup test confirmation.", lang))
            preview = answer[:500]
            await query.edit_message_text(f"{tr('ai_test_ok', lang)}\n\n{preview}", reply_markup=ai_setup_keyboard(lang))
        except Exception as exc:
            await query.edit_message_text(tr("ai_test_failed", lang, error=str(exc)[:500]), reply_markup=ai_setup_keyboard(lang))

    elif query.data == "ng_setup":
        if not is_admin(user_id):
            return ConversationHandler.END
        context.user_data.clear()
        await query.edit_message_text(nigeria_config_text(), reply_markup=nigeria_setup_keyboard())

    elif query.data == "ng_view":
        if not is_admin(user_id):
            return ConversationHandler.END
        await query.edit_message_text(nigeria_config_text(), reply_markup=nigeria_setup_keyboard())

    elif query.data == "ng_enable":
        if not is_admin(user_id):
            return ConversationHandler.END
        set_setting("ng_enabled", "on")
        await query.edit_message_text(nigeria_config_text(), reply_markup=nigeria_setup_keyboard())

    elif query.data == "ng_disable":
        if not is_admin(user_id):
            return ConversationHandler.END
        set_setting("ng_enabled", "off")
        await query.edit_message_text(nigeria_config_text(), reply_markup=nigeria_setup_keyboard())

    elif query.data == "ng_provider_menu":
        if not is_admin(user_id):
            return ConversationHandler.END
        await query.edit_message_text("Choose Nigeria provider/channel:", reply_markup=nigeria_provider_keyboard())

    elif query.data.startswith("ng_provider_"):
        if not is_admin(user_id):
            return ConversationHandler.END
        provider = query.data.replace("ng_provider_", "", 1)
        if provider == "other":
            context.user_data["ng_setup_step"] = "provider"
            await query.edit_message_text("Send provider/channel name (example: Kuda, GTBank, POS transfer).", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="ng_setup")]]))
            return NG_SETUP_TEXT
        set_setting("ng_provider", provider)
        await query.edit_message_text(nigeria_config_text(), reply_markup=nigeria_setup_keyboard())

    elif query.data in {"ng_set_account", "ng_set_holder", "ng_set_bank", "ng_set_secret"}:
        if not is_admin(user_id):
            return ConversationHandler.END
        step = query.data.replace("ng_set_", "", 1)
        context.user_data["ng_setup_step"] = step
        prompts = {
            "account": "Send receiving account number / phone number.",
            "holder": "Send account holder / receiver name.",
            "bank": "Send bank name or wallet name.",
            "secret": "Send optional webhook secret/API key/token, or tap Skip.",
        }
        keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data="ng_setup")]]
        if step == "secret":
            keyboard.insert(0, [InlineKeyboardButton("⏭️ Skip / Clear", callback_data="ng_secret_skip")])
        await query.edit_message_text(prompts[step], reply_markup=InlineKeyboardMarkup(keyboard))
        return NG_SETUP_TEXT

    elif query.data == "ng_secret_skip":
        if not is_admin(user_id):
            return ConversationHandler.END
        set_setting("ng_secret", "")
        context.user_data.pop("ng_setup_step", None)
        await query.edit_message_text(nigeria_config_text(), reply_markup=nigeria_setup_keyboard())

    elif query.data == "ng_rates_menu":
        if not is_admin(user_id):
            return ConversationHandler.END
        await query.edit_message_text("Select network to set NGN rate:", reply_markup=nigeria_rates_keyboard())

    elif query.data.startswith("ng_rate_"):
        if not is_admin(user_id):
            return ConversationHandler.END
        network = query.data.replace("ng_rate_", "", 1)
        context.user_data["ng_setup_step"] = "rate"
        context.user_data["ng_rate_network"] = network
        ni = NETWORKS[network]
        await query.edit_message_text(f"Send NGN rate for {ni['name']}.\n\nExample: if 1 {ni['symbol']} costs ₦1500, send 1500.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="ng_setup")]]))
        return NG_SETUP_TEXT

    elif query.data == "balance":
        await query.edit_message_text(lang_text(lang, "⏳ ব্যালেন্স লোড হচ্ছে...", "⏳ Loading balance...", "⏳ Balance dey load..."), reply_markup=back_keyboard(lang))
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
            msg = f"{lang_text(lang, '❌ ব্যালেন্স লোড ব্যর্থ!', '❌ Balance load failed!', '❌ Balance no load!')}\n{exc}"
        await query.edit_message_text(
            msg,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(lang_text(lang, "🔄 রিফ্রেশ", "🔄 Refresh", "🔄 Refresh"), callback_data="balance")], [InlineKeyboardButton(tr("back", lang), callback_data="back")]]),
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
        await show_my_wallet_menu(query, user_id, lang)

    elif query.data in {"mw_setup", "mw_change"}:
        if query.data == "mw_change":
            delete_user_wallet(user_id)
        context.user_data.clear()
        await query.edit_message_text(lang_text(lang, "🔐 Wallet Setup\n\nআপনার Network বেছে নিন:", "🔐 Wallet Setup\n\nChoose your network:", "🔐 Wallet Setup\n\nChoose your network:"), reply_markup=user_network_menu())
        return SETUP_NETWORK

    elif query.data == "mw_send":
        row = get_user_wallet(user_id)
        if not row:
            await query.edit_message_text(lang_text(lang, "❌ Wallet নেই! আগে setup করুন।", "❌ No wallet! Set up wallet first.", "❌ No wallet! Set up wallet first."))
            return ConversationHandler.END
        network = row[2]
        net_info = NETWORKS.get(network, {"name": network})
        await query.edit_message_text(lang_text(lang, f"💸 Crypto পাঠানো\n\n🌐 Network: {net_info['name']}\n👛 আপনার address: {row[3]}\n\nDestination wallet address দিন:\n📋 উদাহরণ: {wallet_hint(network)}", f"💸 Send Crypto\n\n🌐 Network: {net_info['name']}\n👛 Your address: {row[3]}\n\nSend destination wallet address:\n📋 Example: {wallet_hint(network)}", f"💸 Send Crypto\n\n🌐 Network: {net_info['name']}\n👛 Your address: {row[3]}\n\nSend destination wallet address:\n📋 Example: {wallet_hint(network)}"))
        return SEND_W_DEST

    elif query.data == "uw_gencode_menu":
        await start_user_gencode(query, context, user_id, username, lang)

    elif query.data.startswith("uw_gc_amount_"):
        await select_user_gencode_amount(query, context, user_id, lang)

    elif query.data.startswith("uw_gc_duration_"):
        await select_user_gencode_duration(query, context, user_id, lang)

    elif query.data == "uw_gc_back_amount":
        await show_user_gencode_amount_step(query, context, user_id, lang)

    elif query.data == "uw_gc_confirm":
        await ask_user_gencode_password(query, context, user_id, lang)

    elif query.data == "uw_gc_cancel":
        context.user_data.clear()
        await query.edit_message_text(lang_text(lang, "❌ Gift code তৈরি বাতিল হয়েছে।", "❌ Gift code creation cancelled.", "❌ Gift code creation cancel."), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(tr("back", lang), callback_data="my_wallet_menu")]]))

    elif query.data == "mw_delete":
        await query.edit_message_text(
            lang_text(lang, "⚠️ সতর্কতা!\n\nWallet key মুছে দেওয়া হবে।\nUndo করা যাবে না!\n\nনিশ্চিত?", "⚠️ Warning!\n\nWallet key will be deleted.\nThis cannot be undone.\n\nConfirm?", "⚠️ Warning!\n\nWallet key go delete.\nYou no fit undo am.\n\nConfirm?"),
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(lang_text(lang, "✅ হ্যাঁ, মুছে দাও", "✅ Yes, delete", "✅ Yes, delete"), callback_data="del_confirm"), InlineKeyboardButton(lang_text(lang, "❌ না", "❌ No", "❌ No"), callback_data="my_wallet_menu")]]),
        )

    elif query.data == "show_guide":
        await query.edit_message_text(guide_text(lang), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(tr("back", lang), callback_data="my_wallet_menu")]]))

    elif query.data == "check_mybal":
        context.user_data["uw_waiting_bal_password"] = True
        await query.edit_message_text(lang_text(lang, "🔐 আপনার Password দিন:\n\n⚠️ Message পাঠানোর পর মুছে যাবে।", "🔐 Send your password:\n\n⚠️ Message will be deleted after you send it.", "🔐 Send your password:\n\n⚠️ Message go delete after you send am."))

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
        await query.edit_message_text(tr("maintenance_on", lang), reply_markup=back_keyboard(lang))

    elif query.data == "maintenance_off":
        if not is_admin(user_id):
            return ConversationHandler.END
        set_setting("maintenance_mode", "off")
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
        await query.edit_message_text(lang_text(lang, "❌ বাতিল হয়েছে।", "❌ Cancelled.", "❌ Cancelled."), reply_markup=back_keyboard(lang))
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
        await show_payment_method_menu(query, context, user_id)

    elif query.data == "pay_bkash":
        await confirm_buy(query, context, user_id, username, "bkash")

    elif query.data == "pay_nigeria":
        await confirm_buy(query, context, user_id, username, "nigeria")

    elif query.data == "cancel":
        context.user_data.clear()
        await query.edit_message_text(lang_text(lang, "❌ বাতিল হয়েছে!\n\nআবার শুরু করতে /start দিন.", "❌ Cancelled!\n\nSend /start to begin again.", "❌ Cancelled!\n\nSend /start to start again."), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Menu", callback_data="back")]]))
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
        await query.edit_message_text(lang_text(lang, "🎁 গিফট কোড রিডিম\n\nআপনার গিফট কোড লিখুন:\n\n📋 উদাহরণ: ABC12345", "🎁 Redeem Gift Code\n\nSend your gift code:\n\n📋 Example: ABC12345", "🎁 Redeem Gift Code\n\nSend your gift code:\n\n📋 Example: ABC12345"))

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
        await query.edit_message_text(lang_text(lang, "🔐 আপনার Password দিন:\n\n⚠️ Message পাঠানোর পর মুছে যাবে।", "🔐 Send your password:\n\n⚠️ Message will be deleted after you send it.", "🔐 Send your password:\n\n⚠️ Message go delete after you send am."))
        return SEND_W_PASSWORD

    elif query.data == "sw_cancel":
        context.user_data.clear()
        await query.edit_message_text(lang_text(lang, "❌ বাতিল হয়েছে।", "❌ Cancelled.", "❌ Cancelled."))
        return ConversationHandler.END

    elif query.data == "del_confirm":
        await query.edit_message_text(lang_text(lang, "🔐 Password দিন নিশ্চিত করতে:", "🔐 Send password to confirm:", "🔐 Send password to confirm:"))
        return DEL_PASSWORD

    elif query.data == "del_cancel":
        await query.edit_message_text(lang_text(lang, "❌ বাতিল হয়েছে।", "❌ Cancelled.", "❌ Cancelled."))
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
        elif trx_id.startswith("NGN-"):
            source = f"🇳🇬 Nigeria Payment: {bdt} NGN"
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
    total, completed, failed, total_bdt, total_crypto = get_transaction_stats()
    pending_count = len(get_pending_orders(100))
    failed_count = len(get_failed_transactions(100))
    maintenance = "ON" if is_maintenance_enabled() else "OFF"
    await update.message.reply_text(
        "📊 Admin Dashboard\n\n"
        f"🧾 Total TX: {total or 0}\n"
        f"✅ Completed: {completed or 0}\n"
        f"❌ Failed: {failed or 0}\n"
        f"⏳ Pending local payments: {pending_count}\n"
        f"🔁 Retry queue: {failed_count}\n"
        f"💰 Completed BDT: {round(total_bdt or 0, 4)}\n"
        f"💵 Completed crypto total: {round(total_crypto or 0, 6)}\n"
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
        await update.message.reply_text("🛑 Maintenance mode ON")
    elif arg in {"off", "disable", "disabled"}:
        set_setting("maintenance_mode", "off")
        await update.message.reply_text("✅ Maintenance mode OFF")
    else:
        await update.message.reply_text(f"🛠️ Maintenance: {'ON' if is_maintenance_enabled() else 'OFF'}\n\nUse /maintenance on or /maintenance off")


async def terms_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(terms_text(user_lang(update.effective_user.id)))


async def backup_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    from db import DB_PATH

    if not os.path.exists(DB_PATH):
        await update.message.reply_text("❌ Database file not found.")
        return
    await update.message.reply_document(document=open(DB_PATH, "rb"), filename=f"mouno-backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}.db")


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
    await query.edit_message_text("⏳ Retrying crypto send...")
    try:
        sig = await send_crypto(network, wallet, crypto)
        update_transaction(trx_id, sig=sig, status="completed")
        await query.edit_message_text(f"✅ Retry successful!\n\n🌐 {ni['name']}\n💵 {crypto} {ni['symbol']}\n👛 {wallet}\n🔗 {ni['explorer']}{sig}", reply_markup=back_keyboard(lang))
    except Exception as exc:
        await query.edit_message_text(f"❌ Retry failed again.\n\n{exc}", reply_markup=failed_retry_keyboard(trx_id))


def pending_order_keyboard(row):
    trx_id, user_id, _amount_bdt, _amount_usdc, _wallet, network, _created_at = row[:7]
    return [
        InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user_id}_{trx_id}_{network}"),
        InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user_id}_{trx_id}"),
    ]


def pending_orders_text(rows):
    if not rows:
        return "✅ No pending local payment orders."
    msg = "🧾 Pending Local Payment Orders\n\n"
    for row in rows:
        trx_id, user_id, amount_bdt, amount_usdc, wallet, network, created_at = row[:7]
        order_id = row[7] if len(row) > 7 else None
        net_info = NETWORKS.get(network, {"name": network, "symbol": "?"})
        meta = payment_meta(trx_id)
        short_wallet = f"{wallet[:8]}...{wallet[-6:]}" if wallet else "N/A"
        msg += (
            f"💳 {meta['method']}\n"
            f"🔑 {meta['id_label']}: {display_reference(trx_id)}\n"
            f"🧾 {order_id or 'N/A'}\n"
            f"👤 User: {user_id}\n"
            f"🌐 {net_info['name']}\n"
            f"💰 {amount_bdt} {meta['currency']} → {amount_usdc} {net_info['symbol']}\n"
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
        await update.message.reply_text("✅ No pending local payment orders.")
        return
    await update.message.reply_text(pending_orders_text(rows))
    for row in rows:
        trx_id, user_id, amount_bdt, amount_usdc, _wallet, network, _created_at = row[:7]
        order_id = row[7] if len(row) > 7 else None
        net_info = NETWORKS.get(network, {"name": network, "symbol": "?"})
        meta = payment_meta(trx_id)
        await update.message.reply_text(
            f"{meta['verify']}:\n\n🧾 Order: {order_id or 'N/A'}\n💳 {meta['method']}\n🔑 {meta['id_label']}: {display_reference(trx_id)}\n👤 User: {user_id}\n🌐 {net_info['name']}\n💰 {amount_bdt} {meta['currency']}\n💵 {amount_usdc} {net_info['symbol']}",
            reply_markup=InlineKeyboardMarkup([pending_order_keyboard(row)]),
        )


async def show_my_wallet_menu(query, user_id, lang=None):
    lang = lang or user_lang(user_id)
    row = get_user_wallet(user_id)
    if row:
        network = row[2]
        net_info = NETWORKS.get(network, {"name": network, "symbol": "?"})
        keyboard = [
            [InlineKeyboardButton(lang_text(lang, "💰 আমার Balance", "💰 My Balance", "💰 My Balance"), callback_data="check_mybal"), InlineKeyboardButton(lang_text(lang, "💸 Crypto পাঠাও", "💸 Send Crypto", "💸 Send Crypto"), callback_data="mw_send")],
            [InlineKeyboardButton(lang_text(lang, "🎁 Gift Code তৈরি", "🎁 Generate Gift Code", "🎁 Generate Gift Code"), callback_data="uw_gencode_menu")],
            [InlineKeyboardButton(lang_text(lang, "🔄 Wallet পরিবর্তন", "🔄 Change Wallet", "🔄 Change Wallet"), callback_data="mw_change"), InlineKeyboardButton(lang_text(lang, "🗑️ Wallet মুছো", "🗑️ Delete Wallet", "🗑️ Delete Wallet"), callback_data="mw_delete")],
            [InlineKeyboardButton(lang_text(lang, "📖 ব্যবহার গাইড", "📖 User Guide", "📖 User Guide"), callback_data="show_guide")],
            [InlineKeyboardButton(tr("back", lang), callback_data="back")],
        ]
        await query.edit_message_text(
            panel(tr("wallet", lang), f"✅ {lang_text(lang, 'Connected', 'Connected', 'Connected')}\n\n🌐 Network: {net_info['name']}\n👛 Address: `{short_wallet(row[3])}`\n\n👇 {lang_text(lang, 'একটি action বেছে নিন', 'Choose an action', 'Choose an action')}"),
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
    else:
        keyboard = [[InlineKeyboardButton(lang_text(lang, "🔐 Wallet সংযুক্ত করুন", "🔐 Connect Wallet", "🔐 Connect Wallet"), callback_data="mw_setup")], [InlineKeyboardButton(lang_text(lang, "📖 ব্যবহার গাইড", "📖 User Guide", "📖 User Guide"), callback_data="show_guide")], [InlineKeyboardButton(tr("back", lang), callback_data="back")]]
        await query.edit_message_text(panel(tr("wallet", lang), lang_text(lang, "❌ এখনো কোনো wallet connected নেই।\n\nBalance দেখতে বা crypto নিরাপদে পাঠাতে wallet connect করুন।", "❌ No wallet connected yet.\n\nConnect a wallet to check balance and send crypto securely.", "❌ No wallet connected yet.\n\nConnect wallet to check balance and send crypto safely.")), reply_markup=InlineKeyboardMarkup(keyboard))


async def show_payment_method_menu(query, context, user_id):
    lang = user_lang(user_id)
    fiat_amount = context.user_data.get("fiat_amount", context.user_data.get("amount_bdt"))
    wallet = context.user_data.get("wallet")
    network = context.user_data.get("network", "solana")
    if not all([fiat_amount, wallet]):
        await query.edit_message_text(lang_text(lang, "❌ সেশন শেষ! /start দিয়ে আবার শুরু করুন।", "❌ Session expired. Send /start again.", "❌ Session expire. Send /start again."))
        return
    net_info = NETWORKS[network]
    bdt_rate = get_rate(network)
    ngn_rate = get_ngn_rate(network)
    keyboard = [
        [InlineKeyboardButton(tr("bkash_payment", lang), callback_data="pay_bkash")],
        [InlineKeyboardButton(tr("nigeria_payment", lang), callback_data="pay_nigeria")],
        [InlineKeyboardButton(tr("cancel", lang), callback_data="cancel")],
    ]
    ngn_line = f"🇳🇬 Nigeria: {fiat_amount} NGN → {round(float(fiat_amount) / ngn_rate, 6)} {net_info['symbol']}" if ngn_rate else "🇳🇬 Nigeria: not configured for this network"
    await query.edit_message_text(
        panel(
            tr("choose_payment_method", lang),
            f"🌐 Network: {net_info['name']}\n"
            f"👛 Wallet: `{short_wallet(wallet)}`\n{DIVIDER}\n"
            f"📲 bKash: {fiat_amount} BDT → {round(float(fiat_amount) / bdt_rate, 6)} {net_info['symbol']}\n"
            f"{ngn_line}"
        ),
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def confirm_buy(query, context, user_id, username, payment_method="bkash"):
    lang = user_lang(user_id)
    fiat_amount = float(context.user_data.get("fiat_amount", context.user_data.get("amount_bdt", 0)))
    wallet = context.user_data.get("wallet")
    network = context.user_data.get("network", "solana")
    if not all([fiat_amount, wallet]):
        await query.edit_message_text(lang_text(lang, "❌ সেশন শেষ! /start দিয়ে আবার শুরু করুন।", "❌ Session expired. Send /start again.", "❌ Session expire. Send /start again."))
        return
    net_info = NETWORKS[network]
    if payment_method == "nigeria":
        if not nigeria_configured(network):
            await query.edit_message_text(
                lang_text(lang, "🇳🇬 Nigeria payment এই network-এর জন্য চালু/সেটআপ করা নেই। bKash বেছে নিন অথবা admin-এর সাথে যোগাযোগ করুন।", "🇳🇬 Nigeria payment is not enabled/configured for this network. Choose bKash or contact admin.", "🇳🇬 Nigeria payment no dey enabled/configured for this network. Choose bKash or contact admin."),
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(tr("bkash_payment", lang), callback_data="pay_bkash"), InlineKeyboardButton(tr("cancel", lang), callback_data="cancel")]]),
            )
            return
        rate = get_ngn_rate(network)
        crypto_amount = round(fiat_amount / rate, 6)
        sufficient, current_bal = check_sufficient(network, crypto_amount)
        if not sufficient and current_bal is not None:
            await query.edit_message_text(f"❌ Insufficient {net_info['symbol']} stock.\n\nNeed: {crypto_amount}\nAvailable: {current_bal}", reply_markup=back_keyboard(lang))
            return
        context.user_data["payment_method"] = "nigeria"
        context.user_data["amount_bdt"] = fiat_amount
        context.user_data["usdc_amount"] = crypto_amount
        context.user_data["waiting_trxid"] = True
        context.user_data["trx_deadline"] = asyncio.get_event_loop().time() + 900
        provider = get_setting("ng_provider", "Nigeria Payment")
        account = get_setting("ng_account", "")
        holder = get_setting("ng_holder", "")
        bank = get_setting("ng_bank", "")
        await query.edit_message_text(
            (
                f"🎯 {lang_text(lang, 'অর্ডার কনফার্ম', 'Order Confirmed', 'Order Confirmed')}!\n{DIVIDER}\n"
                f"🌐 Network: {net_info['name']}\n"
                f"💰 {lang_text(lang, 'ঠিক', 'Send exactly', 'Send exactly')} {fiat_amount} NGN\n"
                f"🇳🇬 Provider: {provider}\n"
                f"🏛️ Bank/Wallet: {bank}\n"
                f"👤 Name: {holder}\n"
                f"📱 Account/Phone: `{account}`\n\n"
                f"✅ {lang_text(lang, 'Payment করার পর Reference/Session/Transaction ID লিখুন', 'After payment, send your Reference/Session/Transaction ID', 'After payment, send your Reference/Session/Transaction ID')}\n"
                f"⏰ {lang_text(lang, 'সময়সীমা: ১৫ মিনিট', 'Time limit: 15 minutes', 'Time limit: 15 minutes')}"
            ),
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(tr("cancel", lang), callback_data="cancel")]]),
        )
        try:
            await query.get_bot().send_message(ADMIN_ID, f"🛎️ New Nigeria payment order!\n\n👤 @{username} ({user_id})\n🌐 {net_info['name']}\n💰 {fiat_amount} NGN\n💵 {crypto_amount} {net_info['symbol']}\n👛 {wallet}\n\n⏳ Waiting for Reference/Session ID...")
        except Exception as exc:
            logger.error(exc)
        return

    amount_bdt = fiat_amount
    crypto_amount = round(amount_bdt / get_rate(network), 6)
    sufficient, current_bal = check_sufficient(network, crypto_amount)
    if not sufficient and current_bal is not None:
        await query.edit_message_text(f"😔 দুঃখিত! এই মুহূর্তে অর্ডার পূরণ সম্ভব নয়।\n\n🌐 {net_info['name']}\n💵 আপনি চাইছেন: {crypto_amount} {net_info['symbol']}\n💰 মজুত: {current_bal} {net_info['symbol']}\n\nঅনুগ্রহ করে কম পরিমাণে অর্ডার করুন।\n❓ @MdMouno", reply_markup=back_keyboard(lang))
        return
    context.user_data["payment_method"] = "bkash"
    context.user_data["amount_bdt"] = amount_bdt
    context.user_data["usdc_amount"] = crypto_amount
    context.user_data["waiting_trxid"] = True
    context.user_data["trx_deadline"] = asyncio.get_event_loop().time() + 900
    await query.edit_message_text(
        (
            f"🎯 {'Order Confirmed' if lang == 'en' else 'অর্ডার কনফার্ম'}!\n{DIVIDER}\n"
            f"🌐 Network: {net_info['name']}\n"
            f"💰 {lang_text(lang, 'ঠিক', 'Send exactly', 'Send exactly')} {amount_bdt} BDT\n\n"
            f"📲 bKash: {BKASH_NUMBER}\n\n"
            f"✅ {lang_text(lang, 'পাঠানোর পর TrxID লিখুন', 'After payment, send your TrxID', 'After payment, send your TrxID')}\n"
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


def user_gencode_amount_keyboard(lang):
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("0.5", callback_data="uw_gc_amount_0.5"), InlineKeyboardButton("1", callback_data="uw_gc_amount_1")],
            [InlineKeyboardButton("2", callback_data="uw_gc_amount_2"), InlineKeyboardButton("5", callback_data="uw_gc_amount_5")],
            [InlineKeyboardButton("10", callback_data="uw_gc_amount_10"), InlineKeyboardButton(tr("custom_amount", lang), callback_data="uw_gc_amount_custom")],
            [InlineKeyboardButton(tr("cancel", lang), callback_data="uw_gc_cancel"), InlineKeyboardButton(tr("back", lang), callback_data="my_wallet_menu")],
        ]
    )


def user_gencode_duration_keyboard(lang):
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("15 min", callback_data="uw_gc_duration_15"), InlineKeyboardButton("30 min", callback_data="uw_gc_duration_30")],
            [InlineKeyboardButton("1 hour", callback_data="uw_gc_duration_60"), InlineKeyboardButton("6 hours", callback_data="uw_gc_duration_360")],
            [InlineKeyboardButton("24 hours", callback_data="uw_gc_duration_1440"), InlineKeyboardButton(tr("custom_duration", lang), callback_data="uw_gc_duration_custom")],
            [InlineKeyboardButton(tr("cancel", lang), callback_data="uw_gc_cancel"), InlineKeyboardButton(tr("back", lang), callback_data="uw_gc_back_amount")],
        ]
    )


def gift_duration_text(minutes, lang="bn"):
    hours, mins = divmod(int(minutes), 60)
    if lang in {"en", "pcm"}:
        return f"{hours}h {mins}m" if hours else f"{mins}m"
    return f"{hours} ঘণ্টা {mins} মিনিট" if hours else f"{mins} মিনিট"


async def start_user_gencode(query, context, user_id, username, lang):
    row = get_user_wallet(user_id)
    if not row:
        context.user_data.clear()
        await query.edit_message_text(lang_text(lang, "❌ Connected wallet নেই। আগে wallet connect করুন।", "❌ No connected wallet. Connect a wallet first.", "❌ No connected wallet. Connect wallet first."), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(lang_text(lang, "🔐 Wallet সংযুক্ত করুন", "🔐 Connect Wallet", "🔐 Connect Wallet"), callback_data="mw_setup")]]))
        return
    network = row[2]
    source_wallet = row[3]
    escrow_wallet, escrow_error = get_admin_escrow_wallet(network)
    if not escrow_wallet:
        context.user_data.clear()
        net_info = NETWORKS.get(network, {"name": network})
        await query.edit_message_text(lang_text(lang, "⚠️ এই network-এর gift code funding এখন unavailable. Admin setup শেষ হলে আবার চেষ্টা করুন।", "⚠️ Gift code funding is unavailable for this network. Try again after admin setup is complete.", "⚠️ Gift code funding no dey available for this network now. Try again after admin setup complete."), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(tr("back", lang), callback_data="my_wallet_menu")]]))
        try:
            await query.get_bot().send_message(ADMIN_ID, f"⚠️ User gift-code escrow unavailable\n\n👤 @{username} ({user_id})\n🌐 {net_info['name']}\n👛 Source: {source_wallet}\nError: {escrow_error}")
        except Exception as exc:
            logger.error("Escrow unavailable admin notify failed: %s", exc)
        return
    context.user_data.clear()
    context.user_data.update(
        {
            "uw_gencode_step": "amount",
            "uw_gencode_network": network,
            "uw_gencode_source_wallet": source_wallet,
            "uw_gencode_escrow_wallet": escrow_wallet,
            "uw_gencode_username": username,
        }
    )
    await show_user_gencode_amount_step(query, context, user_id, lang)


async def show_user_gencode_amount_step(query, context, user_id, lang):
    row = get_user_wallet(user_id)
    network = context.user_data.get("uw_gencode_network") or (row[2] if row else None)
    if not row or not network:
        context.user_data.clear()
        await query.edit_message_text(lang_text(lang, "❌ Session expired. Wallet menu থেকে আবার চেষ্টা করুন।", "❌ Session expired. Try again from Wallet menu.", "❌ Session expire. Try again from Wallet menu."), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(tr("back", lang), callback_data="my_wallet_menu")]]))
        return
    net_info = NETWORKS.get(network, {"name": network, "symbol": "?"})
    context.user_data["uw_gencode_step"] = "amount"
    await query.edit_message_text(
        lang_text(lang, f"🎁 Gift Code তৈরি\n\n🌐 Network: {net_info['name']}\n👛 Connected wallet: `{short_wallet(row[3])}`\n\nকত {net_info['symbol']} gift code করবেন?", f"🎁 Generate Gift Code\n\n🌐 Network: {net_info['name']}\n👛 Connected wallet: `{short_wallet(row[3])}`\n\nHow many {net_info['symbol']} should the gift code contain?", f"🎁 Generate Gift Code\n\n🌐 Network: {net_info['name']}\n👛 Connected wallet: `{short_wallet(row[3])}`\n\nHow many {net_info['symbol']} you wan put for gift code?"),
        parse_mode="Markdown",
        reply_markup=user_gencode_amount_keyboard(lang),
    )


async def select_user_gencode_amount(query, context, user_id, lang):
    row = get_user_wallet(user_id)
    if not row or not context.user_data.get("uw_gencode_network"):
        context.user_data.clear()
        await query.edit_message_text(lang_text(lang, "❌ Session expired. Wallet menu থেকে আবার চেষ্টা করুন।", "❌ Session expired. Try again from Wallet menu.", "❌ Session expire. Try again from Wallet menu."), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(tr("back", lang), callback_data="my_wallet_menu")]]))
        return
    value = query.data.replace("uw_gc_amount_", "", 1)
    if value == "custom":
        context.user_data["uw_gencode_step"] = "custom_amount"
        await query.edit_message_text(lang_text(lang, "💵 Custom amount লিখুন:\n\nশুধু সংখ্যা (যেমন: 3.5)", "💵 Send custom amount:\n\nNumbers only (example: 3.5)", "💵 Send custom amount:\n\nNumbers only (example: 3.5)"), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(tr("cancel", lang), callback_data="uw_gc_cancel")]]))
        return
    context.user_data["uw_gencode_amount"] = float(value)
    context.user_data["uw_gencode_step"] = "duration"
    await query.edit_message_text(lang_text(lang, "⏰ Gift code কতক্ষণ valid থাকবে?", "⏰ How long should the gift code stay valid?", "⏰ How long gift code go valid?"), reply_markup=user_gencode_duration_keyboard(lang))


async def select_user_gencode_duration(query, context, user_id, lang):
    if not get_user_wallet(user_id) or not context.user_data.get("uw_gencode_amount"):
        context.user_data.clear()
        await query.edit_message_text(lang_text(lang, "❌ Session expired. Wallet menu থেকে আবার চেষ্টা করুন।", "❌ Session expired. Try again from Wallet menu.", "❌ Session expire. Try again from Wallet menu."), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(tr("back", lang), callback_data="my_wallet_menu")]]))
        return
    value = query.data.replace("uw_gc_duration_", "", 1)
    if value == "custom":
        context.user_data["uw_gencode_step"] = "custom_duration"
        await query.edit_message_text(lang_text(lang, "⏰ Custom duration মিনিটে লিখুন:\n\nযেমন: 45", "⏰ Send custom duration in minutes:\n\nExample: 45", "⏰ Send custom duration in minutes:\n\nExample: 45"), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(tr("cancel", lang), callback_data="uw_gc_cancel")]]))
        return
    context.user_data["uw_gencode_minutes"] = int(value)
    context.user_data["uw_gencode_step"] = "summary"
    await show_user_gencode_summary(query, context, lang)


async def show_user_gencode_summary(target, context, lang):
    network = context.user_data.get("uw_gencode_network")
    amount = context.user_data.get("uw_gencode_amount")
    minutes = context.user_data.get("uw_gencode_minutes")
    source_wallet = context.user_data.get("uw_gencode_source_wallet")
    escrow_wallet = context.user_data.get("uw_gencode_escrow_wallet")
    net_info = NETWORKS.get(network, {"name": network, "symbol": "?"})
    message = (
        f"📊 Gift Code Summary\n\n"
        f"👛 Connected wallet: `{source_wallet}`\n"
        f"🌐 Network: {net_info['name']}\n"
        f"💵 Amount: {amount} {net_info['symbol']}\n"
        f"⏰ Expiry: {gift_duration_text(minutes, lang)}\n"
        f"🏦 Escrow: `{short_wallet(escrow_wallet)}`\n\n"
        f"{lang_text(lang, '⚠️ Confirm করলে আপনার connected wallet থেকে asset deduct হয়ে bot escrow-তে যাবে।', '⚠️ Confirming will deduct the asset from your connected wallet and send it to bot escrow.', '⚠️ If you confirm, asset go deduct from your connected wallet and enter bot escrow.')}\n"
        f"{lang_text(lang, '🎟️ এরপর code তৈরি হবে এবং যার কাছে code থাকবে সে একবার redeem করতে পারবে।', '🎟️ Then a code will be generated. Whoever has the code can redeem it once.', '🎟️ Then code go generate. Person wey get code fit redeem am once.')}\n\n"
        f"{lang_text(lang, 'নিশ্চিত?', 'Confirm?', 'Confirm?')}"
    )
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("✅ Confirm", callback_data="uw_gc_confirm"), InlineKeyboardButton(tr("cancel", lang), callback_data="uw_gc_cancel")], [InlineKeyboardButton(tr("back", lang), callback_data="uw_gc_back_amount")]])
    if hasattr(target, "edit_message_text"):
        await target.edit_message_text(message, parse_mode="Markdown", reply_markup=keyboard)
    else:
        await target.reply_text(message, parse_mode="Markdown", reply_markup=keyboard)


async def ask_user_gencode_password(query, context, user_id, lang):
    if not get_user_wallet(user_id) or not all(context.user_data.get(key) for key in ["uw_gencode_network", "uw_gencode_amount", "uw_gencode_minutes", "uw_gencode_escrow_wallet"]):
        context.user_data.clear()
        await query.edit_message_text(lang_text(lang, "❌ Session expired. Wallet menu থেকে আবার চেষ্টা করুন।", "❌ Session expired. Try again from Wallet menu.", "❌ Session expire. Try again from Wallet menu."), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(tr("back", lang), callback_data="my_wallet_menu")]]))
        return
    context.user_data["uw_gencode_step"] = "password"
    await query.edit_message_text(lang_text(lang, "🔐 Wallet Password দিন:\n\nConfirm funding করতে একবার password লাগবে।\n⚠️ Message পাঠানোর পর মুছে যাবে।", "🔐 Send wallet password:\n\nPassword is required once to confirm funding.\n⚠️ Message will be deleted after you send it.", "🔐 Send wallet password:\n\nPassword dey required once to confirm funding.\n⚠️ Message go delete after you send am."), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(tr("cancel", lang), callback_data="uw_gc_cancel")]]))


async def handle_user_gencode_text(update, context, user_id, username, lang):
    step = context.user_data.get("uw_gencode_step")
    if step == "custom_amount":
        try:
            amount = float(update.message.text.strip())
            if amount <= 0:
                raise ValueError
        except Exception:
            await update.message.reply_text(tr("invalid_amount", lang))
            return
        context.user_data["uw_gencode_amount"] = amount
        context.user_data["uw_gencode_step"] = "duration"
        await update.message.reply_text(lang_text(lang, "⏰ Gift code কতক্ষণ valid থাকবে?", "⏰ How long should the gift code stay valid?", "⏰ How long gift code go valid?"), reply_markup=user_gencode_duration_keyboard(lang))
        return
    if step == "custom_duration":
        try:
            minutes = int(update.message.text.strip())
            if minutes <= 0:
                raise ValueError
        except Exception:
            await update.message.reply_text(tr("enter_custom_duration", lang))
            return
        context.user_data["uw_gencode_minutes"] = minutes
        context.user_data["uw_gencode_step"] = "summary"
        await show_user_gencode_summary(update.message, context, lang)
        return
    if step == "password":
        await complete_user_gift_code(update, context, user_id, username, lang)


async def complete_user_gift_code(update, context, user_id, username, lang):
    password = update.message.text.strip()
    try:
        await update.message.delete()
    except Exception:
        pass
    row = get_user_wallet(user_id)
    if not row:
        context.user_data.clear()
        await update.message.reply_text(lang_text(lang, "❌ Wallet নেই। আবার setup করুন।", "❌ No wallet. Set it up again.", "❌ No wallet. Set am up again."))
        return
    network = context.user_data.get("uw_gencode_network")
    amount = float(context.user_data.get("uw_gencode_amount", 0))
    minutes = int(context.user_data.get("uw_gencode_minutes", 0))
    escrow_wallet = context.user_data.get("uw_gencode_escrow_wallet")
    source_wallet = context.user_data.get("uw_gencode_source_wallet") or row[3]
    if not all([network, amount > 0, minutes > 0, escrow_wallet]):
        context.user_data.clear()
        await update.message.reply_text(lang_text(lang, "❌ Session expired. Wallet menu থেকে আবার চেষ্টা করুন।", "❌ Session expired. Try again from Wallet menu.", "❌ Session expire. Try again from Wallet menu."))
        return
    net_info = NETWORKS.get(network, {"name": network, "symbol": "?", "explorer": ""})
    code = gen_code()
    while get_code(code):
        code = gen_code()
    await update.message.reply_text(f"⏳ Funding gift code...\n\n💵 {amount} {net_info['symbol']}\n🏦 Escrow: `{short_wallet(escrow_wallet)}`", parse_mode="Markdown")
    try:
        sig = await asyncio.get_running_loop().run_in_executor(None, lambda: send_from_user_wallet(user_id, password, escrow_wallet, amount))
    except Exception as exc:
        if "ভুল password" in str(exc) or "wrong" in str(exc).lower():
            await update.message.reply_text(lang_text(lang, "❌ ভুল Password! আবার password দিন:\n\nCode এখনো তৈরি হয়নি।", "❌ Wrong password! Send password again:\n\nCode has not been created yet.", "❌ Wrong password! Send password again:\n\nCode never create yet."))
            context.user_data["uw_gencode_step"] = "password"
            return
        context.user_data.clear()
        logger.error("User gift-code funding failed: %s", exc)
        await update.message.reply_text(f"{lang_text(lang, '❌ Gift code funding ব্যর্থ!', '❌ Gift code funding failed!', '❌ Gift code funding fail!')}\n\n{exc}\n\n{lang_text(lang, 'Code তৈরি হয়নি।', 'Code was not created.', 'Code no create.')}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Wallet Menu", callback_data="my_wallet_menu")]]))
        return
    expires_at = (datetime.now() + timedelta(minutes=minutes)).isoformat()
    create_code(code, amount, expires_at, network)
    save_transaction(f"UGIFT-FUND-{code}", user_id, 0, amount, escrow_wallet, sig, "completed", network)
    context.user_data.clear()
    explorer = f"{net_info.get('explorer', '')}{sig}"
    expiry_text = gift_duration_text(minutes, lang)
    await update.message.reply_text(
        f"{lang_text(lang, '🎉 Gift code তৈরি হয়েছে!', '🎉 Gift code generated!', '🎉 Gift code don generate!')}\n\n"
        f"🎟️ Code: `{code}`\n"
        f"🌐 Network: {net_info['name']}\n"
        f"💵 Amount: {amount} {net_info['symbol']}\n"
        f"⏰ Expiry: {expiry_text}\n"
        f"🔗 Funding TX: {explorer}\n\n"
        f"{lang_text(lang, '⚠️ যার কাছে এই code থাকবে সে একবার redeem করতে পারবে।', '⚠️ Whoever has this code can redeem it once.', '⚠️ Person wey get this code fit redeem am once.')}",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(lang_text(lang, "🎁 আরেকটি তৈরি", "🎁 Create another", "🎁 Create another"), callback_data="uw_gencode_menu"), InlineKeyboardButton("🔙 Wallet Menu", callback_data="my_wallet_menu")]]),
    )
    try:
        await update.get_bot().send_message(
            ADMIN_ID,
            f"🎁 User-funded gift code created\n\n👤 @{username} ({user_id})\n🎟️ {code}\n🌐 {net_info['name']}\n💵 {amount} {net_info['symbol']}\n📤 Source: {source_wallet}\n🏦 Escrow: {escrow_wallet}\n🔗 Funding TX: {explorer}",
        )
    except Exception as exc:
        logger.error("User gift-code admin notify failed: %s", exc)


async def create_gift_code_from_context(target, context, minutes, lang):
    network = context.user_data.get("gencode_network", "solana")
    amount = float(context.user_data.get("gencode_amount", 0))
    if amount <= 0 or minutes <= 0:
        await target.edit_message_text(lang_text(lang, "❌ ভুল পরিমাণ বা সময়!", "❌ Invalid amount or time.", "❌ Amount or time no correct."))
        return
    code = gen_code()
    expires_at = (datetime.now() + timedelta(minutes=minutes)).isoformat()
    create_code(code, amount, expires_at, network)
    net_info = NETWORKS[network]
    time_str = gift_duration_text(minutes, lang)
    context.user_data.clear()
    message = (
        f"{tr('code_created', lang)}\n\n"
        f"🎟️ Code: `{code}`\n"
        f"🌐 {net_info['name']}\n"
        f"💵 {amount} {net_info['symbol']}\n"
        f"⏰ {time_str}\n\n"
        f"⚠️ {lang_text(lang, 'শুধুমাত্র একজন ব্যবহার করতে পারবে!', 'Single use only.', 'Single use only.')}"
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
    meta = payment_meta(trx_id)
    net_info = NETWORKS.get(network, {"name": network, "symbol": "?", "explorer": ""})
    target_wallet = get_wallet(target_uid)
    if not target_wallet:
        await query.edit_message_text(f"❌ User এর wallet পাওয়া যায়নি!\nUser ID: {target_uid}")
        return
    await query.edit_message_text(f"✅ Approved!\n\n⏳ Crypto পাঠানো হচ্ছে...\n\n👤 User: {target_uid}\n🔑 {meta['id_label']}: {display_reference(trx_id)}\n🌐 {net_info['name']}")

    sms_row = get_sms(trx_id)
    if sms_row:
        amount_bdt = sms_row[1]
        crypto_amount = round(amount_bdt / get_rate(network), 6)
    else:
        amount_bdt = 0
        crypto_amount = 0

    order_id = None
    pending = get_pending_order(trx_id)
    if pending:
        amount_bdt = pending[2]
        crypto_amount = pending[3]
        target_wallet = pending[4] or target_wallet
        order_id = pending[7] if len(pending) > 7 else None

    try:
        sig = await send_crypto(network, target_wallet, crypto_amount)
        explorer = f"{net_info['explorer']}{sig}"
        if sms_row:
            mark_sms_used(trx_id)
        save_transaction(trx_id, target_uid, amount_bdt, crypto_amount, target_wallet, sig, "completed", network, order_id=order_id)
        delete_pending_order(trx_id)
        await query.edit_message_text(f"✅ Crypto পাঠানো হয়েছে!\n\n👤 User: {target_uid}\n🔑 {meta['id_label']}: {display_reference(trx_id)}\n💰 {amount_bdt} {meta['currency']}\n🌐 {net_info['name']}\n💵 {crypto_amount} {net_info['symbol']}\n👛 {target_wallet}\n🔗 {explorer}")
        try:
            await query.get_bot().send_message(int(target_uid), f"🎉 Payment confirmed!\n\n🌐 {net_info['name']}\n💵 {crypto_amount} {net_info['symbol']}\n👛 {target_wallet}\n🔗 {explorer}\n\nধন্যবাদ! 🙏")
        except Exception:
            pass
    except Exception as exc:
        await query.edit_message_text(f"❌ পাঠাতে ব্যর্থ!\n\n{exc}")
        logger.error("Admin approve send failed: %s", exc)


async def reject_order(query, user_id):
    if not is_admin(user_id):
        return
    _prefix, target_uid, trx_id = query.data.split("_", 2)
    meta = payment_meta(trx_id)
    delete_pending_order(trx_id)
    await query.edit_message_text(f"❌ Rejected!\n\n👤 User: {target_uid}\n🔑 {meta['id_label']}: {display_reference(trx_id)}")
    try:
        await query.get_bot().send_message(int(target_uid), f"❌ Your payment could not be verified.\n\n🔑 {meta['id_label']}: {display_reference(trx_id)}\n\nPlease check the ID or contact support:\n📞 @MdMouno")
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
    ngn_rate = get_ngn_rate(network)
    ngn_line = f"\n🇳🇬 NGN Rate: 1 {net_info['symbol']} = {ngn_rate} NGN" if ngn_rate else ""
    await update.message.reply_text(panel("👛 Wallet Saved", f"🌐 {net_info['name']}\n👛 `{short_wallet(wallet)}`\n{DIVIDER}\n{tr('enter_fiat_amount', lang, symbol=net_info['symbol'])}\n\n💵 bKash Rate: 1 {net_info['symbol']} = {get_rate(network)} BDT{ngn_line}\n✍️ {tr('numbers_only', lang)}"))
    return WAITING_AMOUNT


async def waiting_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = user_lang(update.effective_user.id)
    try:
        fiat_amount = float(update.message.text.strip())
        if fiat_amount <= 0:
            raise ValueError
    except Exception:
        await update.message.reply_text(f"{tr('invalid_amount', lang)}\n{tr('numbers_only', lang)}")
        return WAITING_AMOUNT

    network = context.user_data.get("network", "solana")
    net_info = NETWORKS[network]
    rate = get_rate(network)
    crypto_amount = round(fiat_amount / rate, 6)
    context.user_data["fiat_amount"] = fiat_amount
    context.user_data["amount_bdt"] = fiat_amount
    context.user_data["usdc_amount"] = crypto_amount
    keyboard = [[InlineKeyboardButton(tr("confirm", lang), callback_data="confirm_buy"), InlineKeyboardButton(tr("cancel", lang), callback_data="cancel")]]
    await update.message.reply_text(
        panel(
            tr('order_summary', lang),
            f"🌐 Network: {net_info['name']}\n"
            f"💰 Amount: {fiat_amount} BDT/NGN\n"
            f"💵 bKash estimate: {crypto_amount} {net_info['symbol']}\n"
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
            lang_text(lang, f"❌ পর্যাপ্ত {net_info['symbol']} নেই।\n\nদরকার: {amount_crypto}\nআছে: {current_bal}", f"❌ Insufficient {net_info['symbol']} stock.\n\nNeed: {amount_crypto}\nAvailable: {current_bal}", f"❌ {net_info['symbol']} stock no enough.\n\nNeed: {amount_crypto}\nAvailable: {current_bal}")
        )
        return ConversationHandler.END

    order_id = gen_order_id("STAR")
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
            lang_text(lang, f"❌ পর্যাপ্ত {net_info['symbol']} নেই।{stock_line}\nদরকার: {amount} {net_info['symbol']}", f"❌ Insufficient {net_info['symbol']} stock.{stock_line}\nNeed: {amount} {net_info['symbol']}", f"❌ {net_info['symbol']} stock no enough.{stock_line}\nNeed: {amount} {net_info['symbol']}")
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
        await query.edit_message_text(lang_text(lang, "❌ সেশন শেষ। আবার শুরু করুন।", "❌ Session expired. Start again.", "❌ Session expire. Start again."))
        return
    net_info = NETWORKS[network]
    await query.edit_message_text(lang_text(lang, "⏳ Asset পাঠানো হচ্ছে...", "⏳ Sending asset...", "⏳ Asset dey send..."))
    try:
        sig = await send_crypto(network, wallet, amount)
        explorer = f"{net_info['explorer']}{sig}"
        save_transaction(f"ADMIN-{sig[:24]}", user_id, 0, amount, wallet, sig, "completed", network)
        context.user_data.clear()
        await query.edit_message_text(
            f"{tr('admin_send_done', lang)}\n\n"
            f"🌐 {net_info['name']}\n"
            f"💵 {amount} {net_info['symbol']}\n"
            f"👛 {wallet}\n"
            f"🔗 {explorer}",
            reply_markup=back_keyboard(lang),
        )
    except Exception as exc:
        save_transaction(f"ADMIN-FAILED-{gen_code(8)}", user_id, 0, amount, wallet, "", "failed", network)
        context.user_data.clear()
        await query.edit_message_text(f"❌ Send failed.\n\n{exc}", reply_markup=back_keyboard(lang))


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
    net_info = NETWORKS[network]
    await update.message.reply_text(f"✅ রেট আপডেট!\n\n🌐 {net_info['name']}\n💵 1 {net_info['symbol']} = {new_rate} BDT")
    return ConversationHandler.END


async def waiting_trxid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    username = update.effective_user.username or update.effective_user.first_name
    lang = user_lang(user_id)

    if is_admin(user_id) and context.user_data.get("ai_setup_step"):
        step = context.user_data.get("ai_setup_step")
        value = update.message.text.strip()
        if value.lower() in {"/cancel", "cancel"}:
            context.user_data.pop("ai_setup_step", None)
            await update.message.reply_text(ai_config_text(lang), reply_markup=ai_setup_keyboard(lang))
            return ConversationHandler.END
        if not value:
            await update.message.reply_text("❌ Empty value. Send a value or cancel.")
            return AI_SETUP_TEXT
        if step == "key":
            set_setting("ai_api_key", value)
            try:
                await update.message.delete()
            except Exception:
                pass
            saved_text = f"{tr('ai_setup_saved', lang)}\nAPI key: {mask_secret(value)}"
        elif step == "model":
            set_setting("ai_model", value)
            saved_text = f"{tr('ai_setup_saved', lang)}\nModel: {value}"
        elif step == "base_url":
            set_setting("ai_base_url", value)
            saved_text = f"{tr('ai_setup_saved', lang)}\nBase URL: {value}"
        else:
            saved_text = tr("ai_setup_saved", lang)
        context.user_data.pop("ai_setup_step", None)
        await update.message.reply_text(f"{saved_text}\n\n{ai_config_text(lang)}", reply_markup=ai_setup_keyboard(lang))
        return ConversationHandler.END

    if context.user_data.get("ai_support"):
        text = update.message.text.strip()
        if text.lower() in {"/cancel", "cancel", "বন্ধ", "বাতিল"}:
            context.user_data.clear()
            await update.message.reply_text(lang_text(lang, "✅ AI Support বন্ধ হয়েছে।", "✅ AI Support closed.", "✅ AI Support don close."), reply_markup=main_menu(user_id, lang))
            return
        await update.message.reply_text(tr("ai_thinking", lang))
        try:
            answer = await asyncio.get_running_loop().run_in_executor(None, lambda: ask_ai_support(text, lang))
        except Exception as exc:
            logger.error("AI support failed: %s", exc)
            answer = tr("ai_unavailable", lang)
        await update.message.reply_text(answer)
        return AI_SUPPORT

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

    if is_admin(user_id) and context.user_data.get("ng_setup_step"):
        step = context.user_data.get("ng_setup_step")
        value = update.message.text.strip()
        if step == "rate":
            network = context.user_data.get("ng_rate_network", "solana")
            try:
                rate = float(value)
                if rate <= 0:
                    raise ValueError
            except Exception:
                await update.message.reply_text("❌ Invalid NGN rate. Send a number like 1500.")
                return NG_SETUP_TEXT
            set_setting(f"ngn_rate_{network}", rate)
        else:
            key_map = {"provider": "ng_provider", "account": "ng_account", "holder": "ng_holder", "bank": "ng_bank", "secret": "ng_secret"}
            if not value:
                await update.message.reply_text("❌ Empty value. Send a value or cancel.")
                return NG_SETUP_TEXT
            set_setting(key_map[step], value)
        context.user_data.pop("ng_setup_step", None)
        context.user_data.pop("ng_rate_network", None)
        await update.message.reply_text(nigeria_config_text(), reply_markup=nigeria_setup_keyboard())
        return ConversationHandler.END

    if context.user_data.get("redeem_step"):
        return await handle_redeem(update, context, user_id, username)
    if context.user_data.get("uw_waiting_bal_password"):
        return await handle_balance_password(update, context, user_id)
    if context.user_data.get("uw_gencode_step") in {"custom_amount", "custom_duration", "password"}:
        return await handle_user_gencode_text(update, context, user_id, username, lang)
    if not context.user_data.get("waiting_trxid"):
        return

    deadline = context.user_data.get("trx_deadline", 0)
    if asyncio.get_event_loop().time() > deadline:
        context.user_data.clear()
        await update.message.reply_text("⏰ সময়সীমা শেষ!\n\nআবার অর্ডার করুন /start দিয়ে\n\n❓ @MdMouno")
        return

    payment_method = context.user_data.get("payment_method", "bkash")
    raw_trx_id = update.message.text.strip().upper()
    trx_id = ng_reference_key(raw_trx_id) if payment_method == "nigeria" else raw_trx_id
    meta = payment_meta(trx_id)
    if len(display_reference(trx_id)) < 4:
        await update.message.reply_text("❌ Invalid Reference/Session ID. Try again." if payment_method == "nigeria" else "❌ ভুল TrxID! আবার চেষ্টা করুন।")
        return
    if trx_exists(trx_id):
        await update.message.reply_text(lang_text(lang, f"⚠️ এই {meta['id_label']} আগেই ব্যবহার হয়েছে!\n\n❓ @MdMouno", f"⚠️ This {meta['id_label']} was already used!\n\n❓ @MdMouno", f"⚠️ This {meta['id_label']} don already use!\n\n❓ @MdMouno"))
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
        order_id = save_pending_order(trx_id, user_id, amount_bdt, crypto_amount, wallet, network)
        keyboard = [[InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user_id}_{trx_id}_{network}"), InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user_id}_{trx_id}")]]
        try:
            await update.get_bot().send_message(ADMIN_ID, f"⚠️ Payment notice not found. Manual verify needed.\n\n🧾 Order: {order_id}\n💳 Method: {meta['method']}\n👤 User: @{username} ({user_id})\n🔑 {meta['id_label']}: {display_reference(trx_id)}\n💰 Amount: {amount_bdt} {meta['currency']}\n💵 Est: {crypto_amount} {net_info['symbol']}\n🌐 Network: {net_info['name']}\n👛 Wallet: {wallet}\n\n{meta['verify']} and tap Approve or Reject:", reply_markup=InlineKeyboardMarkup(keyboard))
        except Exception as exc:
            logger.error(exc)
        await update.message.reply_text(f"⏳ {meta['id_label']} is being verified.\n\n🔑 {display_reference(trx_id)}\n\nAdmin is checking, please wait...")
        return

    amount_bdt = sms_row[1]
    crypto_amount = context.user_data.get("usdc_amount") or round(amount_bdt / (get_ngn_rate(network) if payment_method == "nigeria" else get_rate(network)), 6)
    expected_amount = float(context.user_data.get("amount_bdt", 0) or 0)
    if payment_method == "nigeria" and expected_amount and abs(float(amount_bdt) - expected_amount) > 0.01:
        order_id = save_pending_order(trx_id, user_id, expected_amount, context.user_data.get("usdc_amount", 0), wallet, network)
        keyboard = [[InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user_id}_{trx_id}_{network}"), InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user_id}_{trx_id}")]]
        await update.get_bot().send_message(
            ADMIN_ID,
            f"⚠️ Nigerian payment reference matched but amount is different.\n\n🧾 Order: {order_id}\n👤 User: @{username} ({user_id})\n🔑 Reference: {display_reference(trx_id)}\n🧾 Expected: {expected_amount} NGN\n📩 Notice received: {amount_bdt} NGN\n🌐 {net_info['name']}\n👛 {wallet}\n\nPlease verify manually.",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        await update.message.reply_text("⏳ Payment reference found but amount needs admin review. Please wait.")
        return
    sufficient, current_bal = check_sufficient(network, crypto_amount)
    if not sufficient and current_bal is not None:
        await update.message.reply_text(f"❌ পর্যাপ্ত {net_info['symbol']} নেই!\n\n🌐 {net_info['name']}\n💵 চান: {crypto_amount}\n💰 আছে: {current_bal}\n\n📞 @MdMouno")
        return

    await update.message.reply_text(f"✅ Payment verified!\n\n🌐 {net_info['name']}\n💰 {amount_bdt} {meta['currency']} = {crypto_amount} {net_info['symbol']}\n👛 {wallet}\n\n⏳ Sending...")
    try:
        sig = await send_crypto(network, wallet, crypto_amount)
        explorer = f"{net_info['explorer']}{sig}"
        mark_sms_used(trx_id)
        save_transaction(trx_id, user_id, amount_bdt, crypto_amount, wallet, sig, "completed", network)
        context.user_data.clear()
        await update.message.reply_text(f"🎉 {net_info['symbol']} পাঠানো হয়েছে!\n\n🌐 {net_info['name']}\n💵 {crypto_amount} {net_info['symbol']}\n👛 {wallet}\n🔗 {explorer}\n\nধন্যবাদ! 🙏")
    except Exception as exc:
        save_transaction(trx_id, user_id, amount_bdt, crypto_amount, wallet, "", "failed", network)
        context.user_data.clear()
        logger.error("Send failed: %s", exc)
        await update.message.reply_text(f"❌ পাঠাতে সমস্যা!\n\n📞 @MdMouno\n\nআপনার TrxID: {trx_id}\nসংরক্ষণ করুন।")


async def handle_redeem(update, context, user_id, username):
    lang = user_lang(user_id)
    if context.user_data.get("redeem_step") == "code":
        code = update.message.text.strip().upper()
        row = get_code(code)
        if not row:
            await update.message.reply_text(lang_text(lang, "❌ কোড পাওয়া যায়নি!\n\nসঠিক কোড লিখুন।", "❌ Code not found!\n\nSend the correct code.", "❌ Code no dey!\n\nSend correct code."))
            return
        _code_val, amount_crypto, expires_at, used, _used_by, _created_at, code_network = row
        if used:
            await update.message.reply_text(lang_text(lang, "⚠️ এই কোড আগেই ব্যবহার হয়েছে!\n\n❓ @MdMouno", "⚠️ This code was already used!\n\n❓ @MdMouno", "⚠️ This code don already use!\n\n❓ @MdMouno"))
            context.user_data.clear()
            return
        if datetime.now() > datetime.fromisoformat(expires_at):
            await update.message.reply_text(lang_text(lang, "⏰ এই কোডের মেয়াদ শেষ!\n\n❓ @MdMouno", "⏰ This code has expired!\n\n❓ @MdMouno", "⏰ This code don expire!\n\n❓ @MdMouno"))
            context.user_data.clear()
            return
        net_info = NETWORKS.get(code_network, NETWORKS["solana"])
        context.user_data.update({"redeem_code": code, "redeem_usdc": amount_crypto, "redeem_network": code_network, "redeem_step": "wallet"})
        await update.message.reply_text(lang_text(lang, f"✅ কোড যাচাই সফল!\n\n🎁 পাবেন: {amount_crypto} {net_info['symbol']}\n🌐 নেটওয়ার্ক: {net_info['name']}\n\nআপনার {net_info['name']} Wallet Address দিন:\n\n📋 উদাহরণ: {wallet_hint(code_network)}", f"✅ Code verified!\n\n🎁 You will receive: {amount_crypto} {net_info['symbol']}\n🌐 Network: {net_info['name']}\n\nSend your {net_info['name']} wallet address:\n\n📋 Example: {wallet_hint(code_network)}", f"✅ Code verified!\n\n🎁 You go receive: {amount_crypto} {net_info['symbol']}\n🌐 Network: {net_info['name']}\n\nSend your {net_info['name']} wallet address:\n\n📋 Example: {wallet_hint(code_network)}"))
        return

    wallet = update.message.text.strip()
    network = context.user_data.get("redeem_network", "solana")
    net_info = NETWORKS[network]
    if not valid_wallet(network, wallet):
        await update.message.reply_text(lang_text(lang, f"❌ ভুল {net_info['name']} wallet!\n\nসঠিক address দিন।", f"❌ Invalid {net_info['name']} wallet!\n\nSend correct address.", f"❌ {net_info['name']} wallet no correct!\n\nSend correct address."))
        return
    code = context.user_data["redeem_code"]
    amount_crypto = context.user_data["redeem_usdc"]
    context.user_data.clear()
    await update.message.reply_text(lang_text(lang, f"⏳ {net_info['symbol']} পাঠানো হচ্ছে...\n\n🌐 {net_info['name']}\n💵 {amount_crypto} {net_info['symbol']}\n👛 {wallet}", f"⏳ Sending {net_info['symbol']}...\n\n🌐 {net_info['name']}\n💵 {amount_crypto} {net_info['symbol']}\n👛 {wallet}", f"⏳ {net_info['symbol']} dey send...\n\n🌐 {net_info['name']}\n💵 {amount_crypto} {net_info['symbol']}\n👛 {wallet}"))
    try:
        sig = await send_crypto(network, wallet, amount_crypto)
        explorer = f"{net_info['explorer']}{sig}"
        use_code(code, user_id)
        save_transaction(f"GIFT-{code}", user_id, 0, amount_crypto, wallet, sig, "completed", network)
        await update.message.reply_text(lang_text(lang, f"🎉 {net_info['symbol']} পাঠানো হয়েছে!\n\n🎁 {amount_crypto} {net_info['symbol']}\n🌐 {net_info['name']}\n👛 {wallet}\n🔗 {explorer}\n\nধন্যবাদ! 🙏", f"🎉 {net_info['symbol']} sent!\n\n🎁 {amount_crypto} {net_info['symbol']}\n🌐 {net_info['name']}\n👛 {wallet}\n🔗 {explorer}\n\nThank you! 🙏", f"🎉 {net_info['symbol']} don send!\n\n🎁 {amount_crypto} {net_info['symbol']}\n🌐 {net_info['name']}\n👛 {wallet}\n🔗 {explorer}\n\nThank you! 🙏"))
        try:
            await update.get_bot().send_message(ADMIN_ID, f"🎁 গিফট কোড রিডিম!\n\n👤 @{username} ({user_id})\n🎟️ {code}\n🌐 {net_info['name']}\n💵 {amount_crypto} {net_info['symbol']}\n👛 {wallet}\n🔗 {explorer}")
        except Exception:
            pass
    except Exception as exc:
        await update.message.reply_text(lang_text(lang, "❌ পাঠাতে সমস্যা!\n\n📞 @MdMouno", "❌ Sending failed!\n\n📞 @MdMouno", "❌ Sending fail!\n\n📞 @MdMouno"))
        logger.error("Redeem failed: %s", exc)


async def handle_balance_password(update, context, user_id):
    lang = user_lang(user_id)
    password = update.message.text.strip()
    try:
        await update.message.delete()
    except Exception:
        pass
    context.user_data.pop("uw_waiting_bal_password", None)
    bal, network, error = get_user_balance(user_id, password)
    if error == "wrong_password":
        await update.message.reply_text(lang_text(lang, "❌ ভুল Password!", "❌ Wrong password!", "❌ Wrong password!"))
        return
    if error:
        await update.message.reply_text(f"❌ Error: {error}")
        return
    row = get_user_wallet(user_id)
    net_info = NETWORKS.get(network, {"name": network, "symbol": "?"})
    await update.message.reply_text(lang_text(lang, f"💰 আপনার Balance:\n\n🌐 {net_info['name']}\n👛 {row[3]}\n💵 {bal} {net_info['symbol']}\n\n💸 পাঠাতে: /send_wallet", f"💰 Your Balance:\n\n🌐 {net_info['name']}\n👛 {row[3]}\n💵 {bal} {net_info['symbol']}\n\n💸 To send: /send_wallet", f"💰 Your Balance:\n\n🌐 {net_info['name']}\n👛 {row[3]}\n💵 {bal} {net_info['symbol']}\n\n💸 To send: /send_wallet"))


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
    await update.message.reply_text(f"⏳ Sending {amount} USDC (Solana)...")
    try:
        sig = await asyncio.get_running_loop().run_in_executor(None, lambda: send_usdc(wallet, amount))
        save_transaction(f"ADMIN-{sig[:24]}", update.effective_user.id, 0, amount, wallet, sig, "completed", "solana")
        text = f"✅ Sent!\n\n💵 {amount} USDC\n👛 {wallet}\n🔗 https://solscan.io/tx/{sig}"
    except Exception as exc:
        text = f"❌ Failed!\n{exc}"
    await update.message.reply_text(text)


async def setup_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = user_lang(update.effective_user.id)
    await update.message.reply_text(lang_text(lang, "🔐 Wallet Setup\n\nআপনার Network বেছে নিন:\n\n⚠️ Private Key AES-256 দিয়ে encrypt হবে\n❓ গাইড: /guide", "🔐 Wallet Setup\n\nChoose your network:\n\n⚠️ Private key will be encrypted with AES-256\n❓ Guide: /guide", "🔐 Wallet Setup\n\nChoose your network:\n\n⚠️ Private key go encrypt with AES-256\n❓ Guide: /guide"), reply_markup=user_network_menu())
    return SETUP_NETWORK


async def setup_network_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = user_lang(query.from_user.id)
    if query.data == "uw_cancel":
        await query.edit_message_text(lang_text(lang, "❌ বাতিল হয়েছে।", "❌ Cancelled.", "❌ Cancelled."))
        return ConversationHandler.END
    network = query.data.replace("uw_", "")
    context.user_data["uw_network"] = network
    net_info = NETWORKS.get(network, {"name": network, "symbol": "?"})
    net_guide = network_guide_text(network, lang)
    await query.edit_message_text(lang_text(lang, f"✅ নেটওয়ার্ক: {net_info['name']}\n\n{net_guide}\n━━━━━━━━━━━━━━━━━━━━━\nএখন আপনার Private Key পাঠান:\n\n⚠️ Message পাঠানোর পর bot স্বয়ংক্রিয়ভাবে মুছে দেবে।", f"✅ Network: {net_info['name']}\n\n{net_guide}\n━━━━━━━━━━━━━━━━━━━━━\nNow send your private key:\n\n⚠️ Bot will delete the message automatically after you send it.", f"✅ Network: {net_info['name']}\n\n{net_guide}\n━━━━━━━━━━━━━━━━━━━━━\nNow send your private key:\n\n⚠️ Bot go delete the message automatically after you send am."))
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
        await update.message.reply_text(f"{lang_text(lang, '❌ Invalid Private Key!', '❌ Invalid Private Key!', '❌ Invalid Private Key!')}\n\n{exc}\n\n{lang_text(lang, 'আবার চেষ্টা করুন:', 'Try again:', 'Try again:')}")
        return SETUP_KEY
    context.user_data["uw_private_key"] = private_key
    context.user_data["uw_wallet_address"] = wallet_address
    await update.message.reply_text(lang_text(lang, f"✅ Key যাচাই সফল!\n\n👛 {wallet_address}\n\nএখন একটি শক্তিশালী Password তৈরি করুন:\n\n• কমপক্ষে ৮ character\n• সংখ্যা ও অক্ষর মিলিয়ে দিন\n• Password ভুললে key recover হবে না!\n\nআপনার password লিখুন:", f"✅ Key verified!\n\n👛 {wallet_address}\n\nNow create a strong password:\n\n• Minimum 8 characters\n• Mix letters and numbers\n• If you forget password, key cannot be recovered!\n\nSend your password:", f"✅ Key verified!\n\n👛 {wallet_address}\n\nNow create strong password:\n\n• Minimum 8 characters\n• Mix letters and numbers\n• If you forget password, key no fit recover!\n\nSend your password:"))
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
        await update.message.reply_text(lang_text(lang, "❌ Password কমপক্ষে ৮ character!\n\nআবার লিখুন:", "❌ Password must be at least 8 characters!\n\nSend again:", "❌ Password must be at least 8 characters!\n\nSend again:"))
        return SETUP_PASSWORD
    try:
        encrypted_key, salt = encrypt_key(private_key, password)
        save_user_wallet(user_id, encrypted_key, salt, network, wallet_addr)
        context.user_data.clear()
        net_info = NETWORKS.get(network, {"name": network, "symbol": "?"})
        await update.message.reply_text(lang_text(lang, f"🎉 Wallet Setup সফল!\n\n🌐 {net_info['name']}\n👛 {wallet_addr}\n\n💰 /mybalance → Balance দেখুন\n💸 /send_wallet → Crypto পাঠান\n🔑 /changekey → Key পরিবর্তন\n🗑️ /deletekey → Key মুছুন\n📖 /guide → ব্যবহার বিধি\n\n⚠️ Password মনে রাখুন!", f"🎉 Wallet Setup successful!\n\n🌐 {net_info['name']}\n👛 {wallet_addr}\n\n💰 /mybalance → Check balance\n💸 /send_wallet → Send crypto\n🔑 /changekey → Change key\n🗑️ /deletekey → Delete key\n📖 /guide → User guide\n\n⚠️ Remember your password!", f"🎉 Wallet Setup successful!\n\n🌐 {net_info['name']}\n👛 {wallet_addr}\n\n💰 /mybalance → Check balance\n💸 /send_wallet → Send crypto\n🔑 /changekey → Change key\n🗑️ /deletekey → Delete key\n📖 /guide → User guide\n\n⚠️ Remember your password!"))
    except Exception as exc:
        await update.message.reply_text(f"{lang_text(lang, '❌ Setup ব্যর্থ!', '❌ Setup failed!', '❌ Setup fail!')}\n{exc}")
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
        save_transaction(f"WALLET-{sig[:24]}", user_id, 0, amount, dest, sig, "completed", network)
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
        await query.answer(ok=False, error_message="Order expired. Please create a new order.")
        return
    order_id, user_id, _username, _network, _wallet, _amount_crypto, stars_amount, status, *_rest = order
    if status != "pending":
        await query.answer(ok=False, error_message="This order was already processed.")
        return
    if str(query.from_user.id) != str(user_id):
        await query.answer(ok=False, error_message="This invoice belongs to another user.")
        return
    if query.currency != "XTR" or int(query.total_amount) != int(stars_amount):
        await query.answer(ok=False, error_message="Payment amount mismatch.")
        return
    await query.answer(ok=True)


async def successful_star_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    payment = update.message.successful_payment
    if payment.currency != "XTR":
        return
    order = get_star_order(payment.invoice_payload)
    if not order:
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
        await update.message.reply_text("❌ Payment verification mismatch. Contact admin.")
        return

    update_star_order_status(order_id, "paid", payment.telegram_payment_charge_id, payment.provider_payment_charge_id)
    await update.message.reply_text(tr("stars_paid_sending", lang))

    try:
        sig = await send_crypto(network, wallet, amount_crypto)
        explorer = f"{net_info['explorer']}{sig}"
        update_star_order_status(order_id, "completed", payment.telegram_payment_charge_id, payment.provider_payment_charge_id, sig)
        save_transaction(f"STAR-{payment.telegram_payment_charge_id}", user_id, 0, amount_crypto, wallet, sig, "completed", network)
        await update.message.reply_text(
            f"{tr('stars_completed', lang)}\n\n"
            f"🌐 {net_info['name']}\n"
            f"💵 {amount_crypto} {net_info['symbol']}\n"
            f"⭐ {stars_amount} Stars\n"
            f"👛 {wallet}\n"
            f"🔗 {explorer}"
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
        save_transaction(f"STAR-{payment.telegram_payment_charge_id}", user_id, 0, amount_crypto, wallet, "", "failed", network)
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
    await update.message.reply_text(guide_text(user_lang(update.effective_user.id)))


async def changekey_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    delete_user_wallet(str(update.effective_user.id))
    await update.message.reply_text("🔄 পুরনো key মুছে দেওয়া হয়েছে!\n\nনতুন wallet setup করুন:")
    return await setup_cmd(update, context)


async def process_bkash(app, text, sender):
    parsed = parse_bkash_payment_notice(text)
    if not parsed:
        return
    trx_id = parsed["trx_id"]
    amount_bdt = parsed["amount_bdt"]

    if trx_exists(trx_id):
        logger.info("Duplicate bKash notice ignored because transaction already exists: %s", trx_id)
        return

    already_saved = sms_exists(trx_id)
    saved_new = save_sms(trx_id, amount_bdt, sender, text)
    logger.info("bKash notice saved: %s BDT | TrxID: %s | source: %s | new: %s", amount_bdt, trx_id, sender, saved_new)

    pending = get_pending_order(trx_id)
    if pending:
        await complete_pending_order_from_sms(app, pending, amount_bdt)
        return

    if already_saved:
        logger.info("Duplicate bKash notice ignored because TrxID was already saved: %s", trx_id)
        return

    try:
        await app.bot.send_message(ADMIN_ID, f"💰 bKash payment notice!\n\n📩 Source: {sender}\n💵 {amount_bdt} BDT\n🔑 TrxID: {trx_id}")
    except Exception as exc:
        logger.error(exc)


async def process_nigeria_payment(app, text, sender):
    parsed = parse_nigeria_payment_notice(text)
    if not parsed:
        return
    trx_id = ng_reference_key(parsed["reference"])
    amount_ngn = parsed["amount_ngn"]
    notice_sender = parsed.get("sender") or sender

    if trx_exists(trx_id):
        logger.info("Duplicate Nigeria notice ignored because transaction already exists: %s", trx_id)
        return

    already_saved = sms_exists(trx_id)
    saved_new = save_sms(trx_id, amount_ngn, notice_sender or sender, text)
    logger.info("Nigeria notice saved: %s NGN | Ref: %s | source: %s | new: %s", amount_ngn, trx_id, sender, saved_new)

    pending = get_pending_order(trx_id)
    if pending:
        await complete_pending_order_from_sms(app, pending, amount_ngn)
        return

    if already_saved:
        logger.info("Duplicate Nigeria notice ignored because reference was already saved: %s", trx_id)
        return

    try:
        await app.bot.send_message(ADMIN_ID, f"🇳🇬 Nigeria payment notice!\n\n📩 Source: {sender}\n🏷️ Parsed sender: {notice_sender}\n💵 {amount_ngn} NGN\n🔑 Reference: {display_reference(trx_id)}")
    except Exception as exc:
        logger.error(exc)


async def complete_pending_order_from_sms(app, pending, sms_amount_bdt):
    trx_id, user_id, expected_bdt, expected_crypto, wallet, network, _created_at = pending[:7]
    order_id = pending[7] if len(pending) > 7 else None
    net_info = NETWORKS.get(network, {"name": network, "symbol": "?", "explorer": ""})
    meta = payment_meta(trx_id)

    if expected_bdt and abs(float(sms_amount_bdt) - float(expected_bdt)) > 0.01:
        keyboard = [[
            InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user_id}_{trx_id}_{network}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user_id}_{trx_id}"),
        ]]
        await app.bot.send_message(
            ADMIN_ID,
            f"⚠️ {meta['method']} notice matched a pending order, but amount is different.\n\n"
            f"🔑 {meta['id_label']}: {display_reference(trx_id)}\n"
            f"👤 User: {user_id}\n"
            f"🌐 {net_info['name']}\n"
            f"🧾 Expected: {expected_bdt} {meta['currency']}\n"
            f"📩 Notice received: {sms_amount_bdt} {meta['currency']}\n\n"
            "Please verify manually.",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return

    rate = get_ngn_rate(network) if str(trx_id).startswith("NGN-") else get_rate(network)
    crypto_amount = expected_crypto or round(float(sms_amount_bdt) / rate, 6)
    sufficient, current_bal = check_sufficient(network, crypto_amount)
    if not sufficient and current_bal is not None:
        await app.bot.send_message(
            ADMIN_ID,
            f"❌ Payment verified but insufficient {net_info['symbol']}.\n\n"
            f"🔑 {meta['id_label']}: {display_reference(trx_id)}\n"
            f"👤 User: {user_id}\n"
            f"💵 Need: {crypto_amount}\n"
            f"💰 Available: {current_bal}",
        )
        return

    try:
        sig = await send_crypto(network, wallet, crypto_amount)
        explorer = f"{net_info['explorer']}{sig}"
        mark_sms_used(trx_id)
        save_transaction(trx_id, user_id, sms_amount_bdt, crypto_amount, wallet, sig, "completed", network, order_id=order_id)
        delete_pending_order(trx_id)
        await app.bot.send_message(
            int(user_id),
            f"🎉 Payment verified automatically!\n\n"
            f"🌐 {net_info['name']}\n"
            f"💰 {sms_amount_bdt} {meta['currency']}\n"
            f"💵 {crypto_amount} {net_info['symbol']}\n"
            f"👛 {wallet}\n"
            f"🔗 {explorer}\n\n"
            "Thank you!",
        )
        await app.bot.send_message(
            ADMIN_ID,
            f"✅ Auto-completed delayed {meta['method']} order.\n\n"
            f"👤 User: {user_id}\n"
            f"🔑 {meta['id_label']}: {display_reference(trx_id)}\n"
            f"🌐 {net_info['name']}\n"
            f"💰 {sms_amount_bdt} {meta['currency']}\n"
            f"💵 {crypto_amount} {net_info['symbol']}\n"
            f"🔗 {explorer}",
        )
    except Exception as exc:
        save_transaction(trx_id, user_id, sms_amount_bdt, crypto_amount, wallet, "", "failed", network, order_id=order_id)
        await app.bot.send_message(
            ADMIN_ID,
            f"🚨 Auto-complete failed after {meta['method']} verification.\n\n"
            f"👤 User: {user_id}\n🔑 {meta['id_label']}: {display_reference(trx_id)}\n🌐 {net_info['name']}\n❌ {exc}",
        )
        logger.error("Auto-complete pending order failed: %s", exc)


def sms_handler(app, loop, text, sender):
    if str(sender).startswith("ng_"):
        asyncio.run_coroutine_threadsafe(process_nigeria_payment(app, text, sender), loop)
    else:
        asyncio.run_coroutine_threadsafe(process_bkash(app, text, sender), loop)


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
    app.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_star_payment))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, waiting_trxid))

    await app.initialize()
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True)

    loop = asyncio.get_running_loop()
    set_callback(lambda txt, sndr: sms_handler(app, loop, txt, sndr))
    threading.Thread(target=run_webhook, daemon=True).start()
    logger.info("Bot started!")

    try:
        await asyncio.Event().wait()
    finally:
        await app.updater.stop()
        await app.stop()
        await app.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
