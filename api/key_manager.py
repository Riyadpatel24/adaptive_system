"""
Hybrid API Key Manager
- Admin key from .env (full access)
- User keys stored in SQLite (generated on request)
"""

import sqlite3
import secrets
import os
from datetime import datetime

DB_PATH = os.getenv("DB_PATH", "storage/events.db")
KEYS_DB_PATH = os.path.join(os.path.dirname(DB_PATH), "api_keys.db")


def get_connection():
    conn = sqlite3.connect(KEYS_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_keys_db():
    """Create the api_keys table if it doesn't exist."""
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS api_keys (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            key         TEXT    UNIQUE NOT NULL,
            name        TEXT    NOT NULL,
            created_at  TEXT    DEFAULT (datetime('now')),
            last_used   TEXT,
            use_count   INTEGER DEFAULT 0,
            is_active   INTEGER DEFAULT 1
        )
    """)
    conn.commit()
    conn.close()


def generate_key(name: str) -> dict:
    """Generate and store a new API key. Returns the key record."""
    key = secrets.token_hex(32)
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO api_keys (key, name) VALUES (?, ?)",
            (key, name)
        )
        conn.commit()
        row = conn.execute("SELECT * FROM api_keys WHERE key = ?", (key,)).fetchone()
        return dict(row)
    finally:
        conn.close()


def validate_key(key: str) -> str | None:
    """
    Returns role string if valid, None if invalid.
    Roles: 'admin' | 'user'
    """
    admin_key = os.getenv("API_KEY", "")

    # Admin key check
    if admin_key and key == admin_key:
        return "admin"

    # DB user key check
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT id FROM api_keys WHERE key = ? AND is_active = 1",
            (key,)
        ).fetchone()

        if row:
            # Update usage stats
            conn.execute(
                "UPDATE api_keys SET last_used = datetime('now'), use_count = use_count + 1 WHERE id = ?",
                (row["id"],)
            )
            conn.commit()
            return "user"
    finally:
        conn.close()

    return None


def list_keys() -> list[dict]:
    """Return all keys (without exposing the actual key value fully)."""
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT id, name, substr(key,1,8)||'...' as key_preview, created_at, last_used, use_count, is_active FROM api_keys ORDER BY id DESC"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def revoke_key(key_id: int) -> bool:
    """Deactivate a key by ID."""
    conn = get_connection()
    try:
        conn.execute("UPDATE api_keys SET is_active = 0 WHERE id = ?", (key_id,))
        conn.commit()
        return conn.total_changes > 0
    finally:
        conn.close()


def delete_key(key_id: int) -> bool:
    """Permanently delete a key by ID."""
    conn = get_connection()
    try:
        conn.execute("DELETE FROM api_keys WHERE id = ?", (key_id,))
        conn.commit()
        return conn.total_changes > 0
    finally:
        conn.close()