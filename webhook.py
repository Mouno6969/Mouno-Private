import logging
import re

from flask import Flask, jsonify, request

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


def run_webhook():
    app.run(host="0.0.0.0", port=5000)
