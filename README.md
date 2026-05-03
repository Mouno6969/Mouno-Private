# Mouno Private

Organized Python source for a Telegram crypto seller bot recovered from Termux `cat ~/mouno/...` output.

## What is included

- Telegram bot menu and order flow in `bot.py`
- Bengali/English language selection with stored user preferences
- Telegram Stars payment flow with automatic crypto delivery after successful payment
- Button-driven admin gift-code generation flow
- Button-driven admin asset send flow across supported networks
- Admin dashboard commands, backup, maintenance mode, failed-send retry, order IDs, reservations, profit tracking, audit log, gas monitor, terms/support, and gas warnings
- AI Support button using fast NVIDIA Build/NIM Llama 3.1 8B, Qwen2 7B, Mistral Small 24B, Nemotron Nano 8B, and Llama 4 Scout first; Groq/OpenRouter/Gemini and other providers next; slow NVIDIA Kimi/DeepSeek/Gemma remain bottom fallbacks
- Admin Menu → ⚙️ AI Setup can save AI API keys at runtime from inside Telegram; useful for Termux/main branch runs without editing `.env` or restarting
- SQLite persistence in `db.py`
- bKash SMS webhook parser in `webhook.py`
- Delayed-SMS pending order recovery and `/pending` admin fallback
- Admin/user wallet management with encrypted private keys in `crypto_manager.py`
- Network senders for Solana, Polygon, BSC, Avalanche, Ethereum, Base, Tron, and TON
- Balance checks with active stock reservations, native gas monitoring, seller public stats, and user guide text

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
- New order/admin tools: `/help`, `/order ORD-XXXXXX`, `/status TRXID_OR_ORDERID`, `/receipt ORD_OR_TRX`, `/seller USER_ID`, `/seller_badge USER_ID new|verified|trusted`, `/seller_dashboard`, `/report [weekly]`, `/profit [daily|weekly]`, `/costrate [NETWORK RATE]`, `/gas`, `/reservations`, `/audit`, `/payout`, `/payouts`, `/webhook_health`, `/bot_health`, `/restart_help`, `/test_sms`, `/test_seller_sms`, `/aiadmin why order failed ORD-123`, `/ai_usage`.
- Confirmed buyer/Stars orders reserve seller stock until completed, rejected, cancelled, failed, or expired. User-facing stock checks show stock available after reserves.
- Profit snapshots are stored on completed transactions with sale rate, cost rate, profit BDT, margin, and source (`bkash`, `stars`, `gift`, `wallet`, `admin_send`). Configure `DEFAULT_COST_RATE_BDT`, `COST_RATE_<NETWORK>`, or `/costrate NETWORK RATE`.
- Native gas checks cover Solana, Polygon, BSC, Avalanche, Ethereum, Base, Tron, and TON. `LOW_GAS_THRESHOLD_*` values block new buyer orders when gas is definitely below threshold; unknown gas checks warn/log but do not block sends.
- Admin audit events record badge changes, approvals/rejections, retries, payouts, maintenance, rates, cost rates, backups, test SMS, reservations, and admin sends.
- Seller/admin menu buttons include order status lookup, seller dashboard with low-balance and webhook-health warnings, bot health, safe restart guide, reports, payout review, seller badges, test tools, and backup now.
- `LOW_BALANCE_THRESHOLD` and optional `LOW_BALANCE_THRESHOLD_NETWORK` values control low-stock warnings. `LOW_GAS_THRESHOLD_*` controls gas monitor thresholds. `WEBHOOK_STALE_MINUTES` controls bKash webhook health.
- Flask `/admin` and `/dashboard` provide a minimal protected dashboard when `DASHBOARD_TOKEN` or `ADMIN_WEB_TOKEN` is set. Pass the token with `?token=` or `X-Dashboard-Token`.
- Daily admin report and database backup are sent near local midnight. Optional `BACKUP_UPLOAD_URL` can receive the backup file; no Google OAuth flow is bundled.
- Admins can configure AI API keys from Admin Menu → ⚙️ AI Setup and monitor per-model success/failure counts from 📊 AI Usage; setup buttons follow the enforced fast-provider-first order. Keys saved this way are stored in local SQLite `mouno.db` and take effect immediately. `.env` AI keys remain supported as fallback/configuration.
- Runtime files such as `mouno.db`, `bot.log`, `rate.json`, and `.env` are ignored.
- Obvious Termux copy/paste formatting issues were corrected while preserving the project structure and behavior.
