from logger.event_logger import EventLogger
from sre.synthetic_telemetry import SyntheticTelemetryGenerator


def ingest_synthetic_telemetry():
    """
    Generates synthetic SRE telemetry and persists it via EventLogger.
    This is the ONLY place where telemetry is generated and logged.
    """

    logger = EventLogger()
    generator = SyntheticTelemetryGenerator(seed=42)

    # Define entities (opaque identifiers)
    entities = [
        ("node-1", "node", "healthy"),
        ("node-2", "node", "cpu_spike"),
        ("proc-auth", "process", "memory_leak"),
        ("proc-cache", "process", "cascading_failure"),
    ]

    for entity_id, entity_type, pattern in entities:
        events = generator.generate_series(
            entity_id=entity_id,
            entity_type=entity_type,
            duration=60,          # 60 time steps
            pattern=pattern,
            interval_seconds=1
        )

        for event in events:
            logger.log_event(event)
