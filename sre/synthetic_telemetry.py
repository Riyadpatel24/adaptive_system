import random
from datetime import datetime, timedelta
import psutil

from models.event import Event


# --------------------------------------------------
# TELEMETRY MODE
# --------------------------------------------------

TELEMETRY_MODE = "synthetic"
# options: "synthetic" or "real"


# --------------------------------------------------
# GLOBAL simulated system state (Actuator effects)
# --------------------------------------------------

SYSTEM_STATE = {
    "cpu_modifier": 1.0,
    "memory_modifier": 1.0,
    "disk_modifier": 1.0
}


def apply_policy_effect(policy_level: str):
    """
    Simulate effect of policy on system state.
    """

    if policy_level == "lockdown":
        SYSTEM_STATE["cpu_modifier"] = 0.5
        SYSTEM_STATE["memory_modifier"] = 0.6
        SYSTEM_STATE["disk_modifier"] = 0.7

    elif policy_level == "strict":
        SYSTEM_STATE["memory_modifier"] = 0.7

    elif policy_level == "normal":
        SYSTEM_STATE["cpu_modifier"] = 1.0
        SYSTEM_STATE["memory_modifier"] = 1.0
        SYSTEM_STATE["disk_modifier"] = 1.0


# --------------------------------------------------
# SYNTHETIC TELEMETRY GENERATOR
# --------------------------------------------------

class SyntheticTelemetryGenerator:
    """
    Generates realistic SRE telemetry as time-series data.
    """

    def __init__(self, seed: int = 42):
        random.seed(seed)

    def generate_series(
        self,
        entity_id: str,
        entity_type: str,
        duration: int,
        pattern: str,
        interval_seconds: int = 1
    ):

        metrics = ["cpu_usage", "memory_usage", "disk_usage"]

        cpu = random.uniform(85, 98) * SYSTEM_STATE["cpu_modifier"]
        memory = random.uniform(80, 95) * SYSTEM_STATE["memory_modifier"]
        disk = random.uniform(70, 95) * SYSTEM_STATE["disk_modifier"]

        current = {
            "cpu_usage": cpu,
            "memory_usage": memory,
            "disk_usage": disk
        }

        timestamp = datetime.utcnow()
        events = []

        for step in range(duration):

            for metric in metrics:

                current[metric] = self._next_value(
                    metric,
                    current[metric],
                    pattern,
                    step
                )

                events.append(
                    Event(
                        entity_id=entity_id,
                        entity_type=entity_type,
                        metric=metric,
                        value=current[metric],
                        unit="%",
                        timestamp=timestamp
                    )
                )

            timestamp += timedelta(seconds=interval_seconds)

        return events

    # --------------------------------------------------
    # PATTERN ENGINE
    # --------------------------------------------------

    def _next_value(self, metric, value, pattern, step):

        if pattern == "healthy":
            return self._healthy(value)

        if pattern == "cpu_spike" and metric == "cpu_usage":
            return self._cpu_spike(value, step)

        if pattern == "memory_leak" and metric == "memory_usage":
            return self._memory_leak(value)

        if pattern == "cascading_failure":
            return self._cascade(value, step)

        return self._healthy(value)

    def _healthy(self, value):
        return max(0, min(100, value + random.uniform(-1.5, 1.5)))

    def _cpu_spike(self, value, step):

        if step < 10:
            return min(100, value + random.uniform(5, 10))

        return max(10, value - random.uniform(8, 15))

    def _memory_leak(self, value):
        return min(100, value + random.uniform(0.5, 1.2))

    def _cascade(self, value, step):

        if step < 8:
            return min(100, value + random.uniform(2, 4))

        return min(100, value + random.uniform(6, 12))


_generator = SyntheticTelemetryGenerator()


# --------------------------------------------------
# REAL TELEMETRY MODE
# --------------------------------------------------

def get_real_metrics():

    cpu = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory().percent
    disk = psutil.disk_usage('/').percent

    return {
        "avg_latency": cpu * 2,
        "failure_rate": max(0, (cpu - 80) / 20),
        "success_rate": 1 - max(0, (cpu - 80) / 20)
    }


# --------------------------------------------------
# TELEMETRY API
# --------------------------------------------------

def generate_telemetry(pattern="healthy"):
    """
    Unified telemetry interface.
    """

    if TELEMETRY_MODE == "real":
        return get_real_metrics()

    # Synthetic mode
    events = _generator.generate_series(
        entity_id="system",
        entity_type="node",
        duration=1,
        pattern=pattern
    )

    cpu = next(e.value for e in reversed(events) if e.metric == "cpu_usage")
    memory = next(e.value for e in reversed(events) if e.metric == "memory_usage")
    disk = next(e.value for e in reversed(events) if e.metric == "disk_usage")

    return {
        "avg_latency": cpu * 2,
        "failure_rate": max(0, (cpu - 80) / 20),
        "success_rate": 1 - max(0, (cpu - 80) / 20)
    }