"""
Automation service for Buy/Swap experience.

Provides storage + helpers for two automated features:
  * Limit Orders   - execute a swap/buy when a watched token hits a target USD price.
  * Scheduled Buys - recurring/auto-buy on a fixed interval (daily/weekly/monthly).

Both features rely on "full auto-sign": the user supplies their Personal Wallet
password once during setup. We never store it in plaintext - it is encrypted with
the server-side master key (SELLER_WALLET_MASTER_KEY) and decrypted only at the
moment the bot needs to sign a triggered transaction.

This module is intentionally Telegram-agnostic. The actual transaction signing /
broadcasting executor lives in bot.py (where all wallet + chain helpers exist).
"""

import sqlite3
from contextlib import closing
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation

from crypto_manager import encrypt_seller_key, decrypt_seller_key
from db import DB_PATH, gen_order_id


INTERVAL_SECONDS = {
    "daily": 24 * 60 * 60,
    "weekly": 7 * 24 * 60 * 60,
    "monthly": 30 * 24 * 60 * 60,
}

LIMIT_DIRECTIONS = {"below", "above"}


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------
def init_automation_tables():
    with closing(sqlite3.connect(DB_PATH)) as con:
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS limit_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id TEXT UNIQUE,
                user_id TEXT NOT NULL,
                from_chain_id TEXT,
                from_chain_name TEXT,
                from_token TEXT,
                to_chain_id TEXT,
                to_chain_name TEXT,
                to_token TEXT,
                amount TEXT,
                preference TEXT DEFAULT 'cheapest',
                watch_symbol TEXT,
                direction TEXT,
                target_price TEXT,
                enc_password TEXT,
                pw_salt TEXT,
                status TEXT DEFAULT 'active',
                last_price TEXT,
                tx_hash TEXT,
                error TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                triggered_at TIMESTAMP
            )
            """
        )
        con.execute("CREATE INDEX IF NOT EXISTS idx_limit_orders_user ON limit_orders(user_id)")
        con.execute("CREATE INDEX IF NOT EXISTS idx_limit_orders_status ON limit_orders(status)")
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS scheduled_buys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                schedule_id TEXT UNIQUE,
                user_id TEXT NOT NULL,
                from_chain_id TEXT,
                from_chain_name TEXT,
                from_token TEXT,
                to_chain_id TEXT,
                to_chain_name TEXT,
                to_token TEXT,
                amount TEXT,
                preference TEXT DEFAULT 'cheapest',
                interval_key TEXT,
                enc_password TEXT,
                pw_salt TEXT,
                status TEXT DEFAULT 'active',
                runs_count INTEGER DEFAULT 0,
                last_tx_hash TEXT,
                last_error TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                next_run TIMESTAMP,
                last_run TIMESTAMP
            )
            """
        )
        con.execute("CREATE INDEX IF NOT EXISTS idx_scheduled_buys_user ON scheduled_buys(user_id)")
        con.execute("CREATE INDEX IF NOT EXISTS idx_scheduled_buys_status ON scheduled_buys(status)")
        con.commit()


# ---------------------------------------------------------------------------
# Password vault helpers (encrypted with the server master key)
# ---------------------------------------------------------------------------
def seal_password(password):
    """Encrypt the user's wallet password with the server master key."""
    enc, salt = encrypt_seller_key(password)
    return enc, salt


def open_password(enc_password, pw_salt):
    """Decrypt a sealed wallet password. Raises on tamper/missing master key."""
    return decrypt_seller_key(enc_password, pw_salt)


# ---------------------------------------------------------------------------
# Limit orders
# ---------------------------------------------------------------------------
def create_limit_order(user_id, intent, watch_symbol, direction, target_price, password):
    direction = str(direction).lower()
    if direction not in LIMIT_DIRECTIONS:
        raise ValueError("direction must be 'below' or 'above'")
    enc_password, pw_salt = seal_password(password)
    order_id = gen_order_id("LMT")
    with closing(sqlite3.connect(DB_PATH)) as con:
        con.execute(
            """
            INSERT INTO limit_orders (
                order_id, user_id, from_chain_id, from_chain_name, from_token,
                to_chain_id, to_chain_name, to_token, amount, preference,
                watch_symbol, direction, target_price, enc_password, pw_salt, status
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?, 'active')
            """,
            (
                order_id, str(user_id),
                str(intent.get("from_chain_id")), intent.get("from_chain_name"), intent.get("from_token"),
                str(intent.get("to_chain_id")), intent.get("to_chain_name"), intent.get("to_token"),
                str(intent.get("amount")), intent.get("preference") or "cheapest",
                watch_symbol, direction, str(target_price), enc_password, pw_salt,
            ),
        )
        con.commit()
    return order_id


def list_limit_orders(user_id, statuses=("active",)):
    placeholders = ",".join("?" for _ in statuses)
    with closing(sqlite3.connect(DB_PATH)) as con:
        con.row_factory = sqlite3.Row
        return con.execute(
            f"SELECT * FROM limit_orders WHERE user_id=? AND status IN ({placeholders}) ORDER BY id DESC",
            (str(user_id), *statuses),
        ).fetchall()


def get_active_limit_orders():
    with closing(sqlite3.connect(DB_PATH)) as con:
        con.row_factory = sqlite3.Row
        return con.execute("SELECT * FROM limit_orders WHERE status='active' ORDER BY id ASC").fetchall()


def get_limit_order(order_id, user_id=None):
    with closing(sqlite3.connect(DB_PATH)) as con:
        con.row_factory = sqlite3.Row
        if user_id is not None:
            return con.execute(
                "SELECT * FROM limit_orders WHERE order_id=? AND user_id=?", (order_id, str(user_id))
            ).fetchone()
        return con.execute("SELECT * FROM limit_orders WHERE order_id=?", (order_id,)).fetchone()


def update_limit_price(order_id, last_price):
    with closing(sqlite3.connect(DB_PATH)) as con:
        con.execute("UPDATE limit_orders SET last_price=? WHERE order_id=?", (str(last_price), order_id))
        con.commit()


def mark_limit_order(order_id, status, tx_hash=None, error=None):
    with closing(sqlite3.connect(DB_PATH)) as con:
        con.execute(
            "UPDATE limit_orders SET status=?, tx_hash=COALESCE(?, tx_hash), error=?, triggered_at=CURRENT_TIMESTAMP WHERE order_id=?",
            (status, tx_hash, error, order_id),
        )
        con.commit()


def cancel_limit_order(order_id, user_id):
    with closing(sqlite3.connect(DB_PATH)) as con:
        cur = con.execute(
            "UPDATE limit_orders SET status='cancelled', enc_password='', pw_salt='' WHERE order_id=? AND user_id=? AND status='active'",
            (order_id, str(user_id)),
        )
        con.commit()
        return cur.rowcount > 0


def limit_should_trigger(direction, target_price, current_price):
    try:
        target = Decimal(str(target_price))
        current = Decimal(str(current_price))
    except (InvalidOperation, ValueError):
        return False
    if direction == "below":
        return current <= target
    if direction == "above":
        return current >= target
    return False


# ---------------------------------------------------------------------------
# Scheduled buys
# ---------------------------------------------------------------------------
def _next_run_from(interval_key, start=None):
    start = start or datetime.utcnow()
    seconds = INTERVAL_SECONDS.get(interval_key, INTERVAL_SECONDS["weekly"])
    return start + timedelta(seconds=seconds)


def create_scheduled_buy(user_id, intent, interval_key, password):
    interval_key = str(interval_key).lower()
    if interval_key not in INTERVAL_SECONDS:
        raise ValueError("interval must be daily, weekly, or monthly")
    enc_password, pw_salt = seal_password(password)
    schedule_id = gen_order_id("SCH")
    next_run = _next_run_from(interval_key)
    with closing(sqlite3.connect(DB_PATH)) as con:
        con.execute(
            """
            INSERT INTO scheduled_buys (
                schedule_id, user_id, from_chain_id, from_chain_name, from_token,
                to_chain_id, to_chain_name, to_token, amount, preference,
                interval_key, enc_password, pw_salt, status, next_run
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?, 'active', ?)
            """,
            (
                schedule_id, str(user_id),
                str(intent.get("from_chain_id")), intent.get("from_chain_name"), intent.get("from_token"),
                str(intent.get("to_chain_id")), intent.get("to_chain_name"), intent.get("to_token"),
                str(intent.get("amount")), intent.get("preference") or "cheapest",
                interval_key, enc_password, pw_salt, next_run.isoformat(),
            ),
        )
        con.commit()
    return schedule_id


def list_scheduled_buys(user_id, statuses=("active", "paused")):
    placeholders = ",".join("?" for _ in statuses)
    with closing(sqlite3.connect(DB_PATH)) as con:
        con.row_factory = sqlite3.Row
        return con.execute(
            f"SELECT * FROM scheduled_buys WHERE user_id=? AND status IN ({placeholders}) ORDER BY id DESC",
            (str(user_id), *statuses),
        ).fetchall()


def get_due_scheduled_buys(now=None):
    now = now or datetime.utcnow()
    with closing(sqlite3.connect(DB_PATH)) as con:
        con.row_factory = sqlite3.Row
        return con.execute(
            "SELECT * FROM scheduled_buys WHERE status='active' AND next_run IS NOT NULL AND next_run <= ? ORDER BY id ASC",
            (now.isoformat(),),
        ).fetchall()


def get_scheduled_buy(schedule_id, user_id=None):
    with closing(sqlite3.connect(DB_PATH)) as con:
        con.row_factory = sqlite3.Row
        if user_id is not None:
            return con.execute(
                "SELECT * FROM scheduled_buys WHERE schedule_id=? AND user_id=?", (schedule_id, str(user_id))
            ).fetchone()
        return con.execute("SELECT * FROM scheduled_buys WHERE schedule_id=?", (schedule_id,)).fetchone()


def record_scheduled_run(schedule_id, interval_key, tx_hash=None, error=None):
    next_run = _next_run_from(interval_key)
    with closing(sqlite3.connect(DB_PATH)) as con:
        con.execute(
            """
            UPDATE scheduled_buys
            SET runs_count = runs_count + 1,
                last_tx_hash = COALESCE(?, last_tx_hash),
                last_error = ?,
                last_run = CURRENT_TIMESTAMP,
                next_run = ?
            WHERE schedule_id = ?
            """,
            (tx_hash, error, next_run.isoformat(), schedule_id),
        )
        con.commit()


def set_scheduled_status(schedule_id, user_id, status):
    if status not in {"active", "paused", "cancelled"}:
        raise ValueError("invalid status")
    with closing(sqlite3.connect(DB_PATH)) as con:
        if status == "active":
            # Re-arm the next run when resuming.
            next_run = _next_run_from("daily").isoformat()
            cur = con.execute(
                "UPDATE scheduled_buys SET status='active', next_run=? WHERE schedule_id=? AND user_id=?",
                (next_run, schedule_id, str(user_id)),
            )
        elif status == "cancelled":
            cur = con.execute(
                "UPDATE scheduled_buys SET status='cancelled', enc_password='', pw_salt='' WHERE schedule_id=? AND user_id=?",
                (schedule_id, str(user_id)),
            )
        else:
            cur = con.execute(
                "UPDATE scheduled_buys SET status=? WHERE schedule_id=? AND user_id=?",
                (status, schedule_id, str(user_id)),
            )
        con.commit()
        return cur.rowcount > 0
