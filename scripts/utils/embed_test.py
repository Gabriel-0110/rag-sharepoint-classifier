#!/usr/bin/env python3
"""
Document classification using Mistral-7B with embedding search
"""
import json
import requests
import numpy as np
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import logging

logger = logging.getLogger(__name__)

# Initialize components
embedding_model = SentenceTransformer('nlpaueb/legal-bert-base-uncased', device='cpu')
qdrant_client = QdrantClient(url="http://localhost:6333")

def get_similar_documents(text: str, limit: int = 10, min_score: float = 0.3) -> list:
    """
    Find similar documents using vector search, filter by min_score, and return sorted by score.
    """
    try:
        embedding = embedding_model.encode(text).tolist()
        search_result = qdrant_client.search(
            collection_name="documents",
            query_vector=embedding,
            limit=limit
        )
        # Filter and sort
        filtered = [r for r in search_result if getattr(r, 'score', 0) >= min_score]
        filtered.sort(key=lambda r: r.score, reverse=True)
        return filtered
    except Exception as e:
        logger.error(f"Similarity search failed: {e}")
        return []

def classify_with_llm(text: str, filename: str = "document.pdf") -> tuple:
    """
    Classify document using enhanced RAG classifier with Qdrant context
    
    Args:
        text: Document text content
        filename: Document filename
        
    Returns:
        tuple: (document_type, document_category)
    """
    try:
        # Retrieve top 3 relevant snippets for context
        similar = get_similar_documents(text, limit=10, min_score=0.3)
        context_snippets = []
        for r in similar[:3]:
            payload = getattr(r, 'payload', {})
            snippet = payload.get('text_snippet') or payload.get('text_excerpt') or ''
            if snippet:
                context_snippets.append(snippet)
        context = "\n---\n".join(context_snippets)
        prompt = f"Context documents:\n{context}\n\nInput document:\n{text}\n\nClassify the input document."
        # Use the enhanced RAG classifier API
        response = requests.post(
            "http://localhost:8000/classify",
            json={"text": prompt, "filename": filename},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return result['document_type'], result['document_category']
        else:
            logger.error(f"Classification API error: {response.status_code}")
            return "Misc. Reference Material", "Other Immigration Matters"
            
    except Exception as e:
        logger.error(f"Classification failed: {e}")
        return "Misc. Reference Material", "Other Immigration Matters"

if __name__ == "__main__":
    # Test classification
    test_text = "AFFIDAVIT - I declare under penalty of perjury that the following is true and correct"
    doc_type, doc_category = classify_with_llm(test_text, "test_affidavit.pdf")
    print(f"Classification: {doc_type} -> {doc_category}")
