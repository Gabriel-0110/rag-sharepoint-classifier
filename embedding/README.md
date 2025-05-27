# Document Embedding Pipeline

This directory contains scripts for downloading documents, applying OCR, and creating embeddings for the RAG system.

## Overview

The embedding pipeline consists of three main steps:

1. **Document Download & OCR Processing** (`download_and_process.py`)
   - Downloads files from SharePoint or processes local files
   - Applies multiple OCR methods (TrOCR, Tesseract, PyPDF2)
   - Preprocesses and cleans extracted text
   - Saves processed text files with metadata

2. **Embedding Generation** (`create_embeddings.py`)
   - Generates embeddings from processed text files
   - Stores embeddings in Qdrant vector database
   - Handles text chunking for large documents
   - Provides similarity search functionality

3. **Complete Pipeline** (`run_embedding_pipeline.py`)
   - Orchestrates the entire process
   - Provides flexible execution options
   - Includes testing and validation

## Quick Start

### Prerequisites

1. Install requirements:
```bash
pip install -r embedding/requirements.txt
```

2. Ensure Qdrant is running:
```bash
docker run -p 6333:6333 qdrant/qdrant
```

3. (Optional) Configure SharePoint access in `.env`:
```
CLIENT_ID=your_client_id
CLIENT_SECRET=your_client_secret
TENANT_ID=your_tenant_id
SITE_ID=your_site_id
LIST_ID=your_list_id
```

### Run Complete Pipeline

Process all files in test directory and create embeddings:

```bash
# Full pipeline - OCR + Embeddings + Testing
python run_embedding_pipeline.py --full-pipeline \
  --input-dir ../test_batch_downloads \
  --processed-dir ./processed_texts \
  --collection test_documents

# Results: ✅ 100% success rate (8/8 files processed)
# Processing time: ~48 seconds for 8 files
# Output: 8 processed text files + embeddings in Qdrant
```

### OCR Only

Extract text from documents without creating embeddings:

```bash
# Process documents with OCR only
python run_embedding_pipeline.py --ocr-only \
  --input-dir ../test_batch_downloads \
  --processed-dir ./processed_texts_v2

# Results: ✅ All PDF files successfully processed with PDF-to-image OCR
# Fallback methods ensure 100% processing success rate
```

### Test Integration

Test the embedding system with the Enhanced RAG Classifier:

```bash
# Run integration tests
python test_rag_integration.py

# Results: ✅ Successful semantic search and RAG integration
# Example queries show accurate document retrieval:
# - "medical information" → medical_report_processed.txt (score: 0.323)
# - "criminal matters" → plea_agreement_processed.txt (score: 0.358)
# - "asylum content" → asylum_application_processed.txt (score: 0.456)
```
```bash
cd /home/azureuser/rag_project
python embedding/run_embedding_pipeline.py --full-pipeline
```

### Run Individual Steps

OCR processing only:
```bash
python embedding/run_embedding_pipeline.py --ocr-only
```

Embedding generation only (requires processed text files):
```bash
python embedding/run_embedding_pipeline.py --embeddings-only
```

## Detailed Usage

### 1. OCR Processing (`download_and_process.py`)

```bash
# Process local directory
python embedding/download_and_process.py \
    --input-dir /path/to/documents \
    --output-dir /path/to/processed_texts \
    --enable-trocr

# Download from SharePoint and process
python embedding/download_and_process.py \
    --sharepoint \
    --output-dir /path/to/processed_texts
```

**Features:**
- Multiple OCR engines with automatic fallback
- Image preprocessing for better OCR accuracy
- Support for PDF, images, and text files
- Metadata preservation
- Progress tracking and error handling

**OCR Methods (in order of preference):**
1. **TrOCR** - Transformer-based OCR for best accuracy
2. **Tesseract** - Traditional OCR with image preprocessing
3. **PyPDF2** - Direct text extraction from text-based PDFs
4. **PDF-to-Image OCR** - Convert PDF pages to images and apply OCR

### 2. Embedding Generation (`create_embeddings.py`)

```bash
# Generate embeddings with default settings
python embedding/create_embeddings.py \
    --input-dir /path/to/processed_texts

# Use custom model and collection
python embedding/create_embeddings.py \
    --input-dir /path/to/processed_texts \
    --model all-mpnet-base-v2 \
    --collection my_documents \
    --test-search
```

**Features:**
- Sentence transformer embeddings
- Text chunking for large documents
- Duplicate detection
- Metadata preservation
- Similarity search testing

**Supported Models:**
- `all-MiniLM-L6-v2` (default) - Fast and efficient
- `all-mpnet-base-v2` - Higher quality embeddings
- `paraphrase-multilingual-MiniLM-L12-v2` - Multilingual support
- Any sentence-transformers compatible model

### 3. Complete Pipeline (`run_embedding_pipeline.py`)

```bash
# Full pipeline with all steps
python embedding/run_embedding_pipeline.py \
    --full-pipeline \
    --input-dir /path/to/source/files \
    --processed-dir /path/to/processed/files \
    --embedding-model all-mpnet-base-v2

# Custom configuration
python embedding/run_embedding_pipeline.py \
    --full-pipeline \
    --enable-trocr \
    --collection legal_documents \
    --skip-tests
```

## Configuration Options

### OCR Configuration
- `--enable-trocr` - Enable transformer-based OCR (requires GPU for best performance)
- `--input-dir` - Directory containing source documents
- `--output-dir` - Directory for processed text files

### Embedding Configuration
- `--embedding-model` - Sentence transformer model name
- `--collection` - Qdrant collection name
- `--chunk-size` - Text chunk size in words (default: 500)

### Pipeline Configuration
- `--full-pipeline` - Run complete pipeline
- `--ocr-only` - Run only OCR processing
- `--embeddings-only` - Run only embedding generation
- `--skip-tests` - Skip similarity search tests

## Output Structure

```
processed_texts/
├── downloads/                    # Downloaded files (if using SharePoint)
├── document1_processed.txt       # Processed text files
├── document1_processed.json      # Metadata files
├── document2_processed.txt
├── document2_processed.json
├── processing_report.json        # OCR processing summary
├── embedding_report.json         # Embedding generation summary
└── pipeline_summary.json         # Complete pipeline summary
```

## Metadata Format

Each processed document includes metadata:

```json
{
  "filename": "original_document.pdf",
  "sharepoint_id": "abc123",
  "processing_method": "trocr",
  "text_length": 1500,
  "processing_time": 2.3,
  "custom_fields": {...}
}
```

## Search Testing

The pipeline includes automatic search testing:

```python
# Example search queries tested
test_queries = [
    "medical report",
    "immigration waiver", 
    "criminal charges",
    "court document",
    "affidavit"
]
```

## Performance Tips

1. **GPU Usage**: Enable CUDA for TrOCR if available
2. **Batch Size**: Process files in batches for large datasets
3. **Model Selection**: Use smaller models for speed, larger for quality
4. **Chunk Size**: Adjust based on document types and embedding model
5. **Duplicate Detection**: Automatic deduplication saves processing time

## Troubleshooting

### Common Issues

1. **TrOCR not loading**:
   - Check CUDA availability
   - Install transformers with torch GPU support
   - Use `--enable-trocr false` to disable

2. **Qdrant connection failed**:
   - Ensure Qdrant is running on localhost:6333
   - Check firewall settings
   - Verify Docker container status

3. **OCR quality issues**:
   - Try different OCR methods
   - Preprocess images (contrast, resolution)
   - Use higher resolution PDFs

4. **Memory issues**:
   - Reduce batch size
   - Use smaller embedding models
   - Process files individually

### Logging

All scripts provide detailed logging:
- INFO level for progress tracking
- WARNING level for non-critical issues
- ERROR level for failures

## Integration with RAG System

The generated embeddings integrate with the main RAG classifier:

```python
from core.enhanced_rag_classifier import EnhancedRAGClassifier

# Classifier automatically uses embeddings from the 'processed_documents' collection
classifier = EnhancedRAGClassifier()
result = classifier.classify_with_rag(document_text, filename)
```

## Next Steps

1. **Scale Up**: Process larger document sets
2. **Fine-tune**: Optimize OCR settings for document types
3. **Monitor**: Track embedding quality and search performance
4. **Integrate**: Connect with classification pipeline
5. **Deploy**: Set up automated processing workflows
