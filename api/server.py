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

# key_manager lives in the same api/ directory
from api.key_manager import init_keys_db, generate_key, validate_key, list_keys, revoke_key, delete_key

app = FastAPI(title="Adaptive System API", version="2.0.0")

# ── CORS (allow Netlify + localhost) ──────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Shared state (written by main.py, read by /state) ────────────────────────
_snapshot      = {}
_snapshot_lock = threading.Lock()


def set_snapshot(snapshot_obj, lock=None):
    """Called by main.py to push the latest snapshot into the API."""
    global _snapshot, _snapshot_lock
    if lock is not None:
        _snapshot_lock = lock
    with _snapshot_lock:
        # Accept either a StateSnapshot object or a plain dict
        if hasattr(snapshot_obj, '__dict__'):
            _snapshot = snapshot_obj.__dict__.copy()
        else:
            _snapshot = dict(snapshot_obj)


def _get_snapshot() -> dict:
    with _snapshot_lock:
        return dict(_snapshot)


# ── Auth helpers ──────────────────────────────────────────────────────────────
def _api_key(request: Request) -> str | None:
    return request.headers.get("X-API-Key")


def require_auth(request: Request) -> str:
    """Dependency — any valid key (admin or user). Returns role string."""
    key = _api_key(request)
    if not key:
        raise HTTPException(status_code=401, detail="Missing X-API-Key header.")
    role = validate_key(key)
    if not role:
        raise HTTPException(status_code=403, detail="Invalid or inactive API key.")
    return role


def require_admin(request: Request) -> str:
    """Dependency — admin key only."""
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
    """Health check — no auth required."""
    return {"status": "ok"}


# ── Key generation (public — no auth required) ────────────────────────────────
class GenerateKeyRequest(BaseModel):
    name: str


@app.post("/keys/generate")
def create_key(body: GenerateKeyRequest):
    """
    Anyone can call this to get a user-scoped API key.
    The full key is returned ONCE — users must save it themselves.
    """
    name = body.name.strip() if body.name else ""
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
    """Return current system snapshot. Role is included in the response."""
    snapshot = _get_snapshot()
    if not snapshot:
        return {"entities": {}, "system": {}, "role": role}
    return {**snapshot, "role": role}


@app.get("/chaos/{action_type}")
@app.post("/chaos/{action_type}")
def chaos(action_type: str, role: str = Depends(require_auth)):
    """Trigger a chaos fault. Requires at least user-level auth."""
    valid = {"cpu", "memory", "cpu_spike", "memory_leak"}
    if action_type not in valid:
        raise HTTPException(status_code=400, detail=f"Unknown action. Valid: {valid}")
    # The actual injection is handled by main.py's chaos module
    return {"triggered": action_type, "role": role, "status": f"{action_type} fault queued"}


# ══════════════════════════════════════════════════════════════════════════════
# ADMIN-ONLY ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/admin/keys")
def admin_list_keys(role: str = Depends(require_admin)):
    """List all generated API keys (values are partially masked)."""
    return {"keys": list_keys()}


@app.delete("/admin/keys/{key_id}/revoke")
def admin_revoke_key(key_id: int, role: str = Depends(require_admin)):
    """Deactivate a key without deleting it."""
    if not revoke_key(key_id):
        raise HTTPException(status_code=404, detail=f"Key #{key_id} not found.")
    return {"revoked": key_id}


@app.delete("/admin/keys/{key_id}")
def admin_delete_key(key_id: int, role: str = Depends(require_admin)):
    """Permanently delete a key."""
    if not delete_key(key_id):
        raise HTTPException(status_code=404, detail=f"Key #{key_id} not found.")
    return {"deleted": key_id}