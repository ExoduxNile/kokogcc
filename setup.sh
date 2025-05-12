#!/bin/bash
set -euo pipefail

# Enhanced logging with timestamps
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] INFO: $1"
}

# Retry function with exponential backoff
retry() {
    local max=5
    local delay=15
    local attempt=1
    while true; do
        "$@" && break || {
            if [[ $attempt -lt $max ]]; then
                log "Attempt $attempt failed! Retrying in $delay seconds..."
                sleep $delay
                attempt=$((attempt + 1))
                delay=$((delay * 2))
            else
                log "Max attempts reached! Failed to execute: $*"
                exit 1
            fi
        }
    done
}

log "Starting setup process..."

# Step 1: System dependencies
log "Installing system packages..."
apt-get update -qq && apt-get install -y --no-install-recommends \
    espeak-ng \
    curl \
    ca-certificates

# Step 2: Directory structure
log "Creating model directories..."
mkdir -p /models /voices
chmod -R 755 /models /voices

# Step 3: Download models with retries
log "Downloading model files..."
retry curl -L -o /models/model.onnx \
    "https://github.com/nazdridoy/kokoro-tts/releases/download/v1.0.0/kokoro-v1.0.onnx"

retry curl -L -o /voices/voices-v1.0.bin \
    "https://github.com/nazdridoy/kokoro-tts/releases/download/v1.0.0/voices-v1.0.bin"

# Step 4: Verify downloads
log "Verifying file integrity..."
[ -s /models/model.onnx ] || { log "Model file is empty or missing"; exit 1; }
[ -s /voices/voices-v1.0.bin ] || { log "Voice file is empty or missing"; exit 1; }

# Step 5: Python environment
log "Setting up Python dependencies..."
pip install --no-cache-dir --upgrade pip wheel
pip install --no-cache-dir -r requirements.txt python-multipart

# Step 6: App validation
[ -f "main.py" ] || { log "main.py not found!"; exit 1; }

log "Setup completed successfully"
exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}