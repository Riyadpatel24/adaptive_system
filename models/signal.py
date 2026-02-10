class Signal:
    def __init__(self, entity_id, entity_type, metric, value, confidence):
        self.entity_id = entity_id
        self.entity_type = entity_type
        self.metric = metric
        self.value = value          # normalized (-1 to +1)
        self.confidence = confidence
