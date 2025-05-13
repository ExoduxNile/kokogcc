#!/bin/bash
set -e

# Initiate download_models.py
python downloads/download_models.py

# Run FastAPI server with Uvicorn
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
