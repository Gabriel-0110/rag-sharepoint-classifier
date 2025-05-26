#!/usr/bin/env python3
"""
Quick verification that SharePoint-compatible categories are working
"""

import requests
import json
import time

def test_classification_api():
    """Test the classification API with SharePoint-compatible examples"""
    
    test_cases = [
        {
            "name": "USCIS Receipt Notice",
            "text": "USCIS Receipt Notice I-797C",
            "filename": "receipt.pdf"
        },
        {
            "name": "Criminal Complaint", 
            "text": "Criminal Complaint People v. Smith burglary charges",
            "filename": "complaint.pdf"
        },
        {
            "name": "Notice to Appear",
            "text": "Notice to Appear removal proceedings Immigration Judge",
            "filename": "nta.pdf"
        }
    ]
    
    print("🔍 Testing SharePoint-Compatible Classification API")
    print("=" * 60)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- Test {i}: {test_case['name']} ---")
        
        try:
            response = requests.post(
                'http://localhost:8000/classify-enhanced',
                json={
                    'text': test_case['text'],
                    'filename': test_case['filename']
                },
                timeout=20
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Classification successful:")
                print(f"   Category: {result.get('doc_category', 'Unknown')}")
                print(f"   Type: {result.get('doc_type', 'Unknown')}")
                print(f"   Confidence: {result.get('confidence', 'Unknown')}")
                
                # Check if we're getting SharePoint-compatible categories
                category = result.get('doc_category', '')
                if any(sp_cat in category for sp_cat in [
                    'Asylum & Refugee', 'Family-Sponsored Immigration', 
                    'Employment-Based Immigration', 'Criminal Defense (Pretrial & Trial)',
                    'Removal & Deportation Defense'
                ]):
                    print(f"   ✅ SharePoint-compatible category detected!")
                else:
                    print(f"   ⚠️  Category may not be SharePoint-compatible")
                    
            else:
                print(f"❌ API Error: {response.status_code}")
                
        except requests.exceptions.Timeout:
            print(f"⏱️ Request timed out (may still be processing)")
        except Exception as e:
            print(f"❌ Error: {e}")
            
        time.sleep(2)  # Brief pause between requests

if __name__ == "__main__":
    test_classification_api()
