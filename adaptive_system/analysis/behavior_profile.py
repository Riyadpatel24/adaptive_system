class BehaviorProfile:
    def __init__(self, summary):
        self.summary = summary
        self.profile = {}

    def build(self):
        for actor, data in self.summary.items():
            total = data["total"]
            failures = data["failure"]

            failure_rate = failures / total if total > 0 else 0

            self.profile[actor] = {
                "avg_events": total,
                "failure_rate": round(failure_rate, 2)
            }

        return self.profile