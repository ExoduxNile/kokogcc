#!/bin/bash

# Exit on any error
set -e

# Define file URLs and destinations
VOICES_URL="https://github.com/nazdridoy/kokoro-tts/releases/download/v1.0.0/voices-v1.0.bin"
ONNX_URL="https://github.com/nazdridoy/kokoro-tts/releases/download/v1.0.0/kokoro-v1.0.onnx"
VOICES_FILE="voices-v1.0.bin"
ONNX_FILE="kokoro-v1.0.onnx"

# Check disk space (require at least 500MB free)
MIN_SPACE_MB=500
AVAILABLE_SPACE_MB=$(df -m . | tail -1 | awk '{print $4}')
if [ "$AVAILABLE_SPACE_MB" -lt "$MIN_SPACE_MB" ]; then
    echo "Error: Insufficient disk space. Need at least ${MIN_SPACE_MB}MB, but only ${AVAILABLE_SPACE_MB}MB available."
    exit 1
fi

# Create static and templates directories if they don't exist
mkdir -p static templates

# Function to download a file if it doesn't exist
download_file() {
    local url=$1
    local output=$2
    
    if [ -f "$output" ]; then
        echo "$output already exists, skipping download"
    else
        echo "Downloading $output..."
        curl -L --retry 3 -o "$output" "$url"
        if [ $? -eq 0 ]; then
            echo "Successfully downloaded $output"
        else
            echo "Failed to download $output"
            exit 1
        fi
    fi
}

# Download required files
download_file "$VOICES_URL" "$VOICES_FILE"
download_file "$ONNX_URL" "$ONNX_FILE"

# Install Python dependencies
echo "Installing Python dependencies..."
pip install --no-cache-dir fastapi uvicorn numpy soundfile kokoro_onnx pydantic onnxruntime

# Verify that app.py exists
if [ ! -f "app.py" ]; then
    echo "Error: app.py not found in current directory"
    exit 1
fi

# Start the server with Uvicorn
echo "Starting FastAPI server with Uvicorn..."
exec uvicorn app:app --host 0.0.0.0 --port ${PORT:-8080} --workers 4
