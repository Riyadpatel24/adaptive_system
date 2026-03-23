class AnomalyDetector:

    def __init__(self, failure_threshold=0.5, latency_threshold=150):
        """
        failure_threshold → failure rate anomaly
        latency_threshold → latency anomaly
        """

        self.failure_threshold = failure_threshold
        self.latency_threshold = latency_threshold


    def detect(self, summary):

        anomalies = []

        for actor, data in summary.items():

            total = data.get("total", 0)
            failures = data.get("failure", 0)
            latency = data.get("avg_latency", 0)

            if total == 0:
                continue

            failure_rate = failures / total

            # ------------------------------------------------
            # Failure anomaly
            # ------------------------------------------------
            if failure_rate > self.failure_threshold:

                severity = "CRITICAL" if failure_rate > 0.8 else "WARNING"

                anomalies.append({
                    "actor": actor,
                    "issue": "high_failure_rate",
                    "failure_rate": round(failure_rate, 3),
                    "severity": severity
                })


            # ------------------------------------------------
            # Latency anomaly
            # ------------------------------------------------
            if latency > self.latency_threshold:

                severity = "CRITICAL" if latency > self.latency_threshold * 1.5 else "WARNING"

                anomalies.append({
                    "actor": actor,
                    "issue": "high_latency",
                    "latency": latency,
                    "severity": severity
                })


        return anomalies