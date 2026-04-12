"""
Adaptive System — FastAPI Server
Hybrid authentication: Admin key (.env) + User keys (SQLite)
"""

import os
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import threading

# Import the key manager (adjust path if needed)
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from api.key_manager import init_keys_db, generate_key, validate_key, list_keys, revoke_key, delete_key

app = FastAPI(title="Adaptive System API", version="2.0.0")

# ── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # Tighten in production if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Shared state (set by main.py) ─────────────────────────────────────────────
_snapshot = {}
_lock = threading.Lock()


def set_snapshot(data: dict):
    global _snapshot
    with _lock:
        _snapshot = data


def get_snapshot() -> dict:
    with _lock:
        return dict(_snapshot)


# ── Auth helpers ──────────────────────────────────────────────────────────────
def _get_api_key(request: Request) -> str | None:
    return request.headers.get("X-API-Key")


def require_auth(request: Request) -> str:
    """Dependency — raises 401/403 if key is missing/invalid. Returns role."""
    api_key = _get_api_key(request)
    if not api_key:
        raise HTTPException(status_code=401, detail="API key required. Add X-API-Key header.")

    role = validate_key(api_key)
    if not role:
        raise HTTPException(status_code=403, detail="Invalid or inactive API key.")

    return role


def require_admin(request: Request) -> str:
    """Dependency — admin-only endpoints."""
    api_key = _get_api_key(request)
    if not api_key:
        raise HTTPException(status_code=401, detail="API key required.")

    role = validate_key(api_key)
    if role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required.")

    return role


# ── Startup ───────────────────────────────────────────────────────────────────
@app.on_event("startup")
def startup():
    init_keys_db()


# ── Public endpoints ──────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok"}


# ── Key generation (public — anyone can request a user key) ───────────────────
class GenerateKeyRequest(BaseModel):
    name: str


@app.post("/keys/generate")
def create_key(body: GenerateKeyRequest):
    """
    Public endpoint. Anyone can generate a user-scoped API key.
    The key is returned ONCE — store it securely.
    """
    if not body.name or len(body.name.strip()) < 2:
        raise HTTPException(status_code=422, detail="Name must be at least 2 characters.")

    record = generate_key(body.name.strip())
    return {
        "api_key": record["key"],
        "name": record["name"],
        "created_at": record["created_at"],
        "message": "Save this key — it won't be shown again."
    }


# ── Authenticated endpoints ───────────────────────────────────────────────────
@app.get("/state")
def state(role: str = Depends(require_auth)):
    snapshot = get_snapshot()
    if not snapshot:
        return {"entities": [], "system": {}, "role": role}
    return {**snapshot, "role": role}


@app.get("/chaos/{action_type}")
@app.post("/chaos/{action_type}")
def chaos(action_type: str, role: str = Depends(require_auth)):
    # Chaos requires at least user-level auth
    return {"triggered": action_type, "role": role}


# ── Admin-only key management endpoints ──────────────────────────────────────
@app.get("/admin/keys")
def admin_list_keys(role: str = Depends(require_admin)):
    """List all API keys (previewed, not full values)."""
    return {"keys": list_keys()}


@app.delete("/admin/keys/{key_id}/revoke")
def admin_revoke_key(key_id: int, role: str = Depends(require_admin)):
    """Deactivate a key without deleting it."""
    ok = revoke_key(key_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Key not found.")
    return {"revoked": key_id}


@app.delete("/admin/keys/{key_id}")
def admin_delete_key(key_id: int, role: str = Depends(require_admin)):
    """Permanently delete a key."""
    ok = delete_key(key_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Key not found.")
    return {"deleted": key_id}