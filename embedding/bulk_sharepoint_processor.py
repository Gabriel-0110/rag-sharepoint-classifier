#!/usr/bin/env python3
"""
Bulk SharePoint Document Processing for 20,000+ Files
====================================================

This script processes the entire SharePoint library (Case Management) with 20,000+ documents
to create a complete vector database for semantic search and RAG integration.

Features:
- Processes all documents in SharePoint library
- Batch downloading with retry logic
- Progress tracking and resumability
- Memory-efficient processing
- Comprehensive error handling
- Creates embeddings for all documents
- Updates vector database progressively

Usage:
    python bulk_sharepoint_processor.py --batch-size 100 --max-workers 4
"""

import os
import sys
import json
import time
import logging
import asyncio
import aiohttp
import aiofiles
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Set
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import our existing processors
from core.sharepoint_integration import get_access_token
from embedding.download_and_process import DocumentDownloadProcessor
from embedding.create_embeddings import EmbeddingGenerator
from msal import ConfidentialClientApplication
from dotenv import load_dotenv

# External libraries
import requests
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import uuid

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/azureuser/rag_project/embedding/logs/bulk_sharepoint_processing.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class BulkSharePointProcessor:
    """Process all SharePoint documents for embedding generation."""
    
    def __init__(self):
        """Initialize the bulk processor."""
        self.tenant_id = os.getenv("TENANT_ID")
        self.client_id = os.getenv("CLIENT_ID")
        self.client_secret = os.getenv("CLIENT_SECRET")
        self.site_id = os.getenv("SITE_ID")
        self.list_id = os.getenv("LIST_ID")
        
        # Processing directories
        self.download_dir = Path("/home/azureuser/rag_project/embedding/bulk_downloads")
        self.processed_texts_dir = Path("/home/azureuser/rag_project/embedding/bulk_processed_texts")
        self.progress_file = Path("/home/azureuser/rag_project/embedding/bulk_progress.json")
        
        # Create directories
        self.download_dir.mkdir(exist_ok=True)
        self.processed_texts_dir.mkdir(exist_ok=True)
        
        # Initialize processors
        self.doc_processor = DocumentDownloadProcessor()
        self.embedding_generator = EmbeddingGenerator()
        
        # Initialize Qdrant client
        self.qdrant_client = QdrantClient(
            url=os.getenv("QDRANT_URL", "http://localhost:6333"),
            api_key=os.getenv("QDRANT_API_KEY")
        )
        
        # Progress tracking
        self.progress = self.load_progress()
        
        # Use existing collection instead of creating new one
        self.progress["collection_name"] = "complete_project_library"
        
        # Get access token
        self.access_token = self.get_sharepoint_token()
        
    def get_sharepoint_token(self) -> str:
        """Get SharePoint access token."""
        try:
            app = ConfidentialClientApplication(
                self.client_id,
                authority=f"https://login.microsoftonline.com/{self.tenant_id}",
                client_credential=self.client_secret
            )
            
            result = app.acquire_token_for_client(["https://graph.microsoft.com/.default"])
            
            if not result or not isinstance(result, dict) or "access_token" not in result:
                raise Exception(f"Failed to acquire token: {result}")
                
            return str(result["access_token"]) if result and "access_token" in result else ""
            
        except Exception as e:
            logger.error(f"❌ Failed to get SharePoint token: {e}")
            raise
    
    def load_progress(self) -> Dict:
        """Load processing progress from file."""
        if self.progress_file.exists():
            with open(self.progress_file, 'r') as f:
                return json.load(f)
        return {
            "processed_items": [],
            "failed_items": [],
            "total_files_found": 0,
            "total_files_processed": 0,
            "last_batch": 0,
            "collection_name": "complete_project_library",
            "start_time": None,
            "last_update": None
        }
    
    def save_progress(self):
        """Save processing progress to file."""
        self.progress["last_update"] = datetime.now().isoformat()
        with open(self.progress_file, 'w') as f:
            json.dump(self.progress, f, indent=2)
    
    def get_all_sharepoint_items(self) -> List[Dict]:
        """Get all items from SharePoint document library using /drive/root/children endpoint."""
        logger.info("🔍 Fetching all SharePoint items (using /drive/root/children)...")
        headers = {"Authorization": f"Bearer {self.access_token}"}
        all_items = []
        next_url = f"https://graph.microsoft.com/v1.0/sites/{self.site_id}/drive/root/children?$top=999"
        while next_url:
            try:
                response = requests.get(next_url, headers=headers)
                response.raise_for_status()
                data = response.json()
                items = data.get("value", [])
                if not items:
                    break
                all_items.extend(items)
                logger.info(f"📋 Fetched {len(all_items)} items so far...")
                next_url = data.get("@odata.nextLink")
            except Exception as e:
                logger.error(f"❌ Error fetching SharePoint items: {e}")
                break
        logger.info(f"📊 Total SharePoint items found: {len(all_items)}")
        return all_items
    
    def get_files_from_item(self, item: Dict) -> List[Dict]:
        """Get all files from a SharePoint item (file or folder from /drive/root/children)."""
        headers = {"Authorization": f"Bearer {self.access_token}"}
        if "file" in item:
            return [item]
        elif "folder" in item:
            # Recursively get all files in this folder
            files = []
            next_url = f"https://graph.microsoft.com/v1.0/sites/{self.site_id}/drive/items/{item['id']}/children?$top=999"
            while next_url:
                try:
                    response = requests.get(next_url, headers=headers)
                    response.raise_for_status()
                    data = response.json()
                    children = data.get("value", [])
                    for child in children:
                        if "file" in child:
                            files.append(child)
                        elif "folder" in child:
                            files.extend(self.get_files_from_item(child))
                    next_url = data.get("@odata.nextLink")
                except Exception as e:
                    logger.error(f"❌ Error walking folder {item.get('name', item.get('id', 'unknown'))}: {e}")
                    break
            return files
        else:
            return []
    
    def walk_folder_recursive(self, drive_id: str, folder_id: str, depth: int = 0) -> List[Dict]:
        """Recursively walk through folders to get all files."""
        if depth > 10:  # Prevent infinite recursion
            return []
        
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/items/{folder_id}/children?$top=999"
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            files = []
            children = response.json().get("value", [])
            
            for child in children:
                if "file" in child:
                    files.append(child)
                elif "folder" in child:
                    # Recursively get files from subfolder
                    sub_files = self.walk_folder_recursive(drive_id, child["id"], depth + 1)
                    files.extend(sub_files)
            
            return files
            
        except Exception as e:
            logger.error(f"❌ Error walking folder {folder_id}: {e}")
            return []
    
    def process_files_batch(self, files: List[Dict], batch_num: int) -> Dict:
        """Process a batch of files."""
        logger.info(f"🔄 Processing batch {batch_num} with {len(files)} files...")
        
        batch_results = {
            "batch_num": batch_num,
            "processed": 0,
            "failed": 0,
            "embeddings_created": 0,
            "files": []
        }
        
        for file_info in files:
            try:
                filename = file_info.get("name", "unknown")
                file_id = file_info.get("id", "unknown")
                download_url = file_info.get("@microsoft.graph.downloadUrl")
                
                if not download_url:
                    logger.warning(f"⚠️ No download URL for {filename}")
                    batch_results["failed"] += 1
                    continue
                
                # Check if already processed
                if file_id in self.progress["processed_items"]:
                    logger.info(f"✅ Already processed: {filename}")
                    continue
                
                # Download file
                local_path = self.download_dir / f"{uuid.uuid4()}_{filename}"
                
                try:
                    response = requests.get(download_url, timeout=60)
                    response.raise_for_status()
                    
                    with open(local_path, 'wb') as f:
                        f.write(response.content)
                    
                    logger.info(f"📥 Downloaded: {filename}")
                    
                except Exception as e:
                    logger.error(f"❌ Download failed for {filename}: {e}")
                    batch_results["failed"] += 1
                    continue
                
                # Process with OCR and text extraction
                try:
                    processed_file = self.doc_processor.process_file(str(local_path))

                    # If processed_file is a list, take the first element if available
                    if isinstance(processed_file, list) and processed_file:
                        processed_file_item = processed_file[0]
                    else:
                        processed_file_item = processed_file

                    # Check for processed_text in dict
                    has_text = False
                    if isinstance(processed_file_item, dict):
                        has_text = processed_file_item.get("processed_text")

                    if processed_file_item and has_text:
                        # Create embeddings
                        embedding_result = self.embedding_generator.create_embedding_for_file(
                            processed_file_item,
                            collection_name=self.progress["collection_name"]
                        )

                        # If embedding_result is a list, take the first element if available
                        if isinstance(embedding_result, list) and embedding_result:
                            embedding_result_item = embedding_result[0]
                        else:
                            embedding_result_item = embedding_result

                        chunks_created = 0
                        if isinstance(embedding_result_item, dict):
                            chunks_created = embedding_result_item.get("chunks_created", 0)

                        if embedding_result_item:
                            batch_results["embeddings_created"] += 1
                            batch_results["processed"] += 1

                            # Track progress
                            self.progress["processed_items"].append(file_id)
                            self.progress["total_files_processed"] += 1

                            batch_results["files"].append({
                                "filename": filename,
                                "file_id": file_id,
                                "status": "success",
                                "chunks": chunks_created
                            })

                            logger.info(f"✅ Processed and embedded: {filename}")
                        else:
                            logger.error(f"❌ Embedding creation failed for {filename}")
                            batch_results["failed"] += 1
                    else:
                        logger.error(f"❌ Text extraction failed for {filename}")
                        batch_results["failed"] += 1
                
                except Exception as e:
                    logger.error(f"❌ Processing failed for {filename}: {e}")
                    batch_results["failed"] += 1
                    self.progress["failed_items"].append({
                        "file_id": file_id,
                        "filename": filename,
                        "error": str(e)
                    })
                
                finally:
                    # Clean up downloaded file
                    if local_path.exists():
                        local_path.unlink()
                        
            except Exception as e:
                logger.error(f"❌ Unexpected error in batch processing: {e}")
                batch_results["failed"] += 1
        
        # Save progress after each batch
        self.progress["last_batch"] = batch_num
        self.save_progress()
        
        logger.info(f"📊 Batch {batch_num} complete: {batch_results['processed']} processed, "
                   f"{batch_results['failed']} failed, {batch_results['embeddings_created']} embeddings created")
        
        return batch_results
    
    def create_vector_collection(self):
        """Create or ensure vector collection exists."""
        try:
            collection_name = self.progress["collection_name"]
            
            # Check if collection exists
            try:
                collection_info = self.qdrant_client.get_collection(collection_name)
                logger.info(f"✅ Vector collection '{collection_name}' already exists with {collection_info.points_count} points")
            except:
                # Create collection if it doesn't exist
                self.qdrant_client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=384,  # sentence-transformers/all-MiniLM-L6-v2 dimension
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"✅ Created vector collection '{collection_name}'")
                
        except Exception as e:
            logger.error(f"❌ Failed to create vector collection: {e}")
            raise
    
    def process_all_documents(self, batch_size: int = 100, max_workers: int = 4):
        """Process all SharePoint documents."""
        logger.info("🚀 Starting bulk SharePoint document processing...")
        
        if not self.progress["start_time"]:
            self.progress["start_time"] = datetime.now().isoformat()
        
        # Create vector collection
        self.create_vector_collection()
        
        # Get all SharePoint items
        all_items = self.get_all_sharepoint_items()
        
        # Get all files from all items
        logger.info("📁 Discovering all files in SharePoint library...")
        all_files = []
        
        for i, item in enumerate(all_items):
            if i % 100 == 0:
                logger.info(f"🔍 Processed {i}/{len(all_items)} items, found {len(all_files)} files so far...")
            
            item_files = self.get_files_from_item(item)
            all_files.extend(item_files)
        
        logger.info(f"📊 Total files discovered: {len(all_files)}")
        self.progress["total_files_found"] = len(all_files)
        
        # Filter out already processed files
        remaining_files = [
            f for f in all_files 
            if f.get("id") not in self.progress["processed_items"]
        ]
        
        logger.info(f"📋 Files remaining to process: {len(remaining_files)}")
        
        # Process in batches
        total_batches = (len(remaining_files) + batch_size - 1) // batch_size
        
        for batch_num in range(self.progress["last_batch"], total_batches):
            start_idx = batch_num * batch_size
            end_idx = min(start_idx + batch_size, len(remaining_files))
            
            batch_files = remaining_files[start_idx:end_idx]
            
            logger.info(f"🔄 Processing batch {batch_num + 1}/{total_batches}")
            
            try:
                batch_result = self.process_files_batch(batch_files, batch_num + 1)
                
                # Log progress
                processed_count = self.progress["total_files_processed"]
                total_count = self.progress["total_files_found"]
                progress_pct = (processed_count / total_count * 100) if total_count > 0 else 0
                
                logger.info(f"📈 Overall progress: {processed_count}/{total_count} "
                           f"({progress_pct:.1f}%) files processed")
                
            except Exception as e:
                logger.error(f"❌ Batch {batch_num + 1} failed: {e}")
                continue
        
        # Final summary
        self.print_final_summary()
    
    def print_final_summary(self):
        """Print final processing summary."""
        logger.info("🎉 Bulk SharePoint processing complete!")
        logger.info("=" * 60)
        logger.info(f"📊 FINAL SUMMARY:")
        logger.info(f"   Total files found: {self.progress['total_files_found']}")
        logger.info(f"   Files processed: {self.progress['total_files_processed']}")
        logger.info(f"   Failed files: {len(self.progress['failed_items'])}")
        logger.info(f"   Collection name: {self.progress['collection_name']}")
        
        if self.progress["start_time"]:
            start_time = datetime.fromisoformat(self.progress["start_time"])
            duration = datetime.now() - start_time
            logger.info(f"   Total processing time: {duration}")
        
        logger.info("=" * 60)
        
        # Check collection status
        try:
            collection_info = self.qdrant_client.get_collection(self.progress["collection_name"])
            logger.info(f"📊 Vector collection '{self.progress['collection_name']}' "
                       f"contains {collection_info.points_count} embeddings")
        except Exception as e:
            logger.error(f"❌ Could not get collection info: {e}")

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Bulk process SharePoint documents for embeddings")
    parser.add_argument("--batch-size", type=int, default=50, 
                       help="Number of files to process per batch (default: 50)")
    parser.add_argument("--max-workers", type=int, default=2,
                       help="Maximum number of worker threads (default: 2)")
    parser.add_argument("--resume", action="store_true",
                       help="Resume from last checkpoint")
    
    args = parser.parse_args()
    
    try:
        processor = BulkSharePointProcessor()
        
        if args.resume:
            logger.info("🔄 Resuming from last checkpoint...")
        else:
            logger.info("🚀 Starting fresh bulk processing...")
        
        processor.process_all_documents(
            batch_size=args.batch_size,
            max_workers=args.max_workers
        )
        
    except KeyboardInterrupt:
        logger.info("⏹️ Processing interrupted by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        raise

if __name__ == "__main__":
    main()
