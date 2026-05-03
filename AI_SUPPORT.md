# AI Support

The bot includes a read-only `🤖 AI Support` button and `/ai` command.

## Configure

Set one or more free/free-tier provider keys in `.env`:

```env
AI_PROVIDER_ORDER=gemini,groq,openrouter
GEMINI_API_KEY=your_google_ai_studio_key
GEMINI_MODEL=gemini-1.5-flash
GROQ_API_KEY=your_groq_key
GROQ_MODEL=llama-3.1-8b-instant
OPENROUTER_API_KEY=your_openrouter_key
OPENROUTER_MODEL=meta-llama/llama-3.1-8b-instruct:free
```

You can set only one key, or multiple keys. The bot tries the first configured provider in `AI_PROVIDER_ORDER` and automatically falls back to the next configured provider if one fails. Restart the bot after editing `.env`.

Do not hardcode the API key in code and do not commit `.env`.

## What AI can do

- Answer beginner support questions in Bengali/English
- Explain bKash payment delay/notification issues
- Explain TrxID/order ID/pending flow
- Explain wallet network and gas warnings
- Tell users to contact support

## What AI cannot do

- Approve payments
- Send crypto
- Change rates
- Access private keys
- Verify a payment by itself

The prompt intentionally keeps AI read-only for safety.

## Security note

If you ever paste your API key in a chat or public place, rotate/restrict it in the provider dashboard.
