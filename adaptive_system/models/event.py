from datetime import datetime

class Event:
    def __init__(
        self,
        entity_id,
        entity_type,
        metric,
        value,
        unit,
        timestamp=None
    ):
        self.entity_id = entity_id
        self.entity_type = entity_type
        self.metric = metric
        self.value = float(value)
        self.unit = unit
        self.timestamp = timestamp or datetime.utcnow()

    def to_tuple(self):
        return (
            self.entity_id,
            self.entity_type,
            self.metric,
            self.value,
            self.unit,
            self.timestamp,
        )
