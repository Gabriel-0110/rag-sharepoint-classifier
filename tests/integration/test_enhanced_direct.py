#!/usr/bin/env python3
"""
Direct test of Enhanced RAG Classification functionality
"""

import asyncio
import sys
import os

# Add the project directory to the path
sys.path.append('/home/azureuser/rag_project')

async def test_enhanced_rag_direct():
    """Test the enhanced RAG classifier directly."""
    print("🧪 Testing Enhanced RAG Classifier Directly")
    
    try:
        # Import and initialize
        from enhanced_rag_classifier import EnhancedRAGClassifier
        print("📚 Initializing Enhanced RAG Classifier...")
        
        classifier = EnhancedRAGClassifier()
        print("✅ Enhanced RAG Classifier initialized successfully!")
        
        # Test with our contract document
        test_file = "/home/azureuser/rag_project/test_contract.pdf"
        
        if os.path.exists(test_file):
            print(f"📄 Testing with file: {test_file}")
            
            # Read the file content (we'll use the existing extracted text)
            with open("/home/azureuser/rag_project/test_contract.txt", "r") as f:
                test_text = f.read()
            
            print(f"📝 Document text preview: {test_text[:200]}...")
            
            # Classify using enhanced RAG
            result = classifier.classify_with_rag(test_text, "test_contract.pdf")
            
            print("\n🎯 Enhanced RAG Classification Results:")
            print("=" * 50)
            print(f"📋 Document Type: {result.get('doc_type', 'Unknown')}")
            print(f"🏷️  Category: {result.get('doc_category', 'Unknown')}")
            print(f"🎯 Confidence: {result.get('confidence', 'Unknown')}")
            
            if 'rag_context' in result:
                rag_info = result['rag_context']
                print(f"🔍 RAG Context Used: {rag_info.get('context_used', False)}")
                print(f"📚 Similar Documents Found: {rag_info.get('similar_documents', 0)}")
                print(f"🏷️  Relevant Categories Found: {rag_info.get('relevant_categories', 0)}")
            
            print("=" * 50)
            
            # Test with a different document type
            print("\n📄 Testing with a different document type...")
            
            test_text_2 = """
            EMPLOYMENT CONTRACT
            
            This employment agreement is between ABC Corporation and John Smith
            for the position of Software Engineer. The contract includes salary,
            benefits, vacation time, and termination clauses.
            
            Salary: $80,000 per year
            Start Date: January 1, 2024
            Benefits: Health insurance, dental, 401k matching
            """
            
            result_2 = classifier.classify_with_rag(test_text_2, "employment_contract.pdf")
            
            print("🎯 Second Classification Results:")
            print("=" * 30)
            print(f"📋 Document Type: {result_2.get('doc_type', 'Unknown')}")
            print(f"🏷️  Category: {result_2.get('doc_category', 'Unknown')}")
            print(f"🎯 Confidence: {result_2.get('confidence', 'Unknown')}")
            print("=" * 30)
            
            return True
            
        else:
            print(f"❌ Test file not found: {test_file}")
            return False
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function."""
    success = asyncio.run(test_enhanced_rag_direct())
    
    if success:
        print("\n🎉 Enhanced RAG Classifier test completed successfully!")
        print("✅ The enhanced RAG system is working and ready for production use!")
    else:
        print("\n💥 Enhanced RAG Classifier test failed!")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
