import os
import uuid
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams, Distance
from extract_all import extract_text_from_file
from embed_test import classify_with_llm
from update_sharepoint import update_metadata
from log_classification import log_classification_result

def classify_and_update(file_path: str, item_id: str) -> dict:
    """
    Extract text, classify document, upsert to Qdrant,
    update SharePoint metadata, and log result.
    """
    # 1. Extract
    text = extract_text_from_file(file_path)

    # 2. Classify
    doc_type, doc_category = classify_with_llm(text)

    # 3. Embed
    embedder = SentenceTransformer("all-MiniLM-L6-v2")
    vector = embedder.encode([text])[0].tolist()

    # 4. Qdrant upsert
    client = QdrantClient(url=os.getenv("QDRANT_URL", "http://localhost:6333"))
    existing = [c.name for c in client.get_collections().collections]
    if "documents" not in existing:
        client.create_collection(
            collection_name="documents",
            vectors_config=VectorParams(size=len(vector), distance=Distance.COSINE)
        )
    client.upsert(
        collection_name="documents",
        points=[{
            "id": str(uuid.uuid4()),
            "vector": vector,
            "payload": {
                "file_name": os.path.basename(file_path),
                "text_snippet": text[:300],
                "doc_type": doc_type,
                "doc_category": doc_category
            }
        }]
    )

    # 5. Update SharePoint
    update_metadata(item_id=item_id,
                      filename=os.path.basename(file_path),
                      doc_type=doc_type,
                      doc_category=doc_category)

    # 6. Log
    log_classification_result(os.path.basename(file_path),
                              item_id, doc_type, doc_category)

    return {"doc_type": doc_type, "doc_category": doc_category, "status": "ok"}
