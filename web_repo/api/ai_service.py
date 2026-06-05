import logging
import requests
import os
from config import CEREBRAS_API_KEY, CEREBRAS_MODEL, SUPPORT_USERNAME
import db

logger = logging.getLogger(__name__)

def ask_ai_support(question, lang="bn", context=None):
    # Simplified version for the website
    api_key = db.get_setting("ai_cerebras_api_key") or CEREBRAS_API_KEY
    if not api_key:
        return "AI Support is currently unavailable."

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": CEREBRAS_MODEL,
        "messages": [
            {"role": "system", "content": f"You are a helpful support assistant for BGC Crypto. Support: @{SUPPORT_USERNAME}"},
            {"role": "user", "content": f"Context: {context}\n\nQuestion: {question}" if context else question},
        ],
        "temperature": 0.2,
        "max_tokens": 850,
    }
    try:
        response = requests.post("https://api.cerebras.ai/v1/chat/completions", headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        logger.error(f"AI Error: {e}")
        return "Sorry, I am having trouble connecting to my brain right now."
