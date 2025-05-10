#!/bin/bash

# Exit on any error
set -e

# Log function for better debugging
log() {
    echo "[INFO] $1"
}

log "Starting setup..."

# Step 1: Install required system packages
apt-get update -qq && apt-get install -y --no-install-recommends espeak-ng > /dev/null 2>&1

# Step 2: Create directories if they don't exist
mkdir -p models voice

# Step 3: Download model files with proper names
log "Downloading model files..."
curl -L -o kokoro-v1.0.onnx \
    "https://huggingface.co/onnx-community/Kokoro-82M-v1.0-ONNX/resolve/main/onnx/model.onnx" || {
    log "Failed to download ONNX model"
    exit 1
}

curl -L -o voices-v1.0.bin \
    "https://github.com/nazdridoy/kokoro-tts/releases/download/v1.0.0/voices-v1.0.bin" || {
    log "Failed to download voice file"
    exit 1
}

# Step 4: Install Python dependencies
log "Installing Python dependencies..."
pip install --no-cache-dir -r requirements.txt

# Step 5: Verify main.py exists
if [ ! -f "main.py" ]; then
    log "Error: main.py not found"
    exit 1
fi

log "Setup completed successfully"
exec uvicorn main:app --host 0.0.0.0 --port $PORT
