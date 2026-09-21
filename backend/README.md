# SkyGuard AI — Backend

FastAPI backend for the **SkyGuard AI** environmental monitoring and anomaly detection system.

This backend is designed for **Windows 11**, **Python 3.13**, and **uv** for dependency and virtual-environment management.

---

## Project Structure

```text
backend/
├── .python-version              # Python 3.13
├── pyproject.toml               # Project configuration and dependencies
├── uv.lock                      # Locked dependency versions
├── .env                          # Environment variables (not committed)
│
├── artifacts/                    # Trained ML model artifacts
│   ├── lstm_model.pt
│   ├── isolation_forest.pkl
│   └── shap_explainer.pkl
│
├── src/
│   └── backend/
│       ├── __init__.py
│       ├── main.py               # FastAPI application entry point
│       │
│       ├── ml/                   # ML inference modules
│       │
│       ├── routers/              # FastAPI route definitions
│       │
│       ├── models/               # Pydantic request/response schemas
│       │
│       └── services/             # Application/business logic
│           └── simulator.py      # Sensor stream simulator
│
└── .venv/                        # uv-managed virtual environment
```

---

# Requirements

Before starting the backend, make sure the following are installed:

* Windows 11
* Python 3.13
* `uv`
* PostgreSQL (if running the database locally)
* Git
* Docker Desktop (optional, for containerized deployment)

---

# 1. Install `uv`

If `uv` is not already installed, open **PowerShell** and run:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Close and reopen PowerShell after installation.

Verify the installation:

```powershell
uv --version
```

Expected output will look similar to:

```text
uv 0.x.x
```

---

# 2. Clone the Repository

If you haven't cloned the project yet:

```powershell
git clone <repository-url>
```

Navigate to the backend:

```powershell
cd <repository-folder>\backend
```

For example:

```powershell
cd C:\Projects\SkyGuard\backend
```

Verify the project files:

```powershell
Get-ChildItem
```

You should see:

```text
.python-version
pyproject.toml
uv.lock
src
artifacts
```

---

# 3. Configure Python 3.13

This project uses **Python 3.13**.

The `.python-version` file should contain:

```text
3.13
```

You can set it using PowerShell:

```powershell
Set-Content .python-version "3.13"
```

Verify the file:

```powershell
Get-Content .python-version
```

Expected:

```text
3.13
```

---

# 4. Install Python 3.13 Using uv

If Python 3.13 is not installed:

```powershell
uv python install 3.13
```

Verify available Python versions:

```powershell
uv python list
```

Then verify the project Python version:

```powershell
uv run python --version
```

Expected:

```text
Python 3.13.x
```

---

# 5. Install Project Dependencies

This project uses `uv.lock` to maintain reproducible dependency versions.

From the `backend` directory, run:

```powershell
uv sync
```

This will:

* Create `.venv` if it doesn't already exist
* Install Python 3.13 if required
* Install dependencies from `uv.lock`
* Synchronize the environment with `pyproject.toml`

After running the command, you should have:

```text
backend/
└── .venv/
```

Verify the environment:

```powershell
uv run python --version
```

Expected:

```text
Python 3.13.x
```

---

# 6. Virtual Environment

`uv` automatically manages the project's `.venv`.

You **do not need to activate `.venv`** when using `uv run`.

For example:

```powershell
uv run python --version
```

and:

```powershell
uv run uvicorn backend.main:app --reload --app-dir src
```

will automatically use the project's virtual environment.

## Optional: Activate `.venv`

If you prefer to activate it manually in PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Your terminal should then show:

```text
(.venv) PS C:\Projects\SkyGuard\backend>
```

If PowerShell blocks the activation script, run:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then activate again:

```powershell
.venv\Scripts\Activate.ps1
```

Activation is optional when using `uv run`.

---

# 7. Environment Variables

The backend uses a `.env` file for configuration.

If an example environment file exists:

```powershell
Copy-Item .env.example .env
```

Otherwise create `.env` manually:

```powershell
New-Item .env -ItemType File
```

Example `.env`:

```env
DB_CONNECTION_STRING=postgresql://postgres:postgres@localhost:5432/skaguard

LSTM_MODEL_PATH=artifacts/lstm_model.pt
ISOLATION_FOREST_PATH=artifacts/isolation_forest.pkl
SHAP_EXPLAINER_PATH=artifacts/shap_explainer.pkl

ENVIRONMENT=development
STATION_ID=BOMBAY001

HOST=0.0.0.0
PORT=8000
```

### Important

Do not commit `.env` to Git.

Make sure your `.gitignore` contains:

```gitignore
.env
.venv/
__pycache__/
*.pyc
```

---

# 8. ML Model Artifacts

The trained machine-learning models should be placed inside:

```text
artifacts/
├── lstm_model.pt
├── isolation_forest.pkl
└── shap_explainer.pkl
```

Verify the files from PowerShell:

```powershell
Get-ChildItem .\artifacts\
```

Expected:

```text
lstm_model.pt
isolation_forest.pkl
shap_explainer.pkl
```

If the directory doesn't exist:

```powershell
New-Item -ItemType Directory artifacts
```

You can copy exported models using:

```powershell
Copy-Item "C:\path\to\lstm_model.pt" ".\artifacts\"
Copy-Item "C:\path\to\isolation_forest.pkl" ".\artifacts\"
Copy-Item "C:\path\to\shap_explainer.pkl" ".\artifacts\"
```

---

# 9. Start the FastAPI Backend

The FastAPI application is located at:

```text
src/backend/main.py
```

Because this project uses a `src` layout, start the server from the `backend` directory with:

```powershell
uv run uvicorn backend.main:app --reload --app-dir src
```

### Explanation

```text
backend.main
```

refers to:

```text
src/backend/main.py
```

and:

```text
:app
```

refers to the FastAPI object:

```python
app = FastAPI()
```

The `--app-dir src` option tells Uvicorn to look inside the `src` directory.

The `--reload` option automatically restarts the server when Python source files change.

---

# 10. Expected Server Output

A successful startup should look similar to:

```text
INFO:     Will watch for changes in these directories: [...]
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Started reloader process [...]
INFO:     Started server process [...]
INFO:     Application startup complete.
```

The backend is now available at:

```text
http://localhost:8000
```

---

# 11. FastAPI Documentation

FastAPI automatically provides interactive API documentation.

## Swagger UI

Open:

```text
http://localhost:8000/docs
```

## ReDoc

Open:

```text
http://localhost:8000/redoc
```

Swagger UI can be used to test the backend endpoints without requiring Postman or another API client.

---

# 12. Health Check

The backend provides:

```text
GET /health
```

Open:

```text
http://localhost:8000/health
```

Expected response:

```json
{
  "status": "healthy"
}
```

You can also test it from PowerShell:

```powershell
Invoke-RestMethod http://localhost:8000/health
```

Or using `curl.exe`:

```powershell
curl.exe http://localhost:8000/health
```

Expected:

```json
{"status":"healthy"}
```

---

# 13. Available Endpoints

| Method | Endpoint     | Description               |
| ------ | ------------ | ------------------------- |
| GET    | `/health`    | Backend health check      |
| POST   | `/readings`  | Ingest a sensor reading   |
| POST   | `/predict`   | Run anomaly prediction    |
| GET    | `/stations`  | List available stations   |
| WS     | `/ws/alerts` | Live anomaly alert stream |

Interactive API documentation:

```text
http://localhost:8000/docs
```

---

# 14. Testing `/predict`

The exact request schema depends on the Pydantic model currently implemented in:

```text
src/backend/models/
```

The easiest way to test it is through Swagger:

```text
http://localhost:8000/docs
```

Select:

```text
POST /predict
```

Click:

```text
Try it out
```

Enter the request JSON according to the schema shown by FastAPI.

For example, if the endpoint accepts:

```json
{
  "station_id": "BOMBAY001",
  "ts": "2026-09-21T20:00:00",
  "temperature_c": 28.5,
  "pressure_hpa": 1008.2,
  "humidity_pct": 72.0
}
```

you can submit that request directly through Swagger.

---

# 15. ML Inference Module

The ML inference implementation is located under:

```text
src/backend/ml/
```

The backend loads three trained artifacts:

```text
artifacts/lstm_model.pt
artifacts/isolation_forest.pkl
artifacts/shap_explainer.pkl
```

A typical model-loading implementation can look like:

```python
import os
from pathlib import Path

import joblib
import torch


LSTM_MODEL_PATH = Path(
    os.getenv("LSTM_MODEL_PATH", "artifacts/lstm_model.pt")
)

ISOLATION_FOREST_PATH = Path(
    os.getenv(
        "ISOLATION_FOREST_PATH",
        "artifacts/isolation_forest.pkl",
    )
)

SHAP_EXPLAINER_PATH = Path(
    os.getenv(
        "SHAP_EXPLAINER_PATH",
        "artifacts/shap_explainer.pkl",
    )
)


lstm_model = torch.load(
    LSTM_MODEL_PATH,
    weights_only=True,
)

isolation_forest = joblib.load(
    ISOLATION_FOREST_PATH,
)

shap_explainer = joblib.load(
    SHAP_EXPLAINER_PATH,
)
```

The prediction function is expected to expose functionality similar to:

```python
def predict_reading(
    station_id: str,
    ts,
    temperature_c: float,
    pressure_hpa: float,
    humidity_pct: float,
) -> dict:
    """
    Run the anomaly-detection ensemble.

    Components:
    - LSTM Autoencoder
    - Isolation Forest
    - Multivariate checks
    """

    # TODO: Implement the complete ensemble
    # according to the SkyGuard AI TRD.

    return {
        "confidence": 0.0,
        "anomaly_type": None,
        "severity": None,
        "shap_values": {},
        "root_cause_tag": None,
    }
```

---

# 16. Run the Stream Simulator

The sensor simulator is located at:

```text
src/backend/services/simulator.py
```

The simulator replays historical Bombay sensor data and sends readings to:

```text
POST /readings
```

Run it from the backend root:

```powershell
uv run python -m backend.services.simulator --csv data\bombay_2024_2025.csv --interval 1.0 --inject
```

### Parameters

```text
--csv
```

Path to the input CSV.

```text
--interval 1.0
```

Send one reading approximately every 1 second.

```text
--inject
```

Enable synthetic anomaly injection.

---

# 17. Using a Windows Absolute Path

If your CSV is somewhere else, use its full Windows path:

```powershell
uv run python -m backend.services.simulator --csv "C:\Projects\SkyGuard\data\bombay_2024_2025.csv" --interval 1.0 --inject
```

Using quotes is recommended when the path contains spaces.

For example:

```powershell
uv run python -m backend.services.simulator --csv "C:\Users\Chaitanya Nevse\Documents\SkyGuard\data\bombay_2024_2025.csv" --interval 1.0 --inject
```

---

# 18. Run Backend and Simulator Together

You need two PowerShell terminals.

## Terminal 1 — FastAPI

```powershell
cd path\to\SkyGuard\backend

uv sync

uv run uvicorn backend.main:app --reload --app-dir src
```

Keep this terminal running.

The backend will be available at:

```text
http://localhost:8000
```

---

## Terminal 2 — Simulator

Open another PowerShell window:

```powershell
cd path\to\SkyGuard\backend

uv run python -m backend.services.simulator --csv data\bombay_2024_2025.csv --interval 1.0 --inject
```

The simulator will send sensor readings to the running backend.

---

# 19. Development Workflow

The normal development workflow is:

```text
Historical CSV
      │
      ▼
Stream Simulator
      │
      │ POST /readings
      ▼
FastAPI Backend
      │
      ▼
ML Detection Pipeline
      │
      ├── LSTM Autoencoder
      ├── Isolation Forest
      ├── Multivariate Checks
      └── SHAP Explanation
      │
      ▼
Anomaly Result
      │
      ▼
WebSocket / API
      │
      ▼
Frontend
```

---

# 20. `uv` Commands

## Synchronize dependencies

```powershell
uv sync
```

## Install Python 3.13

```powershell
uv python install 3.13
```

## Check Python version

```powershell
uv run python --version
```

## Run Python

```powershell
uv run python
```

## Add a dependency

```powershell
uv add <package>
```

Example:

```powershell
uv add pandas
```

## Remove a dependency

```powershell
uv remove <package>
```

## Update the lockfile

```powershell
uv lock
```

## Upgrade dependencies

```powershell
uv lock --upgrade
uv sync
```

---

# 21. Dependency Management

This project uses:

```text
pyproject.toml
uv.lock
```

Use `uv` to manage dependencies.

### Recommended

```powershell
uv add fastapi
```

### Avoid manually installing project dependencies with

```powershell
pip install ...
```

unless there is a specific reason to do so.

The `uv.lock` file ensures that developers and CI environments use the same resolved dependency versions.

---

# 22. PostgreSQL

If the backend uses a local PostgreSQL database, make sure PostgreSQL is running.

The expected connection string is configured in `.env`:

```env
DB_CONNECTION_STRING=postgresql://postgres:postgres@localhost:5432/skaguard
```

The expected setup is:

```text
FastAPI
   │
   ▼
PostgreSQL
localhost:5432
   │
   ▼
skaguard database
```

Make sure the database exists before starting features that depend on it.

---

# 23. Useful Windows Commands

## List files

```powershell
Get-ChildItem
```

or:

```powershell
dir
```

## Check Python

```powershell
python --version
```

Project Python:

```powershell
uv run python --version
```

## Check `uv`

```powershell
uv --version
```

## Check running process on port 8000

```powershell
netstat -ano | findstr :8000
```

## Kill a process

Replace `<PID>` with the process ID:

```powershell
taskkill /PID <PID> /F
```

---

# 24. Troubleshooting

## `uv` is not recognized

If you see:

```text
uv : The term 'uv' is not recognized...
```

close PowerShell and open a new PowerShell window.

Then:

```powershell
uv --version
```

If it still doesn't work, reinstall `uv`.

---

## Python version is incorrect

Check:

```powershell
Get-Content .python-version
```

It should be:

```text
3.13
```

Then:

```powershell
uv python install 3.13
```

Recreate the environment:

```powershell
Remove-Item -Recurse -Force .venv
uv sync
```

Verify:

```powershell
uv run python --version
```

Expected:

```text
Python 3.13.x
```

---

## `.venv` is missing

Run:

```powershell
uv sync
```

`uv` will create it automatically.

---

## `backend.main` cannot be imported

Verify the project structure:

```text
backend/
└── src/
    └── backend/
        ├── __init__.py
        └── main.py
```

Make sure you're running the command from the `backend` directory:

```powershell
cd path\to\SkyGuard\backend
```

Then:

```powershell
uv run uvicorn backend.main:app --reload --app-dir src
```

---

## FastAPI or Uvicorn is missing

Run:

```powershell
uv sync
```

If the packages are not declared in `pyproject.toml`, add them:

```powershell
uv add fastapi
uv add "uvicorn[standard]"
```

Then:

```powershell
uv sync
```

---

## Port 8000 is already in use

Check:

```powershell
netstat -ano | findstr :8000
```

Terminate the process:

```powershell
taskkill /PID <PID> /F
```

Or use another port:

```powershell
uv run uvicorn backend.main:app --reload --app-dir src --port 8001
```

Then open:

```text
http://localhost:8001/docs
```

---

## Model artifact not found

If you receive:

```text
FileNotFoundError
```

verify:

```powershell
Get-ChildItem .\artifacts\
```

The directory should contain:

```text
artifacts/
├── lstm_model.pt
├── isolation_forest.pkl
└── shap_explainer.pkl
```

Also verify the paths in `.env`.

---

# 25. Docker Deployment

For production or full-stack deployment, Docker Desktop can be used on Windows 11.

The repository contains:

```text
Dockerfile
docker-compose.yml
```

From the repository root:

```powershell
docker compose up --build
```

This can start the required services, such as:

```text
Backend
Frontend
PostgreSQL
Simulator
```

depending on the current `docker-compose.yml` configuration.

Stop the services:

```powershell
docker compose down
```

Rebuild and start:

```powershell
docker compose up --build
```

---

# 26. Recommended Daily Startup

Once the project is completely configured, the normal workflow is very simple.

## Terminal 1

```powershell
cd path\to\SkyGuard\backend

uv sync

uv run uvicorn backend.main:app --reload --app-dir src
```

Then open:

```text
http://localhost:8000/docs
```

---

## Terminal 2

```powershell
cd path\to\SkyGuard\backend

uv run python -m backend.services.simulator --csv data\bombay_2024_2025.csv --interval 1.0 --inject
```

---

# 27. Quick Start

For a machine that already has `uv` installed and the project cloned:

```powershell
cd path\to\SkyGuard\backend

uv python install 3.13

uv sync

uv run python --version

uv run uvicorn backend.main:app --reload --app-dir src
```

Expected:

```text
Python 3.13.x
```

Then open:

```text
http://localhost:8000/docs
```

For the simulator, open a second terminal:

```powershell
cd path\to\SkyGuard\backend

uv run python -m backend.services.simulator --csv data\bombay_2024_2025.csv --interval 1.0 --inject
```

---

# 28. Important Notes

* **Python version:** 3.13
* **Operating system:** Windows 11
* **Package manager:** `uv`
* **Virtual environment:** `.venv`
* **Dependency lockfile:** `uv.lock`
* **FastAPI entry point:** `src/backend/main.py`
* **Development server:** Uvicorn
* **API port:** `8000`
* **Swagger:** `http://localhost:8000/docs`
* **Health endpoint:** `GET /health`
* **Simulator:** `src/backend/services/simulator.py`

The recommended way to run the backend is:

```powershell
uv run uvicorn backend.main:app --reload --app-dir src
```

and the recommended way to run the simulator is:

```powershell
uv run python -m backend.services.simulator --csv data\bombay_2024_2025.csv --interval 1.0 --inject
```
