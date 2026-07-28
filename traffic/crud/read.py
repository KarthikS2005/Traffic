"""
read.py
-------
Fetch/query trip and prediction records from the database.
"""

import sys
import os
import pandas as pd

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "Database"))
from SQL import get_connection


def get_all_trips():
    """Return all trip/corridor records as a pandas DataFrame."""
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM trips", conn)
    conn.close()
    return df


def get_trip_by_id(trip_row_id):
    """Return a single trip by its primary key id."""
    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT * FROM trips WHERE id = ?", conn, params=(trip_row_id,)
    )
    conn.close()
    return df


def get_trips_by_area(origin=None, destination=None):
    """Return trips filtered by origin and/or destination area."""
    query = "SELECT * FROM trips WHERE 1=1"
    params = []
    if origin:
        query += " AND origin_area = ?"
        params.append(origin)
    if destination:
        query += " AND destination_area = ?"
        params.append(destination)

    conn = get_connection()
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df


def get_od_pairs():
    """Return the list of unique (origin_area, destination_area) corridors."""
    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT DISTINCT origin_area, destination_area FROM trips "
        "ORDER BY origin_area, destination_area", conn
    )
    conn.close()
    return df.to_dict(orient="records")


def get_all_areas():
    """Return the sorted list of unique area names (origins + destinations)."""
    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT origin_area AS area FROM trips "
        "UNION SELECT destination_area AS area FROM trips", conn
    )
    conn.close()
    return sorted(df["area"].dropna().unique().tolist())


def get_recent_predictions(limit=20):
    """Return the most recent prediction-log entries."""
    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT * FROM predictions ORDER BY id DESC LIMIT ?", conn, params=(limit,)
    )
    conn.close()
    return df


def get_all_predictions():
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM predictions ORDER BY id DESC", conn)
    conn.close()
    return df


if __name__ == "__main__":
    print(get_all_trips().head())
    print(get_od_pairs()[:5])
