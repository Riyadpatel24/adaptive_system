from analysis.recovery.risk_decay import apply_decay
from analysis.recovery.cooldown_manager import CooldownManager

RISK_STABLE_THRESHOLD = 0.5
RECOVERY_PERSISTENCE_THRESHOLD = 2


class RecoveryEngine:
    def __init__(self):
        self.cooldown = CooldownManager()

    def evaluate_recovery(self, entity_state: dict) -> str:
        """
        Decide if entity is recovering.
        """
        trend = entity_state.get("trend")
        persistence = entity_state.get("persistence", 0)

        if trend in ("stable", "improving") and persistence >= RECOVERY_PERSISTENCE_THRESHOLD:
            return "recovering"
        if trend == "worsening":
            return "worsening"
        return "none"

    def decay_risk(self, entity_state: dict):
        entity_state["risk"] = apply_decay(
            entity_state["risk"],
            entity_state.get("trend", "stable")
        )

    def maybe_deescalate_policy(self, snapshot):
        """
        Lower system mode when overall risk is low.
        """
        system_risk = snapshot.system.get("risk", 0)

        if system_risk < RISK_STABLE_THRESHOLD:
            snapshot.system["mode"] = "normal"
