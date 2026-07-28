"""
main.py
--------
Entry point for the Bengaluru Route Clearance Prediction pipeline.

Run order:
    1. Ensures traffic.db is set up
    2. Loads Traffic 3.csv -> DB (if not already loaded)
    3. Trains the dual route-time ML models (if not already trained)
    4. Launches the FastAPI server, which also serves the live
       dashboard (map + UI) from the frontend/ folder

Usage:
    python traffic/main.py
Then open:
    http://127.0.0.1:8000
"""

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "Database"))
sys.path.append(os.path.join(os.path.dirname(__file__), "Conversion"))
sys.path.append(os.path.join(os.path.dirname(__file__), "models"))

from SQL import create_tables
from csv_to_db import load_csv_to_db
from train_model import train_and_evaluate, MODEL_R1_PATH, MODEL_R2_PATH


def run_pipeline():
    print("Step 1: Setting up database...")
    create_tables()

    print("\nStep 2: Loading CSV data into database...")
    load_csv_to_db()

    print("\nStep 3: Training ML models...")
    if not (os.path.exists(MODEL_R1_PATH) and os.path.exists(MODEL_R2_PATH)):
        train_and_evaluate()
    else:
        print("Models already exist, skipping training. "
              "Delete route_model_r1.pkl / route_model_r2.pkl to retrain.")

    print("\nStep 4: Launching API + live dashboard on http://127.0.0.1:8000 ...")
    import uvicorn
    sys.path.append(os.path.dirname(__file__))  # so "api.app" resolves
    from api.app import app as fastapi_app
    uvicorn.run(fastapi_app, host="127.0.0.1", port=8000)


if __name__ == "__main__":
    run_pipeline()
