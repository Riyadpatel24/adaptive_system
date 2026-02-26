import time

DEFAULT_DECAY_RATE = 0.01  # risk points per cycle
MIN_RISK = 0.0


def apply_decay(risk: float, trend: str, decay_rate: float = DEFAULT_DECAY_RATE) -> float:
    """
    Reduce risk slowly when system is not worsening.
    """
    if trend in ("stable", "recovering", "improving", "insufficient_data"):
        return max(MIN_RISK, round(risk - decay_rate, 4))
    return risk
