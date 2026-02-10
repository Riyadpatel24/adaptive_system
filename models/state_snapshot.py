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
        action_status=None
    ):
        self.entities[entity_id] = {
            "health": health,
            "risk": risk,
            "trend": trend,
            "persistence": persistence,
            "volatility": volatility,
            "last_action": last_action,
            "action_status": action_status
        }

    def update_system(self, risk, mode):
        self.system = {
            "risk": risk,
            "mode": mode,
            "timestamp": self.timestamp
        }

    def to_dict(self):
        return {
            "timestamp": self.timestamp,
            "system": self.system,
            "entities": self.entities
        }
