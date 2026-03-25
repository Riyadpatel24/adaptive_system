from config import SIMULATION_MODE

from sre.synthetic_telemetry import apply_policy_effect


class ActionExecutor:

    def execute(self, action):

        mode_tag = "[SIMULATED]" if SIMULATION_MODE else "[LIVE]"

        print(
            f"\n[ACTION EXECUTION] {mode_tag}\n"
            f" type={action.action_type.value}\n"
            f" target={action.target}\n"
            f" confidence={action.confidence:.2f}\n"
            f" reason={action.reason}"
        )

        action_type = action.action_type.value
        target = action.target

        # --------------------------------
        # ACTION ROUTER
        # --------------------------------

        if action_type == "restart_service":
            return self._restart_service(target)

        elif action_type == "clear_cache":
            return self._clear_cache(target)

        elif action_type == "scale_resources":
            return self._scale_resources(target)

        elif action_type == "apply_policy":
            return self._apply_policy(target)

        elif action_type == "lockdown":
            return self._lockdown(target)

        elif action_type == "throttle_node":
            return self._apply_policy("strict")

        else:
            print("[ACTION] Unknown action type")
            return False

    # --------------------------------
    # ACTION IMPLEMENTATIONS
    # --------------------------------

    def _restart_service(self, target):
        print(f"[EXECUTOR] {'Would restart' if SIMULATION_MODE else 'Restarting'} service: {target}")
        print("[EXECUTOR] Service restarted")
        return True

    def _clear_cache(self, target):
        print(f"[EXECUTOR] {'Would clear' if SIMULATION_MODE else 'Clearing'} cache for: {target}")
        print("[EXECUTOR] Cache cleared")
        return True

    def _scale_resources(self, target):
        print(f"[EXECUTOR] {'Would scale' if SIMULATION_MODE else 'Scaling'} resources for: {target}")
        print("[EXECUTOR] Resources scaled")
        return True

    def _apply_policy(self, policy_level):
        print(f"[EXECUTOR] {'Would apply' if SIMULATION_MODE else 'Applying'} policy level: {policy_level}")
        apply_policy_effect(policy_level)
        print("[EXECUTOR] Policy applied")
        return True

    def _lockdown(self, target):
        print(f"[EXECUTOR] {'Would initiate' if SIMULATION_MODE else 'Initiating'} lockdown for: {target}")
        apply_policy_effect("lockdown")
        print("[EXECUTOR] Lockdown complete — service isolated.")
        return True