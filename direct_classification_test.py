#!/usr/bin/env python3
"""
Direct test of the enhanced RAG classifier to verify SharePoint categories
"""

import sys
import os

# Add the project path
sys.path.insert(0, '/home/azureuser/rag_project')

try:
    from core.enhanced_rag_classifier import EnhancedRAGClassifier
    
    print("🔍 Direct Classification Test")
    print("=" * 50)
    
    # Initialize classifier
    classifier = EnhancedRAGClassifier()
    
    # Display available categories
    print(f"\n📊 Available Categories ({len(classifier.category_definitions)}):")
    for i, category in enumerate(sorted(classifier.category_definitions.keys()), 1):
        print(f"  {i:2d}. {category}")
    
    print(f"\n📋 Available Document Types ({len(classifier.document_types)}):")
    sample_types = list(sorted(classifier.document_types.keys()))[:10]
    for i, doc_type in enumerate(sample_types, 1):
        print(f"  {i:2d}. {doc_type}")
    print(f"  ... and {len(classifier.document_types) - 10} more")
    
    # Test fallback classification
    print(f"\n🧪 Testing Fallback Classification:")
    test_cases = [
        "USCIS Receipt Notice I-797C Form",
        "Criminal Complaint burglary charges",
        "Notice to Appear removal proceedings"
    ]
    
    for test_text in test_cases:
        result = classifier._fallback_classification(test_text)
        print(f"\nInput: {test_text}")
        print(f"  Category: {result['doc_category']}")
        print(f"  Type: {result['doc_type']}")
        print(f"  Confidence: {result['confidence']}")
        
        # Check if SharePoint-compatible
        is_sharepoint_compatible = result['doc_category'] in classifier.category_definitions
        print(f"  SharePoint Compatible: {'✅' if is_sharepoint_compatible else '❌'}")
    
    print(f"\n✅ Direct classification test completed successfully!")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
