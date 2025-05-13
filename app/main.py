import os
import uuid
import asyncio
import shutil
import traceback
from pathlib import Path
from typing import Optional, Union
from fastapi import FastAPI, Request, Form, UploadFile, File, HTTPException, Body
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import soundfile as sf
import io
from pydantic import BaseModel

from .tts.processor import TTSProcessor

app = FastAPI(title="Kokoro TTS Web Service")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup directories
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Supported formats and their MIME types
SUPPORTED_FORMATS = {
    'wav': 'audio/wav',
    'mp3': 'audio/mpeg',
    'flac': 'audio/flac',
    'ogg': 'audio/ogg',
    'aac': 'audio/aac'
}

class TTSParams(BaseModel):
    text: str
    voice: str = "af_sarah"
    speed: float = 1.0
    lang: str = "en-us"
    format: str = "mp3"

@app.post("/process-text/")
async def process_text(
    request: Request,
    text: Optional[str] = Form(None),
    voice: Optional[str] = Form("af_sarah"),
    speed: Optional[float] = Form(1.0),
    lang: Optional[str] = Form("en-us"),
    format: Optional[str] = Form("mp3"),
    json_data: Optional[TTSParams] = Body(None)
):
    """Handle both form data and JSON requests for TTS"""
    try:
        # Determine input source (form or JSON)
        if json_data:
            params = json_data
        else:
            if not text:
                raise HTTPException(status_code=400, detail="Text cannot be empty")
            params = TTSParams(
                text=text,
                voice=voice,
                speed=speed,
                lang=lang,
                format=format.lower()
            )
        
        # Validate format
        if params.format not in SUPPORTED_FORMATS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported format. Supported: {', '.join(SUPPORTED_FORMATS.keys())}"
            )

        processor = TTSProcessor()
        
        # Generate unique filename
        output_filename = f"output_{uuid.uuid4().hex}.{params.format}"
        output_path = os.path.join(UPLOAD_DIR, output_filename)
        
        # Process the text (WAV format internally)
        await processor.process_text(params, output_path.replace(f".{params.format}", ".wav"))
        
        # Convert to requested format if needed
        if params.format != "wav":
            output_path = await convert_audio_format(
                output_path.replace(f".{params.format}", ".wav"),
                output_path,
                params.format
            )
        
        # For API clients, return JSON with URL
        if "application/json" in request.headers.get("accept", ""):
            return JSONResponse({
                "status": "success",
                "audio_url": f"/download/{output_filename}",
                "download_url": f"/download/{output_filename}"
            })
        
        # For form submissions, return the file directly
        return FileResponse(
            output_path,
            media_type=SUPPORTED_FORMATS[params.format],
            filename=output_filename
        )
        
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

async def convert_audio_format(
    input_path: str,
    output_path: str,
    target_format: str
) -> str:
    """Convert audio file to different format using soundfile"""
    try:
        data, samplerate = sf.read(input_path)
        
        # Special handling for MP3 requires additional library
        if target_format == "mp3":
            import pydub
            from pydub import AudioSegment
            
            # Convert via WAV -> MP3
            sound = AudioSegment.from_wav(input_path)
            sound.export(output_path, format="mp3", bitrate="192k")
        else:
            sf.write(output_path, data, samplerate, format=target_format)
        
        # Remove temporary WAV file
        os.remove(input_path)
        
        return output_path
    except Exception as e:
        # Fallback to WAV if conversion fails
        if os.path.exists(input_path):
            shutil.move(input_path, output_path.replace(f".{target_format}", ".wav"))
            return output_path.replace(f".{target_format}", ".wav")
        raise HTTPException(
            status_code=500,
            detail=f"Audio conversion failed: {str(e)}"
        )

@app.post("/process-file/")
async def process_file(
    file: UploadFile = File(...),
    voice: str = Form("af_sarah"),
    speed: float = Form(1.0),
    lang: str = Form("en-us"),
    format: str = Form("mp3"),
    split_chapters: bool = Form(False)
):
    """Process uploaded files with format support"""
    input_path = None
    try:
        # Validate format
        if format.lower() not in SUPPORTED_FORMATS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported format. Supported: {', '.join(SUPPORTED_FORMATS.keys())}"
            )

        # Save uploaded file
        file_ext = os.path.splitext(file.filename)[1].lower()
        input_filename = f"input_{uuid.uuid4().hex}{file_ext}"
        input_path = os.path.join(UPLOAD_DIR, input_filename)
        
        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        processor = TTSProcessor()
        params = TTSParams(
            text="",  # Will be read from file
            voice=voice,
            speed=speed,
            lang=lang,
            format=format
        )
        
        if split_chapters:
            output_filename = f"output_{uuid.uuid4().hex}.zip"
            output_path = os.path.join(UPLOAD_DIR, output_filename)
            await processor.process_file_with_chapters(params, output_path)
        else:
            output_filename = f"output_{uuid.uuid4().hex}.{format}"
            output_path = os.path.join(UPLOAD_DIR, output_filename)
            
            # Process to WAV first
            wav_path = output_path.replace(f".{format}", ".wav")
            await processor.process_file(params, wav_path)
            
            # Convert to target format
            if format != "wav":
                output_path = await convert_audio_format(wav_path, output_path, format)
        
        return JSONResponse({
            "status": "success",
            "message": "File processed successfully",
            "download_url": f"/download/{output_filename}"
        })
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
    finally:
        if input_path and os.path.exists(input_path):
            os.remove(input_path)

@app.get("/download/{filename}")
async def download_file(filename: str):
    """Serve processed audio files"""
    file_path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    file_ext = os.path.splitext(filename)[1].lower()[1:]
    media_type = SUPPORTED_FORMATS.get(file_ext, "application/octet-stream")
    
    return FileResponse(
        file_path,
        media_type=media_type,
        filename=filename
    )

@app.get("/supported-formats")
async def get_supported_formats():
    """Return list of supported audio formats"""
    return {
        "supported_formats": list(SUPPORTED_FORMATS.keys()),
        "default_format": "mp3"
    }

@app.on_event("startup")
async def startup_event():
    """Initialize resources"""
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    
    # Verify audio conversion dependencies
    try:
        import pydub
        import ffmpeg
    except ImportError:
        print("Warning: pydub/ffmpeg not installed. MP3 conversion will be limited.")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources"""
    pass
