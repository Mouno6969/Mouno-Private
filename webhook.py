import logging
import re

from flask import Flask, jsonify, request

app = Flask(__name__)
logger = logging.getLogger(__name__)
_callback = None


def set_callback(fn):
    global _callback
    _callback = fn


def parse_bkash_sms(text):
    pattern = r"You have received Tk ([\d,]+\.?\d*) from (\d+)\..*?TrxID (\w+) at (\d{2}/\d{2}/\d{4} \d{2}:\d{2})"
    match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
    if not match:
        return None
    return {
        "amount_bdt": float(match.group(1).replace(",", "")),
        "sender": match.group(2),
        "trx_id": match.group(3),
        "datetime": match.group(4),
    }


@app.route("/sms", methods=["POST"])
def sms():
    raw = request.get_data(as_text=True)
    data = request.json or {}
    logger.info("Raw: %s", raw[:300])
    all_text = raw + " " + " ".join(str(v) for v in data.values())

    if "You have received" in all_text:
        parsed = parse_bkash_sms(all_text)
        if parsed and _callback:
            _callback(all_text, "bkash")
            logger.info("bKash parsed: %s", parsed)
        else:
            logger.warning("Parse failed: %s", all_text[:100])
    else:
        logger.info("Not bKash: %s", all_text[:50])

    return jsonify({"status": "ok"})


def run_webhook():
    app.run(host="0.0.0.0", port=5000)
