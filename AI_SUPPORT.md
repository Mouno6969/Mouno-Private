# AI Support

The bot includes a read-only `🤖 AI Support` button and `/ai` command.

## Configure

Add your Gemini API key to `.env`:

```env
GEMINI_API_KEY=your_google_ai_studio_key
GEMINI_MODEL=gemini-1.5-flash
```

Do not hardcode the API key in code and do not commit `.env`.

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

Admins can use `/aistatus` for local AI setup diagnostics. It shows whether the Gemini API key is configured, model name, support username, pending bKash count, maintenance mode, and confirms AI context is sanitized/read-only. It does not call Gemini.
