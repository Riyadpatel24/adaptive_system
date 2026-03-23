import os

# ----------------------------------------------------------
# STORAGE
# ----------------------------------------------------------
DB_PATH = os.getenv("DB_PATH", "storage/events.db")
MEMORY_PATH = os.getenv("MEMORY_PATH", "storage/memory.json")

# ----------------------------------------------------------
# TELEMETRY
# options: "synthetic" | "real"
# ----------------------------------------------------------
TELEMETRY_MODE = os.getenv("TELEMETRY_MODE", "synthetic")

# ----------------------------------------------------------
# SIMULATION MODE
# When True, actions are printed but not actually executed.
# ----------------------------------------------------------
SIMULATION_MODE = os.getenv("SIMULATION_MODE", "true").lower() == "true"

# ----------------------------------------------------------
# ACTION COOLDOWN
# ----------------------------------------------------------
ACTION_COOLDOWN_SECONDS = int(os.getenv("ACTION_COOLDOWN_SECONDS", "30"))

# ----------------------------------------------------------
# CHAOS ENGINEERING
# ----------------------------------------------------------
CHAOS_ENABLED = os.getenv("CHAOS_ENABLED", "false").lower() == "true"
CHAOS_INTERVAL_SECONDS = int(os.getenv("CHAOS_INTERVAL_SECONDS", "60"))

# ----------------------------------------------------------
# API SERVER
# ----------------------------------------------------------
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))

# ----------------------------------------------------------
# SYSTEM THRESHOLDS
# ----------------------------------------------------------
RISK_STABLE_THRESHOLD = 0.5
RECOVERY_PERSISTENCE_THRESHOLD = 2