import logging
import re
from html import escape

from flask import Flask, jsonify, request

from balance import get_all_balances
from config import DASHBOARD_TOKEN
from db import dashboard_snapshot, get_webhook_health, touch_webhook_notice

app = Flask(__name__)
logger = logging.getLogger(__name__)
_callback = None


def set_callback(fn):
    global _callback
    _callback = fn


def _amount_to_float(value):
    return float(value.replace(",", ""))


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


def handle_payment_notice(source):
    raw = request.get_data(as_text=True)
    data = request.json or {}
    logger.info("Raw: %s", raw[:300])
    all_text = raw + " " + " ".join(str(v) for v in data.values())

    parsed = parse_bkash_payment_notice(all_text)
    if parsed and _callback:
        touch_webhook_notice(source, parsed.get("trx_id"), parsed.get("amount_bdt"))
        _callback(all_text, source)
        logger.info("bKash %s parsed: %s", source, parsed)
    elif parsed:
        logger.warning("bKash %s parsed but callback is not ready: %s", source, parsed)
    else:
        logger.info("Not a supported bKash payment notice: %s", all_text[:100])

    return jsonify({"status": "ok"})


@app.route("/sms", methods=["POST"])
def sms():
    return handle_payment_notice("bkash_sms")


@app.route("/notification", methods=["POST"])
@app.route("/bkash-notification", methods=["POST"])
def notification():
    return handle_payment_notice("bkash_app_notification")


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
    <h2>Recent Orders</h2>{table(['trx_id','order_id','user_id','bdt','crypto','network','status','created'], snap['transactions'])}
    <h2>Pending Orders</h2>{table(['trx_id','user_id','bdt','crypto','wallet','network','created','order_id'], snap['pending'])}
    <h2>Sellers</h2>{table(['user_id','status','updated'], snap['sellers'])}
    <h2>Payouts</h2>{table(['id','order_id','user_id','amount','method','details','status','note','created','updated'], snap['payouts'])}
    </body></html>
    """
    return html


def run_webhook():
    app.run(host="0.0.0.0", port=5000)
