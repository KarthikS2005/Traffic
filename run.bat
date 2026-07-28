@echo off
echo Installing dependencies...
pip install -r requirements.txt

echo Running Traffic Route Clearance Prediction pipeline...
python traffic\main.py

pause
