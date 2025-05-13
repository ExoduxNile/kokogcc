# Use official Python image
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libsndfile1 \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies to system path
RUN pip install --no-cache-dir -r requirements.txt

# Create models directory and download models
RUN mkdir -p models && \
    wget -q https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin -O models/voices-v1.0.bin && \
    wget -q https://github.com/nazdridoy/kokoro-tts/releases/download/v1.0.0/kokoro-v1.0.onnx -O models/kokoro-v1.0.onnx

# Verify model downloads
RUN ls -lh models/ && \
    [ -s models/voices-v1.0.bin ] && \
    [ -s models/kokoro-v1.0.onnx ] || (echo "Model files failed to download" && exit 1)

# Copy the rest of the application
COPY . .

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Create uploads directory
RUN mkdir -p uploads

# Expose the port the app runs on
EXPOSE 8000

# Run FastAPI server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000" "--timeout-keep-alive", "300"]
