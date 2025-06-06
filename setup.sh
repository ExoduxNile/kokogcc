#!/bin/bash

# Unified setup script for Kokoro TTS (works with and without Docker)

# Configuration variables
PYTHON_VERSION="3.12"
APP_DIR="/app"
MODEL_URLS=(
    "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin"
    "https://github.com/nazdridoy/kokoro-tts/releases/download/v1.0.0/kokoro-v1.0.onnx"
)

# Function to verify downloads
verify_download() {
    local file_path=$1
    if [ ! -f "$file_path" ]; then
        echo "Error: Failed to download $file_path"
        return 1
    fi
    
    # Check if file has content (not empty)
    if [ ! -s "$file_path" ]; then
        echo "Error: Downloaded file $file_path is empty"
        rm -f "$file_path"
        return 1
    fi
    return 0
}

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

# Function to setup Python environment
setup_python_env() {
    echo "Setting up Python environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install --no-cache-dir -r requirements.txt
}

# Function to download models with retries
download_models() {
    echo "Downloading models..."
    mkdir -p models
    
    for url in "${MODEL_URLS[@]}"; do
        filename=$(basename "$url")
        dest_path="models/$filename"
        
        if [ -f "$dest_path" ]; then
            echo "Model $filename already exists, verifying..."
            if verify_download "$dest_path"; then
                echo "Existing model $filename is valid, skipping download"
                continue
            fi
        fi
        
        echo "Downloading $filename..."
        max_retries=3
        retry_count=0
        success=0
        
        while [ $retry_count -lt $max_retries ]; do
            if wget --no-verbose --show-progress "$url" -O "$dest_path"; then
                if verify_download "$dest_path"; then
                    success=1
                    break
                fi
            fi
            retry_count=$((retry_count+1))
            echo "Download failed, retrying ($retry_count/$max_retries)..."
            sleep 2
        done
        
        if [ $success -eq 0 ]; then
            echo "Error: Failed to download $filename after $max_retries attempts"
            echo "You can manually download it using:"
            echo "wget '$url' -O '$dest_path'"
            exit 1
        fi
    done
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

    echo "Setup complete!"
    echo ""
    echo "To run the application:"
    echo "1. Activate virtual environment: source venv/bin/activate"
    echo "2. Start server: uvicorn app.main:app --host 0.0.0.0 --port 8000 --timeout-keep-alive 300"
}

# Execute main setup
main_setup
