class BaselineModel:
    def __init__(self, summary):
        self.summary = summary
        self.baseline = {}

    def build_baseline(self):
        for actor, data in self.summary.items():
            total = data["total"]
            failures = data["failure"]

            if total == 0:
                continue

            failure_rate = failures / total

            self.baseline[actor] = {
                "avg_events": total,
                "failure_rate": round(failure_rate, 2)
            }

        return self.baseline
