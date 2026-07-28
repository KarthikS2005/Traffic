# 🚦 Bengaluru Route Clearance Prediction — Live Dashboard

Predicts which of two routes on a Bengaluru commute corridor will clear
faster, using a pair of trained Random Forest models (one per route),
served through a FastAPI backend with full CRUD over the trip data, and
visualized on a live map dashboard.

This project follows the same layout/pattern as the original
`Traffic_Clearance_Prediction` project (Database / Conversion / crud /
models / preprocessing / main.py), rebuilt around the `Traffic 3.csv`
route dataset and the model-training logic that used to live in
`model_training.ipynb` — now organized as a retrainable pipeline, wired
to a database, exposed over an API, and rendered on a live map.

## Project Structure

```
Traffic_Route_Prediction/
├── traffic/
│   ├── Database/
│   │   └── SQL.py                 # trips + predictions tables
│   ├── Conversion/
│   │   ├── csv_to_db.py           # Traffic 3.csv -> trips table
│   │   └── db_to_csv.py           # DB -> CSV export
│   ├── crud/
│   │   ├── create.py              # add_trip / log_prediction
│   │   ├── read.py                # get_all_trips / get_od_pairs / ...
│   │   ├── update.py              # update_trip
│   │   └── delete.py              # delete_trip / delete_prediction
│   ├── preprocessing/
│   │   ├── data_cleaning.py
│   │   └── feature_engineering.py # feature columns + traffic-band classifier
│   ├── models/
│   │   ├── train_model.py         # trains route_model_r1 / route_model_r2
│   │   ├── predict.py             # live recommendation engine
│   │   ├── geo_data.py            # lat/lng for areas + hotspots (map)
│   │   ├── route_model_r1.pkl     # created after training
│   │   └── route_model_r2.pkl     # created after training
│   ├── api/
│   │   └── app.py                 # FastAPI app (CRUD + predict + dashboard)
│   └── main.py                    # setup DB -> train (if needed) -> launch API
├── frontend/
│   ├── index.html                 # live dashboard shell
│   ├── style.css                  # dark traffic-ops theme
│   └── app.js                     # Leaflet map + polling + prediction UI
├── Traffic 3.csv
├── requirements.txt
├── run.bat
├── run.sh
└── README.md
```

## Setup

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Run everything (sets up the DB, trains the models on first run, and
   launches the API + dashboard):
   ```
   python traffic/main.py
   ```
   Or on Windows, double-click `run.bat`. On Mac/Linux, `./run.sh`.

3. Open the live dashboard:
   ```
   http://127.0.0.1:8000
   ```

## How It Works

1. **Data** — `Traffic 3.csv` (150 Bengaluru commute corridors, each with
   two alternate routes, distances, base times, hotspot, and clearance
   delay) is loaded into SQLite (`traffic.db`) via `Conversion/csv_to_db.py`.
2. **CRUD** — corridor records can be listed/added/updated/deleted via
   `crud/` (used directly by the scripts and exposed over the API).
3. **Preprocessing** — `preprocessing/data_cleaning.py` drops
   duplicate/invalid rows; `feature_engineering.py` defines the model
   feature columns and the Blue/Green/Yellow/Red traffic-band classifier.
4. **ML Models** — `models/train_model.py` trains two Random Forest
   pipelines (one predicting `route_1_total_time_min`, one predicting
   `route_2_total_time_min`) from origin/destination + route distance,
   base time, and clearance delay, using a `OneHotEncoder` for the area
   names. This is the same modeling approach as the original
   `model_training.ipynb`, restructured into a reusable, retrainable module.
5. **Prediction** — `models/predict.py` loads the trained models and
   reproduces the notebook's `recommend_commute()` logic as structured
   data: predicted time per route, traffic band, the recommended route,
   time saved, and the bottleneck hotspot.
6. **API** — `api/app.py` (FastAPI) exposes:
   - `GET /api/areas` — areas + hotspots with coordinates (for the map)
   - `GET /api/pairs` — known origin/destination corridors
   - `GET /api/predict?origin=&destination=` — run a live prediction
     (also logs it to the `predictions` table)
   - `GET /api/dashboard/live` — a live snapshot across every corridor
   - `GET /api/predictions/recent` — recent prediction activity feed
   - `GET/POST/PUT/DELETE /api/trips` — full CRUD over the trip data
7. **Dashboard** — `frontend/` is a static dark-themed live-ops dashboard
   (served by FastAPI itself) with a Leaflet map of Bengaluru: area and
   hotspot markers, corridor lines colored by live traffic band, an
   origin/destination predictor, and a recent-activity feed. It polls
   `/api/dashboard/live` and `/api/predictions/recent` every few seconds.

### About the "live" data

`Traffic 3.csv` is a static historical snapshot (150 rows), not a real
real-time feed. To make the dashboard behave like a live system, the
clearance-delay input to the model is nudged by a small, deterministic
jitter that changes every 5-minute window (see
`models/predict.py::_live_jitter_factor`). This is clearly a simulated
fluctuation for demo purposes — swap it out for a real traffic-sensor
feed if/when one is available, by feeding real delay values into
`recommend_commute()` instead.

## Retraining the Model

Delete `traffic/models/route_model_r1.pkl` and `route_model_r2.pkl`
(or edit `trips` via the API/CRUD first) and re-run `traffic/main.py`
to retrain on the current database contents.
