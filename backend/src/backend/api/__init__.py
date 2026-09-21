from backend.api.routes_stations import router as stations_router
from backend.api.routes_readings import router as readings_router
from backend.api.routes_anomalies import router as anomalies_router
from backend.api.routes_health import router as health_router
from backend.api.routes_benchmarks import router as benchmarks_router
from backend.api.routes_internal import router as internal_router
from backend.api.routes_ws import router as ws_router

__all__ = [
    "stations_router",
    "readings_router",
    "anomalies_router",
    "health_router",
    "benchmarks_router",
    "internal_router",
    "ws_router",
]