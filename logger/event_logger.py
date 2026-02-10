import datetime
from config import DB_PATH
import sqlite3

class EventLogger:
    def __init__(self):
        self.db_path = DB_PATH
        self._create_table()


    def _create_table(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_id TEXT,
                entity_type TEXT,
                metric TEXT,
                value REAL,
                unit TEXT,
                timestamp TEXT
            )
        """)

        conn.commit()
        conn.close()

    def log_event(self, event):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO events (
                entity_id,
                entity_type,
                metric,
                value,
                unit,
                timestamp
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            event.to_tuple()
        )

        conn.commit()
        conn.close()
        
    # --------------------------------------------------
# Module-level adaptation logger (for system loop)
# --------------------------------------------------

def log_adaptation(state):
    from datetime import datetime

    timestamp = datetime.utcnow().isoformat()

    print(
        f"[{timestamp}] ADAPTATION | "
        f"timeout_ms={state.timeout_ms} | "
        f"retry_limit={state.retry_limit} | "
        f"mode={state.mode} | "
        f"change={state.last_change}"
    )
