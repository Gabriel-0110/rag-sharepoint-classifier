# RAG Project - Clean Structure

## 📁 Project Overview
**Total Size**: ~346MB (mostly vector database storage)

## 🟢 Core Application Files
```
├── main.py                     # Main FastAPI application with RAG endpoints
├── mistral_api_server.py       # Mistral-7B AI model server
├── requirements.txt            # Python dependencies
├── start_mistral.sh           # Service startup script
└── .env                       # Environment variables (keep secure!)
```

## 🧠 Source Code (`src/` directory)
```
src/
├── upsert_documents.py        # Document embedding and Qdrant ingestion
├── retrieve_and_classify.py   # RAG retrieval and OpenAI classification
└── classify_and_update.py     # Full pipeline orchestration
```

## 🔧 Processing & Integration Scripts
```
├── extract_all.py             # Text extraction (PDF, DOCX, images)
├── batch_from_sharepoint.py   # SharePoint batch processing
├── update_sharepoint.py       # SharePoint metadata updates
├── log_classification.py      # Classification result logging
└── classify_and_update.py     # Pipeline orchestration
```

## 🧪 Development & Testing
```
├── debug_pipeline.py          # Pipeline debugging
├── embed_test.py              # Embedding and classification testing
├── search_test.py             # Search functionality testing
├── download_test.py           # Download testing
└── extract_test.py            # Text extraction testing
```

## 💾 Data & Storage
```
├── storage/                   # Qdrant vector database (266MB)
│   ├── collections/documents/ # Document embeddings and metadata
│   └── raft_state.json       # Database state
├── backup/                    # Backed up files (32KB)
├── batch_input/              # Input files for processing (empty)
├── downloads/                # Downloaded documents (empty)
├── extracted_texts/          # Extracted text files (empty)
├── sp_batch_downloads/       # SharePoint downloads (empty)
└── snapshots/                # Temporary snapshots (empty)
```

## 📊 Current State
- **Security**: ✅ Hardcoded tokens removed
- **Size**: ✅ Optimized (removed ~200MB+ of unnecessary files)
- **Structure**: ✅ Clean and organized
- **Functionality**: ✅ All core features preserved

## 🚀 Ready for:
- ✅ Production deployment
- ✅ Git repository management
- ✅ Continued development
- ✅ SharePoint integration
- ✅ RAG query processing

## 🔄 Processing Workflow
1. **Input**: Documents uploaded to SharePoint or local directories
2. **Extract**: Text extraction from PDF/DOCX/images
3. **Embed**: Generate vector embeddings using sentence-transformers
4. **Store**: Store in Qdrant vector database
5. **Query**: RAG retrieval + Mistral/OpenAI classification
6. **Update**: Write results back to SharePoint metadata

## 📋 Next Steps
- Keep this clean structure
- Regularly clean processing directories after batch jobs
- Monitor storage/ directory size as documents are added
- Use backup/ directory for important logs before deletion
