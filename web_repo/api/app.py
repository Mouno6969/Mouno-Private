import os
import re
import secrets
import time
import logging
import jwt
from pathlib import Path
import datetime
from functools import wraps
from flask import Flask, request, jsonify
from flask_cors import CORS

# flask_socketio is optional: if it is not installed on the server, the app
# must still start so that all REST endpoints (marketplace, tools) keep working.
try:
    from flask_socketio import SocketIO
    _SOCKETIO_AVAILABLE = True
except ImportError:
    SocketIO = None
    _SOCKETIO_AVAILABLE = False
from werkzeug.security import generate_password_hash, check_password_hash
import sys
import requests as http_requests

import db
import config
import notifier
from balance import get_all_balances
from swap_service import quote_lifi, summarize_quote, get_lifi_chains, fetch_token_price_usd
from crypto_manager import (
    get_user_balance, send_from_user_wallet, get_wallet_address, encrypt_key, save_user_wallet,
    add_user_wallet, list_user_wallets, delete_user_wallet_by_id, send_from_wallet,
    list_wallet_balances, has_master_password, verify_master_password,
    get_user_evm_wallet, get_user_solana_wallet, get_user_wallet, decrypt_key,
)
import automation_service
from automation_vault import (
    init_automation_vault, store_auto_password, has_auto_password,
    get_auto_password,
)

logger = logging.getLogger(__name__)


def notify_admin_telegram(message):
    """Send a Telegram notification to the admin (best-effort, never raises)."""
    if not config.BOT_TOKEN or not config.ADMIN_ID:
        return
    try:
        http_requests.post(
            f"https://api.telegram.org/bot{config.BOT_TOKEN}/sendMessage",
            json={"chat_id": config.ADMIN_ID, "text": message},
            timeout=5,
        )
    except Exception as exc:
        logger.warning("Admin Telegram notification failed: %s", exc)


def broadcast_sellers_update():
    """Broadcast updated sellers list to all connected clients via WebSocket."""
    try:
        sellers = db.list_sellers_by_status("approved", 30)
        result = []
        for s in sellers:
            seller_id = s[0]
            wallets = db.list_enabled_seller_wallets(seller_id)
            networks = []
            for w in wallets:
                network = w[1]
                rate = db.get_seller_rate(seller_id, network) or db.get_network_rate(network) or config.RATE
                networks.append({'network': network, 'rate': rate})
            if not networks:
                continue
            result.append({
                'seller_id': str(seller_id),
                'display_name': s[2],
                'support_contact': s[4],
                'bkash_number': s[3],
                'networks': networks,
            })
        socketio.emit('sellers_updated', {'sellers': result})
    except Exception as exc:
        logger.error("Broadcast sellers update failed: %s", exc)

app = Flask(__name__, static_folder=None)

# Restrict CORS to known origins instead of allowing every site to make
# credentialed requests to a money-handling API. Origins come from config
# (env-overridable); "*" should only ever be used for local development.
#
# Note: the CORS spec forbids combining a "*" origin with credentials, and
# browsers reject such responses outright. So we only enable credentials when
# we have an explicit allow-list; the wildcard dev fallback runs without them.
_ALLOWED_ORIGINS = config.ALLOWED_ORIGINS or ["*"]
_CORS_SUPPORTS_CREDENTIALS = _ALLOWED_ORIGINS != ["*"]
CORS(app, origins=_ALLOWED_ORIGINS, supports_credentials=_CORS_SUPPORTS_CREDENTIALS)


class _NoopSocketIO:
    """Fallback used when flask_socketio is not installed.

    REST endpoints keep working; realtime broadcasts become no-ops and the
    server runs with the plain Flask development/WSGI runner.
    """

    def emit(self, *args, **kwargs):
        pass

    def on(self, *args, **kwargs):
        def decorator(f):
            return f
        return decorator

    def run(self, flask_app, host="0.0.0.0", port=5001, **kwargs):
        flask_app.run(host=host, port=port)


if _SOCKETIO_AVAILABLE:
    socketio = SocketIO(app, cors_allowed_origins=_ALLOWED_ORIGINS, async_mode='threading')
else:
    logger.warning(
        "flask_socketio is not installed - realtime updates disabled. "
        "Run 'pip install -r requirements.txt' to enable WebSocket support."
    )
    socketio = _NoopSocketIO()
_SECRET = os.getenv("WEB_SECRET_KEY")
if not _SECRET:
    raise RuntimeError("WEB_SECRET_KEY must be set in the environment")
app.config['SECRET_KEY'] = _SECRET


@app.after_request
def set_security_headers(response):
    """Attach baseline security headers to every response.

    Defends against clickjacking, MIME sniffing and referrer leakage, and asks
    browsers to pin HTTPS. The CSP is intentionally permissive about styles
    (Tailwind injects inline styles) but blocks framing and restricts default
    sources to same-origin. Tune as needed for any future third-party embeds.
    """
    response.headers.setdefault('X-Frame-Options', 'DENY')
    response.headers.setdefault('X-Content-Type-Options', 'nosniff')
    response.headers.setdefault('Referrer-Policy', 'strict-origin-when-cross-origin')
    response.headers.setdefault(
        'Strict-Transport-Security', 'max-age=31536000; includeSubDomains'
    )
    response.headers.setdefault('Permissions-Policy', 'geolocation=(), microphone=(), camera=()')
    response.headers.setdefault(
        'Content-Security-Policy',
        "default-src 'self'; "
        "img-src 'self' data: https:; "
        "style-src 'self' 'unsafe-inline'; "
        "script-src 'self'; "
        "connect-src 'self' https: wss:; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "object-src 'none'"
    )
    return response


# Ensure automation tables exist on startup. These share the same SQLite DB
# (mouno.db) as the Telegram bot, whose limit_order_monitor / scheduled_buy_runner
# background workers execute web-created automations. The web app only creates
# rows + the auto-sign vault; it never runs its own scheduler/background thread.
try:
    automation_service.init_automation_tables()
    init_automation_vault()
except Exception as _exc:  # never block app startup on schema init
    logger.error("Automation table init failed: %s", _exc)

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        try:
            if token.startswith("Bearer "):
                token = token[7:]
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = db.get_web_user(data['username'])
            if not current_user:
                return jsonify({'message': 'User not found!'}), 401
        except Exception as e:
            return jsonify({'message': 'Token is invalid!', 'error': str(e)}), 401
        return f(current_user, *args, **kwargs)
    return decorated

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'message': 'Username and password required'}), 400

    hashed_password = generate_password_hash(data['password'], method='pbkdf2:sha256')
    if db.create_web_user(data['username'], hashed_password):
        return jsonify({'message': 'User created successfully'}), 201
    else:
        return jsonify({'message': 'Username already exists'}), 400

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'message': 'Username and password required'}), 400

    user = db.get_web_user(data['username'])
    if not user:
        return jsonify({'message': 'Invalid credentials'}), 401

    if check_password_hash(user[2], data['password']):
        token = jwt.encode({
            'username': user[1],
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        }, app.config['SECRET_KEY'], algorithm="HS256")

        return jsonify({
            'token': token,
            'username': user[1],
            'telegram_id': user[3]
        })

    return jsonify({'message': 'Invalid credentials'}), 401

@app.route('/api/market', methods=['GET'])
def get_market():
    networks = ["solana", "trc20", "polygon", "bsc", "ton", "avalanche", "ethereum", "ethereum_usdc", "base"]
    rates = {}
    for net in networks:
        rate = db.get_network_rate(net) or config.RATE
        rates[net] = rate

    return jsonify({
        'rates': rates,
        'bKash': config.BKASH_NUMBER,
        'support': config.SUPPORT_USERNAME
    })

@app.route('/api/me', methods=['GET'])
@token_required
def get_me(current_user):
    telegram_stats = None
    if current_user[3]:
        telegram_stats = db.get_user_analytics(current_user[3])

    return jsonify({
        'username': current_user[1],
        'telegram_id': current_user[3],
        'created_at': current_user[4],
        'telegram_stats': telegram_stats
    })

@app.route('/api/orders', methods=['GET'])
@token_required
def get_user_orders(current_user):
    user_id = current_user[3] if current_user[3] else f"web_{current_user[0]}"
    with db.closing(db.connect()) as con:
        orders = con.execute(
            "SELECT trx_id, order_id, amount_bdt, amount_usdc, network, wallet, status, created_at FROM transactions WHERE user_id=? ORDER BY created_at DESC",
            (str(user_id),)
        ).fetchall()

        pending = con.execute(
            "SELECT trx_id, order_id, amount_bdt, amount_usdc, network, wallet, created_at FROM pending_orders WHERE user_id=? ORDER BY created_at DESC",
            (str(user_id),)
        ).fetchall()

    return jsonify({
        'completed': [dict(zip(['trx_id', 'order_id', 'amount_bdt', 'amount_usdc', 'network', 'wallet', 'status', 'created_at'], row)) for row in orders],
        'pending': [dict(zip(['trx_id', 'order_id', 'amount_bdt', 'amount_usdc', 'network', 'wallet', 'created_at'], row)) for row in pending]
    })

@app.route('/api/buy', methods=['POST'])
@token_required
def buy_crypto(current_user):
    user_id = current_user[3] if current_user[3] else f"web_{current_user[0]}"

    data = request.get_json() or {}
    try:
        amount_bdt = float(data.get('amount_bdt'))
    except (TypeError, ValueError):
        return jsonify({'message': 'Valid amount_bdt required'}), 400
    trx_id = (data.get('trx_id') or '').strip().upper()
    network = data.get('network'); wallet = data.get('wallet')
    if not (trx_id and network and wallet):
        return jsonify({'message': 'network, wallet and trx_id required'}), 400

    if db.trx_exists(trx_id):
        return jsonify({'message': 'This TrxID has already been used'}), 400

    rate = db.get_network_rate(network) or config.RATE
    amount_usdc = round(amount_bdt / rate, 6)

    order_id = db.save_pending_order(trx_id, user_id, amount_bdt, amount_usdc, wallet, network)

    # Add audit log
    db.add_audit(user_id, "web_buy_order_created", "pending_order", order_id, f"network={network} amount={amount_bdt} BDT")

    # Notify admin via Telegram (like the bot does)
    sms = db.get_sms(trx_id)
    if sms:
        notify_admin_telegram(
            "\U0001f6a8 Web order placed & bKash SMS already received!\n\n"
            f"\U0001f4e6 Order: {order_id}\n"
            f"\U0001f464 User: {user_id}\n"
            f"\U0001f4b5 Amount: {amount_bdt} BDT \u2192 {amount_usdc} USDC\n"
            f"\U0001f310 Network: {network}\n"
            f"\U0001f4b3 Wallet: {wallet}\n"
            f"\U0001f511 TrxID: {trx_id}\n\n"
            "\u26a0\ufe0f Payment was already received before the order. "
            "The bot should auto-match on the next webhook cycle, or approve manually."
        )
    else:
        notify_admin_telegram(
            "\U0001f6d2 New web order placed\n\n"
            f"\U0001f4e6 Order: {order_id}\n"
            f"\U0001f464 User: {user_id}\n"
            f"\U0001f4b5 Amount: {amount_bdt} BDT \u2192 {amount_usdc} USDC\n"
            f"\U0001f310 Network: {network}\n"
            f"\U0001f4b3 Wallet: {wallet}\n"
            f"\U0001f511 TrxID: {trx_id}\n\n"
            "Waiting for bKash payment confirmation."
        )

    # Fire webhook notification for the transaction (best-effort).
    try:
        notifier.notify_event(
            "transaction",
            f"New web order placed\n"
            f"Order: {order_id}\n"
            f"User: {user_id}\n"
            f"Amount: {amount_bdt} BDT -> {amount_usdc} USDC\n"
            f"Network: {network}",
        )
    except Exception as exc:
        logger.warning("Transaction notification failed: %s", exc)

    return jsonify({
        'status': 'pending',
        'order_id': order_id,
        'message': 'Order submitted successfully! Our system will verify the bKash payment and deliver your crypto automatically.'
    })

@app.route('/api/swap/chains', methods=['GET'])
def get_chains():
    try:
        chains = get_lifi_chains(api_key=config.LIFI_API_KEY)
        return jsonify(chains)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/swap/quote', methods=['GET'])
def swap_quote():
    fromChain = request.args.get('fromChain')
    toChain = request.args.get('toChain')
    fromToken = request.args.get('fromToken')
    toToken = request.args.get('toToken')
    amount = request.args.get('amount')
    fromAddress = request.args.get('fromAddress')

    try:
        intent = {
            "from_chain_id": fromChain,
            "to_chain_id": toChain,
            "from_token": fromToken,
            "to_token": toToken,
            "amount": amount,
            "wallet": fromAddress
        }
        quote = quote_lifi(intent, api_key=config.LIFI_API_KEY)
        summary = summarize_quote(quote)
        return jsonify({**quote, "summary": summary})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/referral', methods=['GET'])
@token_required
def get_referral(current_user):
    if not current_user[3]:
        return jsonify({'message': 'Telegram account not linked'}), 400

    stats = db.referral_stats(current_user[3])
    code = db.get_or_create_referral_code(current_user[3])
    enabled = db.get_setting("referral_enabled", "off") == "on"

    return jsonify({
        'stats': stats,
        'code': code,
        'enabled': enabled,
        'min_withdraw': db.get_setting("referral_min_withdraw_usd", "1")
    })

@app.route('/api/gift/redeem', methods=['POST'])
@token_required
def redeem_gift(current_user):
    data = request.get_json() or {}
    code = (data.get('code') or '').strip().upper()
    wallet = (data.get('wallet') or '').strip()

    if not code or not wallet:
        return jsonify({'message': 'Code and wallet required'}), 400

    user_id = current_user[3] if current_user[3] else f"web_{current_user[0]}"
    username = current_user[1]

    # Peek at the code to determine if it's a giveaway code
    peek = db.get_code(code)
    if not peek:
        return jsonify({'message': 'Code not found'}), 404
    giveaway_id = peek[7] if len(peek) > 7 else None

    if giveaway_id:
        # Giveaway codes: claim_giveaway_code uses BEGIN IMMEDIATE (atomic)
        claim = db.claim_giveaway_code(code, user_id)
        if not claim.get("ok"):
            reason = claim.get("reason", "unknown")
            msgs = {
                "used": "This code has already been claimed",
                "expired": "This code has expired",
                "fully_claimed": "Giveaway is already fully claimed",
                "not_found": "Code not found",
            }
            return jsonify({'message': msgs.get(reason, f"Could not claim: {reason}")}), 400
        network = claim.get("network", "solana")
        amount_crypto = claim.get("amount", 0)
    else:
        # Non-giveaway codes: use_code_if_available uses BEGIN IMMEDIATE (atomic)
        # This prevents double-spend race conditions
        row, error = db.use_code_if_available(code, user_id)
        if error:
            msgs = {
                "not_found": ("Code not found", 404),
                "used": ("This code has already been used", 400),
                "expired": ("This code has expired", 400),
            }
            msg, status_code = msgs.get(error, (f"Could not redeem: {error}", 400))
            return jsonify({'message': msg}), status_code
        amount_crypto = row[1]
        network = row[6] or 'solana'

    status = "pending"
    sig = ""

    try:
        _repo_root = str(Path(__file__).resolve().parent.parent.parent)
        if _repo_root not in sys.path:
            sys.path.insert(0, _repo_root)
        from sender import send_usdc
        from bsc_sender import send_bsc_usdt
        from polygon_sender import send_polygon_usdc
        from evm_sender import send_evm_token
        from tron_sender import send_trc20_usdt
        from ton_sender import send_ton

        if network == "solana":
            sig = send_usdc(wallet, amount_crypto)
        elif network == "polygon":
            sig = send_polygon_usdc(wallet, amount_crypto)
        elif network == "bsc":
            sig = send_bsc_usdt(wallet, amount_crypto)
        elif network == "trc20":
            sig = send_trc20_usdt(wallet, amount_crypto)
        elif network == "ton":
            sig = send_ton(wallet, amount_crypto)
        elif network in ("avalanche", "ethereum", "ethereum_usdc", "base"):
            asset = "usdc" if network in ("ethereum_usdc", "base") else "usdt"
            chain = "ethereum" if network == "ethereum_usdc" else network
            sig = send_evm_token(chain, asset, wallet, amount_crypto)
        else:
            sig = ""
        status = "completed"
        db.save_transaction(f"GIFT-{code}", user_id, 0, amount_crypto, wallet, sig or "", status, network, source="gift" if not giveaway_id else "giveaway")
    except Exception as exc:
        logger.error("Gift delivery failed: %s", exc)
        status = "failed"
        db.save_transaction(f"GIFT-{code}", user_id, 0, amount_crypto, wallet, "", status, network, source="gift" if not giveaway_id else "giveaway")

    notify_admin_telegram(
        f"{'✅' if status == 'completed' else '❌'} Web gift code redeemed\n\n"
        f"📦 Code: {code}\n"
        f"👤 User: {username} ({user_id})\n"
        f"💵 Amount: {amount_crypto} ({network})\n"
        f"📳 Wallet: {wallet}\n"
        f"📊 Status: {status}\n"
        f"🔗 Sig: {sig or 'N/A'}"
    )

    # Fire webhook notification: a giveaway / gift bonus was credited.
    try:
        notifier.notify_event(
            "giveaway_result" if giveaway_id else "referral_bonus",
            f"{'Giveaway' if giveaway_id else 'Gift'} code redeemed\n"
            f"Code: {code}\n"
            f"User: {username} ({user_id})\n"
            f"Amount: {amount_crypto} ({network})\n"
            f"Status: {status}",
        )
    except Exception as exc:
        logger.warning("Gift/giveaway notification failed: %s", exc)

    # In-app notification: a giveaway / referral bonus was credited to this user.
    try:
        if status == "completed":
            is_giveaway = bool(giveaway_id)
            db.create_notification(
                _uid(current_user),
                'bonus',
                ('Giveaway reward received' if is_giveaway else 'Gift code redeemed'),
                f"{amount_crypto} {str(network).upper()} has been credited to your wallet.",
                metadata={'ref': f'gift:{code}', 'network': network, 'amount': amount_crypto},
            )
    except Exception as exc:
        logger.warning("In-app bonus notification failed: %s", exc)

    if status == "completed":
        return jsonify({'message': f'Gift redeemed! {amount_crypto} sent to your wallet.', 'status': 'completed', 'sig': sig}), 200
    else:
        return jsonify({'message': 'Code claimed but delivery failed. Admin has been notified and will send manually.', 'status': 'failed'}), 202

from ai_service import ask_ai_support
import honcho_memory
from concurrent.futures import ThreadPoolExecutor

# Small pool for fetching Honcho memory concurrently with the AI call so the
# remote Honcho round-trip does not add serial latency to every chat reply.
_honcho_executor = ThreadPoolExecutor(max_workers=4)


def _recent_chat_context(session_id, user_id):
    """Build context from recent locally-stored turns (fast, no network)."""
    try:
        recent = db.get_recent_chat_messages(session_id, user_id, limit=8)
        if not recent:
            return ""
        lines = []
        for m in recent:
            speaker = "User" if m["role"] == "user" else "AI"
            lines.append(f"{speaker}: {m['content']}")
        return "Recent conversation in this chat:\n" + "\n".join(lines)
    except Exception as exc:
        logger.warning("Recent chat context failed: %s", exc)
        return ""


def _honcho_context(session_id, user_id, question):
    """Fetch Honcho insight (remote, possibly slow). Never raises."""
    try:
        honcho_ctx = honcho_memory.get_memory_context(
            f"web-{session_id}", f"web-user-{user_id}", question
        )
        if honcho_ctx:
            return "What we know about this user:\n" + honcho_ctx
    except Exception as exc:
        logger.warning("Honcho web context failed: %s", exc)
    return ""


@app.route('/api/ai/honcho-health', methods=['GET'])
@token_required
def ai_honcho_health(current_user):
    """Admin-only diagnostic: shows whether Honcho memory is wired up correctly."""
    telegram_id = current_user[3]
    if not telegram_id or str(telegram_id) != str(config.ADMIN_ID):
        return jsonify({'message': 'Forbidden'}), 403
    try:
        return jsonify(honcho_memory.health()), 200
    except Exception as exc:
        return jsonify({'error': str(exc)}), 500


@app.route('/api/ai/sessions', methods=['GET'])
@token_required
def ai_list_sessions(current_user):
    sessions = db.list_chat_sessions(current_user[0])
    return jsonify({'sessions': sessions}), 200


@app.route('/api/ai/sessions', methods=['POST'])
@token_required
def ai_create_session(current_user):
    data = request.get_json() or {}
    title = (data.get('title') or 'New chat')[:120]
    session_id = db.create_chat_session(current_user[0], title)
    return jsonify({'session_id': session_id, 'title': title}), 201


@app.route('/api/ai/sessions/<int:session_id>/messages', methods=['GET'])
@token_required
def ai_session_messages(current_user, session_id):
    messages = db.get_chat_messages(session_id, current_user[0])
    if messages is None:
        return jsonify({'message': 'Session not found'}), 404
    return jsonify({'messages': messages}), 200


@app.route('/api/ai/sessions/<int:session_id>', methods=['DELETE'])
@token_required
def ai_delete_session(current_user, session_id):
    ok = db.delete_chat_session(session_id, current_user[0])
    if not ok:
        return jsonify({'message': 'Session not found'}), 404
    return jsonify({'message': 'Deleted'}), 200


@app.route('/api/ai/chat', methods=['POST'])
@token_required
def ai_chat(current_user):
    data = request.get_json() or {}
    question = (data.get('question') or '').strip()
    if not question:
        return jsonify({'message': 'Question required'}), 400

    user_id = current_user[0]

    # Coerce session_id to int; treat anything non-numeric as "no session".
    raw_session_id = data.get('session_id')
    try:
        session_id = int(raw_session_id) if raw_session_id is not None else None
    except (TypeError, ValueError):
        session_id = None

    # Create a session on the fly if none was provided / it isn't ours.
    if not session_id or db.get_chat_messages(session_id, user_id) is None:
        session_id = db.create_chat_session(user_id)

    # Persist the user's message first so history is never lost.
    db.add_chat_message(session_id, user_id, 'user', question)

    # Kick off the (possibly slow) Honcho memory lookup concurrently so it
    # overlaps with building local context, instead of blocking serially.
    honcho_future = _honcho_executor.submit(_honcho_context, session_id, user_id, question)
    recent_context = _recent_chat_context(session_id, user_id)

    try:
        honcho_context = honcho_future.result(timeout=4)
    except Exception:
        honcho_context = ""

    context_text = "\n\n".join(p for p in (honcho_context, recent_context) if p)[:4000]

    try:
        answer = ask_ai_support(question, context=context_text or None)
    except Exception as exc:
        logger.error("AI chat error: %s", exc)
        answer = "Sorry, AI support is temporarily unavailable. Please try again later."

    db.add_chat_message(session_id, user_id, 'assistant', answer)

    # Record into Honcho so future turns remember this exchange (best-effort).
    try:
        honcho_memory.record_turn(f"web-{session_id}", f"web-user-{user_id}", question, answer)
    except Exception as exc:
        logger.warning("Honcho record_turn (web) failed: %s", exc)

    return jsonify({
        'answer': answer,
        'session_id': session_id,
        'suggest_escalation': _should_suggest_escalation(answer),
    }), 200


# ─── Support ticketing (human escalation) ───

# Low-confidence / "I don't know" style phrases that signal the AI couldn't
# resolve the question, so we surface an escalate-to-human option.
_ESCALATION_PHRASES = (
    "i don't know", "i do not know", "i'm not sure", "i am not sure",
    "i cannot help", "i can't help", "contact support", "contact our support",
    "temporarily unavailable", "currently unavailable", "no ai provider",
    "reach out to support", "human agent", "speak to a human",
    "আমি জানি না", "নিশ্চিত নই", "সাপোর্টে যোগাযোগ",
)


def _should_suggest_escalation(answer):
    """Heuristic: did the AI fail to resolve the question?"""
    if not answer:
        return True
    low = answer.lower()
    return any(phrase in low for phrase in _ESCALATION_PHRASES)


@app.route('/api/support/tickets', methods=['POST'])
@token_required
def create_ticket(current_user):
    data = request.get_json() or {}
    user_id = current_user[0]
    subject = (data.get('subject') or 'Support request').strip()[:200]

    raw_session_id = data.get('session_id')
    try:
        session_id = int(raw_session_id) if raw_session_id is not None else None
    except (TypeError, ValueError):
        session_id = None

    # Carry over the recent transcript from the linked AI chat session.
    transcript = None
    if session_id:
        transcript = db.get_recent_chat_messages(session_id, user_id, limit=20) or None

    priority = (data.get('priority') or 'normal')
    ticket = db.create_support_ticket(
        user_id, subject, session_id=session_id, priority=priority, transcript=transcript
    )

    # Notify the support channel (best-effort, never blocks the response).
    try:
        notifier.notify_event(
            "ticket_created",
            f"New support ticket #{ticket['id']}\n"
            f"User: {current_user[1]} (id {user_id})\n"
            f"Subject: {ticket['subject']}\n"
            f"Priority: {ticket['priority']}",
        )
    except Exception as exc:
        logger.warning("Ticket notification failed: %s", exc)

    return jsonify({'ticket': ticket}), 201


@app.route('/api/support/tickets', methods=['GET'])
@token_required
def list_tickets(current_user):
    tickets = db.list_support_tickets(current_user[0])
    return jsonify({'tickets': tickets}), 200


@app.route('/api/support/tickets/<int:ticket_id>', methods=['GET'])
@token_required
def get_ticket(current_user, ticket_id):
    ticket = db.get_support_ticket(ticket_id, current_user[0])
    if ticket is None:
        return jsonify({'message': 'Ticket not found'}), 404
    return jsonify({'ticket': ticket}), 200


@app.route('/api/support/tickets/<int:ticket_id>/messages', methods=['POST'])
@token_required
def add_ticket_reply(current_user, ticket_id):
    data = request.get_json() or {}
    body = (data.get('body') or '').strip()
    if not body:
        return jsonify({'message': 'Message body required'}), 400
    ok = db.add_ticket_message(ticket_id, current_user[0], 'user', body)
    if not ok:
        return jsonify({'message': 'Ticket not found'}), 404
    ticket = db.get_support_ticket(ticket_id, current_user[0])
    return jsonify({'ticket': ticket}), 201


@app.route('/api/support/tickets/<int:ticket_id>', methods=['PATCH'])
@token_required
def patch_ticket(current_user, ticket_id):
    data = request.get_json() or {}
    status = (data.get('status') or '').strip().lower()
    if status not in ('open', 'pending', 'resolved', 'closed'):
        return jsonify({'message': 'Invalid status'}), 400
    ticket = db.update_ticket_status(ticket_id, current_user[0], status)
    if ticket is None:
        return jsonify({'message': 'Ticket not found'}), 404
    return jsonify({'ticket': ticket}), 200


@app.route('/api/link-telegram', methods=['POST'])
@token_required
def link_telegram(current_user):
    data = request.get_json() or {}
    link_code = (data.get('link_code') or '').strip().upper()

    if not link_code:
        return jsonify({'message': 'Link code required'}), 400

    # Verify link code from shared database
    telegram_id = db.get_setting(f"link_code_{link_code}")
    if not telegram_id:
        return jsonify({'message': 'Invalid or expired link code'}), 400

    # Optional: check time
    link_time = db.get_setting(f"link_code_time_{link_code}")
    # Cleanup code after use
    db.set_setting(f"link_code_{link_code}", "")

    db.link_web_user_telegram(current_user[0], telegram_id)
    return jsonify({'message': 'Telegram account linked successfully', 'telegram_id': telegram_id})

@app.route('/api/seller/apply', methods=['POST'])
@token_required
def seller_apply(current_user):
    data = request.get_json() or {}
    display_name = data.get('display_name')
    bkash_number = data.get('bkash_number')
    support_contact = data.get('support_contact')

    if not (display_name and bkash_number and support_contact):
        return jsonify({'message': 'All fields required'}), 400

    user_id = current_user[3]
    if not user_id:
        return jsonify({'message': 'Link Telegram account first to apply as seller'}), 400

    seller = db.create_or_update_seller_application(user_id, current_user[1], display_name, bkash_number, support_contact)
    return jsonify({'message': 'Application submitted', 'status': seller[5]})

@app.route('/api/seller/status', methods=['GET'])
@token_required
def get_seller_status(current_user):
    if not current_user[3]:
        return jsonify({'status': 'not_linked'})

    seller = db.get_seller(current_user[3])
    if not seller:
        return jsonify({'status': 'none'})

    return jsonify({
        'status': seller[5],
        'display_name': seller[2],
        'bkash_number': seller[3],
        'sms_token': seller[6]
    })

@app.route('/api/seller/orders', methods=['GET'])
@token_required
def get_seller_orders(current_user):
    if not current_user[3]:
        return jsonify({'message': 'Telegram account not linked'}), 400

    orders = db.list_seller_orders(current_user[3], limit=50)
    # Convert list of tuples to list of dicts
    cols = ['order_id', 'seller_id', 'buyer_id', 'buyer_username', 'payment_method', 'trx_id', 'network', 'wallet', 'amount_bdt', 'amount_crypto', 'stars_amount', 'status', 'tx_sig', 'error', 'created_at', 'updated_at']
    return jsonify([dict(zip(cols, row)) for row in orders])

@app.route('/api/seller/inventory', methods=['GET'])
@token_required
def get_seller_inventory(current_user):
    if not current_user[3]:
        return jsonify({'message': 'Telegram account not linked'}), 400

    rates = db.list_seller_rates(current_user[3])
    wallets = db.list_seller_wallets(current_user[3])

    return jsonify({
        'rates': [dict(zip(['seller_id', 'network', 'rate', 'created_at', 'updated_at'], row)) for row in rates],
        'wallets': [dict(zip(['seller_id', 'network', 'encrypted_key', 'salt', 'wallet_address', 'enabled', 'created_at', 'updated_at'], row)) for row in wallets]
    })

@app.route('/api/giveaways', methods=['GET'])
def list_giveaways():
    with db.closing(db.connect()) as con:
        rows = con.execute(
            """
            SELECT session_id, network, base_amount, recipient_count,
                   early_bonus_count, early_bonus_amount, claimed_count, expires_at, created_at
            FROM giveaway_sessions
            WHERE expires_at > datetime('now')
            ORDER BY created_at DESC LIMIT 20
            """
        ).fetchall()
    result = []
    for r in rows:
        remaining = (r[3] or 0) - (r[6] or 0)
        result.append({
            'session_id': r[0], 'network': r[1], 'base_amount': r[2],
            'recipient_count': r[3], 'early_bonus_count': r[4],
            'early_bonus_amount': r[5], 'claimed_count': r[6],
            'remaining': max(remaining, 0),
            'expires_at': r[7], 'created_at': r[8]
        })
    return jsonify(result)

@app.route('/api/balance', methods=['GET'])
@token_required
def check_balance(current_user):
    try:
        balances, evm_addr = get_all_balances()
        return jsonify({'balances': balances, 'evm_address': evm_addr})
    except Exception as exc:
        logger.error("Balance check failed: %s", exc)
        return jsonify({'message': 'Balance check unavailable', 'error': str(exc)}), 503

# ─── Global Stats & Activity ───
@app.route('/api/stats', methods=['GET'])
def get_global_stats():
    try:
        total_tx, completed, failed, total_bdt, total_crypto, total_profit, total_users, new_users_today = db.get_transaction_stats()
        return jsonify({
            'total_orders': total_tx,
            'completed_orders': completed,
            'total_volume_bdt': total_bdt,
            'total_users': total_users,
            'new_users_today': new_users_today
        })
    except Exception as exc:
        logger.error("Global stats failed: %s", exc)
        return jsonify({'message': 'Failed to load stats'}), 500

@app.route('/api/recent-activity', methods=['GET'])
def get_recent_activity():
    try:
        rows = db.get_recent_transactions(limit=10)
        activity = []
        for r in rows:
            # Mask wallet for privacy
            wallet = r[4]
            masked_wallet = f"{wallet[:6]}...{wallet[-4:]}" if wallet and len(wallet) > 10 else "N/A"
            activity.append({
                'trx_id': r[0],
                'amount_crypto': r[2],
                'network': r[3],
                'wallet': masked_wallet,
                'status': r[5],
                'created_at': r[6]
            })
        return jsonify(activity)
    except Exception as exc:
        logger.error("Recent activity failed: %s", exc)
        return jsonify([])

# ─── TX Log ───
@app.route('/api/txlog', methods=['GET'])
@token_required
def tx_log(current_user):
    try:
        user_id = current_user[3] if current_user[3] else f"web_{current_user[0]}"
        from contextlib import closing as _closing
        from db import connect as _connect
        with _closing(_connect()) as con:
            rows = con.execute(
                "SELECT trx_id, amount_bdt, amount_usdc, network, wallet, status, created_at, order_id FROM transactions WHERE user_id=? ORDER BY datetime(created_at) DESC LIMIT 30",
                (str(user_id),)
            ).fetchall()
        txs = []
        for r in rows:
            trx_id, bdt, crypto, network, wallet, status, created = r[:7]
            order_id = r[7] if len(r) > 7 else None
            if trx_id.startswith("STAR-"):
                source = "Stars"
            elif trx_id.startswith("GIFT-"):
                source = "Gift Code"
            elif trx_id.startswith("ADMIN-"):
                source = "Admin Send"
            elif trx_id.startswith("WALLET-"):
                source = "User Wallet"
            else:
                source = f"{bdt} BDT"
            txs.append({
                'trx_id': trx_id, 'amount_bdt': bdt, 'amount_crypto': crypto,
                'network': network, 'wallet': wallet, 'status': status,
                'created_at': created, 'order_id': order_id, 'source': source
            })
        return jsonify(txs)
    except Exception as exc:
        logger.error("TX log failed: %s", exc)
        return jsonify({'message': 'Failed to load TX log'}), 500

# ─── Order Status Lookup ───
@app.route('/api/order/lookup', methods=['GET'])
@token_required
def order_lookup(current_user):
    identifier = request.args.get('id', '').strip()
    if not identifier:
        return jsonify({'message': 'Please provide an order ID or TrxID'}), 400
    try:
        kind, row = db.find_order(identifier)
        if not row:
            return jsonify({'message': 'Order not found', 'found': False}), 404
        if kind == 'transaction':
            return jsonify({
                'found': True, 'type': 'transaction',
                'trx_id': row[0], 'amount_bdt': row[1], 'amount_crypto': row[2],
                'network': row[3], 'wallet': row[4], 'status': row[5],
                'created_at': row[6], 'order_id': row[7],
                'sig': row[9] if len(row) > 9 else None
            })
        elif kind == 'pending':
            return jsonify({
                'found': True, 'type': 'pending',
                'trx_id': row[0] if len(row) > 0 else None,
                'amount_bdt': row[2] if len(row) > 2 else None,
                'amount_crypto': row[3] if len(row) > 3 else None,
                'wallet': row[4] if len(row) > 4 else None,
                'network': row[5] if len(row) > 5 else None,
                'status': 'pending',
                'created_at': row[6] if len(row) > 6 else None,
                'order_id': row[7] if len(row) > 7 else None
            })
        elif kind == 'star':
            return jsonify({
                'found': True, 'type': 'star',
                'order_id': row[0] if len(row) > 0 else None,
                'status': row[7] if len(row) > 7 else None,
                'network': row[3] if len(row) > 3 else None,
                'amount_crypto': row[5] if len(row) > 5 else None,
                'created_at': row[12] if len(row) > 12 else None
            })
        return jsonify({'found': True, 'type': kind, 'raw': str(row)})
    except Exception as exc:
        logger.error("Order lookup failed: %s", exc)
        return jsonify({'message': 'Lookup failed'}), 500

# ─── Receipt ───
@app.route('/api/order/receipt', methods=['GET'])
@token_required
def order_receipt(current_user):
    identifier = request.args.get('id', '').strip()
    if not identifier:
        return jsonify({'message': 'Please provide an order ID or TrxID'}), 400
    try:
        tx = db.get_transaction_detail(identifier)
        if not tx:
            pending = db.get_pending_order(identifier) or db.get_pending_order_by_order_id(identifier)
            if pending:
                return jsonify({
                    'found': True, 'status': 'pending',
                    'message': 'Receipt is only available for completed orders.'
                })
            return jsonify({'found': False, 'message': 'Order not found'}), 404
        trx_id = tx[0]
        if trx_id.startswith('STAR-'):
            source = 'Stars'
        elif trx_id.startswith('GIFT-'):
            source = 'Gift Code'
        elif trx_id.startswith('ADMIN-'):
            source = 'Admin Send'
        elif trx_id.startswith('WALLET-'):
            source = 'User Wallet'
        else:
            source = f"{tx[1]} BDT"
        return jsonify({
            'found': True, 'status': 'completed',
            'trx_id': trx_id, 'amount_bdt': tx[1], 'amount_crypto': tx[2],
            'network': tx[3], 'wallet': tx[4], 'created_at': tx[6],
            'order_id': tx[7] if len(tx) > 7 else None,
            'sig': tx[9] if len(tx) > 9 else None,
            'source': source
        })
    except Exception as exc:
        logger.error("Receipt failed: %s", exc)
        return jsonify({'message': 'Receipt unavailable'}), 500

# ─── Payout / Withdraw ───
@app.route('/api/payout', methods=['POST'])
@token_required
def payout_request(current_user):
    data = request.get_json() or {}
    amount = data.get('amount')
    method = data.get('method', 'bKash')
    details = data.get('details', '')
    if not amount:
        return jsonify({'message': 'Amount is required'}), 400
    try:
        amount = float(amount)
        if amount <= 0:
            return jsonify({'message': 'Amount must be positive'}), 400
    except (ValueError, TypeError):
        return jsonify({'message': 'Invalid amount'}), 400
    try:
        user_id = current_user[0] if isinstance(current_user, (list, tuple)) else current_user.get('id', current_user.get('username', ''))
        req_id = db.create_payout_request(str(user_id), amount, method, details)
        notify_admin_telegram(
            f"💸 Web Payout Request\n\nID: {req_id}\nUser: {user_id}\nAmount: {amount}\nMethod: {method}\nDetails: {details}"
        )
        try:
            notifier.notify_event(
                "transaction",
                f"Payout request #{req_id}\nUser: {user_id}\nAmount: {amount}\nMethod: {method}",
            )
        except Exception as exc:
            logger.warning("Payout notification failed: %s", exc)
        return jsonify({'success': True, 'request_id': req_id})
    except Exception as exc:
        logger.error("Payout request failed: %s", exc)
        return jsonify({'message': 'Payout request failed'}), 500

@app.route('/api/payout/history', methods=['GET'])
@token_required
def payout_history(current_user):
    try:
        user_id = current_user[0] if isinstance(current_user, (list, tuple)) else current_user.get('id', current_user.get('username', ''))
        from contextlib import closing
        from db import connect
        with closing(connect()) as con:
            rows = con.execute(
                "SELECT id, amount, method, details, status, created_at FROM payout_requests WHERE user_id=? ORDER BY datetime(created_at) DESC LIMIT 20",
                (str(user_id),)
            ).fetchall()
        result = [{'id': r[0], 'amount': r[1], 'method': r[2], 'details': r[3], 'status': r[4], 'created_at': r[5]} for r in rows]
        return jsonify(result)
    except Exception as exc:
        logger.error("Payout history failed: %s", exc)
        return jsonify([])

# ─── Wallet Tools ───
@app.route('/api/wallet/setup', methods=['POST'])
@token_required
def wallet_setup(current_user):
    data = request.get_json() or {}
    network = data.get('network')
    private_key = data.get('private_key')
    password = data.get('password')
    if not network or not private_key or not password:
        return jsonify({'message': 'Network, private_key and password are required'}), 400
    try:
        user_id = current_user[0] if isinstance(current_user, (list, tuple)) else current_user.get('id', current_user.get('username', ''))
        try:
            address = get_wallet_address(network, private_key)
        except Exception:
            return jsonify({'message': 'Invalid private key for this network'}), 400
        if not address:
            return jsonify({'message': 'Invalid private key for this network'}), 400
        encrypted, salt = encrypt_key(private_key, password)
        save_user_wallet(str(user_id), encrypted, salt, network, address)
        return jsonify({'success': True, 'address': address, 'network': network})
    except Exception as exc:
        logger.error("Wallet setup failed: %s", exc)
        return jsonify({'message': 'Wallet setup failed'}), 500

@app.route('/api/wallet/balance', methods=['POST'])
@token_required
def wallet_balance(current_user):
    data = request.get_json() or {}
    password = data.get('password')
    if not password:
        return jsonify({'message': 'Password is required'}), 400
    try:
        user_id = current_user[0] if isinstance(current_user, (list, tuple)) else current_user.get('id', current_user.get('username', ''))
        balance_info, network, error = get_user_balance(str(user_id), password)
        if error or balance_info is None:
            return jsonify({'message': error or 'No wallet found or wrong password'}), 400
        return jsonify({'success': True, 'balance': balance_info, 'network': network})
    except Exception as exc:
        logger.error("Wallet balance failed: %s", exc)
        return jsonify({'message': 'Balance check failed'}), 500

@app.route('/api/wallet/send', methods=['POST'])
@token_required
def wallet_send(current_user):
    data = request.get_json() or {}
    destination = data.get('destination')
    amount = data.get('amount')
    password = data.get('password')
    if not destination or not password:
        return jsonify({'message': 'Destination and password are required'}), 400
    try:
        amount = float(amount) if amount else 0
        if amount <= 0:
            return jsonify({'message': 'Amount must be positive'}), 400
    except (ValueError, TypeError):
        return jsonify({'message': 'Invalid amount'}), 400
    try:
        user_id = current_user[0] if isinstance(current_user, (list, tuple)) else current_user.get('id', current_user.get('username', ''))
        result = send_from_user_wallet(str(user_id), password, destination, amount)
        if result:
            return jsonify({'success': True, 'tx_hash': result})
        return jsonify({'message': 'Send failed'}), 400
    except Exception as exc:
        logger.error("Wallet send failed: %s", exc)
        return jsonify({'message': 'Send failed'}), 500

@app.route('/api/wallet/status', methods=['GET'])
@token_required
def wallet_status(current_user):
    try:
        user_id = current_user[0] if isinstance(current_user, (list, tuple)) else current_user.get('id', current_user.get('username', ''))
        from crypto_manager import get_user_wallet as _get_uw
        wallet = _get_uw(str(user_id))
        if wallet:
            return jsonify({'has_wallet': True, 'network': wallet[2] if len(wallet) > 2 else None})
        return jsonify({'has_wallet': False})
    except Exception:
        return jsonify({'has_wallet': False})

# ─── Multi-Wallet Tools ───
def _uid(current_user):
    if isinstance(current_user, (list, tuple)):
        uid = current_user[0] if current_user else None
    elif isinstance(current_user, dict):
        uid = current_user.get('id') or current_user.get('username')
    else:
        uid = current_user
    uid = str(uid).strip() if uid is not None else ''
    if not uid:
        raise RuntimeError("We couldn't verify your session. Please sign in again.")
    return uid


@app.route('/api/wallets', methods=['GET'])
@token_required
def list_wallets(current_user):
    try:
        wallets = list_user_wallets(_uid(current_user))
        return jsonify({'ok': True, 'message': 'ok', 'data': {'wallets': wallets}})
    except Exception as exc:
        logger.error("List wallets failed: %s", exc)
        return jsonify({'ok': False, 'message': 'We couldn\'t load your wallets right now. Please try again.', 'data': None}), 500


@app.route('/api/wallets', methods=['POST'])
@token_required
def add_wallet(current_user):
    data = request.get_json() or {}
    network = data.get('network')
    mode = (data.get('mode') or 'create').lower()
    private_key = data.get('private_key')
    label = data.get('label')
    master_password = data.get('master_password')
    if not network or not master_password:
        return jsonify({'ok': False, 'message': 'Please choose a network and enter your master password.', 'data': None}), 400
    if mode not in ('create', 'import'):
        return jsonify({'ok': False, 'message': "Please choose whether to create a new wallet or import an existing one.", 'data': None}), 400
    if mode == 'import' and not private_key:
        return jsonify({'ok': False, 'message': 'Please paste the private key of the wallet you want to import.', 'data': None}), 400
    try:
        key_arg = private_key if mode == 'import' else 'create'
        wallet = add_user_wallet(_uid(current_user), network, key_arg, master_password, label=label)
        return jsonify({'ok': True, 'message': 'Wallet added', 'data': {'wallet': wallet}})
    except RuntimeError as exc:
        return jsonify({'ok': False, 'message': str(exc), 'data': None}), 400
    except Exception as exc:
        logger.error("Add wallet failed: %s", exc)
        return jsonify({'ok': False, 'message': 'We couldn\'t add that wallet. Please check your details and try again.', 'data': None}), 500


@app.route('/api/wallets/<int:wallet_id>', methods=['DELETE'])
@token_required
def remove_wallet(current_user, wallet_id):
    data = request.get_json(silent=True) or {}
    master_password = data.get('master_password')
    try:
        ok = delete_user_wallet_by_id(_uid(current_user), wallet_id, master_password)
        if not ok:
            return jsonify({'ok': False, 'message': 'We couldn\'t find that wallet. It may have already been removed.', 'data': None}), 404
        return jsonify({'ok': True, 'message': 'Wallet removed', 'data': None})
    except RuntimeError as exc:
        return jsonify({'ok': False, 'message': str(exc), 'data': None}), 400
    except Exception as exc:
        logger.error("Remove wallet failed: %s", exc)
        return jsonify({'ok': False, 'message': 'We couldn\'t remove that wallet right now. Please try again.', 'data': None}), 500


@app.route('/api/wallets/balances', methods=['GET'])
@token_required
def wallets_balances(current_user):
    try:
        balances = list_wallet_balances(_uid(current_user))
        return jsonify({'ok': True, 'message': 'ok', 'data': {'wallets': balances}})
    except Exception as exc:
        logger.error("Wallet balances failed: %s", exc)
        return jsonify({'ok': False, 'message': 'We couldn\'t load your balances right now. Please try again.', 'data': None}), 500


@app.route('/api/wallets/<int:wallet_id>/send', methods=['POST'])
@token_required
def send_wallet(current_user, wallet_id):
    data = request.get_json() or {}
    to_address = (data.get('to_address') or '').strip()
    asset = data.get('asset')
    master_password = data.get('master_password')
    if not to_address:
        return jsonify({'ok': False, 'message': 'Please enter a destination address.', 'data': None}), 400
    if not master_password:
        return jsonify({'ok': False, 'message': 'Please enter your master password to authorize this transfer.', 'data': None}), 400
    try:
        amount = float(data.get('amount'))
        if amount <= 0:
            raise ValueError
    except (TypeError, ValueError):
        return jsonify({'ok': False, 'message': 'Please enter a valid amount greater than zero.', 'data': None}), 400
    try:
        tx_hash = send_from_wallet(_uid(current_user), wallet_id, master_password, to_address, amount, asset)
        if tx_hash:
            return jsonify({'ok': True, 'message': 'Transfer sent successfully.', 'data': {'tx_hash': tx_hash}})
        return jsonify({'ok': False, 'message': 'The transfer could not be completed. Please try again.', 'data': None}), 400
    except RuntimeError as exc:
        return jsonify({'ok': False, 'message': str(exc), 'data': None}), 400
    except Exception as exc:
        logger.error("Wallet send failed: %s", exc)
        return jsonify({'ok': False, 'message': 'Something went wrong while sending. Please check your balance and try again.', 'data': None}), 500


@app.route('/api/wallets/master/status', methods=['GET'])
@token_required
def wallet_master_status(current_user):
    try:
        return jsonify({'ok': True, 'message': 'ok', 'data': {'has_master': has_master_password(_uid(current_user))}})
    except Exception as exc:
        logger.error("Master status failed: %s", exc)
        return jsonify({'ok': False, 'message': 'We couldn\'t check your wallet status right now. Please try again.', 'data': None}), 500

# ─── Seller Marketplace (buyer side) ───
@app.route('/api/sellers', methods=['GET'])
def list_market_sellers():
    """Public list of approved sellers with their enabled networks and effective rates."""
    try:
        sellers = db.list_sellers_by_status("approved", 30)
        result = []
        for s in sellers:
            seller_id = s[0]
            wallets = db.list_enabled_seller_wallets(seller_id)
            networks = []
            for w in wallets:
                network = w[1]
                rate = db.get_seller_rate(seller_id, network) or db.get_network_rate(network) or config.RATE
                networks.append({'network': network, 'rate': rate})
            if not networks:
                continue
            result.append({
                'seller_id': str(seller_id),
                'display_name': s[2],
                'support_contact': s[4],
                'bkash_number': s[3],
                'networks': networks,
            })
        return jsonify(result)
    except Exception as exc:
        logger.error("Seller marketplace list failed: %s", exc)
        return jsonify({'message': 'Failed to load sellers'}), 500


@app.route('/api/seller/order', methods=['POST'])
@token_required
def place_seller_order(current_user):
    """Place a bKash seller order from the web (mirrors the bot's seller buy flow)."""
    data = request.get_json() or {}
    seller_id = str(data.get('seller_id') or '').strip()
    network = data.get('network')
    wallet = (data.get('wallet') or '').strip()
    trx_id = (data.get('trx_id') or '').strip().upper()
    try:
        amount_bdt = float(data.get('amount_bdt'))
        if amount_bdt <= 0:
            raise ValueError
    except (TypeError, ValueError):
        return jsonify({'message': 'Valid amount_bdt required'}), 400
    if not (seller_id and network and wallet and trx_id):
        return jsonify({'message': 'seller_id, network, wallet and trx_id required'}), 400

    seller = db.get_seller(seller_id)
    if not seller or seller[5] != 'approved':
        return jsonify({'message': 'Seller unavailable'}), 404
    enabled_networks = [w[1] for w in db.list_enabled_seller_wallets(seller_id)]
    if network not in enabled_networks:
        return jsonify({'message': 'This seller has not enabled this network'}), 400

    rate = db.get_seller_rate(seller_id, network) or db.get_network_rate(network) or config.RATE
    if not rate or rate <= 0:
        return jsonify({'message': 'Exchange rate configuration error. Please try again later.'}), 422
    amount_crypto = round(amount_bdt / rate, 6)

    buyer_id = current_user[3] if current_user[3] else f"web_{current_user[0]}"
    order_id = f"SO_{datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{secrets.token_hex(3).upper()}"

    try:
        db.create_seller_order(
            order_id, seller_id, buyer_id, current_user[1], 'bkash',
            network, wallet, amount_bdt, amount_crypto, None,
            status='waiting_payment', trx_id=trx_id,
        )
    except db.sqlite3.IntegrityError:
        return jsonify({'message': 'This TrxID has already been used for this seller. Use a different TrxID.'}), 409
    
    db.add_audit(buyer_id, "web_seller_order_created", "seller_order", order_id, f"seller={seller_id} network={network} amount={amount_bdt} BDT")

    # Notify the seller (their seller_id is their Telegram ID) and the admin.
    seller_msg = (
        "\U0001f6CE New web seller order (bKash)\n\n"
        f"\U0001f9FE Order: {order_id}\n"
        f"\U0001f464 Buyer: {current_user[1]} ({buyer_id})\n"
        f"\U0001f4B5 Amount: {amount_bdt} BDT \u2192 {amount_crypto}\n"
        f"\U0001f310 Network: {network}\n"
        f"\U0001f45B Wallet: {wallet}\n"
        f"\U0001f511 TrxID: {trx_id}\n\n"
        "Verify the bKash payment and approve from the bot."
    )
    if config.BOT_TOKEN:
        try:
            http_requests.post(
                f"https://api.telegram.org/bot{config.BOT_TOKEN}/sendMessage",
                json={"chat_id": seller_id, "text": seller_msg},
                timeout=5,
            )
        except Exception as exc:
            logger.warning("Seller order notification failed: %s", exc)
    notify_admin_telegram(seller_msg)
    
    # Broadcast updated sellers list to all connected clients
    broadcast_sellers_update()

    return jsonify({
        'status': 'waiting_payment',
        'order_id': order_id,
        'amount_crypto': amount_crypto,
        'rate': rate,
        'seller_bkash': seller[3],
        'message': 'Seller order submitted! The seller will verify your bKash payment and deliver the crypto.'
    })


# ─── Free Tools (mirrors the bot's Free Service menu) ───
def _normalize_telegram_target(value):
    """Normalize @username / t.me link / numeric ID input (same rules as the bot)."""
    raw = (value or '').strip().strip(',')
    if not raw:
        return None
    raw = raw.split('?', 1)[0].rstrip('/')
    match = re.match(r"^(?:https?://)?(?:www\.)?(?:t\.me|telegram\.me)/(.+)$", raw, re.IGNORECASE)
    if match:
        path = match.group(1).strip('/')
        if path.startswith('+') or path.lower().startswith('joinchat/'):
            return None
        if path.startswith('c/'):
            parts = path.split('/')
            if len(parts) >= 2 and parts[1].isdigit():
                return f"-100{parts[1]}"
            return None
        raw = path.split('/', 1)[0]
    if re.fullmatch(r"-?\d+", raw):
        return raw
    raw = raw.lstrip('@')
    if re.fullmatch(r"[A-Za-z0-9_]{5,32}", raw):
        return f"@{raw}"
    return None


@app.route('/api/tools/telegram-id', methods=['GET'])
@token_required
def tool_telegram_id(current_user):
    """Telegram ID Finder: resolve a public @username / t.me link to its numeric ID."""
    if not config.BOT_TOKEN:
        return jsonify({'message': 'Tool unavailable: bot token not configured'}), 503
    target = _normalize_telegram_target(request.args.get('target', ''))
    if not target:
        return jsonify({'message': 'Send a public @username, t.me link or numeric ID. Private invite links cannot be resolved.'}), 400
    try:
        res = http_requests.get(
            f"https://api.telegram.org/bot{config.BOT_TOKEN}/getChat",
            params={'chat_id': target},
            timeout=10,
        ).json()
        if not res.get('ok'):
            return jsonify({'message': 'Could not resolve this target. Private chats usually require the bot to have access.'}), 404
        chat = res.get('result', {})
        return jsonify({
            'id': chat.get('id'),
            'type': chat.get('type'),
            'title': chat.get('title') or ((chat.get('first_name') or '') + (' ' + chat.get('last_name') if chat.get('last_name') else '')).strip() or None,
            'username': chat.get('username'),
        })
    except Exception as exc:
        logger.error("Telegram ID finder failed: %s", exc)
        return jsonify({'message': 'Lookup failed, please try again'}), 500


@app.route('/api/tools/ata/check', methods=['POST'])
@token_required
def tool_ata_check(current_user):
    """Solana ATA Refund: check empty Associated Token Accounts (key never stored)."""
    data = request.get_json() or {}
    private_key = (data.get('private_key') or '').strip()
    if not private_key:
        return jsonify({'message': 'Solana private key required'}), 400
    try:
        from solana_refund import find_refundable_atas
        summary = find_refundable_atas(private_key)
        return jsonify({
            'wallet': summary['wallet'],
            'refundable_count': summary['refundable_count'],
            'total_sol': summary['total_sol'],
            'non_empty_count': summary['non_empty_count'],
            'token_account_count': summary['token_account_count'],
        })
    except Exception as exc:
        logger.error("ATA check failed: %s", exc)
        return jsonify({'message': 'Invalid key or RPC error. Make sure you sent a valid Solana private key.'}), 400


@app.route('/api/tools/ata/refund', methods=['POST'])
@token_required
def tool_ata_refund(current_user):
    """Solana ATA Refund: close empty ATAs and return rent SOL to the same wallet."""
    data = request.get_json() or {}
    private_key = (data.get('private_key') or '').strip()
    if not private_key:
        return jsonify({'message': 'Solana private key required'}), 400
    try:
        from solana_refund import close_refundable_atas
        summary = close_refundable_atas(private_key)
        # Return 200 even if some batches failed, so user can see partial results
        return jsonify({
            'wallet': summary['wallet'],
            'refunded_count': summary.get('successfully_closed', summary.get('refundable_count', 0)),
            'total_sol': summary.get('total_sol', 0),
            'signatures': summary.get('signatures', []),
            'failed_batches': summary.get('failed_batches', []),
            'message': f"Closed {summary.get('successfully_closed', 0)} ATAs" + (f", {len(summary.get('failed_batches', []))} batch(es) failed" if summary.get('failed_batches') else "")
        }), 200
    except Exception as exc:
        logger.error("ATA refund failed: %s", exc)
        return jsonify({'message': 'Refund failed. Check the key, and make sure the wallet has a little SOL for fees.'}), 400


@app.route('/api/tools/forward', methods=['POST'])
@token_required
def tool_telegram_forward(current_user):
    """Telegram Message Forwarder: one-time send via the user's OWN bot token (never stored)."""
    data = request.get_json() or {}
    bot_token = (data.get('bot_token') or '').strip()
    message = (data.get('message') or '').strip()
    raw_chats = data.get('chat_ids') or []
    if isinstance(raw_chats, str):
        raw_chats = re.split(r"[\s,]+", raw_chats)
    chat_ids = [c.strip() for c in raw_chats if c and c.strip()][:20]

    if not re.fullmatch(r"\d+:[A-Za-z0-9_-]{30,}", bot_token):
        return jsonify({'message': 'Invalid bot token format. Get one from @BotFather.'}), 400
    if not message:
        return jsonify({'message': 'Message text required'}), 400
    if not chat_ids:
        return jsonify({'message': 'At least one chat ID or @username required'}), 400

    # Each individual request has a strict 5s timeout to prevent worker blocking
    # Total request should timeout at the gateway/proxy level (~30s), not rely on this per-chat timeout
    results = []
    request_deadline = time.time() + 25  # Leave 5s buffer for response construction
    for chat in chat_ids:
        if time.time() > request_deadline:
            results.append({'chat': chat, 'ok': False, 'error': 'Request timeout exceeded'})
            continue
        target = _normalize_telegram_target(chat) or chat
        try:
            res = http_requests.post(
                f"https://api.telegram.org/bot{bot_token}/sendMessage",
                json={'chat_id': int(target) if re.fullmatch(r"-?\d+", str(target)) else target, 'text': message},
                timeout=5,  # Per-request: strict 5s timeout to prevent blocking
            ).json()
            if res.get('ok'):
                results.append({'chat': chat, 'ok': True})
            else:
                results.append({'chat': chat, 'ok': False, 'error': res.get('description', 'Failed')})
        except http_requests.exceptions.Timeout:
            results.append({'chat': chat, 'ok': False, 'error': 'Timeout'})
        except Exception as exc:
            results.append({'chat': chat, 'ok': False, 'error': str(exc)[:100]})

    sent = sum(1 for r in results if r['ok'])
    return jsonify({'sent': sent, 'failed': len(results) - sent, 'results': results})


# ─── Buy/Swap Automation (Limit Orders + Scheduled Buys) ───
# These endpoints only create/list/cancel rows in the SHARED mouno.db. The
# Telegram bot's limit_order_monitor / scheduled_buy_runner workers execute
# them and auto-sign with the user's sealed wallet password. The web app does
# NOT run its own scheduler.

_SOL_CHAIN_IDS = {"1151111081099710", "sol", "solana"}


def _wallet_getters_for_chain(from_chain_id=None):
    """Return the wallet getter(s) relevant to a chain. Solana automations must
    validate against the Solana wallet; EVM automations against the EVM wallet.
    When the chain is unknown, fall back to checking all wallets."""
    if from_chain_id is not None and str(from_chain_id).lower() in _SOL_CHAIN_IDS:
        return (get_user_solana_wallet,)
    if from_chain_id:
        return (get_user_evm_wallet,)
    return (get_user_evm_wallet, get_user_solana_wallet, get_user_wallet)


def _verify_wallet_password(user_id, password, from_chain_id=None):
    """True if `password` decrypts the user's wallet for the given chain. When
    `from_chain_id` is omitted, returns True if it decrypts ANY wallet (used
    only for the one-time setup check)."""
    for getter in _wallet_getters_for_chain(from_chain_id):
        try:
            row = getter(str(user_id))
        except Exception:
            row = None
        if not row:
            continue
        try:
            decrypt_key(row[0], row[1], password)
            return True
        except Exception:
            continue
    return False


def _build_automation_intent(data):
    """Validate + assemble a swap intent from request JSON. Raises ValueError."""
    from_chain_id = str(data.get('from_chain_id') or '').strip()
    to_chain_id = str(data.get('to_chain_id') or '').strip()
    from_token = str(data.get('from_token') or '').strip()
    to_token = str(data.get('to_token') or '').strip()
    amount_raw = data.get('amount')
    if not (from_chain_id and to_chain_id and from_token and to_token):
        raise ValueError('from_chain_id, to_chain_id, from_token and to_token are required')
    try:
        amount = float(amount_raw)
    except (TypeError, ValueError):
        raise ValueError('A valid amount is required')
    if amount <= 0:
        raise ValueError('Amount must be greater than zero')
    preference = (data.get('preference') or 'cheapest').lower()
    if preference not in ('cheapest', 'fastest'):
        preference = 'cheapest'
    return {
        'from_chain_id': from_chain_id,
        'from_chain_name': data.get('from_chain_name'),
        'to_chain_id': to_chain_id,
        'to_chain_name': data.get('to_chain_name'),
        'from_token': from_token,
        'to_token': to_token,
        'amount': str(amount_raw).strip(),
        'preference': preference,
    }


def _limit_order_public(row):
    """Serialize a limit_orders row WITHOUT any password material."""
    return {
        'order_id': row['order_id'],
        'from_chain_id': row['from_chain_id'],
        'from_chain_name': row['from_chain_name'],
        'from_token': row['from_token'],
        'to_chain_id': row['to_chain_id'],
        'to_chain_name': row['to_chain_name'],
        'to_token': row['to_token'],
        'amount': row['amount'],
        'preference': row['preference'],
        'watch_symbol': row['watch_symbol'],
        'direction': row['direction'],
        'target_price': row['target_price'],
        'last_price': row['last_price'],
        'status': row['status'],
        'tx_hash': row['tx_hash'],
        'error': row['error'],
        'created_at': row['created_at'],
        'triggered_at': row['triggered_at'],
    }


def _scheduled_buy_public(row):
    """Serialize a scheduled_buys row WITHOUT any password material."""
    return {
        'schedule_id': row['schedule_id'],
        'from_chain_id': row['from_chain_id'],
        'from_chain_name': row['from_chain_name'],
        'from_token': row['from_token'],
        'to_chain_id': row['to_chain_id'],
        'to_chain_name': row['to_chain_name'],
        'to_token': row['to_token'],
        'amount': row['amount'],
        'preference': row['preference'],
        'interval_key': row['interval_key'],
        'status': row['status'],
        'runs_count': row['runs_count'],
        'last_tx_hash': row['last_tx_hash'],
        'last_error': row['last_error'],
        'created_at': row['created_at'],
        'next_run': row['next_run'],
        'last_run': row['last_run'],
    }


@app.route('/api/automation/setup-password', methods=['GET', 'POST'])
@token_required
def automation_setup_password(current_user):
    user_id = _uid(current_user)
    if request.method == 'GET':
        return jsonify({'configured': has_auto_password(user_id)})

    data = request.get_json() or {}
    password = data.get('password')
    if not password:
        return jsonify({'message': 'Wallet password is required'}), 400
    if not (get_user_evm_wallet(str(user_id)) or get_user_solana_wallet(str(user_id)) or get_user_wallet(str(user_id))):
        return jsonify({'message': 'Set up a personal wallet first before enabling auto-sign.'}), 400
    if not _verify_wallet_password(user_id, password):
        return jsonify({'message': 'Incorrect wallet password.'}), 400
    try:
        store_auto_password(user_id, password)
    except Exception as exc:
        logger.error('Auto-sign setup failed: %s', exc)
        return jsonify({'message': 'Could not enable auto-sign right now.'}), 500
    return jsonify({'configured': True, 'message': 'Auto-sign enabled.'})


@app.route('/api/automation/limit-orders', methods=['GET', 'POST'])
@token_required
def automation_limit_orders(current_user):
    user_id = _uid(current_user)

    if request.method == 'GET':
        rows = automation_service.list_limit_orders(user_id, statuses=('active', 'filled', 'failed', 'cancelled'))
        return jsonify({'orders': [_limit_order_public(r) for r in rows]})

    password = get_auto_password(user_id)
    if not password:
        return jsonify({'message': 'Enable auto-sign (set your wallet password) before creating automations.'}), 400
    data = request.get_json() or {}
    try:
        intent = _build_automation_intent(data)
    except ValueError as exc:
        return jsonify({'message': str(exc)}), 400

    direction = str(data.get('direction') or '').lower()
    if direction not in automation_service.LIMIT_DIRECTIONS:
        return jsonify({'message': "direction must be 'below' or 'above'"}), 400
    try:
        target_price = float(data.get('target_price'))
    except (TypeError, ValueError):
        return jsonify({'message': 'A valid target price is required'}), 400
    if target_price <= 0:
        return jsonify({'message': 'Target price must be greater than zero'}), 400

    if not _verify_wallet_password(user_id, password, from_chain_id=intent['from_chain_id']):
        return jsonify({'message': "Saved wallet password does not match this chain's wallet. Re-run auto-sign setup or use a wallet secured with the same password."}), 400

    try:
        order_id = automation_service.create_limit_order(
            user_id, intent,
            watch_symbol=intent.get('to_token'),
            direction=direction,
            target_price=str(data.get('target_price')).strip(),
            password=password,
        )
    except Exception as exc:
        logger.error('Create limit order failed: %s', exc)
        return jsonify({'message': 'Could not create limit order.'}), 500
    return jsonify({'order_id': order_id, 'message': 'Limit order created. The bot is watching the price 24/7.'})


@app.route('/api/automation/limit-orders/<order_id>', methods=['PATCH', 'DELETE'])
@token_required
def automation_limit_order_detail(current_user, order_id):
    user_id = _uid(current_user)
    existing = automation_service.get_limit_order(order_id, user_id=user_id)
    if not existing:
        return jsonify({'message': 'Limit order not found'}), 404

    if request.method == 'DELETE':
        ok = automation_service.cancel_limit_order(order_id, user_id)
        if not ok:
            return jsonify({'message': 'Limit order could not be cancelled (already inactive).'}), 400
        return jsonify({'message': 'Limit order cancelled.'})

    # PATCH: update target price (only while still active)
    if existing['status'] != 'active':
        return jsonify({'message': 'Only active limit orders can be updated.'}), 400
    data = request.get_json() or {}
    try:
        new_price = float(data.get('target_price'))
    except (TypeError, ValueError):
        return jsonify({'message': 'A valid target price is required'}), 400
    if new_price <= 0:
        return jsonify({'message': 'Target price must be greater than zero'}), 400
    ok = automation_service.update_limit_target_price(order_id, user_id, str(data.get('target_price')).strip())
    if not ok:
        return jsonify({'message': 'Limit order could not be updated (no longer active).'}), 400
    return jsonify({'message': 'Target price updated.'})


@app.route('/api/automation/scheduled-buys', methods=['GET', 'POST'])
@token_required
def automation_scheduled_buys(current_user):
    user_id = _uid(current_user)

    if request.method == 'GET':
        rows = automation_service.list_scheduled_buys(user_id, statuses=('active', 'paused', 'cancelled'))
        return jsonify({'schedules': [_scheduled_buy_public(r) for r in rows]})

    password = get_auto_password(user_id)
    if not password:
        return jsonify({'message': 'Enable auto-sign (set your wallet password) before creating automations.'}), 400
    data = request.get_json() or {}
    try:
        intent = _build_automation_intent(data)
    except ValueError as exc:
        return jsonify({'message': str(exc)}), 400

    interval_key = str(data.get('interval_key') or data.get('interval') or '').lower()
    if interval_key not in automation_service.INTERVAL_SECONDS:
        return jsonify({'message': 'interval must be daily, weekly, or monthly'}), 400

    if not _verify_wallet_password(user_id, password, from_chain_id=intent['from_chain_id']):
        return jsonify({'message': "Saved wallet password does not match this chain's wallet. Re-run auto-sign setup or use a wallet secured with the same password."}), 400

    try:
        schedule_id = automation_service.create_scheduled_buy(
            user_id, intent, interval_key=interval_key, password=password,
        )
    except Exception as exc:
        logger.error('Create scheduled buy failed: %s', exc)
        return jsonify({'message': 'Could not create scheduled buy.'}), 500
    return jsonify({'schedule_id': schedule_id, 'message': f'Auto-buy created. Runs {interval_key}.'})


@app.route('/api/automation/scheduled-buys/<schedule_id>', methods=['PATCH', 'DELETE'])
@token_required
def automation_scheduled_buy_detail(current_user, schedule_id):
    user_id = _uid(current_user)
    existing = automation_service.get_scheduled_buy(schedule_id, user_id=user_id)
    if not existing:
        return jsonify({'message': 'Scheduled buy not found'}), 404

    if request.method == 'DELETE':
        ok = automation_service.set_scheduled_status(schedule_id, user_id, 'cancelled')
        if not ok:
            return jsonify({'message': 'Scheduled buy could not be cancelled.'}), 400
        return jsonify({'message': 'Scheduled buy cancelled.'})

    # PATCH: pause / resume
    data = request.get_json() or {}
    status = str(data.get('status') or '').lower()
    if status not in ('active', 'paused'):
        return jsonify({'message': "status must be 'active' (resume) or 'paused'"}), 400
    if existing['status'] == 'cancelled':
        return jsonify({'message': 'Cancelled schedules cannot be changed.'}), 400
    ok = automation_service.set_scheduled_status(schedule_id, user_id, status)
    if not ok:
        return jsonify({'message': 'Could not update scheduled buy.'}), 400
    return jsonify({'message': 'Resumed.' if status == 'active' else 'Paused.'})


# ─────────────────────────────────────────────────────────────────────────────
# Portfolio dashboard, transaction analytics & notifications
# ─────────────────────────────────────────────────────────────────────────────
from decimal import Decimal

# Stablecoins are pegged ~$1, so we skip a live lookup for them.
_STABLE_SYMBOLS = {'USDC', 'USDT', 'DAI', 'BUSD', 'TUSD', 'USDC.E'}

# Minimal symbol → (LI.FI chain id, token address) map for live USD pricing of
# non-stable assets (used by price alerts and portfolio valuation). Native
# tokens use the zero address; LI.FI resolves the chain's native coin.
_SYMBOL_PRICE_TOKENS = {
    'ETH': ('1', '0x0000000000000000000000000000000000000000'),
    'WETH': ('1', '0x0000000000000000000000000000000000000000'),
    'BTC': ('1', '0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599'),   # WBTC
    'WBTC': ('1', '0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599'),
    'BNB': ('56', '0x0000000000000000000000000000000000000000'),
    'MATIC': ('137', '0x0000000000000000000000000000000000000000'),
    'POL': ('137', '0x0000000000000000000000000000000000000000'),
    'AVAX': ('43114', '0x0000000000000000000000000000000000000000'),
    'SOL': ('1151111081099710', '11111111111111111111111111111111'),
}

# network → asset symbol (mirrors balance.get_wallet_balances asset_map).
_NETWORK_ASSET = {
    'solana': 'USDC', 'solana_usdt': 'USDT', 'trc20': 'USDT', 'polygon': 'USDC',
    'bsc': 'USDT', 'ton': 'USDT', 'avalanche': 'USDT', 'ethereum': 'USDT',
    'ethereum_usdc': 'USDC', 'base': 'USDC',
}

# Symbols we can price live (used to validate price alerts at creation time).
_SUPPORTED_PRICE_SYMBOLS = set(_STABLE_SYMBOLS) | set(_SYMBOL_PRICE_TOKENS.keys())

# ─── Shared, short-lived price cache + per-user evaluation throttle ───
# Polled endpoints (/api/portfolio/overview, /api/notifications) refresh every
# ~30s. Without a cross-request cache each poll would issue a fresh blocking
# LI.FI call per asset, which can exhaust the worker pool and hit rate limits.
import threading
import time as _time

_PRICE_CACHE = {}                 # key -> (value, expires_at)
_PRICE_CACHE_LOCK = threading.Lock()
_PRICE_CACHE_TTL = 60             # seconds
_EVAL_THROTTLE = {}               # (uid, kind) -> last_run_epoch
_EVAL_THROTTLE_LOCK = threading.Lock()
_EVAL_MIN_INTERVAL = 120          # seconds between on-read event evaluations per user


def _eval_due(uid, kind, min_interval=_EVAL_MIN_INTERVAL):
    """True at most once per `min_interval` per (uid, kind); throttles read-path work."""
    now = _time.time()
    key = (str(uid), kind)
    with _EVAL_THROTTLE_LOCK:
        last = _EVAL_THROTTLE.get(key, 0)
        if now - last < min_interval:
            return False
        _EVAL_THROTTLE[key] = now
        return True


def _get_symbol_price_usd(symbol, chain=None):
    """Live USD price for a symbol via LI.FI; Decimal(1) for stablecoins; None if unknown.

    Results are cached in-process for `_PRICE_CACHE_TTL` seconds, shared across
    requests, so frequent polling does not issue a network call every time.
    """
    sym = str(symbol or '').upper().strip()
    if not sym:
        return None
    if sym in _STABLE_SYMBOLS:
        return Decimal('1')
    mapping = _SYMBOL_PRICE_TOKENS.get(sym)
    if not mapping:
        return None

    cache_key = sym
    now = _time.time()
    with _PRICE_CACHE_LOCK:
        cached = _PRICE_CACHE.get(cache_key)
        if cached and cached[1] > now:
            return cached[0]

    chain_id, token = mapping
    try:
        price = fetch_token_price_usd(chain_id, token, api_key=config.LIFI_API_KEY)
    except Exception as exc:
        logger.warning("Price lookup failed for %s: %s", sym, exc)
        return None

    if price is not None:
        with _PRICE_CACHE_LOCK:
            _PRICE_CACHE[cache_key] = (price, now + _PRICE_CACHE_TTL)
    return price


def _tx_user_id(current_user):
    """Transaction-table identity (telegram id, else web_<id>), matching /api/txlog."""
    return current_user[3] if current_user[3] else f"web_{current_user[0]}"


def _check_price_alerts(uid):
    """On-demand (no scheduler): fire active alerts whose target is hit.

    Creates a 'price_alert' notification and marks the alert triggered. Returns
    the list of fired alert ids. Best-effort: never raises.
    """
    fired = []
    try:
        alerts = db.list_active_price_alerts(uid)
    except Exception:
        return fired
    price_cache = {}
    for a in alerts:
        sym = a['symbol']
        cache_key = (sym, a.get('chain'))
        if cache_key not in price_cache:
            price_cache[cache_key] = _get_symbol_price_usd(sym, a.get('chain'))
        price = price_cache[cache_key]
        if price is None:
            continue
        try:
            current = float(price)
            target = float(a['target_price'])
        except (TypeError, ValueError):
            continue
        hit = (a['direction'] == 'above' and current >= target) or \
              (a['direction'] == 'below' and current <= target)
        if not hit:
            continue
        try:
            # Atomic: marking the alert triggered and inserting the notification
            # commit together, so an alert can't be consumed without notifying.
            db.fire_price_alert(
                a['id'], uid, f"{sym} price alert",
                f"{sym} is now ${current:,.4f}, "
                f"{'above' if a['direction'] == 'above' else 'below'} your target of ${target:,.4f}.",
                metadata={'ref': f"alert:{a['id']}", 'symbol': sym, 'price': current, 'target': target},
            )
            fired.append(a['id'])
        except Exception as exc:
            logger.warning("Firing price alert %s failed: %s", a.get('id'), exc)
    return fired


def _sync_large_tx_notifications(uid, tx_uid):
    """On-demand: create 'large_tx' notifications for newly confirmed big transfers."""
    try:
        threshold = float(config.LARGE_TX_USD_THRESHOLD)
    except Exception:
        threshold = 100.0
    try:
        from contextlib import closing as _closing
        from db import connect as _connect
        with _closing(_connect()) as con:
            rows = con.execute(
                "SELECT trx_id, amount_usdc, network FROM transactions "
                "WHERE user_id=? AND status='completed' ORDER BY datetime(created_at) DESC LIMIT 20",
                (str(tx_uid),),
            ).fetchall()
        for trx_id, usdc, network in rows:
            try:
                usd = float(usdc or 0)
            except (TypeError, ValueError):
                usd = 0.0
            if usd < threshold:
                continue
            if db.notification_exists_for_ref(uid, 'large_tx', f"tx:{trx_id}"):
                continue
            db.create_notification(
                uid, 'large_tx', 'Large transaction confirmed',
                f"A transaction of ${usd:,.2f} on {str(network).upper()} was confirmed.",
                metadata={'ref': f"tx:{trx_id}", 'network': network, 'usd': usd},
            )
    except Exception as exc:
        logger.warning("Large tx notification sync failed: %s", exc)


@app.route('/api/portfolio/overview', methods=['GET'])
@token_required
def portfolio_overview(current_user):
    uid = _uid(current_user)
    try:
        wallets = list_wallet_balances(uid)
    except Exception as exc:
        logger.error("Portfolio balances failed: %s", exc)
        return jsonify({'ok': False, 'message': "We couldn't load your portfolio right now. Please try again.", 'data': None}), 500

    holdings = []
    total = 0.0
    price_cache = {}
    for w in wallets:
        bal = w.get('balance')
        try:
            amount = float(bal) if bal not in (None, '') else 0.0
        except (TypeError, ValueError):
            amount = 0.0
        if amount <= 0:
            continue
        asset = w.get('asset') or _NETWORK_ASSET.get(w.get('network'), 'TOKEN')
        if asset not in price_cache:
            price_cache[asset] = _get_symbol_price_usd(asset, w.get('network'))
        price = price_cache[asset]
        if price is not None:
            usd = amount * float(price)
        elif asset in _STABLE_SYMBOLS:
            usd = amount
        else:
            usd = 0.0
        holdings.append({
            'asset': asset,
            'network': w.get('network'),
            'label': w.get('label'),
            'address': w.get('wallet_address'),
            'amount': amount,
            'usd_value': round(usd, 2),
        })
        total += usd

    for h in holdings:
        h['pct'] = round((h['usd_value'] / total * 100), 2) if total > 0 else 0.0
    holdings.sort(key=lambda h: h['usd_value'], reverse=True)

    change_pct = None
    try:
        # Read the prior value BEFORE recording today's snapshot, otherwise the
        # just-inserted row becomes the "24h ago" value and change is always 0%.
        prev = db.get_portfolio_value_24h_ago(uid)
        db.record_portfolio_snapshot(uid, total)
        if prev and prev > 0:
            change_pct = round((total - prev) / prev * 100, 2)
    except Exception as exc:
        logger.warning("Portfolio snapshot/24h change failed: %s", exc)

    fired = _check_price_alerts(uid) if _eval_due(uid, 'price_alert') else []

    return jsonify({'ok': True, 'message': 'ok', 'data': {
        'net_worth_usd': round(total, 2),
        'change_24h_pct': change_pct,
        'holdings': holdings,
        'alerts_triggered': fired,
    }})


@app.route('/api/price-alerts', methods=['GET'])
@token_required
def list_price_alerts_route(current_user):
    try:
        alerts = db.list_price_alerts(_uid(current_user))
        return jsonify({'ok': True, 'message': 'ok', 'data': {'alerts': alerts}})
    except Exception as exc:
        logger.error("List price alerts failed: %s", exc)
        return jsonify({'ok': False, 'message': "We couldn't load your price alerts. Please try again.", 'data': None}), 500


@app.route('/api/price-alerts', methods=['POST'])
@token_required
def create_price_alert_route(current_user):
    data = request.get_json() or {}
    symbol = (data.get('symbol') or '').strip()
    direction = (data.get('direction') or 'below').lower()
    chain = data.get('chain')
    if not symbol:
        return jsonify({'ok': False, 'message': 'Please enter the asset symbol (e.g. BTC).', 'data': None}), 400
    if symbol.upper() not in _SUPPORTED_PRICE_SYMBOLS:
        supported = ', '.join(sorted(_SUPPORTED_PRICE_SYMBOLS))
        return jsonify({'ok': False, 'message': f"'{symbol}' isn't supported for live pricing yet. Supported assets: {supported}.", 'data': None}), 400
    if direction not in ('above', 'below'):
        return jsonify({'ok': False, 'message': "Direction must be 'above' or 'below'.", 'data': None}), 400
    try:
        target = float(data.get('target_price'))
        if target <= 0:
            raise ValueError
    except (TypeError, ValueError):
        return jsonify({'ok': False, 'message': 'Please enter a valid target price greater than zero.', 'data': None}), 400
    try:
        alert_id = db.create_price_alert(_uid(current_user), symbol, chain, direction, target)
        return jsonify({'ok': True, 'message': 'Price alert created.', 'data': {'id': alert_id}})
    except Exception as exc:
        logger.error("Create price alert failed: %s", exc)
        return jsonify({'ok': False, 'message': "We couldn't create that price alert. Please try again.", 'data': None}), 500


@app.route('/api/price-alerts/<int:alert_id>', methods=['DELETE'])
@token_required
def delete_price_alert_route(current_user, alert_id):
    try:
        ok = db.delete_price_alert(_uid(current_user), alert_id)
        if not ok:
            return jsonify({'ok': False, 'message': 'That alert was not found. It may already be removed.', 'data': None}), 404
        return jsonify({'ok': True, 'message': 'Price alert cancelled.', 'data': None})
    except Exception as exc:
        logger.error("Delete price alert failed: %s", exc)
        return jsonify({'ok': False, 'message': "We couldn't cancel that alert. Please try again.", 'data': None}), 500


@app.route('/api/analytics/summary', methods=['GET'])
@token_required
def analytics_summary(current_user):
    tx_uid = _tx_user_id(current_user)
    period = (request.args.get('period') or 'month').lower()
    days_map = {'week': 7, 'month': 30, 'quarter': 90, 'year': 365, 'all': 36500}
    days = days_map.get(period, 30)
    try:
        from contextlib import closing as _closing
        from db import connect as _connect
        with _closing(_connect()) as con:
            rows = con.execute(
                "SELECT amount_usdc, amount_bdt, network, wallet, created_at FROM transactions "
                "WHERE user_id=? AND status='completed' AND datetime(created_at) >= datetime('now', ?)",
                (str(tx_uid), f'-{days} days'),
            ).fetchall()
            prev_rows = con.execute(
                "SELECT amount_usdc FROM transactions WHERE user_id=? AND status='completed' "
                "AND datetime(created_at) >= datetime('now', ?) AND datetime(created_at) < datetime('now', ?)",
                (str(tx_uid), f'-{days * 2} days', f'-{days} days'),
            ).fetchall()

        by_asset, by_network, recipients = {}, {}, {}
        total_volume = 0.0
        for usdc, _bdt, network, wallet, _created in rows:
            try:
                amt = float(usdc or 0)
            except (TypeError, ValueError):
                amt = 0.0
            total_volume += amt
            asset = _NETWORK_ASSET.get(network, 'TOKEN')
            by_asset[asset] = by_asset.get(asset, 0.0) + amt
            by_network[network or 'unknown'] = by_network.get(network or 'unknown', 0.0) + amt
            if wallet:
                recipients[wallet] = recipients.get(wallet, 0) + 1

        prev_volume = 0.0
        for (usdc,) in prev_rows:
            try:
                prev_volume += float(usdc or 0)
            except (TypeError, ValueError):
                pass

        spend_by_asset = sorted(
            [{'asset': k, 'usd_value': round(v, 2)} for k, v in by_asset.items()],
            key=lambda x: x['usd_value'], reverse=True)
        spend_by_network = sorted(
            [{'network': k, 'usd_value': round(v, 2)} for k, v in by_network.items()],
            key=lambda x: x['usd_value'], reverse=True)
        top_recipients = sorted(
            [{'address': k, 'count': v} for k, v in recipients.items()],
            key=lambda x: x['count'], reverse=True)[:10]

        change = round((total_volume - prev_volume) / prev_volume * 100, 2) if prev_volume > 0 else None

        return jsonify({'ok': True, 'message': 'ok', 'data': {
            'period': period,
            'total_volume': round(total_volume, 2),
            'prev_volume': round(prev_volume, 2),
            'volume_change_pct': change,
            'tx_count': len(rows),
            'spend_by_asset': spend_by_asset,
            'spend_by_network': spend_by_network,
            'top_recipients': top_recipients,
        }})
    except Exception as exc:
        logger.error("Analytics summary failed: %s", exc)
        return jsonify({'ok': False, 'message': "We couldn't load your analytics right now. Please try again.", 'data': None}), 500


@app.route('/api/notifications', methods=['GET'])
@token_required
def get_notifications(current_user):
    uid = _uid(current_user)
    # Lightweight, on-demand event detection. The Telegram bot owns the shared
    # mouno.db background monitors; the web app intentionally runs no scheduler
    # (see automation note above), so we evaluate alerts/large-tx on read.
    # Throttled to at most once per _EVAL_MIN_INTERVAL per user so 30s polling
    # does not trigger blocking price lookups on every request.
    if _eval_due(uid, 'large_tx'):
        _sync_large_tx_notifications(uid, _tx_user_id(current_user))
    if _eval_due(uid, 'price_alert'):
        _check_price_alerts(uid)
    try:
        items = db.list_notifications(uid, limit=50)
        unread = db.count_unread_notifications(uid)
        return jsonify({'ok': True, 'message': 'ok', 'data': {'notifications': items, 'unread': unread}})
    except Exception as exc:
        logger.error("List notifications failed: %s", exc)
        return jsonify({'ok': False, 'message': "We couldn't load your notifications right now. Please try again.", 'data': None}), 500


@app.route('/api/notifications/read', methods=['POST'])
@token_required
def mark_notifications_read_route(current_user):
    uid = _uid(current_user)
    data = request.get_json(silent=True) or {}
    notif_id = data.get('id')
    # Validate client input separately so a malformed id is a 400, not a 500.
    try:
        notif_id = int(notif_id) if notif_id is not None else None
    except (TypeError, ValueError):
        return jsonify({'ok': False, 'message': 'Invalid notification id.', 'data': None}), 400
    try:
        db.mark_notifications_read(uid, notif_id)
        return jsonify({'ok': True, 'message': 'Marked as read', 'data': {'unread': db.count_unread_notifications(uid)}})
    except Exception as exc:
        logger.error("Mark notifications read failed: %s", exc)
        return jsonify({'ok': False, 'message': "We couldn't update your notifications. Please try again.", 'data': None}), 500


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5001)
