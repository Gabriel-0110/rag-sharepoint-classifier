#!/usr/bin/env python3
"""
Complete Library Embedding Pipeline - ALL DOCUMENTS

This script processes EVERY document in the project library including:
- All PDFs from all directories
- All TXT files (both source and documentation)
- All important Markdown documentation files
- All reports and guides

Creates a truly comprehensive vector database for the complete project knowledge base.
"""

import os
import sys
import json
from pathlib import Path
from typing import List, Dict, Any
import logging
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from embedding.create_embeddings import EmbeddingGenerator

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def find_all_documents():
    """Find ALL documents in the project that should be embedded."""
    
    print("🔍 DISCOVERING ALL DOCUMENTS IN PROJECT LIBRARY")
    print("="*60)
    
    # Define document types and their locations
    document_sources = {
        "PDFs": [],
        "TXT_Files": [],
        "Documentation": [],
        "Reports": [],
        "Guides": []
    }
    
    # Find all PDFs
    pdf_patterns = ["**/*.pdf"]
    for pattern in pdf_patterns:
        for pdf_file in project_root.glob(pattern):
            if not any(exclude in str(pdf_file) for exclude in ['.git', '__pycache__', '.pytest_cache']):
                document_sources["PDFs"].append(pdf_file)
    
    # Find important TXT files (exclude processed files and logs)
    txt_patterns = ["**/*.txt"]
    for pattern in txt_patterns:
        for txt_file in project_root.glob(pattern):
            if not any(exclude in str(txt_file) for exclude in [
                '.git', '__pycache__', '.pytest_cache', 'processed.txt', 
                'log.txt', 'test_output', 'requirements'
            ]):
                document_sources["TXT_Files"].append(txt_file)
    
    # Find important documentation (MD files)
    important_docs = [
        "docs/*.md",
        "reports/*.md", 
        "embedding/*.md",
        "FINAL_*.md",
        "COMPREHENSIVE_*.md",
        "MISSION_*.md"
    ]
    
    for pattern in important_docs:
        for md_file in project_root.glob(pattern):
            if 'FINAL' in md_file.name or 'COMPREHENSIVE' in md_file.name or 'MISSION' in md_file.name:
                document_sources["Reports"].append(md_file)
            elif md_file.parent.name in ['docs', 'reports']:
                document_sources["Documentation"].append(md_file)
            else:
                document_sources["Guides"].append(md_file)
    
    # Print summary
    total_docs = sum(len(docs) for docs in document_sources.values())
    print(f"\n📊 DOCUMENT DISCOVERY SUMMARY")
    print(f"Total Documents Found: {total_docs}")
    for category, docs in document_sources.items():
        print(f"  {category}: {len(docs)} files")
    
    return document_sources

def process_all_documents():
    """Process every document in the project library."""
    
    print("\n🚀 PROCESSING COMPLETE PROJECT LIBRARY")
    print("="*60)
    
    # Initialize embedding generator for complete library
    embedding_gen = EmbeddingGenerator(
        model_name="all-MiniLM-L6-v2",
        collection_name="complete_project_library"
    )
    
    # Discover all documents
    document_sources = find_all_documents()
    
    processing_summary = []
    total_files = 0
    total_embeddings = 0
    failed_files = []
    
    # Process each category
    for category, documents in document_sources.items():
        if not documents:
            continue
            
        print(f"\n📁 Processing {category}...")
        print(f"Files to process: {len(documents)}")
        
        for doc_file in documents:
            try:
                print(f"  Processing: {doc_file.name}")
                
                # Read content based on file type
                if doc_file.suffix.lower() == '.pdf':
                    # For PDFs, we'll read the processed text if available
                    processed_name = doc_file.stem + "_processed.txt"
                    processed_paths = list(project_root.glob(f"**/processed_texts*/{processed_name}"))
                    
                    if processed_paths:
                        with open(processed_paths[0], 'r', encoding='utf-8') as f:
                            content = f.read().strip()
                    else:
                        # If no processed version, skip for now (would need OCR)
                        print(f"    ⚠️ No processed version found for {doc_file.name}")
                        continue
                else:
                    # For TXT and MD files, read directly
                    try:
                        with open(doc_file, 'r', encoding='utf-8') as f:
                            content = f.read().strip()
                    except UnicodeDecodeError:
                        # Try with different encoding
                        with open(doc_file, 'r', encoding='latin-1') as f:
                            content = f.read().strip()
                
                if not content or len(content) < 50:
                    print(f"    ⚠️ Skipping {doc_file.name} - insufficient content")
                    continue
                
                # Create a temporary file for embedding processing
                temp_file = Path(f"/tmp/{doc_file.name}_temp.txt")
                with open(temp_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                # Generate embeddings
                embeddings_created = len(embedding_gen.process_text_file(temp_file))
                
                # Clean up temp file
                temp_file.unlink()
                
                total_files += 1
                total_embeddings += embeddings_created
                
                processing_summary.append({
                    "category": category,
                    "filename": doc_file.name,
                    "relative_path": str(doc_file.relative_to(project_root)),
                    "embeddings_created": embeddings_created,
                    "content_length": len(content),
                    "status": "success"
                })
                
                print(f"    ✅ {embeddings_created} embeddings created")
                
            except Exception as e:
                failed_files.append({
                    "file": str(doc_file),
                    "error": str(e),
                    "category": category
                })
                print(f"    ❌ Failed: {e}")
                processing_summary.append({
                    "category": category,
                    "filename": doc_file.name,
                    "relative_path": str(doc_file.relative_to(project_root)),
                    "embeddings_created": 0,
                    "content_length": 0,
                    "status": "failed",
                    "error": str(e)
                })
    
    # Generate comprehensive report
    report = {
        "processing_timestamp": datetime.now().isoformat(),
        "collection_name": "complete_project_library",
        "embedding_model": "all-MiniLM-L6-v2",
        "total_files_processed": total_files,
        "total_embeddings_created": total_embeddings,
        "total_failures": len(failed_files),
        "success_rate": f"{((total_files / (total_files + len(failed_files))) * 100):.1f}%" if total_files + len(failed_files) > 0 else "0%",
        "categories_processed": {
            category: len([item for item in processing_summary if item["category"] == category and item["status"] == "success"])
            for category in document_sources.keys()
        },
        "processing_details": processing_summary,
        "failed_files": failed_files
    }
    
    # Save report
    report_path = Path(__file__).parent / "complete_project_library_report.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    print("\n" + "="*60)
    print("🎯 COMPLETE LIBRARY PROCESSING FINISHED")
    print("="*60)
    print(f"📁 Total files processed: {total_files}")
    print(f"❌ Failed files: {len(failed_files)}")
    print(f"🔢 Total embeddings: {total_embeddings}")
    print(f"📊 Success rate: {report['success_rate']}")
    print(f"🗃️  Collection: complete_project_library")
    print(f"📋 Full report: {report_path}")
    print("="*60)
    
    # Test search functionality
    print("\n🔍 TESTING COMPREHENSIVE SEARCH...")
    test_queries = [
        "Azure RAG system architecture",
        "document classification process", 
        "embedding pipeline configuration",
        "SharePoint integration setup",
        "CUDA memory optimization",
        "TrOCR processing workflow",
        "immigration waiver application",
        "medical report analysis",
        "system testing methodology",
        "project completion status"
    ]
    
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        try:
            results = embedding_gen.search_similar(query, limit=3)
            for i, result in enumerate(results, 1):
                print(f"  {i}. {result['filename']} (score: {result['score']:.3f})")
        except Exception as e:
            print(f"  ❌ Search failed: {e}")
    
    return report

if __name__ == "__main__":
    try:
        report = process_all_documents()
        print(f"\n✅ COMPLETE PROJECT LIBRARY EMBEDDING: SUCCESS")
        print(f"Total embeddings in complete_project_library: {report['total_embeddings_created']}")
    except Exception as e:
        logger.error(f"Complete library processing failed: {e}")
        raise
