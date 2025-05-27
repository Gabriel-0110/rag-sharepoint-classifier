#!/usr/bin/env python3
"""
Create Unified Document Library Collection

This script consolidates all processed documents from different directories
into a single comprehensive vector database collection for the complete document library.
"""

import os
import sys
import json
from pathlib import Path
from typing import List, Dict, Any
import logging

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from create_embeddings import EmbeddingGenerator

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def consolidate_document_library():
    """Consolidate all processed documents into a unified collection."""
    
    print("🚀 CONSOLIDATING COMPLETE DOCUMENT LIBRARY")
    print("="*60)
    
    # Define source directories
    source_dirs = [
        "processed_texts_test_batch",
        "processed_texts_sp_batch", 
        "processed_texts_data_docs",
        "processed_texts_docs"
    ]
    
    # Initialize embedding generator
    embedding_gen = EmbeddingGenerator(
        model_name="all-MiniLM-L6-v2",
        collection_name="complete_document_library"
    )
    
    total_files = 0
    total_embeddings = 0
    processing_summary = []
    
    for source_dir in source_dirs:
        source_path = Path(__file__).parent / source_dir
        
        if not source_path.exists():
            logger.warning(f"Directory not found: {source_path}")
            continue
            
        logger.info(f"📁 Processing directory: {source_dir}")
        
        # Get all text files in the directory
        text_files = list(source_path.glob("*_processed.txt"))
        
        if not text_files:
            logger.warning(f"No processed text files found in {source_dir}")
            continue
            
        logger.info(f"Found {len(text_files)} processed text files")
        
        # Process each file
        for text_file in text_files:
            try:
                # Read the processed text
                with open(text_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                
                if not content:
                    logger.warning(f"Empty file: {text_file.name}")
                    continue
                
                # Generate embeddings for this document
                embeddings_created = len(embedding_gen.process_text_file(text_file))
                
                total_files += 1
                total_embeddings += embeddings_created
                
                processing_summary.append({
                    "source_directory": source_dir,
                    "filename": text_file.name,
                    "embeddings_created": embeddings_created,
                    "content_length": len(content)
                })
                
                logger.info(f"✅ {text_file.name}: {embeddings_created} embeddings")
                
            except Exception as e:
                logger.error(f"Failed to process {text_file.name}: {e}")
    
    # Save consolidation report
    import datetime
    report = {
        "consolidation_timestamp": datetime.datetime.fromtimestamp(embedding_gen.stats()["start_time"]).isoformat(),
        "total_files_processed": total_files,
        "total_embeddings_created": total_embeddings,
        "source_directories": source_dirs,
        "collection_name": "complete_document_library",
        "embedding_model": "all-MiniLM-L6-v2",
        "processing_details": processing_summary
    }
    
    report_path = Path(__file__).parent / "complete_library_consolidation_report.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    print("\n" + "="*60)
    print("🎯 CONSOLIDATION COMPLETE")
    print("="*60)
    print(f"📁 Total files processed: {total_files}")
    print(f"🔢 Total embeddings: {total_embeddings}")
    print(f"🗃️  Collection: complete_document_library") 
    print(f"📋 Report saved: {report_path}")
    print("="*60)
    
    # Test the unified collection
    logger.info("🔍 Testing unified document library search...")
    
    test_queries = [
        "medical report",
        "immigration waiver", 
        "criminal charges",
        "court document",
        "affidavit",
        "Azure RAG system",
        "contract agreement"
    ]
    
    for query in test_queries:
        logger.info(f"\nQuery: '{query}'")
        results = embedding_gen.search_similar(query, limit=3)
        for i, result in enumerate(results, 1):
            logger.info(f"  {i}. {result['filename']} (score: {result['score']:.3f})")
    
    return report

if __name__ == "__main__":
    try:
        consolidate_document_library()
    except Exception as e:
        logger.error(f"Consolidation failed: {e}")
        raise
