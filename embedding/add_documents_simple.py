#!/usr/bin/env python3
"""
Simple script to add missing documents to vector database
"""

import sys
import os
from pathlib import Path
import requests

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def main():
    print("🔍 SIMPLE DOCUMENT ADDITION TEST")
    print("="*50)
    
    # Check current collection status
    try:
        response = requests.get("http://localhost:6333/collections/complete_project_library")
        if response.status_code == 200:
            data = response.json()
            current_count = data["result"]["points_count"]
            print(f"📊 Current embeddings in collection: {current_count}")
        else:
            print(f"❌ Cannot access collection: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Error accessing Qdrant: {e}")
        return
    
    # Find markdown files
    docs_dir = project_root / "docs"
    print(f"\n📁 Checking docs directory: {docs_dir}")
    
    if not docs_dir.exists():
        print("❌ Docs directory does not exist")
        return
    
    md_files = list(docs_dir.glob("*.md"))
    print(f"📄 Found {len(md_files)} markdown files:")
    
    for md_file in md_files[:5]:  # Show first 5
        file_size = md_file.stat().st_size
        print(f"  - {md_file.name} ({file_size} bytes)")
    
    # Try to import and use the embedding generator
    print(f"\n🔧 Testing import...")
    try:
        from create_embeddings import EmbeddingGenerator
        print("✅ Import successful")
        
        # Initialize
        embedding_gen = EmbeddingGenerator(
            model_name="all-MiniLM-L6-v2",
            collection_name="complete_project_library"
        )
        print("✅ EmbeddingGenerator initialized")
        
        # Process one test file
        if md_files:
            test_file = md_files[0]
            print(f"\n🧪 Testing with file: {test_file.name}")
            
            with open(test_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            print(f"📄 File size: {len(content)} characters")
            
            if len(content) > 100:
                # Create temp file
                temp_file = Path(f"/tmp/test_embed_{test_file.stem}.txt")
                with open(temp_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print("🔄 Processing with embedding generator...")
                try:
                    result = embedding_gen.process_text_file(temp_file)
                    print(f"✅ Created {len(result)} embeddings")
                    temp_file.unlink()  # Clean up
                except Exception as e:
                    print(f"❌ Processing failed: {e}")
                    if temp_file.exists():
                        temp_file.unlink()
            else:
                print("⚠️ File too short to process")
        
    except Exception as e:
        print(f"❌ Import or processing failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Final status check
    try:
        response = requests.get("http://localhost:6333/collections/complete_project_library")
        if response.status_code == 200:
            data = response.json()
            final_count = data["result"]["points_count"]
            print(f"\n📊 Final embeddings in collection: {final_count}")
            if final_count > current_count:
                print(f"🎯 Added {final_count - current_count} new embeddings")
        else:
            print(f"❌ Cannot verify final status: {response.status_code}")
    except Exception as e:
        print(f"❌ Error checking final status: {e}")

if __name__ == "__main__":
    main()
