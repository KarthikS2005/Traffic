"""
delete.py
---------
Delete trip or prediction-log records from the database.
"""

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "Database"))
from SQL import get_connection


def delete_trip(trip_row_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM trips WHERE id = ?", (trip_row_id,))
    conn.commit()
    rows_affected = cursor.rowcount
    conn.close()
    print(f"Deleted {rows_affected} trip row(s) with id={trip_row_id}")
    return rows_affected


def delete_prediction(prediction_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM predictions WHERE id = ?", (prediction_id,))
    conn.commit()
    rows_affected = cursor.rowcount
    conn.close()
    print(f"Deleted {rows_affected} prediction row(s) with id={prediction_id}")
    return rows_affected


if __name__ == "__main__":
    delete_trip(1)
