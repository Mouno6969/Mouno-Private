# AI Support

The bot includes a read-only `🤖 AI Support` button and `/ai` command.

## Configure providers

AI Support uses a fallback chain. It tries the first configured provider, then automatically tries the next configured provider if the current one times out, returns an HTTP/quota error, or returns an empty response.

Default priority:

1. Gemini
2. Groq
3. OpenRouter
4. Together
5. Hugging Face Inference
6. Mistral

Configure providers in `.env` or from Telegram as admin:

```env
GEMINI_API_KEY=your_google_ai_studio_key
GEMINI_MODEL=gemini-1.5-flash
GROQ_API_KEY=your_groq_key
GROQ_MODEL=llama-3.1-8b-instant
OPENROUTER_API_KEY=your_openrouter_key
OPENROUTER_MODEL=meta-llama/llama-3.1-8b-instruct:free
HF_API_KEY=your_huggingface_key
HF_MODEL=mistralai/Mistral-7B-Instruct-v0.3
TOGETHER_API_KEY=your_together_key
TOGETHER_MODEL=meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo
MISTRAL_API_KEY=your_mistral_key
MISTRAL_MODEL=open-mistral-7b
```

Do not hardcode API keys in code and do not commit `.env`.

## Telegram admin setup

Admins can open `/aisetup` or tap `🤖 AI Setup` in the admin menu.

- Provider buttons show `✅` when a key is configured from Telegram DB or `.env`, and `➕` when missing.
- Tap a provider to add/update the API key, clear the Telegram DB key, or set a model name.
- When an API key is sent, the bot deletes the Telegram message after receipt and never echoes the key back.
- Telegram-provided keys are stored raw in SQLite `app_settings` because there is no general API-key encryption layer. Protect DB backups and exported `/backup` files as secrets.
- Clearing a key removes only the Telegram DB key. If the same provider has an `.env` key, it remains active through env fallback.

## What AI can do

- Answer beginner support questions in Bengali, English, or Nigerian Pidgin/Pidgin English
- Use sanitized read-only context from the user's recent transactions, pending bKash orders, and Telegram Stars orders
- Explain bKash payment delay/notification issues, TrxID/order ID, pending flow, wallet network, and gas warnings
- For pending, stuck, proof, dispute, or status questions, tell users to keep payment proof/screenshot/receipt plus TrxID/order ID ready for admin/support verification
- Point users to support when manual review or retry is needed

## Safe identifiers users may share

- Order ID
- bKash TrxID
- Telegram Stars order ID
- Public wallet address, preferably partial
- Payment proof/screenshot/receipt for admin verification

## What AI cannot do

- Approve payments or mark orders paid
- Send crypto or perform admin/write actions
- Change rates or settings
- Access private keys or raw SMS
- Verify a payment by itself
- Ask for private key, seed phrase, wallet password, bot token, API key, OTP, or admin credentials

If a secret is exposed, the AI should tell the user to delete it and rotate/change it immediately.

## Diagnostics

Admins can use `/aistatus` or the `📊 AI Status` admin button for local AI setup diagnostics. It shows all providers, configured source (`env`, `telegram`, or missing), model, fallback priority, support username, pending bKash count, maintenance mode, and confirms AI context is sanitized/read-only. It does not call external AI APIs.
