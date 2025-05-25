import os
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient

# Initialize embedder and Qdrant client
embedder = SentenceTransformer('all-MiniLM-L6-v2')
qdrant = QdrantClient(url='http://localhost:6333')

# Build a query
query = input("Enter a search query: ")
print(f"Searching for: '{query}'\n")

# Encode the query
vector = embedder.encode([query])[0].tolist()

# Perform search
results = qdrant.search(
    collection_name='documents',
    query_vector=vector,
    limit=5
)

# Display results
if not results:
    print("No results found.")
else:
    print("Top matches:")
    for hit in results:
        payload = hit.payload
        print(f"- ID: {hit.id} | Score: {hit.score:.4f}")
        print(f"  File: {payload.get('file_name')}\n  Snippet: {payload.get('text_snippet')}...\n")
