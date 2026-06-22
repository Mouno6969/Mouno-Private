"""Personal-account Telegram forwarding for the website.

Ports the Telethon personal-account forwarding helpers from the bot (bot.py)
into the web process. A "connection" is a plain dict with the keys produced by
personal_auth._complete_personal_auth:
    {session, api_id, api_hash, display_name, account_id}

app.py is responsible for decrypting the stored credentials into that dict and
for all DB/crypto access; this module only talks to Telegram and manages the
in-process scheduled-forward tasks on the shared tg_runtime loop.
"""

import asyncio
import re
import secrets

import db
import tg_runtime

try:
    from telethon import TelegramClient
    from telethon import utils as telethon_utils
    from telethon.errors import FloodWaitError
    from telethon.sessions import StringSession
except Exception:  # pragma: no cover - telethon always present in prod venv
    TelegramClient = None
    telethon_utils = None
    FloodWaitError = None
    StringSession = None

# Guard rails mirror the bot's personal-account limits.
MAX_TARGETS = 45
MIN_INTERVAL_MINUTES = 15
TARGET_DELAY_SECONDS = 3
DIALOG_FETCH_LIMIT = 200

# schedule_id -> asyncio.Task (lives on the tg_runtime loop)
_SCHEDULED = {}


def available():
    return bool(TelegramClient and StringSession)


def safe_error(exc):
    """Strip anything that looks like a bot token / api credential from errors."""
    return re.sub(r"\b\d{5,}:[A-Za-z0-9_-]+\b", "[REDACTED]", str(exc))[:160]


# ── Target parsing (mirrors bot.normalize_free_forward_target) ────────────────

def normalize_target(value):
    raw = (value or "").strip().strip(",")
    if not raw:
        return None
    raw = raw.split("?", 1)[0].rstrip("/")
    match = re.match(r"^(?:https?://)?(?:www\.)?(?:t\.me|telegram\.me)/(.+)$", raw, re.IGNORECASE)
    if match:
        path = match.group(1).strip("/")
        if path.startswith("+") or path.lower().startswith("joinchat/") or path.startswith("c/"):
            return None
        raw = path.split("/", 1)[0]
    if re.fullmatch(r"-?\d+", raw):
        return raw
    raw = raw.lstrip("@")
    if re.fullmatch(r"[A-Za-z0-9_]{5,32}", raw):
        return f"@{raw}"
    return None


def parse_targets(values, max_targets=MAX_TARGETS):
    """Accepts a list of strings (or a single whitespace/comma string) and
    returns (valid_targets, invalid_inputs)."""
    if isinstance(values, str):
        values = re.split(r"[\s,]+", values)
    targets = []
    invalid = []
    for value in values or []:
        if not str(value).strip():
            continue
        target = normalize_target(str(value))
        if not target:
            invalid.append(str(value).strip())
            continue
        if target not in targets:
            targets.append(target)
    return targets[:max_targets], invalid


# ── Telethon client + operations ──────────────────────────────────────────────

async def _client(connection):
    client = TelegramClient(
        StringSession(connection.get("session") or ""),
        int(connection.get("api_id")),
        connection.get("api_hash") or "",
    )
    await client.connect()
    return client


def _peer_id(entity):
    if telethon_utils:
        return str(telethon_utils.get_peer_id(entity))
    return str(getattr(entity, "id", ""))


async def _list_dialogs(connection, limit=DIALOG_FETCH_LIMIT):
    dialogs = []
    client = await _client(connection)
    try:
        if not await client.is_user_authorized():
            raise RuntimeError("personal account session expired")
        async for dialog in client.iter_dialogs(limit=limit):
            if not (getattr(dialog, "is_group", False) or getattr(dialog, "is_channel", False)):
                continue
            entity = getattr(dialog, "entity", None)
            if not entity:
                continue
            peer_id = _peer_id(entity)
            if not peer_id:
                continue
            username = getattr(entity, "username", None)
            title = getattr(dialog, "title", None) or getattr(entity, "title", None) or username or peer_id
            dialogs.append({
                "id": peer_id,
                "title": title,
                "username": username,
                "type": "channel" if getattr(dialog, "is_channel", False) else "group",
            })
    finally:
        await client.disconnect()
    return dialogs


async def _send_text(client, target, text):
    entity_target = int(target) if re.fullmatch(r"-?\d+", str(target)) else target
    entity = await client.get_entity(entity_target)
    await client.send_message(entity, text or "")


async def _send_to_targets(connection, targets, text):
    ok = []
    failed = []
    client = await _client(connection)
    try:
        if not await client.is_user_authorized():
            raise RuntimeError("personal account session expired")
        for target in targets:
            try:
                await _send_text(client, target, text)
                ok.append(target)
                await asyncio.sleep(TARGET_DELAY_SECONDS)
            except Exception as exc:
                if FloodWaitError and isinstance(exc, FloodWaitError):
                    failed.append((target, f"Telegram rate limit: wait {getattr(exc, 'seconds', 'some')} seconds"))
                    break
                failed.append((target, safe_error(exc)))
    finally:
        await client.disconnect()
    return ok, failed


def _result_text(ok, failed):
    parts = [f"Sent: {len(ok)}"]
    if failed:
        parts.append("Failed: " + "; ".join(f"{t}: {e}" for t, e in failed[:5]))
    return " | ".join(parts)


# ── Synchronous entry points (called from Flask handlers) ─────────────────────

def list_dialogs(connection):
    return tg_runtime.run_coro(_list_dialogs(connection), timeout=90)


def send_now(connection, targets, text):
    ok, failed = tg_runtime.run_coro(_send_to_targets(connection, targets, text), timeout=300)
    return {
        "sent": len(ok),
        "failed": [{"target": t, "error": e} for t, e in failed],
        "summary": _result_text(ok, failed),
    }


def check_authorized(connection):
    """Best-effort: confirm the stored session can still act as the account."""
    async def _check():
        client = await _client(connection)
        try:
            return await client.is_user_authorized()
        finally:
            await client.disconnect()
    try:
        return bool(tg_runtime.run_coro(_check(), timeout=45))
    except Exception:
        return False


# ── Scheduled forwarding ──────────────────────────────────────────────────────

def new_schedule_id():
    return "FWD-" + secrets.token_hex(5)


async def _schedule_loop(schedule_id, web_user_id, connection, targets, text, interval_minutes):
    try:
        while True:
            ok, failed = await _send_to_targets(connection, targets, text)
            db.update_tg_forward_schedule_run(schedule_id, _result_text(ok, failed))
            await asyncio.sleep(float(interval_minutes) * 60)
    except asyncio.CancelledError:
        raise
    except Exception as exc:
        db.update_tg_forward_schedule_run(schedule_id, f"stopped: {safe_error(exc)}")
        db.stop_tg_forward_schedule(schedule_id, web_user_id)
    finally:
        _SCHEDULED.pop(schedule_id, None)


def start_schedule(schedule_id, web_user_id, connection, targets, text, interval_minutes):
    """Create the long-running forward task on the shared runtime loop."""
    loop = tg_runtime.get_loop()

    def _create():
        task = loop.create_task(
            _schedule_loop(schedule_id, str(web_user_id), connection, targets, text, interval_minutes)
        )
        _SCHEDULED[schedule_id] = task

    loop.call_soon_threadsafe(_create)


def cancel_schedule(schedule_id):
    """Cancel a running task if present. Returns True if a live task was found."""
    task = _SCHEDULED.get(schedule_id)
    if not task:
        return False
    loop = tg_runtime.get_loop()
    loop.call_soon_threadsafe(task.cancel)
    _SCHEDULED.pop(schedule_id, None)
    return True


def resume_all(load_connection):
    """Restart loops for every active schedule after a process restart.

    load_connection(web_user_id) -> connection dict or None. Schedules whose
    account can no longer be loaded/decrypted are marked stopped.
    """
    for sched in db.list_active_tg_forward_schedules():
        sid = sched["schedule_id"]
        if sid in _SCHEDULED:
            continue
        web_user_id = sched["web_user_id"]
        try:
            connection = load_connection(web_user_id)
        except Exception:
            connection = None
        if not connection:
            db.update_tg_forward_schedule_run(sid, "stopped: account no longer connected")
            db.stop_tg_forward_schedule(sid, web_user_id)
            continue
        import json
        try:
            targets = json.loads(sched["targets"])
        except Exception:
            targets = []
        if not targets:
            db.stop_tg_forward_schedule(sid, web_user_id)
            continue
        start_schedule(sid, web_user_id, connection, targets, sched["message"], sched["interval_minutes"])
