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
STARTUP_TIME = 30  # seconds
app.state.startup_time = time.time()
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

@app.get("/health")
async def health():
    """Lightweight health check"""
    # Fail if startup takes too long
    if time.time() - app.state.startup_time > STARTUP_TIME:
        raise HTTPException(status_code=503, detail="Startup timeout")
    return {"status": "warming_up"}

@app.on_event("startup")
async def startup():
    # Skip full verification in probes
    if os.getenv("SKIP_STARTUP_CHECKS", "false").lower() != "true":
        verify_files()  # Your existing verification
        initialize_model()
    app.state.ready = True