from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache
import os


class Settings(BaseSettings):
    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/skyguard",
        validation_alias="DATABASE_URL"
    )

    # Backend
    api_host: str = Field(default="0.0.0.0", validation_alias="API_HOST")
    api_port: int = Field(default=8000, validation_alias="API_PORT")

    # ML Artifacts
    ml_artifacts_dir: str = Field(
        default="./ml_artifacts",
        validation_alias="ML_ARTIFACTS_DIR"
    )

    # Simulator
    simulator_csv_path: str = Field(
        default="./data/bombay_2024_2025.csv",
        validation_alias="SIMULATOR_CSV_PATH"
    )
    simulator_interval: float = Field(
        default=1.0,
        validation_alias="SIMULATOR_INTERVAL"
    )
    simulator_inject_anomalies: bool = Field(
        default=True,
        validation_alias="SIMULATOR_INJECT_ANOMALIES"
    )
    backend_api_url: str = Field(
        default="http://localhost:8000/internal/ingest",
        validation_alias="BACKEND_API_URL"
    )

    # CORS
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"],
        validation_alias="CORS_ORIGINS"
    )

    # Environment
    environment: str = Field(default="development", validation_alias="ENVIRONMENT")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()