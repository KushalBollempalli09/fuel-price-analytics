"""
Reads station IDs already sitting in raw.stations, batches them
(Tankerkönig allows up to 10 IDs per request), calls prices.php,
and inserts each station's price snapshot into raw.prices.
"""

import os
import json
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

BATCH_SIZE = 10  # Tankerkönig's per-request limit for prices.php


def get_station_ids(conn):
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT station_id FROM raw.stations;")
    ids = [row[0] for row in cur.fetchall()]
    cur.close()
    return ids


def chunk(lst, size):
    """Split a list into consecutive chunks of `size`."""
    for i in range(0, len(lst), size):
        yield lst[i:i + size]


def fetch_prices(station_ids_batch):
    url = "https://creativecommons.tankerkoenig.de/json/prices.php"
    params = {
        "ids": ",".join(station_ids_batch),
        "apikey": API_KEY,
    }
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    return response.json()


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
    for batch in chunk(station_ids, BATCH_SIZE):
        data = fetch_prices(batch)
        if not data.get("ok"):
            print("API call failed for batch:", batch, "->", data)
            continue
        inserted = insert_prices(conn, data["prices"])
        total_inserted += inserted
        print(f"  Batch of {len(batch)} stations -> inserted {inserted} price records.")

    conn.close()
    print(f"Done. Total price records inserted: {total_inserted}")