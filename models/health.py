from enum import Enum

class HealthState(Enum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    CRITICAL = "CRITICAL"

class EntityHealth:
    def __init__(self, entity_id, entity_type, risk, state):
        self.entity_id = entity_id
        self.entity_type = entity_type
        self.risk = risk            # 0.0 → 1.0
        self.state = state
