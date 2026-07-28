"""
SQL.py
------
Handles the SQLite database connection and table schema for the
Bengaluru Route Clearance / Traffic Prediction project.

Two tables:
    trips        -> the historical commute dataset (from "Traffic 3.csv")
    predictions  -> a live log of every prediction made through the
                    API / dashboard, used to drive the "recent activity"
                    feed on the frontend.
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "traffic.db")


def get_connection():
    """Return a connection object to the traffic database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def create_tables():
    """Create the trips and predictions tables if they don't already exist."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trips (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trip_id TEXT,
            origin_area TEXT NOT NULL,
            destination_area TEXT NOT NULL,
            route_1_name TEXT,
            route_1_dist_km REAL,
            route_1_base_time_min REAL,
            route_1_hotspot TEXT,
            route_1_clearance_delay_min REAL,
            route_1_total_time_min REAL,
            route_2_name TEXT,
            route_2_dist_km REAL,
            route_2_base_time_min REAL,
            route_2_hotspot TEXT,
            route_2_clearance_delay_min REAL,
            route_2_total_time_min REAL,
            recommended_route TEXT,
            time_saved_min REAL,
            highlighted_heavy_traffic_area TEXT,
            actionable_recommendation TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            origin_area TEXT NOT NULL,
            destination_area TEXT NOT NULL,
            route_1_name TEXT,
            route_1_pred_time_min REAL,
            route_1_band TEXT,
            route_2_name TEXT,
            route_2_pred_time_min REAL,
            route_2_band TEXT,
            recommended_route TEXT,
            time_saved_min REAL,
            bottleneck TEXT,
            alert TEXT,
            created_at TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()
    print("Tables 'trips' and 'predictions' are ready.")


if __name__ == "__main__":
    create_tables()
