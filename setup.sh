#!/bin/bash

# Exit on any error
set -e

# Log function for better debugging
log() {
    echo "[INFO] $1"
}

log "Starting setup..."

# Step 1: Install system dependencies
log "Installing system dependencies..."
apt-get update -qq && apt-get install -y --no-install-recommends espeak-ng > /dev/null 2>&1

# Step 2: Create directories with proper permissions
log "Creating directories..."
mkdir -p models/v1_0 voices/v1_0
chmod -R 755 models voices

# Step 3: Download model files to correct locations
log "Downloading model files to root..."
sleep 50
curl -L -o /models/model.onnx \
    "https://github.com/nazdridoy/kokoro-tts/releases/download/v1.0.0/kokoro-v1.0.onnx" || {
    log "Failed to download ONNX model"
    exit 1
}
sleep 50
curl -L -o /voices/voices-v1.0.bin \
    "https://github.com/nazdridoy/kokoro-tts/releases/download/v1.0.0/voices-v1.0.bin" || {
    log "Failed to download voice file"
    exit 1
}

# Step 5: Install Python dependencies
log "Installing Python dependencies..."
pip install --no-cache-dir -r requirements.txt python-multipart

# Step 6: Verify main.py exists
if [ ! -f "main.py" ]; then
    log "Error: main.py not found"
    exit 1
fi

log "Setup completed successfully"
exec uvicorn main:app --host 0.0.0.0 --port ${PORT}
