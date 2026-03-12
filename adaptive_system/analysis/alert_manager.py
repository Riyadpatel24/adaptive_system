def generate_alert(actor, severity):
    if severity == "LOW":
        return f"[INFO] {actor} operating normally."

    elif severity == "MEDIUM":
        return f"[WARNING] {actor} showing abnormal behavior."

    elif severity == "HIGH":
        return f"[ALERT] {actor} is in CRITICAL state!"

    else:
        return f"[UNKNOWN] {actor} status unclear."
