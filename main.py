from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import StreamingResponse, HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exception_handlers import http_exception_handler
from starlette.exceptions import HTTPException as StarletteHTTPException
import os
import io
import soundfile as sf
from kokoro_onnx import Kokoro
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Kokoro TTS API")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://tropley.com",
        "https://www.tropley.com"
    ],
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"]
)

# Model paths (matches setup.sh)
MODEL_BASE = os.getenv("MODEL_DIR", "/")  # Configurable via env
model_path = os.path.join(MODEL_BASE, "models/model.onnx")
voices_path = os.path.join(MODEL_BASE, "voices/voices-v1.0.bin")

# Verify files on startup
@app.on_event("startup")
async def verify_files():
    missing = []
    for path in [model_path, voices_path]:
        if not os.path.exists(path):
            missing.append(path)
            logger.error(f"Missing required file: {path}")

    if missing:
        raise RuntimeError(f"Missing required files: {', '.join(missing)}")

    logger.info("All model files verified successfully")

# Initialize model
try:
    kokoro = Kokoro(model_path, voices_path)
    logger.info("Model initialized successfully")
except Exception as e:
    logger.critical(f"Model initialization failed: {str(e)}")
    raise

# Health endpoints
@app.get("/health", include_in_schema=False)
async def health():
    """K8s-compatible health check"""
    return JSONResponse(content={"status": "healthy"})

@app.get("/ready", include_in_schema=False)
async def readiness():
    """Readiness check with model verification"""
    try:
        # Simple model operation to verify functionality
        kokoro.get_voices()
        return JSONResponse(content={"status": "ready"})
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service not ready: {str(e)}")

# Enhanced 503 handler
@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 503:
        return HTMLResponse(
            content="""
            <!DOCTYPE html>
            <html>
            <head><title>503 Service Unavailable</title></head>
            <body>
                <h1>503 - Service Unavailable</h1>
                <p>The server is under heavy load or maintenance. Try again later. 🚧</p>
                <p>Debug info: {}</p>
            </body>
            </html>
            """.format(exc.detail),
            status_code=503,
        )
    return await http_exception_handler(request, exc)

    # ... (existing implementation)

@app.on_event("startup")
async def startup():
    # Your existing initialization code
    app.state.ready = True