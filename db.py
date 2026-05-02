import os
import sqlite3
import secrets
import string
from contextlib import closing

DB_PATH = os.path.join(os.path.dirname(__file__), "mouno.db")


def connect():
    return sqlite3.connect(DB_PATH)


def gen_order_id(prefix="ORD"):
    chars = string.ascii_uppercase + string.digits
    suffix = "".join(secrets.choice(chars) for _ in range(6))
    return f"{prefix}-{suffix}"


def ensure_column(con, table, column, definition):
    columns = [row[1] for row in con.execute(f"PRAGMA table_info({table})").fetchall()]
    if column not in columns:
        con.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def init_db():
    with closing(connect()) as con:
        cur = con.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS wallets (
                user_id TEXT PRIMARY KEY,
                wallet TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS sms_log (
                trx_id TEXT PRIMARY KEY,
                amount_bdt REAL,
                sender TEXT,
                raw_sms TEXT,
                used INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                trx_id TEXT PRIMARY KEY,
                order_id TEXT,
                user_id TEXT,
                amount_bdt REAL,
                amount_usdc REAL,
                wallet TEXT,
                sig TEXT,
                status TEXT,
                network TEXT DEFAULT 'solana',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS gift_codes (
                code TEXT PRIMARY KEY,
                amount_usdc REAL,
                amount REAL,
                network TEXT DEFAULT 'solana',
                expires_at TEXT,
                used INTEGER DEFAULT 0,
                used_by TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS network_rates (
                network TEXT PRIMARY KEY,
                rate REAL
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS pending_orders (
                trx_id TEXT PRIMARY KEY,
                user_id TEXT,
                amount_bdt REAL,
                amount_usdc REAL,
                wallet TEXT,
                network TEXT,
                order_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS app_settings (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS user_preferences (
                user_id TEXT PRIMARY KEY,
                language TEXT DEFAULT 'bn',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS star_orders (
                order_id TEXT PRIMARY KEY,
                user_id TEXT,
                username TEXT,
                network TEXT,
                wallet TEXT,
                amount_crypto REAL,
                stars_amount INTEGER,
                status TEXT DEFAULT 'pending',
                telegram_payment_charge_id TEXT,
                provider_payment_charge_id TEXT,
                tx_sig TEXT,
                error TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS sellers (
                seller_id TEXT PRIMARY KEY,
                username TEXT,
                display_name TEXT,
                bkash_number TEXT,
                support_contact TEXT,
                status TEXT DEFAULT 'pending',
                sms_token TEXT UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS seller_wallets (
                seller_id TEXT,
                network TEXT,
                encrypted_key TEXT,
                salt TEXT,
                wallet_address TEXT,
                enabled INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (seller_id, network)
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS seller_rates (
                seller_id TEXT,
                network TEXT,
                rate REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (seller_id, network)
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS seller_payment_notices (
                seller_id TEXT,
                trx_id TEXT,
                amount_bdt REAL,
                sender TEXT,
                source TEXT,
                raw_notice TEXT,
                used INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (seller_id, trx_id)
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS seller_orders (
                order_id TEXT PRIMARY KEY,
                seller_id TEXT,
                buyer_id TEXT,
                buyer_username TEXT,
                payment_method TEXT,
                trx_id TEXT,
                network TEXT,
                wallet TEXT,
                amount_bdt REAL,
                amount_crypto REAL,
                stars_amount INTEGER,
                status TEXT,
                tx_sig TEXT,
                error TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS seller_star_ledger (
                ledger_id TEXT PRIMARY KEY,
                seller_id TEXT,
                order_id TEXT,
                stars_amount INTEGER,
                status TEXT DEFAULT 'pending_payout',
                admin_note TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        ensure_column(con, "transactions", "network", "TEXT DEFAULT 'solana'")
        ensure_column(con, "transactions", "order_id", "TEXT")
        ensure_column(con, "gift_codes", "network", "TEXT DEFAULT 'solana'")
        ensure_column(con, "gift_codes", "amount", "REAL")
        ensure_column(con, "pending_orders", "order_id", "TEXT")
        con.commit()


def save_wallet(user_id, wallet):
    with closing(connect()) as con:
        con.execute("INSERT OR REPLACE INTO wallets (user_id, wallet) VALUES (?, ?)", (user_id, wallet))
        con.commit()


def get_wallet(user_id):
    with closing(connect()) as con:
        row = con.execute("SELECT wallet FROM wallets WHERE user_id=?", (user_id,)).fetchone()
        return row[0] if row else None


def save_sms(trx_id, amount_bdt, sender, raw_sms):
    with closing(connect()) as con:
        cur = con.execute(
            "INSERT OR IGNORE INTO sms_log (trx_id, amount_bdt, sender, raw_sms) VALUES (?, ?, ?, ?)",
            (trx_id, amount_bdt, sender, raw_sms),
        )
        con.commit()
        return cur.rowcount > 0


def get_sms(trx_id):
    with closing(connect()) as con:
        return con.execute("SELECT * FROM sms_log WHERE trx_id=? AND used=0", (trx_id,)).fetchone()


def sms_exists(trx_id):
    with closing(connect()) as con:
        row = con.execute("SELECT 1 FROM sms_log WHERE trx_id=?", (trx_id,)).fetchone()
        return row is not None


def mark_sms_used(trx_id):
    with closing(connect()) as con:
        con.execute("UPDATE sms_log SET used=1 WHERE trx_id=?", (trx_id,))
        con.commit()


def save_transaction(trx_id, user_id, amount_bdt, amount_usdc, wallet, sig, status, network="solana", order_id=None):
    order_id = order_id or gen_order_id()
    with closing(connect()) as con:
        con.execute(
            """
            INSERT INTO transactions
            (trx_id, order_id, user_id, amount_bdt, amount_usdc, wallet, sig, status, network)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(trx_id) DO UPDATE SET
                order_id=COALESCE(transactions.order_id, excluded.order_id),
                user_id=excluded.user_id,
                amount_bdt=excluded.amount_bdt,
                amount_usdc=excluded.amount_usdc,
                wallet=excluded.wallet,
                sig=excluded.sig,
                status=excluded.status,
                network=excluded.network,
                created_at=CURRENT_TIMESTAMP
            """,
            (trx_id, order_id, user_id, amount_bdt, amount_usdc, wallet, sig, status, network),
        )
        con.commit()
        return order_id


def update_transaction(trx_id, sig=None, status=None):
    with closing(connect()) as con:
        if sig is not None and status is not None:
            con.execute("UPDATE transactions SET sig=?, status=?, created_at=CURRENT_TIMESTAMP WHERE trx_id=?", (sig, status, trx_id))
        elif sig is not None:
            con.execute("UPDATE transactions SET sig=?, created_at=CURRENT_TIMESTAMP WHERE trx_id=?", (sig, trx_id))
        elif status is not None:
            con.execute("UPDATE transactions SET status=?, created_at=CURRENT_TIMESTAMP WHERE trx_id=?", (status, trx_id))
        con.commit()


def trx_exists(trx_id):
    with closing(connect()) as con:
        row = con.execute("SELECT 1 FROM transactions WHERE trx_id=?", (trx_id,)).fetchone()
        return row is not None


def get_recent_transactions(limit=10):
    with closing(connect()) as con:
        return con.execute(
            """
            SELECT trx_id, amount_bdt, amount_usdc, network, wallet, status, created_at, order_id
            FROM transactions
            ORDER BY datetime(created_at) DESC, rowid DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()


def get_transaction(trx_id):
    with closing(connect()) as con:
        return con.execute(
            """
            SELECT trx_id, amount_bdt, amount_usdc, network, wallet, status, created_at, order_id, user_id, sig
            FROM transactions WHERE trx_id=?
            """,
            (trx_id,),
        ).fetchone()


def get_user_recent_transactions(user_id, limit=5):
    with closing(connect()) as con:
        return con.execute(
            """
            SELECT trx_id, amount_bdt, amount_usdc, network, wallet, status, created_at, order_id, user_id, sig
            FROM transactions
            WHERE user_id=?
            ORDER BY datetime(created_at) DESC, rowid DESC
            LIMIT ?
            """,
            (str(user_id), limit),
        ).fetchall()


def get_failed_transactions(limit=10):
    with closing(connect()) as con:
        return con.execute(
            """
            SELECT trx_id, amount_bdt, amount_usdc, network, wallet, status, created_at, order_id, user_id, sig
            FROM transactions
            WHERE status='failed'
            ORDER BY datetime(created_at) DESC, rowid DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()


def get_transaction_stats():
    with closing(connect()) as con:
        return con.execute(
            """
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN status='completed' THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN status='failed' THEN 1 ELSE 0 END) as failed,
                COALESCE(SUM(CASE WHEN status='completed' THEN amount_bdt ELSE 0 END), 0) as total_bdt,
                COALESCE(SUM(CASE WHEN status='completed' THEN amount_usdc ELSE 0 END), 0) as total_crypto
            FROM transactions
            """
        ).fetchone()


def create_code(code, amount_usdc, expires_at, network="solana"):
    with closing(connect()) as con:
        con.execute(
            """
            INSERT OR REPLACE INTO gift_codes (code, amount_usdc, amount, expires_at, network)
            VALUES (?, ?, ?, ?, ?)
            """,
            (code, amount_usdc, amount_usdc, expires_at, network),
        )
        con.commit()


def get_code(code):
    with closing(connect()) as con:
        return con.execute(
            "SELECT code, amount_usdc, expires_at, used, used_by, created_at, network FROM gift_codes WHERE code=?",
            (code,),
        ).fetchone()


def use_code(code, user_id):
    with closing(connect()) as con:
        con.execute("UPDATE gift_codes SET used=1, used_by=? WHERE code=?", (user_id, code))
        con.commit()


def disable_code(code):
    with closing(connect()) as con:
        con.execute("UPDATE gift_codes SET used=1 WHERE code=?", (code,))
        con.commit()


def get_all_active_codes():
    with closing(connect()) as con:
        return con.execute(
            """
            SELECT code, COALESCE(amount, amount_usdc), network, expires_at
            FROM gift_codes
            WHERE used=0 AND datetime(expires_at) > datetime('now')
            ORDER BY created_at DESC
            """
        ).fetchall()


def get_network_rate(network):
    with closing(connect()) as con:
        row = con.execute("SELECT rate FROM network_rates WHERE network=?", (network,)).fetchone()
        return row[0] if row else None


def set_network_rate(network, rate):
    with closing(connect()) as con:
        con.execute("INSERT OR REPLACE INTO network_rates (network, rate) VALUES (?, ?)", (network, rate))
        con.commit()


def save_pending_order(trx_id, user_id, amount_bdt, amount_usdc, wallet, network, order_id=None):
    order_id = order_id or gen_order_id()
    with closing(connect()) as con:
        con.execute(
            """
            INSERT OR REPLACE INTO pending_orders
            (trx_id, user_id, amount_bdt, amount_usdc, wallet, network, order_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (trx_id, user_id, amount_bdt, amount_usdc, wallet, network, order_id),
        )
        con.commit()
        return order_id


def get_pending_order(trx_id):
    with closing(connect()) as con:
        return con.execute("SELECT * FROM pending_orders WHERE trx_id=?", (trx_id,)).fetchone()


def get_pending_orders(limit=20):
    with closing(connect()) as con:
        return con.execute(
            """
            SELECT trx_id, user_id, amount_bdt, amount_usdc, wallet, network, created_at, order_id
            FROM pending_orders
            ORDER BY datetime(created_at) DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()


def get_user_pending_orders(user_id, limit=5):
    with closing(connect()) as con:
        return con.execute(
            """
            SELECT trx_id, order_id, amount_bdt, amount_usdc, wallet, network, created_at
            FROM pending_orders
            WHERE user_id=?
            ORDER BY datetime(created_at) DESC, rowid DESC
            LIMIT ?
            """,
            (str(user_id), limit),
        ).fetchall()


def get_pending_order_count():
    with closing(connect()) as con:
        row = con.execute("SELECT COUNT(*) FROM pending_orders").fetchone()
        return row[0] if row else 0


def delete_pending_order(trx_id):
    with closing(connect()) as con:
        con.execute("DELETE FROM pending_orders WHERE trx_id=?", (trx_id,))
        con.commit()


def get_user_language(user_id):
    with closing(connect()) as con:
        row = con.execute("SELECT language FROM user_preferences WHERE user_id=?", (str(user_id),)).fetchone()
        return row[0] if row else None


def set_user_language(user_id, language):
    if language not in {"bn", "en"}:
        language = "bn"
    with closing(connect()) as con:
        con.execute(
            """
            INSERT INTO user_preferences (user_id, language, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id) DO UPDATE SET
                language=excluded.language,
                updated_at=CURRENT_TIMESTAMP
            """,
            (str(user_id), language),
        )
        con.commit()


def get_setting(key, default=None):
    with closing(connect()) as con:
        row = con.execute("SELECT value FROM app_settings WHERE key=?", (key,)).fetchone()
        return row[0] if row else default


def set_setting(key, value):
    with closing(connect()) as con:
        con.execute(
            """
            INSERT INTO app_settings (key, value, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=CURRENT_TIMESTAMP
            """,
            (key, str(value)),
        )
        con.commit()


def save_star_order(order_id, user_id, username, network, wallet, amount_crypto, stars_amount):
    with closing(connect()) as con:
        con.execute(
            """
            INSERT OR REPLACE INTO star_orders
            (order_id, user_id, username, network, wallet, amount_crypto, stars_amount, status, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', CURRENT_TIMESTAMP)
            """,
            (order_id, str(user_id), username or "", network, wallet, amount_crypto, int(stars_amount)),
        )
        con.commit()


def get_star_order(order_id):
    with closing(connect()) as con:
        return con.execute(
            """
            SELECT order_id, user_id, username, network, wallet, amount_crypto, stars_amount, status,
                   telegram_payment_charge_id, provider_payment_charge_id, tx_sig, error, created_at, updated_at
            FROM star_orders WHERE order_id=?
            """,
            (order_id,),
        ).fetchone()


def get_user_star_orders(user_id, limit=5):
    with closing(connect()) as con:
        return con.execute(
            """
            SELECT order_id, network, wallet, amount_crypto, stars_amount, status, tx_sig, error, created_at, updated_at
            FROM star_orders
            WHERE user_id=?
            ORDER BY datetime(COALESCE(updated_at, created_at)) DESC, rowid DESC
            LIMIT ?
            """,
            (str(user_id), limit),
        ).fetchall()


def update_star_order_status(order_id, status, telegram_payment_charge_id=None, provider_payment_charge_id=None, tx_sig=None, error=None):
    with closing(connect()) as con:
        con.execute(
            """
            UPDATE star_orders
            SET status=?,
                telegram_payment_charge_id=COALESCE(?, telegram_payment_charge_id),
                provider_payment_charge_id=COALESCE(?, provider_payment_charge_id),
                tx_sig=COALESCE(?, tx_sig),
                error=COALESCE(?, error),
                updated_at=CURRENT_TIMESTAMP
            WHERE order_id=?
            """,
            (status, telegram_payment_charge_id, provider_payment_charge_id, tx_sig, error, order_id),
        )
        con.commit()


init_db()


def create_or_update_seller_application(seller_id, username, display_name, bkash_number, support_contact, sms_token=None):
    seller_id = str(seller_id)
    sms_token = sms_token or gen_order_id("ST").replace("-", "")
    with closing(connect()) as con:
        con.execute(
            """
            INSERT INTO sellers (seller_id, username, display_name, bkash_number, support_contact, status, sms_token, updated_at)
            VALUES (?, ?, ?, ?, ?, 'pending', ?, CURRENT_TIMESTAMP)
            ON CONFLICT(seller_id) DO UPDATE SET
                username=excluded.username,
                display_name=excluded.display_name,
                bkash_number=excluded.bkash_number,
                support_contact=excluded.support_contact,
                status=CASE WHEN sellers.status='approved' THEN sellers.status ELSE 'pending' END,
                sms_token=COALESCE(sellers.sms_token, excluded.sms_token),
                updated_at=CURRENT_TIMESTAMP
            """,
            (seller_id, username or "", display_name, bkash_number, support_contact, sms_token),
        )
        con.commit()
    return get_seller(seller_id)


def get_seller(seller_id):
    with closing(connect()) as con:
        return con.execute("SELECT seller_id, username, display_name, bkash_number, support_contact, status, sms_token, created_at, updated_at FROM sellers WHERE seller_id=?", (str(seller_id),)).fetchone()


def get_seller_by_sms_token(sms_token):
    with closing(connect()) as con:
        return con.execute("SELECT seller_id, username, display_name, bkash_number, support_contact, status, sms_token, created_at, updated_at FROM sellers WHERE sms_token=?", (sms_token,)).fetchone()


def list_sellers_by_status(status, limit=20):
    with closing(connect()) as con:
        return con.execute("SELECT seller_id, username, display_name, bkash_number, support_contact, status, sms_token, created_at, updated_at FROM sellers WHERE status=? ORDER BY datetime(updated_at) DESC LIMIT ?", (status, limit)).fetchall()


def list_approved_sellers(limit=30):
    return list_sellers_by_status("approved", limit)


def update_seller_status(seller_id, status):
    with closing(connect()) as con:
        con.execute("UPDATE sellers SET status=?, updated_at=CURRENT_TIMESTAMP WHERE seller_id=?", (status, str(seller_id)))
        con.commit()


def approve_seller(seller_id):
    update_seller_status(seller_id, "approved")


def reject_seller(seller_id):
    update_seller_status(seller_id, "rejected")


def disable_seller(seller_id):
    update_seller_status(seller_id, "disabled")


def save_seller_wallet(seller_id, network, encrypted_key, salt, wallet_address):
    with closing(connect()) as con:
        con.execute(
            """
            INSERT INTO seller_wallets (seller_id, network, encrypted_key, salt, wallet_address, enabled, updated_at)
            VALUES (?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP)
            ON CONFLICT(seller_id, network) DO UPDATE SET
                encrypted_key=excluded.encrypted_key,
                salt=excluded.salt,
                wallet_address=excluded.wallet_address,
                enabled=1,
                updated_at=CURRENT_TIMESTAMP
            """,
            (str(seller_id), network, encrypted_key, salt, wallet_address),
        )
        con.commit()


def get_seller_wallet(seller_id, network):
    with closing(connect()) as con:
        return con.execute("SELECT seller_id, network, encrypted_key, salt, wallet_address, enabled, created_at, updated_at FROM seller_wallets WHERE seller_id=? AND network=?", (str(seller_id), network)).fetchone()


def list_seller_wallets(seller_id, enabled_only=False):
    sql = "SELECT seller_id, network, encrypted_key, salt, wallet_address, enabled, created_at, updated_at FROM seller_wallets WHERE seller_id=?"
    params = [str(seller_id)]
    if enabled_only:
        sql += " AND enabled=1"
    sql += " ORDER BY network"
    with closing(connect()) as con:
        return con.execute(sql, params).fetchall()


def list_enabled_seller_wallets(seller_id):
    return list_seller_wallets(seller_id, True)


def disable_seller_wallet(seller_id, network):
    with closing(connect()) as con:
        con.execute("UPDATE seller_wallets SET enabled=0, updated_at=CURRENT_TIMESTAMP WHERE seller_id=? AND network=?", (str(seller_id), network))
        con.commit()


def set_seller_rate(seller_id, network, rate):
    with closing(connect()) as con:
        if rate is None:
            con.execute("DELETE FROM seller_rates WHERE seller_id=? AND network=?", (str(seller_id), network))
        else:
            con.execute(
                """
                INSERT INTO seller_rates (seller_id, network, rate, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(seller_id, network) DO UPDATE SET rate=excluded.rate, updated_at=CURRENT_TIMESTAMP
                """,
                (str(seller_id), network, float(rate)),
            )
        con.commit()


def get_seller_rate(seller_id, network):
    with closing(connect()) as con:
        row = con.execute("SELECT rate FROM seller_rates WHERE seller_id=? AND network=?", (str(seller_id), network)).fetchone()
        return row[0] if row else None


def list_seller_rates(seller_id):
    with closing(connect()) as con:
        return con.execute("SELECT seller_id, network, rate, created_at, updated_at FROM seller_rates WHERE seller_id=? ORDER BY network", (str(seller_id),)).fetchall()


def save_seller_payment_notice(seller_id, trx_id, amount_bdt, sender, source, raw_notice):
    with closing(connect()) as con:
        cur = con.execute(
            """
            INSERT OR IGNORE INTO seller_payment_notices
            (seller_id, trx_id, amount_bdt, sender, source, raw_notice)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (str(seller_id), trx_id, amount_bdt, sender or "", source or "", raw_notice),
        )
        con.commit()
        return cur.rowcount > 0


def get_seller_payment_notice(seller_id, trx_id):
    with closing(connect()) as con:
        return con.execute("SELECT seller_id, trx_id, amount_bdt, sender, source, raw_notice, used, created_at FROM seller_payment_notices WHERE seller_id=? AND trx_id=? AND used=0", (str(seller_id), trx_id)).fetchone()


def mark_seller_payment_notice_used(seller_id, trx_id):
    with closing(connect()) as con:
        con.execute("UPDATE seller_payment_notices SET used=1 WHERE seller_id=? AND trx_id=?", (str(seller_id), trx_id))
        con.commit()


def create_seller_order(order_id, seller_id, buyer_id, buyer_username, payment_method, network, wallet, amount_bdt, amount_crypto, stars_amount=None, status="waiting_payment", trx_id=None):
    with closing(connect()) as con:
        con.execute(
            """
            INSERT INTO seller_orders
            (order_id, seller_id, buyer_id, buyer_username, payment_method, trx_id, network, wallet, amount_bdt, amount_crypto, stars_amount, status, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (order_id, str(seller_id), str(buyer_id), buyer_username or "", payment_method, trx_id, network, wallet, amount_bdt, amount_crypto, stars_amount, status),
        )
        con.commit()


def get_seller_order(order_id):
    with closing(connect()) as con:
        return con.execute("SELECT order_id, seller_id, buyer_id, buyer_username, payment_method, trx_id, network, wallet, amount_bdt, amount_crypto, stars_amount, status, tx_sig, error, created_at, updated_at FROM seller_orders WHERE order_id=?", (order_id,)).fetchone()


def get_seller_order_by_trx(seller_id, trx_id):
    with closing(connect()) as con:
        return con.execute("SELECT order_id, seller_id, buyer_id, buyer_username, payment_method, trx_id, network, wallet, amount_bdt, amount_crypto, stars_amount, status, tx_sig, error, created_at, updated_at FROM seller_orders WHERE seller_id=? AND trx_id=? ORDER BY datetime(created_at) DESC LIMIT 1", (str(seller_id), trx_id)).fetchone()


def find_waiting_seller_order_by_trx(seller_id, trx_id):
    with closing(connect()) as con:
        return con.execute("SELECT order_id, seller_id, buyer_id, buyer_username, payment_method, trx_id, network, wallet, amount_bdt, amount_crypto, stars_amount, status, tx_sig, error, created_at, updated_at FROM seller_orders WHERE seller_id=? AND trx_id=? AND status IN ('waiting_payment','pending_manual','paid') ORDER BY datetime(created_at) DESC LIMIT 1", (str(seller_id), trx_id)).fetchone()


def list_seller_orders(seller_id, statuses=None, limit=10):
    params = [str(seller_id)]
    sql = "SELECT order_id, seller_id, buyer_id, buyer_username, payment_method, trx_id, network, wallet, amount_bdt, amount_crypto, stars_amount, status, tx_sig, error, created_at, updated_at FROM seller_orders WHERE seller_id=?"
    if statuses:
        sql += " AND status IN (%s)" % ",".join("?" for _ in statuses)
        params.extend(statuses)
    sql += " ORDER BY datetime(updated_at) DESC, rowid DESC LIMIT ?"
    params.append(limit)
    with closing(connect()) as con:
        return con.execute(sql, params).fetchall()


def list_pending_seller_orders(seller_id=None, limit=20):
    statuses = ["waiting_payment", "pending_manual", "failed"]
    if seller_id:
        return list_seller_orders(seller_id, statuses, limit)
    with closing(connect()) as con:
        return con.execute("SELECT order_id, seller_id, buyer_id, buyer_username, payment_method, trx_id, network, wallet, amount_bdt, amount_crypto, stars_amount, status, tx_sig, error, created_at, updated_at FROM seller_orders WHERE status IN ('waiting_payment','pending_manual','failed') ORDER BY datetime(updated_at) DESC LIMIT ?", (limit,)).fetchall()


def update_seller_order(order_id, **fields):
    allowed = {"trx_id", "status", "tx_sig", "error", "stars_amount", "amount_bdt", "amount_crypto"}
    updates = []
    values = []
    for key, value in fields.items():
        if key in allowed:
            updates.append(f"{key}=?")
            values.append(value)
    if not updates:
        return
    updates.append("updated_at=CURRENT_TIMESTAMP")
    values.append(order_id)
    with closing(connect()) as con:
        con.execute(f"UPDATE seller_orders SET {', '.join(updates)} WHERE order_id=?", values)
        con.commit()


def create_seller_star_ledger(ledger_id, seller_id, order_id, stars_amount):
    with closing(connect()) as con:
        con.execute(
            """
            INSERT OR IGNORE INTO seller_star_ledger (ledger_id, seller_id, order_id, stars_amount, status, updated_at)
            VALUES (?, ?, ?, ?, 'pending_payout', CURRENT_TIMESTAMP)
            """,
            (ledger_id, str(seller_id), order_id, int(stars_amount)),
        )
        con.commit()


def list_pending_seller_payouts(limit=20):
    with closing(connect()) as con:
        return con.execute("SELECT ledger_id, seller_id, order_id, stars_amount, status, admin_note, created_at, updated_at FROM seller_star_ledger WHERE status='pending_payout' ORDER BY datetime(created_at) LIMIT ?", (limit,)).fetchall()


def list_seller_star_ledger(seller_id, status=None, limit=20):
    params = [str(seller_id)]
    sql = "SELECT ledger_id, seller_id, order_id, stars_amount, status, admin_note, created_at, updated_at FROM seller_star_ledger WHERE seller_id=?"
    if status:
        sql += " AND status=?"
        params.append(status)
    sql += " ORDER BY datetime(created_at) DESC LIMIT ?"
    params.append(limit)
    with closing(connect()) as con:
        return con.execute(sql, params).fetchall()


def mark_seller_payout_status(ledger_id, status, admin_note=""):
    with closing(connect()) as con:
        con.execute("UPDATE seller_star_ledger SET status=?, admin_note=?, updated_at=CURRENT_TIMESTAMP WHERE ledger_id=?", (status, admin_note or "", ledger_id))
        con.commit()
