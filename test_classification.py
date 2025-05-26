#!/usr/bin/env python3
"""
Test script to verify the enhanced classification system is working
with updated document categories and types.
"""

import requests
import json
import time

def test_classification_endpoint():
    """Test the enhanced classification endpoint with sample documents"""
    
    base_url = "http://localhost:8000"
    
    # Test cases covering different document types we defined
    test_cases = [
        {
            "name": "Immigration Court Notice to Appear",
            "text": """NOTICE TO APPEAR
            
In Removal Proceedings Under Section 240 of the Immigration and Nationality Act

To: John Smith
File No: A123456789

You are an alien present in the United States who has been determined by an immigration officer to be removable from the United States for the reasons stated below. You are ordered to appear before an immigration judge of the U.S. Immigration Court.

Charges: Section 237(a)(1)(A) of the Immigration and Nationality Act - being an alien who at the time of entry was not in possession of valid entry documents.""",
            "filename": "NTA_John_Smith_A123456789.pdf"
        },
        {
            "name": "USCIS Form I-130",
            "text": """USCIS Form I-130
Immigrant Petition for Alien Relative

Part 1. Information About You (Petitioner)
1. I am filing this petition for my: Spouse
2. Are you filing this petition based on your status as a lawful permanent resident? Yes

Part 2. Information About Your Relative
Full Name: Maria Smith
Date of Birth: 01/15/1985
Country of Birth: Mexico""",
            "filename": "I130_Maria_Smith.pdf"
        },
        {
            "name": "Criminal Complaint",
            "text": """UNITED STATES DISTRICT COURT
CRIMINAL COMPLAINT

Case No: 24-CR-123

The undersigned complainant being duly sworn states that there is probable cause to believe that on or about January 15, 2024, in the District of Nevada, defendant JOHN DOE did knowingly and intentionally possess with intent to distribute controlled substances, in violation of 21 U.S.C. § 841(a)(1).""",
            "filename": "Criminal_Complaint_24CR123.pdf"
        },
        {
            "name": "Client Communication Email",
            "text": """From: attorney@lawfirm.com
To: client@email.com
Subject: Update on Your Immigration Case

Dear Mr. Smith,

I wanted to provide you with an update on the status of your Form I-485 Application to Adjust Status. We received a Request for Evidence (RFE) from USCIS requesting additional documentation regarding your employment authorization.

Please review the attached RFE and gather the requested documents. We have 87 days to respond.

Best regards,
Immigration Attorney""",
            "filename": "Client_Email_Case_Update.pdf"
        }
    ]
    
    print("🔍 Testing Enhanced RAG Classification System")
    print("=" * 60)
    
    # Test each case
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📄 Test {i}: {test_case['name']}")
        print("-" * 40)
        
        try:
            # Make the request
            response = requests.post(
                f"{base_url}/classify-enhanced",
                json={
                    "text": test_case["text"],
                    "filename": test_case["filename"]
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Status: SUCCESS")
                print(f"📂 Category: {result.get('category', 'N/A')}")
                print(f"📋 Document Type: {result.get('document_type', 'N/A')}")
                print(f"🎯 Confidence: {result.get('confidence', 'N/A')}")
                
                if 'reasoning' in result:
                    print(f"💭 Reasoning: {result['reasoning'][:100]}...")
                    
            else:
                print(f"❌ Status: ERROR ({response.status_code})")
                print(f"Error: {response.text}")
                
        except requests.exceptions.Timeout:
            print(f"⏰ Status: TIMEOUT")
        except Exception as e:
            print(f"💥 Status: EXCEPTION - {str(e)}")
            
        time.sleep(1)  # Brief pause between requests
    
    print(f"\n🏁 Classification Testing Complete")
    print("=" * 60)

if __name__ == "__main__":
    test_classification_endpoint()
