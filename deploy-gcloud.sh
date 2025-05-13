#!/bin/bash
set -e

PROJECT_ID="ttss-456320"
SERVICE_NAME="kokoro-tts"
REGION="us-central1"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

# Build and push image
docker build -t $IMAGE_NAME .
docker push $IMAGE_NAME

# Deploy to Cloud Run (no auth)
gcloud run deploy $SERVICE_NAME \
  --image $IMAGE_NAME \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --cpu 2 \
  --memory 8Gi \
  --port 8000 \
  --timeout 900

# Get service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
  --platform managed \
  --region $REGION \
  --format 'value(status.url)')
echo "Service deployed: $SERVICE_URL"
