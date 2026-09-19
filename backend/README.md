# SkyGuard AI — Backend README

## Project Structure

```
backend/
├── .python-version          ← Python 3.14
├── pyproject.toml           ← Project config + uv-based dependencies
├── uv.lock                  ← Resolved dependency lockfile (200+ packages)
├── .env                     ← Environment variables (DB URL, artifact paths)
├── artifacts/               ← Trained model artifacts (exported from Colab)
│   ├── lstm_model.pt
│   ├── isolation_forest.pkl
│   └── shap_explainer.pkl
├── src/
│   └── backend/
│       ├── __init__.py
│       ├── main.py          ← FastAPI app entry point (/health, /predict)
│       ├── ml/              ← Model inference module (loads artifacts at startup)
│       ├── routers/         ← FastAPI routers (currently main router)
│       ├── models/          ← Pydantic request/response schemas
│       └── services/        ← Business logic (simulator, detection core, health)
│           └── simulator.py ← APScheduler-based stream simulator
└── .venv/                   ← Virtual environment (optional if using uv)
```

## Quick Start

### 1. Install Dependencies

```bash
# From the backend directory
cd backend

# Use uv (recommended — fast, lockfile-based, matches uv.lock)
uv sync

# Or with pip (creates venv automatically)
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt  # (generated from pyproject.toml + uv.lock)
```

### 2. Set Up Environment

```bash
cp .env.example .env  # if example exists
# Or edit backend/.env directly:
#
#   DB_CONNECTION_STRING="postgresql://postgres:postgres@localhost:5432/skaguard"
#   LSTM_MODEL_PATH="artifacts/lstm_model.pt"
#   ISOLATION_FOREST_PATH="artifacts/isolation_forest.pkl"
#   SHAP_EXPLAINER_PATH="artifacts/shap_explainer.pkl"
#   ENVIRONMENT="development"
#   STATION_ID="BOMBAY001"
#   HOST="0.0.0.0"
#   PORT="8000"
```

### 3. Ensure Artifacts Are Present

```bash
# Create artifacts dir and place your Colab-exported models:
mkdir -p artifacts
# Copy/rename from Colab export:
#   lstm_model.pt      → artifacts/lstm_model.pt
#   isolation_forest.pkl → artifacts/isolation_forest.pkl
#   shap_explainer.pkl → artifacts/shap_explainer.pkl
```

### 4. Start the Backend

```bash
# Using uv run (recommended)
uv run main.py

# Or with venv activated
source .venv/bin/activate
python -m src.backend.main
```

The backend will start at `http://localhost:8000`.

### 5. Verify Health Endpoint

```bash
curl http://localhost:8000/health
# Expected: {"status": "healthy"}
```

### 6. Run the Stream Simulator

```bash
# From the backend directory
python -m src.backend.services.simulator --csv data/bombay_2024_2025.csv --interval 1.0 --inject
```

This will start APScheduler-based replay of your Bombay data, pushing readings to `http://localhost:8000/readings` with occasional synthetic anomalies.

### Available Endpoints (Minimal Prototype)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Liveness check |
| POST | `/readings` | Ingest a single reading (station_id, ts, temp, pressure, humidity) |
| POST | `/predict` | Score a reading: `{confidence, anomaly_type, severity, shap_values, root_cause_tag}` |
| GET | `/stations` | List stations (placeholder for prototype) |
| WS | `/ws/alerts` | WebSocket for live anomaly alerts |

### Project Layout Notes

- **`ml/` module**: This is where you'll place the inference code that loads the 3 Colab-exported artifacts at FastAPI startup. Pattern per TRD §3.1.1:
  ```python
  # ml/__init__.py or ml/model.py
  import os
  from pathlib import Path
  from typing import Optional

  import joblib
  import torch

  ARTIFACTS_DIR = Path(os.getenv("LSTM_MODEL_PATH", "artifacts"))

  # Load once at import time (on every worker startup)
  lstm_model = torch.load(ARTIFACTS_DIR / "lstm_model.pt", weights_only=True)
  isolation_forest = joblib.load(ARTIFACTS_DIR / "isolation_forest.pkl")
  shap_explainer = joblib.load(ARTIFACTS_DIR / "shap_explainer.pkl")

  def predict_reading(station_id: str, ts, temperature_c: float,
                      pressure_hpa: float, humidity_pct: float) -> dict:
      """Run ensemble: LSTM-AE + Isolation Forest + multivariate checks."""
      # TODO: Implement full ensemble per TRD §3.2
      # Returns: confidence (0-1), anomaly_type, severity, shap_values dict, root_cause_tag
      ...
  ```

- **`uv.lock`**: Dependency lockfile resolved via `uv`. Guarantees every developer/CI/run gets the exact same resolved dependency set. Never manually `pip install` — use `uv sync` instead.

- **.env**: Keep this file out of version control (it's in the .gitignore pattern). Contains DB connection and model artifact paths.

### Development

```bash
# Lint / format (if biome configured)
biome check .

# Format
biome format --write .
```

## Deployment

For production, use Docker (see `Dockerfile` and `docker-compose.yml` in repo root):

```bash
docker-compose up --build  # brings up backend + frontend + PostgreSQL + simulator
```

See `SkyGuard_AI_TRD.md` §3.8 for full deployment rationale (two-tier metro/central, `uv` in Dockerfiles, etc.).