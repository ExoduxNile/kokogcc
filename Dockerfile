FROM python:3.12-alpine AS builder

WORKDIR /app

RUN apk add --no-cache curl build-base

RUN curl -L -o kokoro-v1.0.onnx https://github.com/nazdridoy/kokoro-tts/releases/download/v1.0.0/kokoro-v1.0.onnx && curl -L -o voices-v1.0.bin https://github.com/nazdridoy/kokoro-tts/releases/download/v1.0.0/voices-v1.0.bin

COPY setup.sh .
COPY requirements.txt .

RUN chmod +x setup.sh

RUN ./setup.sh

FROM python:3.12-alpine

WORKDIR /app

COPY --from=builder /app/.venv .venv

COPY main.py .
COPY --from=builder /app/kokoro-v1.0.onnx .
COPY --from=builder /app/voices-v1.0.bin .
COPY Procfile .
COPY runtime.txt .

ENV PATH="/app/.venv/bin:$PATH" EXPOSE=8080

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
