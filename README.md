# 🧠 Adaptive System — Autonomous SRE Engine

An autonomous Site Reliability Engineering (SRE) system that continuously monitors system entities, detects anomalies, predicts failures, and takes corrective actions — all in a self-tuning loop.

---

## 📐 Architecture

```
Telemetry → Normalize → Analyze → Cognition → Safety Guard → Execute Action
                                      ↓
                              Root Cause Engine
                                      ↓
                              Policy Adaptation
```

The system runs a loop every 2 seconds:
1. Collect synthetic (or real) telemetry
2. Normalize signals across a rolling window
3. Analyze entity health and risk scores
4. Predict failures using temporal history
5. Reason about actions via the Cognition Engine
6. Pass through Safety Guard + Cooldown checks
7. Execute actions (LOCKDOWN / THROTTLE_NODE)
8. Run root cause analysis across all entities
9. Adapt system policy (timeout, retry limits, mode)

A FastAPI server runs in a background thread and exposes the live system state on port `8000`. A Flask target server simulates a real web service on port `5000`.

---

## 📁 Project Structure

```
adaptive_system/
├── main.py                  # Core control loop
├── start.py                 # Launcher (starts both servers)
├── config.py                # All configuration via env vars
├── target_server.py         # Simulated Flask target service (port 5000)
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
│
├── actions/
│   ├── action.py            # Action model (LOCKDOWN, THROTTLE_NODE)
│   ├── executor.py          # Executes or simulates actions
│   ├── safety_guard.py      # Blocks unsafe/premature actions
│   └── recovery_actions.py
│
├── analysis/
│   ├── telemetry_normalizer.py
│   ├── memory.py
│   ├── signals/
│   │   ├── signal_analyzer.py   # Risk scoring per entity
│   │   └── time_analyzer.py     # Trend, persistence, volatility
│   ├── reasoning/
│   │   ├── cognition_engine.py  # Decision engine
│   │   ├── failure_predictor.py
│   │   ├── root_cause_engine.py
│   │   └── dependency_graph.py
│   ├── policy/
│   │   └── policy_engine.py     # Adaptive timeout/retry tuning
│   └── recovery/
│       ├── recovery_engine.py
│       └── cooldown_manager.py
│
├── api/
│   └── server.py            # FastAPI — /health /state /entities
│
├── models/
│   ├── system_state.py
│   ├── state_snapshot.py
│   └── ...
│
├── sre/
│   ├── synthetic_telemetry.py
│   └── telemetry_ingestion.py
│
├── storage/
│   └── temporal_memory.py
│
├── logger/
│   └── event_logger.py
│
├── chaos/
│   └── fault_injector.py    # CPU spike / memory leak injection
│
├── frontend/
│   └── adaptive-system.html # Live dashboard (open in browser)
│
└── tests/
    └── test_core.py
```

---

## 🚀 Quick Start

### Option 1 — Docker (Recommended)

```bash
# 1. Clone the repo
git clone https://github.com/Riyadpatel24/adaptive_system.git
cd adaptive_system

# 2. Create your environment file
cp .env.example .env

# 3. Edit .env — at minimum set a strong API_KEY
nano .env

# 4. Build and run
docker compose up --build

# 5. Open the dashboard
open frontend/adaptive-system.html
# Or visit: http://localhost:8000/state
```

### Option 2 — Local Python

```bash
# 1. Clone the repo
git clone https://github.com/Riyadpatel24/adaptive_system.git
cd adaptive_system

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment
cp .env.example .env
# Edit .env as needed

# 5. Run
python start.py
```

---

## 🔌 API Reference

All endpoints except `/health` require the `X-API-Key` header:

```
X-API-Key: your_api_key_here
```

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check (no auth) |
| GET | `/state` | Full system snapshot |
| GET | `/entities` | All monitored entities |
| GET | `/entities/{id}` | Single entity detail |
| POST | `/chaos/cpu` | Trigger CPU spike (requires CHAOS_ENABLED=true) |
| POST | `/chaos/memory` | Trigger memory leak (requires CHAOS_ENABLED=true) |

**Interactive docs:** http://localhost:8000/docs

**Example request:**
```bash
curl http://localhost:8000/state \
  -H "X-API-Key: your_api_key_here"
```

---

## ⚙️ Configuration

All settings are controlled via environment variables. Copy `.env.example` to `.env` to get started.

| Variable | Default | Description |
|----------|---------|-------------|
| `API_KEY` | `""` | Secret key for API auth. Empty = auth disabled (dev only) |
| `TELEMETRY_MODE` | `synthetic` | `synthetic` or `real` |
| `SIMULATION_MODE` | `true` | `true` = log actions only, `false` = execute them |
| `ACTION_COOLDOWN_SECONDS` | `30` | Minimum seconds between actions on the same entity |
| `CHAOS_ENABLED` | `false` | Enable chaos fault injection |
| `CHAOS_INTERVAL_SECONDS` | `60` | How often chaos is injected (in loop cycles) |
| `API_HOST` | `0.0.0.0` | API bind address |
| `API_PORT` | `8000` | API port |
| `DB_PATH` | `storage/events.db` | SQLite database path |
| `MEMORY_PATH` | `storage/memory.json` | Persistent memory file path |

---

## 🧪 Running Tests

```bash
# Make sure dependencies are installed
pip install -r requirements.txt
pip install pytest

# Run all tests
pytest tests/test_core.py -v
```

---

## 🌐 Dashboard

Open `frontend/adaptive-system.html` directly in your browser. It polls the `/state` and `/entities` API endpoints and shows a live view of:

- System risk level
- Per-entity health, trend, and predicted risk
- Action history
- Policy mode (normal / degraded / critical)

> **Note:** If you set an `API_KEY`, update the `X-API-Key` header in the dashboard's fetch calls inside `adaptive-system.html`.

---

## 🔥 Chaos Engineering

To test system resilience, enable chaos mode in `.env`:

```env
CHAOS_ENABLED=true
CHAOS_INTERVAL_SECONDS=60
```

Or trigger manually via the API:

```bash
curl -X POST http://localhost:8000/chaos/cpu \
  -H "X-API-Key: your_api_key_here"
```

---

## 🛡️ Security Notes

- Always set a strong `API_KEY` in production — never use the default `changeme`
- The `/health` endpoint is intentionally public for load balancer checks
- Run behind a reverse proxy (nginx/Caddy) with HTTPS in production
- `SIMULATION_MODE=false` means real system actions will execute — verify carefully before enabling

---

## 📦 Deployment Checklist

- [ ] `cp .env.example .env` and fill in all values
- [ ] Set a strong `API_KEY`
- [ ] Set `SIMULATION_MODE=false` when ready for real actions
- [ ] `docker compose up --build`
- [ ] Verify `/health` returns `{"status": "ok"}`
- [ ] Open dashboard and confirm entities are populating
- [ ] (Optional) Set up nginx reverse proxy with HTTPS

---

## 🤝 Contributing

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Commit your changes (`git commit -m "Add my feature"`)
4. Push and open a Pull Request

---

## 📄 License

MIT
