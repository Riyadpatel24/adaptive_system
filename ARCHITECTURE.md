# Architecture — Autonomous SRE Engine

## What It Does

Most monitoring systems alert a human when something goes wrong. This system acts on its own — it ingests service telemetry, predicts failures before they happen, identifies the root cause, and executes corrective actions without human intervention.

---

## Data Flow

```
  Raw Telemetry
  (CPU / memory / disk)
         │
         ▼
┌─────────────────────┐
│  TelemetryNormalizer│  Converts raw values into scored signals
│  sre/ + analysis/   │  (signal: 0–1, confidence: 0–1, reason: str)
└─────────────────────┘
         │
         ▼
┌─────────────────────┐
│   SignalAnalyzer    │  Groups signals by entity, computes weighted
│   signals/          │  risk score, classifies: HEALTHY / WARNING /
└─────────────────────┘  DEGRADED / CRITICAL
         │
         ├──────────────────────────────────────┐
         ▼                                      ▼
┌─────────────────────┐            ┌─────────────────────────┐
│  TemporalAnalyzer   │            │    FailurePredictor     │
│  signals/           │            │    reasoning/           │
│                     │            │                         │
│  trend: worsening / │            │  Linear regression over │
│  improving / stable │            │  rolling window →       │
│  volatility         │            │  risk_forecast 3 cycles │
│  persistence        │            │  ahead                  │
└─────────────────────┘            └─────────────────────────┘
         │                                      │
         └──────────────┬───────────────────────┘
                        ▼
         ┌─────────────────────────┐
         │    CognitionEngine      │  Per-entity decision:
         │    reasoning/           │  CRITICAL  → lockdown
         └─────────────────────────┘  DEGRADED  → throttle
                        │             HEALTHY   → observe
                        ▼
         ┌─────────────────────────┐
         │    ActionSafetyGuard    │  Blocks action if:
         │    actions/             │  - trend is improving
         └─────────────────────────┘  - persistence < 3
                        │             - volatility > 0.2
                        ▼
         ┌─────────────────────────┐
         │    CooldownManager      │  Prevents same action
         │    analysis/recovery/   │  firing repeatedly
         └─────────────────────────┘
                        │
                        ▼
         ┌─────────────────────────┐
         │    ActionExecutor       │  SIMULATION_MODE=true → logs only
         │    actions/             │  SIMULATION_MODE=false → real exec
         └─────────────────────────┘
                        │
         ┌──────────────┘
         ▼
┌─────────────────────┐        ┌─────────────────────────┐
│  RootCauseEngine    │        │    RecoveryEngine       │
│  reasoning/         │        │    analysis/recovery/   │
│                     │        │                         │
│  Traverses dep.     │        │  Detects when risk is   │
│  graph to find      │        │  decaying, de-escalates │
│  upstream failure   │        │  action level           │
└─────────────────────┘        └─────────────────────────┘
         │                                  │
         └──────────────┬───────────────────┘
                        ▼
         ┌─────────────────────────┐
         │    StateSnapshot        │  Thread-safe in-memory
         │    models/              │  state served by REST API
         └─────────────────────────┘
                        │
                        ▼
         ┌─────────────────────────┐
         │    FastAPI + Dashboard  │  GET /state, /entities
         │    api/ + frontend/     │  Live Chart.js frontend
         └─────────────────────────┘
```

---

## Component Reference

### `sre/`
| File | Role |
|---|---|
| `synthetic_telemetry.py` | Generates fake CPU/memory/disk events, or reads real process metrics via psutil. `apply_policy_effect()` modifies telemetry in response to actions — thread-safe via `threading.Lock`. |
| `telemetry_ingestion.py` | Persists telemetry events to SQLite (`storage/events.db`). Accepts pre-collected telemetry to avoid double-sampling. |

### `analysis/`
| File | Role |
|---|---|
| `telemetry_normalizer.py` | Reads recent events from SQLite, normalises raw metric values into scored signals (0–1) with confidence weights. |
| `signals/signal_analyzer.py` | Weighted average of signals per entity → risk score → state classification. Thresholds: CRITICAL ≥ 0.85, DEGRADED ≥ 0.6, WARNING ≥ 0.3. |
| `signals/time_analyzer.py` | Computes trend (slope), volatility (std dev), and persistence (count of readings above 0.7) over a rolling window. |
| `reasoning/cognition_engine.py` | Per-entity decision: maps state to an action hint (lockdown / strict_mode / observe). |
| `reasoning/failure_predictor.py` | `np.polyfit` linear regression over rolling risk history → forecasts risk 3 cycles ahead. Clamped to [0, 1]. |
| `reasoning/root_cause_engine.py` | Traverses `DependencyGraph` to find the upstream CRITICAL service causing a cascade. |
| `reasoning/dependency_graph.py` | Static map of service dependencies. Extend this with real service discovery in production. |
| `recovery/recovery_engine.py` | Detects when risk is falling and triggers de-escalation. |
| `recovery/cooldown_manager.py` | Enforces minimum gap between repeated actions on the same entity. |
| `policy/policy_engine.py` | Adapts system parameters (timeout, retry limit) based on observed failure rate and success rate. |

### `actions/`
| File | Role |
|---|---|
| `action.py` | `Action` dataclass + `ActionType` enum (LOCKDOWN, THROTTLE_NODE, RESTART_PROCESS, ISOLATE_NODE). |
| `safety_guard.py` | Final gate before execution. Returns `bool`. Blocks on improving trend, low persistence, or high volatility. |
| `executor.py` | Routes action type to implementation. In `SIMULATION_MODE`, logs only — no real side effects. |

### `models/`
| File | Role |
|---|---|
| `system_state.py` | Tunable parameters (timeout_ms, retry_limit) and performance metrics updated each cycle. |
| `state_snapshot.py` | Thread-safe snapshot of all entity states served to the API. |
| `event.py` | Raw telemetry event model. |

---

## Key Design Decisions

**Why linear regression for prediction?**
The rolling window is small (5 readings) and the goal is trend direction, not absolute accuracy. `np.polyfit` is fast, interpretable, and has no hyperparameters to tune. The forecast is intentionally conservative — 3 cycles ahead is enough to act before a threshold breach without false positives from longer extrapolation.

**Why weighted signal averaging?**
Different metrics have different reliability depending on the entity type. Confidence weights let the normalizer express "I'm 90% sure this CPU reading is anomalous" separately from the signal magnitude. A high signal with low confidence contributes less than a moderate signal with high confidence.

**Why a hard dependency graph instead of dynamic discovery?**
For a college project, static is correct — it keeps root cause analysis deterministic and testable. In production this would be replaced with a service mesh (Istio, Consul) providing live dependency data.

**Why `SIMULATION_MODE` default to `true`?**
The executor stubs (lockdown, restart, throttle) would need real infrastructure (Kubernetes API, systemd, subprocess calls) to do anything meaningful. The simulation flag means the system can run anywhere and demonstrate the full decision pipeline without side effects.

---

## Extending the System

**Add a new action type:**
1. Add a value to `ActionType` enum in `actions/action.py`
2. Add a branch in `CognitionEngine.reason_from_entity()` to emit the new hint
3. Add a route in `ActionExecutor.execute()` and implement the method
4. Add test cases in `tests/test_core.py`

**Switch to real infrastructure:**
- Set `TELEMETRY_MODE=real` in `config.py` — psutil integration already implemented
- Set `SIMULATION_MODE=false` and replace executor stubs with real subprocess / Kubernetes API calls
- Replace `DependencyGraph` hardcoded map with a live service mesh query

**Add a new entity to monitor:**
Register it in `DependencyGraph.__init__()` with its upstream dependencies. The rest of the pipeline picks it up automatically.

---

## Running Tests

```bash
pytest tests/test_core.py -v
```

36 tests covering `SignalAnalyzer`, `FailurePredictor`, `TemporalAnalyzer`, `RootCauseEngine`, and `ActionSafetyGuard`.