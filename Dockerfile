# Use official Python 3.11 image
FROM python:3.11-slim-bookworm

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    espeak-ng \
    curl && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# First copy only requirements to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt python-multipart

# Download model files (with checksum verification)
RUN mkdir -p models/v1_0 voices/v1_0 && \
    curl -L -o model.onnx \
    "https://huggingface.co/onnx-community/Kokoro-82M-v1.0-ONNX/resolve/main/onnx/model.onnx" && \
    curl -L -o voices-v1.0.bin \
    "https://github.com/nazdridoy/kokoro-tts/releases/download/v1.0.0/voices-v1.0.bin" && \
    [ -f model.onnx ] || { echo "Model download failed"; exit 1; } && \
    [ -f voices-v1.0.bin ] || { echo "Voices download failed"; exit 1; }

# Copy the rest of the application
COPY . .

# Verify critical files exist
RUN [ -f main.py ] || { echo "main.py missing"; exit 1; } && \
    [ -f model.onnx ] || { echo "model.onnx missing"; exit 1; } && \
    [ -f voices-v1.0.bin ] || { echo "voices-v1.0.bin missing"; exit 1; }

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:$PORT/ || exit 1

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
