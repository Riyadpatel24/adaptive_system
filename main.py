import time
import threading
import uvicorn

from actions.action import Action, ActionType
from actions.safety_guard import ActionSafetyGuard
from actions.executor import ActionExecutor

from analysis.recovery.recovery_engine import RecoveryEngine
from analysis.recovery.cooldown_manager import CooldownManager

from sre.telemetry_ingestion import ingest_synthetic_telemetry
from sre.synthetic_telemetry import generate_telemetry, apply_policy_effect

from analysis.telemetry_normalizer import TelemetryNormalizer
from analysis.signals.signal_analyzer import SignalAnalyzer
from analysis.reasoning.cognition_engine import CognitionEngine

from analysis.reasoning.dependency_graph import DependencyGraph
from analysis.reasoning.root_cause_engine import RootCauseEngine
from analysis.reasoning.failure_predictor import FailurePredictor

from analysis.policy.policy_engine import (
    PolicyEngine,
    should_adapt,
    adapt_parameters
)

from analysis.memory import Memory
from storage.temporal_memory import TemporalMemory
from analysis.signals.time_analyzer import TemporalAnalyzer

from models.system_state import SystemState
from models.state_snapshot import StateSnapshot

from logger.event_logger import log_adaptation
from api.server import set_snapshot


ACTION_COOLDOWN_SECONDS = 30


def start_api():
    uvicorn.run(
        "api.server:app",
        host="0.0.0.0",
        port=8000,
        log_level="warning"
    )


def collect_telemetry():
    return generate_telemetry()


def main():

    print("\n=== Autonomous SRE System Started ===\n")

    snapshot = StateSnapshot()

    temporal_memory = TemporalMemory(window_size=5)
    time_analyzer = TemporalAnalyzer()

    recovery_engine = RecoveryEngine()
    cooldown_manager = CooldownManager()

    safety_guard = ActionSafetyGuard()
    executor = ActionExecutor()

    memory = Memory()

    normalizer = TelemetryNormalizer()
    analyzer = SignalAnalyzer()

    cognition = CognitionEngine(memory)
    policy_engine = PolicyEngine()

    # NEW ENGINES
    dependency_graph = DependencyGraph()
    root_cause_engine = RootCauseEngine(dependency_graph)
    failure_predictor = FailurePredictor()

    state = SystemState()

    ingest_synthetic_telemetry()

    set_snapshot(snapshot)
    api_thread = threading.Thread(target=start_api, daemon=True)
    api_thread.start()

    print("\n=== Self-Tuning System Loop Started ===\n")

    while True:

        telemetry = collect_telemetry()
        ingest_synthetic_telemetry()

        signals = normalizer.normalize(window_size=20)
        entity_health = analyzer.analyze(signals)

        # -----------------------------
        # ENTITY ANALYSIS
        # -----------------------------

        for entity_id, data in entity_health.items():

            risk = data["risk_score"]

            temporal_memory.record(entity_id, risk)
            history = temporal_memory.get_history(entity_id)
            temporal = time_analyzer.analyze(history)

            # -----------------------------
            # FAILURE PREDICTION
            # -----------------------------

            prediction = failure_predictor.predict(history)

            snapshot.update_entity(
                entity_id=entity_id,
                health=data["state"],
                risk=risk,
                trend=temporal["trend"],
                persistence=temporal["persistence"],
                volatility=temporal["volatility"],
                predicted_risk=prediction["risk_forecast"]
            )

            # -----------------------------
            # COGNITION
            # -----------------------------

            thought = cognition.reason_from_entity(data)

            if thought["decision_hint"] == "lockdown":

                action = Action(
                    action_type=ActionType.LOCKDOWN,
                    target=entity_id,
                    reason=thought["explanation"],
                    confidence=thought["confidence"]
                )

                allowed, changed = safety_guard.allow(action, temporal)
                
                if not allowed:
                    print(f"[SAFETY] Action blocked for {entity_id} - trend={temporal['trend']}, persistence={temporal['persistence']}")
                    continue
                
                now = time.time()
                entity_state = snapshot.entities.get(entity_id, {})

                cooldown_until = entity_state.get("cooldown_until")
                last_action = entity_state.get("last_action")

                # -----------------------------
                # COOLDOWN CHECK
                # -----------------------------
                if cooldown_until and now < cooldown_until:

                    print(f"[COOLDOWN] {entity_id} action suppressed")

                    snapshot.update_entity(
                        entity_id=entity_id,
                        action_status="COOLDOWN"
                    )

                    continue

                # -----------------------------
                # PREVENT SAME ACTION LOOP
                # -----------------------------
                if last_action == action.action_type.value:

                    print(f"[SKIP] {entity_id} already in {last_action}")

                    continue

                # -----------------------------
                # EXECUTE ACTION
                # -----------------------------
                executor.execute(action)

                snapshot.update_entity(
                    entity_id=entity_id,
                    last_action=action.action_type.value,
                    action_status="EXECUTED",
                    last_action_time=now,
                    cooldown_until=now + ACTION_COOLDOWN_SECONDS
                )
        # -----------------------------
        # ROOT CAUSE ANALYSIS
        # -----------------------------

        root_cause = root_cause_engine.find_root_cause(entity_health)

        if root_cause:
            print(f"\n[ROOT CAUSE DETECTED] → {root_cause}")

        # -----------------------------
        # SYSTEM RISK
        # -----------------------------

        system_risk = max(
            (e["risk"] for e in snapshot.entities.values()),
            default=0
        )

        snapshot.update_system(
            risk=system_risk,
            mode="initial"
        )

        # -----------------------------
        # POLICY ADAPTATION
        # -----------------------------

        if should_adapt(state):

            prev = (state.timeout_ms, state.retry_limit, state.mode)

            state = adapt_parameters(state)

            curr = (state.timeout_ms, state.retry_limit, state.mode)

            if prev != curr:
                log_adaptation(state)

        time.sleep(2)


if __name__ == "__main__":
    main()