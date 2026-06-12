"""Best-effort webhook notifications (Telegram / Discord).

This module sends notifications about important events (transactions,
giveaways, referral bonuses, support tickets) to configured chat/webhook
endpoints. Every send is wrapped so that a missing credential or a network
failure never crashes the request that triggered it.

Credential resolution intentionally reuses the bot's existing Telegram
credentials (``BOT_TOKEN`` + ``ADMIN_ID``) that already live in config, so we
don't duplicate bot tokens. Dedicated overrides may be supplied via
``TELEGRAM_BOT_TOKEN`` / ``TELEGRAM_CHAT_ID`` and ``DISCORD_WEBHOOK_URL``.
"""

import logging
import threading

import requests

import config

logger = logging.getLogger(__name__)

# Keep this conservative: notifications are best-effort and run off the
# request thread, but a tight timeout still bounds resource use.
_TIMEOUT = 5

# Event -> channels mapping. Toggle channels per event here without touching
# call sites. Supported channels: "telegram", "discord".
EVENT_CHANNELS = {
    "transaction": ["telegram", "discord"],
    "giveaway_result": ["telegram", "discord"],
    "referral_bonus": ["telegram", "discord"],
    "ticket_created": ["telegram", "discord"],
}


def _telegram_token():
    return getattr(config, "TELEGRAM_BOT_TOKEN", None) or getattr(config, "BOT_TOKEN", None)


def _telegram_chat_id():
    return getattr(config, "TELEGRAM_CHAT_ID", None) or getattr(config, "ADMIN_ID", None)


def send_telegram(message, chat_id=None):
    """POST a message to Telegram. No-ops (with a warning) if unconfigured."""
    token = _telegram_token()
    target = chat_id or _telegram_chat_id()
    if not token or not target:
        logger.warning("Telegram notification skipped: missing token or chat id.")
        return False
    try:
        requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": target, "text": message},
            timeout=_TIMEOUT,
        )
        return True
    except Exception as exc:
        logger.warning("Telegram notification failed: %s", exc)
        return False


def send_discord(message, webhook_url=None):
    """POST a message to a Discord webhook. No-ops if unconfigured."""
    url = webhook_url or getattr(config, "DISCORD_WEBHOOK_URL", None)
    if not url:
        logger.warning("Discord notification skipped: missing webhook url.")
        return False
    try:
        requests.post(url, json={"content": message}, timeout=_TIMEOUT)
        return True
    except Exception as exc:
        logger.warning("Discord notification failed: %s", exc)
        return False


def _dispatch(event_type, message):
    """Synchronously fan a message out to every enabled channel."""
    channels = EVENT_CHANNELS.get(event_type, [])
    for channel in channels:
        try:
            if channel == "telegram":
                send_telegram(message)
            elif channel == "discord":
                send_discord(message)
        except Exception as exc:  # defensive; senders already swallow errors
            logger.warning("notify_event(%s) channel %s failed: %s", event_type, channel, exc)


def notify_event(event_type, message):
    """Fan a message out to every channel enabled for ``event_type``.

    Best-effort and **non-blocking**: the actual HTTP sends run on a daemon
    thread so a slow or unreachable endpoint never adds latency to the
    user-facing request that triggered the notification. Individual channel
    failures are swallowed so the caller is never affected.
    """
    if not EVENT_CHANNELS.get(event_type):
        return
    try:
        thread = threading.Thread(
            target=_dispatch,
            args=(event_type, message),
            name=f"notify-{event_type}",
            daemon=True,
        )
        thread.start()
    except Exception as exc:  # spawning a thread should never break the caller
        logger.warning("notify_event(%s) could not start thread: %s", event_type, exc)
