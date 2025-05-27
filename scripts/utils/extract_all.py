#!/usr/bin/env python
"""
Text extraction utilities for various document formats
"""
import os
import re
from pathlib import Path
from docx import Document
import fitz  # PyMuPDF
from PIL import Image
import pytesseract

def clean_text(raw: str) -> str:
    """Cleans up extracted text: removes hyphenation and excess newlines."""
    if not raw:
        return ""
    
    # Remove excessive whitespace
    cleaned = re.sub(r'\s+', ' ', raw)
    
    # Remove hyphenation at line breaks
    cleaned = re.sub(r'-\s+', '', cleaned)
    
    # Normalize line breaks
    cleaned = re.sub(r'\n+', '\n', cleaned)
    
    return cleaned.strip()

def extract_text_from_file(file_path: str) -> str:
    """Extracts and returns cleaned text from a DOCX, PDF, or image file."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    ext = Path(file_path).suffix.lower()
    raw_text = ""

    if ext == ".docx":
        doc = Document(file_path)
        raw_text = "\n".join(p.text for p in doc.paragraphs)

    elif ext == ".pdf":
        pdf = fitz.open(file_path)
        for page in pdf:
            pg_text = None
            # Try to extract text using dir() to avoid attribute errors
            for method in ("get_text", "getText"):
                if method in dir(page):
                    try:
                        pg_text = getattr(page, method)()
                        break
                    except Exception:
                        continue
            if pg_text and pg_text.strip():
                raw_text += pg_text
            else:
                # fallback to OCR if no text found
                pix = None
                for method in ("get_pixmap", "getPixmap"):
                    if method in dir(page):
                        try:
                            pix = getattr(page, method)(dpi=300)
                            break
                        except Exception:
                            continue
                if pix is not None:
                    img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
                    raw_text += pytesseract.image_to_string(img)
                else:
                    print("OCR failed for page: no pixmap method found")
            raw_text += "\n\n"
        pdf.close()

    elif ext in [".jpg", ".jpeg", ".png"]:
        img = Image.open(file_path).convert("RGB")
        raw_text = pytesseract.image_to_string(img)

    else:
        raise ValueError(f"Unsupported file type: {ext}")

    return clean_text(raw_text)

if __name__ == "__main__":
    # Test extraction
    test_file = "/home/azureuser/rag_project/test_batch_downloads/example.pdf"
    if os.path.exists(test_file):
        text = extract_text_from_file(test_file)
        print(f"Extracted {len(text)} characters")
        print(text[:200] + "..." if len(text) > 200 else text)
