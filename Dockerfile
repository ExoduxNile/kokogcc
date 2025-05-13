FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libsndfile1 \
    wget \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Set Python path
ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1

# Copy requirements first
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Download models
RUN mkdir -p models && \
    wget -q "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin" -O "models/voices-v1.0.bin" && \
    wget -q "https://github.com/nazdridoy/kokoro-tts/releases/download/v1.0.0/kokoro-v1.0.onnx" -O "models/kokoro-v1.0.onnx"

# Copy application
COPY . .

# Create necessary directories
RUN mkdir -p uploads

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--timeout-keep-alive", "300"]
