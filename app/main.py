import os
import uuid
import asyncio
import shutil
import traceback
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, Request, Form, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware  # Add this import

from .tts.processor import TTSProcessor
from .models.schemas import TTSParams

app = FastAPI(title="Kokoro TTS Web Service")

# Add CORS middleware (place this right after creating the FastAPI app)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://tropley.com",  # Your Vercel domain
        "https://www.tropley.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup static files and templates
static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

# Create upload directory if it doesn't exist
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'.txt', '.pdf', '.epub'}

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Render the homepage with TTS form"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/process-text/")
async def process_text(
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
    except ValueError as e:
        return JSONResponse(
            {"status": "error", "message": str(e)},
            status_code=400
        )
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(
            {"status": "error", "message": str(e)},
            status_code=500
        )

@app.post("/process-file/")
async def process_file(
    file: UploadFile = File(...),
    voice: str = Form("af_sarah"),
    speed: float = Form(1.0),
    lang: str = Form("en-us"),
    split_chapters: bool = Form(False)
):
    """Process uploaded file through TTS"""
    input_path = None
    try:
        # Validate file extension
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            raise ValueError(f"Unsupported file type. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}")

        # Save uploaded file
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
            output_filename = f"output_{uuid.uuid4().hex}.zip"
            output_path = os.path.join(UPLOAD_DIR, output_filename)
            await processor.process_file_with_chapters(params, output_path)
        else:
            output_filename = f"output_{uuid.uuid4().hex}.wav"
            output_path = os.path.join(UPLOAD_DIR, output_filename)
            await processor.process_file(params, output_path)
        
        return JSONResponse({
            "status": "success",
            "message": "File processed successfully",
            "download_url": f"/download/{output_filename}"
        })
    except ValueError as e:
        return JSONResponse(
            {"status": "error", "message": str(e)},
            status_code=400
        )
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(
            {"status": "error", "message": str(e)},
            status_code=500
        )
    finally:
        # Clean up input file if it exists
        if input_path and os.path.exists(input_path):
            os.remove(input_path)

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
    os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources when app stops"""
    pass
