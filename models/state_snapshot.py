import time


class StateSnapshot:

    def __init__(self):
        self.timestamp = time.time()
        self.entities = {}
        self.system = {}

    def update_entity(self, entity_id, **fields):
        """
        Flexible entity update method.
        Allows partial updates without requiring all fields.
        """

        if entity_id not in self.entities:
            self.entities[entity_id] = {
                "health": None,
                "risk": None,
                "predicted_risk": None,
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

        # Update only provided fields
        for key, value in fields.items():
            entity[key] = value

    # -----------------------------
    # SYSTEM LEVEL STATE
    # -----------------------------

    def update_system(self, risk, mode):

        self.system = {
            "risk": risk,
            "mode": mode,
            "timestamp": time.time()
        }

    # -----------------------------
    # EXPORT SNAPSHOT
    # -----------------------------

    def to_dict(self):

        return {
            "timestamp": self.timestamp,
            "system": self.system,
            "entities": self.entities
        }