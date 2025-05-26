#!/usr/bin/env python3
"""
Complete SharePoint Document Classification Automation
Monitors SharePoint library and automatically classifies new documents.
"""

import os
import sys
import time
import requests
from datetime import datetime, timedelta
from msal import ConfidentialClientApplication
from dotenv import load_dotenv
import json
import logging

# Add paths for imports
sys.path.append('/home/azureuser/rag_project/scripts/utils')
sys.path.append('/home/azureuser/rag_project/enhanced')

try:
    from extract_all import extract_text_from_file
    from update_sharepoint import update_metadata
    from log_classification import log_classification_result
except ImportError as e:
    logging.error(f"Import error: {e}")
    print(f"Import error: {e}")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/azureuser/rag_project/logs/application/sharepoint_automation.log'),
        logging.StreamHandler()
    ]
)

# Load environment variables
load_dotenv()

# Configuration
TENANT_ID = os.getenv("TENANT_ID")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
SITE_ID = os.getenv("SITE_ID")
LIST_ID = os.getenv("LIST_ID")
DOWNLOAD_DIR = "sp_batch_downloads"
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "300"))  # 5 minutes default

# Ensure download directory exists
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

class SharePointAutomation:
    def __init__(self):
        self.app = ConfidentialClientApplication(
            CLIENT_ID,
            authority=f"https://login.microsoftonline.com/{TENANT_ID}",
            client_credential=CLIENT_SECRET
        )
        self.headers = None
        self.processed_items = set()
        self.load_processed_items()
    
    def get_access_token(self):
        """Get fresh access token"""
        token_result = self.app.acquire_token_for_client(["https://graph.microsoft.com/.default"])
        if "access_token" not in token_result:
            raise RuntimeError(f"Failed to acquire token: {token_result}")
        
        self.headers = {"Authorization": f"Bearer {token_result['access_token']}"}
        return token_result['access_token']
    
    def load_processed_items(self):
        """Load previously processed items from log"""
        log_file = "classification_log.csv"
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                lines = f.readlines()[1:]  # Skip header
                for line in lines:
                    parts = line.strip().split(',')
                    if len(parts) >= 3:
                        # Extract SharePoint ID (handle different CSV formats)
                        sp_id = parts[2] if parts[2].isdigit() else parts[-1]
                        if sp_id.isdigit():
                            self.processed_items.add(sp_id)
        
        print(f"📋 Loaded {len(self.processed_items)} previously processed items")
    
    def get_recent_documents(self, hours_back=24):
        """Get documents modified in the last N hours"""
        if not self.headers:
            self.get_access_token()
        
        # Calculate datetime filter (ISO format)
        cutoff_time = (datetime.utcnow() - timedelta(hours=hours_back)).isoformat() + "Z"
        
        # Get items from SharePoint list
        url = f"https://graph.microsoft.com/v1.0/sites/{SITE_ID}/lists/{LIST_ID}/items"
        logging.info(f"Checking for new documents in SharePoint site ID: {SITE_ID} and list ID: {LIST_ID}")
        params = {
            "$expand": "fields",
            "$filter": f"fields/Modified ge '{cutoff_time}'",
            "$top": 100
        }
        
        response = requests.get(url, headers=self.headers, params=params)
        
        if response.status_code == 200:
            items = response.json().get('value', [])
            print(f"📄 Found {len(items)} recent documents")
            return items
        else:
            print(f"❌ Error fetching documents: {response.status_code}")
            print(response.text)
            return []
    
    def download_document(self, item):
        """Download document from SharePoint"""
        if not self.headers:
            self.get_access_token()
        
        try:
            # Get file download URL
            item_id = item['id']
            fields = item.get('fields', {})
            filename = fields.get('FileLeafRef', f"document_{item_id}")
            
            # Skip if already processed
            if item_id in self.processed_items:
                print(f"⏭️  Skipping {filename} (already processed)")
                return None, None
            
            # Get drive item for download
            url = f"https://graph.microsoft.com/v1.0/sites/{SITE_ID}/lists/{LIST_ID}/items/{item_id}/driveItem/content"
            
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                file_path = os.path.join(DOWNLOAD_DIR, filename)
                with open(file_path, 'wb') as f:
                    f.write(response.content)
                
                print(f"⬇️  Downloaded: {filename}")
                return file_path, item_id
            else:
                print(f"❌ Error downloading {filename}: {response.status_code}")
                return None, None
                
        except Exception as e:
            print(f"❌ Error processing item {item.get('id')}: {e}")
            return None, None
    
    def process_document(self, file_path, item_id):
        """Extract, classify, and update metadata for a document"""
        try:
            filename = os.path.basename(file_path)
            print(f"🔍 Processing: {filename}")
            
            # Extract text
            text = extract_text_from_file(file_path)
            if not text.strip():
                print(f"⚠️  No text extracted from {filename}")
                return False
            
            print(f"📄 Extracted {len(text)} characters")
            
            # Classify document using available endpoints
            try:
                # Try enhanced classification first
                classification_response = requests.post(
                    'http://localhost:8000/classify-enhanced',
                    json={'text': text, 'filename': filename},
                    timeout=30
                )
                
                if classification_response.status_code == 200:
                    classification = classification_response.json()
                    doc_type = classification.get('doc_type', 'Unknown')
                    doc_category = classification.get('doc_category', 'General')
                    confidence = classification.get('confidence', 'Low')
                    logging.info(f"Enhanced classification successful: {doc_type} | {doc_category} | Confidence: {confidence}")
                
                # If enhanced classification fails, use simple rules-based classification
                else:
                    logging.warning(f"Enhanced classification failed ({classification_response.status_code}), using rules-based classification...")
                    doc_type, doc_category = self._classify_with_rules(text, filename)
                    logging.info(f"Rules-based classification: {doc_type} | {doc_category}")
                    
            except Exception as e:
                logging.error(f"Classification error: {e}")
                doc_type, doc_category = self._classify_with_rules(text, filename)
            
            print(f"🏷️  Classification: {doc_type} | {doc_category}")
            
            # Update SharePoint metadata
            update_metadata(item_id, doc_type, doc_category, filename)
            
            # Mark as processed
            self.processed_items.add(item_id)
            
            print(f"✅ Completed: {filename}")
            return True
            
        except Exception as e:
            print(f"❌ Error processing {filename}: {e}")
            return False
        finally:
            # Clean up downloaded file
            if os.path.exists(file_path):
                os.remove(file_path)
    
    def run_automation_cycle(self):
        """Run one complete automation cycle"""
        print(f"\n🚀 Starting automation cycle - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            # Get recent documents
            recent_docs = self.get_recent_documents(hours_back=1)  # Check last hour
            
            if not recent_docs:
                print("📭 No new documents found")
                return
            
            processed_count = 0
            
            for item in recent_docs:
                try:
                    # Download document
                    file_path, item_id = self.download_document(item)
                    
                    if file_path and item_id:
                        # Process document
                        success = self.process_document(file_path, item_id)
                        if success:
                            processed_count += 1
                        
                        # Small delay between documents
                        time.sleep(2)
                
                except Exception as e:
                    print(f"❌ Error in automation cycle: {e}")
                    continue
            
            print(f"📊 Cycle complete: {processed_count} documents processed")
            
        except Exception as e:
            print(f"❌ Critical error in automation cycle: {e}")
    
    def run_continuous(self):
        """Run continuous monitoring"""
        print(f"🎯 Starting continuous SharePoint monitoring...")
        print(f"📊 Poll interval: {POLL_INTERVAL} seconds")
        print(f"🗂️  Monitoring: {LIST_ID}")
        
        while True:
            try:
                # Check services are running before processing
                if not self.check_services():
                    logging.error("Required services not available. Waiting 60 seconds...")
                    time.sleep(60)
                    continue
                
                self.run_automation_cycle()
                print(f"⏰ Sleeping for {POLL_INTERVAL} seconds...")
                time.sleep(POLL_INTERVAL)
                
            except KeyboardInterrupt:
                print("\n🛑 Stopping automation...")
                break
            except Exception as e:
                logging.error(f"❌ Unexpected error: {e}")
                print(f"❌ Unexpected error: {e}")
                print("🔄 Continuing after 60 seconds...")
                time.sleep(60)
    
    def check_services(self):
        """Check if required services are running"""
        services = {
            'FastAPI': 'http://localhost:8000/enhanced-status',
            'Qdrant': 'http://localhost:6333/collections'
        }
        
        all_services_ok = True
        for service_name, url in services.items():
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    logging.info(f"✅ {service_name} service is running")
                else:
                    logging.warning(f"⚠️ {service_name} service returned {response.status_code}")
                    all_services_ok = False
            except Exception as e:
                logging.error(f"❌ {service_name} service not available: {e}")
                all_services_ok = False
        
        # Check Mistral AI optionally (not required for basic operation)
        try:
            response = requests.get('http://localhost:8001/health', timeout=2)
            if response.status_code == 200:
                logging.info("✅ Mistral AI service is running (optional)")
            else:
                logging.info("⚠️ Mistral AI service not available (using fallback classification)")
        except:
            logging.info("⚠️ Mistral AI service not available (using fallback classification)")
        
        return all_services_ok
    
    def _classify_with_rules(self, text: str, filename: str) -> tuple:
        """Simple rules-based classification as fallback"""
        text_lower = text.lower()
        filename_lower = filename.lower()
        
        # Immigration document patterns
        immigration_keywords = ['uscis', 'green card', 'visa', 'immigration', 'naturalization', 
                              'citizenship', 'petition', 'i-130', 'i-485', 'i-765', 'i-131',
                              'birth certificate', 'marriage certificate', 'passport']
        
        # Criminal law patterns  
        criminal_keywords = ['criminal', 'felony', 'misdemeanor', 'police', 'arrest', 'court',
                           'plea', 'sentencing', 'conviction', 'probation']
        
        # Document type patterns
        if any(keyword in text_lower or keyword in filename_lower for keyword in immigration_keywords):
            if 'birth certificate' in text_lower or 'birth certificate' in filename_lower:
                return 'Birth Certificate', 'Immigration - Family-Based'
            elif 'marriage certificate' in text_lower or 'marriage' in filename_lower:
                return 'Marriage Certificate', 'Immigration - Family-Based'
            elif 'passport' in text_lower or 'passport' in filename_lower:
                return 'Passport Copy', 'Immigration - USCIS Matters'
            elif 'green card' in text_lower or 'greencard' in filename_lower:
                return 'Green Card Copy', 'Immigration - Adjustment of Status'
            else:
                return 'Immigration Document', 'Immigration - USCIS Matters'
        
        elif any(keyword in text_lower or keyword in filename_lower for keyword in criminal_keywords):
            if 'felony' in text_lower:
                return 'Criminal Document', 'Criminal Defense - Felony'
            elif 'misdemeanor' in text_lower:
                return 'Criminal Document', 'Criminal Defense - Misdemeanor'
            else:
                return 'Criminal Document', 'Criminal Defense - Immigration Consequences'
        
        # Default classification
        return 'Legal Document', 'Administrative'

def main():
    """Main entry point"""
    automation = SharePointAutomation()
    
    # Check if running in continuous mode
    mode = os.getenv("AUTOMATION_MODE", "continuous").lower()
    
    if mode == "once":
        print("🔄 Running single automation cycle...")
        automation.run_automation_cycle()
    else:
        print("🔄 Running continuous automation...")
        automation.run_continuous()

if __name__ == "__main__":
    main()
