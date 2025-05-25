#!/usr/bin/env python3
"""
Enhanced RAG Classification with Category Definitions
Implements the advanced RAG features mentioned in the PDF document.
"""

import json
import numpy as np
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import requests
from typing import List, Dict, Tuple

class EnhancedRAGClassifier:
    def __init__(self):
        self.client = QdrantClient(url="http://localhost:6333")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.mistral_url = "http://localhost:8001/classify"
        
        # Category definitions as specified in PDF
        self.category_definitions = {
            "Corporate": "Legal documents related to corporate transactions, company records, business agreements, mergers and acquisitions",
            "Litigation": "Legal documents related to lawsuits, court filings, case law, legal disputes, pleadings",
            "Contract": "Legal agreements between parties, including terms, conditions, obligations, and rights",
            "Employment": "Documents related to employment law, workplace policies, hiring, termination, benefits",
            "Intellectual Property": "Patents, trademarks, copyrights, trade secrets, licensing agreements",
            "Real Estate": "Property transactions, leases, deeds, zoning, construction contracts",
            "Immigration": "Visa applications, citizenship documents, work permits, immigration law",
            "Criminal Justice": "Criminal law documents, police reports, court records, sentencing",
            "Family Law": "Divorce, custody, adoption, marriage, domestic relations",
            "Tax": "Tax returns, tax law documents, IRS communications, tax planning"
        }
        
        self.document_types = {
            "Contract": "A legally binding agreement between two or more parties",
            "Legal Memo": "Internal legal analysis and recommendations on specific issues",
            "Court Filing": "Documents submitted to court including pleadings, motions, briefs",
            "Correspondence": "Letters, emails, and other communications between parties",
            "Legal Opinion": "Formal legal analysis and conclusions on specific matters",
            "Regulatory Document": "Government regulations, compliance documents, permits",
            "Corporate Document": "Articles of incorporation, bylaws, board resolutions",
            "Financial Document": "Financial statements, tax documents, accounting records"
        }
        
        self._setup_category_collection()
    
    def _setup_category_collection(self):
        """Setup the category definitions collection in Qdrant as per PDF requirements."""
        try:
            # Create categories collection if it doesn't exist
            collections = self.client.get_collections().collections
            category_exists = any(c.name == "categories" for c in collections)
            
            if not category_exists:
                self.client.create_collection(
                    collection_name="categories",
                    vectors_config=VectorParams(size=384, distance=Distance.COSINE)
                )
                print("📁 Created categories collection")
            
            # Check if categories are already stored
            try:
                result = self.client.scroll("categories", limit=1)
                if len(result[0]) > 0:
                    print("📋 Category definitions already loaded")
                    return
            except:
                pass
            
            # Store category definitions as embeddings
            points = []
            point_id = 1
            
            # Store document type definitions
            for doc_type, definition in self.document_types.items():
                embedding = self.embedding_model.encode(definition)
                points.append(PointStruct(
                    id=point_id,
                    vector=embedding.tolist(),
                    payload={
                        "type": "document_type",
                        "name": doc_type,
                        "definition": definition
                    }
                ))
                point_id += 1
            
            # Store category definitions
            for category, definition in self.category_definitions.items():
                embedding = self.embedding_model.encode(definition)
                points.append(PointStruct(
                    id=point_id,
                    vector=embedding.tolist(),
                    payload={
                        "type": "category",
                        "name": category,
                        "definition": definition
                    }
                ))
                point_id += 1
            
            # Upload to Qdrant
            self.client.upsert("categories", points)
            print(f"✅ Stored {len(points)} category/type definitions in Qdrant")
            
        except Exception as e:
            print(f"❌ Error setting up categories: {e}")
    
    def get_rag_context(self, document_text: str, top_k: int = 3) -> Tuple[List[Dict], List[Dict]]:
        """
        Get RAG context using vector similarity as specified in PDF.
        Returns similar documents and relevant category definitions.
        """
        try:
            # Generate embedding for the document
            doc_embedding = self.embedding_model.encode(document_text)
            
            # Search for similar documents
            similar_docs = self.client.search(
                collection_name="documents",
                query_vector=doc_embedding.tolist(),
                limit=top_k,
                with_payload=True
            )
            
            # Search for relevant category definitions
            relevant_categories = self.client.search(
                collection_name="categories",
                query_vector=doc_embedding.tolist(),
                limit=top_k,
                with_payload=True
            )
            
            return similar_docs, relevant_categories
            
        except Exception as e:
            print(f"❌ Error getting RAG context: {e}")
            return [], []
    
    def classify_with_rag(self, document_text: str, filename: str) -> Dict:
        """
        Enhanced classification using RAG context as specified in PDF document.
        """
        try:
            # Get RAG context
            similar_docs, relevant_categories = self.get_rag_context(document_text)
            
            # Build enhanced prompt with RAG context
            prompt = self._build_rag_prompt(document_text, similar_docs, relevant_categories)
            
            # Call Mistral API with enhanced prompt
            response = requests.post(
                self.mistral_url,
                json={"text": prompt},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Add RAG context info to result
                result["rag_context"] = {
                    "similar_documents": len(similar_docs),
                    "relevant_categories": len(relevant_categories),
                    "context_used": True
                }
                
                return result
            else:
                # Fallback to basic classification
                return self._fallback_classification(document_text)
                
        except Exception as e:
            print(f"❌ Error in RAG classification: {e}")
            return self._fallback_classification(document_text)
    
    def _build_rag_prompt(self, document_text: str, similar_docs: List, relevant_categories: List) -> str:
        """Build enhanced prompt with RAG context as per PDF specifications."""
        
        prompt = """You are a legal document classification assistant with access to contextual information.

DOCUMENT TO CLASSIFY:
{document_text}

CONTEXTUAL INFORMATION:
""".format(document_text=document_text[:2000])  # Limit text to avoid token limits
        
        # Add similar documents context
        if similar_docs:
            prompt += "\nSIMILAR DOCUMENTS IN DATABASE:\n"
            for i, doc in enumerate(similar_docs[:2]):  # Limit to top 2
                if doc.payload and 'doc_type' in doc.payload:
                    prompt += f"- Document {i+1}: Type '{doc.payload.get('doc_type', 'Unknown')}', Category '{doc.payload.get('doc_category', 'Unknown')}'\n"
        
        # Add relevant category definitions
        if relevant_categories:
            prompt += "\nRELEVANT CATEGORY DEFINITIONS:\n"
            for cat in relevant_categories[:3]:  # Top 3 most relevant
                if cat.payload:
                    prompt += f"- {cat.payload['name']}: {cat.payload['definition']}\n"
        
        prompt += """
CLASSIFICATION TASK:
Based on the document content and the contextual information above, classify this document.

Available Document Types: Contract, Legal Memo, Court Filing, Correspondence, Legal Opinion, Regulatory Document, Corporate Document, Financial Document

Available Categories: Corporate, Litigation, Employment, Intellectual Property, Real Estate, Immigration, Criminal Justice, Family Law, Tax

Provide your answer in this exact format:
Document Type: [TYPE]
Document Category: [CATEGORY]
Confidence: [High/Medium/Low]
"""
        
        return prompt
    
    def _fallback_classification(self, document_text: str) -> Dict:
        """Fallback to basic classification if RAG fails."""
        try:
            response = requests.post(
                "http://localhost:8001/classify",
                json={"text": document_text[:2000]},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                result["rag_context"] = {
                    "similar_documents": 0,
                    "relevant_categories": 0,
                    "context_used": False
                }
                return result
            else:
                return {
                    "doc_type": "Unknown",
                    "doc_category": "Other",
                    "confidence": "Low",
                    "rag_context": {"context_used": False}
                }
                
        except Exception as e:
            print(f"❌ Fallback classification failed: {e}")
            return {
                "doc_type": "Unknown",
                "doc_category": "Other",
                "confidence": "Low",
                "error": str(e)
            }

def main():
    """Test the enhanced RAG classifier."""
    print("🚀 Testing Enhanced RAG Classification System")
    
    classifier = EnhancedRAGClassifier()
    
    # Test with sample text
    test_text = """
    SOFTWARE DEVELOPMENT AGREEMENT
    
    This agreement is entered into between Company A and Company B
    for the development of a web application. The contract includes
    payment terms, deliverables, timeline, and intellectual property rights.
    """
    
    result = classifier.classify_with_rag(test_text, "test_agreement.pdf")
    
    print(f"\n📋 Classification Result:")
    print(f"   Document Type: {result.get('doc_type', 'Unknown')}")
    print(f"   Category: {result.get('doc_category', 'Unknown')}")
    print(f"   Confidence: {result.get('confidence', 'Unknown')}")
    print(f"   RAG Context: {result.get('rag_context', {})}")

if __name__ == "__main__":
    main()
