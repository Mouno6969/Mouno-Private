import os
import sqlite3
import secrets
import string
from contextlib import closing
from datetime import datetime, timedelta

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


def create_web_user(username, password_hash, telegram_id=None):
    with closing(connect()) as con:
        try:
            con.execute(
                "INSERT INTO web_users (username, password_hash, telegram_id) VALUES (?, ?, ?)",
                (username, password_hash, telegram_id),
            )
            con.commit()
            return True
        except sqlite3.IntegrityError:
            return False


def get_web_user(username):
    with closing(connect()) as con:
        return con.execute(
            "SELECT id, username, password_hash, telegram_id, created_at FROM web_users WHERE username=?",
            (username,),
        ).fetchone()


def link_web_user_telegram(web_user_id, telegram_id):
    with closing(connect()) as con:
        con.execute("UPDATE web_users SET telegram_id=? WHERE id=?", (str(telegram_id), web_user_id))
        con.commit()


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
            CREATE TABLE IF NOT EXISTS web_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                telegram_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
            CREATE TABLE IF NOT EXISTS giveaway_sessions (
                session_id TEXT PRIMARY KEY,
                creator_id TEXT,
                source TEXT CHECK(source IN ('admin_stock', 'user_wallet')),
                network TEXT,
                base_amount REAL,
                recipient_count INTEGER,
                early_bonus_count INTEGER DEFAULT 0,
                early_bonus_amount REAL DEFAULT 0,
                claimed_count INTEGER DEFAULT 0,
                expires_at TEXT,
                encrypted_key TEXT,
                salt TEXT,
                wallet_address TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
            CREATE TABLE IF NOT EXISTS ai_provider_stats (
                provider TEXT PRIMARY KEY,
                success_count INTEGER DEFAULT 0,
                failure_count INTEGER DEFAULT 0,
                last_success_at TIMESTAMP,
                last_failure_at TIMESTAMP,
                last_error TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS user_preferences (
                user_id TEXT PRIMARY KEY,
                language TEXT DEFAULT 'bn',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
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
            CREATE TABLE IF NOT EXISTS seller_profiles (
                user_id TEXT PRIMARY KEY,
                status TEXT DEFAULT 'new' CHECK(status IN ('new', 'verified', 'trusted')),
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS payout_requests (
                id TEXT PRIMARY KEY,
                order_id TEXT,
                user_id TEXT,
                amount REAL,
                method TEXT,
                details TEXT,
                status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'paid', 'rejected')),
                admin_note TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS stock_reservations (
                id TEXT PRIMARY KEY,
                order_id TEXT,
                trx_id TEXT,
                user_id TEXT,
                seller_id TEXT,
                network TEXT,
                amount_crypto REAL,
                status TEXT DEFAULT 'active' CHECK(status IN ('active','released','consumed','expired')),
                reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id TEXT PRIMARY KEY,
                actor_id TEXT,
                action TEXT,
                target_type TEXT,
                target_id TEXT,
                details TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
        cur.execute("""
            CREATE TABLE IF NOT EXISTS referral_links (
                user_id TEXT PRIMARY KEY,
                code TEXT UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS referral_relationships (
                referred_user_id TEXT PRIMARY KEY,
                referrer_id TEXT,
                code TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS referral_ledger (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                type TEXT,
                amount_usd REAL,
                source_type TEXT,
                source_id TEXT,
                referred_user_id TEXT,
                status TEXT,
                details TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(source_type, source_id, user_id, type)
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS referral_withdrawals (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                amount_usd REAL,
                network TEXT,
                wallet TEXT,
                tx_sig TEXT,
                status TEXT,
                error TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        ensure_column(con, "transactions", "network", "TEXT DEFAULT 'solana'")
        ensure_column(con, "transactions", "order_id", "TEXT")
        ensure_column(con, "transactions", "updated_at", "TIMESTAMP")
        ensure_column(con, "transactions", "rate_bdt", "REAL")
        ensure_column(con, "transactions", "cost_rate_bdt", "REAL")
        ensure_column(con, "transactions", "profit_bdt", "REAL")
        ensure_column(con, "transactions", "profit_margin_pct", "REAL")
        ensure_column(con, "transactions", "source", "TEXT")
        ensure_column(con, "transactions", "seller_id", "TEXT")
        ensure_column(con, "gift_codes", "network", "TEXT DEFAULT 'solana'")
        ensure_column(con, "gift_codes", "amount", "REAL")
        ensure_column(con, "gift_codes", "giveaway_id", "TEXT")
        ensure_column(con, "gift_codes", "creator_id", "TEXT")
        ensure_column(con, "gift_codes", "claim_number", "INTEGER")
        ensure_column(con, "gift_codes", "claimed_amount", "REAL")
        ensure_column(con, "pending_orders", "order_id", "TEXT")
        ensure_column(con, "pending_orders", "updated_at", "TIMESTAMP")
        ensure_column(con, "pending_orders", "seller_id", "TEXT")
        ensure_column(con, "star_orders", "seller_id", "TEXT")
        ensure_column(con, "stock_reservations", "seller_id", "TEXT")
        ensure_column(con, "user_preferences", "created_at", "TIMESTAMP")
        ensure_column(con, "user_preferences", "username", "TEXT")
        ensure_column(con, "user_preferences", "first_name", "TEXT")
        cur.execute("UPDATE user_preferences SET created_at=COALESCE(created_at, updated_at, CURRENT_TIMESTAMP)")
        cur.execute("UPDATE transactions SET updated_at=COALESCE(updated_at, created_at)")
        cur.execute("UPDATE transactions SET seller_id=COALESCE(seller_id, ?) ", (os.getenv("ADMIN_ID"),))
        cur.execute("UPDATE pending_orders SET updated_at=COALESCE(updated_at, created_at)")
        cur.execute("UPDATE pending_orders SET seller_id=COALESCE(seller_id, ?) ", (os.getenv("ADMIN_ID"),))
        cur.execute("UPDATE star_orders SET seller_id=COALESCE(seller_id, ?) ", (os.getenv("ADMIN_ID"),))
        cur.execute("UPDATE stock_reservations SET seller_id=COALESCE(seller_id, ?) ", (os.getenv("ADMIN_ID"),))
        cur.execute("INSERT OR IGNORE INTO app_settings (key, value) VALUES ('referral_enabled', 'off')")
        cur.execute("INSERT OR IGNORE INTO app_settings (key, value) VALUES ('referral_percent', '0')")
        cur.execute("INSERT OR IGNORE INTO app_settings (key, value) VALUES ('referral_min_withdraw_usd', '1')")
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


def _source_from_trx(trx_id, source=None):
    if source:
        return source
    value = str(trx_id or "")
    if value.startswith("STAR-"):
        return "stars"
    if value.startswith("GIFT-"):
        return "gift"
    if value.startswith("ADMIN-"):
        return "admin_send"
    if value.startswith("WALLET-"):
        return "wallet"
    return "bkash"


def _cost_rate_for_network(con, network):
    row = con.execute("SELECT value FROM app_settings WHERE key=?", (f"cost_rate_{network}",)).fetchone()
    if row and row[0] not in (None, ""):
        try:
            return float(row[0])
        except Exception:
            return 0.0
    for key in (f"COST_RATE_{str(network).upper()}", "DEFAULT_COST_RATE_BDT"):
        value = os.getenv(key)
        if value not in (None, ""):
            try:
                return float(value)
            except Exception:
                return 0.0
    return 0.0


def _profit_snapshot(con, amount_bdt, amount_usdc, network, status, source):
    try:
        sale = float(amount_bdt or 0)
        crypto = float(amount_usdc or 0)
    except Exception:
        sale, crypto = 0.0, 0.0
    if status != "completed" or sale <= 0 or crypto <= 0 or source in {"admin_send", "gift", "wallet"}:
        return None, None, 0.0 if status == "completed" else None, None
    rate_bdt = sale / crypto if crypto else None
    cost_rate = _cost_rate_for_network(con, network)
    if cost_rate <= 0:
        return rate_bdt, 0.0, None, None
    profit = sale - (crypto * cost_rate)
    margin = (profit / sale * 100) if sale > 0 else None
    return rate_bdt, cost_rate, profit, margin


def save_transaction(trx_id, user_id, amount_bdt, amount_usdc, wallet, sig, status, network="solana", order_id=None, source=None, seller_id=None):
    order_id = order_id or gen_order_id()
    source = _source_from_trx(trx_id, source)
    seller_id = str(seller_id or os.getenv("ADMIN_ID") or "")
    with closing(connect()) as con:
        rate_bdt, cost_rate_bdt, profit_bdt, profit_margin_pct = _profit_snapshot(con, amount_bdt, amount_usdc, network, status, source)
        con.execute(
            """
            INSERT INTO transactions
            (trx_id, order_id, user_id, amount_bdt, amount_usdc, wallet, sig, status, network, updated_at,
             rate_bdt, cost_rate_bdt, profit_bdt, profit_margin_pct, source, seller_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(trx_id) DO UPDATE SET
                order_id=COALESCE(transactions.order_id, excluded.order_id),
                user_id=excluded.user_id,
                amount_bdt=excluded.amount_bdt,
                amount_usdc=excluded.amount_usdc,
                wallet=excluded.wallet,
                sig=excluded.sig,
                status=excluded.status,
                network=excluded.network,
                rate_bdt=excluded.rate_bdt,
                cost_rate_bdt=excluded.cost_rate_bdt,
                profit_bdt=excluded.profit_bdt,
                profit_margin_pct=excluded.profit_margin_pct,
                source=excluded.source,
                seller_id=excluded.seller_id,
                updated_at=CURRENT_TIMESTAMP
            """,
            (trx_id, order_id, user_id, amount_bdt, amount_usdc, wallet, sig, status, network, rate_bdt, cost_rate_bdt, profit_bdt, profit_margin_pct, source, seller_id),
        )
        con.commit()
        return order_id


def update_transaction(trx_id, sig=None, status=None):
    with closing(connect()) as con:
        old = con.execute("SELECT amount_bdt, amount_usdc, network, source FROM transactions WHERE trx_id=?", (trx_id,)).fetchone()
        profit_values = (None, None, None, None)
        if old and status is not None:
            rate_bdt, cost_rate_bdt, profit_bdt, profit_margin_pct = _profit_snapshot(con, old[0], old[1], old[2], status, old[3])
            profit_values = (rate_bdt, cost_rate_bdt, profit_bdt, profit_margin_pct)
        if sig is not None and status is not None:
            con.execute("UPDATE transactions SET sig=?, status=?, rate_bdt=?, cost_rate_bdt=?, profit_bdt=?, profit_margin_pct=?, updated_at=CURRENT_TIMESTAMP WHERE trx_id=?", (sig, status, *profit_values, trx_id))
        elif sig is not None:
            con.execute("UPDATE transactions SET sig=?, updated_at=CURRENT_TIMESTAMP WHERE trx_id=?", (sig, trx_id))
        elif status is not None:
            con.execute("UPDATE transactions SET status=?, rate_bdt=?, cost_rate_bdt=?, profit_bdt=?, profit_margin_pct=?, updated_at=CURRENT_TIMESTAMP WHERE trx_id=?", (status, *profit_values, trx_id))
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
            SELECT trx_id, amount_bdt, amount_usdc, network, wallet, status, created_at, order_id, user_id, sig, source
            FROM transactions WHERE trx_id=?
            """,
            (trx_id,),
        ).fetchone()


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
        tx = con.execute(
            """
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN status='completed' THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN status='failed' THEN 1 ELSE 0 END) as failed,
                COALESCE(SUM(CASE WHEN status='completed' THEN amount_bdt ELSE 0 END), 0) as total_bdt,
                COALESCE(SUM(CASE WHEN status='completed' THEN amount_usdc ELSE 0 END), 0) as total_crypto,
                COALESCE(SUM(CASE WHEN status='completed' THEN profit_bdt ELSE 0 END), 0) as total_profit
            FROM transactions
            """
        ).fetchone()
        users = con.execute(
            """
            SELECT
                COUNT(*),
                SUM(CASE WHEN datetime(created_at) >= datetime('now', '-1 day') THEN 1 ELSE 0 END)
            FROM user_preferences
            """
        ).fetchone()
        return tx + users


def set_cost_rate(network, rate):
    set_setting(f"cost_rate_{network}", rate)


def get_cost_rate(network):
    with closing(connect()) as con:
        return _cost_rate_for_network(con, network)


def get_all_cost_rates(networks):
    return {network: get_cost_rate(network) for network in networks}


def get_profit_summary(period="daily"):
    modifier = "-7 days" if str(period).lower().startswith("week") else "-1 day"
    with closing(connect()) as con:
        overall = con.execute(
            """
            SELECT COUNT(*), COALESCE(SUM(amount_bdt), 0), COALESCE(SUM(amount_usdc), 0),
                   COALESCE(SUM(profit_bdt), 0), AVG(profit_margin_pct)
            FROM transactions
            WHERE status='completed' AND datetime(created_at) >= datetime('now', ?)
            """,
            (modifier,),
        ).fetchone()
        by_network = con.execute(
            """
            SELECT network, COUNT(*), COALESCE(SUM(amount_bdt), 0), COALESCE(SUM(amount_usdc), 0),
                   COALESCE(SUM(profit_bdt), 0), AVG(profit_margin_pct)
            FROM transactions
            WHERE status='completed' AND datetime(created_at) >= datetime('now', ?)
            GROUP BY network ORDER BY SUM(profit_bdt) DESC LIMIT 10
            """,
            (modifier,),
        ).fetchall()
        return {"period": period, "overall": overall, "by_network": by_network}


def create_code(code, amount_usdc, expires_at, network="solana", giveaway_id=None, creator_id=None):
    with closing(connect()) as con:
        con.execute(
            """
            INSERT OR REPLACE INTO gift_codes
            (code, amount_usdc, amount, expires_at, network, giveaway_id, creator_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (code, amount_usdc, amount_usdc, expires_at, network, giveaway_id, creator_id),
        )
        con.commit()


def get_code(code):
    with closing(connect()) as con:
        return con.execute(
            """
            SELECT code, amount_usdc, expires_at, used, used_by, created_at, network,
                   giveaway_id, creator_id, claim_number, claimed_amount
            FROM gift_codes WHERE code=?
            """,
            (code,),
        ).fetchone()


def use_code_if_available(code, user_id):
    with closing(connect()) as con:
        con.execute("BEGIN IMMEDIATE")
        row = con.execute(
            """
            SELECT code, amount_usdc, expires_at, used, used_by, created_at, network,
                   giveaway_id, creator_id, claim_number, claimed_amount
            FROM gift_codes WHERE code=?
            """,
            (code,),
        ).fetchone()
        if not row:
            con.rollback()
            return None, "not_found"
        if row[3]:
            con.rollback()
            return row, "used"
        try:
            expired = datetime.now() > datetime.fromisoformat(row[2])
        except Exception:
            expired = True
        if expired:
            con.rollback()
            return row, "expired"
        con.execute("UPDATE gift_codes SET used=1, used_by=? WHERE code=? AND used=0", (str(user_id), code))
        if con.total_changes < 1:
            con.rollback()
            return row, "used"
        con.commit()
        return get_code(code), None


def use_code(code, user_id):
    with closing(connect()) as con:
        con.execute("UPDATE gift_codes SET used=1, used_by=? WHERE code=?", (user_id, code))
        con.commit()


def create_giveaway_session(
    session_id,
    creator_id,
    source,
    network,
    base_amount,
    recipient_count,
    early_bonus_count,
    early_bonus_amount,
    expires_at,
    encrypted_key=None,
    salt=None,
    wallet_address=None,
):
    with closing(connect()) as con:
        con.execute(
            """
            INSERT INTO giveaway_sessions
            (session_id, creator_id, source, network, base_amount, recipient_count,
             early_bonus_count, early_bonus_amount, expires_at, encrypted_key, salt, wallet_address)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                str(creator_id),
                source,
                network,
                float(base_amount),
                int(recipient_count),
                int(early_bonus_count or 0),
                float(early_bonus_amount or 0),
                expires_at,
                encrypted_key,
                salt,
                wallet_address,
            ),
        )
        con.commit()


def create_giveaway_codes(session_id, codes):
    with closing(connect()) as con:
        session = con.execute("SELECT creator_id, network, expires_at, base_amount FROM giveaway_sessions WHERE session_id=?", (session_id,)).fetchone()
        if not session:
            raise ValueError("giveaway session not found")
        creator_id, network, expires_at, base_amount = session
        con.executemany(
            """
            INSERT INTO gift_codes (code, amount_usdc, amount, expires_at, network, giveaway_id, creator_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [(code, base_amount, base_amount, expires_at, network, session_id, creator_id) for code in codes],
        )
        con.commit()


def get_giveaway_session(session_id):
    with closing(connect()) as con:
        return con.execute(
            """
            SELECT session_id, creator_id, source, network, base_amount, recipient_count,
                   early_bonus_count, early_bonus_amount, claimed_count, expires_at,
                   encrypted_key, salt, wallet_address, created_at, updated_at
            FROM giveaway_sessions WHERE session_id=?
            """,
            (session_id,),
        ).fetchone()


def claim_giveaway_code(code, user_id):
    with closing(connect()) as con:
        con.execute("BEGIN IMMEDIATE")
        code_row = con.execute(
            """
            SELECT code, amount_usdc, expires_at, used, used_by, created_at, network,
                   giveaway_id, creator_id, claim_number, claimed_amount
            FROM gift_codes WHERE code=?
            """,
            (code,),
        ).fetchone()
        if not code_row:
            con.rollback()
            return {"ok": False, "reason": "not_found"}
        if not code_row[7]:
            con.rollback()
            return {"ok": False, "reason": "not_giveaway", "code": code_row}
        if code_row[3]:
            con.rollback()
            return {"ok": False, "reason": "used", "code": code_row}
        try:
            expired = datetime.now() > datetime.fromisoformat(code_row[2])
        except Exception:
            expired = True
        if expired:
            con.rollback()
            return {"ok": False, "reason": "expired", "code": code_row}

        session = con.execute(
            """
            SELECT session_id, creator_id, source, network, base_amount, recipient_count,
                   early_bonus_count, early_bonus_amount, claimed_count, expires_at,
                   encrypted_key, salt, wallet_address, created_at, updated_at
            FROM giveaway_sessions WHERE session_id=?
            """,
            (code_row[7],),
        ).fetchone()
        if not session:
            con.rollback()
            return {"ok": False, "reason": "session_not_found", "code": code_row}
        if int(session[8] or 0) >= int(session[5] or 0):
            con.rollback()
            return {"ok": False, "reason": "fully_claimed", "code": code_row, "session": session}

        claim_number = int(session[8] or 0) + 1
        bonus = float(session[7] or 0) if claim_number <= int(session[6] or 0) else 0.0
        amount = round(float(session[4] or 0) + bonus, 8)
        con.execute(
            """
            UPDATE gift_codes
            SET used=1, used_by=?, claim_number=?, claimed_amount=?
            WHERE code=? AND used=0
            """,
            (str(user_id), claim_number, amount, code),
        )
        if con.total_changes < 1:
            con.rollback()
            return {"ok": False, "reason": "used", "code": code_row}
        con.execute(
            """
            UPDATE giveaway_sessions
            SET claimed_count=?, updated_at=CURRENT_TIMESTAMP
            WHERE session_id=?
            """,
            (claim_number, session[0]),
        )
        con.commit()
        return {
            "ok": True,
            "code": code,
            "session_id": session[0],
            "creator_id": session[1],
            "source": session[2],
            "network": session[3],
            "amount": amount,
            "claim_number": claim_number,
            "recipient_count": session[5],
            "early_bonus_count": session[6],
            "early_bonus_amount": session[7],
            "encrypted_key": session[10],
            "salt": session[11],
            "wallet_address": session[12],
            "expires_at": session[9],
        }


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


def save_pending_order(trx_id, user_id, amount_bdt, amount_usdc, wallet, network, order_id=None, seller_id=None):
    order_id = order_id or gen_order_id()
    seller_id = str(seller_id or os.getenv("ADMIN_ID") or "")
    with closing(connect()) as con:
        con.execute(
            """
            INSERT OR REPLACE INTO pending_orders
            (trx_id, user_id, amount_bdt, amount_usdc, wallet, network, order_id, seller_id, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (trx_id, user_id, amount_bdt, amount_usdc, wallet, network, order_id, seller_id),
        )
        con.commit()
        return order_id


def _reservation_where(order_id=None, trx_id=None):
    if order_id:
        return "order_id=?", (order_id,)
    if trx_id:
        return "trx_id=?", (trx_id,)
    raise ValueError("order_id or trx_id required")


def expire_stock_reservations():
    with closing(connect()) as con:
        rows = con.execute(
            "SELECT id, order_id, trx_id FROM stock_reservations WHERE status='active' AND datetime(expires_at) <= datetime('now')"
        ).fetchall()
        con.execute("UPDATE stock_reservations SET status='expired', reason='ttl_expired', updated_at=CURRENT_TIMESTAMP WHERE status='active' AND datetime(expires_at) <= datetime('now')")
        for rid, order_id, trx_id in rows:
            con.execute(
                "INSERT INTO audit_log (id, actor_id, action, target_type, target_id, details) VALUES (?, 'system', 'reservation_expired', 'reservation', ?, ?)",
                (gen_order_id("AUD"), rid, f"order={order_id} trx={trx_id}"),
            )
        con.commit()
        return len(rows)


def create_stock_reservation(order_id, user_id, network, amount_crypto, trx_id=None, ttl_minutes=15, reason="order", seller_id=None):
    expire_stock_reservations()
    if not order_id:
        order_id = gen_order_id()
    seller_id = str(seller_id or os.getenv("ADMIN_ID") or "")
    expires_at = (datetime.utcnow() + timedelta(minutes=ttl_minutes)).isoformat(timespec="seconds")
    with closing(connect()) as con:
        existing = con.execute("SELECT id FROM stock_reservations WHERE order_id=? AND status='active'", (order_id,)).fetchone()
        if existing:
            con.execute(
                """
                UPDATE stock_reservations
                SET trx_id=COALESCE(?, trx_id), user_id=?, network=?, amount_crypto=?, reason=?, expires_at=?, seller_id=?, updated_at=CURRENT_TIMESTAMP
                WHERE id=?
                """,
                (trx_id, str(user_id), network, float(amount_crypto), reason, expires_at, seller_id, existing[0]),
            )
            res_id = existing[0]
        else:
            res_id = gen_order_id("RES")
            con.execute(
                """
                INSERT INTO stock_reservations (id, order_id, trx_id, user_id, seller_id, network, amount_crypto, status, reason, expires_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'active', ?, ?)
                """,
                (res_id, order_id, trx_id, str(user_id), seller_id, network, float(amount_crypto), reason, expires_at),
            )
        con.commit()
        return res_id, order_id


def bind_stock_reservation_trx(order_id, trx_id):
    with closing(connect()) as con:
        con.execute("UPDATE stock_reservations SET trx_id=?, updated_at=CURRENT_TIMESTAMP WHERE order_id=? AND status='active'", (trx_id, order_id))
        con.commit()


def get_active_reserved_amount(network, exclude_order_id=None, exclude_trx_id=None):
    expire_stock_reservations()
    sql = "SELECT COALESCE(SUM(amount_crypto), 0) FROM stock_reservations WHERE status='active' AND network=?"
    params = [network]
    if exclude_order_id:
        sql += " AND COALESCE(order_id, '') != ?"
        params.append(exclude_order_id)
    if exclude_trx_id:
        sql += " AND COALESCE(trx_id, '') != ?"
        params.append(exclude_trx_id)
    with closing(connect()) as con:
        return float(con.execute(sql, params).fetchone()[0] or 0)


def get_active_reservation(order_id=None, trx_id=None):
    expire_stock_reservations()
    where, params = _reservation_where(order_id, trx_id)
    with closing(connect()) as con:
        return con.execute(
            f"SELECT id, order_id, trx_id, user_id, seller_id, network, amount_crypto, status, reason, created_at, expires_at, updated_at FROM stock_reservations WHERE status='active' AND {where}",
            params,
        ).fetchone()


def _set_reservation_status(status, order_id=None, trx_id=None, reason=None, actor_id="system"):
    where, params = _reservation_where(order_id, trx_id)
    with closing(connect()) as con:
        rows = con.execute(f"SELECT id, order_id, trx_id, network, amount_crypto FROM stock_reservations WHERE status='active' AND {where}", params).fetchall()
        con.execute(f"UPDATE stock_reservations SET status=?, reason=COALESCE(?, reason), updated_at=CURRENT_TIMESTAMP WHERE status='active' AND {where}", (status, reason, *params))
        for rid, oid, tid, network, amount in rows:
            con.execute(
                "INSERT INTO audit_log (id, actor_id, action, target_type, target_id, details) VALUES (?, ?, ?, 'reservation', ?, ?)",
                (gen_order_id("AUD"), str(actor_id), f"reservation_{status}", rid, f"order={oid} trx={tid} network={network} amount={amount} reason={reason or ''}"),
            )
        con.commit()
        return len(rows)


def consume_stock_reservation(order_id=None, trx_id=None):
    return _set_reservation_status("consumed", order_id, trx_id, "sent", "system")


def release_stock_reservation(order_id=None, trx_id=None, reason="released", actor_id="system"):
    return _set_reservation_status("released", order_id, trx_id, reason, actor_id)


def list_stock_reservations(status="active", limit=20):
    expire_stock_reservations()
    with closing(connect()) as con:
        if status:
            return con.execute(
                """
                SELECT id, order_id, trx_id, user_id, seller_id, network, amount_crypto, status, reason, created_at, expires_at, updated_at
                FROM stock_reservations WHERE status=? ORDER BY datetime(created_at) DESC LIMIT ?
                """,
                (status, limit),
            ).fetchall()
        return con.execute(
            """
            SELECT id, order_id, trx_id, user_id, seller_id, network, amount_crypto, status, reason, created_at, expires_at, updated_at
            FROM stock_reservations ORDER BY datetime(created_at) DESC LIMIT ?
            """,
            (limit,),
        ).fetchall()


def get_pending_order(trx_id):
    with closing(connect()) as con:
        return con.execute(
            """
            SELECT trx_id, user_id, amount_bdt, amount_usdc, wallet, network, created_at, order_id, updated_at
            FROM pending_orders WHERE trx_id=?
            """,
            (trx_id,),
        ).fetchone()


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


def save_user_info(user_id, username, first_name):
    with closing(connect()) as con:
        con.execute(
            """
            INSERT INTO user_preferences (user_id, username, first_name, created_at, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id) DO UPDATE SET
                username=excluded.username,
                first_name=excluded.first_name,
                created_at=COALESCE(user_preferences.created_at, CURRENT_TIMESTAMP),
                updated_at=CURRENT_TIMESTAMP
            """,
            (str(user_id), username, first_name),
        )
        con.commit()


def get_users_paged(filter_type="all", page=0, search_query=None, limit=10):
    offset = int(page) * int(limit)
    where_clause = "1=1"
    params = []

    if filter_type == "new":
        where_clause = "datetime(u.created_at) >= datetime('now', '-7 days')"
    elif filter_type == "top":
        # Handled by ORDER BY
        pass
    elif filter_type == "inactive":
        where_clause = "u.user_id NOT IN (SELECT user_id FROM transactions WHERE status='completed' AND datetime(created_at) >= datetime('now', '-30 days'))"
    elif filter_type == "search" and search_query:
        where_clause = "(u.user_id LIKE ? OR u.username LIKE ? OR u.first_name LIKE ?)"
        q = f"%{search_query}%"
        params = [q, q, q]

    sql = f"""
        SELECT
            u.user_id,
            u.username,
            u.first_name,
            u.created_at,
            COUNT(t.trx_id) as order_count,
            COALESCE(SUM(t.amount_bdt), 0) as total_spent
        FROM user_preferences u
        LEFT JOIN transactions t ON u.user_id = t.user_id AND t.status = 'completed'
        WHERE {where_clause}
        GROUP BY u.user_id
    """

    if filter_type == "top":
        sql += " ORDER BY total_spent DESC, order_count DESC"
    else:
        sql += " ORDER BY u.created_at DESC"

    sql += " LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    with closing(connect()) as con:
        rows = con.execute(sql, params).fetchall()
        total = con.execute(f"SELECT COUNT(*) FROM user_preferences u WHERE {where_clause}", params[:-2]).fetchone()[0]
        return rows, total


def get_all_users_for_export():
    sql = """
        SELECT
            u.user_id,
            u.username,
            u.first_name,
            u.created_at,
            COUNT(t.trx_id) as order_count,
            COALESCE(SUM(t.amount_bdt), 0) as total_spent
        FROM user_preferences u
        LEFT JOIN transactions t ON u.user_id = t.user_id AND t.status = 'completed'
        GROUP BY u.user_id
        ORDER BY u.created_at DESC
    """
    with closing(connect()) as con:
        return con.execute(sql).fetchall()


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


def _referral_code():
    chars = string.ascii_letters + string.digits
    return "".join(secrets.choice(chars) for _ in range(10))


def get_or_create_referral_code(user_id):
    user_id = str(user_id)
    with closing(connect()) as con:
        row = con.execute("SELECT code FROM referral_links WHERE user_id=?", (user_id,)).fetchone()
        if row:
            return row[0]
        for _ in range(20):
            code = _referral_code()
            try:
                con.execute("INSERT INTO referral_links (user_id, code) VALUES (?, ?)", (user_id, code))
                con.commit()
                return code
            except sqlite3.IntegrityError:
                continue
        raise RuntimeError("could not generate referral code")


def get_referrer_for_user(user_id):
    with closing(connect()) as con:
        row = con.execute("SELECT referrer_id FROM referral_relationships WHERE referred_user_id=?", (str(user_id),)).fetchone()
        return row[0] if row else None


def bind_referral(referred_user_id, referrer_code):
    referred_user_id = str(referred_user_id)
    code = str(referrer_code or "").strip()
    if code.startswith("ref_"):
        code = code[4:]
    if not code:
        return "invalid"
    with closing(connect()) as con:
        row = con.execute("SELECT user_id, code FROM referral_links WHERE code=?", (code,)).fetchone()
        if not row:
            return "invalid"
        referrer_id, saved_code = str(row[0]), row[1]
        if referrer_id == referred_user_id:
            return "self"
        exists = con.execute("SELECT referrer_id FROM referral_relationships WHERE referred_user_id=?", (referred_user_id,)).fetchone()
        if exists:
            return "exists"
        try:
            con.execute(
                "INSERT INTO referral_relationships (referred_user_id, referrer_id, code) VALUES (?, ?, ?)",
                (referred_user_id, referrer_id, saved_code),
            )
            con.commit()
            return "bound"
        except sqlite3.IntegrityError:
            return "exists"


def referral_balance(user_id):
    with closing(connect()) as con:
        row = con.execute(
            "SELECT COALESCE(SUM(amount_usd), 0) FROM referral_ledger WHERE user_id=? AND status='completed'",
            (str(user_id),),
        ).fetchone()
        return float(row[0] or 0)


def referral_available_balance(user_id):
    with closing(connect()) as con:
        row = con.execute(
            """
            SELECT COALESCE(SUM(amount_usd), 0) FROM referral_ledger
            WHERE user_id=? AND (status='completed' OR (type='withdrawal' AND status='pending'))
            """,
            (str(user_id),),
        ).fetchone()
        return float(row[0] or 0)


def list_referral_ledger(user_id, limit=10):
    with closing(connect()) as con:
        return con.execute(
            """
            SELECT id, type, amount_usd, source_type, source_id, referred_user_id, status, details, created_at
            FROM referral_ledger WHERE user_id=?
            ORDER BY datetime(created_at) DESC, rowid DESC LIMIT ?
            """,
            (str(user_id), int(limit)),
        ).fetchall()


def referral_stats(user_id):
    user_id = str(user_id)
    with closing(connect()) as con:
        count = con.execute("SELECT COUNT(*) FROM referral_relationships WHERE referrer_id=?", (user_id,)).fetchone()[0]
        earned = con.execute(
            "SELECT COALESCE(SUM(amount_usd), 0) FROM referral_ledger WHERE user_id=? AND type='credit' AND status='completed'",
            (user_id,),
        ).fetchone()[0]
        withdrawn = con.execute(
            "SELECT COALESCE(SUM(-amount_usd), 0) FROM referral_ledger WHERE user_id=? AND type='withdrawal' AND status='completed'",
            (user_id,),
        ).fetchone()[0]
        balance = con.execute(
            "SELECT COALESCE(SUM(amount_usd), 0) FROM referral_ledger WHERE user_id=? AND status='completed'",
            (user_id,),
        ).fetchone()[0]
        return {"referral_count": int(count or 0), "total_earned": float(earned or 0), "total_withdrawn": float(withdrawn or 0), "balance": float(balance or 0)}


def credit_referral_reward(referred_user_id, source_type, source_id, amount_usd, percent, details=None):
    try:
        amount_usd = float(amount_usd or 0)
        percent = float(percent or 0)
    except Exception:
        return None
    if amount_usd <= 0 or percent <= 0:
        return None
    referred_user_id = str(referred_user_id)
    referrer_id = get_referrer_for_user(referred_user_id)
    if not referrer_id or str(referrer_id) == referred_user_id:
        return None
    reward = round(amount_usd * percent / 100, 6)
    if reward <= 0:
        return None
    ledger_id = f"REF-{source_type}-{source_id}-{referrer_id}-credit"[:120]
    with closing(connect()) as con:
        cur = con.execute(
            """
            INSERT OR IGNORE INTO referral_ledger
            (id, user_id, type, amount_usd, source_type, source_id, referred_user_id, status, details)
            VALUES (?, ?, 'credit', ?, ?, ?, ?, 'completed', ?)
            """,
            (ledger_id, str(referrer_id), reward, str(source_type), str(source_id), referred_user_id, details),
        )
        con.commit()
        if cur.rowcount <= 0:
            return None
        return {"id": ledger_id, "user_id": str(referrer_id), "amount_usd": reward}


def create_referral_withdrawal(user_id, amount_usd, network, wallet, status="pending", error=None):
    withdrawal_id = gen_order_id("RWD")
    with closing(connect()) as con:
        con.execute(
            """
            INSERT INTO referral_withdrawals (id, user_id, amount_usd, network, wallet, status, error)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (withdrawal_id, str(user_id), float(amount_usd), network, wallet, status, error),
        )
        con.commit()
        return withdrawal_id


def mark_referral_withdrawal(withdrawal_id, status, tx_sig=None, error=None):
    with closing(connect()) as con:
        con.execute(
            """
            UPDATE referral_withdrawals
            SET status=?, tx_sig=COALESCE(?, tx_sig), error=COALESCE(?, error), updated_at=CURRENT_TIMESTAMP
            WHERE id=?
            """,
            (status, tx_sig, error, withdrawal_id),
        )
        con.commit()


def reserve_referral_withdrawal(user_id, withdrawal_id, amount_usd, network, wallet):
    user_id = str(user_id)
    amount_usd = float(amount_usd)
    if amount_usd <= 0:
        return False
    with closing(connect()) as con:
        try:
            con.execute("BEGIN IMMEDIATE")
            row = con.execute(
                """
                SELECT COALESCE(SUM(amount_usd), 0) FROM referral_ledger
                WHERE user_id=? AND (status='completed' OR (type='withdrawal' AND status='pending'))
                """,
                (user_id,),
            ).fetchone()
            if float(row[0] or 0) + 1e-9 < amount_usd:
                con.rollback()
                return False
            cur = con.execute(
                """
                INSERT OR IGNORE INTO referral_ledger
                (id, user_id, type, amount_usd, source_type, source_id, referred_user_id, status, details)
                VALUES (?, ?, 'withdrawal', ?, 'referral_withdrawal', ?, NULL, 'pending', ?)
                """,
                (f"REFWD-{withdrawal_id}", user_id, -amount_usd, withdrawal_id, f"network={network} wallet={wallet}"),
            )
            if cur.rowcount <= 0:
                con.rollback()
                return False
            wd_cur = con.execute(
                "UPDATE referral_withdrawals SET status='sending', updated_at=CURRENT_TIMESTAMP WHERE id=? AND user_id=?",
                (withdrawal_id, user_id),
            )
            if wd_cur.rowcount <= 0:
                con.rollback()
                return False
            con.commit()
            return True
        except Exception:
            con.rollback()
            raise


def complete_referral_withdrawal(withdrawal_id, tx_sig):
    with closing(connect()) as con:
        try:
            con.execute("BEGIN IMMEDIATE")
            con.execute(
                "UPDATE referral_ledger SET status='completed', details=COALESCE(details, '') || ?, updated_at=CURRENT_TIMESTAMP WHERE id=? AND type='withdrawal' AND status='pending'",
                (f" tx={tx_sig}", f"REFWD-{withdrawal_id}"),
            )
            con.execute(
                "UPDATE referral_withdrawals SET status='completed', tx_sig=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
                (tx_sig, withdrawal_id),
            )
            con.commit()
        except Exception:
            con.rollback()
            raise


def fail_referral_withdrawal(withdrawal_id, error=None, tx_sig=None):
    with closing(connect()) as con:
        try:
            con.execute("BEGIN IMMEDIATE")
            con.execute(
                "UPDATE referral_ledger SET status='failed', details=COALESCE(details, '') || ?, updated_at=CURRENT_TIMESTAMP WHERE id=? AND type='withdrawal' AND status='pending'",
                (f" error={str(error or '')[:200]}", f"REFWD-{withdrawal_id}"),
            )
            con.execute(
                """
                UPDATE referral_withdrawals
                SET status='failed', tx_sig=COALESCE(?, tx_sig), error=COALESCE(?, error), updated_at=CURRENT_TIMESTAMP
                WHERE id=?
                """,
                (tx_sig, str(error)[:500] if error is not None else None, withdrawal_id),
            )
            con.commit()
        except Exception:
            con.rollback()
            raise


def debit_referral_withdrawal(user_id, withdrawal_id, amount_usd, network, wallet, tx_sig):
    if not reserve_referral_withdrawal(user_id, withdrawal_id, amount_usd, network, wallet):
        return False
    complete_referral_withdrawal(withdrawal_id, tx_sig)
    return True


def referral_admin_stats():
    with closing(connect()) as con:
        row = con.execute(
            """
            SELECT
                COALESCE(SUM(CASE WHEN type='credit' AND status='completed' THEN amount_usd ELSE 0 END), 0),
                COALESCE(SUM(CASE WHEN type='withdrawal' AND status='completed' THEN -amount_usd ELSE 0 END), 0),
                COALESCE(SUM(CASE WHEN status='completed' THEN amount_usd ELSE 0 END), 0)
            FROM referral_ledger
            """
        ).fetchone()
        failed = con.execute("SELECT COUNT(*) FROM referral_withdrawals WHERE status='failed'").fetchone()[0]
        rels = con.execute("SELECT COUNT(*) FROM referral_relationships").fetchone()[0]
        return {"credited": float(row[0] or 0), "withdrawn": float(row[1] or 0), "liability": float(row[2] or 0), "failed_withdrawals": int(failed or 0), "relationships": int(rels or 0)}


def _sanitize_ai_error(error):
    if not error:
        return None
    if isinstance(error, BaseException):
        return type(error).__name__[:80]
    value = " ".join(str(error).replace("\r", " ").replace("\n", " ").split())
    if not value:
        return None
    parts = value.split()
    label = parts[0][:80]
    status = next((part for part in parts[1:] if part.startswith("status=") and part[7:].isdigit()), None)
    if status:
        return f"{label} {status}"[:120]
    return label


def record_ai_provider_result(provider, success, error=None):
    safe_error = None if success else _sanitize_ai_error(error)
    with closing(connect()) as con:
        con.execute(
            """
            INSERT INTO ai_provider_stats (
                provider, success_count, failure_count, last_success_at,
                last_failure_at, last_error, updated_at
            )
            VALUES (
                ?, ?, ?,
                CASE WHEN ? THEN CURRENT_TIMESTAMP ELSE NULL END,
                CASE WHEN ? THEN NULL ELSE CURRENT_TIMESTAMP END,
                ?, CURRENT_TIMESTAMP
            )
            ON CONFLICT(provider) DO UPDATE SET
                success_count=success_count + excluded.success_count,
                failure_count=failure_count + excluded.failure_count,
                last_success_at=CASE WHEN ? THEN CURRENT_TIMESTAMP ELSE last_success_at END,
                last_failure_at=CASE WHEN ? THEN last_failure_at ELSE CURRENT_TIMESTAMP END,
                last_error=CASE WHEN ? THEN last_error ELSE excluded.last_error END,
                updated_at=CURRENT_TIMESTAMP
            """,
            (provider, 1 if success else 0, 0 if success else 1, success, success, safe_error, success, success, success),
        )
        con.commit()


def list_ai_provider_stats():
    with closing(connect()) as con:
        return con.execute(
            """
            SELECT provider, success_count, failure_count, last_success_at,
                   last_failure_at, last_error, updated_at
            FROM ai_provider_stats
            ORDER BY success_count DESC, provider
            """
        ).fetchall()


def add_audit(actor_id, action, target_type=None, target_id=None, details=None):
    audit_id = gen_order_id("AUD")
    with closing(connect()) as con:
        con.execute(
            """
            INSERT INTO audit_log (id, actor_id, action, target_type, target_id, details)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (audit_id, str(actor_id), action, target_type, target_id, details),
        )
        con.commit()
        return audit_id


def list_audit(limit=30):
    with closing(connect()) as con:
        return con.execute(
            "SELECT id, actor_id, action, target_type, target_id, details, created_at FROM audit_log ORDER BY datetime(created_at) DESC, rowid DESC LIMIT ?",
            (limit,),
        ).fetchall()


def save_star_order(order_id, user_id, username, network, wallet, amount_crypto, stars_amount, seller_id=None):
    seller_id = str(seller_id or os.getenv("ADMIN_ID") or "")
    with closing(connect()) as con:
        con.execute(
            """
            INSERT OR REPLACE INTO star_orders
            (order_id, user_id, username, network, wallet, amount_crypto, stars_amount, status, seller_id, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', ?, CURRENT_TIMESTAMP)
            """,
            (order_id, str(user_id), username or "", network, wallet, amount_crypto, int(stars_amount), seller_id),
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


def get_transaction_by_order_id(order_id):
    with closing(connect()) as con:
        return con.execute(
            """
            SELECT trx_id, amount_bdt, amount_usdc, network, wallet, status, created_at, order_id, user_id, sig, updated_at
            FROM transactions WHERE order_id=?
            """,
            (order_id,),
        ).fetchone()


def get_transaction_detail(identifier):
    row = get_transaction(identifier)
    if row:
        return row + (None,)
    return get_transaction_by_order_id(identifier)


def get_pending_order_by_order_id(order_id):
    with closing(connect()) as con:
        return con.execute(
            """
            SELECT trx_id, user_id, amount_bdt, amount_usdc, wallet, network, created_at, order_id, updated_at
            FROM pending_orders WHERE order_id=?
            """,
            (order_id,),
        ).fetchone()


def find_order(identifier):
    ident = str(identifier).strip()
    tx = get_transaction_detail(ident)
    if tx:
        return "transaction", tx
    pending = get_pending_order(ident) or get_pending_order_by_order_id(ident)
    if pending:
        return "pending", pending
    star = get_star_order(ident)
    if star:
        return "star", star
    return None, None


def set_seller_status(user_id, status):
    if status not in {"new", "verified", "trusted"}:
        raise ValueError("invalid seller status")
    with closing(connect()) as con:
        con.execute(
            """
            INSERT INTO seller_profiles (user_id, status, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id) DO UPDATE SET status=excluded.status, updated_at=CURRENT_TIMESTAMP
            """,
            (str(user_id), status),
        )
        con.commit()


def get_seller_status(user_id):
    with closing(connect()) as con:
        return con.execute("SELECT user_id, status, updated_at FROM seller_profiles WHERE user_id=?", (str(user_id),)).fetchone()


def list_seller_profiles(limit=50):
    with closing(connect()) as con:
        return con.execute(
            "SELECT user_id, status, updated_at FROM seller_profiles ORDER BY datetime(updated_at) DESC LIMIT ?",
            (limit,),
        ).fetchall()


def create_payout_request(user_id, amount, method, details, order_id=None):
    req_id = gen_order_id("PAY")
    with closing(connect()) as con:
        con.execute(
            """
            INSERT INTO payout_requests (id, order_id, user_id, amount, method, details)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (req_id, order_id, str(user_id), float(amount), method, details),
        )
        con.commit()
        return req_id


def get_payout_request(req_id):
    with closing(connect()) as con:
        return con.execute(
            "SELECT id, order_id, user_id, amount, method, details, status, admin_note, created_at, updated_at FROM payout_requests WHERE id=?",
            (req_id,),
        ).fetchone()


def list_payout_requests(status="pending", limit=20):
    with closing(connect()) as con:
        if status:
            return con.execute(
                """
                SELECT id, order_id, user_id, amount, method, details, status, admin_note, created_at, updated_at
                FROM payout_requests WHERE status=? ORDER BY datetime(created_at) DESC LIMIT ?
                """,
                (status, limit),
            ).fetchall()
        return con.execute(
            """
            SELECT id, order_id, user_id, amount, method, details, status, admin_note, created_at, updated_at
            FROM payout_requests ORDER BY datetime(created_at) DESC LIMIT ?
            """,
            (limit,),
        ).fetchall()


def update_payout_request(req_id, status, admin_note=""):
    if status not in {"pending", "paid", "rejected"}:
        raise ValueError("invalid payout status")
    with closing(connect()) as con:
        con.execute(
            "UPDATE payout_requests SET status=?, admin_note=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (status, admin_note or "", req_id),
        )
        con.commit()


def touch_webhook_notice(source, trx_id=None, amount_bdt=None):
    set_setting("webhook_last_notice_at", datetime_now())
    set_setting("webhook_last_source", source or "unknown")
    if trx_id:
        set_setting("webhook_last_trx_id", trx_id)
    if amount_bdt is not None:
        set_setting("webhook_last_amount_bdt", amount_bdt)


def datetime_now():
    from datetime import datetime

    return datetime.now().isoformat(timespec="seconds")


def get_webhook_health():
    return {
        "last_notice_at": get_setting("webhook_last_notice_at"),
        "source": get_setting("webhook_last_source"),
        "trx_id": get_setting("webhook_last_trx_id"),
        "amount_bdt": get_setting("webhook_last_amount_bdt"),
    }


def get_report_stats(period="daily"):
    modifier = "-7 days" if str(period).lower().startswith("week") else "-1 day"
    with closing(connect()) as con:
        tx = con.execute(
            f"""
            SELECT COUNT(*),
                   SUM(CASE WHEN status='completed' THEN 1 ELSE 0 END),
                   SUM(CASE WHEN status='failed' THEN 1 ELSE 0 END),
                   SUM(CASE WHEN status NOT IN ('completed','failed') THEN 1 ELSE 0 END),
                   COALESCE(SUM(CASE WHEN status='completed' THEN amount_bdt ELSE 0 END), 0),
                   COALESCE(SUM(CASE WHEN status='completed' THEN amount_usdc ELSE 0 END), 0),
                   COALESCE(SUM(CASE WHEN status='completed' THEN profit_bdt ELSE 0 END), 0)
            FROM transactions WHERE datetime(created_at) >= datetime('now', ?)
            """,
            (modifier,),
        ).fetchone()
        top_networks = con.execute(
            """
            SELECT network, COUNT(*), COALESCE(SUM(amount_usdc), 0), COALESCE(SUM(amount_bdt), 0)
            FROM transactions
            WHERE datetime(created_at) >= datetime('now', ?) AND status='completed'
            GROUP BY network ORDER BY COUNT(*) DESC, SUM(amount_usdc) DESC LIMIT 5
            """,
            (modifier,),
        ).fetchall()
        pending = con.execute("SELECT COUNT(*) FROM pending_orders").fetchone()[0]
        stars_pending = con.execute("SELECT COUNT(*), COALESCE(SUM(stars_amount), 0) FROM star_orders WHERE status IN ('pending','paid')").fetchone()
        payouts_pending = con.execute("SELECT COUNT(*), COALESCE(SUM(amount), 0) FROM payout_requests WHERE status='pending'").fetchone()
        ref = con.execute(
            """
            SELECT
                COALESCE(SUM(CASE WHEN type='credit' AND status='completed' THEN amount_usd ELSE 0 END), 0),
                COALESCE(SUM(CASE WHEN type='withdrawal' AND status='completed' THEN -amount_usd ELSE 0 END), 0),
                COALESCE(SUM(CASE WHEN status='completed' THEN amount_usd ELSE 0 END), 0)
            FROM referral_ledger
            """
        ).fetchone()
        ref_failed = con.execute("SELECT COUNT(*) FROM referral_withdrawals WHERE status='failed'").fetchone()[0]
        new_users = con.execute(
            "SELECT COUNT(*) FROM user_preferences WHERE datetime(created_at) >= datetime('now', ?)",
            (modifier,),
        ).fetchone()[0]
        return {"period": period, "transactions": tx, "top_networks": top_networks, "pending_orders": pending, "stars_pending": stars_pending, "payouts_pending": payouts_pending, "referrals": ref, "referral_failed_withdrawals": ref_failed, "new_users": new_users}


def get_seller_public_stats(user_id):
    seller_id = str(user_id or os.getenv("ADMIN_ID") or "")
    with closing(connect()) as con:
        status_row = con.execute("SELECT status, updated_at FROM seller_profiles WHERE user_id=?", (seller_id,)).fetchone()
        tx = con.execute(
            """
            SELECT COUNT(*),
                   SUM(CASE WHEN status='completed' THEN 1 ELSE 0 END),
                   SUM(CASE WHEN status='failed' THEN 1 ELSE 0 END),
                   COALESCE(SUM(CASE WHEN status='completed' THEN amount_bdt ELSE 0 END), 0),
                   COALESCE(SUM(CASE WHEN status='completed' THEN amount_usdc ELSE 0 END), 0),
                   MAX(CASE WHEN status='completed' THEN updated_at ELSE NULL END)
            FROM transactions WHERE COALESCE(seller_id, ?) = ?
            """,
            (seller_id, seller_id),
        ).fetchone()
        avg_delivery = con.execute(
            """
            SELECT AVG((julianday(COALESCE(updated_at, created_at)) - julianday(created_at)) * 86400)
            FROM transactions
            WHERE COALESCE(seller_id, ?) = ? AND status='completed' AND updated_at IS NOT NULL
            """,
            (seller_id, seller_id),
        ).fetchone()[0]
        reserves = con.execute(
            """
            SELECT COUNT(*), COALESCE(SUM(amount_crypto), 0)
            FROM stock_reservations WHERE status='active' AND COALESCE(seller_id, ?) = ?
            """,
            (seller_id, seller_id),
        ).fetchone()
        return {
            "user_id": seller_id,
            "status": status_row[0] if status_row else "new",
            "updated_at": status_row[1] if status_row else None,
            "total_orders": tx[0] or 0,
            "completed_orders": tx[1] or 0,
            "failed_orders": tx[2] or 0,
            "completed_bdt": tx[3] or 0,
            "completed_crypto": tx[4] or 0,
            "last_completed_at": tx[5],
            "avg_delivery_seconds": avg_delivery,
            "active_reservations": reserves[0] or 0,
            "reserved_crypto": reserves[1] or 0,
        }


def get_user_analytics(user_id):
    user_id = str(user_id)
    with closing(connect()) as con:
        # Basic user info
        user_pref = con.execute("SELECT created_at FROM user_preferences WHERE user_id=?", (user_id,)).fetchone()
        joined_at = user_pref[0] if user_pref else None

        # Transaction stats
        tx_stats = con.execute(
            """
            SELECT
                COUNT(*),
                COALESCE(SUM(amount_bdt), 0),
                COALESCE(AVG(amount_bdt), 0),
                MAX(created_at)
            FROM transactions
            WHERE user_id=? AND status='completed'
            """,
            (user_id,),
        ).fetchone()

        total_orders = tx_stats[0] or 0
        total_bdt = round(tx_stats[1] or 0, 2)
        avg_bdt = round(tx_stats[2] or 0, 2)
        last_order_at = tx_stats[3]

        # Favorite network
        fav_network_row = con.execute(
            """
            SELECT network, COUNT(*) as cnt
            FROM transactions
            WHERE user_id=? AND status='completed'
            GROUP BY network
            ORDER BY cnt DESC
            LIMIT 1
            """,
            (user_id,),
        ).fetchone()
        fav_network = fav_network_row[0] if fav_network_row else None

        # Inactivity
        inactive_days = None
        if last_order_at:
            inactive_row = con.execute(
                "SELECT CAST(julianday('now') - julianday(?) AS INTEGER)",
                (last_order_at,)
            ).fetchone()
            inactive_days = inactive_row[0] if inactive_row else 0

        return {
            "user_id": user_id,
            "joined_at": joined_at,
            "total_orders": total_orders,
            "total_bdt": total_bdt,
            "avg_bdt": avg_bdt,
            "fav_network": fav_network,
            "last_order_at": last_order_at,
            "inactive_days": inactive_days
        }


def dashboard_snapshot(limit=20):
    with closing(connect()) as con:
        return {
            "transactions": con.execute("SELECT trx_id, order_id, user_id, amount_bdt, amount_usdc, network, status, profit_bdt, source, created_at FROM transactions ORDER BY datetime(created_at) DESC LIMIT ?", (limit,)).fetchall(),
            "pending": get_pending_orders(limit),
            "sellers": list_seller_profiles(limit),
            "payouts": list_payout_requests(None, limit),
            "reservations": list_stock_reservations(None, limit),
            "audit": list_audit(limit),
            "profit_daily": get_profit_summary("daily"),
            "profit_weekly": get_profit_summary("weekly"),
        }



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
        return con.execute("SELECT seller_id, username, display_name, bkash_number, support_contact, status, sms_token, created_at, updated_at FROM sellers WHERE sms_token=?", (str(sms_token),)).fetchone()


def list_sellers_by_status(status, limit=20):
    with closing(connect()) as con:
        return con.execute("SELECT seller_id, username, display_name, bkash_number, support_contact, status, sms_token, created_at, updated_at FROM sellers WHERE status=? ORDER BY datetime(updated_at) DESC LIMIT ?", (status, limit)).fetchall()


def list_approved_sellers(limit=30):
    return list_sellers_by_status("approved", limit)


def _update_market_seller_status(seller_id, status):
    with closing(connect()) as con:
        con.execute("UPDATE sellers SET status=?, updated_at=CURRENT_TIMESTAMP WHERE seller_id=?", (status, str(seller_id)))
        con.commit()


def approve_seller(seller_id):
    _update_market_seller_status(seller_id, "approved")


def reject_seller(seller_id):
    _update_market_seller_status(seller_id, "rejected")


def disable_seller(seller_id):
    _update_market_seller_status(seller_id, "disabled")


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
            (str(seller_id), str(trx_id), amount_bdt, sender or "", source or "", raw_notice),
        )
        con.commit()
        return cur.rowcount > 0


def get_seller_payment_notice(seller_id, trx_id):
    with closing(connect()) as con:
        return con.execute("SELECT seller_id, trx_id, amount_bdt, sender, source, raw_notice, used, created_at FROM seller_payment_notices WHERE seller_id=? AND trx_id=? AND used=0", (str(seller_id), str(trx_id))).fetchone()


def get_seller_payment_notice_owner(trx_id):
    with closing(connect()) as con:
        return con.execute(
            """
            SELECT seller_id, trx_id, amount_bdt, sender, source, raw_notice, used, created_at
            FROM seller_payment_notices
            WHERE trx_id=?
            ORDER BY datetime(created_at), rowid
            LIMIT 1
            """,
            (str(trx_id),),
        ).fetchone()


def mark_seller_payment_notice_used(seller_id, trx_id):
    with closing(connect()) as con:
        con.execute("UPDATE seller_payment_notices SET used=1 WHERE seller_id=? AND trx_id=?", (str(seller_id), str(trx_id)))
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
        return con.execute("SELECT order_id, seller_id, buyer_id, buyer_username, payment_method, trx_id, network, wallet, amount_bdt, amount_crypto, stars_amount, status, tx_sig, error, created_at, updated_at FROM seller_orders WHERE seller_id=? AND trx_id=? ORDER BY datetime(created_at) DESC LIMIT 1", (str(seller_id), str(trx_id))).fetchone()


def get_completed_seller_order_by_trx(trx_id):
    with closing(connect()) as con:
        return con.execute("SELECT order_id, seller_id, buyer_id, buyer_username, payment_method, trx_id, network, wallet, amount_bdt, amount_crypto, stars_amount, status, tx_sig, error, created_at, updated_at FROM seller_orders WHERE trx_id=? AND status='completed' ORDER BY datetime(updated_at) DESC, rowid DESC LIMIT 1", (str(trx_id),)).fetchone()


def find_waiting_seller_order_by_trx(seller_id, trx_id):
    with closing(connect()) as con:
        return con.execute("SELECT order_id, seller_id, buyer_id, buyer_username, payment_method, trx_id, network, wallet, amount_bdt, amount_crypto, stars_amount, status, tx_sig, error, created_at, updated_at FROM seller_orders WHERE seller_id=? AND trx_id=? AND status IN ('waiting_payment','pending_manual','paid') ORDER BY datetime(created_at) DESC LIMIT 1", (str(seller_id), str(trx_id))).fetchone()


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


init_db()
