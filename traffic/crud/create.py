"""
create.py
---------
Insert new trip records and prediction-log records into the database.
"""

import sys
import os
from datetime import datetime, timezone

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "Database"))
from SQL import get_connection

TRIP_FIELDS = [
    "trip_id", "origin_area", "destination_area",
    "route_1_name", "route_1_dist_km", "route_1_base_time_min",
    "route_1_hotspot", "route_1_clearance_delay_min", "route_1_total_time_min",
    "route_2_name", "route_2_dist_km", "route_2_base_time_min",
    "route_2_hotspot", "route_2_clearance_delay_min", "route_2_total_time_min",
    "recommended_route", "time_saved_min",
    "highlighted_heavy_traffic_area", "actionable_recommendation",
]


def add_trip(**fields):
    """Insert a new trip/corridor record. Unknown keys are ignored."""
    data = {k: fields.get(k) for k in TRIP_FIELDS}

    conn = get_connection()
    cursor = conn.cursor()
    columns = ", ".join(data.keys())
    placeholders = ", ".join("?" for _ in data)
    cursor.execute(
        f"INSERT INTO trips ({columns}) VALUES ({placeholders})",
        list(data.values()),
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    print(f"Inserted trip with id={new_id}")
    return new_id


def log_prediction(origin_area, destination_area,
                    route_1_name, route_1_pred_time_min, route_1_band,
                    route_2_name, route_2_pred_time_min, route_2_band,
                    recommended_route, time_saved_min, bottleneck, alert):
    """Log a live prediction made through the API/dashboard."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO predictions
        (origin_area, destination_area,
         route_1_name, route_1_pred_time_min, route_1_band,
         route_2_name, route_2_pred_time_min, route_2_band,
         recommended_route, time_saved_min, bottleneck, alert, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        origin_area, destination_area,
        route_1_name, route_1_pred_time_min, route_1_band,
        route_2_name, route_2_pred_time_min, route_2_band,
        recommended_route, time_saved_min, bottleneck, alert,
        datetime.now(timezone.utc).isoformat(),
    ))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id


if __name__ == "__main__":
    # Example usage
    add_trip(
        trip_id="TRIP-TEST",
        origin_area="Koramangala",
        destination_area="Whitefield",
        route_1_name="via Marathahalli ORR",
        route_1_dist_km=16.9,
        route_1_base_time_min=49.6,
        route_1_hotspot="Marathahalli Multiplex",
        route_1_clearance_delay_min=23.7,
        route_1_total_time_min=73.3,
        route_2_name="via Varthur Road",
        route_2_dist_km=21.0,
        route_2_base_time_min=52.1,
        route_2_hotspot="HAL Airport Road",
        route_2_clearance_delay_min=16.6,
        route_2_total_time_min=68.7,
        recommended_route="via Varthur Road",
        time_saved_min=4.6,
        highlighted_heavy_traffic_area="Marathahalli Multiplex (via Marathahalli ORR)",
        actionable_recommendation="Take via Varthur Road (4.6 mins faster).",
    )
