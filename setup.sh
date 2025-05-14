#!/bin/bash

# Unified setup script for Kokoro TTS (works with and without Docker)

# Configuration variables
PYTHON_VERSION="3.12"
APP_DIR="/app"
MODEL_URLS=(
    "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin"
    "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx"
)

# Function to install system dependencies
install_system_deps() {
    echo "Installing system dependencies..."
    sudo apt-get update && sudo apt-get install -y \
        libsndfile1 \
        wget \
        python3 \
        python3-pip \
        python3-venv \
        nodejs \
        npm \
        && sudo rm -rf /var/lib/apt/lists/*
}

# Function to download models
download_models() {
    echo "Downloading models..."
    mkdir -p models
    for url in "${MODEL_URLS[@]}"; do
        filename=$(basename "$url")
        if [ ! -f "models/$filename" ]; then
            echo "Downloading $filename..."
            wget -q "$url" -O "models/$filename"
            if [ $? -ne 0 ]; then
                echo "[ERROR] Failed to download $filename. Please check your internet connection or the URL."
            fi
        else
            echo "Model $filename already exists, skipping download"
        fi
    done

    # Check if voices file was downloaded successfully
    if [ ! -f "models/voices-v1.0.bin" ]; then
        echo ""
        echo "[ERROR] voices-v1.0.bin not found after download!"
        echo "You can manually download it with:"
        echo "wget -O models/voices-v1.0.bin https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin"
        exit 1
    fi
}

# Function to setup Python environment
setup_python_env() {
    echo "Setting up Python environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install --no-cache-dir -r requirements.txt
}

# Function to clean caches
clean_caches() {
    echo "Cleaning caches..."
    npm cache clean --force
    pip cache purge
    find . -type d -name "__pycache__" -exec rm -r {} +
}

# Function to setup directories
setup_directories() {
    echo "Creating necessary directories..."
    mkdir -p uploads
    mkdir -p static
}

# Main setup function
main_setup() {
    # Check if running in Docker
    if [ -f /.dockerenv ]; then
        echo "Running inside Docker container - skipping some setup steps"
    else
        install_system_deps
    fi

    setup_python_env
    download_models
    setup_directories
    clean_caches

    echo ""
    echo "✅ Setup complete!"
    echo ""
    echo "👉 To run the application:"
    echo "1. Activate virtual environment: source venv/bin/activate"
    echo "2. Start the server: uvicorn app.main:app --host 0.0.0.0 --port 8000 --timeout-keep-alive 300"
}

# Execute main setup
main_setup

