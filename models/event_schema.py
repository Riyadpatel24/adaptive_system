class EventSchema:
    """
    Generic behavioral event schema used by the adaptive engine.
    """

    def __init__(
        self,
        entity_id: str,
        action_type: str,
        metric_value: float,
        timestamp: float,
        context: dict | None = None,
    ):
        self.entity_id = entity_id
        self.action_type = action_type
        self.metric_value = metric_value
        self.timestamp = timestamp
        self.context = context or {}

    def to_dict(self):
        return {
            "entity_id": self.entity_id,
            "action_type": self.action_type,
            "metric_value": self.metric_value,
            "timestamp": self.timestamp,
            "context": self.context,
        }