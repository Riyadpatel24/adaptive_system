import time

class ActionExecutor:
    def execute(self, action):
        print(
            f"[ACTION] type={action.action_type.value} "
            f"target={action.target} "
            f"confidence={action.confidence}"
        )
        time.sleep(0.5)
        return True
