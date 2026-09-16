"""
Prices ingestion script.
Reads station IDs already sitting in raw.stations, batches them,
calls prices.php, and inserts each station's price snapshot into raw.prices.

Includes retry/backoff on rate limits and network errors, and a lock file
to prevent overlapping cron runs if one execution takes longer than the
scheduled interval.
"""

import os
import json
import time
import sys
from datetime import datetime
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

BATCH_SIZE = 10
DELAY_BETWEEN_BATCHES = 3.5
MAX_RETRIES = 3

LOCK_FILE = "/tmp/fetch_prices.lock"
STALE_LOCK_SECONDS = 25 * 60  # if a lock is older than 25 min, assume the run that made it crashed


def acquire_lock():
    if os.path.exists(LOCK_FILE):
        age = time.time() - os.path.getmtime(LOCK_FILE)
        if age < STALE_LOCK_SECONDS:
            return False  # a real, recent run is presumably still active
        print(f"Found a stale lock ({int(age)}s old) — a previous run likely crashed. Removing it.")
        os.remove(LOCK_FILE)
    with open(LOCK_FILE, "w") as f:
        f.write(str(os.getpid()))
    return True


def release_lock():
    try:
        os.remove(LOCK_FILE)
    except FileNotFoundError:
        pass


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
    params = {"ids": ",".join(station_ids_batch), "apikey": API_KEY}
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.get(url, params=params, timeout=15)
            if response.status_code == 503:
                wait = attempt * 10
                print(f"    503 rate-limited, waiting {wait}s (attempt {attempt}/{MAX_RETRIES})")
                time.sleep(wait)
                continue
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            wait = attempt * 5
            print(f"    Network error ({type(e).__name__}), retrying in {wait}s (attempt {attempt}/{MAX_RETRIES})")
            time.sleep(wait)
    print(f"    Giving up on this batch after {MAX_RETRIES} retries.")
    return {"ok": False, "reason": "exhausted retries"}


def insert_prices(conn, prices_dict):
    cur = conn.cursor()
    for station_id, price_data in prices_dict.items():
        cur.execute(
            "INSERT INTO raw.prices (station_id, payload) VALUES (%s, %s)",
            (station_id, json.dumps(price_data)),
        )
    conn.commit()
    cur.close()
    return len(prices_dict)


if __name__ == "__main__":
    print(f"\n=== Run started: {datetime.now().isoformat()} ===")

    if not acquire_lock():
        print("Another run is already in progress (lock file present). Skipping this run.")
        sys.exit(0)

    try:
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
    finally:
        release_lock()