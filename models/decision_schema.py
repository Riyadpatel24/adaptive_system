class DecisionSchema:
    """
    Standard decision output from the adaptive engine.
    """

    def __init__(
        self,
        risk_score: float,
        confidence: float,
        recommended_action: str,
        severity: str,
    ):
        self.risk_score = risk_score
        self.confidence = confidence
        self.recommended_action = recommended_action
        self.severity = severity

    def to_dict(self):
        return {
            "risk_score": self.risk_score,
            "confidence": self.confidence,
            "recommended_action": self.recommended_action,
            "severity": self.severity,
        }