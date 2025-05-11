#!/bin/bash

# Exit on any error
set -e

# Log function for better debugging
log() {
    echo "[INFO] $1"
}

log "Starting setup..."


# Step 1: Create directories for model and voice files
#mkdir -p models/v1_0 voices/v1_0

# Step 2: Download model files to correct locations
log "Downloading model files..."
curl -L -o models/v1_0/model.onnx \
    "https://huggingface.co/onnx-community/Kokoro-82M-v1.0-ONNX/resolve/main/onnx/model.onnx" || {
    log "Failed to download ONNX model"
    exit 1
}

mkdir -p voices/v1_0
curl -L -o voices/v1_0/voices-v1.0.bin \
    "https://github.com/nazdridoy/kokoro-tts/releases/download/v1.0.0/voices-v1.0.bin" || {
    log "Failed to download voice file"
    exit 1
}

# Step 3: Install Python dependencies
log "Installing Python dependencies..."
pip install --no-cache-dir -r requirements.txt

# Step 4: Verify main.py exists
if [ ! -f "main.py" ]; then
    log "Error: main.py not found"
    exit 1
fi

log "Setup completed successfully"
exec uvicorn main:app --host 0.0.0.0 --port 8080
