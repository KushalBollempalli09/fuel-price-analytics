"""
Prices ingestion script.
Reads station IDs already sitting in raw.stations, batches them
(Tankerkönig allows up to 10 IDs per request), calls prices.php,
and inserts each station's price snapshot into raw.prices.

Includes a small delay between batches and retry-with-backoff on
rate-limit / server errors, since we're now checking 1000+ stations
per run instead of just 36.
"""

import os
import json
import time
import requests
import psycopg2
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.environ["TANKERKOENIG_API_KEY"]

DB_CONFIG = {
    "host": os.environ["DB_HOST"],
    "port": os.environ["DB_PORT"],
    "dbname": os.environ["DB_NAME"],
    "user": os.environ["DB_USER"],
    "password": os.environ["DB_PASSWORD"],
}

BATCH_SIZE = 10        # Tankerkönig's per-request limit for prices.php
DELAY_BETWEEN_BATCHES = 3.5  # seconds — be polite, avoid 503s
MAX_RETRIES = 3


def get_station_ids(conn):
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT station_id FROM raw.stations;")
    ids = [row[0] for row in cur.fetchall()]
    cur.close()
    return ids


def chunk(lst, size):
    for i in range(0, len(lst), size):
        yield lst[i:i + size]


def fetch_prices(station_ids_batch):
    url = "https://creativecommons.tankerkoenig.de/json/prices.php"
    params = {
        "ids": ",".join(station_ids_batch),
        "apikey": API_KEY,
    }
    for attempt in range(1, MAX_RETRIES + 1):
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 503:
            wait = attempt * 10  # 10s, 20s, 30s — was 3/6/9, too short for this endpoint
            print(f"    503 rate-limited, waiting {wait}s (attempt {attempt}/{MAX_RETRIES})")
            time.sleep(wait)
            continue
        response.raise_for_status()
        return response.json()
    print(f"    Giving up on this batch after {MAX_RETRIES} retries.")
    return {"ok": False, "reason": "exhausted retries"}


def insert_prices(conn, prices_dict):
    cur = conn.cursor()
    for station_id, price_data in prices_dict.items():
        cur.execute(
            """
            INSERT INTO raw.prices (station_id, payload)
            VALUES (%s, %s)
            """,
            (station_id, json.dumps(price_data)),
        )
    conn.commit()
    cur.close()
    return len(prices_dict)


if __name__ == "__main__":
    conn = psycopg2.connect(**DB_CONFIG)

    station_ids = get_station_ids(conn)
    print(f"Found {len(station_ids)} stations to price-check.")

    total_inserted = 0
    total_batches = (len(station_ids) + BATCH_SIZE - 1) // BATCH_SIZE

    for i, batch in enumerate(chunk(station_ids, BATCH_SIZE), start=1):
        data = fetch_prices(batch)
        if not data.get("ok"):
            print(f"  [{i}/{total_batches}] API call failed for batch -> {data}")
        else:
            inserted = insert_prices(conn, data["prices"])
            total_inserted += inserted
            print(f"  [{i}/{total_batches}] inserted {inserted} price records.")
        time.sleep(DELAY_BETWEEN_BATCHES)

    conn.close()
    print(f"Done. Total price records inserted: {total_inserted}")