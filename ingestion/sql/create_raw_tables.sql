-- Raw landing zone: stores the untouched JSON payloads from Tankerkönig,
-- one row per API pull. Nothing here is cleaned or deduplicated yet —
-- that happens later in dbt staging models.

CREATE SCHEMA IF NOT EXISTS raw;

CREATE TABLE IF NOT EXISTS raw.stations (
    id BIGSERIAL PRIMARY KEY,
    station_id TEXT NOT NULL,
    payload JSONB NOT NULL,
    retrieved_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS raw.prices (
    id BIGSERIAL PRIMARY KEY,
    station_id TEXT NOT NULL,
    payload JSONB NOT NULL,
    retrieved_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Speeds up later dbt staging queries that filter/join by station_id
CREATE INDEX IF NOT EXISTS idx_raw_stations_station_id ON raw.stations(station_id);
CREATE INDEX IF NOT EXISTS idx_raw_prices_station_id ON raw.prices(station_id);