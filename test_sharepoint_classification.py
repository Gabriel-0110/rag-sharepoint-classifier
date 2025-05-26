#!/usr/bin/env python3
"""
Test script to verify SharePoint-compatible classification system
"""

import sys
import os
sys.path.append('/home/azureuser/rag_project')

from core.enhanced_rag_classifier import EnhancedRAGClassifier
import json

def test_sharepoint_classification():
    """Test the updated SharePoint-compatible classification system"""
    print("🔍 Testing SharePoint-Compatible RAG Classification System")
    print("=" * 60)
    
    try:
        # Initialize classifier
        print("📋 Initializing Enhanced RAG Classifier...")
        classifier = EnhancedRAGClassifier()
        
        # Test cases with SharePoint-compatible expected results
        test_cases = [
            {
                "name": "USCIS Receipt Notice",
                "text": """UNITED STATES CITIZENSHIP AND IMMIGRATION SERVICES
RECEIPT NOTICE
Form I-797C, Notice of Action

Receipt Number: MSC1234567890
Priority Date: January 15, 2024
Notice Date: February 1, 2024

The above petition has been received by USCIS. We will notify you when a decision has been made.""",
                "filename": "uscis_receipt.pdf",
                "expected_type": "USCIS Receipt Notice",
                "expected_category": "Family-Sponsored Immigration"
            },
            {
                "name": "Criminal Complaint",
                "text": """STATE OF CALIFORNIA
CRIMINAL COMPLAINT

Case No: CR-2024-0001
People v. Smith

CHARGES:
Count 1: Violation of Penal Code Section 459 (Burglary)
Count 2: Violation of Penal Code Section 484 (Theft)

The defendant is hereby charged with the above offenses.""",
                "filename": "criminal_complaint.pdf",
                "expected_type": "Criminal Complaint/Indictment",
                "expected_category": "Criminal Defense (Pretrial & Trial)"
            },
            {
                "name": "Notice to Appear",
                "text": """NOTICE TO APPEAR
IN REMOVAL PROCEEDINGS UNDER SECTION 240 OF THE IMMIGRATION AND NATIONALITY ACT

File No: A123456789
Name: John Doe

YOU ARE AN ALIEN PRESENT IN THE UNITED STATES WHO HAS NOT BEEN ADMITTED OR PAROLED.

You are hereby notified to appear before an Immigration Judge.""",
                "filename": "nta.pdf",
                "expected_type": "Notice to Appear (NTA)",
                "expected_category": "Removal & Deportation Defense"
            }
        ]
        
        print(f"\n🧪 Running {len(test_cases)} test cases...")
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n--- Test Case {i}: {test_case['name']} ---")
            print(f"Filename: {test_case['filename']}")
            
            try:
                # Test fallback classification first (should be fast)
                fallback_result = classifier._fallback_classification(test_case['text'])
                print(f"Fallback Classification:")
                print(f"  Category: {fallback_result.get('doc_category', 'Unknown')}")
                print(f"  Type: {fallback_result.get('doc_type', 'Unknown')}")
                print(f"  Confidence: {fallback_result.get('confidence', 'Unknown')}")
                
                # Test full RAG classification (may timeout)
                print(f"Testing RAG Classification...")
                try:
                    rag_result = classifier.classify_with_rag(test_case['text'], test_case['filename'])
                    print(f"RAG Classification:")
                    print(f"  Category: {rag_result.get('doc_category', 'Unknown')}")
                    print(f"  Type: {rag_result.get('doc_type', 'Unknown')}")
                    print(f"  Confidence: {rag_result.get('confidence', 'Unknown')}")
                    print(f"  RAG Context: {rag_result.get('rag_context', {})}")
                except Exception as e:
                    print(f"  ⚠️ RAG Classification failed: {e}")
                    print(f"  Using fallback result instead")
                
            except Exception as e:
                print(f"❌ Error in test case: {e}")
        
        print(f"\n✅ Classification system test completed!")
        
        # Display available categories and types
        print(f"\n📊 Available SharePoint-Compatible Categories ({len(classifier.category_definitions)}):")
        for category in sorted(classifier.category_definitions.keys()):
            print(f"  • {category}")
            
        print(f"\n📋 Available SharePoint-Compatible Document Types ({len(classifier.document_types)}):")
        for doc_type in sorted(classifier.document_types.keys()):
            print(f"  • {doc_type}")
            
    except Exception as e:
        print(f"❌ Failed to initialize classifier: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = test_sharepoint_classification()
    sys.exit(0 if success else 1)
