FROM python:3.11-slim-bookworm

# 1. Install minimal system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    espeak-ng \
    curl && \
    rm -rf /var/lib/apt/lists/*

# 2. Pre-download models during build (not runtime)
RUN mkdir -p /models /voices && \
    curl -L -o /models/model.onnx \
    "https://github.com/nazdridoy/kokoro-tts/releases/download/v1.0.0/kokoro-v1.0.onnx" && \
    curl -L -o /voices/voices-v1.0.bin \
    "https://github.com/nazdridoy/kokoro-tts/releases/download/v1.0.0/voices-v1.0.bin"

WORKDIR /app
COPY . .

# 3. Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# 4. Optimized health checks
HEALTHCHECK --interval=15s --timeout=5s --start-period=30s \
    CMD curl -f http://localhost:$PORT/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
