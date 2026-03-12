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
