import os
import jwt
import datetime
from functools import wraps
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import sys

import db
import config
from balance import get_all_balances
from swap_service import quote_lifi, summarize_quote, get_lifi_chains
from crypto_manager import get_user_balance, send_from_user_wallet, get_wallet_address, encrypt_key, save_user_wallet

app = Flask(__name__, static_folder=None)
CORS(app)
_SECRET = os.getenv("WEB_SECRET_KEY")
if not _SECRET:
    raise RuntimeError("WEB_SECRET_KEY must be set in the environment")
app.config['SECRET_KEY'] = _SECRET

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
    networks = ["solana", "trc20", "polygon", "bsc", "ton"]
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

    # Check if SMS already arrived
    sms = db.get_sms(trx_id)
    if sms:
        # For simplicity in this demo, we'll just save it as pending
        # and let the admin or a background task handle it if needed.
        # In a full implementation, we could trigger send_crypto here.
        pass

    order_id = db.save_pending_order(trx_id, user_id, amount_bdt, amount_usdc, wallet, network)

    # Add audit log
    db.add_audit(user_id, "web_buy_order_created", "pending_order", order_id, f"network={network} amount={amount_bdt} BDT")

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

    # We use the existing logic from db.py but we need to handle the sending.
    # Since the API is separate, it's better to reuse the bot's logic if possible.
    # For now, let's just return a placeholder or implement basic verification.

    row = db.get_code(code)
    if not row:
        return jsonify({'message': 'Code not found'}), 404
    if row[3]: # used
        return jsonify({'message': 'Code already used'}), 400

    # In a real scenario, we'd trigger the send_crypto here.
    # For simplicity, we'll assume the same shared logic.
    return jsonify({'message': 'Redeem initiated (implement crypto send in backend)'}), 202

from ai_service import ask_ai_support

@app.route('/api/ai/chat', methods=['POST'])
@token_required
def ai_chat(current_user):
    data = request.get_json() or {}
    question = data.get('question')
    if not question:
        return jsonify({'message': 'Question required'}), 400

    try:
        answer = ask_ai_support(question)
    except Exception as exc:
        logger.error("AI chat error: %s", exc)
        answer = "Sorry, AI support is temporarily unavailable. Please try again later."
    return jsonify({'answer': answer}), 200

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
        'rates': [dict(zip(['seller_id', 'network', 'rate', 'created_at', 'updated_at'], r)) for row in rates],
        'wallets': [dict(zip(['seller_id', 'network', 'encrypted_key', 'salt', 'wallet_address', 'enabled', 'created_at', 'updated_at'], w)) for row in wallets]
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
