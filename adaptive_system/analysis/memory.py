import json
import os
from datetime import datetime, timedelta

class Memory:
    def __init__(self, path="storage/memory.json"):
        self.path = path
        if not os.path.exists(self.path):
            with open(self.path, "w") as f:
                json.dump({"history": [], "policy_history": []}, f)

    def load(self):
        with open(self.path, "r") as f:
            return json.load(f)

    def save(self, data):
        with open(self.path, "w") as f:
            json.dump(data, f, indent=4)

    def record_state(self, metrics, policy):
        data = self.load()

        data["history"].append({
            "timestamp": datetime.now().isoformat(),
            "metrics": metrics
        })

        data["policy_history"].append({
            "timestamp": datetime.now().isoformat(),
            "policy": policy
        })

    def record_policy_outcome(self, context_signature, policy, before_rate, after_rate):
        data = self.load()

        effectiveness = before_rate - after_rate

        data.setdefault("policy_outcomes", []).append({
            "context": context_signature,
            "policy": policy["response_level"],
            "before_failure_rate": before_rate,
            "after_failure_rate": after_rate,
            "effectiveness": effectiveness
        })

    def record_policy_outcome(self, policy, risk_before, risk_after):
        data = self.load()

        outcomes = data.setdefault("policy_outcomes", [])
        outcomes.append({
            "policy": policy["response_level"],
            "risk_before": risk_before,
            "risk_after": risk_after,
            "improvement": round(risk_before - risk_after, 3)
        })

    def record_risk_snapshot(self, risk):
        data = self.load()

        history = data.setdefault("risk_history", [])
        history.append(risk)

        # keep last 10 snapshots only
        data["risk_history"] = history[-10:]

        self.save(data)
        
    def get_risk_trend(self):
        data = self.load()
        history = data.get("risk_history", [])

        if len(history) < 3:
            return "unknown"

        delta = history[-1] - history[0]

        if delta > 0.1:
            return "increasing"
        if delta < -0.1:
            return "decreasing"
        return "stable"
    
    def record_policy_application(self, policy_level: str):
        data = self.load()
        data["last_policy"] = {
            "level": policy_level,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.save(data)

    def is_in_cooldown(self, cooldown_seconds: int) -> bool:
        data = self.load()
        last = data.get("last_policy")

        if not last:
            return False

        last_time = datetime.fromisoformat(last["timestamp"])
        return datetime.utcnow() - last_time < timedelta(seconds=cooldown_seconds)

    def last_policy_level(self):
        data = self.load()
        last = data.get("last_policy")
        return last["level"] if last else None