import time


class CooldownManager:
    def is_in_cooldown(self, entity_state: dict) -> bool:
        cooldown_until = entity_state.get("cooldown_until")
        if cooldown_until is None:
            return False
        return time.time() < cooldown_until

    def remaining(self, entity_state: dict) -> int:
        cooldown_until = entity_state.get("cooldown_until")
        if not cooldown_until:
            return 0
        return max(0, int(cooldown_until - time.time()))
