import sqlite3
from datetime import datetime
from config import DB_PATH


class EventLogger:

    def __init__(self):

        self.db_path = DB_PATH
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()

        self._create_table()

    # --------------------------------------------------
    # TABLE SETUP
    # --------------------------------------------------

    def _create_table(self):

        self.cursor.execute("""
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

        # useful indexes for faster queries
        self.cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_metric ON events(metric)"
        )

        self.cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_timestamp ON events(timestamp)"
        )

        self.conn.commit()

    # --------------------------------------------------
    # LOG EVENT
    # --------------------------------------------------

    def log_event(self, event):

        self.cursor.execute(
            """
            INSERT INTO events (
                entity_id,
                entity_type,
                metric,
                value,
                unit,
                timestamp
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            event.to_tuple()
        )

        self.conn.commit()

    # --------------------------------------------------
    # QUERY FUNCTIONS
    # --------------------------------------------------

    def get_recent_events(self, limit=50):

        self.cursor.execute(
            """
            SELECT * FROM events
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            (limit,)
        )

        return self.cursor.fetchall()

    def get_metric_history(self, metric, limit=100):

        self.cursor.execute(
            """
            SELECT value, timestamp
            FROM events
            WHERE metric = ?
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            (metric, limit)
        )

        return self.cursor.fetchall()

    # --------------------------------------------------
    # CLOSE CONNECTION
    # --------------------------------------------------

    def close(self):

        self.conn.close()


# --------------------------------------------------
# SYSTEM ADAPTATION LOGGER
# --------------------------------------------------

def log_adaptation(state):

    timestamp = datetime.utcnow().isoformat()

    print(
        f"[{timestamp}] ADAPTATION | "
        f"timeout_ms={state.timeout_ms} | "
        f"retry_limit={state.retry_limit} | "
        f"mode={state.mode} | "
        f"change={state.last_change}"
    )