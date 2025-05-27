#!/usr/bin/env python3
"""
Add All Missing Documents to Vector Database

This script adds all the documents we missed in the initial processing.
"""

import sys
import os
from pathlib import Path
import subprocess

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from create_embeddings import EmbeddingGenerator

def process_missing_documents():
    """Process all the documents we haven't embedded yet."""
    
    print("🔍 ADDING ALL MISSING DOCUMENTS TO VECTOR DATABASE")
    print("="*70)
    
    # Initialize embedding generator
    embedding_gen = EmbeddingGenerator(
        model_name="all-MiniLM-L6-v2",
        collection_name="complete_project_library"
    )
    
    total_added = 0
    
    # 1. Add all documentation markdown files
    print("\n📚 Processing Documentation Files...")
    docs_dir = project_root / "docs"
    reports_dir = project_root / "reports"
    
    md_files = []
    if docs_dir.exists():
        md_files.extend(list(docs_dir.glob("*.md")))
    if reports_dir.exists():
        md_files.extend(list(reports_dir.glob("*.md")))
    
    for md_file in md_files:
        try:
            print(f"  Processing: {md_file.name}")
            
            # Read the markdown file
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if len(content) > 100:  # Only process files with substantial content
                # Create temporary text file
                temp_file = Path(f"/tmp/{md_file.stem}_temp.txt")
                with open(temp_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                # Process with embedding generator
                embeddings_created = len(embedding_gen.process_text_file(temp_file))
                temp_file.unlink()  # Clean up
                
                total_added += embeddings_created
                print(f"    ✅ Added {embeddings_created} embeddings")
            else:
                print(f"    ⚠️ Skipped - too short")
                
        except Exception as e:
            print(f"    ❌ Failed: {e}")
    
    # 2. Add the main Azure RAG PDF (from docs/)
    print("\n📄 Processing Azure RAG Documentation PDF...")
    azure_pdf = project_root / "docs" / "Open-Source RAG Document Classification System on Azure.pdf"
    if azure_pdf.exists():
        # Check if we have a processed version
        processed_files = list(project_root.glob("**/processed_texts*/*Azure*processed.txt"))
        if processed_files:
            try:
                with open(processed_files[0], 'r', encoding='utf-8') as f:
                    content = f.read()
                
                temp_file = Path("/tmp/azure_rag_doc_temp.txt")
                with open(temp_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                embeddings_created = len(embedding_gen.process_text_file(temp_file))
                temp_file.unlink()
                
                total_added += embeddings_created
                print(f"  ✅ Azure RAG PDF: {embeddings_created} embeddings added")
            except Exception as e:
                print(f"  ❌ Failed to process Azure PDF: {e}")
    
    # 3. Add important configuration and text files
    print("\n⚙️ Processing Configuration Files...")
    config_files = [
        project_root / "docs" / "CONFIGURATION_TEMPLATE.txt"
    ]
    
    for config_file in config_files:
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if len(content) > 50:
                    temp_file = Path(f"/tmp/{config_file.stem}_temp.txt")
                    with open(temp_file, 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    embeddings_created = len(embedding_gen.process_text_file(temp_file))
                    temp_file.unlink()
                    
                    total_added += embeddings_created
                    print(f"  ✅ {config_file.name}: {embeddings_created} embeddings")
            except Exception as e:
                print(f"  ❌ Failed {config_file.name}: {e}")
    
    print("\n" + "="*70)
    print("🎯 ADDITIONAL DOCUMENTS PROCESSING COMPLETE")
    print("="*70)
    print(f"📊 New embeddings added: {total_added}")
    
    # Check final collection status
    try:
        import requests
        response = requests.get("http://localhost:6333/collections/complete_project_library")
        if response.status_code == 200:
            data = response.json()
            total_points = data["result"]["points_count"]
            print(f"🗃️  Total embeddings in complete_project_library: {total_points}")
        else:
            print("❌ Could not verify collection status")
    except Exception as e:
        print(f"❌ Error checking collection: {e}")
    
    return total_added

if __name__ == "__main__":
    try:
        added = process_missing_documents()
        print(f"\n✅ SUCCESS: Added {added} new embeddings to complete project library")
    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        sys.exit(1)
