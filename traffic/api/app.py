"""
app.py
------
FastAPI backend for the Bengaluru Route Clearance Prediction project.

Exposes:
  - CRUD endpoints over the `trips` table
  - A live prediction endpoint that runs the trained ML models
  - A live dashboard snapshot endpoint (all corridors, current bands)
  - The recent-predictions activity feed
  - Static hosting of the frontend dashboard (map + UI)

Run with:
    uvicorn traffic.api.app:app --reload --app-dir <project_root>
or simply:
    python traffic/main.py
"""

import os
import sys

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
TRAFFIC_DIR = os.path.dirname(THIS_DIR)
PROJECT_ROOT = os.path.dirname(TRAFFIC_DIR)

sys.path.append(os.path.join(TRAFFIC_DIR, "Database"))
sys.path.append(os.path.join(TRAFFIC_DIR, "Conversion"))
sys.path.append(os.path.join(TRAFFIC_DIR, "crud"))
sys.path.append(os.path.join(TRAFFIC_DIR, "preprocessing"))
sys.path.append(os.path.join(TRAFFIC_DIR, "models"))

from SQL import create_tables
from csv_to_db import load_csv_to_db
import create as crud_create
import read as crud_read
import update as crud_update
import delete as crud_delete
from predict import recommend_commute, load_models, MODEL_R1_PATH, MODEL_R2_PATH
from geo_data import all_areas_geojson, all_hotspots_geojson

app = FastAPI(title="Bengaluru Route Clearance Prediction API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    create_tables()
    load_csv_to_db()
    if os.path.exists(MODEL_R1_PATH) and os.path.exists(MODEL_R2_PATH):
        try:
            load_models()
            print("Loaded existing trained models.")
        except Exception as e:
            print(f"Could not load models ({e}); train via train_model.py")
    else:
        print("No trained models found yet. Run traffic/models/train_model.py first.")


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class TripIn(BaseModel):
    trip_id: Optional[str] = None
    origin_area: str
    destination_area: str
    route_1_name: Optional[str] = None
    route_1_dist_km: Optional[float] = None
    route_1_base_time_min: Optional[float] = None
    route_1_hotspot: Optional[str] = None
    route_1_clearance_delay_min: Optional[float] = None
    route_1_total_time_min: Optional[float] = None
    route_2_name: Optional[str] = None
    route_2_dist_km: Optional[float] = None
    route_2_base_time_min: Optional[float] = None
    route_2_hotspot: Optional[str] = None
    route_2_clearance_delay_min: Optional[float] = None
    route_2_total_time_min: Optional[float] = None
    recommended_route: Optional[str] = None
    time_saved_min: Optional[float] = None
    highlighted_heavy_traffic_area: Optional[str] = None
    actionable_recommendation: Optional[str] = None


class TripUpdate(BaseModel):
    # All fields optional -- partial update
    origin_area: Optional[str] = None
    destination_area: Optional[str] = None
    route_1_name: Optional[str] = None
    route_1_dist_km: Optional[float] = None
    route_1_base_time_min: Optional[float] = None
    route_1_hotspot: Optional[str] = None
    route_1_clearance_delay_min: Optional[float] = None
    route_1_total_time_min: Optional[float] = None
    route_2_name: Optional[str] = None
    route_2_dist_km: Optional[float] = None
    route_2_base_time_min: Optional[float] = None
    route_2_hotspot: Optional[str] = None
    route_2_clearance_delay_min: Optional[float] = None
    route_2_total_time_min: Optional[float] = None
    recommended_route: Optional[str] = None
    time_saved_min: Optional[float] = None
    highlighted_heavy_traffic_area: Optional[str] = None
    actionable_recommendation: Optional[str] = None


# ---------------------------------------------------------------------------
# Health / meta
# ---------------------------------------------------------------------------

@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/areas")
def areas():
    """All known areas + hotspots with coordinates, for map markers."""
    return {
        "areas": all_areas_geojson(),
        "hotspots": all_hotspots_geojson(),
    }


@app.get("/api/pairs")
def pairs():
    """Unique origin/destination corridors available for prediction."""
    return crud_read.get_od_pairs()


# ---------------------------------------------------------------------------
# CRUD: trips
# ---------------------------------------------------------------------------

@app.get("/api/trips")
def list_trips():
    df = crud_read.get_all_trips()
    return df.to_dict(orient="records")


@app.get("/api/trips/{trip_row_id}")
def get_trip(trip_row_id: int):
    df = crud_read.get_trip_by_id(trip_row_id)
    if df.empty:
        raise HTTPException(status_code=404, detail="Trip not found")
    return df.to_dict(orient="records")[0]


@app.post("/api/trips", status_code=201)
def create_trip(trip: TripIn):
    new_id = crud_create.add_trip(**trip.model_dump())
    return {"id": new_id}


@app.put("/api/trips/{trip_row_id}")
def update_trip(trip_row_id: int, trip: TripUpdate):
    fields = {k: v for k, v in trip.model_dump().items() if v is not None}
    rows_affected = crud_update.update_trip(trip_row_id, **fields)
    if not rows_affected:
        raise HTTPException(status_code=404, detail="Trip not found or no changes")
    return {"updated": rows_affected}


@app.delete("/api/trips/{trip_row_id}")
def delete_trip(trip_row_id: int):
    rows_affected = crud_delete.delete_trip(trip_row_id)
    if not rows_affected:
        raise HTTPException(status_code=404, detail="Trip not found")
    return {"deleted": rows_affected}


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------

@app.get("/api/predict")
def predict(origin: str, destination: str, live: bool = True):
    rows = crud_read.get_trips_by_area(origin, destination)
    if rows.empty:
        raise HTTPException(
            status_code=404,
            detail=f"No corridor found for {origin} -> {destination}",
        )

    try:
        result = recommend_commute(rows.iloc[0].to_dict(), live=live)
    except FileNotFoundError:
        raise HTTPException(
            status_code=503,
            detail="Model not trained yet. Run traffic/models/train_model.py first.",
        )

    crud_create.log_prediction(
        origin_area=result["origin"],
        destination_area=result["destination"],
        route_1_name=result["route_1"]["name"],
        route_1_pred_time_min=result["route_1"]["predicted_time_min"],
        route_1_band=result["route_1"]["band"]["code"],
        route_2_name=result["route_2"]["name"],
        route_2_pred_time_min=result["route_2"]["predicted_time_min"],
        route_2_band=result["route_2"]["band"]["code"],
        recommended_route=result["recommended_route"],
        time_saved_min=result["time_saved_min"],
        bottleneck=result["bottleneck"],
        alert=result["alert"],
    )

    return result


@app.get("/api/predictions/recent")
def recent_predictions(limit: int = 20):
    df = crud_read.get_recent_predictions(limit)
    return df.to_dict(orient="records")


# ---------------------------------------------------------------------------
# Live dashboard snapshot -- every corridor, refreshed with simulated jitter
# ---------------------------------------------------------------------------

@app.get("/api/dashboard/live")
def dashboard_live():
    pairs_list = crud_read.get_od_pairs()
    snapshot = []
    for pair in pairs_list:
        rows = crud_read.get_trips_by_area(pair["origin_area"], pair["destination_area"])
        if rows.empty:
            continue
        try:
            result = recommend_commute(rows.iloc[0].to_dict(), live=True)
        except FileNotFoundError:
            raise HTTPException(
                status_code=503,
                detail="Model not trained yet. Run traffic/models/train_model.py first.",
            )
        snapshot.append(result)
    return {"corridors": snapshot, "count": len(snapshot)}


# ---------------------------------------------------------------------------
# Frontend static hosting (mounted last so /api/* takes priority)
# ---------------------------------------------------------------------------

FRONTEND_DIR = os.path.join(PROJECT_ROOT, "frontend")
if os.path.isdir(FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
