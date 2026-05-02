import asyncio
import json
import logging
import math
import os
import secrets
import string
import threading
from datetime import datetime, timedelta

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
from config import ADMIN_ID, BKASH_NUMBER, BOT_TOKEN, RATE, STAR_RATE
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
    get_user_language,
    get_wallet,
    mark_sms_used,
    save_pending_order,
    save_sms,
    save_transaction,
    save_wallet,
    set_user_language,
    set_network_rate,
    sms_exists,
    trx_exists,
    save_star_order,
    update_star_order_status,
    use_code,
)
from evm_sender import send_evm_token
from polygon_sender import send_polygon_usdc
from sender import send_usdc
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

RATE_FILE = "rate.json"

NETWORKS = {
    "solana": {"name": "Solana (SOL)", "symbol": "USDC", "explorer": "https://solscan.io/tx/"},
    "polygon": {"name": "Polygon USDC", "symbol": "USDC", "explorer": "https://polygonscan.com/tx/"},
    "bsc": {"name": "BSC USDT (BEP20)", "symbol": "USDT", "explorer": "https://bscscan.com/tx/"},
    "avalanche": {"name": "Avalanche USDT", "symbol": "USDT", "explorer": "https://snowtrace.io/tx/"},
    "ethereum": {"name": "Ethereum USDT (ERC20)", "symbol": "USDT", "explorer": "https://etherscan.io/tx/"},
    "ethereum_usdc": {"name": "Ethereum USDC (ERC20)", "symbol": "USDC", "explorer": "https://etherscan.io/tx/"},
    "base": {"name": "Base USDC", "symbol": "USDC", "explorer": "https://basescan.org/tx/"},
    "trc20": {"name": "Tron USDT (TRC20)", "symbol": "USDT", "explorer": "https://tronscan.org/#/transaction/"},
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
}


def is_admin(user_id) -> bool:
    return str(user_id) == str(ADMIN_ID)


def user_lang(user_id) -> str:
    return get_user_language(user_id) or "bn"


def tr(key, lang="bn", **kwargs):
    value = TEXT.get(key, {}).get(lang) or TEXT.get(key, {}).get("bn") or key
    return value.format(**kwargs) if kwargs else value


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
    return "0x1234abcd..."


def valid_wallet(network, wallet):
    if network == "solana":
        return 32 <= len(wallet) <= 44
    if network == "trc20":
        return wallet.startswith("T") and len(wallet) == 34
    return wallet.startswith("0x") and len(wallet) == 42


def main_menu(user_id, lang=None):
    lang = lang or user_lang(user_id)
    keyboard = [
        [InlineKeyboardButton(tr("buy", lang), callback_data="buy"), InlineKeyboardButton(tr("stars", lang), callback_data="star_buy")],
        [InlineKeyboardButton(tr("gift", lang), callback_data="redeem_menu"), InlineKeyboardButton(tr("rate", lang), callback_data="rate")],
        [InlineKeyboardButton(tr("balance", lang), callback_data="balance"), InlineKeyboardButton(tr("txlog", lang), callback_data="txlog")],
        [InlineKeyboardButton(tr("wallet", lang), callback_data="my_wallet_menu"), InlineKeyboardButton(tr("help", lang), callback_data="help")],
        [InlineKeyboardButton(tr("language", lang), callback_data="language_menu")],
    ]
    if is_admin(user_id):
        keyboard.append([InlineKeyboardButton(tr("set_rate", lang), callback_data="setrate_menu"), InlineKeyboardButton(tr("gen_code", lang), callback_data="gencode_menu")])
        keyboard.append([InlineKeyboardButton(tr("admin_send", lang), callback_data="admin_send"), InlineKeyboardButton(tr("disable_code", lang), callback_data="disable_code_menu")])
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
            [InlineKeyboardButton(tr("cancel", lang), callback_data=cancel_callback)],
        ]
    )


def user_network_menu():
    return network_menu("uw")


def rates_text(title=None, lang="bn"):
    rates = get_all_rates()
    title = title if title is not None else f"💵 {tr('current_rates', lang)}:"
    return (
        f"{title}\n━━━━━━━━━━━━━━━━━━━━━\n"
        f"⬡ Solana USDC:           1 = {rates.get('solana', 0)} BDT\n"
        f"⬡ Polygon USDC:          1 = {rates.get('polygon', 0)} BDT\n"
        f"⬡ BSC USDT (BEP20):      1 = {rates.get('bsc', 0)} BDT\n"
        f"⬡ Avalanche USDT:        1 = {rates.get('avalanche', 0)} BDT\n"
        f"⬡ Ethereum USDT (ERC20): 1 = {rates.get('ethereum', 0)} BDT\n"
        f"⬡ Ethereum USDC (ERC20): 1 = {rates.get('ethereum_usdc', 0)} BDT\n"
        f"⬡ Base USDC:             1 = {rates.get('base', 0)} BDT\n"
        f"⬡ Tron USDT (TRC20):     1 = {rates.get('trc20', 0)} BDT"
    )


def home_text(user_name=None, lang="bn"):
    greeting = f"👋 {tr('welcome', lang)}, {user_name}!\n\n" if user_name else ""
    return (
        "╭────────────────────╮\n"
        f"   {tr('home_title', lang)}\n"
        "╰────────────────────╯\n\n"
        f"{greeting}{rates_text(lang=lang)}\n━━━━━━━━━━━━━━━━━━━━━\n"
        f"📲 bKash: {BKASH_NUMBER}\n\n{tr('select_action', lang)}"
    )


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
    raise ValueError(f"Unsupported network: {network}")


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
            f"📊 {tr('current_rates', lang)}\n\n{rates_text('', lang)}\n\n📲 bKash: {BKASH_NUMBER}\n⚡ 1-3 minutes delivery",
            reply_markup=back_keyboard(lang),
        )

    elif query.data == "balance":
        await query.edit_message_text("⏳ Loading balance..." if lang == "en" else "⏳ ব্যালেন্স লোড হচ্ছে...", reply_markup=back_keyboard(lang))
        try:
            balances, evm_addr = get_all_balances()
            msg = (
                "💰 বর্তমান ব্যালেন্স / Current Balance:\n\n━━━━━━━━━━━━━━━━━━━━━\n"
                f"⬡ Solana USDC:           {balances.get('solana', 'N/A')} USDC\n"
                f"⬡ Polygon USDC:          {balances.get('polygon', 'N/A')} USDC\n"
                f"⬡ BSC USDT (BEP20):      {balances.get('bsc', 'N/A')} USDT\n"
                f"⬡ Avalanche USDT:        {balances.get('avalanche', 'N/A')} USDT\n"
                f"⬡ Ethereum USDT (ERC20): {balances.get('ethereum', 'N/A')} USDT\n"
                f"⬡ Ethereum USDC (ERC20): {balances.get('ethereum_usdc', 'N/A')} USDC\n"
                f"⬡ Base USDC:             {balances.get('base', 'N/A')} USDC\n"
                f"⬡ Tron USDT (TRC20):     {balances.get('trc20', 'N/A')} USDT\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n🔑 EVM Address: {evm_addr}\n\n⚡ Real-time balance"
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
            "❓ সাহায্য / Help\n\n━━━━━━━━━━━━━━━━━━━━━\n📌 কিভাবে কিনবেন:\n\n"
            "1️⃣ USDC/USDT কিনুন বাটনে চাপুন\n2️⃣ নেটওয়ার্ক বেছে নিন\n3️⃣ Wallet address দিন\n"
            "4️⃣ কত টাকার কিনবেন বলুন\n5️⃣ বিকাশে টাকা পাঠান\n6️⃣ TrxID জমা দিন\n7️⃣ Crypto পেয়ে যান!\n\n"
            "🎁 গিফট কোড থাকলে:\nগিফট কোড বাটন → কোড → wallet → পান!\n\n"
            "🔐 নিজের Wallet:\nআমার Wallet বাটন → Setup করুন\n\n━━━━━━━━━━━━━━━━━━━━━\n❓ সমস্যায়: @MdMouno",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 ফিরে যান", callback_data="back")]]),
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
        await query.edit_message_text(f"{tr('select_network', lang)}:\n\n{rates_text('', lang)}", reply_markup=network_menu("network", lang))

    elif query.data == "star_buy":
        context.user_data.clear()
        context.user_data["star_step"] = "network"
        await query.edit_message_text(tr("stars_intro", lang), reply_markup=network_menu("star_network", lang))

    elif query.data == "admin_send":
        if not is_admin(user_id):
            return ConversationHandler.END
        context.user_data.clear()
        context.user_data["admin_send_step"] = "network"
        await query.edit_message_text(tr("admin_send_intro", lang), reply_markup=network_menu("admin_send_network", lang))

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
            f"✅ নেটওয়ার্ক: {net_info['name']}\n💵 রেট: 1 {net_info['symbol']} = {get_rate(network)} BDT\n\n"
            f"{tr('enter_wallet', lang, network=net_info['name'])}:\n\n📋 {tr('example', lang)}: {wallet_hint(network)}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(tr("cancel", lang), callback_data="cancel")]]),
        )
        return WAITING_WALLET

    elif query.data == "confirm_buy":
        await confirm_buy(query, context, user_id, username)

    elif query.data == "cancel":
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
        return "📜 কোনো ট্রানজেকশন নেই।"
    msg = "📜 সর্বশেষ ট্রানজেকশন:\n\n━━━━━━━━━━━━━━━━━━━━━\n"
    for trx_id, bdt, crypto, network, wallet, status, created in rows:
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
        msg += f"{icon} {sd}\n{source}\n💵 {crypto} {ni['symbol']}\n🌐 {ni['name']}\n👛 {sw}\n🔑 {trx_id}\n───────────────────\n"
    return msg


async def txlog_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.reply_text(txlog_text())
    except Exception as exc:
        await update.message.reply_text(f"❌ লোড ব্যর্থ!\n{exc}")


def pending_order_keyboard(row):
    trx_id, user_id, _amount_bdt, _amount_usdc, _wallet, network, _created_at = row
    return [
        InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user_id}_{trx_id}_{network}"),
        InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user_id}_{trx_id}"),
    ]


def pending_orders_text(rows):
    if not rows:
        return "✅ No pending bKash orders."
    msg = "🧾 Pending bKash Orders\n\n"
    for trx_id, user_id, amount_bdt, amount_usdc, wallet, network, created_at in rows:
        net_info = NETWORKS.get(network, {"name": network, "symbol": "?"})
        short_wallet = f"{wallet[:8]}...{wallet[-6:]}" if wallet else "N/A"
        msg += (
            f"🔑 {trx_id}\n"
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
        trx_id, user_id, amount_bdt, amount_usdc, _wallet, network, _created_at = row
        net_info = NETWORKS.get(network, {"name": network, "symbol": "?"})
        await update.message.reply_text(
            f"Verify in bKash app:\n\n🔑 TrxID: {trx_id}\n👤 User: {user_id}\n🌐 {net_info['name']}\n💰 {amount_bdt} BDT\n💵 {amount_usdc} {net_info['symbol']}",
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
        await query.edit_message_text(f"🔐 আমার Wallet Panel\n\n✅ Wallet সংযুক্ত আছে!\n\n🌐 Network: {net_info['name']}\n👛 Address: {row[3]}\n\nনিচের মেনু থেকে কাজ করুন 👇", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        keyboard = [[InlineKeyboardButton("🔐 Wallet সংযুক্ত করুন", callback_data="mw_setup")], [InlineKeyboardButton("📖 ব্যবহার গাইড", callback_data="show_guide")], [InlineKeyboardButton("🔙 ফিরে যান", callback_data="back")]]
        await query.edit_message_text("🔐 আমার Wallet Panel\n\n❌ কোনো Wallet সংযুক্ত নেই!\n\nশুরু করতে নিচের বাটনে চাপুন 👇", reply_markup=InlineKeyboardMarkup(keyboard))


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
    context.user_data["waiting_trxid"] = True
    context.user_data["trx_deadline"] = asyncio.get_event_loop().time() + 900
    await query.edit_message_text(
        (
            f"🎯 {'Order Confirmed' if lang == 'en' else 'অর্ডার কনফার্ম'}!\n\n"
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
    net_info = NETWORKS.get(network, {"name": network, "symbol": "?", "explorer": ""})
    target_wallet = get_wallet(target_uid)
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

    pending = get_pending_order(trx_id)
    if pending:
        amount_bdt = pending[2]
        crypto_amount = pending[3]
        target_wallet = pending[4] or target_wallet

    try:
        sig = await send_crypto(network, target_wallet, crypto_amount)
        explorer = f"{net_info['explorer']}{sig}"
        save_transaction(trx_id, target_uid, amount_bdt, crypto_amount, target_wallet, sig, "completed", network)
        delete_pending_order(trx_id)
        await query.edit_message_text(f"✅ Crypto পাঠানো হয়েছে!\n\n👤 User: {target_uid}\n🔑 TrxID: {trx_id}\n🌐 {net_info['name']}\n💵 {crypto_amount} {net_info['symbol']}\n👛 {target_wallet}\n🔗 {explorer}")
        try:
            await query.get_bot().send_message(int(target_uid), f"🎉 পেমেন্ট confirm হয়েছে!\n\n🌐 {net_info['name']}\n💵 {crypto_amount} {net_info['symbol']}\n👛 {target_wallet}\n🔗 {explorer}\n\nধন্যবাদ! 🙏")
        except Exception:
            pass
    except Exception as exc:
        await query.edit_message_text(f"❌ পাঠাতে ব্যর্থ!\n\n{exc}")
        logger.error("Admin approve send failed: %s", exc)


async def reject_order(query, user_id):
    if not is_admin(user_id):
        return
    _prefix, target_uid, trx_id = query.data.split("_", 2)
    delete_pending_order(trx_id)
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
    await update.message.reply_text(
        f"{tr('wallet_saved', lang)}\n\n🌐 {net_info['name']}\n👛 {wallet}\n\n"
        f"{tr('enter_amount_bdt', lang, symbol=net_info['symbol'])}\n\n"
        f"💵 Rate: 1 {net_info['symbol']} = {get_rate(network)} BDT\n\n{tr('numbers_only', lang)}"
    )
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
        await update.message.reply_text(f"😔 দুঃখিত! এই মুহূর্তে অর্ডার পূরণ সম্ভব নয়।\n\n🌐 {net_info['name']}\n💵 আপনি চাইছেন: {crypto_amount} {net_info['symbol']}\n💰 মজুত: {current_bal} {net_info['symbol']}\n\nঅনুগ্রহ করে কম পরিমাণে অর্ডার করুন।\n❓ @MdMouno")
        return ConversationHandler.END

    context.user_data["amount_bdt"] = amount_bdt
    context.user_data["usdc_amount"] = crypto_amount
    keyboard = [[InlineKeyboardButton(tr("confirm", lang), callback_data="confirm_buy"), InlineKeyboardButton(tr("cancel", lang), callback_data="cancel")]]
    await update.message.reply_text(
        f"{tr('order_summary', lang)}\n━━━━━━━━━━━━━━━━━━━━━\n"
        f"🌐 Network: {net_info['name']}\n"
        f"💰 {tr('send_bdt', lang)}: {amount_bdt} BDT\n"
        f"💵 {tr('receive_crypto', lang)}: {crypto_amount} {net_info['symbol']}\n"
        f"📈 Rate: 1 {net_info['symbol']} = {rate} BDT\n"
        f"👛 Wallet: {context.user_data['wallet']}\n━━━━━━━━━━━━━━━━━━━━━\n\n{tr('confirm_prompt', lang)}",
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
            f"❌ Insufficient {net_info['symbol']} stock.\n\nNeed: {amount_crypto}\nAvailable: {current_bal}"
            if lang == "en"
            else f"❌ পর্যাপ্ত {net_info['symbol']} নেই।\n\nদরকার: {amount_crypto}\nআছে: {current_bal}"
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
        f"👛 {wallet}"
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
        f"👛 {wallet}{stock_line}\n\n"
        f"{tr('admin_send_confirm', lang)}",
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
        context.user_data.clear()
        await update.message.reply_text("⏰ সময়সীমা শেষ!\n\nআবার অর্ডার করুন /start দিয়ে\n\n❓ @MdMouno")
        return

    trx_id = update.message.text.strip().upper()
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
        save_pending_order(trx_id, user_id, amount_bdt, crypto_amount, wallet, network)
        keyboard = [[InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user_id}_{trx_id}_{network}"), InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user_id}_{trx_id}")]]
        try:
            await update.get_bot().send_message(ADMIN_ID, f"⚠️ SMS পাওয়া যায়নি! Manual Verify দরকার।\n\n👤 User: @{username} ({user_id})\n🔑 TrxID: {trx_id}\n💰 Amount: {amount_bdt} BDT\n💵 Est: {crypto_amount} {net_info['symbol']}\n🌐 Network: {net_info['name']}\n👛 Wallet: {wallet}\n\nbKash এ TrxID যাচাই করে Approve বা Reject করুন:", reply_markup=InlineKeyboardMarkup(keyboard))
        except Exception as exc:
            logger.error(exc)
        await update.message.reply_text(f"⏳ TrxID যাচাই করা হচ্ছে।\n\n🔑 TrxID: {trx_id}\n\nAdmin যাচাই করছেন, একটু অপেক্ষা করুন...")
        return

    amount_bdt = sms_row[1]
    crypto_amount = round(amount_bdt / get_rate(network), 6)
    sufficient, current_bal = check_sufficient(network, crypto_amount)
    if not sufficient and current_bal is not None:
        await update.message.reply_text(f"❌ পর্যাপ্ত {net_info['symbol']} নেই!\n\n🌐 {net_info['name']}\n💵 চান: {crypto_amount}\n💰 আছে: {current_bal}\n\n📞 @MdMouno")
        return

    await update.message.reply_text(f"✅ পেমেন্ট যাচাই সফল!\n\n🌐 {net_info['name']}\n💰 {amount_bdt} BDT = {crypto_amount} {net_info['symbol']}\n👛 {wallet}\n\n⏳ পাঠানো হচ্ছে...")
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
    await update.message.reply_text(f"⏳ {net_info['symbol']} পাঠানো হচ্ছে...\n\n🌐 {net_info['name']}\n💵 {amount_crypto} {net_info['symbol']}\n👛 {wallet}")
    try:
        sig = await send_crypto(network, wallet, amount_crypto)
        explorer = f"{net_info['explorer']}{sig}"
        use_code(code, user_id)
        save_transaction(f"GIFT-{code}", user_id, 0, amount_crypto, wallet, sig, "completed", network)
        await update.message.reply_text(f"🎉 {net_info['symbol']} পাঠানো হয়েছে!\n\n🎁 {amount_crypto} {net_info['symbol']}\n🌐 {net_info['name']}\n👛 {wallet}\n🔗 {explorer}\n\nধন্যবাদ! 🙏")
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
    await update.message.reply_text(f"⏳ Sending {amount} USDC (Solana)...")
    try:
        sig = await asyncio.get_running_loop().run_in_executor(None, lambda: send_usdc(wallet, amount))
        save_transaction(f"ADMIN-{sig[:24]}", update.effective_user.id, 0, amount, wallet, sig, "completed", "solana")
        text = f"✅ Sent!\n\n💵 {amount} USDC\n👛 {wallet}\n🔗 https://solscan.io/tx/{sig}"
    except Exception as exc:
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
    await update.message.reply_text(GUIDE)


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


async def complete_pending_order_from_sms(app, pending, sms_amount_bdt):
    trx_id, user_id, expected_bdt, expected_crypto, wallet, network, _created_at = pending
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
    sufficient, current_bal = check_sufficient(network, crypto_amount)
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
        save_transaction(trx_id, user_id, sms_amount_bdt, crypto_amount, wallet, sig, "completed", network)
        delete_pending_order(trx_id)
        await app.bot.send_message(
            int(user_id),
            f"🎉 Payment verified automatically!\n\n"
            f"🌐 {net_info['name']}\n"
            f"💵 {crypto_amount} {net_info['symbol']}\n"
            f"👛 {wallet}\n"
            f"🔗 {explorer}\n\n"
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
        save_transaction(trx_id, user_id, sms_amount_bdt, crypto_amount, wallet, "", "failed", network)
        await app.bot.send_message(
            ADMIN_ID,
            f"🚨 Auto-complete failed after bKash SMS verification.\n\n"
            f"👤 User: {user_id}\n🔑 TrxID: {trx_id}\n🌐 {net_info['name']}\n❌ {exc}",
        )
        logger.error("Auto-complete pending order failed: %s", exc)


def sms_handler(app, loop, text, sender):
    asyncio.run_coroutine_threadsafe(process_bkash(app, text, sender), loop)


async def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is not configured")

    request = HTTPXRequest(connection_pool_size=8, read_timeout=60, write_timeout=60, connect_timeout=60, pool_timeout=60)
    app = Application.builder().token(BOT_TOKEN).request(request).build()

    buy_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_handler, pattern="^network_(solana|polygon|bsc|avalanche|ethereum|ethereum_usdc|base|trc20)$")],
        states={WAITING_WALLET: [MessageHandler(filters.TEXT & ~filters.COMMAND, waiting_wallet)], WAITING_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, waiting_amount)]},
        fallbacks=[CommandHandler("start", start), CallbackQueryHandler(button_handler, pattern="^cancel$")],
    )
    star_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_handler, pattern="^star_network_(solana|polygon|bsc|avalanche|ethereum|ethereum_usdc|base|trc20)$")],
        states={
            WAITING_STAR_WALLET: [MessageHandler(filters.TEXT & ~filters.COMMAND, waiting_star_wallet)],
            WAITING_STAR_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, waiting_star_amount)],
        },
        fallbacks=[CommandHandler("start", start), CallbackQueryHandler(button_handler, pattern="^cancel$")],
    )
    admin_send_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_handler, pattern="^admin_send_network_(solana|polygon|bsc|avalanche|ethereum|ethereum_usdc|base|trc20)$")],
        states={
            ADMIN_SEND_WALLET: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_send_wallet_received)],
            ADMIN_SEND_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_send_amount_received)],
        },
        fallbacks=[CommandHandler("start", start), CallbackQueryHandler(button_handler, pattern="^admin_send_cancel$")],
    )
    rate_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_handler, pattern="^setrate_(solana|polygon|bsc|avalanche|ethereum|ethereum_usdc|base|trc20)$")],
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
    app.add_handler(CommandHandler("txlog", txlog_cmd))
    app.add_handler(CommandHandler("mybalance", mybalance_cmd))
    app.add_handler(CommandHandler("guide", guide_cmd))
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
