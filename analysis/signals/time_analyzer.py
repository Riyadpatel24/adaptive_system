class TimeBasedAnalyzer:
    def __init__(self, window_size=5):
        self.window_size = window_size

    def analyze(self, events):
        """
        events: list of (actor, status) tuples ordered by time
        """
        recent = events[-self.window_size:]

        if not recent:
            return None

        total = len(recent)
        failures = sum(1 for _, status in recent if status == "failure")

        failure_rate = failures / total

        return {
            "window_size": total,
            "failure_rate": failure_rate
        }

import statistics

class TemporalAnalyzer:
    def analyze(self, history):
        if len(history) < 3:
            return {
                "trend": "insufficient_data",
                "slope": 0.0,
                "volatility": 0.0,
                "persistence": len(history)
            }

        times, risks = zip(*history)

        slope = risks[-1] - risks[0]
        volatility = statistics.pstdev(risks)
        persistence = sum(1 for r in risks if r > 0.7)

        if slope > 0.05:
            trend = "worsening"
        elif slope < -0.05:
            trend = "improving"
        else:
            trend = "stable"

        return {
            "trend": trend,
            "slope": round(slope, 3),
            "volatility": round(volatility, 3),
            "persistence": persistence
        }