import time


class StateSnapshot:
    def __init__(self):
        self.timestamp = time.time()
        self.entities = {}
        self.system = {}

    def update_entity(
        self,
        entity_id,
        health,
        risk,
        trend,
        persistence,
        volatility,
        last_action=None,
        action_status=None,
        last_action_time=None,
        cooldown_until=None,
        recovery_state=None,
        cooldown_remaining=None
    ):
        # Initialize entity only once
        if entity_id not in self.entities:
            self.entities[entity_id] = {
                "health": None,
                "risk": None,
                "trend": None,
                "persistence": None,
                "volatility": None,
                "last_action": None,
                "action_status": None,
                "last_action_time": None,
                "cooldown_until": None,
                "recovery_state": None,
                "cooldown_remaining": 0
            }

        entity = self.entities[entity_id]

        # Always update live health signals
        entity["health"] = health
        entity["risk"] = risk
        entity["trend"] = trend
        entity["persistence"] = persistence
        entity["volatility"] = volatility

        # Update action-related fields ONLY if provided
        if last_action is not None:
            entity["last_action"] = last_action

        if action_status is not None:
            entity["action_status"] = action_status

        if last_action_time is not None:
            entity["last_action_time"] = last_action_time

        if cooldown_until is not None:
            entity["cooldown_until"] = cooldown_until

        # Phase 4 recovery fields
        if recovery_state is not None:
            entity["recovery_state"] = recovery_state

        if cooldown_remaining is not None:
            entity["cooldown_remaining"] = cooldown_remaining

    def update_system(self, risk, mode):
        self.system = {
            "risk": risk,
            "mode": mode,
            "timestamp": time.time()
        }

    def to_dict(self):
        return {
            "timestamp": self.timestamp,
            "system": self.system,
            "entities": self.entities
        }
