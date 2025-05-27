#!/usr/bin/env python3
"""
Simple Document Processor for testing the enhanced classification system.
"""

import os
import PyPDF2
from typing import Optional

class DocumentProcessor:
    """Simple document processor for testing purposes."""
    
    def __init__(self):
        pass
    
    def extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF file."""
        try:
            text = ""
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text += page.extract_text() + "\n"
            
            return text.strip()
            
        except Exception as e:
            return f"Error extracting text from PDF: {str(e)}"
    
    def extract_text_from_file(self, file_path: str) -> str:
        """Extract text from various file types."""
        try:
            if not os.path.exists(file_path):
                return f"File not found: {file_path}"
            
            if file_path.lower().endswith('.pdf'):
                return self.extract_text_from_pdf(file_path)
            elif file_path.lower().endswith(('.txt', '.text')):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                return f"Unsupported file type: {file_path}"
                
        except Exception as e:
            return f"Error processing file {file_path}: {str(e)}"
