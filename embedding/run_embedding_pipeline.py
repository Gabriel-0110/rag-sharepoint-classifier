#!/usr/bin/env python3
"""
Complete Embedding Pipeline Script

This script runs the complete pipeline:
1. Downloads files (optional)
2. Processes files with OCR
3. Generates embeddings
4. Tests the search functionality

Usage:
    python run_embedding_pipeline.py --help
    python run_embedding_pipeline.py --full-pipeline
    python run_embedding_pipeline.py --ocr-only
    python run_embedding_pipeline.py --embeddings-only
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import our scripts
from embedding.download_and_process import DocumentDownloadProcessor
from embedding.create_embeddings import EmbeddingGenerator, test_embedding_search

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_ocr_processing(input_dir: str, output_dir: str, enable_trocr: bool = True) -> dict:
    """Run OCR processing step."""
    logger.info("🔄 STEP 1: OCR Processing")
    logger.info("="*50)
    
    processor = DocumentDownloadProcessor(
        output_dir=output_dir,
        enable_trocr=enable_trocr
    )
    
    summary = processor.process_directory(input_dir)
    
    logger.info(f"✅ OCR processing complete: {summary['successful']}/{summary['total_files']} files")
    return summary

def run_embedding_generation(input_dir: str, model_name: str, collection_name: str) -> dict:
    """Run embedding generation step."""
    logger.info("\n🔄 STEP 2: Embedding Generation")
    logger.info("="*50)
    
    generator = EmbeddingGenerator(
        model_name=model_name,
        collection_name=collection_name
    )
    
    summary = generator.process_directory(Path(input_dir))
    logger.info(f"✅ Embedding generation complete: {summary['total_embeddings']} embeddings created")
    # Return only the summary dict
    return summary

def run_search_tests(generator: EmbeddingGenerator):
    """Run search functionality tests."""
    logger.info("\n🔄 STEP 3: Search Testing")
    logger.info("="*50)
    
    test_embedding_search(generator)
    logger.info("✅ Search tests complete")

def main():
    """Main pipeline execution."""
    parser = argparse.ArgumentParser(description="Complete embedding pipeline")
    
    # Pipeline options
    parser.add_argument("--full-pipeline", action="store_true",
                       help="Run complete pipeline (OCR + Embeddings + Tests)")
    parser.add_argument("--ocr-only", action="store_true",
                       help="Run only OCR processing")
    parser.add_argument("--embeddings-only", action="store_true",
                       help="Run only embedding generation")
    
    # Input/Output directories
    parser.add_argument("--input-dir", 
                       default="/home/azureuser/rag_project/test_batch_downloads",
                       help="Input directory with source files")
    parser.add_argument("--processed-dir",
                       default="/home/azureuser/rag_project/embedding/processed_texts", 
                       help="Directory for processed text files")
    
    # Model configuration
    parser.add_argument("--embedding-model", default="all-MiniLM-L6-v2",
                       help="Sentence transformer model")
    parser.add_argument("--collection", default="processed_documents",
                       help="Qdrant collection name")
    parser.add_argument("--enable-trocr", action="store_true", default=True,
                       help="Enable TrOCR for advanced OCR")
    
    # Test options
    parser.add_argument("--skip-tests", action="store_true",
                       help="Skip search functionality tests")
    
    args = parser.parse_args()
    
    # Validate arguments
    if not any([args.full_pipeline, args.ocr_only, args.embeddings_only]):
        args.full_pipeline = True  # Default to full pipeline
    
    try:
        start_time = datetime.now()
        
        print("🚀 EMBEDDING PIPELINE STARTING")
        print("="*60)
        print(f"📅 Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📁 Input directory: {args.input_dir}")
        print(f"📁 Processed directory: {args.processed_dir}")
        print(f"🤖 Embedding model: {args.embedding_model}")
        print(f"🗃️  Collection: {args.collection}")
        print("="*60)
        
        ocr_summary = None
        embedding_summary = None
        generator = None
        
        # Step 1: OCR Processing
        if args.full_pipeline or args.ocr_only:
            ocr_summary = run_ocr_processing(
                input_dir=args.input_dir,
                output_dir=args.processed_dir,
                enable_trocr=args.enable_trocr
            )
            
            if ocr_summary["successful"] == 0:
                logger.warning("⚠️ No files processed successfully in OCR step")
                if not args.full_pipeline:
                    return
        
        # Step 2: Embedding Generation
        if args.full_pipeline or args.embeddings_only:
            # Check if processed files exist
            processed_dir = Path(args.processed_dir)
            text_files = list(processed_dir.glob("*.txt"))
            if not text_files:
                logger.error(f"❌ No text files found in {processed_dir}")
                logger.error("   Make sure to run OCR processing first")
                return
            embedding_summary = run_embedding_generation(
                input_dir=args.processed_dir,
                model_name=args.embedding_model,
                collection_name=args.collection
            )
            generator = EmbeddingGenerator(
                model_name=args.embedding_model,
                collection_name=args.collection
            )
        
        # Step 3: Search Tests
        if (args.full_pipeline or args.embeddings_only) and not args.skip_tests:
            if generator is not None and embedding_summary is not None and embedding_summary.get("total_embeddings", 0) > 0:
                run_search_tests(generator)
            else:
                logger.warning("⚠️ Skipping tests - no embeddings created")
        
        # Final summary
        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds()
        
        print("\n" + "="*60)
        print("🎯 PIPELINE COMPLETE")
        print("="*60)
        print(f"⏱️  Total time: {total_time:.1f}s")
        
        if ocr_summary:
            print(f"📄 OCR: {ocr_summary['successful']}/{ocr_summary['total_files']} files processed")
        
        if embedding_summary:
            print(f"🔢 Embeddings: {embedding_summary['total_embeddings']} created")
            print(f"📊 Files: {embedding_summary['successful_files']}/{embedding_summary['total_files']}")
            print(f"⚡ Duplicates skipped: {embedding_summary['skipped_duplicates']}")
        
        print(f"📁 Output: {args.processed_dir}")
        print("="*60)
        
        # Save pipeline summary
        pipeline_summary = {
            "pipeline_start": start_time.isoformat(),
            "pipeline_end": end_time.isoformat(),
            "total_time_seconds": total_time,
            "steps_run": {
                "ocr_processing": args.full_pipeline or args.ocr_only,
                "embedding_generation": args.full_pipeline or args.embeddings_only,
                "search_tests": (args.full_pipeline or args.embeddings_only) and not args.skip_tests
            },
            "configuration": {
                "input_dir": args.input_dir,
                "processed_dir": args.processed_dir,
                "embedding_model": args.embedding_model,
                "collection": args.collection,
                "trocr_enabled": args.enable_trocr
            },
            "ocr_summary": ocr_summary,
            "embedding_summary": embedding_summary
        }
        
        summary_path = Path(args.processed_dir) / "pipeline_summary.json"
        import json
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(pipeline_summary, f, indent=2)
        
        logger.info(f"📋 Pipeline summary saved to: {summary_path}")
        
        return pipeline_summary
        
    except Exception as e:
        logger.error(f"❌ Pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()
