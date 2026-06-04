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
from swap_service import quote_lifi, summarize_quote

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

    rate = db.get_network_rate(network) or config.RATE
    amount_usdc = round(amount_bdt / rate, 2)

    order_id = db.save_pending_order(trx_id, user_id, amount_bdt, amount_usdc, wallet, network)

    return jsonify({
        'status': 'pending',
        'order_id': order_id,
        'message': 'Order submitted. It will be processed once bKash payment is verified.'
    })

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
