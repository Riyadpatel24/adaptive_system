import sqlite3

class BehaviorAnalyzer:
    def __init__(self, db_path="storage/events.db"):
        self.db_path = db_path

    def analyze(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT actor, status FROM events")
        rows = cursor.fetchall()
        conn.close()

        summary = {}

        for actor, status in rows:
            if actor not in summary:
                summary[actor] = {
                    "total": 0,
                    "success": 0,
                    "failure": 0
                }

            summary[actor]["total"] += 1
            if status == "success":
                summary[actor]["success"] += 1
            elif status == "failure":
                summary[actor]["failure"] += 1

        return summary

    def get_recent_events(self, limit=5):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT actor, status 
            FROM events 
            ORDER BY timestamp DESC 
            LIMIT ?
        """, (limit,))

        rows = cursor.fetchall()
        conn.close()

        return rows
