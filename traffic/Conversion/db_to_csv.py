"""
db_to_csv.py
------------
Exports the trips table (and optionally the predictions log) from
traffic.db back into CSV files. Useful after CRUD edits, to produce
an updated dataset for retraining.
"""

import sys
import os
import pandas as pd

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "Database"))
from SQL import get_connection

TRIPS_OUTPUT_CSV = os.path.join(os.path.dirname(__file__), "..", "..", "trips_export.csv")
PREDICTIONS_OUTPUT_CSV = os.path.join(os.path.dirname(__file__), "..", "..", "predictions_export.csv")


def export_trips_to_csv(output_path=TRIPS_OUTPUT_CSV):
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM trips", conn)
    conn.close()

    df.to_csv(output_path, index=False)
    print(f"Exported {len(df)} trip rows to {output_path}")


def export_predictions_to_csv(output_path=PREDICTIONS_OUTPUT_CSV):
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM predictions", conn)
    conn.close()

    df.to_csv(output_path, index=False)
    print(f"Exported {len(df)} prediction rows to {output_path}")


if __name__ == "__main__":
    export_trips_to_csv()
    export_predictions_to_csv()
