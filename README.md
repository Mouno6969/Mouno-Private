# Mouno Private

Organized Python source for a Telegram crypto seller bot recovered from Termux `cat ~/mouno/...` output.

## What is included

- Telegram bot menu and order flow in `bot.py`
- Bengali, English, and Nigerian Pidgin language selection with stored user preferences
- Telegram Stars payment flow with automatic crypto delivery after successful payment
- Button-driven admin gift-code generation flow
- Button-driven admin asset send flow across supported networks
- Admin dashboard commands, backup, maintenance mode, failed-send retry, order IDs, terms/support, and gas warnings
- AI Support button with configurable OpenRouter, OpenAI, or Gemini providers
- SQLite persistence in `db.py`
- bKash SMS webhook parser in `webhook.py`
- Nigerian local payment automation with bot-collected admin setup, NGN rates, and SMS/app notification forwarding (`NIGERIA_PAYMENT_AUTOMATION.md`)
- Delayed-SMS/app-notification pending order recovery and `/pending` admin fallback
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

Fill `.env` with your Telegram, bKash, RPC, and wallet values. Nigeria local payment details are configured inside the bot via `🇳🇬 Nigeria Pay Setup`. AI Support can be configured inside the bot via `🤖 AI Setup`.

## Run

```bash
python bot.py
```

The bot starts Telegram polling and a Flask webhook on port `5000` for bKash endpoints (`/sms`, `/notification`, `/bkash-notification`) and Nigeria endpoints (`/ng-sms`, `/ng-notification`, `/nigeria-notification`).

## Notes

- No private keys or bot tokens are committed. Use environment variables only.
- `STAR_RATE` controls how many Telegram Stars equal 1 USDC/USDT. Use `STAR_RATE_SOLANA`, `STAR_RATE_TRC20`, etc. for per-network overrides.
- AI Support supports OpenRouter, OpenAI, and Gemini. Recommended setup: Admin menu → `🤖 AI Setup` → choose provider → set API key → set model → `Test AI`. Bot settings override `.env` fallbacks (`AI_PROVIDER`, `AI_API_KEY`, `AI_MODEL`, `AI_BASE_URL`, plus legacy `GEMINI_API_KEY`/`GEMINI_MODEL`). If Gemini does not work, switch to OpenRouter or OpenAI without code changes.
- Runtime files such as `mouno.db`, `bot.log`, `rate.json`, and `.env` are ignored.
- Obvious Termux copy/paste formatting issues were corrected while preserving the project structure and behavior.
