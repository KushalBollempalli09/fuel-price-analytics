"""
Expanded ingestion script.
Pulls the list of gas stations near ~20 major German cities and inserts
the raw JSON response into Postgres (raw.stations). Run this occasionally
(not on a schedule) since station lists rarely change — unlike prices.
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

RADIUS_KM = 5
DELAY_BETWEEN_CITIES = 2.5  # seconds — generous gap, this endpoint is sensitive
MAX_RETRIES = 3

CITIES = {
    "Berlin": (52.52, 13.40),
    "Hamburg": (53.55, 9.99),
    "Munich": (48.14, 11.58),
    "Cologne": (50.94, 6.96),
    "Frankfurt": (50.11, 8.68),
    "Stuttgart": (48.78, 9.18),
    "Duesseldorf": (51.23, 6.78),
    "Dortmund": (51.51, 7.47),
    "Essen": (51.46, 7.01),
    "Leipzig": (51.34, 12.37),
    "Bremen": (53.08, 8.81),
    "Dresden": (51.05, 13.74),
    "Hannover": (52.37, 9.73),
    "Nuremberg": (49.45, 11.08),
    "Duisburg": (51.43, 6.76),
    "Bochum": (51.48, 7.22),
    "Wuppertal": (51.26, 7.15),
    "Bielefeld": (52.02, 8.53),
    "Bonn": (50.74, 7.10),
    "Mannheim": (49.49, 8.47),
}


def fetch_stations(lat, lng, radius):
    url = "https://creativecommons.tankerkoenig.de/json/list.php"
    params = {
        "lat": lat,
        "lng": lng,
        "rad": radius,
        "sort": "dist",
        "type": "all",
        "apikey": API_KEY,
    }
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
    return {"ok": False, "reason": "exhausted retries"}


def insert_stations(conn, data):
    cur = conn.cursor()
    stations = data.get("stations", [])
    for station in stations:
        cur.execute(
            "INSERT INTO raw.stations (station_id, payload) VALUES (%s, %s)",
            (station["id"], json.dumps(station)),
        )
    conn.commit()
    cur.close()
    return len(stations)


if __name__ == "__main__":
    conn = psycopg2.connect(**DB_CONFIG)
    total = 0

    for city, (lat, lng) in CITIES.items():
        data = fetch_stations(lat, lng, RADIUS_KM)
        if not data.get("ok"):
            print(f"{city}: failed -> {data}")
        else:
            inserted = insert_stations(conn, data)
            total += inserted
            print(f"{city}: inserted {inserted} stations")
        time.sleep(DELAY_BETWEEN_CITIES)

    conn.close()
    print(f"Done. Total stations inserted: {total}")