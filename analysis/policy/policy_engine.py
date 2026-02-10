class PolicyEngine:
    def __init__(self):
        self.base_policy = {
            "max_failure_rate": 0.5,
            "response_level": "normal",
            "cooldown_time": 5
        }

    def get_policy(self):
        return self.base_policy.copy()

    # -----------------------------
    # Cognition-aware adaptation
    # -----------------------------
    def adapt_with_cognition(self, thought, memory=None):
        policy = self.base_policy.copy()

        # Base decision from cognition
        if thought["decision_hint"] == "lockdown":
            policy["response_level"] = "lockdown"
            policy["cooldown_time"] = 30

        elif thought["decision_hint"] == "strict":
            policy["response_level"] = "strict"
            policy["cooldown_time"] = 15

        else:
            policy["response_level"] = "normal"
            policy["cooldown_time"] = 5

        # Cooldown enforcement
        if memory and policy["response_level"] == "lockdown":
            if memory.is_in_cooldown(policy["cooldown_time"]):
                policy["response_level"] = "strict"

        return policy

    # -----------------------------
    # Learning: prefer policies that worked
    # -----------------------------
    def prefer_learned_policy(self, memory, trend):
        data = memory.load()
        outcomes = data.get("policy_outcomes", [])

        if not outcomes:
            return None

        relevant = [
            o for o in outcomes
            if "improvement" in o and o["improvement"] > 0
        ]

        if not relevant:
            return None

        scores = {}
        for o in relevant:
            scores.setdefault(o["policy"], []).append(o["improvement"])

        best_policy = max(
            scores.items(),
            key=lambda x: sum(x[1]) / len(x[1])
        )[0]

        return best_policy

    # -----------------------------
    # Gradual recovery (optional)
    # -----------------------------
    def recover_policy(self, current_policy, trend):
        level = current_policy["response_level"]

        if trend == "decreasing":
            if level == "lockdown":
                return "strict"
            if level == "strict":
                return "normal"

        return level
    
def should_adapt(state):
    if state.mode in ("frozen", "stable"):
        return False
    return True

def adapt_parameters(state):
    if state.mode == "stable":
        state.last_change = "no_change"
        return state

    state.adaptation_count += 1

    if state.avg_response_time > state.timeout_ms:
        state.timeout_ms = int(state.timeout_ms * 1.1)
        state.last_change = "timeout_increased"

    elif state.failure_rate < 0.05 and state.retry_limit > 1:
        state.retry_limit -= 1
        state.last_change = "retry_decreased"

    if state.success_rate > 0.95:
        state.mode = "stable"

    if state.adaptation_count > 20:
        state.mode = "frozen"

    return state
