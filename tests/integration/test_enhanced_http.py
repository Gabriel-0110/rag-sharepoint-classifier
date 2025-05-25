#!/usr/bin/env python3
"""
Test Enhanced RAG via HTTP requests
"""

import requests
import json
import time

def test_enhanced_rag_http():
    """Test enhanced RAG via HTTP requests."""
    print("🌐 Testing Enhanced RAG via HTTP API")
    
    # Wait a moment for any server to start
    time.sleep(2)
    
    # First check if basic server is running
    try:
        response = requests.get("http://localhost:8000/", timeout=5)
        print(f"✅ Basic server health check: {response.status_code}")
    except Exception as e:
        print(f"❌ Server not responding: {e}")
        return False
    
    # Check enhanced status
    try:
        response = requests.get("http://localhost:8000/enhanced-status", timeout=5)
        if response.status_code == 200:
            status = response.json()
            print(f"🎯 Enhanced RAG Status: {status}")
            
            if status.get("enhanced_rag_available"):
                print("✅ Enhanced RAG is available!")
                
                # Test enhanced classification
                test_data = {
                    "text": """
                    SOFTWARE DEVELOPMENT AGREEMENT
                    
                    This agreement is between ABC Tech and XYZ Corp for developing
                    a mobile application. The contract includes payment milestones,
                    intellectual property rights, and delivery schedule.
                    
                    Project: Mobile app development
                    Duration: 6 months
                    Total Cost: $50,000
                    """,
                    "filename": "software_dev_agreement.pdf"
                }
                
                response = requests.post(
                    "http://localhost:8000/classify-enhanced",
                    json=test_data,
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print("\n🎯 Enhanced Classification Results:")
                    print("=" * 50)
                    print(f"📋 Document Type: {result.get('doc_type', 'Unknown')}")
                    print(f"🏷️  Category: {result.get('doc_category', 'Unknown')}")
                    print(f"🎯 Confidence: {result.get('confidence', 'Unknown')}")
                    print(f"🚀 Enhanced RAG: {result.get('enhanced_rag', False)}")
                    
                    if 'rag_context' in result:
                        rag_info = result['rag_context']
                        print(f"🔍 Context Used: {rag_info.get('context_used', False)}")
                        print(f"📚 Similar Docs: {rag_info.get('similar_documents', 0)}")
                        print(f"🏷️  Relevant Categories: {rag_info.get('relevant_categories', 0)}")
                    
                    print("=" * 50)
                    return True
                else:
                    print(f"❌ Enhanced classification failed: {response.status_code}")
                    print(f"Error: {response.text}")
                    return False
            else:
                print("❌ Enhanced RAG not available")
                return False
        else:
            print(f"❌ Enhanced status check failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing enhanced RAG: {e}")
        return False

if __name__ == "__main__":
    success = test_enhanced_rag_http()
    if success:
        print("\n🎉 Enhanced RAG HTTP test completed successfully!")
    else:
        print("\n💥 Enhanced RAG HTTP test failed!")
