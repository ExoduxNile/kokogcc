import os
import asyncio
import shutil
import zipfile
from typing import Optional
from pathlib import Path
from kokoro_onnx import Kokoro
from ..models.schemas import TTSParams

class TTSProcessor:
    def __init__(self):
        """Initialize TTS processor with Kokoro model"""
        self.model = Kokoro("models/kokoro-v1.0.onnx", "models/voices-v1.0.bin")
    
    async def process_text(self, params: TTSParams, output_path: str):
    """Process text input and save to audio file"""
    try:
        # Validate input
        if not params.text or len(params.text.strip()) == 0:
            raise ValueError("Text cannot be empty")
        
        max_chunk_size = 2000  # characters
        if len(params.text) > max_chunk_size:
            # Split and process in chunks
            chunks = [params.text[i:i+max_chunk_size] for i in range(0, len(params.text), max_chunk_size)]
            all_samples = []
            sample_rate = None
            
            for chunk in chunks:
                samples, sr = await self._process_chunk(chunk, params.voice, params.speed, params.lang)
                all_samples.extend(samples)
                sample_rate = sr
                
            sf.write(output_path, np.array(all_samples), sample_rate)
        else:
            # Process normally
            samples, sample_rate = await self._process_chunk(params.text, params.voice, params.speed, params.lang)
            sf.write(output_path, samples, sample_rate)
            
        return True
        
    except Exception as e:
        error_msg = f"Failed to process text: {str(e)}"
        print(error_msg)  # Log the error
        raise Exception(error_msg)

async def _process_chunk(self, text: str, voice: str, speed: float, lang: str):
    """Helper method to process a single chunk of text"""
    samples, sample_rate = await asyncio.to_thread(
        self.model.create,
        text,
        voice=voice,
        speed=speed,
        lang=lang
    )
    return samples, sample_rate
        
        return True
        
    except Exception as e:
        error_msg = f"Failed to process text: {str(e)}"
        print(error_msg)  # Log the error
        raise Exception(error_msg)
    
    async def process_file(self, params: TTSParams, output_path: str):
        """Process a file (TXT, EPUB, PDF) and save to audio file"""
        try:
            # Extract text from file based on type
            text = self._extract_text_from_file(params.input_file)
            
            # Process the text
            await self.process_text(
                TTSParams(
                    text=text,
                    voice=params.voice,
                    speed=params.speed,
                    lang=params.lang
                ),
                output_path
            )
            
        except Exception as e:
            raise Exception(f"Failed to process file: {str(e)}")
    
    async def process_file_with_chapters(self, params: TTSParams, output_zip_path: str):
        """Process a file with chapter splitting and create a zip archive"""
        try:
            # Create temporary directory for chapter files
            temp_dir = os.path.join(os.path.dirname(output_zip_path), f"temp_{os.path.basename(output_zip_path)}")
            os.makedirs(temp_dir, exist_ok=True)
            
            # Extract chapters from file
            chapters = self._extract_chapters_from_file(params.input_file)
            
            # Process each chapter
            for i, chapter in enumerate(chapters, 1):
                chapter_path = os.path.join(temp_dir, f"chapter_{i}.wav")
                await self.process_text(
                    TTSParams(
                        text=chapter['content'],
                        voice=params.voice,
                        speed=params.speed,
                        lang=params.lang
                    ),
                    chapter_path
                )
            
            # Create zip archive
            with zipfile.ZipFile(output_zip_path, 'w') as zipf:
                for root, _, files in os.walk(temp_dir):
                    for file in files:
                        zipf.write(
                            os.path.join(root, file),
                            arcname=file
                        )
            
            # Clean up temporary directory
            shutil.rmtree(temp_dir)
            
        except Exception as e:
            raise Exception(f"Failed to process file with chapters: {str(e)}")
    
    def _extract_text_from_file(self, file_path: str) -> str:
        """Extract text from supported file types"""
        if file_path.endswith('.txt'):
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        elif file_path.endswith('.epub'):
            return self._extract_text_from_epub(file_path)
        elif file_path.endswith('.pdf'):
            return self._extract_text_from_pdf(file_path)
        else:
            raise ValueError("Unsupported file type")
    
    def _extract_text_from_epub(self, epub_path: str) -> str:
        """Extract text from EPUB file"""
        from ebooklib import epub
        from bs4 import BeautifulSoup
        
        book = epub.read_epub(epub_path)
        full_text = ""
        for item in book.get_items():
            if item.get_type() == epub.ITEM_DOCUMENT:
                soup = BeautifulSoup(item.get_body_content(), "html.parser")
                full_text += soup.get_text()
        return full_text
    
    def _extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF file"""
        import fitz  # PyMuPDF
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text
    
    def _extract_chapters_from_file(self, file_path: str) -> list:
        """Extract chapters from supported file types"""
        if file_path.endswith('.epub'):
            return self._extract_chapters_from_epub(file_path)
        elif file_path.endswith('.pdf'):
            return self._extract_chapters_from_pdf(file_path)
        else:
            # For non-chapter files, treat entire content as one chapter
            text = self._extract_text_from_file(file_path)
            return [{'title': 'Chapter 1', 'content': text}]
    
    def _extract_chapters_from_epub(self, epub_path: str) -> list:
        """Extract chapters from EPUB file"""
        from ebooklib import epub
        from bs4 import BeautifulSoup
        
        book = epub.read_epub(epub_path)
        chapters = []
        
        # Simple implementation - can be enhanced with TOC parsing
        for item in book.get_items():
            if item.get_type() == epub.ITEM_DOCUMENT:
                soup = BeautifulSoup(item.get_body_content(), "html.parser")
                # Look for chapter headings
                for heading in soup.find_all(['h1', 'h2']):
                    if 'chapter' in heading.get_text().lower():
                        content = []
                        for sibling in heading.find_next_siblings():
                            if sibling.name in ['h1', 'h2']:
                                break
                            content.append(sibling.get_text())
                        chapters.append({
                            'title': heading.get_text(),
                            'content': '\n'.join(content)
                        })
        
        # If no chapters found, treat entire content as one chapter
        if not chapters:
            text = self._extract_text_from_epub(epub_path)
            chapters.append({'title': 'Chapter 1', 'content': text})
        
        return chapters
    
    def _extract_chapters_from_pdf(self, pdf_path: str) -> list:
        """Extract chapters from PDF file"""
        import fitz  # PyMuPDF
        
        doc = fitz.open(pdf_path)
        chapters = []
        current_chapter = None
        current_content = []
        
        # Simple implementation - can be enhanced with TOC parsing
        for page in doc:
            text = page.get_text()
            # Look for chapter headings (simple pattern)
            if 'chapter' in text.lower():
                if current_chapter:
                    chapters.append({
                        'title': current_chapter,
                        'content': '\n'.join(current_content)
                    })
                current_chapter = text.strip()
                current_content = []
            else:
                current_content.append(text)
        
        # Add the last chapter
        if current_chapter:
            chapters.append({
                'title': current_chapter,
                'content': '\n'.join(current_content)
            })
        
        # If no chapters found, treat entire content as one chapter
        if not chapters:
            text = self._extract_text_from_pdf(pdf_path)
            chapters.append({'title': 'Chapter 1', 'content': text})
        
        doc.close()
        return chapters
