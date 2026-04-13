"""
api/server.py
Adaptive System — FastAPI Server
Hybrid authentication: Admin key (.env) + User keys (SQLite)
"""

import os
import threading
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from api.key_manager import init_keys_db, generate_key, validate_key, list_keys, revoke_key, delete_key

app = FastAPI(title="Adaptive System API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Shared state ──────────────────────────────────────────────────────────────
_snapshot      = {}
_snapshot_lock = threading.Lock()


def _serialize(obj):
    """
    Recursively convert any object into a JSON-safe structure.
    Handles plain dicts, objects with __dict__, lists, and primitives.
    This is the key fix — StateSnapshot entity values may be custom objects,
    not plain dicts, so a shallow __dict__.copy() isn't enough.
    """
    if obj is None or isinstance(obj, (bool, int, float, str)):
        return obj
    if isinstance(obj, dict):
        return {k: _serialize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_serialize(i) for i in obj]
    if hasattr(obj, '__dict__'):
        return {k: _serialize(v) for k, v in obj.__dict__.items()
                if not k.startswith('_')}
    try:
        return str(obj)
    except Exception:
        return None


def set_snapshot(snapshot_obj, lock=None):
    """
    Called by main.py every 2-second cycle to push the latest snapshot.
    Accepts either a StateSnapshot object or a plain dict.
    Deep-serializes everything so FastAPI can return clean JSON.
    """
    global _snapshot, _snapshot_lock

    if lock is not None:
        _snapshot_lock = lock

    serialized = _serialize(snapshot_obj)
    if not isinstance(serialized, dict):
        serialized = {}

    with _snapshot_lock:
        _snapshot = serialized


def _get_snapshot() -> dict:
    with _snapshot_lock:
        return dict(_snapshot)


# ── Auth helpers ──────────────────────────────────────────────────────────────
def _api_key(request: Request):
    return request.headers.get("X-API-Key")


def require_auth(request: Request) -> str:
    key = _api_key(request)
    if not key:
        raise HTTPException(status_code=401, detail="Missing X-API-Key header.")
    role = validate_key(key)
    if not role:
        raise HTTPException(status_code=403, detail="Invalid or inactive API key.")
    return role


def require_admin(request: Request) -> str:
    key = _api_key(request)
    if not key:
        raise HTTPException(status_code=401, detail="Missing X-API-Key header.")
    role = validate_key(key)
    if role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required.")
    return role


# ── Startup ───────────────────────────────────────────────────────────────────
@app.on_event("startup")
def on_startup():
    init_keys_db()


# ══════════════════════════════════════════════════════════════════════════════
# PUBLIC ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/health")
def health():
    return {"status": "ok"}


class GenerateKeyRequest(BaseModel):
    name: str


@app.post("/keys/generate")
def create_key(body: GenerateKeyRequest):
    name = (body.name or "").strip()
    if len(name) < 2:
        raise HTTPException(status_code=422, detail="Name must be at least 2 characters.")
    record = generate_key(name)
    return {
        "api_key":    record["key"],
        "name":       record["name"],
        "created_at": record["created_at"],
        "message":    "Save this key — it will not be shown again."
    }


# ══════════════════════════════════════════════════════════════════════════════
# AUTHENTICATED ENDPOINTS (user or admin)
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/state")
def get_state(role: str = Depends(require_auth)):
    snapshot = _get_snapshot()

    entities = snapshot.get("entities", {})
    system   = snapshot.get("system",   {})

    # Fallback: if StateSnapshot stores system fields at top level
    # (e.g. snapshot.risk, snapshot.mode) rather than nested under 'system',
    # pull them out so the frontend always gets {entities, system, role}
    if not system and snapshot:
        system = {
            "risk":       snapshot.get("risk",       snapshot.get("system_risk", 0)),
            "mode":       snapshot.get("mode",       "initial"),
            "root_cause": snapshot.get("root_cause", None),
        }

    return {
        "entities": entities,
        "system":   system,
        "role":     role,
    }


@app.get("/chaos/{action_type}")
@app.post("/chaos/{action_type}")
def chaos(action_type: str, role: str = Depends(require_auth)):
    valid = {"cpu", "memory", "cpu_spike", "memory_leak"}
    if action_type not in valid:
        raise HTTPException(status_code=400, detail=f"Unknown action type. Valid: {valid}")
    return {"triggered": action_type, "role": role, "status": f"{action_type} fault queued"}


# ══════════════════════════════════════════════════════════════════════════════
# ADMIN-ONLY ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/admin/keys")
def admin_list_keys(role: str = Depends(require_admin)):
    return {"keys": list_keys()}


@app.delete("/admin/keys/{key_id}/revoke")
def admin_revoke_key(key_id: int, role: str = Depends(require_admin)):
    if not revoke_key(key_id):
        raise HTTPException(status_code=404, detail=f"Key #{key_id} not found.")
    return {"revoked": key_id}


@app.delete("/admin/keys/{key_id}")
def admin_delete_key(key_id: int, role: str = Depends(require_admin)):
    if not delete_key(key_id):
        raise HTTPException(status_code=404, detail=f"Key #{key_id} not found.")
    return {"deleted": key_id}