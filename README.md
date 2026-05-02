# Mouno Private

Organized Python source for a Telegram crypto seller bot recovered from Termux `cat ~/mouno/...` output.

## What is included

- Telegram bot menu and order flow in `bot.py`
- Bengali/English language selection with stored user preferences
- Telegram Stars payment flow with automatic crypto delivery after successful payment
- Button-driven admin gift-code generation flow
- Button-driven admin asset send flow across supported networks
- Admin dashboard commands, backup, maintenance mode, failed-send retry, order IDs, terms/support, and gas warnings
- Read-only AI Support button using Gemini API through `GEMINI_API_KEY`, with sanitized recent order context and Bengali/English/Pidgin replies
- SQLite persistence in `db.py`
- bKash SMS webhook parser in `webhook.py`
- Delayed-SMS pending order recovery and `/pending` admin fallback
- Admin/user wallet management with encrypted private keys in `crypto_manager.py`
- Network senders for Solana, Polygon, BSC, Avalanche, Ethereum, Base, Tron, and TON
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
- `STAR_RATE` controls how many Telegram Stars equal 1 USDC/USDT. Use `STAR_RATE_SOLANA`, `STAR_RATE_TRC20`, etc. for per-network overrides.
- Runtime files such as `mouno.db`, `bot.log`, `rate.json`, and `.env` are ignored.
- Obvious Termux copy/paste formatting issues were corrected while preserving the project structure and behavior.
