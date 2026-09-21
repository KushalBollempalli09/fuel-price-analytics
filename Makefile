.PHONY: ingest-stations ingest-prices dbt-run dbt-test dbt-docs up down logs all

# Start Postgres + Metabase containers
up:
	docker compose up -d

# Stop containers (data persists in the volume)
down:
	docker compose down

# Watch container logs live
logs:
	docker compose logs -f

# Pull fresh station lists across all 20 cities (run occasionally, not on a schedule)
ingest-stations:
	venv/bin/python3 ingestion/fetch_stations.py

# Pull current prices for all known stations (cron runs every 20 min)
ingest-prices:
	venv/bin/python3 ingestion/fetch_prices.py

# Build all dbt models (staging -> marts -> KPIs)
dbt-run:
	cd dbt/fuel_price_dbt && ../../venv/bin/dbt run

# Run all dbt data quality tests
dbt-test:
	cd dbt/fuel_price_dbt && ../../venv/bin/dbt test

# Generate and serve dbt's documentation site
dbt-docs:
	cd dbt/fuel_price_dbt && ../../venv/bin/dbt docs generate && ../../venv/bin/dbt docs serve

# Full pipeline: containers up, ingest once, transform, test
all: up ingest-prices dbt-run dbt-test
	@echo "Pipeline complete."