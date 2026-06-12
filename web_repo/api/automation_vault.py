"""
Web-only auto-sign password vault.

The web Automation experience collects the user's Personal Wallet password ONCE
during setup (instead of asking on every limit-order / scheduled-buy creation
like the Telegram bot does). The password is sealed with the server master key
(SELLER_WALLET_MASTER_KEY, via automation_service.seal_password) and stored so
later creations can re-seal it into each limit_orders / scheduled_buys row that
the shared bot monitors execute.

This lives outside automation_service.py on purpose: automation_service.py is the
shared module imported by the Telegram bot and must stay schema-compatible with
it. This extra table is web-specific and never touched by the bot, so the bot's
limit_order_monitor / scheduled_buy_runner keep working unchanged.

Raw passwords are NEVER stored in plaintext and NEVER returned to clients.
"""

import sqlite3
from contextlib import closing

from automation_service import seal_password, open_password
from db import DB_PATH


def init_automation_vault():
    with closing(sqlite3.connect(DB_PATH)) as con:
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS automation_auth (
                user_id TEXT PRIMARY KEY,
                enc_password TEXT NOT NULL,
                pw_salt TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        con.commit()


def store_auto_password(user_id, password):
    """Seal and persist the user's wallet password for future auto-sign triggers."""
    enc_password, pw_salt = seal_password(password)
    with closing(sqlite3.connect(DB_PATH)) as con:
        con.execute(
            """
            INSERT INTO automation_auth (user_id, enc_password, pw_salt, updated_at)
            VALUES (?,?,?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id) DO UPDATE SET
                enc_password=excluded.enc_password,
                pw_salt=excluded.pw_salt,
                updated_at=CURRENT_TIMESTAMP
            """,
            (str(user_id), enc_password, pw_salt),
        )
        con.commit()


def has_auto_password(user_id):
    with closing(sqlite3.connect(DB_PATH)) as con:
        row = con.execute(
            "SELECT 1 FROM automation_auth WHERE user_id=?", (str(user_id),)
        ).fetchone()
        return row is not None


def get_auto_password(user_id):
    """Return the decrypted wallet password, or None if not configured."""
    with closing(sqlite3.connect(DB_PATH)) as con:
        row = con.execute(
            "SELECT enc_password, pw_salt FROM automation_auth WHERE user_id=?",
            (str(user_id),),
        ).fetchone()
    if not row:
        return None
    try:
        return open_password(row[0], row[1])
    except Exception:
        return None


def clear_auto_password(user_id):
    with closing(sqlite3.connect(DB_PATH)) as con:
        con.execute("DELETE FROM automation_auth WHERE user_id=?", (str(user_id),))
        con.commit()
