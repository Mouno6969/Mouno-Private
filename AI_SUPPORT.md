# AI Support

The bot includes a read-only `🤖 AI Support` button and `/ai` command.

## Recommended setup

Use the bot admin menu:

1. Open the admin menu.
2. Tap `🤖 AI Setup`.
3. Choose a provider: OpenRouter, OpenAI, Gemini, or Off.
4. Tap `Set API key` and send the provider API key.
5. Tap `Set model` and send the model name.
6. Optional: tap `Set base URL` for an OpenAI-compatible custom provider.
7. Tap `Test AI`.

Settings saved from the bot are stored in SQLite `app_settings` and take priority over `.env` values. API keys are masked in the setup screen and are not logged.

If Gemini does not work, switch the provider to OpenRouter or OpenAI from `🤖 AI Setup` without changing code.

## Providers

- `openrouter` uses `https://openrouter.ai/api/v1/chat/completions`.
  - Default model: `openai/gpt-4o-mini`.
- `openai` uses `https://api.openai.com/v1/chat/completions`.
  - Default model: `gpt-4o-mini`.
- `gemini` keeps the legacy Google Gemini REST path.
  - Default model: `gemini-1.5-flash`.
- `off` disables AI Support.

## Environment fallback

Bot `app_settings` are checked first. If a setting is missing, `.env` is used:

```env
AI_PROVIDER=openrouter
AI_API_KEY=
AI_MODEL=
AI_BASE_URL=

# Legacy Gemini fallback still works
GEMINI_API_KEY=
GEMINI_MODEL=gemini-1.5-flash
```

`AI_BASE_URL` is only for OpenAI-compatible providers. Leave it empty for the built-in OpenRouter/OpenAI URLs.

## What AI can do

- Answer beginner support questions in Bengali, English, or Nigerian Pidgin
- Explain bKash and Nigerian local payment delay/notification issues
- Explain TrxID/reference/order ID/pending flow
- Explain Telegram Stars payments
- Explain wallet network and gas warnings
- Explain gift codes and connected-wallet funding at a high level
- Tell users to contact support

## What AI cannot do

- Approve payments
- Send crypto
- Change rates
- Access private keys
- Verify a payment by itself

The prompt intentionally keeps AI read-only for safety.

## Security note

If you ever paste an API key in a chat or public place, rotate/restrict it with the provider.
