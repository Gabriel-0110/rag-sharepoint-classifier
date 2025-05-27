#!/usr/bin/env python3
"""
Bulk Processing System Configuration
===================================

Configure the system for optimal large-scale SharePoint document processing.
Sets up environment, creates necessary directories, and optimizes settings.

Usage:
    python setup_bulk_processing.py
"""

import os
import sys
import json
import shutil
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from dotenv import load_dotenv

load_dotenv()

class BulkProcessingSetup:
    """Set up system for bulk processing."""
    
    def __init__(self):
        self.project_root = Path("/home/azureuser/rag_project")
        self.embedding_dir = self.project_root / "embedding"
        
        # Processing directories
        self.bulk_downloads = self.embedding_dir / "bulk_downloads"
        self.bulk_processed_texts = self.embedding_dir / "bulk_processed_texts"
        self.logs_dir = self.embedding_dir / "logs"
        self.snapshots_dir = self.embedding_dir / "snapshots"
        
        # Configuration files
        self.bulk_config_file = self.embedding_dir / "bulk_processing_config.json"
        
        # Initialize Qdrant client
        self.qdrant_client = QdrantClient(
            url=os.getenv("QDRANT_URL", "http://localhost:6333"),
            api_key=os.getenv("QDRANT_API_KEY")
        )
    
    def create_directories(self):
        """Create all necessary directories."""
        directories = [
            self.bulk_downloads,
            self.bulk_processed_texts,
            self.logs_dir,
            self.snapshots_dir
        ]
        
        print("📁 Creating processing directories...")
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            print(f"✅ Created: {directory}")
        
        # Set permissions for better performance
        for directory in directories:
            os.chmod(directory, 0o755)
    
    def create_bulk_config(self):
        """Create bulk processing configuration."""
        config = {
            "processing": {
                "batch_size": 50,
                "max_workers": 2,
                "chunk_size": 3000,
                "chunk_overlap": 200,
                "max_retries": 3,
                "retry_delay": 5,
                "timeout_seconds": 120
            },
            "memory_management": {
                "max_memory_usage_gb": 8,
                "cleanup_frequency": 100,
                "temp_file_cleanup": True,
                "gc_frequency": 50
            },
            "embedding": {
                "model_name": "sentence-transformers/all-MiniLM-L6-v2",
                "vector_size": 384,
                "distance_metric": "cosine",
                "collection_name": "sharepoint_complete_library"
            },
            "sharepoint": {
                "api_timeout": 60,
                "download_timeout": 120,
                "max_file_size_mb": 100,
                "supported_extensions": [
                    ".pdf", ".docx", ".doc", ".txt", ".rtf",
                    ".png", ".jpg", ".jpeg", ".tiff", ".bmp"
                ]
            },
            "logging": {
                "level": "INFO",
                "max_log_size_mb": 100,
                "backup_count": 5,
                "detailed_progress": True
            },
            "performance": {
                "use_gpu": True,
                "gpu_memory_fraction": 0.7,
                "parallel_ocr": True,
                "cache_embeddings": True
            }
        }
        
        with open(self.bulk_config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"⚙️  Created bulk processing config: {self.bulk_config_file}")
        return config
    
    def setup_vector_collection(self):
        """Set up the main vector collection for bulk processing."""
        collection_name = "sharepoint_complete_library"
        
        try:
            # Check if collection exists
            try:
                collection_info = self.qdrant_client.get_collection(collection_name)
                print(f"✅ Vector collection '{collection_name}' already exists with {collection_info.points_count} points")
                return True
            except:
                pass
            
            # Create collection
            self.qdrant_client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=384,  # sentence-transformers/all-MiniLM-L6-v2
                    distance=Distance.COSINE
                )
            )
            
            print(f"✅ Created vector collection '{collection_name}'")
            return True
            
        except Exception as e:
            print(f"❌ Failed to setup vector collection: {e}")
            return False
    
    def optimize_system_settings(self):
        """Apply system optimizations for bulk processing."""
        print("🔧 Applying system optimizations...")
        
        # Create system optimization script
        optimization_script = self.embedding_dir / "optimize_for_bulk.sh"
        
        script_content = """#!/bin/bash
# System optimizations for bulk document processing

echo "🔧 Optimizing system for bulk processing..."

# Increase file descriptor limits
echo "fs.file-max = 2097152" | sudo tee -a /etc/sysctl.conf
echo "* soft nofile 65536" | sudo tee -a /etc/security/limits.conf
echo "* hard nofile 65536" | sudo tee -a /etc/security/limits.conf

# Optimize memory settings
echo "vm.swappiness = 10" | sudo tee -a /etc/sysctl.conf
echo "vm.dirty_ratio = 15" | sudo tee -a /etc/sysctl.conf
echo "vm.dirty_background_ratio = 5" | sudo tee -a /etc/sysctl.conf

# Apply settings
sudo sysctl -p

# Create swap file if needed (for large processing jobs)
if [ ! -f /swapfile ]; then
    echo "💾 Creating 8GB swap file..."
    sudo fallocate -l 8G /swapfile
    sudo chmod 600 /swapfile
    sudo mkswap /swapfile
    sudo swapon /swapfile
    echo "/swapfile none swap sw 0 0" | sudo tee -a /etc/fstab
fi

# GPU optimizations
if command -v nvidia-smi &> /dev/null; then
    echo "🚀 Applying GPU optimizations..."
    sudo nvidia-smi -pm 1  # Enable persistence mode
    sudo nvidia-smi -acp 0  # Set application clock policy
fi

echo "✅ System optimizations applied"
"""
        
        with open(optimization_script, 'w') as f:
            f.write(script_content)
        
        os.chmod(optimization_script, 0o755)
        print(f"✅ Created optimization script: {optimization_script}")
    
    def create_monitoring_script(self):
        """Create a monitoring script for the bulk process."""
        monitoring_script = self.embedding_dir / "monitor_bulk_process.sh"
        
        script_content = """#!/bin/bash
# Monitor bulk processing

echo "👀 Bulk Processing Monitor"
echo "========================="

# Show system resources
echo "💻 System Resources:"
echo "CPU Usage: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | awk -F'%' '{print $1}')%"
echo "Memory: $(free -h | awk 'NR==2{printf "%.1f/%.1f GB (%.1f%%)", $3/1024/1024, $2/1024/1024, $3*100/$2}')"
echo "Disk: $(df -h /home | awk 'NR==2{printf "%s/%s (%s)", $3, $2, $5}')"

if command -v nvidia-smi &> /dev/null; then
    echo "GPU: $(nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total --format=csv,noheader,nounits | awk -F', ' '{printf "%.0f%% GPU, %.1f/%.1f GB", $1, $2/1024, $3/1024}')"
fi

echo ""

# Show processing status
if [ -f "/home/azureuser/rag_project/embedding/bulk_progress.json" ]; then
    echo "📊 Processing Status:"
    python3 /home/azureuser/rag_project/embedding/bulk_processing_monitor.py --status
else
    echo "⚠️  No bulk processing in progress"
fi

echo ""
echo "🔄 To start monitoring in real-time: python3 bulk_processing_monitor.py --watch"
echo "📝 To follow logs: python3 bulk_processing_monitor.py --tail"
"""
        
        with open(monitoring_script, 'w') as f:
            f.write(script_content)
        
        os.chmod(monitoring_script, 0o755)
        print(f"✅ Created monitoring script: {monitoring_script}")
    
    def check_dependencies(self):
        """Check if all required dependencies are available."""
        print("🔍 Checking dependencies...")
        
        required_packages = [
            "qdrant_client",
            "sentence_transformers",
            "transformers",
            "torch",
            "PIL",
            "pytesseract",
            "pdf2image",
            "python-docx",
            "requests",
            "msal"
        ]
        
        missing_packages = []
        
        for package in required_packages:
            try:
                __import__(package.replace("-", "_"))
                print(f"✅ {package}")
            except ImportError:
                missing_packages.append(package)
                print(f"❌ {package}")
        
        if missing_packages:
            print(f"\n⚠️  Missing packages: {', '.join(missing_packages)}")
            print("Install with: pip install " + " ".join(missing_packages))
            return False
        
        print("✅ All dependencies available")
        return True
    
    def create_quick_start_guide(self):
        """Create a quick start guide for bulk processing."""
        guide_file = self.embedding_dir / "BULK_PROCESSING_GUIDE.md"
        
        guide_content = """# Bulk SharePoint Processing Guide

## 🚀 Quick Start

### 1. Start Bulk Processing
```bash
# Start processing all SharePoint documents
python3 embedding/bulk_sharepoint_processor.py --batch-size 50

# Resume from last checkpoint
python3 embedding/bulk_sharepoint_processor.py --resume --batch-size 100
```

### 2. Monitor Progress
```bash
# Check current status
python3 embedding/bulk_processing_monitor.py --status

# Watch in real-time
python3 embedding/bulk_processing_monitor.py --watch

# Follow logs
python3 embedding/bulk_processing_monitor.py --tail
```

### 3. System Monitoring
```bash
# Run system monitor
./embedding/monitor_bulk_process.sh

# Apply system optimizations (run once)
./embedding/optimize_for_bulk.sh
```

## 📊 Processing Overview

The bulk processor will:
1. **Discover** all files in SharePoint "Case Management" library
2. **Download** files in batches (configurable batch size)
3. **Extract** text using OCR (TrOCR → Tesseract → PyPDF2 fallback)
4. **Generate** embeddings using sentence-transformers
5. **Store** in Qdrant vector database collection
6. **Track** progress with resumable checkpoints

## ⚙️ Configuration

Edit `embedding/bulk_processing_config.json` to adjust:
- Batch size (default: 50 files per batch)
- Worker threads (default: 2)
- Memory limits and cleanup frequency
- Timeout settings
- Performance optimizations

## 🔧 Troubleshooting

### If Processing Stalls
```bash
# Check status
python3 embedding/bulk_processing_monitor.py --status

# Clean up and restart
python3 embedding/bulk_processing_monitor.py --cleanup
python3 embedding/bulk_sharepoint_processor.py --resume
```

### Memory Issues
```bash
# Apply system optimizations
./embedding/optimize_for_bulk.sh

# Reduce batch size
python3 embedding/bulk_sharepoint_processor.py --batch-size 25
```

### Check Collection Status
```bash
# Check Qdrant collection
curl http://localhost:6333/collections/sharepoint_complete_library
```

## 📈 Expected Performance

- **Processing Speed**: ~2-5 files per minute (depending on file size/complexity)
- **Total Time**: 70-170 hours for 20,000 files
- **Memory Usage**: 4-8 GB RAM
- **Disk Space**: ~10-50 GB temporary storage
- **Vector Database**: ~1-5 GB final collection size

## 🎯 Final Result

After completion, you'll have:
- Complete vector database with all 20,000+ documents
- Semantic search capabilities across entire library
- RAG-ready document corpus
- Full audit trail and processing logs
"""
        
        with open(guide_file, 'w') as f:
            f.write(guide_content)
        
        print(f"✅ Created quick start guide: {guide_file}")
    
    def run_setup(self):
        """Run complete setup process."""
        print("🚀 Setting up bulk SharePoint processing system...")
        print("=" * 60)
        
        # Check dependencies
        if not self.check_dependencies():
            print("❌ Please install missing dependencies before continuing")
            return False
        
        # Create directories
        self.create_directories()
        
        # Create configuration
        config = self.create_bulk_config()
        
        # Setup vector collection
        if not self.setup_vector_collection():
            print("❌ Failed to setup vector collection")
            return False
        
        # Create optimization scripts
        self.optimize_system_settings()
        self.create_monitoring_script()
        
        # Create documentation
        self.create_quick_start_guide()
        
        print("=" * 60)
        print("✅ Bulk processing setup complete!")
        print("")
        print("🎯 Next Steps:")
        print("1. Run system optimizations: ./embedding/optimize_for_bulk.sh")
        print("2. Start bulk processing: python3 embedding/bulk_sharepoint_processor.py")
        print("3. Monitor progress: python3 embedding/bulk_processing_monitor.py --watch")
        print("")
        print("📖 See BULK_PROCESSING_GUIDE.md for detailed instructions")
        
        return True

def main():
    """Main entry point."""
    setup = BulkProcessingSetup()
    setup.run_setup()

if __name__ == "__main__":
    main()
