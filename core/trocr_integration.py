#!/usr/bin/env python3
"""
TrOCR Integration Module
Implements transformer-based OCR as mentioned in PDF requirements for better accuracy.
"""

import torch
import os
from transformers import TrOCRProcessor as HFTrOCRProcessor, VisionEncoderDecoderModel
from PIL import Image
import fitz  # PyMuPDF
import io
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

class TrOCRProcessor:
    def __init__(self):
        # Force CPU usage to avoid GPU memory conflicts with Mistral model
        self.device = "cpu"
        self.processor = None
        self.model = None
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize TrOCR model and processor."""
        try:
            logger.info("Initializing TrOCR model...")
            self.processor = HFTrOCRProcessor.from_pretrained('microsoft/trocr-base-printed')
            self.model = VisionEncoderDecoderModel.from_pretrained('microsoft/trocr-base-printed')
            
            if self.device == "cuda":
                self.model = self.model.to(self.device)
                logger.info("TrOCR model loaded on GPU")
            else:
                logger.info("TrOCR model loaded on CPU")
                
        except Exception as e:
            logger.error(f"Failed to initialize TrOCR: {e}")
            self.processor = None
            self.model = None
    
    def is_available(self) -> bool:
        """Check if TrOCR is available for use."""
        return self.processor is not None and self.model is not None
    
    def extract_text_from_image(self, image: Image.Image) -> str:
        """Extract text from a PIL Image using TrOCR."""
        if not self.is_available():
            raise RuntimeError("TrOCR model not available")
        
        try:
            # Ensure image is in RGB format
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Process image
            pixel_values = self.processor(images=image, return_tensors="pt").pixel_values
            
            if self.device == "cuda":
                pixel_values = pixel_values.to(self.device)
            
            # Generate text
            with torch.no_grad():
                generated_ids = self.model.generate(pixel_values, max_length=512)
            
            # Decode text
            text = self.processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
            return text.strip()
            
        except Exception as e:
            logger.error(f"TrOCR text extraction failed: {e}")
            return ""
    
    def extract_text_from_pdf_pages(self, pdf_path: str) -> str:
        """Extract text from PDF pages using TrOCR."""
        if not self.is_available():
            raise RuntimeError("TrOCR model not available")
        
        try:
            doc = fitz.open(pdf_path)
            all_text = []
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                
                # Render page as image
                mat = fitz.Matrix(2.0, 2.0)  # 2x zoom for better OCR
                pix = page.get_pixmap(matrix=mat)
                img_data = pix.tobytes("png")
                
                # Convert to PIL Image
                image = Image.open(io.BytesIO(img_data))
                
                # Extract text using TrOCR
                page_text = self.extract_text_from_image(image)
                if page_text:
                    all_text.append(f"[Page {page_num + 1}]\n{page_text}")
                
                logger.info(f"Processed page {page_num + 1}/{len(doc)} with TrOCR")
            
            doc.close()
            return "\n\n".join(all_text)
            
        except Exception as e:
            logger.error(f"TrOCR PDF processing failed: {e}")
            return ""

class HybridOCRProcessor:
    """
    Hybrid OCR processor that combines Tesseract and TrOCR for optimal results.
    Falls back to Tesseract if TrOCR is not available.
    """
    
    def __init__(self):
        self.trocr = TrOCRProcessor()
        self.use_trocr = self.trocr.is_available()
        
        if self.use_trocr:
            logger.info("Hybrid OCR: TrOCR available, will use for primary OCR")
        else:
            logger.info("Hybrid OCR: TrOCR not available, falling back to Tesseract only")
    
    def extract_text_from_pdf(self, pdf_path: str, prefer_trocr: bool = True) -> str:
        """
        Extract text from PDF using hybrid approach.
        
        Args:
            pdf_path: Path to PDF file
            prefer_trocr: Whether to prefer TrOCR over Tesseract
        
        Returns:
            Extracted text
        """
        try:
            # First try extracting embedded text
            doc = fitz.open(pdf_path)
            embedded_text = ""
            for page in doc:
                embedded_text += page.get_text()
            doc.close()
            
            # If we have substantial embedded text, use it
            if len(embedded_text.strip()) > 100:
                logger.info("Using embedded PDF text (no OCR needed)")
                return embedded_text
            
            # Need OCR - choose method
            if self.use_trocr and prefer_trocr:
                logger.info("Using TrOCR for PDF processing")
                return self.trocr.extract_text_from_pdf_pages(pdf_path)
            else:
                logger.info("Using Tesseract for PDF processing")
                return self._tesseract_pdf_ocr(pdf_path)
                
        except Exception as e:
            logger.error(f"Hybrid OCR failed: {e}")
            return ""
    
    def _tesseract_pdf_ocr(self, pdf_path: str) -> str:
        """Fallback to Tesseract OCR."""
        try:
            import pytesseract
            doc = fitz.open(pdf_path)
            all_text = []
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                mat = fitz.Matrix(2.0, 2.0)
                pix = page.get_pixmap(matrix=mat)
                img_data = pix.tobytes("png")
                
                image = Image.open(io.BytesIO(img_data))
                page_text = pytesseract.image_to_string(image)
                
                if page_text.strip():
                    all_text.append(f"[Page {page_num + 1}]\n{page_text}")
            
            doc.close()
            return "\n\n".join(all_text)
            
        except Exception as e:
            logger.error(f"Tesseract OCR fallback failed: {e}")
            return ""

# Global instance for reuse
hybrid_ocr = HybridOCRProcessor()

def extract_text_with_enhanced_ocr(file_path: str, prefer_trocr: bool = True) -> str:
    """
    Enhanced OCR function that can be used as drop-in replacement.
    
    Args:
        file_path: Path to document file
        prefer_trocr: Whether to prefer TrOCR over Tesseract
    
    Returns:
        Extracted text
    """
    return hybrid_ocr.extract_text_from_pdf(file_path, prefer_trocr)

if __name__ == "__main__":
    # Test the TrOCR integration
    logging.basicConfig(level=logging.INFO)
    
    test_file = "/home/azureuser/rag_project/test_contract.pdf"
    if os.path.exists(test_file):
        print("Testing TrOCR integration...")
        text = extract_text_with_enhanced_ocr(test_file)
        print(f"Extracted {len(text)} characters")
        print("Sample text:", text[:200] + "..." if len(text) > 200 else text)
    else:
        print("Test file not found")
