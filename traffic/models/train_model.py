"""
train_model.py
---------------
Trains two Random Forest Regressors — one per route — to predict
route_1_total_time_min and route_2_total_time_min for a given
origin/destination corridor, using the historical "Traffic 3.csv"
data (loaded via the trips table / CRUD layer, same pattern as the
rest of this project).

This replaces the exploratory logic that used to live in
model_training.ipynb, now organized as an importable, retrainable
pipeline consistent with the project's CRUD + models structure.
"""

import sys
import os
import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "preprocessing"))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "crud"))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "Conversion"))

from data_cleaning import clean_data
from feature_engineering import (
    FEATURE_COLUMNS, CATEGORICAL_FEATURES, NUMERIC_FEATURES,
    TARGET_ROUTE_1, TARGET_ROUTE_2,
)

MODEL_DIR = os.path.dirname(__file__)
MODEL_R1_PATH = os.path.join(MODEL_DIR, "route_model_r1.pkl")
MODEL_R2_PATH = os.path.join(MODEL_DIR, "route_model_r2.pkl")


def load_and_prepare_data():
    """Load training data from the database (falls back to CSV import first)."""
    from csv_to_db import load_csv_to_db
    from read import get_all_trips

    load_csv_to_db()  # no-op if already loaded
    df = get_all_trips()
    df = clean_data(df)
    return df


def build_pipeline():
    preprocessor = ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES),
            ("num", "passthrough", NUMERIC_FEATURES),
        ]
    )
    return Pipeline(steps=[
        ("preprocessor", preprocessor),
        ("regressor", RandomForestRegressor(n_estimators=200, random_state=42)),
    ])


def train_and_evaluate():
    df = load_and_prepare_data()
    print(f"Training on {len(df)} cleaned corridor records.\n")

    X = df[FEATURE_COLUMNS]
    y_r1 = df[TARGET_ROUTE_1]
    y_r2 = df[TARGET_ROUTE_2]

    X_train, X_test, y_train_r1, y_test_r1, y_train_r2, y_test_r2 = train_test_split(
        X, y_r1, y_r2, test_size=0.2, random_state=42
    )

    model_r1 = build_pipeline()
    model_r2 = build_pipeline()

    model_r1.fit(X_train, y_train_r1)
    model_r2.fit(X_train, y_train_r2)

    print("Machine learning models trained successfully.\n")

    pred_r1 = model_r1.predict(X_test)
    pred_r2 = model_r2.predict(X_test)

    r1_r2_score = r2_score(y_test_r1, pred_r1)
    r1_mae = mean_absolute_error(y_test_r1, pred_r1)
    r1_rmse = np.sqrt(mean_squared_error(y_test_r1, pred_r1))

    r2_r2_score = r2_score(y_test_r2, pred_r2)
    r2_mae = mean_absolute_error(y_test_r2, pred_r2)
    r2_rmse = np.sqrt(mean_squared_error(y_test_r2, pred_r2))

    actual_rec = np.where(y_test_r1 < y_test_r2, 1, 2)
    predicted_rec = np.where(pred_r1 < pred_r2, 1, 2)
    rec_accuracy = (actual_rec == predicted_rec).mean() * 100

    print("=== Model Evaluation Metrics ===")
    print(f"Route 1 Model -> R2: {r1_r2_score:.4f} | MAE: {r1_mae:.2f} min | RMSE: {r1_rmse:.2f} min")
    print(f"Route 2 Model -> R2: {r2_r2_score:.4f} | MAE: {r2_mae:.2f} min | RMSE: {r2_rmse:.2f} min")
    print(f"Recommendation accuracy: {rec_accuracy:.1f}%\n")

    joblib.dump(model_r1, MODEL_R1_PATH)
    joblib.dump(model_r2, MODEL_R2_PATH)
    print(f"Saved models to:\n  {MODEL_R1_PATH}\n  {MODEL_R2_PATH}")

    metrics = {
        "route_1": {"r2": r1_r2_score, "mae": r1_mae, "rmse": r1_rmse},
        "route_2": {"r2": r2_r2_score, "mae": r2_mae, "rmse": r2_rmse},
        "recommendation_accuracy_pct": rec_accuracy,
        "n_train": len(X_train),
        "n_test": len(X_test),
    }
    return model_r1, model_r2, metrics


if __name__ == "__main__":
    train_and_evaluate()
