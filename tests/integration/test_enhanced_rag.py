#!/usr/bin/env python3
"""
Simple test for Enhanced RAG Classifier
"""

import sys
import traceback
import json

def test_enhanced_rag():
    """Test the enhanced RAG classifier step by step."""
    print("🧪 Testing Enhanced RAG Classifier Components")
    
    try:
        # Test imports
        print("1. Testing imports...")
        from qdrant_client import QdrantClient
        from sentence_transformers import SentenceTransformer
        import requests
        print("   ✅ All imports successful")
        
        # Test Qdrant connection
        print("2. Testing Qdrant connection...")
        client = QdrantClient(url="http://localhost:6333")
        collections = client.get_collections().collections
        print(f"   ✅ Connected to Qdrant, collections: {[c.name for c in collections]}")
        
        # Test embedding model
        print("3. Testing embedding model...")
        model = SentenceTransformer('all-MiniLM-L6-v2')
        test_embedding = model.encode("test document")
        print(f"   ✅ Embedding model working, vector size: {len(test_embedding)}")
        
        # Test Mistral API
        print("4. Testing Mistral API...")
        response = requests.get("http://localhost:8001/health", timeout=5)
        if response.status_code == 200:
            print("   ✅ Mistral API is responding")
        else:
            print(f"   ❌ Mistral API error: {response.status_code}")
        
        # Test Enhanced RAG Classifier initialization
        print("5. Testing Enhanced RAG Classifier...")
        from enhanced_rag_classifier import EnhancedRAGClassifier
        classifier = EnhancedRAGClassifier()
        print("   ✅ Enhanced RAG Classifier initialized")
        
        # Check if categories collection was created
        collections_after = client.get_collections().collections
        print(f"   📁 Collections after init: {[c.name for c in collections_after]}")
        
        # Test classification
        print("6. Testing classification...")
        test_text = """
        SERVICE AGREEMENT
        
        This service agreement is between ABC Corp and XYZ Services for consulting services.
        The agreement outlines payment terms, deliverables, and project timeline.
        """
        
        result = classifier.classify_with_rag(test_text, "test_service_agreement.pdf")
        print("   ✅ Classification completed")
        print(f"   📊 Result: {json.dumps(result, indent=2)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_enhanced_rag()
    if success:
        print("\n🎉 Enhanced RAG Classifier test completed successfully!")
    else:
        print("\n💥 Enhanced RAG Classifier test failed!")
        sys.exit(1)
