"""
Honcho-based conversation memory (https://app.honcho.dev).

This module is a thin, fully defensive wrapper around the `honcho-ai` SDK.
Every public function is a no-op that returns safe empty values when:
  - the API key is not configured, or
  - the SDK is not installed, or
  - any network / SDK error occurs.

This guarantees that the website AI chat and the Telegram bot keep working
even if Honcho is unavailable (graceful degradation).

The API key is NOT hardcoded. It is read from:
  1. db.get_setting("honcho_api_key")   (set via the Telegram admin button)
  2. os.getenv("HONCHO_API_KEY")        (fallback)
"""

import os
import logging
import threading

logger = logging.getLogger(__name__)

# Short timeouts so a slow Honcho never blocks a chat reply for long.
_CLIENT_TIMEOUT = 4.0

# Workspace + assistant peer naming
_WORKSPACE_ID = "bgc"
_ASSISTANT_PEER = "assistant"

# How many recent context characters to inject at most.
_MAX_CONTEXT_CHARS = 1500

_lock = threading.Lock()
_client = None
_client_key = None  # the key the cached client was built with


def _get_api_key():
    """Resolve the Honcho API key: DB setting first, then env var."""
    try:
        import db
        val = (db.get_setting("honcho_api_key") or "").strip()
        if val:
            return val
    except Exception:
        pass
    return (os.getenv("HONCHO_API_KEY") or "").strip()


def is_configured():
    """True if an API key is available (does not verify it)."""
    return bool(_get_api_key())


def health():
    """
    Return a small diagnostic dict describing why Honcho is or isn't working.
    Safe to call from an admin endpoint. Never raises.
    Fields:
      - has_key:    an API key was found (DB setting or env var)
      - key_source: "db" | "env" | None
      - sdk_ok:     the honcho-ai SDK is importable
      - client_ok:  a client could be built with the current key
      - live_ok:    a lightweight live call to Honcho succeeded
      - error:      last error string (if any)
    """
    info = {
        "has_key": False,
        "key_source": None,
        "sdk_ok": False,
        "client_ok": False,
        "live_ok": False,
        "workspace": _WORKSPACE_ID,
        "error": None,
    }
    try:
        # Key + source
        db_key = ""
        try:
            import db
            db_key = (db.get_setting("honcho_api_key") or "").strip()
        except Exception:
            db_key = ""
        env_key = (os.getenv("HONCHO_API_KEY") or "").strip()
        if db_key:
            info["has_key"] = True
            info["key_source"] = "db"
        elif env_key:
            info["has_key"] = True
            info["key_source"] = "env"

        # SDK importable?
        try:
            from honcho import Honcho  # noqa: F401
            info["sdk_ok"] = True
        except Exception as exc:
            info["error"] = f"SDK import failed: {exc}"
            return info

        # Client buildable?
        client = _get_client()
        if client is None:
            info["error"] = info["error"] or "Client could not be built (missing/invalid key?)"
            return info
        info["client_ok"] = True

        # Lightweight live call to confirm the key actually authenticates.
        try:
            client.peer(_ASSISTANT_PEER)
            info["live_ok"] = True
        except Exception as exc:
            info["error"] = f"Live call failed: {exc}"
    except Exception as exc:
        info["error"] = f"health() crashed: {exc}"
    return info


def _get_client():
    """Lazily build (and cache) a Honcho client for the current key."""
    global _client, _client_key
    api_key = _get_api_key()
    if not api_key:
        return None

    with _lock:
        if _client is not None and _client_key == api_key:
            return _client
        try:
            from honcho import Honcho
        except Exception as exc:
            logger.warning("honcho-ai SDK not available: %s", exc)
            return None
        try:
            try:
                client = Honcho(
                    api_key=api_key,
                    environment="production",
                    workspace_id=_WORKSPACE_ID,
                    timeout=_CLIENT_TIMEOUT,
                )
            except TypeError:
                # Older/newer SDKs may not accept all kwargs.
                client = Honcho(api_key=api_key, environment="production")
            _client = client
            _client_key = api_key
            return _client
        except Exception as exc:
            logger.warning("Failed to init Honcho client: %s", exc)
            return None


def reset_client():
    """Drop the cached client (call after the key changes)."""
    global _client, _client_key
    with _lock:
        _client = None
        _client_key = None


def _get_session(client, session_key, user_peer_name):
    """Return a Honcho session that contains the user + assistant peers."""
    user_peer = client.peer(user_peer_name)
    assistant_peer = client.peer(_ASSISTANT_PEER)
    session = client.session(session_key)
    try:
        session.add_peers([user_peer, assistant_peer])
    except Exception:
        # add_peers is idempotent-ish; ignore if peers already present.
        pass
    return session, user_peer, assistant_peer


def get_memory_context(session_key, user_peer_name, query):
    """
    Return a short natural-language memory/context string about the user for
    the given session, or "" when unavailable. Never raises.
    """
    if not query:
        return ""
    client = _get_client()
    if client is None:
        return ""
    try:
        user_peer = client.peer(user_peer_name)
        # Ask Honcho what it knows about this user, scoped to the session.
        try:
            insight = user_peer.chat(query, session=session_key)
        except TypeError:
            insight = user_peer.chat(query)
        if not insight:
            return ""
        text = str(insight).strip()
        if len(text) > _MAX_CONTEXT_CHARS:
            text = text[:_MAX_CONTEXT_CHARS].rstrip() + "..."
        return text
    except Exception as exc:
        logger.warning("Honcho get_memory_context failed: %s", exc)
        return ""


def record_turn(session_key, user_peer_name, user_message, assistant_message):
    """
    Persist one user+assistant exchange into the Honcho session so future
    turns remember it. Never raises.
    """
    if not (user_message or assistant_message):
        return
    client = _get_client()
    if client is None:
        return
    try:
        session, user_peer, assistant_peer = _get_session(client, session_key, user_peer_name)
        messages = []
        if user_message:
            messages.append(user_peer.message(str(user_message)[:4000]))
        if assistant_message:
            messages.append(assistant_peer.message(str(assistant_message)[:4000]))
        if messages:
            session.add_messages(messages)
    except Exception as exc:
        logger.warning("Honcho record_turn failed: %s", exc)
