import time

from actions.action import Action, ActionType
from actions.safety_guard import ActionSafetyGuard
from actions.executor import ActionExecutor

from sre.telemetry_ingestion import ingest_synthetic_telemetry
from sre.synthetic_telemetry import generate_telemetry, apply_policy_effect

from analysis.telemetry_normalizer import TelemetryNormalizer
from analysis.signals.signal_analyzer import SignalAnalyzer
from analysis.reasoning.cognition_engine import CognitionEngine
from analysis.system_metrics import extract_metrics

from analysis.policy.policy_engine import (
    PolicyEngine,
    should_adapt,
    adapt_parameters
)

from analysis.memory import Memory
from storage.temporal_memory import TemporalMemory
from analysis.signals.time_analyzer import TemporalAnalyzer

from models.system_state import SystemState
from logger.event_logger import log_adaptation


def collect_telemetry():
    return generate_telemetry()

from models.state_snapshot import StateSnapshot
snapshot = StateSnapshot()

from api.server import set_snapshot
import threading
import uvicorn

def start_api():
    uvicorn.run(
        "api.server:app",
        host="0.0.0.0",
        port=8000,
        log_level="warning"
    )


def main():
    print("\n=== Autonomous SRE System Started ===\n")

    temporal_memory = TemporalMemory(window_size=5)
    time_analyzer = TemporalAnalyzer()

    safety_guard = ActionSafetyGuard()
    executor = ActionExecutor()

    ingest_synthetic_telemetry()
    print("Synthetic telemetry ingested.")

    normalizer = TelemetryNormalizer()
    signals = normalizer.normalize(window_size=20)

    print("\n=== Normalized Signals ===")
    for s in signals:
        print(
            f"{s['entity_id']} | {s['metric']} | "
            f"signal={s['signal']} | confidence={s['confidence']}"
        )

    analyzer = SignalAnalyzer()
    entity_health = analyzer.analyze(signals)

    print("\n=== Entity Health + Temporal Analysis ===")
    for entity_id, data in entity_health.items():
        risk = data["risk_score"]

        temporal_memory.record(entity_id, risk)
        history = temporal_memory.get_history(entity_id)
        temporal = time_analyzer.analyze(history)
        
        snapshot.update_entity(
            entity_id=entity_id,
            health=data["state"],
            risk=risk,
            trend=temporal["trend"],
            persistence=temporal["persistence"],
            volatility=temporal["volatility"]
        )

        print(
            f"{entity_id}: state={data['state']} risk={risk} | "
            f"trend={temporal['trend']} "
            f"slope={temporal['slope']} "
            f"volatility={temporal['volatility']} "
            f"persistence={temporal['persistence']}"
        )

    memory = Memory()
    cognition = CognitionEngine(memory)
    thought = cognition.reason_from_health(entity_health)

    print("\n=== Cognition ===")
    print(f"Decision Hint: {thought['decision_hint']}")
    print(f"Confidence: {thought['confidence']}")
    print("Explanation:")
    print(thought["explanation"])

    print("\n=== Action Evaluation ===")
    for entity_id, data in entity_health.items():
        history = temporal_memory.get_history(entity_id)
        temporal = time_analyzer.analyze(history)

        if thought["decision_hint"] == "lockdown":
            action = Action(
                action_type=ActionType.LOCKDOWN,
                target=entity_id,
                reason=thought["explanation"],
                confidence=thought["confidence"]
            )

            allowed, changed = safety_guard.allow(action, temporal)

            if changed:
                if allowed:
                    executor.execute(action)
                    snapshot.update_entity(
                        entity_id=entity_id,
                        health=data["state"],
                        risk=data["risk_score"],
                        trend=temporal["trend"],
                        persistence=temporal["persistence"],
                        volatility=temporal["volatility"],
                        last_action=action.action_type.value,
                        action_status="EXECUTED"
                    )
                else:
                    snapshot.update_entity(
                        entity_id=entity_id,
                        health=data["state"],
                        risk=data["risk_score"],
                        trend=temporal["trend"],
                        persistence=temporal["persistence"],
                        volatility=temporal["volatility"],
                        last_action=action.action_type.value,
                        action_status="BLOCKED"
                    )

                    print(
                        f"[ACTION BLOCKED] target={entity_id} "
                        f"trend={temporal['trend']} "
                        f"persistence={temporal['persistence']} "
                        f"volatility={temporal['volatility']}"
                    )

    risk_before = max(d["risk_score"] for d in entity_health.values())
    memory.record_risk_snapshot(risk_before)
    trend = memory.get_risk_trend()
    
    snapshot.update_system(
        risk=risk_before,
        mode="initial"
    )


    print("\n=== Risk Trend ===")
    print(trend)

    policy_engine = PolicyEngine()
    learned_policy = policy_engine.prefer_learned_policy(memory, trend)

    if learned_policy:
        policy = policy_engine.get_policy()
        policy["response_level"] = learned_policy
    else:
        policy = policy_engine.adapt_with_cognition(thought, memory)
        memory.record_policy_application(policy["response_level"])

    print("\n=== Adaptive Policy ===")
    print(policy)

    apply_policy_effect(policy["response_level"])

    ingest_synthetic_telemetry()
    signals_after = normalizer.normalize(window_size=20)
    entity_health_after = analyzer.analyze(signals_after)

    risk_after = max(d["risk_score"] for d in entity_health_after.values())
    memory.record_policy_outcome(
        policy=policy,
        risk_before=risk_before,
        risk_after=risk_after,
    )

    print("\n=== Learning Outcome ===")
    print(f"Risk before: {risk_before}")
    print(f"Risk after: {risk_after}")
    print(f"Improvement: {round(risk_before - risk_after, 3)}")

    new_level = policy_engine.recover_policy(policy, trend)
    if new_level != policy["response_level"]:
        policy["response_level"] = new_level

    print("\n=== Self-Tuning System Parameters Loop Started ===\n")

    state = SystemState()
    
    set_snapshot(snapshot)
    api_thread = threading.Thread(target=start_api, daemon=True)
    api_thread.start()

    while True:
        telemetry = collect_telemetry()
        ingest_synthetic_telemetry()

        signals = normalizer.normalize(window_size=20)
        entity_health = analyzer.analyze(signals)

        for entity_id, data in entity_health.items():
            risk = data["risk_score"]

            temporal_memory.record(entity_id, risk)
            history = temporal_memory.get_history(entity_id)
            temporal = time_analyzer.analyze(history)

            snapshot.update_entity(
                entity_id=entity_id,
                health=data["state"],
                risk=risk,
                trend=temporal["trend"],
                persistence=temporal["persistence"],
                volatility=temporal["volatility"]
            )

        if should_adapt(state):
            prev = (state.timeout_ms, state.retry_limit, state.mode)
            state = adapt_parameters(state)
            curr = (state.timeout_ms, state.retry_limit, state.mode)

            if prev != curr:
                log_adaptation(state)

        time.sleep(2)

if __name__ == "__main__":
    main()