class ActionSafetyGuard:
    def allow(self, action, temporal):
        # Do NOT act if system is recovering
        if temporal["trend"] == "improving":
            return False, False

        # Need enough evidence
        if temporal["persistence"] < 3:
            return False, False

        # Avoid acting on noisy data
        if temporal["volatility"] > 0.2:
            return False, False

        # Action is allowed and meaningful
        return True, True
