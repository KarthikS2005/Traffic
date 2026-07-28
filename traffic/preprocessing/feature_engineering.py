"""
feature_engineering.py
-----------------------
Derived features and the traffic-band classifier shared by both the
training pipeline and the live prediction/dashboard code.
"""

import pandas as pd

FEATURE_COLUMNS = [
    "origin_area",
    "destination_area",
    "route_1_dist_km",
    "route_1_base_time_min",
    "route_1_clearance_delay_min",
    "route_2_dist_km",
    "route_2_base_time_min",
    "route_2_clearance_delay_min",
]

CATEGORICAL_FEATURES = ["origin_area", "destination_area"]
NUMERIC_FEATURES = [c for c in FEATURE_COLUMNS if c not in CATEGORICAL_FEATURES]

TARGET_ROUTE_1 = "route_1_total_time_min"
TARGET_ROUTE_2 = "route_2_total_time_min"


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds a congestion_ratio for each route (total_time / base_time),
    which is useful for analysis/dashboarding even though the ML
    pipeline itself learns directly from the raw feature columns.
    """
    df = df.copy()
    if "route_1_total_time_min" in df.columns:
        df["route_1_congestion_ratio"] = (
            df["route_1_total_time_min"] / df["route_1_base_time_min"]
        )
    if "route_2_total_time_min" in df.columns:
        df["route_2_congestion_ratio"] = (
            df["route_2_total_time_min"] / df["route_2_base_time_min"]
        )
    return df


def classify_traffic_band(base_time_min, total_time_min):
    """
    Classifies route congestion into Blue, Green, Yellow, or Red bands
    based on the ratio of predicted/actual total time to free-flow base time.
    """
    ratio = total_time_min / base_time_min if base_time_min else 1.0
    if ratio <= 0.95:
        return {"code": "blue", "label": "Very Low Traffic", "emoji": "🔵"}
    elif ratio <= 1.15:
        return {"code": "green", "label": "Smooth Flow", "emoji": "🟢"}
    elif ratio <= 1.40:
        return {"code": "yellow", "label": "Moderate Traffic", "emoji": "🟡"}
    else:
        return {"code": "red", "label": "Heavy Congestion", "emoji": "🔴"}


if __name__ == "__main__":
    sample = pd.read_csv("../../Traffic 3.csv", encoding="utf-8-sig")
    sample = add_features(sample)
    print(sample.head())
