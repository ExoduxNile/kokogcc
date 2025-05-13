#!/bin/bash
set -e

# Configuration
PROJECT_ID="ttss-456320"
SERVICE_NAME="kokoro-tts"
REGION="us-central1"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

# Authenticate with gcloud
gcloud auth login
gcloud config set project $PROJECT_ID

# Build the Docker image
echo "Building Docker image..."
docker build -t $IMAGE_NAME .

# Push to Google Container Registry
echo "Pushing image to GCR..."
docker push $IMAGE_NAME

# Deploy to Cloud Run
echo "Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
  --image $IMAGE_NAME \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --cpu 2 \
  --memory 8Gi \
  --port 8000 \
  --set-env-vars="PYTHONUNBUFFERED=1" \
  --timeout 900

# Get the service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --platform managed --region $REGION --format 'value(status.url)')
echo "Service deployed successfully: $SERVICE_URL"
