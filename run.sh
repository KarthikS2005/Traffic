#!/usr/bin/env bash
set -e
echo "Installing dependencies..."
pip install -r requirements.txt

echo "Running Traffic Route Clearance Prediction pipeline..."
python3 traffic/main.py
