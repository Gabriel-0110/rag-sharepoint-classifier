#!/usr/bin/env python
import os
import re
from pathlib import Path
from docx import Document
import fitz  # PyMuPDF
from PIL import Image
import pytesseract

def clean_text(raw: str) -> str:
    """Cleans up extracted text: removes hyphenation and excess newlines."""
    text = re.sub(r"(\w+)-\n(\w+)", r"\1\2", raw)  # fix word splits
    text = re.sub(r"\n{2,}", "\n\n", text)         # collapse newlines
    return text.strip()

def extract_text_from_file(file_path: str) -> str:
    """Extracts and returns cleaned text from a DOCX, PDF, or image file."""
    ext = Path(file_path).suffix.lower()
    raw_text = ""

    if ext == ".docx":
        doc = Document(file_path)
        raw_text = "\n".join(p.text for p in doc.paragraphs)

    elif ext == ".pdf":
        pdf = fitz.open(file_path)
        for page in pdf:
            pg_text = page.get_text()
            if pg_text.strip():
                raw_text += pg_text
            else:
                # fallback to OCR if no text found
                pix = page.get_pixmap(dpi=300)
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                raw_text += pytesseract.image_to_string(img)
            raw_text += "\n\n"

    elif ext in [".jpg", ".jpeg", ".png"]:
        img = Image.open(file_path).convert("RGB")
        raw_text = pytesseract.image_to_string(img)

    else:
        raise ValueError(f"Unsupported file type: {ext}")

    return clean_text(raw_text)
