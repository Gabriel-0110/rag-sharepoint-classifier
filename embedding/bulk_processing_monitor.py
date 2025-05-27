#!/usr/bin/env python3
"""
Bulk Processing Monitor and Management Tool
===========================================

Monitor and manage the bulk SharePoint processing operation.
Provides real-time status, progress tracking, and management capabilities.

Usage:
    python bulk_processing_monitor.py --status
    python bulk_processing_monitor.py --restart
    python bulk_processing_monitor.py --cleanup
"""

import os
import sys
import json
import time
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from qdrant_client import QdrantClient
from dotenv import load_dotenv

load_dotenv()

class BulkProcessingMonitor:
    """Monitor and manage bulk SharePoint processing."""
    
    def __init__(self):
        self.progress_file = Path("/home/azureuser/rag_project/embedding/bulk_progress.json")
        self.log_file = Path("/home/azureuser/rag_project/embedding/logs/bulk_sharepoint_processing.log")
        self.download_dir = Path("/home/azureuser/rag_project/embedding/bulk_downloads")
        self.processed_texts_dir = Path("/home/azureuser/rag_project/embedding/bulk_processed_texts")
        
        # Initialize Qdrant client
        self.qdrant_client = QdrantClient(
            url=os.getenv("QDRANT_URL", "http://localhost:6333"),
            api_key=os.getenv("QDRANT_API_KEY")
        )
    
    def load_progress(self) -> Dict:
        """Load current progress."""
        if self.progress_file.exists():
            with open(self.progress_file, 'r') as f:
                return json.load(f)
        return {}
    
    def get_collection_stats(self, collection_name: str) -> Dict:
        """Get vector collection statistics."""
        try:
            collection_info = self.qdrant_client.get_collection(collection_name)
            return {
                "exists": True,
                "points_count": collection_info.points_count,
                "vectors_count": collection_info.vectors_count,
                "status": collection_info.status
            }
        except Exception as e:
            return {
                "exists": False,
                "error": str(e)
            }
    
    def get_processing_status(self) -> Dict:
        """Get comprehensive processing status."""
        progress = self.load_progress()
        
        if not progress:
            return {"status": "not_started", "message": "No processing has been started yet"}
        
        # Calculate progress metrics
        total_found = progress.get("total_files_found", 0)
        total_processed = progress.get("total_files_processed", 0)
        total_failed = len(progress.get("failed_items", []))
        
        progress_pct = (total_processed / total_found * 100) if total_found > 0 else 0
        
        # Get collection stats
        collection_name = progress.get("collection_name", "complete_project_library")
        collection_stats = self.get_collection_stats(collection_name)
        
        # Calculate time metrics
        start_time = progress.get("start_time")
        last_update = progress.get("last_update")
        
        time_metrics = {}
        if start_time:
            start_dt = datetime.fromisoformat(start_time)
            elapsed = datetime.now() - start_dt
            time_metrics["elapsed_time"] = str(elapsed)
            
            if total_processed > 0:
                avg_time_per_file = elapsed.total_seconds() / total_processed
                remaining_files = total_found - total_processed
                estimated_remaining = timedelta(seconds=avg_time_per_file * remaining_files)
                time_metrics["estimated_remaining"] = str(estimated_remaining)
                time_metrics["avg_time_per_file"] = f"{avg_time_per_file:.2f} seconds"
        
        if last_update:
            last_update_dt = datetime.fromisoformat(last_update)
            time_since_update = datetime.now() - last_update_dt
            time_metrics["time_since_last_update"] = str(time_since_update)
        
        # Determine status
        if progress_pct >= 100:
            status = "completed"
        elif time_metrics.get("time_since_last_update") and \
             isinstance(last_update, str) and \
             datetime.fromisoformat(last_update) < datetime.now() - timedelta(minutes=30):
            status = "stalled"
        else:
            status = "in_progress"
        
        return {
            "status": status,
            "progress": {
                "total_files_found": total_found,
                "files_processed": total_processed,
                "files_failed": total_failed,
                "progress_percentage": round(progress_pct, 2),
                "last_batch": progress.get("last_batch", 0)
            },
            "collection": {
                "name": collection_name,
                **collection_stats
            },
            "timing": time_metrics,
            "disk_usage": self.get_disk_usage()
        }
    
    def get_disk_usage(self) -> Dict:
        """Get disk usage information."""
        try:
            # Get download directory size
            download_size = sum(f.stat().st_size for f in self.download_dir.rglob('*') if f.is_file())
            
            # Get processed texts directory size
            texts_size = sum(f.stat().st_size for f in self.processed_texts_dir.rglob('*') if f.is_file())
            
            # Get log file size
            log_size = self.log_file.stat().st_size if self.log_file.exists() else 0
            
            return {
                "download_dir_mb": round(download_size / (1024 * 1024), 2),
                "processed_texts_mb": round(texts_size / (1024 * 1024), 2),
                "log_file_mb": round(log_size / (1024 * 1024), 2)
            }
        except Exception as e:
            return {"error": str(e)}
    
    def print_status(self):
        """Print comprehensive status report."""
        status = self.get_processing_status()
        
        print("=" * 70)
        print("🔍 BULK SHAREPOINT PROCESSING STATUS")
        print("=" * 70)
        
        print(f"📊 Status: {status['status'].upper()}")
        
        if 'progress' in status:
            progress = status['progress']
            print(f"📈 Progress: {progress['files_processed']}/{progress['total_files_found']} "
                  f"({progress['progress_percentage']}%)")
            print(f"❌ Failed: {progress['files_failed']} files")
            print(f"📦 Last Batch: {progress['last_batch']}")
        
        if 'collection' in status:
            collection = status['collection']
            print(f"🗃️  Collection: {collection['name']}")
            if collection.get('exists'):
                print(f"   Embeddings: {collection.get('points_count', 'unknown')}")
                print(f"   Status: {collection.get('status', 'unknown')}")
            else:
                print(f"   ❌ Collection not found or error: {collection.get('error', 'unknown')}")
        
        if 'timing' in status and status['timing']:
            timing = status['timing']
            print(f"⏱️  Timing:")
            if 'elapsed_time' in timing:
                print(f"   Elapsed: {timing['elapsed_time']}")
            if 'estimated_remaining' in timing:
                print(f"   Estimated remaining: {timing['estimated_remaining']}")
            if 'avg_time_per_file' in timing:
                print(f"   Avg per file: {timing['avg_time_per_file']}")
            if 'time_since_last_update' in timing:
                print(f"   Last update: {timing['time_since_last_update']} ago")
        
        if 'disk_usage' in status:
            disk = status['disk_usage']
            if 'error' not in disk:
                print(f"💾 Disk Usage:")
                print(f"   Downloads: {disk.get('download_dir_mb', 0)} MB")
                print(f"   Processed texts: {disk.get('processed_texts_mb', 0)} MB")
                print(f"   Log file: {disk.get('log_file_mb', 0)} MB")
        
        print("=" * 70)
        
        # Show recent log entries
        self.show_recent_log_entries()
    
    def show_recent_log_entries(self, lines: int = 10):
        """Show recent log entries."""
        if not self.log_file.exists():
            print("📝 No log file found")
            return
        
        try:
            print(f"📝 Recent Log Entries (last {lines} lines):")
            print("-" * 50)
            
            with open(self.log_file, 'r') as f:
                all_lines = f.readlines()
                recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
                
                for line in recent_lines:
                    print(line.rstrip())
                    
        except Exception as e:
            print(f"❌ Error reading log file: {e}")
    
    def cleanup_temp_files(self):
        """Clean up temporary files."""
        print("🧹 Cleaning up temporary files...")
        
        # Clean download directory
        if self.download_dir.exists():
            count = 0
            for file in self.download_dir.rglob('*'):
                if file.is_file():
                    try:
                        file.unlink()
                        count += 1
                    except Exception as e:
                        print(f"❌ Failed to delete {file}: {e}")
            print(f"✅ Deleted {count} temporary download files")
        
        # Optionally clean processed texts (ask for confirmation)
        if self.processed_texts_dir.exists():
            response = input("🗑️  Delete processed text files? (y/N): ").lower()
            if response == 'y':
                count = 0
                for file in self.processed_texts_dir.rglob('*'):
                    if file.is_file():
                        try:
                            file.unlink()
                            count += 1
                        except Exception as e:
                            print(f"❌ Failed to delete {file}: {e}")
                print(f"✅ Deleted {count} processed text files")
    
    def reset_progress(self):
        """Reset processing progress."""
        response = input("⚠️  This will reset all progress. Are you sure? (y/N): ").lower()
        if response == 'y':
            if self.progress_file.exists():
                self.progress_file.unlink()
                print("✅ Progress file deleted")
            
            # Optionally delete collection
            progress = self.load_progress()
            collection_name = progress.get("collection_name", "complete_project_library")
            
            response = input(f"🗃️  Delete vector collection '{collection_name}'? (y/N): ").lower()
            if response == 'y':
                try:
                    self.qdrant_client.delete_collection(collection_name)
                    print(f"✅ Collection '{collection_name}' deleted")
                except Exception as e:
                    print(f"❌ Failed to delete collection: {e}")
            
            print("🔄 Processing reset complete")
    
    def tail_log(self, lines: int = 50):
        """Follow log file in real-time."""
        if not self.log_file.exists():
            print("📝 No log file found")
            return
        
        print(f"📝 Following log file (press Ctrl+C to stop)...")
        print("-" * 50)
        
        try:
            # Show last N lines first
            with open(self.log_file, 'r') as f:
                all_lines = f.readlines()
                recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
                
                for line in recent_lines:
                    print(line.rstrip())
            
            # Follow new lines
            with open(self.log_file, 'r') as f:
                f.seek(0, 2)  # Go to end of file
                
                while True:
                    line = f.readline()
                    if line:
                        print(line.rstrip())
                    else:
                        time.sleep(1)
                        
        except KeyboardInterrupt:
            print("\n👋 Stopped following log")
        except Exception as e:
            print(f"❌ Error following log: {e}")

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Monitor bulk SharePoint processing")
    parser.add_argument("--status", action="store_true", help="Show processing status")
    parser.add_argument("--cleanup", action="store_true", help="Clean up temporary files")
    parser.add_argument("--reset", action="store_true", help="Reset processing progress")
    parser.add_argument("--tail", type=int, nargs='?', const=50, 
                       help="Follow log file (default: 50 lines)")
    parser.add_argument("--watch", action="store_true", help="Watch status in real-time")
    
    args = parser.parse_args()
    
    monitor = BulkProcessingMonitor()
    
    if args.status or (not any([args.cleanup, args.reset, args.tail, args.watch])):
        monitor.print_status()
    
    if args.cleanup:
        monitor.cleanup_temp_files()
    
    if args.reset:
        monitor.reset_progress()
    
    if args.tail is not None:
        monitor.tail_log(args.tail)
    
    if args.watch:
        print("👀 Watching status (press Ctrl+C to stop)...")
        try:
            while True:
                os.system('clear')  # Clear screen
                monitor.print_status()
                time.sleep(30)  # Update every 30 seconds
        except KeyboardInterrupt:
            print("\n👋 Stopped watching")

if __name__ == "__main__":
    main()
