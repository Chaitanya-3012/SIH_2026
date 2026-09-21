from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.database import init_db, close_db
from backend.api import (
    stations_router,
    readings_router,
    anomalies_router,
    health_router,
    benchmarks_router,
    internal_router,
    ws_router,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    yield
    # Shutdown
    await close_db()


app = FastAPI(
    title="SkyGuard AI Backend",
    description="AWS Anomaly Detection API",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(stations_router)
app.include_router(readings_router)
app.include_router(anomalies_router)
app.include_router(health_router)
app.include_router(benchmarks_router)
app.include_router(internal_router)
app.include_router(ws_router)


@app.get("/health")
async def health_check():
    return {"status": "healthy"}