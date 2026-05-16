import logging
import re
from concurrent.futures import TimeoutError
from html import escape

import requests
from flask import Flask, jsonify, request

from balance import get_all_balances, get_native_gas_balances
from config import ADMIN_ID, BOT_TOKEN, DASHBOARD_TOKEN, FORWARDER_SECRET
from db import dashboard_snapshot, get_seller_by_sms_token, get_webhook_health, touch_webhook_notice
from personal_auth import (
    get_personal_auth_session,
    send_personal_auth_code_sync,
    verify_personal_auth_code_sync,
    verify_personal_auth_password_sync,
)

app = Flask(__name__)
logger = logging.getLogger(__name__)
_callback = None


def set_callback(fn):
    global _callback
    _callback = fn


def _amount_to_float(value):
    return float(value.replace(",", ""))


def _clean_bearer(value):
    value = str(value or "").strip()
    if value.lower().startswith("bearer "):
        return value[7:].strip()
    return ""


def _forwarder_token_ok(data):
    route_token = request.view_args.get("token") if request.view_args else None
    if route_token:
        return True
    if not FORWARDER_SECRET:
        return True
    return _supplied_forwarder_token() == FORWARDER_SECRET


def _supplied_forwarder_token():
    return (
        request.headers.get("X-Forwarder-Token")
        or request.headers.get("X-Webhook-Token")
        or _clean_bearer(request.headers.get("Authorization"))
    )


def _seller_token_ok(token):
    if not token:
        return False
    try:
        seller = get_seller_by_sms_token(token)
    except Exception as exc:
        logger.error("Seller token health lookup failed: %s", exc)
        return False
    return bool(seller and seller[5] == "approved")


def _notice_values(data):
    hidden = {"forwarder_secret", "seller_token", "token", "api_key", "secret", "authorization"}
    return [str(value) for key, value in data.items() if str(key).lower() not in hidden]


def _safe_raw_log(raw):
    text = str(raw or "")[:300]
    if FORWARDER_SECRET:
        text = text.replace(FORWARDER_SECRET, "[REDACTED]")
    text = re.sub(r'(?i)(forwarder_secret|token|authorization|api_key|secret)"?\s*[:=]\s*"?[^",\s}]+', r"\1=[REDACTED]", text)
    return text


def _short_notice_text(text):
    value = " ".join(str(text or "").split())
    if not value:
        return "N/A"
    return value[:700] + ("..." if len(value) > 700 else "")


def notify_admin_parsed_notice(parsed, source, text, scope="main", seller_id=None):
    if not BOT_TOKEN or not ADMIN_ID:
        return False
    seller_line = f"\n🏪 Seller: {seller_id}" if seller_id else ""
    message = (
        "📲 bKash notice parsed by app/webhook\n\n"
        f"📩 Source: {source}\n"
        f"🔎 Scope: {scope}{seller_line}\n"
        f"💵 Amount: {parsed['amount_bdt']} BDT\n"
        f"🔑 TrxID: {parsed['trx_id']}\n"
        f"📝 Message: {_short_notice_text(text)}"
    )
    try:
        response = requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={"chat_id": ADMIN_ID, "text": message},
            timeout=5,
        )
        if response.status_code >= 400:
            logger.error("Admin bKash parse alert failed: HTTP %s %s", response.status_code, response.text[:300])
            return False
        return True
    except Exception as exc:
        logger.error("Admin bKash parse alert failed: %s", exc)
        return False


def parse_bkash_sms(text):
    return parse_bkash_payment_notice(text)


def parse_bkash_payment_notice(text):
    compact = " ".join(str(text).split())
    if not re.search(r"\b(bkash|bKash)\b|বিকাশ", compact, re.IGNORECASE) and not re.search(r"\bTrxID\b|\bTxnID\b|Transaction ID", compact, re.IGNORECASE):
        return None

    amount_patterns = [
        r"You have received\s*(?:Tk|BDT|৳)\s*([\d,]+(?:\.\d+)?)",
        r"(?:received|Receive Money|Payment Received|Cash In)\D{0,20}(?:Tk|BDT|৳)\s*([\d,]+(?:\.\d+)?)",
        r"(?:Tk|BDT|৳)\s*([\d,]+(?:\.\d+)?)\D{0,40}(?:received|Receive Money|Payment Received|Cash In)",
    ]
    trx_patterns = [
        r"\bTrxID\s*[:#-]?\s*([A-Z0-9]+)",
        r"\bTxnID\s*[:#-]?\s*([A-Z0-9]+)",
        r"Transaction\s*ID\s*[:#-]?\s*([A-Z0-9]+)",
    ]
    sender_patterns = [
        r"from\s*(\d{10,14})",
        r"Sender\s*[:#-]?\s*(\d{10,14})",
    ]
    datetime_patterns = [
        r"at\s*(\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2})",
        r"(\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2})",
    ]

    amount = None
    for pattern in amount_patterns:
        match = re.search(pattern, compact, re.IGNORECASE)
        if match:
            amount = _amount_to_float(match.group(1))
            break

    trx_id = None
    for pattern in trx_patterns:
        match = re.search(pattern, compact, re.IGNORECASE)
        if match:
            trx_id = match.group(1).upper()
            break

    if amount is None or not trx_id:
        return None

    sender = "bkash_app"
    for pattern in sender_patterns:
        match = re.search(pattern, compact, re.IGNORECASE)
        if match:
            sender = match.group(1)
            break

    notice_time = None
    for pattern in datetime_patterns:
        match = re.search(pattern, compact, re.IGNORECASE)
        if match:
            notice_time = match.group(1)
            break

    return {
        "amount_bdt": amount,
        "sender": sender,
        "trx_id": trx_id,
        "datetime": notice_time,
    }


def parsed_notice_from_forwarder_data(data):
    if not data or not data.get("parsed_bkash"):
        return None
    try:
        amount = float(str(data.get("amount_bdt", "")).replace(",", ""))
    except (TypeError, ValueError):
        return None
    trx_id = str(data.get("trx_id") or "").strip().upper()
    if not trx_id or not re.fullmatch(r"[A-Z0-9]+", trx_id):
        return None
    return {
        "amount_bdt": amount,
        "sender": str(data.get("notice_sender") or data.get("source") or "bkash_app"),
        "trx_id": trx_id,
        "datetime": data.get("notice_datetime"),
    }


def callback_notice_text(all_text, parsed, used_structured_parse):
    if not used_structured_parse:
        return all_text
    return f"bKash Payment Received Tk {parsed['amount_bdt']} TrxID {parsed['trx_id']}"


def _payment_ack(parsed=None, payment_status=None, **extra):
    payment_status = payment_status or ("parsed" if parsed else "ignored")
    ack = {
        "status": "ok",
        "parsed": bool(parsed),
        "payment_status": payment_status,
        "matched_order": payment_status == "matched_order",
        "duplicate": payment_status == "duplicate",
        "manual_review": payment_status == "manual_review",
    }
    if parsed:
        ack.update({
            "trx_id": parsed.get("trx_id"),
            "amount_bdt": parsed.get("amount_bdt"),
            "notice_sender": parsed.get("sender"),
        })
    ack.update({key: value for key, value in extra.items() if value is not None})
    return ack


def _callback_payment_outcome(callback_result):
    if callback_result is None:
        return None
    if hasattr(callback_result, "result"):
        try:
            callback_result = callback_result.result(timeout=8)
        except TimeoutError:
            return {
                "payment_status": "parsed",
                "processing_pending": True,
                "message": "Server parsed the notice; bot processing is still running.",
            }
        except Exception as exc:
            logger.error("bKash callback processing failed: %s", exc)
            return {
                "payment_status": "manual_review",
                "manual_review": True,
                "message": "Server parsed the notice, but bot processing failed and needs admin review.",
                "error": str(exc),
            }
    return callback_result if isinstance(callback_result, dict) else None


def handle_payment_notice(source):
    raw = request.get_data(as_text=True)
    data = request.get_json(silent=True) or {}
    if not _forwarder_token_ok(data):
        logger.warning("Rejected %s notice: invalid forwarder token", source)
        return jsonify({"status": "forbidden"}), 403
    token = request.view_args.get("token") if request.view_args else None
    token = token or request.args.get("seller_token") or data.get("seller_token")
    logger.info("Raw: %s", _safe_raw_log(raw))
    all_text = ("" if data else raw) + " " + " ".join(_notice_values(data))

    parsed = parse_bkash_payment_notice(all_text)
    used_structured_parse = False
    if not parsed:
        parsed = parsed_notice_from_forwarder_data(data)
        used_structured_parse = bool(parsed)
    ack = _payment_ack(parsed)
    if parsed and _callback:
        touch_webhook_notice(f"seller_{source}" if token else source, parsed.get("trx_id"), parsed.get("amount_bdt"))
        alert_sent = notify_admin_parsed_notice(parsed, source, all_text, "seller" if token else "main", token)
        meta = {"admin_parse_alert_sent": True} if alert_sent else {}
        if token:
            meta["seller_token"] = token
        notice_text = callback_notice_text(all_text, parsed, used_structured_parse)
        try:
            callback_result = _callback(notice_text, source, meta)
        except TypeError:
            callback_result = _callback(notice_text, source)
        outcome = _callback_payment_outcome(callback_result)
        if outcome:
            ack.update(outcome)
            payment_status = ack.get("payment_status")
            ack["matched_order"] = payment_status == "matched_order" or bool(ack.get("matched_order"))
            ack["duplicate"] = payment_status == "duplicate" or bool(ack.get("duplicate"))
            ack["manual_review"] = payment_status == "manual_review" or bool(ack.get("manual_review"))
        logger.info("bKash %s parsed: %s", source, parsed)
    elif parsed:
        notify_admin_parsed_notice(parsed, source, all_text, "seller" if token else "main", token)
        logger.warning("bKash %s parsed but callback is not ready: %s", source, parsed)
    else:
        logger.info("Not a supported bKash payment notice: %s", all_text[:100])

    return jsonify(ack)


@app.route("/sms", methods=["POST"])
@app.route("/seller/<token>/sms", methods=["POST"])
def sms(token=None):
    return handle_payment_notice("bkash_sms")


@app.route("/notification", methods=["POST"])
@app.route("/bkash-notification", methods=["POST"])
@app.route("/seller/<token>/notification", methods=["POST"])
def notification(token=None):
    return handle_payment_notice("bkash_app_notification")


@app.route("/forwarder-health", methods=["GET"])
@app.route("/seller/<token>/health", methods=["GET"])
def forwarder_health(token=None):
    token = token or request.args.get("seller_token")
    if token:
        ok = _seller_token_ok(token)
        status_code = 200 if ok else 403
        return jsonify({
            "status": "ok" if ok else "forbidden",
            "server_reachable": True,
            "mode": "seller",
            "auth_ok": ok,
            "message": "seller token accepted" if ok else "unknown or unapproved seller token",
        }), status_code

    if FORWARDER_SECRET and _supplied_forwarder_token() != FORWARDER_SECRET:
        return jsonify({
            "status": "forbidden",
            "server_reachable": True,
            "mode": "main",
            "auth_ok": False,
            "message": "invalid forwarder secret",
        }), 403

    return jsonify({
        "status": "ok",
        "server_reachable": True,
        "mode": "main",
        "auth_ok": True,
        "message": "forwarder secret accepted" if FORWARDER_SECRET else "forwarder secret is not required on this server",
    })


def _telegram_auth_page(token, message=None, error=None):
    session = get_personal_auth_session(token)
    if not session:
        title = "Telegram login link expired"
        body = "<p>This login link has expired or was already removed. Go back to the bot and tap Connect personal account again.</p>"
    else:
        status = session.get("status") or "new"
        title = "Telegram personal account login"
        notice = f"<div class='ok'>{escape(message)}</div>" if message else ""
        err = f"<div class='err'>{escape(error)}</div>" if error else ""
        if status == "connected":
            body = f"{notice}<p>✅ Personal account connected: <b>{escape(str(session.get('display_name') or 'Telegram account'))}</b>.</p><p>You can return to the bot and choose Forward with personal account.</p>"
        elif status == "password_needed":
            body = f"{notice}{err}<form method='post' action='/telegram-auth/{escape(token)}/password'><label>Telegram 2FA password</label><input name='password' type='password' autocomplete='current-password' required><button type='submit'>Complete login</button></form>"
        elif status == "code_sent":
            body = f"{notice}{err}<p>Telegram sent a login code to your Telegram app. Enter it here only. Do not paste it into any Telegram chat.</p><form method='post' action='/telegram-auth/{escape(token)}/code'><label>Login code</label><input name='code' inputmode='numeric' autocomplete='one-time-code' placeholder='12345' required><button type='submit'>Verify code</button></form>"
        else:
            body = f"{notice}{err}<p>Enter your own Telegram API details from <a href='https://my.telegram.org' target='_blank' rel='noreferrer'>my.telegram.org</a>. The login code must be entered on this page only, never in Telegram chat.</p><form method='post' action='/telegram-auth/{escape(token)}/send-code'><label>API ID</label><input name='api_id' inputmode='numeric' required><label>API hash</label><input name='api_hash' autocomplete='off' required><label>Telegram phone number</label><input name='phone' inputmode='tel' placeholder='+8801XXXXXXXXX' required><button type='submit'>Send Telegram login code</button></form>"
    return f"""
    <!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>
    <title>{escape(title)}</title>
    <style>body{{font-family:system-ui,-apple-system,Segoe UI,sans-serif;margin:0;background:#0f172a;color:#e2e8f0}}main{{max-width:520px;margin:0 auto;padding:28px 18px}}.card{{background:#111827;border:1px solid #334155;border-radius:16px;padding:20px;box-shadow:0 12px 32px #02061766}}label{{display:block;margin:14px 0 6px;color:#cbd5e1}}input{{box-sizing:border-box;width:100%;padding:13px;border-radius:10px;border:1px solid #475569;background:#020617;color:#f8fafc;font-size:16px}}button{{width:100%;margin-top:18px;padding:13px;border:0;border-radius:10px;background:#38bdf8;color:#082f49;font-weight:700;font-size:16px}}a{{color:#7dd3fc}}.warn{{color:#fbbf24}}.ok{{background:#064e3b;color:#d1fae5;padding:10px;border-radius:10px;margin-bottom:12px}}.err{{background:#7f1d1d;color:#fee2e2;padding:10px;border-radius:10px;margin-bottom:12px}}</style>
    </head><body><main><div class='card'><h1>{escape(title)}</h1>{body}<p class='warn'>Security: only connect your own account. Never share Telegram login codes in Telegram chats, groups, or bot DMs.</p></div></main></body></html>
    """


@app.route("/telegram-auth/<token>", methods=["GET"])
def telegram_auth(token):
    return _telegram_auth_page(token)


@app.route("/telegram-auth/<token>/send-code", methods=["POST"])
def telegram_auth_send_code(token):
    ok, result = send_personal_auth_code_sync(token, request.form.get("api_id"), request.form.get("api_hash"), request.form.get("phone"))
    if not ok:
        return _telegram_auth_page(token, error=result), 400
    return _telegram_auth_page(token, message="Login code sent. Check your Telegram app."), 200


@app.route("/telegram-auth/<token>/code", methods=["POST"])
def telegram_auth_code(token):
    ok, result = verify_personal_auth_code_sync(token, request.form.get("code"))
    if not ok:
        return _telegram_auth_page(token, error=result), 400
    if result.get("status") == "password_needed":
        return _telegram_auth_page(token, message="Two-step verification is enabled. Enter your Telegram 2FA password."), 200
    return _telegram_auth_page(token, message="Personal account connected."), 200


@app.route("/telegram-auth/<token>/password", methods=["POST"])
def telegram_auth_password(token):
    ok, result = verify_personal_auth_password_sync(token, request.form.get("password"))
    if not ok:
        return _telegram_auth_page(token, error=result), 400
    return _telegram_auth_page(token, message="Personal account connected."), 200


def _token_ok():
    if not DASHBOARD_TOKEN:
        return False
    supplied = request.args.get("token") or request.headers.get("X-Dashboard-Token") or request.headers.get("Authorization", "").replace("Bearer ", "")
    return supplied == DASHBOARD_TOKEN


@app.route("/admin", methods=["GET"])
@app.route("/dashboard", methods=["GET"])
def dashboard():
    if not _token_ok():
        return "Forbidden", 403
    snap = dashboard_snapshot(25)
    health = get_webhook_health()
    try:
        balances, _evm = get_all_balances()
    except Exception as exc:
        balances = {"error": str(exc)}
    try:
        gas_balances = get_native_gas_balances()
    except Exception as exc:
        gas_balances = {"error": str(exc)}

    def table(headers, rows):
        body = "".join("<tr>" + "".join(f"<td>{escape(str(cell))}</td>" for cell in row) + "</tr>" for row in rows)
        head = "".join(f"<th>{escape(str(h))}</th>" for h in headers)
        return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"

    html = f"""
    <!doctype html><html><head><meta charset='utf-8'><title>Mouno Admin</title>
    <style>body{{font-family:system-ui;margin:24px;background:#0f172a;color:#e2e8f0}}table{{border-collapse:collapse;width:100%;margin:12px 0 28px}}td,th{{border:1px solid #334155;padding:8px;text-align:left}}th{{background:#1e293b}}.card{{background:#111827;padding:16px;border-radius:12px;margin-bottom:16px}}code{{color:#93c5fd}}</style></head><body>
    <h1>Mouno Admin Dashboard</h1>
    <div class='card'><h2>Webhook</h2><p>Last notice: <code>{escape(str(health.get('last_notice_at')))}</code> Source: <code>{escape(str(health.get('source')))}</code> TrxID: <code>{escape(str(health.get('trx_id')))}</code></p></div>
    <div class='card'><h2>Balances</h2><pre>{escape(str(balances))}</pre></div>
    <div class='card'><h2>Gas</h2><pre>{escape(str(gas_balances))}</pre></div>
    <div class='card'><h2>Profit</h2><pre>Daily: {escape(str(snap['profit_daily']['overall']))}\nWeekly: {escape(str(snap['profit_weekly']['overall']))}</pre></div>
    <h2>Recent Orders</h2>{table(['trx_id','order_id','user_id','bdt','crypto','network','status','profit','source','created'], snap['transactions'])}
    <h2>Pending Orders</h2>{table(['trx_id','user_id','bdt','crypto','wallet','network','created','order_id'], snap['pending'])}
    <h2>Reservations</h2>{table(['id','order_id','trx_id','user_id','seller_id','network','crypto','status','reason','created','expires','updated'], snap['reservations'])}
    <h2>Audit Log</h2>{table(['id','actor','action','target_type','target_id','details','created'], snap['audit'])}
    <h2>Sellers</h2>{table(['user_id','status','updated'], snap['sellers'])}
    <h2>Payouts</h2>{table(['id','order_id','user_id','amount','method','details','status','note','created','updated'], snap['payouts'])}
    </body></html>
    """
    return html


def run_webhook():
    app.run(host="0.0.0.0", port=5000)
