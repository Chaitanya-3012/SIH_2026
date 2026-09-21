-- SkyGuard AI Database Schema
-- PostgreSQL + TimescaleDB
-- Run this against a TimescaleDB-enabled PostgreSQL instance

-- Enable TimescaleDB extension (required before creating hypertables)
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- ============================================================
-- stations: Master list of AWS stations
-- station_id = usaf || wban (matches NOAA ISD scheme)
-- ============================================================
CREATE TABLE stations (
    station_id      VARCHAR(20) PRIMARY KEY,
    usaf            VARCHAR(6)  NOT NULL,
    wban            VARCHAR(5)  NOT NULL,
    name            TEXT        NOT NULL,
    country         VARCHAR(2)  NOT NULL DEFAULT 'IN',
    state           TEXT,
    district        TEXT,
    latitude        DOUBLE PRECISION NOT NULL,
    longitude       DOUBLE PRECISION NOT NULL,
    is_metro        BOOLEAN     NOT NULL DEFAULT FALSE,
    deployment_tier VARCHAR(10) NOT NULL DEFAULT 'central' CHECK (deployment_tier IN ('metro', 'central')),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_stations_usaf_wban ON stations (usaf, wban);
CREATE INDEX idx_stations_deployment_tier ON stations (deployment_tier);
CREATE INDEX idx_stations_location ON stations (latitude, longitude);

-- ============================================================
-- readings: Raw sensor readings (hypertable partitioned on ts)
-- source: 'live' | 'simulator' | 'historical'
-- ============================================================
CREATE TABLE readings (
    reading_id      BIGSERIAL,
    station_id      VARCHAR(20) NOT NULL REFERENCES stations(station_id) ON DELETE CASCADE,
    ts              TIMESTAMPTZ NOT NULL,
    temperature_c   DOUBLE PRECISION,
    pressure_hpa    DOUBLE PRECISION,
    humidity_pct    DOUBLE PRECISION,
    source          VARCHAR(20) NOT NULL DEFAULT 'live' CHECK (source IN ('live', 'simulator', 'historical')),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (reading_id, ts)
);

-- Convert to hypertable partitioned by time
SELECT create_hypertable('readings', 'ts', chunk_time_interval => INTERVAL '1 day', if_not_exists => TRUE);

-- Indexes for common query patterns
CREATE INDEX idx_readings_station_ts_desc ON readings (station_id, ts DESC);
CREATE INDEX idx_readings_source ON readings (source);
CREATE INDEX idx_readings_ts ON readings (ts DESC);

-- ============================================================
-- anomalies: One row per flagged reading
-- shap_values: JSONB for per-feature attribution
-- status: 'open' -> 'reviewed' | 'dismissed' (analyst workflow)
-- ============================================================
CREATE TABLE anomalies (
    anomaly_id      BIGSERIAL PRIMARY KEY,
    reading_id      BIGINT      NOT NULL REFERENCES readings(reading_id) ON DELETE CASCADE,
    station_id      VARCHAR(20) NOT NULL REFERENCES stations(station_id) ON DELETE CASCADE,
    ts              TIMESTAMPTZ NOT NULL,
    anomaly_type    VARCHAR(30) NOT NULL CHECK (anomaly_type IN ('spike', 'drift', 'frozen', 'dropout', 'multivariate', 'unknown')),
    confidence_score DOUBLE PRECISION NOT NULL CHECK (confidence_score >= 0 AND confidence_score <= 1),
    severity        VARCHAR(10) NOT NULL CHECK (severity IN ('low', 'medium', 'high')),
    root_cause_tag  VARCHAR(50),
    shap_values     JSONB,
    component_scores JSONB,
    status          VARCHAR(20) NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'reviewed', 'dismissed')),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    reviewed_at     TIMESTAMPTZ,
    reviewed_by     VARCHAR(100)
);

-- Indexes
CREATE INDEX idx_anomalies_station_ts_desc ON anomalies (station_id, ts DESC);
CREATE INDEX idx_anomalies_status ON anomalies (status) WHERE status = 'open';
CREATE INDEX idx_anomalies_reading_id ON anomalies (reading_id);
CREATE INDEX idx_anomalies_ts ON anomalies (ts DESC);

-- ============================================================
-- drift_events: Separate from anomalies (different urgency class)
-- parameter: 'temperature' | 'pressure' | 'humidity'
-- ============================================================
CREATE TABLE drift_events (
    drift_id        BIGSERIAL PRIMARY KEY,
    station_id      VARCHAR(20) NOT NULL REFERENCES stations(station_id) ON DELETE CASCADE,
    ts              TIMESTAMPTZ NOT NULL,
    parameter       VARCHAR(30) NOT NULL CHECK (parameter IN ('temperature', 'pressure', 'humidity')),
    trend_value     DOUBLE PRECISION NOT NULL,
    degradation_flag BOOLEAN    NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_drift_events_station_ts ON drift_events (station_id, ts DESC);
CREATE INDEX idx_drift_events_degradation ON drift_events (degradation_flag) WHERE degradation_flag = TRUE;

-- ============================================================
-- sensor_health: Rolling time series per station (hypertable)
-- composite_score: 0-1, label: 'healthy' | 'degrading' | 'faulty'
-- ============================================================
CREATE TABLE sensor_health (
    health_id            BIGSERIAL,
    station_id           VARCHAR(20) NOT NULL REFERENCES stations(station_id) ON DELETE CASCADE,
    ts                   TIMESTAMPTZ NOT NULL,
    composite_score      DOUBLE PRECISION NOT NULL CHECK (composite_score >= 0 AND composite_score <= 1),
    label                VARCHAR(20) NOT NULL CHECK (label IN ('healthy', 'degrading', 'faulty')),
    anomaly_frequency    DOUBLE PRECISION,
    drift_trend          DOUBLE PRECISION,
    data_completeness    DOUBLE PRECISION,
    reconstruction_error_trend DOUBLE PRECISION,
    variance_behavior    DOUBLE PRECISION,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (health_id, ts)
);

SELECT create_hypertable('sensor_health', 'ts', chunk_time_interval => INTERVAL '1 day', if_not_exists => TRUE);

CREATE INDEX idx_sensor_health_station_ts_desc ON sensor_health (station_id, ts DESC);
CREATE INDEX idx_sensor_health_label ON sensor_health (label);

-- ============================================================
-- model_versions: Model versioning for reproducibility
-- ============================================================
CREATE TABLE model_versions (
    model_id        BIGSERIAL PRIMARY KEY,
    model_type      VARCHAR(50) NOT NULL,
    version_tag     VARCHAR(50) NOT NULL,
    metrics         JSONB,
    is_active       BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    activated_at    TIMESTAMPTZ
);

CREATE UNIQUE INDEX idx_model_versions_type_tag ON model_versions (model_type, version_tag);
CREATE INDEX idx_model_versions_active ON model_versions (is_active) WHERE is_active = TRUE;

-- ============================================================
-- benchmark_results: Evaluation results per model/station
-- ============================================================
CREATE TABLE benchmark_results (
    benchmark_id    BIGSERIAL PRIMARY KEY,
    model_id        BIGINT      NOT NULL REFERENCES model_versions(model_id) ON DELETE CASCADE,
    station_id      VARCHAR(20) REFERENCES stations(station_id) ON DELETE SET NULL,
    precision_score DOUBLE PRECISION,
    recall_score    DOUBLE PRECISION,
    f1_score        DOUBLE PRECISION,
    false_positive_rate DOUBLE PRECISION,
    evaluated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_benchmark_model ON benchmark_results (model_id);
CREATE INDEX idx_benchmark_station ON benchmark_results (station_id);

-- ============================================================
-- users: Minimal placeholder for analyst review workflow
-- ============================================================
CREATE TABLE users (
    user_id       BIGSERIAL PRIMARY KEY,
    email         VARCHAR(255) NOT NULL UNIQUE,
    display_name  VARCHAR(100) NOT NULL,
    role          VARCHAR(20) NOT NULL DEFAULT 'analyst' CHECK (role IN ('analyst', 'admin')),
    is_active     BOOLEAN NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- Trigger function for updated_at timestamp
-- ============================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to stations table
DROP TRIGGER IF EXISTS update_stations_updated_at ON stations;
CREATE TRIGGER update_stations_updated_at
    BEFORE UPDATE ON stations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================
-- Optional: TimescaleDB compression policy (uncomment when needed)
-- ============================================================
-- ALTER TABLE readings SET (timescaledb.compress, timescaledb.compress_segmentby = 'station_id');
-- SELECT add_compression_policy('readings', INTERVAL '30 days');
-- 
-- ALTER TABLE sensor_health SET (timescaledb.compress, timescaledb.compress_segmentby = 'station_id');
-- SELECT add_compression_policy('sensor_health', INTERVAL '30 days');
-- 
-- ALTER TABLE anomalies SET (timescaledb.compress, timescaledb.compress_segmentby = 'station_id');
-- SELECT add_compression_policy('anomalies', INTERVAL '90 days');