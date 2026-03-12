import sqlite3
from collections import defaultdict
from statistics import mean
from config import DB_PATH


class TelemetryNormalizer:
    """
    Converts raw SRE telemetry into normalized signals.
    """

    def __init__(self):
        self.db_path = DB_PATH

    def normalize(self, window_size=10):
        """
        Reads telemetry from DB and returns normalized signals.
        """
        data = self._load_recent_telemetry(window_size)
        signals = []

        for entity_id, metrics in data.items():
            for metric, values in metrics.items():
                result = self._compute_signal(metric, values)

                if result:
                    signals.append({
                        "entity_id": entity_id,
                        "metric": metric,
                        "signal": result["value"],
                        "confidence": result["confidence"],
                        "reason": result["reason"]
                    })

        return signals

    # --------------------------------------------------
    # Internal helpers
    # --------------------------------------------------
    def _load_recent_telemetry(self, window_size):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT entity_id, metric, value
            FROM events
            ORDER BY timestamp DESC
            LIMIT ?
        """, (window_size * 10,))

        rows = cursor.fetchall()
        conn.close()

        data = defaultdict(list)
        structured = defaultdict(lambda: defaultdict(list))

        for entity_id, metric, value in rows:
            structured[entity_id][metric].append(value)

        return structured

    def _compute_signal(self, metric, values):
        avg = mean(values)
        trend = values[0] - values[-1] if len(values) > 1 else 0

        # CPU
        if metric == "cpu_usage":
            if avg > 90:
                return self._signal(-0.9, "cpu_usage sustained above 90%", 0.9)
            if avg > 80:
                return self._signal(-0.6, "cpu_usage sustained above 80%", 0.7)

        # MEMORY
        if metric == "memory_usage":
            if trend > 5:
                return self._signal(-0.7, "memory usage increasing rapidly", 0.8)
            if avg > 85:
                return self._signal(-0.8, "memory usage critically high", 0.9)

        # DISK
        if metric == "disk_usage":
            if avg > 90:
                return self._signal(-0.85, "disk usage above 90%", 0.85)

        return None

    def _signal(self, value, reason, confidence):
        return {
            "value": value,
            "reason": reason,
            "confidence": confidence
        }
