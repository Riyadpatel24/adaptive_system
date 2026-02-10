from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from models.state_snapshot import StateSnapshot

app = FastAPI(title="Adaptive System API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

snapshot: StateSnapshot = None


def set_snapshot(s: StateSnapshot):
    global snapshot
    snapshot = s


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/state")
def get_state():
    if snapshot is None:
        return {"error": "snapshot not ready"}
    return snapshot.to_dict()
