import os
import threading

from fastapi import FastAPI, Depends, HTTPException, Security
from fastapi.security.api_key import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from models.state_snapshot import StateSnapshot

app = FastAPI(title="Adaptive System API")

# ----------------------------------------------------------
# CORS
# ----------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# ----------------------------------------------------------
# API KEY AUTH
# Set API_KEY env var to protect all endpoints.
# If API_KEY is not set, auth is disabled (dev mode).
# ----------------------------------------------------------
API_KEY = os.getenv("API_KEY", "")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def require_api_key(key: str = Security(api_key_header)):
    if not API_KEY:
        return  # Auth disabled — dev mode
    if key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid or missing API key")

# ----------------------------------------------------------
# Thread-safe shared state
# Main loop writes, API reads — lock prevents partial reads
# ----------------------------------------------------------
_snapshot: StateSnapshot = None
_lock: threading.Lock = threading.Lock()


def set_snapshot(s: StateSnapshot, lock: threading.Lock):
    global _snapshot, _lock
    _snapshot = s
    _lock = lock


@app.get("/health")
def health():
    """Public health check — no auth required."""
    return {"status": "ok"}


@app.get("/state", dependencies=[Depends(require_api_key)])
def get_state():
    with _lock:
        if _snapshot is None:
            return {"error": "snapshot not ready"}
        return _snapshot.to_dict()


@app.get("/entities", dependencies=[Depends(require_api_key)])
def get_entities():
    with _lock:
        if _snapshot is None:
            return {"error": "snapshot not ready"}
        return _snapshot.entities


@app.get("/entities/{entity_id}", dependencies=[Depends(require_api_key)])
def get_entity(entity_id: str):
    with _lock:
        if _snapshot is None:
            return {"error": "snapshot not ready"}
        entity = _snapshot.entities.get(entity_id)
        if entity is None:
            return {"error": f"entity '{entity_id}' not found"}
        return entity


@app.post("/chaos/cpu", dependencies=[Depends(require_api_key)])
def trigger_cpu_spike():
    from config import CHAOS_ENABLED
    if not CHAOS_ENABLED:
        return {"error": "Chaos disabled. Set CHAOS_ENABLED=true in environment."}
    from chaos.fault_injector import cpu_spike
    cpu_spike(duration=10)
    return {"status": "cpu spike triggered", "duration": 10}


@app.post("/chaos/memory", dependencies=[Depends(require_api_key)])
def trigger_memory_leak():
    from config import CHAOS_ENABLED
    if not CHAOS_ENABLED:
        return {"error": "Chaos disabled. Set CHAOS_ENABLED=true in environment."}
    from chaos.fault_injector import memory_leak
    memory_leak(duration=10)
    return {"status": "memory leak triggered", "duration": 10}
