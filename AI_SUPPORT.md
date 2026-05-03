# AI Support

The bot includes a read-only `🤖 AI Support` button and `/ai` command.

## Configure

Admins can configure AI inside Telegram from `⚙️ AI Setup`:

1. Press `⚙️ AI Setup` from the admin menu.
2. Choose Gemini, Groq, OpenRouter, Hugging Face, Cohere, or Mistral.
3. Use `🔑 Set API Key` and `🧠 Set Model` to save values in the bot database.
4. Use `🔁 Fallback Order` to change provider priority, for example `gemini,groq,openrouter,huggingface,cohere,mistral`.

Bot-saved keys and fallback order are used immediately; restart is not required. `🧹 Clear Bot Key` only removes the database override and does not change `.env`.

`.env` remains optional/manual. Set one or more free/free-tier provider keys in `.env` if you prefer file-based configuration:

```env
AI_PROVIDER_ORDER=gemini,groq,openrouter,huggingface,cohere,mistral
GEMINI_API_KEY=your_google_ai_studio_key
GEMINI_MODEL=gemini-1.5-flash
GROQ_API_KEY=your_groq_key
GROQ_MODEL=llama-3.1-8b-instant
OPENROUTER_API_KEY=your_openrouter_key
OPENROUTER_MODEL=meta-llama/llama-3.1-8b-instruct:free
HUGGINGFACE_API_KEY=your_huggingface_token
HUGGINGFACE_MODEL=HuggingFaceH4/zephyr-7b-beta
COHERE_API_KEY=your_cohere_key
COHERE_MODEL=command-r
MISTRAL_API_KEY=your_mistral_key
MISTRAL_MODEL=mistral-small-latest
```

You can set only one key, or multiple keys. The bot supports Gemini, Groq, OpenRouter, Hugging Face, Cohere, and Mistral. It reads bot database settings first, then falls back to `.env`. It tries the first configured provider in the current fallback order and automatically falls back to the next configured provider if one fails or returns an empty answer. Restart the bot only after editing `.env` manually.

These are free/free-tier/trial options where available; provider quotas and availability are not guaranteed unlimited.

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
