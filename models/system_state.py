class SystemState:
    def __init__(self):
        # Tunable parameters
        self.timeout_ms = 200
        self.retry_limit = 2
        self.priority_weight = 1.0

        # Performance metrics
        self.avg_response_time = 0.0
        self.failure_rate = 0.0
        self.success_rate = 0.0

        # Adaptation control
        self.adaptation_count = 0
        self.mode = "learning"   # learning | stable | frozen
        self.last_change = None
