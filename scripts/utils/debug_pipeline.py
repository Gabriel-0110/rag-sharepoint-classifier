from extract_all import extract_text_from_file
from embed_test import classify_with_llm
from log_classification import log_classification_result
from core.sharepoint_integration import update_metadata
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams, Distance
import uuid, os

# CONFIG — update these
FILE_PATH = "sp_batch_downloads/0203_001.pdf"  # Pick one of your real files
ITEM_ID = "4273"  # Replace with a valid SharePoint ListItem ID

# Step 1 — Extract
print(f"🔍 Extracting text from: {FILE_PATH}")
text = extract_text_from_file(FILE_PATH)

# Step 2 — Classify
print("🧠 Classifying document...")
doc_type, doc_category = classify_with_llm(text)
print(f"→ Result: {doc_type} | {doc_category}")

# Step 3 — Embed & store
print("🔗 Generating vector embedding...")
embedder = SentenceTransformer("all-MiniLM-L6-v2")
vector = embedder.encode([text])[0].tolist()

qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
client = QdrantClient(url=qdrant_url)

# Ensure the 'documents' collection exists
existing = [col.name for col in client.get_collections().collections]
if "documents" not in existing:
    print("⚙️  Creating 'documents' collection in Qdrant…")
    client.create_collection(
        collection_name="documents",
        vectors_config=VectorParams(size=len(vector), distance=Distance.COSINE)
    )
    print("✅ 'documents' collection created.")

# Upsert the vector
from qdrant_client.http.models import PointStruct

client.upsert(
    collection_name="documents",
    points=[
        PointStruct(
            id=str(uuid.uuid4()),
            vector=vector,
            payload={
                "file_name": os.path.basename(FILE_PATH),
                "text_snippet": text[:300],
                "doc_type": doc_type,
                "doc_category": doc_category
            }
        )
    ]
)
print("✅ Vector stored in Qdrant.")

# Step 4 — Update SharePoint
print("🔄 Updating SharePoint metadata...")
update_metadata(item_id=ITEM_ID,
                filename=os.path.basename(FILE_PATH),
                doc_type=doc_type,
                doc_category=doc_category)

# Step 5 — Log Result
log_classification_result(os.path.basename(FILE_PATH), ITEM_ID, doc_type, doc_category)
print("✅ Classification complete and logged.")
