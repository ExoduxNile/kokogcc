from pydantic import BaseModel
from typing import Optional

class TTSParams(BaseModel):
    """Parameters for TTS processing"""
    text: Optional[str] = None
    input_file: Optional[str] = None
    voice: str = "af_sarah"
    speed: float = 1.0
    lang: str = "en-us"
    format: str = "mp3"
    split_chapters: bool = False
