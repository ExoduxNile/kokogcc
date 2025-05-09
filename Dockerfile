# Stage 1: Build dependencies and download model/voice files
FROM python:3.12-alpine AS builder

WORKDIR /app

# Install system dependencies including build tools
RUN apk add --no-cache --virtual .build-deps \
    curl \
    build-base \
    libc-dev \
    linux-headers \
    musl-dev \
    gcc \
    g++ \
    python3-dev \
    && apk add --no-cache libsndfile-dev

# Download model and voice files
RUN curl -L -o kokoro-v1.0.onnx https://github.com/nazdridoy/kokoro-tts/releases/download/v1.0.0/kokoro-v1.0.onnx && \
    curl -L -o voices-v1.0.bin https://github.com/nazdridoy/kokoro-tts/releases/download/v1.0.0/voices-v1.0.bin

# Create and activate virtual environment
RUN python3 -m venv .venv
ENV PATH="/app/.venv/bin:$PATH"

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir numpy==2.2.5 && \
    pip install --no-cache-dir kokoro-onnx==0.3.9 soundfile fastapi uvicorn kokoro>=0.9.4

# Stage 2: Final image
FROM python:3.12-alpine

WORKDIR /app

# Copy virtual environment and model files from builder
COPY --from=builder /app/.venv .venv
COPY --from=builder /app/kokoro-v1.0.onnx .
COPY --from=builder /app/voices-v1.0.bin .

# Copy application files
COPY main.py .
COPY Procfile .
COPY runtime.txt .

# Install runtime dependencies
RUN apk add --no-cache libsndfile

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH"
EXPOSE=8080

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]