from collections import defaultdict


class SignalAnalyzer:
    """
    Aggregates normalized signals into entity-level health states.
    """

    def analyze(self, signals):
        """
        signals: list of dicts from TelemetryNormalizer

        Returns:
            dict[entity_id] -> analysis result
        """
        grouped = defaultdict(list)

        for s in signals:
            grouped[s["entity_id"]].append(s)

        results = {}

        for entity_id, entity_signals in grouped.items():
            results[entity_id] = self._analyze_entity(entity_signals)

        return results

    # --------------------------------------------------
    # INTERNAL LOGIC
    # --------------------------------------------------
    def _analyze_entity(self, signals):
        weighted_sum = 0.0
        confidence_sum = 0.0
        explanations = []

        for s in signals:
            weighted_sum += abs(s["signal"]) * s["confidence"]
            confidence_sum += s["confidence"]

            explanations.append(
                f"{s['metric']}: {s['reason']} (signal={s['signal']}, confidence={s['confidence']})"
            )

        risk = weighted_sum / confidence_sum if confidence_sum else 0.0

        state = self._classify_state(risk)

        return {
            "risk_score": round(risk, 3),
            "state": state,
            "signals": signals,
            "explanation": explanations
        }

    def _classify_state(self, risk):
        if risk >= 0.85:
            return "CRITICAL"
        if risk >= 0.6:
            return "DEGRADED"
        if risk >= 0.3:
            return "WARNING"
        return "HEALTHY"
