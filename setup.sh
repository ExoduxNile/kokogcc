#!/bin/bash
set -e

# Create models directory if it doesn't exist
mkdir -p models
mkdir -p voices
# Download model files if they don't exist
if [ ! -f "voices/voices-v1.0.bin" ]; then
    echo "Downloading voices-v1.0.bin..."
    wget -q https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin -O models/voices-v1.0.bin
fi

if [ ! -f "models/kokoro-v1.0.onnx" ]; then
    echo "Downloading kokoro-v1.0.onnx..."
    wget -q https://github.com/nazdridoy/kokoro-tts/releases/download/v1.0.0/kokoro-v1.0.onnx -O models/kokoro-v1.0.onnx
fi

# Install Python dependencies
echo "Installing Python dependencies..."
pip install --no-cache-dir -r requirements.txt

# Verify downloads
echo "Verifying model files..."
ls -lh models/

# Run FastAPI server with Uvicorn
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
