"""
update.py
---------
Update an existing trip record in the database.
"""

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "Database"))
from SQL import get_connection


def update_trip(trip_row_id, **fields):
    """
    Update fields of a trip by its primary key id.
    Example: update_trip(3, route_1_dist_km=18.2, route_1_total_time_min=70.0)
    """
    if not fields:
        print("No fields provided to update.")
        return 0

    conn = get_connection()
    cursor = conn.cursor()

    set_clause = ", ".join(f"{key} = ?" for key in fields.keys())
    values = list(fields.values()) + [trip_row_id]

    cursor.execute(f"UPDATE trips SET {set_clause} WHERE id = ?", values)
    conn.commit()
    rows_affected = cursor.rowcount
    conn.close()

    print(f"Updated {rows_affected} row(s) with id={trip_row_id}")
    return rows_affected


if __name__ == "__main__":
    update_trip(1, route_1_dist_km=17.5)
