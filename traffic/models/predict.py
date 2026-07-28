"""
predict.py
-----------
Loads the trained route models and produces live route recommendations
for a given origin/destination corridor — the ML equivalent of the
`recommend_commute()` function from the original notebook, refactored
to return structured data (for the API/dashboard) instead of printing.

LIVE SIMULATION NOTE:
The dataset is a static historical snapshot (150 corridors), so there is
no real real-time traffic feed wired in here. To make the dashboard feel
"live", clearance delays are nudged by a small, deterministic jitter that
changes every 5-minute window (seeded from the corridor + time window),
which is clearly a simulated fluctuation for demo purposes rather than
real sensor data.
"""

import os
import sys
import hashlib
import random
from datetime import datetime, timezone

import joblib
import pandas as pd

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "preprocessing"))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "crud"))

from feature_engineering import FEATURE_COLUMNS, classify_traffic_band
from geo_data import get_coords

MODEL_DIR = os.path.dirname(__file__)
MODEL_R1_PATH = os.path.join(MODEL_DIR, "route_model_r1.pkl")
MODEL_R2_PATH = os.path.join(MODEL_DIR, "route_model_r2.pkl")

_model_cache = {}


def load_models():
    if "r1" not in _model_cache:
        _model_cache["r1"] = joblib.load(MODEL_R1_PATH)
        _model_cache["r2"] = joblib.load(MODEL_R2_PATH)
    return _model_cache["r1"], _model_cache["r2"]


def _live_jitter_factor(seed_key: str, spread: float = 0.18):
    """
    Deterministic pseudo-random multiplier in [1-spread, 1+spread],
    stable within a 5-minute window and seeded per-corridor so
    different corridors don't all move in lockstep.
    """
    window = int(datetime.now(timezone.utc).timestamp() // 300)  # 5-min buckets
    h = hashlib.sha256(f"{seed_key}:{window}".encode()).hexdigest()
    rng = random.Random(h)
    return 1.0 + rng.uniform(-spread, spread)


def recommend_commute(origin_row: dict, live=True):
    """
    origin_row: a dict/Series with the corridor's static feature columns
    (as stored in the trips table), e.g. one row from get_trips_by_area().

    Returns a structured recommendation dict ready for JSON/API/dashboard use.
    """
    model_r1, model_r2 = load_models()

    origin = origin_row["origin_area"]
    destination = origin_row["destination_area"]

    r1_clearance = float(origin_row["route_1_clearance_delay_min"])
    r2_clearance = float(origin_row["route_2_clearance_delay_min"])

    if live:
        r1_clearance *= _live_jitter_factor(f"{origin}->{destination}:r1")
        r2_clearance *= _live_jitter_factor(f"{origin}->{destination}:r2")

    input_data = pd.DataFrame([{
        "origin_area": origin,
        "destination_area": destination,
        "route_1_dist_km": origin_row["route_1_dist_km"],
        "route_1_base_time_min": origin_row["route_1_base_time_min"],
        "route_1_clearance_delay_min": r1_clearance,
        "route_2_dist_km": origin_row["route_2_dist_km"],
        "route_2_base_time_min": origin_row["route_2_base_time_min"],
        "route_2_clearance_delay_min": r2_clearance,
    }])[FEATURE_COLUMNS]

    est_r1_time = float(model_r1.predict(input_data)[0])
    est_r2_time = float(model_r2.predict(input_data)[0])

    r1_name = origin_row["route_1_name"]
    r2_name = origin_row["route_2_name"]
    r1_spot = origin_row["route_1_hotspot"]
    r2_spot = origin_row["route_2_hotspot"]

    r1_band = classify_traffic_band(origin_row["route_1_base_time_min"], est_r1_time)
    r2_band = classify_traffic_band(origin_row["route_2_base_time_min"], est_r2_time)

    if est_r1_time < est_r2_time:
        recommended = r1_name
        time_saved = round(est_r2_time - est_r1_time, 1)
        bottleneck = r2_spot
        alert = f"Take {r1_name} ({time_saved} min faster). Heavy clearance delay at {r2_spot}."
    else:
        recommended = r2_name
        time_saved = round(est_r1_time - est_r2_time, 1)
        bottleneck = r1_spot
        alert = f"Take {r2_name} ({time_saved} min faster). Avoid {r1_spot} due to clearance backlog."

    return {
        "origin": origin,
        "destination": destination,
        "origin_coords": get_coords(origin),
        "destination_coords": get_coords(destination),
        "route_1": {
            "name": r1_name,
            "hotspot": r1_spot,
            "hotspot_coords": get_coords(r1_spot),
            "predicted_time_min": round(est_r1_time, 1),
            "base_time_min": origin_row["route_1_base_time_min"],
            "dist_km": origin_row["route_1_dist_km"],
            "band": r1_band,
        },
        "route_2": {
            "name": r2_name,
            "hotspot": r2_spot,
            "hotspot_coords": get_coords(r2_spot),
            "predicted_time_min": round(est_r2_time, 1),
            "base_time_min": origin_row["route_2_base_time_min"],
            "dist_km": origin_row["route_2_dist_km"],
            "band": r2_band,
        },
        "recommended_route": recommended,
        "time_saved_min": time_saved,
        "bottleneck": bottleneck,
        "alert": alert,
        "live": live,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


if __name__ == "__main__":
    sys.path.append(os.path.join(os.path.dirname(__file__), "..", "crud"))
    from read import get_trips_by_area

    rows = get_trips_by_area("Jayanagar", "ITPL")
    if not rows.empty:
        result = recommend_commute(rows.iloc[0].to_dict())
        print(result)
