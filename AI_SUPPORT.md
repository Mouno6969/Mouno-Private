# AI Support

The bot includes a read-only `🤖 AI Support` button and `/ai` command.

## Configure

Set one or more free/free-tier provider keys in `.env`:

```env
AI_PROVIDER_ORDER=nvidia_llama_8b,nvidia_qwen_7b,nvidia_mistral_small,nvidia_nemotron_nano,nvidia_llama4_scout,groq,openrouter,gemini,huggingface,cohere,mistral,nvidia_kimi,nvidia_deepseek,nvidia_gemma
NVIDIA_API_KEY=your_nvidia_build_nim_key
NVIDIA_LLAMA_8B_API_KEY=
NVIDIA_LLAMA_8B_MODEL=meta/llama-3.1-8b-instruct
NVIDIA_QWEN_7B_API_KEY=
NVIDIA_QWEN_7B_MODEL=qwen/qwen2-7b-instruct
NVIDIA_MISTRAL_SMALL_API_KEY=
NVIDIA_MISTRAL_SMALL_MODEL=mistralai/mistral-small-24b-instruct
NVIDIA_NEMOTRON_NANO_API_KEY=
NVIDIA_NEMOTRON_NANO_MODEL=nvidia/llama-3.1-nemotron-nano-8b-v1
NVIDIA_LLAMA4_SCOUT_API_KEY=
NVIDIA_LLAMA4_SCOUT_MODEL=meta/llama-4-scout-17b-16e-instruct
# Slow/heavy fallback models
NVIDIA_KIMI_API_KEY=
NVIDIA_KIMI_MODEL=moonshotai/kimi-k2.6
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

You can set only one key, or multiple keys. The bot supports fast NVIDIA Build/NIM providers first (`nvidia_llama_8b`, `nvidia_qwen_7b`, `nvidia_mistral_small`, `nvidia_nemotron_nano`, `nvidia_llama4_scout`), then Groq, OpenRouter, Gemini, Hugging Face, Cohere, and Mistral. Slow/heavy NVIDIA Kimi K2.6, DeepSeek V4 Pro, and Gemma 4 31B remain available as bottom fallback providers. The bot enforces this practical order even if an old `.env` has a different `AI_PROVIDER_ORDER`, while still adding valid future providers without duplicates. It automatically falls back to the next configured provider if one fails or returns an empty answer. Use `NVIDIA_API_KEY` as a shared NVIDIA key, or per-model `NVIDIA_*_API_KEY` values when needed. Admins can view model success/failure counts from Admin Menu → 📊 AI Usage or `/ai_usage`. Restart the bot after editing `.env`.

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
