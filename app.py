from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
import sys
import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro
import io
import logging
from threading import Lock

app = FastAPI(title="Kokoro TTS Service")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Kokoro model with thread safety
kokoro_lock = Lock()
kokoro = None
try:
    kokoro = Kokoro("kokoro-v1.0.onnx", "voices-v1.0.bin")
except Exception as e:
    logger.error(f"Failed to initialize Kokoro model: {e}")
    sys.exit(1)

# Pydantic model for request validation
class TTSRequest(BaseModel):
    text: str
    voice: str = "af_sarah"
    speed: float = 1.0
    lang: str = "en-us"
    format: str = "wav"

# Health check endpoint for Cloud Run
@app.get("/health")
async def health_check():
    """Health check endpoint for Cloud Run liveness and readiness probes."""
    if kokoro is None:
        logger.error("Kokoro model not initialized")
        return JSONResponse(status_code=503, content={"status": "unhealthy", "error": "Kokoro model not initialized"})
    try:
        # Lightweight check: verify model is loaded by accessing a simple attribute
        kokoro.get_languages()
        return JSONResponse(status_code=200, content={"status": "healthy"})
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(status_code=503, content={"status": "unhealthy", "error": str(e)})

def validate_language(lang, kokoro):
    """Validate if the language is supported."""
    try:
        supported_languages = set(kokoro.get_languages())
        if lang not in supported_languages:
            return False, f"Unsupported language: {lang}. Supported: {', '.join(sorted(supported_languages))}"
        return True, lang
    except Exception as e:
        return False, f"Error validating language: {str(e)}"

def validate_voice(voice, kokoro):
    """Validate single voice or voice blend."""
    try:
        supported_voices = set(kokoro.get_voices())
        
        if ',' in voice:
            voices = []
            weights = []
            for pair in voice.split(','):
                if ':' in pair:
                    v, w = pair.strip().split(':')
                    voices.append(v.strip())
                    weights.append(float(w.strip()))
                else:
                    voices.append(pair.strip())
                    weights.append(50.0)
            
            if len(voices) != 2:
                return False, "Voice blending requires exactly two voices"
            
            for v in voices:
                if v not in supported_voices:
                    return False, f"Unsupported voice: {v}. Supported: {', '.join(sorted(supported_voices))}"
            
            total = sum(weights)
            if total != 100:
                weights = [w * (100/total) for w in weights]
            
            style1 = kokoro.get_voice_style(voices[0])
            style2 = kokoro.get_voice_style(voices[1])
            blend = np.add(style1 * (weights[0]/100), style2 * (weights[1]/100))
            return True, blend
        else:
            if voice not in supported_voices:
                return False, f"Unsupported voice: {voice}. Supported: {', '.join(sorted(supported_voices))}"
            return True, voice
    except Exception as e:
        return False, f"Error validating voice: {str(e)}"

def process_chunk_sequential(chunk, kokoro, voice, speed, lang, retry_count=0):
    """Process a single chunk of text with retry logic."""
    try:
        samples, sample_rate = kokoro.create(chunk, voice=voice, speed=speed, lang=lang)
        return samples, sample_rate
    except Exception as e:
        if "index 510 is out of bounds" in str(e) and retry_count < 3:
            new_size = int(len(chunk) * 0.6)
            words = chunk.split()
            current_piece = []
            current_size = 0
            pieces = []
            
            for word in words:
                word_size = len(word) + 1
                if current_size + word_size > new_size:
                    if current_piece:
                        pieces.append(' '.join(current_piece).strip())
                    current_piece = [word]
                    current_size = word_size
                else:
                    current_piece.append(word)
                    current_size += word_size
            
            if current_piece:
                pieces.append(' '.join(current_piece).strip())
            
            all_samples = []
            last_sample_rate = None
            
            for piece in pieces:
                samples, sr = process_chunk_sequential(piece, kokoro, voice, speed, lang, retry_count + 1)
                if samples is not None:
                    all_samples.extend(samples)
                    last_sample_rate = sr
            
            if all_samples:
                return all_samples, last_sample_rate
            
        return None, None

def chunk_text(text, chunk_size=1000):
    """Split text into chunks at sentence boundaries."""
    sentences = text.replace('\n', ' ').split('.')
    chunks = []
    current_chunk = []
    current_size = 0
    
    for sentence in sentences:
        if not sentence.strip():
            continue
        sentence = sentence.strip() + '.'
        sentence_size = len(sentence)
        
        if sentence_size > chunk_size:
            words = sentence.split()
            current_piece = []
            current_piece_size = 0
            
            for word in words:
                word_size = len(word) + 1
                if current_piece_size + word_size > chunk_size:
                    if current_piece:
                        chunks.append(' '.join(current_piece).strip() + '.')
                    current_piece = [word]
                    current_piece_size = word_size
                else:
                    current_piece.append(word)
                    current_piece_size += word_size
            
            if current_piece:
                chunks.append(' '.join(current_piece).strip() + '.')
            continue
        
        if current_size + sentence_size > chunk_size and current_chunk:
            chunks.append(' '.join(current_chunk))
            current_chunk = []
            current_size = 0
        
        current_chunk.append(sentence)
        current_size += sentence_size
    
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    
    return chunks

@app.get("/")
async def serve_homepage():
    return FileResponse("static/index.html")

@app.post("/api/tts")
async def text_to_speech(request: TTSRequest):
    try:
        text = request.text
        voice = request.voice
        speed = request.speed
        lang = request.lang
        format = request.format.lower()

        if format not in ['wav', 'mp3']:
            raise HTTPException(status_code=400, detail="Invalid format. Use 'wav' or 'mp3'")

        # Validate parameters
        with kokoro_lock:
            is_valid, lang_result = validate_language(lang, kokoro)
            if not is_valid:
                raise HTTPException(status_code=400, detail=lang_result)
            
            is_valid, voice_result = validate_voice(voice, kokoro)
            if not is_valid:
                raise HTTPException(status_code=400, detail=voice_result)

            # Process text
            chunks = chunk_text(text)
            all_samples = []
            sample_rate = None

            for chunk in chunks:
                samples, sr = process_chunk_sequential(chunk, kokoro, voice_result, speed, lang)
                if samples is None:
                    raise HTTPException(status_code=500, detail="Error processing text chunk")
                all_samples.extend(samples)
                sample_rate = sr

            # Convert to audio file
            output = io.BytesIO()
            sf.write(output, np.array(all_samples), sample_rate, format=format)
            output.seek(0)

            # Return streaming response
            return StreamingResponse(
                content=output,
                media_type=f'audio/{format}',
                headers={
                    "Content-Disposition": f'attachment; filename=output.{format}'
                }
            )

    except Exception as e:
        logger.error(f"Error in TTS processing: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    os.makedirs('static', exist_ok=True)
    os.makedirs('templates', exist_ok=True)
    port = int(os.getenv("PORT", 8080))  # Default to 8080 for Cloud Run
    uvicorn.run(app, host="0.0.0.0", port=port)
