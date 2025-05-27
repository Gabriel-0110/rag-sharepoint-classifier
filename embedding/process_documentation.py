#!/usr/bin/env python3
"""
Process Documentation Files for Complete Library

This script processes all the important documentation files using our existing pipeline.
"""

import os
import sys
from pathlib import Path
import shutil

def main():
    print("📚 PROCESSING DOCUMENTATION FILES FOR COMPLETE LIBRARY")
    print("="*60)
    
    # Create a temporary directory for documentation processing
    docs_temp_dir = Path("/home/azureuser/rag_project/embedding/temp_docs_processing")
    docs_temp_dir.mkdir(exist_ok=True)
    
    # Important documentation files to process
    important_docs = [
        "/home/azureuser/rag_project/docs/CONFIGURATION_GUIDE.md",
        "/home/azureuser/rag_project/docs/PROJECT_STRUCTURE.md", 
        "/home/azureuser/rag_project/docs/IMPLEMENTATION_ANALYSIS.md",
        "/home/azureuser/rag_project/docs/FINAL_STATUS_REPORT.md",
        "/home/azureuser/rag_project/docs/3MODEL_ARCHITECTURE_COMPLETION_REPORT.md",
        "/home/azureuser/rag_project/reports/AUTOMATIC_STARTUP_GUIDE.md",
        "/home/azureuser/rag_project/reports/FINAL_STATUS_UPDATE_MAY26.md",
        "/home/azureuser/rag_project/reports/MISSION_ACCOMPLISHED_FINAL.md"
    ]
    
    processed_count = 0
    
    # Copy important docs to temp directory and convert to txt
    for doc_path in important_docs:
        if os.path.exists(doc_path):
            print(f"  Processing: {os.path.basename(doc_path)}")
            
            # Read the markdown file
            with open(doc_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Create a .txt version in temp directory
            txt_filename = os.path.basename(doc_path).replace('.md', '.txt')
            txt_path = docs_temp_dir / txt_filename
            
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            processed_count += 1
        else:
            print(f"  ⚠️ Not found: {doc_path}")
    
    print(f"\n✅ Prepared {processed_count} documentation files")
    print(f"📁 Files saved to: {docs_temp_dir}")
    
    # Now run our existing pipeline on this temp directory
    print("\n🚀 Running embedding pipeline on documentation...")
    
    # Use the existing pipeline script
    pipeline_cmd = f"""
cd /home/azureuser/rag_project/embedding && python run_embedding_pipeline.py \\
    --input_dir "{docs_temp_dir}" \\
    --output_dir "processed_texts_documentation" \\
    --collection_name "complete_project_library"
"""
    
    print("Command to run:")
    print(pipeline_cmd)
    
    return docs_temp_dir

if __name__ == "__main__":
    temp_dir = main()
    print(f"\nNext step: Run the embedding pipeline on {temp_dir}")
