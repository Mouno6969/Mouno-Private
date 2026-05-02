import re

import requests

from config import (
    GEMINI_API_KEY,
    GEMINI_MODEL,
    GROQ_API_KEY,
    GROQ_MODEL,
    OPENROUTER_API_KEY,
    OPENROUTER_MODEL,
    HF_API_KEY,
    HF_MODEL,
    TOGETHER_API_KEY,
    TOGETHER_MODEL,
    MISTRAL_API_KEY,
    MISTRAL_MODEL,
)
from db import get_setting


AI_PROVIDERS = [
    {
        "id": "gemini",
        "name": "Gemini",
        "key_env": "GEMINI_API_KEY",
        "model_env": "GEMINI_MODEL",
        "env_key": GEMINI_API_KEY,
        "env_model": GEMINI_MODEL,
        "default_model": "gemini-1.5-flash",
        "kind": "gemini",
    },
    {
        "id": "groq",
        "name": "Groq",
        "key_env": "GROQ_API_KEY",
        "model_env": "GROQ_MODEL",
        "env_key": GROQ_API_KEY,
        "env_model": GROQ_MODEL,
        "default_model": "llama-3.1-8b-instant",
        "kind": "openai",
        "url": "https://api.groq.com/openai/v1/chat/completions",
    },
    {
        "id": "openrouter",
        "name": "OpenRouter",
        "key_env": "OPENROUTER_API_KEY",
        "model_env": "OPENROUTER_MODEL",
        "env_key": OPENROUTER_API_KEY,
        "env_model": OPENROUTER_MODEL,
        "default_model": "meta-llama/llama-3.1-8b-instruct:free",
        "kind": "openai",
        "url": "https://openrouter.ai/api/v1/chat/completions",
    },
    {
        "id": "together",
        "name": "Together",
        "key_env": "TOGETHER_API_KEY",
        "model_env": "TOGETHER_MODEL",
        "env_key": TOGETHER_API_KEY,
        "env_model": TOGETHER_MODEL,
        "default_model": "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
        "kind": "openai",
        "url": "https://api.together.xyz/v1/chat/completions",
    },
    {
        "id": "huggingface",
        "name": "HuggingFace",
        "key_env": "HF_API_KEY",
        "model_env": "HF_MODEL",
        "env_key": HF_API_KEY,
        "env_model": HF_MODEL,
        "default_model": "mistralai/Mistral-7B-Instruct-v0.3",
        "kind": "huggingface",
    },
    {
        "id": "mistral",
        "name": "Mistral",
        "key_env": "MISTRAL_API_KEY",
        "model_env": "MISTRAL_MODEL",
        "env_key": MISTRAL_API_KEY,
        "env_model": MISTRAL_MODEL,
        "default_model": "open-mistral-7b",
        "kind": "openai",
        "url": "https://api.mistral.ai/v1/chat/completions",
    },
]

_PROVIDER_BY_ID = {provider["id"]: provider for provider in AI_PROVIDERS}
_SECRET_PATTERNS = [
    re.compile(r"(?i)(key|api_key|token|access_token|authorization|bearer)(\s*[=:]\s*)[^\s&]+"),
    re.compile(r"(?i)bearer\s+[a-z0-9._\-]{12,}"),
    re.compile(r"[A-Za-z0-9_\-]{32,}"),
]


class AIProviderError(RuntimeError):
    pass


def provider_by_id(provider_id):
    return _PROVIDER_BY_ID.get(provider_id)


def provider_setting_key(provider_id):
    return f"ai_provider_{provider_id}_api_key"


def provider_model_setting_key(provider_id):
    return f"ai_provider_{provider_id}_model"


def sanitize_ai_error(value):
    text = str(value or "")[:500]
    for pattern in _SECRET_PATTERNS:
        text = pattern.sub(lambda match: f"{match.group(1)}{match.group(2)}[redacted]" if match.lastindex == 2 else "[redacted]", text)
    text = re.sub(r"https?://\S+", "[url]", text)
    return text[:180] or type(value).__name__


def configured_api_key(provider):
    db_value = (get_setting(provider_setting_key(provider["id"]), "") or "").strip()
    if db_value:
        return db_value, "telegram"
    env_value = (provider.get("env_key") or "").strip()
    if env_value:
        return env_value, "env"
    return "", "missing"


def configured_model(provider):
    return (
        (get_setting(provider_model_setting_key(provider["id"]), "") or "").strip()
        or (provider.get("env_model") or "").strip()
        or provider["default_model"]
    )


def provider_statuses():
    rows = []
    for index, provider in enumerate(AI_PROVIDERS, 1):
        key, source = configured_api_key(provider)
        rows.append(
            {
                "id": provider["id"],
                "name": provider["name"],
                "configured": bool(key),
                "source": source,
                "model": configured_model(provider),
                "priority": index,
                "key_env": provider["key_env"],
                "model_env": provider["model_env"],
            }
        )
    return rows


def configured_providers():
    result = []
    for provider in AI_PROVIDERS:
        key, source = configured_api_key(provider)
        if key:
            item = dict(provider)
            item["api_key"] = key
            item["key_source"] = source
            item["model"] = configured_model(provider)
            result.append(item)
    return result


def build_ai_user_text(question, order_context):
    return (
        "READ-ONLY ORDER CONTEXT\n"
        f"{(order_context or 'No recent order context is available.')[:4000]}\n\n"
        "USER QUESTION\n"
        f"{(question or '')[:3000]}"
    )


def extract_openai_text(data):
    choices = data.get("choices", []) if isinstance(data, dict) else []
    if not choices:
        return ""
    message = choices[0].get("message") or {}
    content = message.get("content") or choices[0].get("text") or ""
    if isinstance(content, list):
        return "".join(part.get("text", "") if isinstance(part, dict) else str(part) for part in content).strip()
    return str(content).strip()


def extract_hf_text(data):
    if isinstance(data, list) and data:
        text = extract_hf_text(data[0])
        if text:
            return text
    if isinstance(data, dict):
        if data.get("error"):
            raise AIProviderError(sanitize_ai_error(data.get("error")))
        if "generated_text" in data:
            return str(data.get("generated_text") or "").strip()
        text = extract_openai_text(data)
        if text:
            return text
        for key in ("summary_text", "translation_text", "text"):
            if data.get(key):
                return str(data[key]).strip()
    return ""


def post_json(provider, url, headers, payload, params=None):
    try:
        response = requests.post(url, headers=headers, params=params, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.HTTPError as exc:
        response = getattr(exc, "response", None)
        status = getattr(response, "status_code", "unknown")
        reason = getattr(response, "reason", "") or ""
        body = ""
        try:
            body = (response.text or "")[:160] if response is not None else ""
        except Exception:
            body = ""
        raise AIProviderError(f"HTTP status={status} reason={sanitize_ai_error(reason)} body={sanitize_ai_error(body)}") from None
    except requests.RequestException as exc:
        raise AIProviderError(type(exc).__name__) from None
    except ValueError:
        raise AIProviderError("invalid_json_response") from None


def ask_gemini(provider, system_prompt, user_text):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{provider['model']}:generateContent"
    payload = {
        "systemInstruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"role": "user", "parts": [{"text": user_text}]}],
        "generationConfig": {"temperature": 0.2, "maxOutputTokens": 650},
    }
    data = post_json(provider, url, {}, payload, params={"key": provider["api_key"]})
    candidates = data.get("candidates", []) if isinstance(data, dict) else []
    if not candidates:
        raise AIProviderError("empty_candidates")
    parts = candidates[0].get("content", {}).get("parts", [])
    text = "".join(part.get("text", "") for part in parts).strip()
    if not text:
        raise AIProviderError("empty_response")
    return text


def ask_openai_compatible(provider, system_prompt, user_text):
    headers = {"Authorization": f"Bearer {provider['api_key']}", "Content-Type": "application/json"}
    if provider["id"] == "openrouter":
        headers["HTTP-Referer"] = "https://t.me/"
        headers["X-Title"] = "Mouno Telegram Bot"
    payload = {
        "model": provider["model"],
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_text},
        ],
        "temperature": 0.2,
        "max_tokens": 650,
    }
    data = post_json(provider, provider["url"], headers, payload)
    text = extract_openai_text(data)
    if not text:
        raise AIProviderError("empty_response")
    return text


def ask_huggingface(provider, system_prompt, user_text):
    url = f"https://api-inference.huggingface.co/models/{provider['model']}"
    prompt = f"System instruction:\n{system_prompt}\n\n{user_text}\n\nAssistant:"
    payload = {
        "inputs": prompt,
        "parameters": {"temperature": 0.2, "max_new_tokens": 650, "return_full_text": False},
        "options": {"wait_for_model": True},
    }
    headers = {"Authorization": f"Bearer {provider['api_key']}", "Content-Type": "application/json"}
    data = post_json(provider, url, headers, payload)
    text = extract_hf_text(data)
    if text.startswith(prompt):
        text = text[len(prompt):].strip()
    if not text:
        raise AIProviderError("empty_response")
    return text


def ask_provider(provider, system_prompt, user_text):
    if provider["kind"] == "gemini":
        return ask_gemini(provider, system_prompt, user_text)
    if provider["kind"] == "huggingface":
        return ask_huggingface(provider, system_prompt, user_text)
    return ask_openai_compatible(provider, system_prompt, user_text)


def ask_ai_support_fallback(question, lang, order_context, system_prompt, logger=None):
    providers = configured_providers()
    if not providers:
        raise RuntimeError("all_ai_providers_failed")
    user_text = build_ai_user_text(question, order_context)
    for provider in providers:
        try:
            answer = ask_provider(provider, system_prompt, user_text)
            if answer.strip():
                if logger:
                    logger.info("AI support answered via provider=%s", provider["name"])
                return answer.strip()
            raise AIProviderError("empty_response")
        except Exception as exc:
            if logger:
                logger.warning("AI provider failed provider=%s error=%s", provider["name"], sanitize_ai_error(exc))
    raise RuntimeError("all_ai_providers_failed")
