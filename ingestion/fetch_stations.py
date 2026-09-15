"""
First ingestion script.
Pulls the list of gas stations near Berlin from the Tankerkönig API
and inserts the raw JSON response into Postgres (raw.stations).
"""

import os
import json
import requests
import psycopg2
from dotenv import load_dotenv

# Load variables from .env into this script's environment
load_dotenv()

API_KEY = os.environ["TANKERKOENIG_API_KEY"]

DB_CONFIG = {
    "host": os.environ["DB_HOST"],
    "port": os.environ["DB_PORT"],
    "dbname": os.environ["DB_NAME"],
    "user": os.environ["DB_USER"],
    "password": os.environ["DB_PASSWORD"],
}

# Berlin coordinates, 5km radius, all fuel types — we'll expand to more cities later
BERLIN_LAT = 52.52
BERLIN_LNG = 13.40
RADIUS_KM = 5


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
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()  # raises an error if the request failed
    return response.json()


def insert_stations(data):
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    stations = data.get("stations", [])
    for station in stations:
        cur.execute(
            """
            INSERT INTO raw.stations (station_id, payload)
            VALUES (%s, %s)
            """,
            (station["id"], json.dumps(station)),
        )

    conn.commit()
    cur.close()
    conn.close()
    print(f"Inserted {len(stations)} station records.")


if __name__ == "__main__":
    data = fetch_stations(BERLIN_LAT, BERLIN_LNG, RADIUS_KM)
    if not data.get("ok"):
        print("API call failed:", data)
    else:
        insert_stations(data)