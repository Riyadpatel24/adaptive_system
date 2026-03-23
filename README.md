# Adaptive System — Autonomous SRE Engine

An autonomous Site Reliability Engineering (SRE) system that monitors
service health in real time, predicts failures, identifies root causes,
and takes self-healing actions — without human intervention.

Built as a major college project demonstrating systems design, signal
processing, and autonomous decision-making.

---

## What It Does

Most monitoring systems alert a human when something goes wrong.
This system acts on its own:

1. **Ingests telemetry** — CPU, memory, disk metrics (synthetic or real)
2. **Analyses signals** — normalizes and scores risk per entity
3. **Predicts failures** — linear trend analysis forecasts risk 3 cycles ahead
4. **Reasons per entity** — classifies each service: HEALTHY / WARNING / DEGRADED / CRITICAL
5. **Finds root causes** — traverses a dependency graph to find upstream failures
6. **Takes action** — lockdown, restart, scale — with safety guards and cooldowns
7. **Self-recovers** — risk decay and policy de-escalation when trend improves
8. **Live dashboard** — real-time frontend + REST API

---

## Architecture
```
main.py (control loop, 2s tick)
│
├── sre/
│   ├── synthetic_telemetry.py   — generates or reads system metrics
│   └── telemetry_ingestion.py   — writes events to SQLite
│
├── analysis/
│   ├── telemetry_normalizer.py  — normalizes raw events into signals
│   ├── signals/
│   │   ├── signal_analyzer.py   — scores risk per entity
│   │   └── time_analyzer.py     — detects trend, volatility, persistence
│   ├── reasoning/
│   │   ├── cognition_engine.py  — per-entity decision making
│   │   ├── failure_predictor.py — linear regression risk forecast
│   │   ├── root_cause_engine.py — dependency graph traversal
│   │   └── dependency_graph.py  — service dependency map
│   ├── recovery/
│   │   ├── recovery_engine.py   — detects recovery, decays risk
│   │   └── cooldown_manager.py  — prevents action thrashing
│   └── policy/
│       └── policy_engine.py     — adapts system parameters over time
│
├── actions/
│   ├── action.py                — Action model
│   ├── safety_guard.py          — blocks actions on noisy/recovering data
│   └── executor.py              — executes actions (SIMULATION_MODE safe)
│
├── api/                         — FastAPI REST API (thread-safe)
├── frontend/                    — live dashboard (Chart.js)
├── chaos/                       — fault injector for resilience testing
├── models/                      — data models
├── storage/                     — SQLite + JSON memory
├── logger/                      — event + adaptation logger
└── config.py                    — all configuration lives here
```

---

## Quick Start
```bash
git clone https://github.com/Riyadpatel24/adaptive_system
cd adaptive_system
pip install -r requirements.txt
python main.py
```

Then open `frontend/adaptive-system.html` in your browser.

---

## Configuration

All settings are in `config.py`. Key options:

| Variable | Default | Description |
|---|---|---|
| `TELEMETRY_MODE` | `synthetic` | `synthetic` or `real` (reads your actual machine via psutil) |
| `SIMULATION_MODE` | `true` | If true, actions are logged only — nothing real executes |
| `CHAOS_ENABLED` | `false` | Inject faults to test resilience |
| `ACTION_COOLDOWN_SECONDS` | `30` | Min gap between repeated actions on same entity |

Override via environment variables:
```bash
TELEMETRY_MODE=real python main.py
```

---

## API Endpoints

| Endpoint | Description |
|---|---|
| `GET /health` | Liveness check |
| `GET /state` | Full system snapshot |
| `GET /entities` | All entity states |
| `GET /entities/{id}` | Single entity detail |

---

## Tech Stack

Python 3.12 · FastAPI · SQLite · NumPy · psutil · Chart.js

---

## Simulation vs Real

Currently runs on synthetic telemetry to simulate SRE scenarios.
The architecture is designed so switching to real monitoring means:
- Set `TELEMETRY_MODE=real` in config (already implemented via psutil)
- Replace executor stubs with actual subprocess or Kubernetes API calls

---

## Chaos Engineering

Set `CHAOS_ENABLED=true` in `config.py` to enable periodic fault
injection. The system will inject CPU spikes and memory leaks, and
you can observe whether the adaptive engine detects and responds.