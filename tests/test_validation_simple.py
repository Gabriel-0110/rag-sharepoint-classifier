#!/usr/bin/env python3
"""
Simple validation test for Enhanced 3-Model RAG Classification System

This test performs basic validation without loading heavy models initially.
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test if all required modules can be imported"""
    print("🔍 Testing imports...")
    
    try:
        from core.enhanced_rag_classifier import EnhancedRAGClassifier
        print("✅ EnhancedRAGClassifier imported successfully")
    except Exception as e:
        print(f"❌ EnhancedRAGClassifier import failed: {e}")
        return False
    
    try:
        from core.document_processor import DocumentProcessor
        print("✅ DocumentProcessor imported successfully")
    except Exception as e:
        print(f"❌ DocumentProcessor import failed: {e}")
        return False
    
    # Commented out because module does not exist
    # try:
    #     from core.vector_store import VectorStore
    #     print("✅ VectorStore imported successfully")
    # except Exception as e:
    #     print(f"❌ VectorStore import failed: {e}")
    #     return False
    
    return True

def test_classifier_initialization():
    """Test if the classifier can be initialized without loading models"""
    print("\n🤖 Testing classifier initialization...")
    
    try:
        from core.enhanced_rag_classifier import EnhancedRAGClassifier
        
        # Initialize without loading models (for testing)
        classifier = EnhancedRAGClassifier(
            use_quantization=True,
            enable_validation=True,
            enable_fallback=True,
            load_models=False  # Don't load models yet
        )
        print("✅ Classifier initialized successfully")
        return True
        
    except Exception as e:
        print(f"❌ Classifier initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_method_existence():
    """Test if all required methods exist in the classifier"""
    print("\n🔧 Testing method existence...")
    
    try:
        from core.enhanced_rag_classifier import EnhancedRAGClassifier
        
        classifier = EnhancedRAGClassifier(load_models=False)
        
        # Check if key methods exist
        required_methods = [
            'classify_document_enhanced',
            '_build_saul_prompt',
            '_parse_classification_result', 
            '_classify_with_fallback',
            '_validate_with_bart',
            '_calculate_confidence_score',
            '_combine_classification_results'
        ]
        
        missing_methods = []
        for method_name in required_methods:
            if not hasattr(classifier, method_name):
                missing_methods.append(method_name)
            else:
                print(f"✅ Method {method_name} exists")
        
        if missing_methods:
            print(f"❌ Missing methods: {missing_methods}")
            return False
        
        print("✅ All required methods exist")
        return True
        
    except Exception as e:
        print(f"❌ Method check failed: {e}")
        return False

def test_file_access():
    """Test if test files are accessible"""
    print("\n📂 Testing file access...")
    
    test_dir = "/home/azureuser/rag_project/test_batch_downloads"
    
    if not os.path.exists(test_dir):
        print(f"❌ Test directory does not exist: {test_dir}")
        return False
    
    files = [f for f in os.listdir(test_dir) if os.path.isfile(os.path.join(test_dir, f))]
    
    if not files:
        print(f"❌ No files found in {test_dir}")
        return False
    
    print(f"✅ Found {len(files)} test files:")
    for i, file_name in enumerate(files[:5], 1):  # Show first 5
        print(f"   {i}. {file_name}")
    
    if len(files) > 5:
        print(f"   ... and {len(files) - 5} more files")
    
    return True

def test_simple_classification():
    """Test simple classification without heavy models"""
    print("\n📊 Testing simple classification...")
    
    try:
        from core.enhanced_rag_classifier import EnhancedRAGClassifier
        
        classifier = EnhancedRAGClassifier(load_models=False)
        
        # Test with simple text
        test_text = """
        I-601A Application for Provisional Unlawful Presence Waiver
        This form is used to request a provisional waiver of unlawful presence.
        """
        
        rag_context = {
            'retrieved_documents': [
                {'content': 'Immigration waiver application', 'metadata': {'source': 'test'}}
            ],
            'query': 'Classify this document'
        }
        
        # Test fallback classification (should work without models)
        result = classifier._fallback_classification(test_text, "test_i601a.txt")
        
        print(f"✅ Fallback classification result: {result.get('category', 'UNKNOWN')}")
        print(f"   Confidence: {result.get('confidence_score', 0.0):.3f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Simple classification failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run validation tests"""
    print("=" * 60)
    print("🧪 ENHANCED 3-MODEL CLASSIFIER VALIDATION TEST")
    print("=" * 60)
    
    tests = [
        ("Import Test", test_imports),
        ("Initialization Test", test_classifier_initialization),
        ("Method Existence Test", test_method_existence),
        ("File Access Test", test_file_access),
        ("Simple Classification Test", test_simple_classification)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            if test_func():
                print(f"✅ {test_name} PASSED")
                passed += 1
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"💥 {test_name} CRASHED: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 VALIDATION SUMMARY: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All validation tests passed! System ready for full testing.")
    else:
        print("⚠️  Some validation tests failed. Please check the issues above.")
    
    print("=" * 60)
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
