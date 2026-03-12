"""
Autonomous SRE System
Main Control Loop
"""

from analysis import memory
from sre.telemetry_ingestion import ingest_synthetic_telemetry
from analysis.telemetry_normalizer import TelemetryNormalizer
from analysis.signal_analyzer import SignalAnalyzer
from analysis.cognition_engine import CognitionEngine
from analysis.policy_engine import PolicyEngine
from analysis.memory import Memory

def main():
    # 1. Ingest synthetic telemetry
    ingest_synthetic_telemetry()
    print("Synthetic telemetry ingested.")

    # 2. Normalize telemetry → signals
    normalizer = TelemetryNormalizer()
    signals = normalizer.normalize(window_size=20)

    print("\n=== Normalized Signals ===")
    for s in signals:
        print(
            f"{s['entity_id']} | {s['metric']} | "
            f"signal={s['signal']} | confidence={s['confidence']}"
        )

    # 3. Analyze signals → entity health
    analyzer = SignalAnalyzer()
    entity_health = analyzer.analyze(signals)

    print("\n=== Entity Health ===")
    for entity, data in entity_health.items():
        print(f"{entity}: state={data['state']} risk={data['risk_score']}")

    # 4. Cognition (reasoning)
    memory = Memory()
    cognition = CognitionEngine(memory)

    thought = cognition.reason_from_health(entity_health)

    print("\n=== Cognition ===")
    print(f"Decision Hint: {thought['decision_hint']}")
    print(f"Confidence: {thought['confidence']}")
    print("Explanation:")
    print(thought["explanation"])

    # 5. Risk snapshot + trend 
    risk_before = max(d["risk_score"] for d in entity_health.values())

    memory.record_risk_snapshot(risk_before)
    trend = memory.get_risk_trend()

    print("\n=== Risk Trend ===")
    print(trend)

    # 6. Policy decision 
    policy_engine = PolicyEngine()

    learned = policy_engine.prefer_learned_policy(memory, trend)

    if learned:
        policy = policy_engine.policy
        policy["response_level"] = learned
        print("\n=== Learned Policy Preference Applied ===")
    else:
        policy = policy_engine.adapt_with_cognition(thought, memory)
        memory.record_policy_application(policy["response_level"])


    print("\n=== Adaptive Policy ===")
    print(policy)
    
    from sre.synthetic_telemetry import apply_policy_effect
    apply_policy_effect(policy["response_level"])

    # 7. Learning outcome (after action)
    ingest_synthetic_telemetry()

    signals_after = normalizer.normalize(window_size=20)
    entity_health_after = analyzer.analyze(signals_after)

    risk_after = max(d["risk_score"] for d in entity_health_after.values())

    memory.record_policy_outcome(
        policy=policy,
        risk_before=risk_before,
        risk_after=risk_after
    )

    print("\n=== Learning Outcome ===")
    print(f"Risk before: {risk_before}")
    print(f"Risk after: {risk_after}")
    print(f"Improvement: {round(risk_before - risk_after, 3)}")

    # 8. Recovery step (NEW)
    new_level = policy_engine.recover_policy(policy, trend)

    if new_level != policy["response_level"]:
        print("\n=== Recovery Action ===")
        print(f"De-escalating policy: {policy['response_level']} → {new_level}")
        policy["response_level"] = new_level



if __name__ == "__main__":
    main()
