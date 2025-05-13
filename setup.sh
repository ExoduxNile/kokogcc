#!/bin/bash

# Exit on any error
set -e

# Define file URLs and destinations
VOICES_URL="https://github.com/nazdridoy/kokoro-tts/releases/download/v1.0.0/voices-v1.0.bin"
ONNX_URL="https://github.com/nazdridoy/kokoro-tts/releases/download/v1.0.0/kokoro-v1.0.onnx"
VOICES_FILE="voices-v1.0.bin"
ONNX_FILE="kokoro-v1.0.onnx"

# Create static and templates directories if they don't exist
mkdir -p static templates

# Function to download a file using Python urllib.request
download_file() {
    local url=$1
    local output=$2
    
    if [ -f "$output" ]; then
        echo "$output already exists, skipping download"
    else
        echo "Downloading $output..."
        $PYTHON -c "import urllib.request; urllib.request.urlretrieve('$url', '$output')"
        if [ $? -eq 0 ]; then
            echo "Successfully downloaded $output"
        else
            echo "Error downloading $output"
            exit 1
        fi
    fi
}

# Download required files
download_file "$VOICES_URL" "$VOICES_FILE"
download_file "$ONNX_URL" "$ONNX_FILE"

# Install Python dependencies without caching (local only)
if [ -z "$RENDER" ]; then
    echo "Installing Python dependencies..."
    $PYTHON -m pip install --no-cache-dir -r requirements.txt

    # Log installed packages
    $PYTHON -m pip list

    # Verify uvicorn is installed
    if ! command -v uvicorn &> /dev/null; then
        echo "Error: uvicorn not found, attempting reinstall..."
        $PYTHON -m pip install --no-cache-dir uvicorn>=0.34.2
        if ! command -v uvicorn &> /dev/null; then
            echo "Error: uvicorn still not found after reinstall"
            exit 1
        fi
    fi
fi

# Verify that app.py exists
if [ -f "app.py" ]; then
    echo "app.py exists, continuing..."
else
    echo "Error: app.py not found in current directory"
    exit 1
fi

# Start the server with Uvicorn (local only)
if [ -z "$RENDER" ]; then
    echo "Starting FastAPI server with Uvicorn..."
    exec uvicorn app:app --host 0.0.0.0 --port ${PORT:-8080} --workers 1
fi
