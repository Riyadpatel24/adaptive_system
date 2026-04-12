"""
api/key_manager.py
Hybrid API Key Manager
 - Admin key: from .env (API_KEY) — full access
 - User keys: generated on demand, stored in SQLite
"""

import sqlite3
import secrets
import os

# Store user keys in a sidecar DB next to events.db
_DB_DIR  = os.path.dirname(os.getenv("DB_PATH", "storage/events.db"))
KEYS_DB  = os.path.join(_DB_DIR, "api_keys.db")


def _conn():
    c = sqlite3.connect(KEYS_DB)
    c.row_factory = sqlite3.Row
    return c


def init_keys_db():
    """Create table on startup if it doesn't already exist."""
    os.makedirs(_DB_DIR, exist_ok=True)
    with _conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS api_keys (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                key        TEXT    UNIQUE NOT NULL,
                name       TEXT    NOT NULL,
                created_at TEXT    DEFAULT (datetime('now')),
                last_used  TEXT,
                use_count  INTEGER DEFAULT 0,
                is_active  INTEGER DEFAULT 1
            )
        """)
        c.commit()


def generate_key(name: str) -> dict:
    """Generate a new user key, persist it, return the full record."""
    key = secrets.token_hex(32)
    with _conn() as c:
        c.execute("INSERT INTO api_keys (key, name) VALUES (?, ?)", (key, name))
        c.commit()
        row = c.execute("SELECT * FROM api_keys WHERE key = ?", (key,)).fetchone()
        return dict(row)


def validate_key(key: str) -> str | None:
    """
    Return the role for a valid key, or None if invalid.
    Roles: 'admin' | 'user'
    """
    # 1. Check admin key from environment
    admin_key = os.getenv("API_KEY", "")
    if admin_key and key == admin_key:
        return "admin"

    # 2. Check user keys in DB
    with _conn() as c:
        row = c.execute(
            "SELECT id FROM api_keys WHERE key = ? AND is_active = 1", (key,)
        ).fetchone()
        if row:
            c.execute(
                "UPDATE api_keys SET last_used = datetime('now'), use_count = use_count + 1 WHERE id = ?",
                (row["id"],)
            )
            c.commit()
            return "user"

    return None


def list_keys() -> list[dict]:
    """Return all keys with a partial preview (first 8 chars + …)."""
    with _conn() as c:
        rows = c.execute("""
            SELECT
                id,
                name,
                substr(key, 1, 8) || '...' AS key_preview,
                created_at,
                last_used,
                use_count,
                is_active
            FROM api_keys
            ORDER BY id DESC
        """).fetchall()
        return [dict(r) for r in rows]


def revoke_key(key_id: int) -> bool:
    """Soft-delete: deactivate a key by ID."""
    with _conn() as c:
        c.execute("UPDATE api_keys SET is_active = 0 WHERE id = ?", (key_id,))
        c.commit()
        return c.total_changes > 0


def delete_key(key_id: int) -> bool:
    """Hard-delete a key by ID."""
    with _conn() as c:
        c.execute("DELETE FROM api_keys WHERE id = ?", (key_id,))
        c.commit()
        return c.total_changes > 0