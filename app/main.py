import os
from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from pathlib import Path
from typing import Optional
import uuid
import asyncio
import shutil

from .tts.processor import TTSProcessor
from .models.schemas import TTSParams

app = FastAPI(title="Kokoro TTS Web Service")

# Setup static files and templates
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# Create upload directory if it doesn't exist
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Render the homepage with TTS form"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/process-text/")
async def process_text(
    request: Request,
    text: str = Form(...),
    voice: str = Form("af_sarah"),
    speed: float = Form(1.0),
    lang: str = Form("en-us")
):
    """Process text input through TTS"""
    try:
        processor = TTSProcessor()
        params = TTSParams(
            text=text,
            voice=voice,
            speed=speed,
            lang=lang
        )
        
        # Generate unique filename
        output_filename = f"output_{uuid.uuid4().hex}.wav"
        output_path = os.path.join(UPLOAD_DIR, output_filename)
        
        # Process the text
        await processor.process_text(params, output_path)
        
        return JSONResponse({
            "status": "success",
            "message": "Text processed successfully",
            "audio_url": f"/download/{output_filename}"
        })
    except Exception as e:
        return JSONResponse(
            {"status": "error", "message": str(e)},
            status_code=500
        )

@app.post("/process-file/")
async def process_file(
    request: Request,
    file: UploadFile = File(...),
    voice: str = Form("af_sarah"),
    speed: float = Form(1.0),
    lang: str = Form("en-us"),
    split_chapters: bool = Form(False)
):
    """Process uploaded file through TTS"""
    try:
        # Save uploaded file
        file_ext = os.path.splitext(file.filename)[1].lower()
        input_filename = f"input_{uuid.uuid4().hex}{file_ext}"
        input_path = os.path.join(UPLOAD_DIR, input_filename)
        
        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        processor = TTSProcessor()
        params = TTSParams(
            input_file=input_path,
            voice=voice,
            speed=speed,
            lang=lang,
            split_chapters=split_chapters
        )
        
        if split_chapters:
            # For chapter splitting, we'll create a zip file
            output_filename = f"output_{uuid.uuid4().hex}.zip"
            output_path = os.path.join(UPLOAD_DIR, output_filename)
            await processor.process_file_with_chapters(params, output_path)
        else:
            # Single audio file output
            output_filename = f"output_{uuid.uuid4().hex}.wav"
            output_path = os.path.join(UPLOAD_DIR, output_filename)
            await processor.process_file(params, output_path)
        
        # Clean up input file
        os.remove(input_path)
        
        return JSONResponse({
            "status": "success",
            "message": "File processed successfully",
            "download_url": f"/download/{output_filename}"
        })
    except Exception as e:
        return JSONResponse(
            {"status": "error", "message": str(e)},
            status_code=500
        )

@app.get("/download/{filename}")
async def download_file(filename: str):
    """Serve processed audio files for download"""
    file_path = os.path.join(UPLOAD_DIR, filename)
    if os.path.exists(file_path):
        return FileResponse(
            file_path,
            media_type="application/octet-stream",
            filename=filename
        )
    return JSONResponse(
        {"status": "error", "message": "File not found"},
        status_code=404
    )

@app.on_event("startup")
async def startup_event():
    """Initialize resources when app starts"""
    # Create necessary directories
    os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources when app stops"""
    # Optionally clean up old files
    pass
