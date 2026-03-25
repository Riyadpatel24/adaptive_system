from logger.event_logger import EventLogger
from sre.synthetic_telemetry import SyntheticTelemetryGenerator, get_real_metrics
from config import TELEMETRY_MODE
from models.event import Event
from datetime import datetime


def ingest_synthetic_telemetry(telemetry=None):
    """
    Ingests telemetry and persists it via EventLogger.
    Mode is controlled by TELEMETRY_MODE in config.py:
      "synthetic" — generates fake SRE scenarios
      "real"      — reads actual processes + Flask server
    """

    logger = EventLogger()

    if TELEMETRY_MODE == "real":
        _ingest_real(logger, telemetry)
    else:
        _ingest_synthetic(logger)


def _ingest_synthetic(logger):
    """Generate and log synthetic telemetry for fake entities."""

    generator = SyntheticTelemetryGenerator(seed=42)

    entities = [
        ("node-1",     "node",    "healthy"),
        ("node-2",     "node",    "cpu_spike"),
        ("proc-auth",  "process", "memory_leak"),
        ("proc-cache", "process", "cascading_failure"),
    ]

    for entity_id, entity_type, pattern in entities:
        events = generator.generate_series(
            entity_id=entity_id,
            entity_type=entity_type,
            duration=60,
            pattern=pattern,
            interval_seconds=1
        )
        for event in events:
            logger.log_event(event)


def _ingest_real(logger, metrics=None):
    if metrics is None:
        metrics = get_real_metrics()
        
    now = datetime.utcnow()

    metric_map = {
        "cpu": "cpu_usage",
        "memory": "memory_usage",
        "disk": "disk_usage"
    }

    for entity_id, values in metrics.items():
        for metric_name, value in values.items():
            mapped = metric_map.get(metric_name, metric_name)
            event = Event(
                entity_id=entity_id,
                entity_type="process" if entity_id.startswith("proc-") else "server",
                metric=mapped,
                value=float(value),
                unit="%",
                timestamp=now
            )
            logger.log_event(event)