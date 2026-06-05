import logging
import requests

import config
import db

logger = logging.getLogger(__name__)

_TIMEOUT = 8

_PROVIDER_ENV_KEYS = {
    "cerebras": lambda: config.CEREBRAS_API_KEY,
    "groq": lambda: config.GROQ_API_KEY,
    "gemini": lambda: config.GEMINI_API_KEY,
    "nvidia_deepseek": lambda: config.NVIDIA_DEEPSEEK_API_KEY,
    "nvidia_kimi": lambda: config.NVIDIA_KIMI_API_KEY,
    "nvidia_gemma": lambda: config.NVIDIA_GEMMA_API_KEY,
    "openrouter": lambda: config.OPENROUTER_API_KEY,
    "mistral": lambda: config.MISTRAL_API_KEY,
    "cohere": lambda: config.COHERE_API_KEY,
    "nvidia_mistral_small": lambda: config.NVIDIA_MISTRAL_SMALL_API_KEY,
    "nvidia_llama4_scout": lambda: config.NVIDIA_LLAMA4_SCOUT_API_KEY,
    "nvidia_nemotron_nano": lambda: config.NVIDIA_NEMOTRON_NANO_API_KEY,
    "nvidia_qwen_7b": lambda: config.NVIDIA_QWEN_7B_API_KEY,
    "nvidia_llama_8b": lambda: config.NVIDIA_LLAMA_8B_API_KEY,
    "huggingface": lambda: config.HUGGINGFACE_API_KEY,
}

_DB_SETTING_KEYS = {
    "cerebras": "ai_cerebras_api_key",
    "groq": "ai_groq_api_key",
    "gemini": "ai_gemini_api_key",
    "nvidia_deepseek": "ai_nvidia_deepseek_api_key",
    "nvidia_kimi": "ai_nvidia_kimi_api_key",
    "nvidia_gemma": "ai_nvidia_gemma_api_key",
    "openrouter": "ai_openrouter_api_key",
    "mistral": "ai_mistral_api_key",
    "cohere": "ai_cohere_api_key",
    "nvidia_mistral_small": "ai_nvidia_mistral_small_api_key",
    "nvidia_llama4_scout": "ai_nvidia_llama4_scout_api_key",
    "nvidia_nemotron_nano": "ai_nvidia_nemotron_nano_api_key",
    "nvidia_qwen_7b": "ai_nvidia_qwen_7b_api_key",
    "nvidia_llama_8b": "ai_nvidia_llama_8b_api_key",
    "huggingface": "ai_huggingface_api_key",
}

_OPENAI_PROVIDERS = {
    "cerebras": lambda: ("https://api.cerebras.ai/v1/chat/completions", config.CEREBRAS_MODEL),
    "groq": lambda: ("https://api.groq.com/openai/v1/chat/completions", config.GROQ_MODEL),
    "openrouter": lambda: ("https://openrouter.ai/api/v1/chat/completions", config.OPENROUTER_MODEL),
    "mistral": lambda: ("https://api.mistral.ai/v1/chat/completions", config.MISTRAL_MODEL),
    "huggingface": lambda: (f"https://api-inference.huggingface.co/models/{config.HUGGINGFACE_MODEL}/v1/chat/completions", config.HUGGINGFACE_MODEL),
    "nvidia_deepseek": lambda: ("https://integrate.api.nvidia.com/v1/chat/completions", config.NVIDIA_DEEPSEEK_MODEL),
    "nvidia_kimi": lambda: ("https://integrate.api.nvidia.com/v1/chat/completions", config.NVIDIA_KIMI_MODEL),
    "nvidia_gemma": lambda: ("https://integrate.api.nvidia.com/v1/chat/completions", config.NVIDIA_GEMMA_MODEL),
    "nvidia_mistral_small": lambda: ("https://integrate.api.nvidia.com/v1/chat/completions", config.NVIDIA_MISTRAL_SMALL_MODEL),
    "nvidia_llama4_scout": lambda: ("https://integrate.api.nvidia.com/v1/chat/completions", config.NVIDIA_LLAMA4_SCOUT_MODEL),
    "nvidia_nemotron_nano": lambda: ("https://integrate.api.nvidia.com/v1/chat/completions", config.NVIDIA_NEMOTRON_NANO_MODEL),
    "nvidia_qwen_7b": lambda: ("https://integrate.api.nvidia.com/v1/chat/completions", config.NVIDIA_QWEN_7B_MODEL),
    "nvidia_llama_8b": lambda: ("https://integrate.api.nvidia.com/v1/chat/completions", config.NVIDIA_LLAMA_8B_MODEL),
}


def _get_provider_key(provider):
    setting_key = _DB_SETTING_KEYS.get(provider)
    if setting_key:
        try:
            val = (db.get_setting(setting_key) or "").strip()
            if val:
                return val
        except Exception:
            pass
    env_fn = _PROVIDER_ENV_KEYS.get(provider)
    return (env_fn() or "").strip() if env_fn else ""


def _configured_providers():
    order_str = getattr(config, "AI_PROVIDER_ORDER", "")
    order = [p.strip() for p in order_str.split(",") if p.strip()] if order_str else list(_PROVIDER_ENV_KEYS.keys())
    return [(p, _get_provider_key(p)) for p in order if _get_provider_key(p)]


def _ask_openai_compatible(endpoint, api_key, model, question):
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": f"You are a helpful support assistant for BGC Crypto. Support: @{config.SUPPORT_USERNAME}"},
            {"role": "user", "content": question},
        ],
        "temperature": 0.2,
        "max_tokens": 850,
    }
    resp = requests.post(endpoint, headers=headers, json=payload, timeout=_TIMEOUT)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"].strip()


def _ask_gemini(api_key, question):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{config.GEMINI_MODEL}:generateContent?key={api_key}"
    payload = {"contents": [{"parts": [{"text": question}]}]}
    resp = requests.post(url, json=payload, timeout=_TIMEOUT)
    resp.raise_for_status()
    return resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()


def _ask_cohere(api_key, question):
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {"model": config.COHERE_MODEL, "message": question, "temperature": 0.2}
    resp = requests.post("https://api.cohere.ai/v1/chat", headers=headers, json=payload, timeout=_TIMEOUT)
    resp.raise_for_status()
    return resp.json()["text"].strip()


def ask_ai_support(question, lang="bn", context=None):
    if context:
        question = f"Context: {context}\n\nQuestion: {question}"

    providers = _configured_providers()
    if not providers:
        return "AI Support is currently unavailable. No AI provider is configured."

    last_error = None
    for provider, api_key in providers:
        try:
            if provider == "gemini":
                return _ask_gemini(api_key, question)
            if provider == "cohere":
                return _ask_cohere(api_key, question)
            info = _OPENAI_PROVIDERS.get(provider)
            if info:
                endpoint, model = info()
                return _ask_openai_compatible(endpoint, api_key, model, question)
            logger.warning("Unknown AI provider: %s", provider)
        except Exception as exc:
            last_error = exc
            logger.warning("AI provider %s failed: %s", provider, exc)
            continue

    logger.error("All AI providers failed. Last error: %s", last_error)
    return "Sorry, AI support is temporarily unavailable. Please try again later."
