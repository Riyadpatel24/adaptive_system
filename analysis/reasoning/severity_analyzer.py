class SeverityAnalyzer:
    def __init__(self):
        pass

    def classify(self, failure_rate):
        if failure_rate < 0.3:
            return "LOW"
        elif failure_rate < 0.6:
            return "MEDIUM"
        else:
            return "HIGH"
