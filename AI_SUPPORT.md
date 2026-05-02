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

If you ever paste your API key in a chat or public place, rotate/restrict it in Google AI Studio.
