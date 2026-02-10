class AnomalyDetector:
    def __init__(self, threshold=2):
        self.threshold = threshold
        
    def detect(self, summary):
        anomalies = []
        
        for actor, data in summary.items():
            total = data["total"]
            failures = data["failure"]
            
            if total == 0:
                continue
            
            failure_rate = failures / total
            
            if failure_rate > 0.5:
                anomalies.append({
                    "actor": actor,
                    "issue": "high_failure_rate",
                    "failure_rate": failure_rate,
                })

        return anomalies   # ✅ OUTSIDE the loop