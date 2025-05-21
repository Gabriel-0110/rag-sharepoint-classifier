#!/usr/bin/env python
import os
import uuid
from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams, Distance
from sentence_transformers import SentenceTransformer

def main():
    # — Configuration (env vars with defaults) —
    QDRANT_URL    = os.getenv("QDRANT_URL", "http://localhost:6333")
    COLLECTION    = os.getenv("QDRANT_COLLECTION", "documents")
    TEXT_DIR      = os.getenv("TEXT_DIR", "extracted_texts")
    CHUNK_SIZE    = int(os.getenv("CHUNK_SIZE", 1000))
    CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 200))

    # Optional SharePoint ID mapping
    SHAREPOINT_IDS = {
        # "ABDEL TECORRAL Affd.601A": "6196b7f4-934c-49cb-af7c-6f15835eb1b9",
    }

    # 1. Connect & recreate
    client = QdrantClient(url=QDRANT_URL, api_key=os.getenv("QDRANT_API_KEY"))
    client.recreate_collection(
        collection_name=COLLECTION,
        vectors_config=VectorParams(size=384, distance=Distance.COSINE)
    )
    print(f"✅ Collection '{COLLECTION}' ready for chunked ingestion.")

    # 2. Load embedder
    embedder = SentenceTransformer("all-MiniLM-L6-v2")
    print("✅ Embedder loaded.")

    # 3. Process files
    for fname in os.listdir(TEXT_DIR):
        if not fname.lower().endswith(".txt"):
            continue
        path = os.path.join(TEXT_DIR, fname)
        with open(path, "r", encoding="utf-8") as f:
            text = f.read().strip()
        if not text:
            print(f"⚠️ Empty file, skipping {fname}")
            continue

        stem    = os.path.splitext(fname)[0]
        base_id = SHAREPOINT_IDS.get(stem) or str(uuid.uuid5(uuid.NAMESPACE_URL, stem))

        start, idx, length = 0, 0, len(text)
        while start < length:
            end   = min(start + CHUNK_SIZE, length)
            chunk = text[start:end]
            vector = embedder.encode(chunk)

            try:
                namespace = uuid.UUID(base_id)
            except ValueError:
                namespace = uuid.NAMESPACE_URL
            chunk_id = str(uuid.uuid5(namespace, f"{stem}_{idx}"))

            payload = {"file_name": fname, "chunk_index": idx, "snippet": chunk[:300]}
            client.upsert(
                collection_name=COLLECTION,
                points=[{"id": chunk_id, "vector": vector.tolist(), "payload": payload}]
            )
            print(f"→ Upserted chunk {idx} of {fname} as ID={chunk_id}")

            start += CHUNK_SIZE - CHUNK_OVERLAP
            idx   += 1

    print("✅ All chunks upserted.")

if __name__ == "__main__":
    main()
