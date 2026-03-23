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

        structured = defaultdict(lambda: defaultdict(list))

        for entity_id, metric, value in rows:
            structured[entity_id][metric].append(value)

        return structured

    def _compute_signal(self, metric, values):
        avg = mean(values)
        trend = values[0] - values[-1] if len(values) > 1 else 0

        if metric == "cpu_usage":
            if avg > 50:
                return self._signal(-0.9, "cpu_usage sustained above 50%", 0.9)
            if avg > 20:
                return self._signal(-0.6, "cpu_usage sustained above 20%", 0.7)
            if avg > 5:
                return self._signal(-0.3, "cpu_usage above 5%", 0.5)

        if metric == "memory_usage":
            if trend > 2:
                return self._signal(-0.7, "memory usage increasing", 0.8)
            if avg > 50:
                return self._signal(-0.8, "memory usage above 50%", 0.9)
            if avg > 20:
                return self._signal(-0.4, "memory usage above 20%", 0.6)

        if metric == "disk_usage":
            if avg > 70:
                return self._signal(-0.85, "disk usage above 70%", 0.85)
            if avg > 40:
                return self._signal(-0.4, "disk usage above 40%", 0.6)

        return None

    def _signal(self, value, reason, confidence):
        return {
            "value": value,
            "reason": reason,
            "confidence": confidence
        }