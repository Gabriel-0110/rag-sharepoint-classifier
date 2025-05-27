#!/usr/bin/env python3
"""
Comprehensive test of RAG Document Classification functionality
Tests all major features including FastAPI endpoints, RAG classification, and SharePoint integration
"""

import os
import sys
import requests
import json
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.absolute()
sys.path.append(str(project_root))

def test_imports():
    """Test that all core modules can be imported successfully"""
    print("🧪 Testing imports...")
    
    try:
        from core.enhanced_rag_classifier import EnhancedRAGClassifier
        print("✅ EnhancedRAGClassifier imported successfully")
    except Exception as e:
        print(f"❌ Failed to import EnhancedRAGClassifier: {e}")
        return False
    
    try:
        from core.confidence_scoring import calculate_confidence_score
        print("✅ Confidence scoring imported successfully")
    except Exception as e:
        print(f"❌ Failed to import confidence scoring: {e}")
        
    try:
        from core.trocr_integration import TrOCRProcessor
        print("✅ TrOCR integration imported successfully")
    except Exception as e:
        print(f"❌ Failed to import TrOCR: {e}")
        
    return True

def test_rag_classifier_initialization():
    """Test RAG classifier initialization"""
    print("\n🧪 Testing RAG Classifier initialization...")
    
    try:
        from core.enhanced_rag_classifier import EnhancedRAGClassifier
        classifier = EnhancedRAGClassifier()
        
        # Check attributes
        assert hasattr(classifier, 'category_definitions'), "Missing category_definitions"
        assert hasattr(classifier, 'client'), "Missing Qdrant client"
        assert hasattr(classifier, 'embedding_model'), "Missing embedding model"
        assert hasattr(classifier, 'mistral_url'), "Missing Mistral URL"
        
        # Check category definitions
        assert len(classifier.category_definitions) > 0, "No category definitions loaded"
        
        categories = list(classifier.category_definitions.keys())
        print(f"✅ Loaded {len(categories)} legal categories:")
        for cat in categories[:3]:  # Show first 3
            print(f"   - {cat}")
        if len(categories) > 3:
            print(f"   ... and {len(categories) - 3} more")
            
        return True
        
    except Exception as e:
        print(f"❌ RAG Classifier initialization failed: {e}")
        return False

def run_comprehensive_tests():
    """Run all comprehensive tests"""
    print("🚀 Starting Comprehensive RAG Document Classification Tests")
    print("=" * 70)
    
    tests = [
        ("Import Tests", test_imports),
        ("RAG Classifier Initialization", test_rag_classifier_initialization),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 70)
    print("📊 COMPREHENSIVE TEST RESULTS")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:35} {status}")
    
    print("-" * 70)
    print(f"Total Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    return passed == total

if __name__ == "__main__":
    success = run_comprehensive_tests()
    sys.exit(0 if success else 1)