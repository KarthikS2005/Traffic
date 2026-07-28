"""
csv_to_db.py
------------
Loads "Traffic 3.csv" into the traffic.db SQLite database (trips table).
"""

import sys
import os
import pandas as pd

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "Database"))
from SQL import get_connection, create_tables

CSV_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "Traffic 3.csv")

TRIP_COLUMNS = [
    "trip_id", "origin_area", "destination_area",
    "route_1_name", "route_1_dist_km", "route_1_base_time_min",
    "route_1_hotspot", "route_1_clearance_delay_min", "route_1_total_time_min",
    "route_2_name", "route_2_dist_km", "route_2_base_time_min",
    "route_2_hotspot", "route_2_clearance_delay_min", "route_2_total_time_min",
    "recommended_route", "time_saved_min",
    "highlighted_heavy_traffic_area", "actionable_recommendation",
]


def load_csv_to_db(csv_path=CSV_PATH):
    create_tables()  # ensure tables exist
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM trips")
    existing_rows = cursor.fetchone()[0]

    if existing_rows > 0:
        print(f"trips already has {existing_rows} rows — skipping CSV import.")
        conn.close()
        return

    df = pd.read_csv(csv_path, encoding="utf-8-sig")
    df = df[TRIP_COLUMNS]
    df.to_sql("trips", conn, if_exists="append", index=False)

    conn.close()
    print(f"Loaded {len(df)} rows from {csv_path} into traffic.db")


if __name__ == "__main__":
    load_csv_to_db()
