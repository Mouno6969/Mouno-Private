# AI Support

The bot includes a read-only `🤖 AI Support` button and `/ai` command.

## Configure

Set one or more free/free-tier provider keys in `.env`:

```env
AI_PROVIDER_ORDER=nvidia_deepseek,nvidia_gemma,gemini,groq,openrouter,huggingface,cohere,mistral
NVIDIA_API_KEY=your_nvidia_build_nim_key
NVIDIA_DEEPSEEK_API_KEY=
NVIDIA_DEEPSEEK_MODEL=deepseek-ai/deepseek-v4-pro
NVIDIA_GEMMA_API_KEY=
NVIDIA_GEMMA_MODEL=google/gemma-4-31b-it
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

You can set only one key, or multiple keys. The bot supports NVIDIA Build/NIM DeepSeek V4 Pro, NVIDIA Build/NIM Gemma 4 31B, Gemini, Groq, OpenRouter, Hugging Face, Cohere, and Mistral. NVIDIA providers are always first priority when configured: the bot tries `nvidia_deepseek`, then `nvidia_gemma`, then the remaining configured providers in `AI_PROVIDER_ORDER` with duplicates removed. It automatically falls back to the next configured provider if one fails or returns an empty answer. Use `NVIDIA_API_KEY` as a shared NVIDIA key, or `NVIDIA_DEEPSEEK_API_KEY` / `NVIDIA_GEMMA_API_KEY` for per-model keys. Restart the bot after editing `.env`.

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
