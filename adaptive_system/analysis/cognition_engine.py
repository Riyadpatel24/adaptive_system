class CognitionEngine:
    def __init__(self, memory):
        """
        memory: instance of Memory class
        """
        self.memory = memory

    def build_context(self, anomalies, metrics, time_analysis):
        """
        Combine all perception signals into a single context object
        """
        return {
            "anomalies": anomalies,
            "metrics": metrics,
            "time_analysis": time_analysis
        }

    def reason(self, context):
        """
        Perform basic reasoning over the current context.

        Returns:
        {
            decision_hint: str
            confidence: float (0–1)
            explanation: str
        }
        """

        # Rule 1: System under stress
        if context["metrics"]["cpu_usage"] > 80:
            return {
                "decision_hint": "reduce_load",
                "confidence": 0.6,
                "explanation": "High CPU usage detected"
            }

        if context["metrics"]["memory_usage"] > 80:
            return {
                "decision_hint": "cleanup_memory",
                "confidence": 0.6,
                "explanation": "High memory usage detected"
            }

        # Rule 2: Repeated failures in short time window
        if context["time_analysis"] and context["time_analysis"]["failure_rate"] > 0.5:
            return {
                "decision_hint": "strict_mode",
                "confidence": 0.7,
                "explanation": "High recent failure rate detected"
            }

        # Default: no strong reasoning signal
        return {
            "decision_hint": "observe",
            "confidence": 0.4,
            "explanation": "No dominant failure pattern identified"
        }

    def reason_from_health(self, entity_health):
        """
        entity_health: output from SignalAnalyzer
        Returns a cognition decision dict.
        """
        worst = None
        for entity, data in entity_health.items():
            if worst is None or data["risk_score"] > worst["risk_score"]:
                worst = {
                    "entity": entity,
                    "risk_score": data["risk_score"],
                    "state": data["state"],
                    "explanation": data["explanation"],
                }

        if not worst:
            return {
                "decision_hint": "observe",
                "confidence": 0.2,
                "explanation": "No significant risk detected"
            }

        if worst["state"] == "CRITICAL":
            return {
                "decision_hint": "lockdown",
                "confidence": min(1.0, worst["risk_score"]),
                "explanation": f"{worst['entity']} is CRITICAL due to: " + "; ".join(worst["explanation"])
            }

        if worst["state"] == "DEGRADED":
            return {
                "decision_hint": "strict_mode",
                "confidence": min(1.0, worst["risk_score"]),
                "explanation": f"{worst['entity']} is DEGRADED due to: " + "; ".join(worst["explanation"])
            }

        return {
            "decision_hint": "observe",
            "confidence": 0.4,
            "explanation": "System health acceptable"
        }
