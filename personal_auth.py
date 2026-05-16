import asyncio
import re
import secrets
import time

try:
    from telethon import TelegramClient
    from telethon.errors import SessionPasswordNeededError
    from telethon.sessions import StringSession
except Exception:
    TelegramClient = None
    SessionPasswordNeededError = None
    StringSession = None


PERSONAL_FORWARD_CONNECTIONS = {}
PERSONAL_AUTH_SESSIONS = {}
PERSONAL_AUTH_TTL_SECONDS = 600
PERSONAL_AUTH_MAX_ATTEMPTS = 5

_runtime_loop = None
_runtime_app = None


def set_personal_auth_runtime(loop, app):
    global _runtime_loop, _runtime_app
    _runtime_loop = loop
    _runtime_app = app


def personal_auth_available():
    return bool(TelegramClient and StringSession)


def personal_auth_display_name(me):
    username = getattr(me, "username", None)
    if username:
        return f"@{username}"
    first = getattr(me, "first_name", None) or ""
    last = getattr(me, "last_name", None) or ""
    name = f"{first} {last}".strip()
    return name or str(getattr(me, "id", "Telegram account"))


def create_personal_auth_session(user_id, lang="en"):
    cleanup_personal_auth_sessions()
    token = secrets.token_urlsafe(32)
    PERSONAL_AUTH_SESSIONS[token] = {
        "user_id": str(user_id),
        "lang": lang,
        "status": "new",
        "expires_at": time.time() + PERSONAL_AUTH_TTL_SECONDS,
        "attempts": 0,
    }
    return token


def get_personal_auth_session(token):
    session = PERSONAL_AUTH_SESSIONS.get(token)
    if not session:
        return None
    if session.get("expires_at", 0) < time.time():
        schedule_personal_auth_disconnect(token)
        PERSONAL_AUTH_SESSIONS.pop(token, None)
        return None
    return session


def cleanup_personal_auth_sessions():
    now = time.time()
    for token, session in list(PERSONAL_AUTH_SESSIONS.items()):
        if session.get("expires_at", 0) < now:
            schedule_personal_auth_disconnect(token)
            PERSONAL_AUTH_SESSIONS.pop(token, None)


def schedule_personal_auth_disconnect(token):
    session = PERSONAL_AUTH_SESSIONS.get(token)
    client = session.get("client") if session else None
    if not client:
        return
    if _runtime_loop and _runtime_loop.is_running():
        asyncio.run_coroutine_threadsafe(_disconnect_client(client), _runtime_loop)


async def _disconnect_client(client):
    try:
        await client.disconnect()
    except Exception:
        pass


def _run_on_runtime(coro_factory):
    if not _runtime_loop or not _runtime_loop.is_running():
        return False, "Telegram auth runtime is not ready. Start the bot server and try again."
    future = asyncio.run_coroutine_threadsafe(coro_factory(), _runtime_loop)
    try:
        return True, future.result(timeout=45)
    except Exception as exc:
        return False, safe_personal_auth_error(exc)


def safe_personal_auth_error(exc):
    return re.sub(r"\b\d{5,}:[A-Za-z0-9_-]+\b", "[REDACTED_TOKEN]", str(exc))[:180]


def send_personal_auth_code_sync(token, api_id, api_hash, phone):
    return _run_on_runtime(lambda: send_personal_auth_code(token, api_id, api_hash, phone))


def verify_personal_auth_code_sync(token, code):
    return _run_on_runtime(lambda: verify_personal_auth_code(token, code))


def verify_personal_auth_password_sync(token, password):
    return _run_on_runtime(lambda: verify_personal_auth_password(token, password))


async def send_personal_auth_code(token, api_id, api_hash, phone):
    session = get_personal_auth_session(token)
    if not session:
        raise RuntimeError("Auth link expired. Go back to the bot and create a new link.")
    if session.get("status") == "connected":
        raise RuntimeError("This auth link has already connected an account. Go back to the bot to create a new link.")
    if not personal_auth_available():
        raise RuntimeError("Telethon is not installed on this server.")
    try:
        api_id = int(str(api_id).strip())
        if api_id <= 0:
            raise ValueError
    except Exception:
        raise RuntimeError("Send a valid numeric Telegram API ID.")
    api_hash = str(api_hash or "").strip()
    if not re.fullmatch(r"[A-Fa-f0-9]{32}", api_hash):
        raise RuntimeError("Send the 32-character Telegram API hash from my.telegram.org.")
    phone = str(phone or "").strip().replace(" ", "")
    if not re.fullmatch(r"\+?\d{8,16}", phone):
        raise RuntimeError("Send a valid phone number with country code.")

    old_client = session.get("client")
    if old_client:
        await _disconnect_client(old_client)

    client = TelegramClient(StringSession(), api_id, api_hash)
    await client.connect()
    try:
        sent_code = await client.send_code_request(phone)
    except Exception:
        await _disconnect_client(client)
        raise
    session.update({
        "status": "code_sent",
        "api_id": str(api_id),
        "api_hash": api_hash,
        "phone": phone,
        "phone_code_hash": getattr(sent_code, "phone_code_hash", None),
        "client": client,
        "attempts": 0,
        "error": None,
    })
    return {"status": "code_sent"}


async def verify_personal_auth_code(token, code):
    session = get_personal_auth_session(token)
    if not session:
        raise RuntimeError("Auth link expired. Go back to the bot and create a new link.")
    if session.get("status") not in {"code_sent", "password_needed"}:
        raise RuntimeError("Request a Telegram login code first.")
    session["attempts"] = int(session.get("attempts") or 0) + 1
    if session["attempts"] > PERSONAL_AUTH_MAX_ATTEMPTS:
        raise RuntimeError("Too many attempts. Go back to the bot and create a new link.")
    client = session.get("client")
    if not client:
        raise RuntimeError("Login session expired. Go back to the bot and create a new link.")
    code = re.sub(r"\D", "", str(code or ""))
    if not code:
        raise RuntimeError("Enter the numeric Telegram login code.")
    try:
        await client.sign_in(session.get("phone"), code=code, phone_code_hash=session.get("phone_code_hash"))
    except Exception as exc:
        if SessionPasswordNeededError and isinstance(exc, SessionPasswordNeededError):
            session["status"] = "password_needed"
            return {"status": "password_needed"}
        raise
    return await _complete_personal_auth(token, session, client)


async def verify_personal_auth_password(token, password):
    session = get_personal_auth_session(token)
    if not session:
        raise RuntimeError("Auth link expired. Go back to the bot and create a new link.")
    if session.get("status") != "password_needed":
        raise RuntimeError("Two-step verification password is not required for this login.")
    client = session.get("client")
    if not client:
        raise RuntimeError("Login session expired. Go back to the bot and create a new link.")
    await client.sign_in(password=str(password or "").strip())
    return await _complete_personal_auth(token, session, client)


async def _complete_personal_auth(token, session, client):
    me = await client.get_me()
    connection = {
        "session": client.session.save(),
        "api_id": str(session.get("api_id") or ""),
        "api_hash": session.get("api_hash") or "",
        "display_name": personal_auth_display_name(me),
        "account_id": str(getattr(me, "id", "")),
    }
    PERSONAL_FORWARD_CONNECTIONS[str(session.get("user_id"))] = connection
    await _disconnect_client(client)
    session["client"] = None
    session["status"] = "connected"
    session["display_name"] = connection["display_name"]
    if _runtime_app:
        try:
            await _runtime_app.bot.send_message(
                chat_id=int(session.get("user_id")),
                text=f"✅ Personal account connected: {connection['display_name']}\n\nReturn to Telegram Message Forwarder and choose forwarding type.",
            )
        except Exception:
            pass
    return {"status": "connected", "display_name": connection["display_name"]}
