# Mouno Private

Organized Python source for a Telegram crypto seller bot recovered from Termux `cat ~/mouno/...` output.

## What is included

- Telegram bot menu and order flow in `bot.py`
- SQLite persistence in `db.py`
- bKash SMS webhook parser in `webhook.py`
- Admin/user wallet management with encrypted private keys in `crypto_manager.py`
- Network senders for Solana, Polygon, BSC, Avalanche, Ethereum, Base, and Tron
- Balance checks and user guide text

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Fill `.env` with your Telegram, bKash, RPC, and wallet values.

## Run

```bash
python bot.py
```

The bot starts Telegram polling and a Flask webhook on port `5000` for `/sms`.

## Notes

- No private keys or bot tokens are committed. Use environment variables only.
- Runtime files such as `mouno.db`, `bot.log`, `rate.json`, and `.env` are ignored.
- Obvious Termux copy/paste formatting issues were corrected while preserving the project structure and behavior.
