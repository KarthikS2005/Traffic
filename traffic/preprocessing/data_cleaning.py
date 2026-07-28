"""
data_cleaning.py
-----------------
Basic cleaning utilities: handle missing values, remove duplicates,
and filter invalid rows for the Bengaluru route/corridor dataset.
"""

import pandas as pd

REQUIRED_NUMERIC_COLS = [
    "route_1_dist_km", "route_1_base_time_min", "route_1_clearance_delay_min",
    "route_1_total_time_min",
    "route_2_dist_km", "route_2_base_time_min", "route_2_clearance_delay_min",
    "route_2_total_time_min",
]

REQUIRED_COLS = ["origin_area", "destination_area"] + REQUIRED_NUMERIC_COLS


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # Drop exact duplicate rows
    df = df.drop_duplicates()

    # Drop rows missing the critical columns
    df = df.dropna(subset=REQUIRED_COLS)

    # Remove invalid/negative values — distances and times must be positive
    for col in REQUIRED_NUMERIC_COLS:
        df = df[df[col] > 0]

    return df.reset_index(drop=True)


if __name__ == "__main__":
    sample = pd.read_csv("../../Traffic 3.csv", encoding="utf-8-sig")
    cleaned = clean_data(sample)
    print(f"Rows before cleaning: {len(sample)}, after cleaning: {len(cleaned)}")
