import threading

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from models.state_snapshot import StateSnapshot

app = FastAPI(title="Adaptive System API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

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
    return {"status": "ok"}


@app.get("/state")
def get_state():
    with _lock:
        if _snapshot is None:
            return {"error": "snapshot not ready"}
        return _snapshot.to_dict()


@app.get("/entities")
def get_entities():
    with _lock:
        if _snapshot is None:
            return {"error": "snapshot not ready"}
        return _snapshot.entities


@app.get("/entities/{entity_id}")
def get_entity(entity_id: str):
    with _lock:
        if _snapshot is None:
            return {"error": "snapshot not ready"}
        entity = _snapshot.entities.get(entity_id)
        if entity is None:
            return {"error": f"entity '{entity_id}' not found"}
        return entity


@app.post("/chaos/cpu")
def trigger_cpu_spike():
    from config import CHAOS_ENABLED
    if not CHAOS_ENABLED:
        return {"error": "Chaos disabled. Set CHAOS_ENABLED=true in config.py"}
    from chaos.fault_injector import cpu_spike
    cpu_spike(duration=10)
    return {"status": "cpu spike triggered", "duration": 10}


@app.post("/chaos/memory")
def trigger_memory_leak():
    from config import CHAOS_ENABLED
    if not CHAOS_ENABLED:
        return {"error": "Chaos disabled. Set CHAOS_ENABLED=true in config.py"}
    from chaos.fault_injector import memory_leak
    memory_leak(duration=10)
    return {"status": "memory leak triggered", "duration": 10}