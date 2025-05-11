from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import StreamingResponse, JSONResponse, HTMLResponse
from fastapi.exception_handlers import http_exception_handler
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
import os
import io
import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro
import warnings

# Suppress warnings
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://tropley.com", "https://www.tropley.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"]
)

# Exception handler for 503 with HTML output
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
            </body>
            </html>
            """,
            status_code=503,
        )
    return await http_exception_handler(request, exc)


# Fake 503 for testing
@app.get("/test-503", response_class=HTMLResponse)
async def trigger_503():
    raise HTTPException(status_code=503, detail="Service Unavailable")

# Load Kokoro model
MODEL_DIR = os.getenv("MODEL_DIR", ".")  # Allows override via environment variable
model_path = os.path.join(MODEL_DIR, "model.onnx")
voices_path = os.path.join(MODEL_DIR, "voices-v1.0.bin")
if not os.path.exists(model_path) or not os.path.exists(voices_path):
    raise HTTPException(status_code=500, detail=f"Missing model or voice files: {model_path}, {voices_path}")
kokoro = Kokoro(model_path, voices_path)

# Utilities
def chunk_text(text, chunk_size=3000):
    words = text.replace('\n', ' ').split()
    chunks = []
    current_chunk = []
    current_size = 0
    for word in words:
        word_size = len(word) + 1
        if current_size + word_size > chunk_size:
            chunks.append(' '.join(current_chunk))
            current_chunk = [word]
            current_size = word_size
        else:
            current_chunk.append(word)
            current_size += word_size
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    return [chunk for chunk in chunks if chunk.strip()]

def validate_language(lang):
    supported_languages = set(kokoro.get_languages())
    if lang not in supported_languages:
        raise HTTPException(status_code=400, detail=f"Unsupported language: {lang}. Supported: {', '.join(sorted(supported_languages))}")
    return lang

def validate_voice(voice):
    supported_voices = set(kokoro.get_voices())
    if voice not in supported_voices:
        raise HTTPException(status_code=400, detail=f"Unsupported voice: {voice}. Supported: {', '.join(sorted(supported_voices))}")
    return voice

# API endpoints
@app.get("/voices")
async def list_voices():
    return {"voices": list(kokoro.get_voices())}

@app.get("/languages")
async def list_languages():
    return {"languages": list(kokoro.get_languages())}

@app.post("/tts")
async def text_to_speech(
    text: str = Form(...),
    voice: str = Form("af_sarah"),
    speed: float = Form(1.0),
    lang: str = Form("en-us"),
    format: str = Form("wav")
):
    if format not in ["wav", "mp3"]:
        raise HTTPException(status_code=400, detail="Format must be 'wav' or 'mp3'")
    lang = validate_language(lang)
    voice = validate_voice(voice)
    chunks = chunk_text(text)
    all_samples = []
    sample_rate = None
    for chunk in chunks:
        try:
            samples, sr = kokoro.create(chunk, voice=voice, speed=speed, lang=lang)
            if samples is not None:
                if sample_rate is None:
                    sample_rate = sr
                all_samples.extend(samples)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error processing chunk: {str(e)}")
    if not all_samples:
        raise HTTPException(status_code=500, detail="No audio generated")
    buffer = io.BytesIO()
    sf.write(buffer, all_samples, sample_rate, format=format)
    buffer.seek(0)
    return StreamingResponse(buffer, media_type=f"audio/{format}", headers={"Content-Disposition": f"attachment; filename=output.{format}"})

