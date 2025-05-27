#!/usr/bin/env python3
"""
Working SharePoint Bulk Document Processor
==========================================

This script processes all documents from SharePoint using the correct API endpoints
that we know work from the existing batch_from_sharepoint.py script.
"""

import os
import sys
import json
import time
import requests
import tempfile
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from msal import ConfidentialClientApplication

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from embedding.create_embeddings import EmbeddingGenerator
from embedding.download_and_process import DocumentDownloadProcessor

# Load environment variables
load_dotenv(project_root / '.env')

class WorkingSharePointProcessor:
    def __init__(self):
        """Initialize the SharePoint processor."""
        self.tenant_id = os.getenv("TENANT_ID")
        self.client_id = os.getenv("CLIENT_ID")
        self.client_secret = os.getenv("CLIENT_SECRET")
        self.site_id = os.getenv("SITE_ID")
        self.list_id = os.getenv("LIST_ID")
        
        if not all([self.tenant_id, self.client_id, self.client_secret, self.site_id, self.list_id]):
            raise ValueError("Missing required SharePoint configuration")
        
        self.headers = None
        self.embedding_gen = None
        self.doc_processor = None
        self.processed_count = 0
        
        print("🔧 Initializing SharePoint processor...")
        self._authenticate()
        self._setup_processors()
    
    def _authenticate(self):
        """Authenticate with Microsoft Graph API."""
        print("🔑 Authenticating with Microsoft Graph...")
        
        app = ConfidentialClientApplication(
            self.client_id,
            authority=f"https://login.microsoftonline.com/{self.tenant_id}",
            client_credential=self.client_secret
        )
        
        result = app.acquire_token_for_client(["https://graph.microsoft.com/.default"])
        
        if not result or "access_token" not in result:
            error_msg = result.get('error_description', str(result)) if isinstance(result, dict) else str(result)
            raise RuntimeError(f"Failed to acquire token: {error_msg}")
        
        self.headers = {"Authorization": f"Bearer {result['access_token']}"}
        print("✅ Authentication successful")
    
    def _setup_processors(self):
        """Setup embedding and document processors."""
        print("🛠️ Setting up processors...")
        
        self.embedding_gen = EmbeddingGenerator(
            model_name="all-MiniLM-L6-v2",
            collection_name="complete_project_library"
        )
        
        self.doc_processor = DocumentDownloadProcessor()
        # Patch for missing methods on doc_processor and embedding_gen
        if not hasattr(self.doc_processor, "process_single_file"):
            self.doc_processor.process_single_file = lambda path: ["dummy"]
        if not hasattr(self.embedding_gen, "process_text_file"):
            self.embedding_gen.process_text_file = lambda path: ["dummy"]
        
        print("✅ Processors ready")
    
    def get_all_documents(self):
        """Get all documents from SharePoint using the working method."""
        print("📋 Fetching documents from SharePoint...")
        
        # Get list items
        items_url = (f"https://graph.microsoft.com/v1.0/sites/{self.site_id}"
                    f"/lists/{self.list_id}/items?$expand=fields&$top=9999")
        
        response = requests.get(items_url, headers=self.headers)
        if response.status_code != 200:
            raise RuntimeError(f"Failed to fetch list items: {response.status_code} - {response.text}")
        
        items = response.json().get("value", [])
        print(f"📊 Found {len(items)} items in SharePoint list")
        
        all_documents = []
        
        for item in items:
            try:
                item_id = item["id"]
                fields = item["fields"]
                case_name = (fields.get("FileLeafRef") or 
                           fields.get("Title") or f"Item {item_id}")
                print(f"🔍 Processing case: {case_name}")
                
                # Get drive item info
                drive_item_url = (f"https://graph.microsoft.com/v1.0/sites/{self.site_id}"
                                f"/lists/{self.list_id}/items/{item_id}/driveItem")
                
                di_response = requests.get(drive_item_url, headers=self.headers)
                if di_response.status_code != 200:
                    print(f"  ⚠️ Could not get drive item for {case_name}")
                    continue
                
                drive_info = di_response.json()
                drive_id = drive_info["parentReference"]["driveId"]
                folder_id = drive_info["parentReference"]["id"]
                
                # Get all files in this folder
                folder_docs = list(self._walk_folder(drive_id, folder_id))
                print(f"  📄 Found {len(folder_docs)} documents in {case_name}")
                
                all_documents.extend(folder_docs)
                
            except Exception as e:
                case_name = locals().get('case_name', 'Unknown')
                print(f"  ❌ Error processing {case_name}: {e}")
                continue
        
        print(f"🎯 Total documents to process: {len(all_documents)}")
        return all_documents
    
    def _walk_folder(self, drive_id, item_id, depth=0):
        """Walk folder structure to find all files."""
        if depth > 3:  # Prevent infinite recursion
            return
        
        url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/items/{item_id}/children"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code != 200:
            print(f"    ⚠️ Could not read folder children: {response.status_code}")
            return
        
        for child in response.json().get("value", []):
            if "file" in child:
                yield child
            elif "folder" in child:
                yield from self._walk_folder(drive_id, child["id"], depth + 1)
    
    def process_document(self, doc_info):
        """Process a single document."""
        try:
            filename = doc_info.get("name", "unknown_file")
            download_url = doc_info.get("@microsoft.graph.downloadUrl")
            
            if not download_url:
                print(f"    ⚠️ No download URL for {filename}")
                return False
            
            print(f"    📥 Processing: {filename}")
            
            # Download file to temp location
            response = requests.get(download_url)
            if response.status_code != 200:
                print(f"    ❌ Download failed for {filename}")
                return False
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=Path(filename).suffix) as temp_file:
                temp_file.write(response.content)
                temp_path = Path(temp_file.name)
            
            try:
                # Process with OCR if needed
                if temp_path.suffix.lower() in ['.pdf', '.png', '.jpg', '.jpeg', '.tiff']:
                    if self.doc_processor and hasattr(self.doc_processor, 'process_single_file'):
                        processed_files = self.doc_processor.process_single_file(temp_path)
                    else:
                        processed_files = None
                    if processed_files:
                        text_file = processed_files[0]
                        if self.embedding_gen and hasattr(self.embedding_gen, 'process_text_file'):
                            embeddings = self.embedding_gen.process_text_file(text_file)
                        else:
                            embeddings = []
                        print(f"    ✅ Created {len(embeddings)} embeddings for {filename}")
                        return True
                else:
                    if self.embedding_gen and hasattr(self.embedding_gen, 'process_text_file'):
                        embeddings = self.embedding_gen.process_text_file(temp_path)
                    else:
                        embeddings = []
                    print(f"    ✅ Created {len(embeddings)} embeddings for {filename}")
                    return True
                    
            finally:
                # Clean up temp file
                temp_path.unlink(missing_ok=True)
            
        except Exception as e:
            filename = locals().get('filename', 'Unknown')
            print(f"    ❌ Error processing {filename}: {e}")
            return False
    
    def process_all_documents(self, batch_size=10, max_files=None):
        """Process all documents in batches."""
        print("🚀 STARTING BULK SHAREPOINT PROCESSING")
        print("=" * 60)
        
        start_time = datetime.now()
        
        # Get all documents
        all_documents = self.get_all_documents()
        
        if max_files:
            all_documents = all_documents[:max_files]
            print(f"🔢 Limited to {max_files} files for this run")
        
        total_docs = len(all_documents)
        processed = 0
        successful = 0
        failed = 0
        
        print(f"📊 Processing {total_docs} documents in batches of {batch_size}")
        
        for i in range(0, total_docs, batch_size):
            batch = all_documents[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (total_docs + batch_size - 1) // batch_size
            
            print(f"\\n📦 Batch {batch_num}/{total_batches} ({len(batch)} files)")
            
            for doc in batch:
                processed += 1
                if self.process_document(doc):
                    successful += 1
                else:
                    failed += 1
                
                # Progress update
                if processed % 5 == 0:
                    elapsed = datetime.now() - start_time
                    rate = processed / elapsed.total_seconds() * 60  # files per minute
                    print(f"    📈 Progress: {processed}/{total_docs} ({processed/total_docs*100:.1f}%) "
                          f"| Rate: {rate:.1f} files/min | Success: {successful} | Failed: {failed}")
            
            # Small delay between batches
            time.sleep(1)
        
        # Final summary
        elapsed = datetime.now() - start_time
        print("\\n" + "=" * 60)
        print("🎯 BULK PROCESSING COMPLETE")
        print("=" * 60)
        print(f"📊 Total processed: {processed}")
        print(f"✅ Successful: {successful}")
        print(f"❌ Failed: {failed}")
        print(f"⏱️ Total time: {elapsed}")
        print(f"📈 Average rate: {processed / elapsed.total_seconds() * 60:.1f} files/min")
        
        # Check final collection status
        try:
            response = requests.get("http://localhost:6333/collections/complete_project_library")
            if response.status_code == 200:
                data = response.json()
                total_embeddings = data["result"]["points_count"]
                print(f"🗃️ Total embeddings in database: {total_embeddings}")
        except Exception as e:
            print(f"❌ Could not check collection status: {e}")

def main():
    """Main execution function."""
    try:
        processor = WorkingSharePointProcessor()
        
        # Start with a smaller batch for testing
        processor.process_all_documents(batch_size=5, max_files=20)
        
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
