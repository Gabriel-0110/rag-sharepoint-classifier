import csv
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient, models

embedding_model = SentenceTransformer('nlpaueb/legal-bert-base-uncased', device='cpu')
qdrant = QdrantClient(url="http://localhost:6333")
COLLECTION = "documents"

def upsert_from_csv(csv_path):
    with open(csv_path, newline='') as f:
        reader = csv.DictReader(f)
        points = []
        for i, row in enumerate(reader):
            text = row['text']
            doc_type = row['doc_type']
            doc_category = row['doc_category']
            embedding = embedding_model.encode(text).tolist()
            payload = {
                "text_snippet": text[:500],
                "doc_type": doc_type,
                "doc_category": doc_category
            }
            points.append(models.PointStruct(
                id=i,
                vector=embedding,
                payload=payload
            ))
        qdrant.upsert(collection_name=COLLECTION, points=points)
        print(f"Upserted {len(points)} documents to Qdrant.")

if __name__ == "__main__":
    upsert_from_csv("scripts/utils/seed_documents.csv")
