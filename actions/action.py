from enum import Enum

class ActionType(Enum):
    NONE = "none"
    LOCKDOWN = "lockdown"
    RESTART_PROCESS = "restart_process"
    THROTTLE_NODE = "throttle_node"
    ISOLATE_NODE = "isolate_node"


class Action:
    def __init__(self, action_type, target, reason, confidence):
        self.action_type = action_type
        self.target = target
        self.reason = reason
        self.confidence = confidence
