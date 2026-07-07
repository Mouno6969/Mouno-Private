"""Web support ticket helpers for the Telegram bot admin inbox."""

from __future__ import annotations

import json
import time
from contextlib import closing

from db import connect

_TICKET_STATUSES = {"open", "pending", "resolved", "closed"}
_TABLES_READY = False


def _ensure_tables(con):
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS support_tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            session_id INTEGER,
            subject TEXT NOT NULL DEFAULT 'Support request',
            status TEXT NOT NULL DEFAULT 'open',
            priority TEXT NOT NULL DEFAULT 'normal',
            assigned_agent TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS ticket_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id INTEGER NOT NULL,
            sender_role TEXT NOT NULL,
            body TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            type TEXT NOT NULL DEFAULT 'info',
            title TEXT NOT NULL,
            body TEXT,
            metadata TEXT,
            dedup_ref TEXT,
            read_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )


def _prepare(con):
    global _TABLES_READY
    if not _TABLES_READY:
        _ensure_tables(con)
        _TABLES_READY = True


def _ticket_row_to_dict(row):
    return {
        "id": row[0],
        "user_id": row[1],
        "session_id": row[2],
        "subject": row[3],
        "status": row[4],
        "priority": row[5],
        "assigned_agent": row[6],
        "created_at": row[7],
        "updated_at": row[8],
    }


def list_open_support_tickets(limit=20):
    """Return open/pending tickets newest first (admin view)."""
    with closing(connect()) as con:
        _prepare(con)
        rows = con.execute(
            """
            SELECT t.id, t.user_id, t.session_id, t.subject, t.status, t.priority,
                   t.assigned_agent, t.created_at, t.updated_at, u.username
            FROM support_tickets t
            LEFT JOIN web_users u ON u.id = t.user_id
            WHERE t.status IN ('open', 'pending')
            ORDER BY datetime(t.updated_at) DESC, t.id DESC
            LIMIT ?
            """,
            (int(limit),),
        ).fetchall()
        out = []
        for row in rows:
            ticket = _ticket_row_to_dict(row[:9])
            ticket["username"] = row[9]
            out.append(ticket)
        return out


def get_support_ticket_admin(ticket_id):
    """Return a ticket with thread messages for admin (no ownership check)."""
    with closing(connect()) as con:
        _prepare(con)
        row = con.execute(
            """
            SELECT t.id, t.user_id, t.session_id, t.subject, t.status, t.priority,
                   t.assigned_agent, t.created_at, t.updated_at, u.username
            FROM support_tickets t
            LEFT JOIN web_users u ON u.id = t.user_id
            WHERE t.id=?
            """,
            (int(ticket_id),),
        ).fetchone()
        if not row:
            return None
        ticket = _ticket_row_to_dict(row[:9])
        ticket["username"] = row[9]
        msgs = con.execute(
            "SELECT sender_role, body, created_at FROM ticket_messages WHERE ticket_id=? ORDER BY id ASC",
            (int(ticket_id),),
        ).fetchall()
        ticket["messages"] = [
            {"sender_role": m[0], "body": m[1], "created_at": m[2]} for m in msgs
        ]
        return ticket


def add_agent_ticket_reply(ticket_id, body, agent_name=None):
    """Append an agent reply; mark ticket pending. Returns ticket dict or None."""
    body = (body or "").strip()
    if not body:
        return None
    with closing(connect()) as con:
        _prepare(con)
        row = con.execute(
            "SELECT id, user_id, session_id, subject, status, priority, assigned_agent, created_at, updated_at "
            "FROM support_tickets WHERE id=?",
            (int(ticket_id),),
        ).fetchone()
        if not row:
            return None
        con.execute(
            "INSERT INTO ticket_messages (ticket_id, sender_role, body) VALUES (?, 'agent', ?)",
            (int(ticket_id), body[:4000]),
        )
        updates = ["updated_at=CURRENT_TIMESTAMP", "status='pending'"]
        params = []
        if agent_name:
            updates.append("assigned_agent=?")
            params.append(str(agent_name)[:120])
        params.append(int(ticket_id))
        con.execute(
            f"UPDATE support_tickets SET {', '.join(updates)} WHERE id=?",
            params,
        )
        con.commit()
        user_row = con.execute(
            "SELECT username FROM web_users WHERE id=?",
            (int(row[1]),),
        ).fetchone()
        ticket = _ticket_row_to_dict(row)
        ticket["username"] = user_row[0] if user_row else None
        return ticket


def update_ticket_status_admin(ticket_id, status):
    """Update ticket status without ownership check."""
    if status not in _TICKET_STATUSES:
        return None
    with closing(connect()) as con:
        _prepare(con)
        row = con.execute(
            "SELECT id, user_id, session_id, subject, status, priority, assigned_agent, created_at, updated_at "
            "FROM support_tickets WHERE id=?",
            (int(ticket_id),),
        ).fetchone()
        if not row:
            return None
        con.execute(
            "UPDATE support_tickets SET status=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (status, int(ticket_id)),
        )
        con.commit()
        user_row = con.execute(
            "SELECT username FROM web_users WHERE id=?",
            (int(row[1]),),
        ).fetchone()
        ticket = _ticket_row_to_dict(row)
        ticket["username"] = user_row[0] if user_row else None
        ticket["status"] = status
        return ticket


def notify_ticket_user(web_user_id, ticket_id, body):
    """Create an in-app notification for the web user (best-effort)."""
    try:
        with closing(connect()) as con:
            _prepare(con)
            ts = int(time.time())
            con.execute(
                "INSERT INTO notifications (user_id, type, title, body, metadata, dedup_ref) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    str(web_user_id),
                    "support",
                    "Support agent replied",
                    (body or "")[:240],
                    json.dumps({"ref": f"ticket:{ticket_id}", "ticket_id": int(ticket_id)}),
                    f"ticket-reply:{ticket_id}:{ts}",
                ),
            )
            con.commit()
    except Exception:
        pass