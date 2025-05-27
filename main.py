#!/usr/bin/env python3
"""
FastAPI application for document classification using enhanced RAG classifier
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List, Tuple, Optional, Union
import logging
import traceback
import sys
import os
import time

# Add the project root to the Python path
sys.path.append('/home/azureuser/rag_project')

# Import our enhanced RAG classifier
from core.enhanced_rag_classifier import EnhancedRAGClassifier

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Enhanced RAG Document Classifier", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global classifier instance
classifier = None

class ClassificationRequest(BaseModel):
    text: str
    filename: str = "document.pdf"

class ClassificationResponse(BaseModel):
    document_type: str
    document_category: str
    confidence_level: str
    confidence_score: float = 0.0
    uncertainty_flags: List[str] = []
    needs_human_review: bool = False
    alternative_classifications: List[Dict[str, str]] = []
    processing_time: str
    rag_context_used: bool = False
    success: bool = True

@app.on_event("startup")
async def startup_event():
    """Initialize the classifier on startup."""
    global classifier
    try:
        logger.info("Initializing Enhanced RAG Classifier...")
        classifier = EnhancedRAGClassifier()
        logger.info("✅ Enhanced RAG Classifier initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize classifier: {e}")
        logger.error(traceback.format_exc())

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Enhanced RAG Document Classifier API", "status": "online"}

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "classifier_ready": classifier is not None,
        "service": "enhanced-rag-classifier"
    }

@app.post("/classify", response_model=ClassificationResponse)
async def classify_document(request: ClassificationRequest):
    """Classify a document using the enhanced RAG classifier."""
    if classifier is None:
        raise HTTPException(status_code=503, detail="Classifier not initialized")
    
    try:
        logger.info(f"Classifying document: {request.filename}")
        
        # Use the enhanced RAG classifier
        result = classifier.classify_with_rag(request.text, request.filename)
        
        # Convert the result to our response format
        confidence_score = float(result.get('confidence_score', 0.0))
        uncertainty_flags = result.get('uncertainty_flags', [])
        needs_review = result.get('needs_human_review', False)
        alternatives = result.get('alternative_classifications', [])
        
        response = ClassificationResponse(
            document_type=result.get('doc_type', 'Unknown'),
            document_category=result.get('doc_category', 'Unknown'),
            confidence_level=result.get('confidence', 'Low'),
            confidence_score=confidence_score,
            uncertainty_flags=uncertainty_flags,
            needs_human_review=needs_review,
            alternative_classifications=alternatives,
            processing_time=f"{result.get('processing_time', 0):.2f}s",
            rag_context_used=result.get('rag_context', {}).get('context_used', False),
            success=True
        )
        
        logger.info(f"Classification successful: {response.document_type} -> {response.document_category}")
        return response
        
    except Exception as e:
        logger.error(f"Classification error: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Classification failed: {str(e)}")

@app.post("/classify-batch")
async def classify_documents_batch(requests: List[ClassificationRequest]):
    """Classify multiple documents in batch."""
    if classifier is None:
        raise HTTPException(status_code=503, detail="Classifier not initialized")
    
    results = []
    for req in requests:
        try:
            result = classifier.classify_with_rag(req.text, req.filename)
            confidence_score = float(result.get('confidence_score', 0.0))
            uncertainty_flags = result.get('uncertainty_flags', [])
            needs_review = result.get('needs_human_review', False)
            
            results.append({
                "filename": req.filename,
                "document_type": result.get('doc_type', 'Unknown'),
                "document_category": result.get('doc_category', 'Unknown'),
                "confidence_level": result.get('confidence', 'Low'),
                "confidence_score": confidence_score,
                "uncertainty_flags": uncertainty_flags,
                "needs_human_review": needs_review,
                "success": True
            })
        except Exception as e:
            results.append({
                "filename": req.filename,
                "error": str(e),
                "success": False
            })
    
    return {"results": results, "total": len(requests)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)