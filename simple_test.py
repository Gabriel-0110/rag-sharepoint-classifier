#!/usr/bin/env python3
import requests
import json
import sys

print("Testing enhanced classification endpoint...")

try:
    response = requests.post(
        "http://localhost:8000/classify-enhanced",
        json={"text": "Immigration form I-130", "filename": "I130.pdf"},
        timeout=10
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Category: {result.get('category', 'N/A')}")
        print(f"Document Type: {result.get('document_type', 'N/A')}")
    else:
        print(f"Error: {response.text}")
        
except requests.exceptions.Timeout:
    print("Request timed out")
except Exception as e:
    print(f"Error: {e}")
