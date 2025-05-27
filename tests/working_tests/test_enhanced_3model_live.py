#!/usr/bin/env python3
"""
Live Test for Enhanced 3-Model RAG Classification System

This test validates the complete 3-model architecture:
1. PRIMARY: SaulLM (Equall/Saul-7B-Instruct-v1) with 8-bit quantization
2. FALLBACK: Mistral (mistralai/Mistral-7B-Instruct-v0.3) with 8-bit quantization  
3. VALIDATOR: BART-MNLI (facebook/bart-large-mnli) for zero-shot validation

Tests with real SharePoint documents from test_batch_downloads directory.
"""

import os
import sys
import json
import time
from pathlib import Path
from typing import Dict, List, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.enhanced_rag_classifier import EnhancedRAGClassifier
from core.document_processor import DocumentProcessor
from core.vector_store import VectorStore

class Live3ModelTest:
    """Test suite for the enhanced 3-model classification system"""
    
    def __init__(self):
        self.test_files_dir = "/home/azureuser/rag_project/test_batch_downloads"
        self.results = []
        self.classifier = None
        self.document_processor = None
        self.vector_store = None
        
    def setup(self):
        """Initialize the classification system"""
        print("🚀 Setting up Enhanced 3-Model Classification System...")
        
        try:
            # Initialize vector store
            print("  📚 Initializing Vector Store...")
            self.vector_store = VectorStore()
            
            # Initialize document processor
            print("  📄 Initializing Document Processor...")
            self.document_processor = DocumentProcessor()
            
            # Initialize enhanced classifier with 3-model architecture
            print("  🤖 Initializing Enhanced Classifier (SaulLM + Mistral + BART)...")
            self.classifier = EnhancedRAGClassifier(
                use_quantization=True,  # Enable 8-bit quantization
                enable_validation=True,  # Enable BART validation
                enable_fallback=True     # Enable Mistral fallback
            )
            
            print("✅ Setup complete!")
            return True
            
        except Exception as e:
            print(f"❌ Setup failed: {str(e)}")
            return False
    
    def get_test_files(self) -> List[str]:
        """Get list of test files to classify"""
        test_files = []
        
        if os.path.exists(self.test_files_dir):
            for file_name in os.listdir(self.test_files_dir):
                file_path = os.path.join(self.test_files_dir, file_name)
                if os.path.isfile(file_path):
                    test_files.append(file_path)
        
        # Sort and limit to 10 files for this test
        test_files.sort()
        return test_files[:10]
    
    def process_document(self, file_path: str) -> Dict[str, Any]:
        """Process a single document and extract text"""
        try:
            file_name = os.path.basename(file_path)
            print(f"  📖 Processing: {file_name}")
            
            # Extract text using document processor
            if file_path.endswith('.pdf'):
                text_content = self.document_processor.extract_text_from_pdf(file_path)
            elif file_path.endswith('.txt'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    text_content = f.read()
            else:
                return {
                    'file_name': file_name,
                    'error': f'Unsupported file type: {file_path}',
                    'processed': False
                }
            
            # Truncate if too long (for testing purposes)
            if len(text_content) > 2000:
                text_content = text_content[:2000] + "..."
            
            return {
                'file_name': file_name,
                'file_path': file_path,
                'text_content': text_content,
                'text_length': len(text_content),
                'processed': True
            }
            
        except Exception as e:
            return {
                'file_name': os.path.basename(file_path),
                'file_path': file_path,
                'error': str(e),
                'processed': False
            }
    
    def classify_document(self, doc_info: Dict[str, Any]) -> Dict[str, Any]:
        """Classify a document using the 3-model architecture"""
        if not doc_info.get('processed', False):
            return {
                **doc_info,
                'classification_result': {
                    'category': 'ERROR',
                    'confidence_score': 0.0,
                    'error': doc_info.get('error', 'Document processing failed')
                }
            }
        
        try:
            file_name = doc_info['file_name']
            text_content = doc_info['text_content']
            
            print(f"  🤖 Classifying: {file_name}")
            print(f"    📝 Text length: {len(text_content)} characters")
            
            # Create mock RAG context (in real scenario, this would come from vector search)
            rag_context = {
                'retrieved_documents': [
                    {
                        'content': text_content[:500],  # Sample context
                        'metadata': {'source': file_name}
                    }
                ],
                'query': f"Classify this document: {file_name}"
            }
            
            # Perform classification using the enhanced 3-model system
            start_time = time.time()
            result = self.classifier.classify_document_enhanced(
                document_text=text_content,
                rag_context=rag_context,
                filename=file_name
            )
            classification_time = time.time() - start_time
            
            # Add timing information
            result['processing_time_seconds'] = round(classification_time, 2)
            
            print(f"    ✅ Classification complete in {classification_time:.2f}s")
            print(f"    📊 Category: {result.get('category', 'UNKNOWN')}")
            print(f"    🎯 Confidence: {result.get('confidence_score', 0.0):.3f}")
            
            if result.get('models_used'):
                print(f"    🔧 Models used: {', '.join(result['models_used'])}")
            
            return {
                **doc_info,
                'classification_result': result
            }
            
        except Exception as e:
            print(f"    ❌ Classification failed: {str(e)}")
            return {
                **doc_info,
                'classification_result': {
                    'category': 'ERROR',
                    'confidence_score': 0.0,
                    'error': str(e),
                    'models_used': []
                }
            }
    
    def run_test(self):
        """Run the complete test suite"""
        print("\n" + "="*80)
        print("🧪 ENHANCED 3-MODEL RAG CLASSIFICATION LIVE TEST")
        print("="*80)
        
        # Setup
        if not self.setup():
            print("❌ Test aborted due to setup failure")
            return False
        
        # Get test files
        test_files = self.get_test_files()
        print(f"\n📂 Found {len(test_files)} test files:")
        for i, file_path in enumerate(test_files, 1):
            print(f"   {i:2d}. {os.path.basename(file_path)}")
        
        if not test_files:
            print("❌ No test files found!")
            return False
        
        print(f"\n🚀 Starting classification of {len(test_files)} documents...")
        print("-" * 80)
        
        # Process and classify each document
        total_start_time = time.time()
        
        for i, file_path in enumerate(test_files, 1):
            print(f"\n📄 Document {i}/{len(test_files)}: {os.path.basename(file_path)}")
            
            # Process document
            doc_info = self.process_document(file_path)
            
            # Classify document
            result = self.classify_document(doc_info)
            
            # Store result
            self.results.append(result)
            
            print(f"   ✅ Document {i} complete")
        
        total_time = time.time() - total_start_time
        
        # Generate summary report
        self.generate_report(total_time)
        
        return True
    
    def generate_report(self, total_time: float):
        """Generate a comprehensive test report"""
        print("\n" + "="*80)
        print("📊 TEST RESULTS SUMMARY")
        print("="*80)
        
        successful_classifications = 0
        error_classifications = 0
        total_processing_time = 0
        categories_found = {}
        models_usage = {}
        
        print("\n📋 INDIVIDUAL RESULTS:")
        print("-" * 80)
        
        for i, result in enumerate(self.results, 1):
            file_name = result['file_name']
            classification = result['classification_result']
            
            category = classification.get('category', 'UNKNOWN')
            confidence = classification.get('confidence_score', 0.0)
            proc_time = classification.get('processing_time_seconds', 0.0)
            models_used = classification.get('models_used', [])
            
            print(f"{i:2d}. {file_name}")
            print(f"    📊 Category: {category}")
            print(f"    🎯 Confidence: {confidence:.3f}")
            print(f"    ⏱️  Time: {proc_time:.2f}s")
            print(f"    🤖 Models: {', '.join(models_used) if models_used else 'None'}")
            
            if 'error' in classification:
                print(f"    ❌ Error: {classification['error']}")
                error_classifications += 1
            else:
                successful_classifications += 1
            
            # Update statistics
            total_processing_time += proc_time
            categories_found[category] = categories_found.get(category, 0) + 1
            
            for model in models_used:
                models_usage[model] = models_usage.get(model, 0) + 1
            
            print()
        
        # Overall statistics
        print("📈 OVERALL STATISTICS:")
        print("-" * 40)
        print(f"✅ Successful classifications: {successful_classifications}")
        print(f"❌ Failed classifications: {error_classifications}")
        print(f"📊 Success rate: {successful_classifications/len(self.results)*100:.1f}%")
        print(f"⏱️  Total processing time: {total_time:.2f}s")
        print(f"⚡ Average time per document: {total_processing_time/len(self.results):.2f}s")
        
        print(f"\n🏷️  CATEGORIES FOUND:")
        for category, count in sorted(categories_found.items()):
            print(f"   {category}: {count} documents")
        
        print(f"\n🤖 MODEL USAGE:")
        for model, count in sorted(models_usage.items()):
            print(f"   {model}: {count} times")
        
        # Save detailed results to JSON
        self.save_results()
        
        print(f"\n💾 Detailed results saved to: enhanced_3model_test_results.json")
        print("="*80)
    
    def save_results(self):
        """Save detailed results to JSON file"""
        output_file = "enhanced_3model_test_results.json"
        
        report_data = {
            'test_info': {
                'test_name': 'Enhanced 3-Model RAG Classification Live Test',
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'total_documents': len(self.results),
                'test_files_directory': self.test_files_dir
            },
            'model_configuration': {
                'primary_model': 'Equall/Saul-7B-Instruct-v1',
                'fallback_model': 'mistralai/Mistral-7B-Instruct-v0.3',
                'validator_model': 'facebook/bart-large-mnli',
                'quantization_enabled': True,
                'validation_enabled': True,
                'fallback_enabled': True
            },
            'results': self.results
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)

def main():
    """Main test execution function"""
    try:
        # Create and run test
        test = Live3ModelTest()
        success = test.run_test()
        
        if success:
            print("\n🎉 Test completed successfully!")
            return 0
        else:
            print("\n💥 Test failed!")
            return 1
            
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())
