import os
import json
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
import openai

# — Configuration via env vars —
QDRANT_URL        = os.getenv("QDRANT_URL",        "http://localhost:6333")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "documents")
TOP_K             = int(os.getenv("TOP_K",          5))
OPENAI_MODEL      = os.getenv("OPENAI_MODEL",      "gpt-3.5-turbo")

# Initialize clients
openai.api_key = os.getenv("OPENAI_API_KEY")
_qdrant_client = QdrantClient(
    url=QDRANT_URL,
    api_key=os.getenv("QDRANT_API_KEY")
)
_embedder = SentenceTransformer("all-MiniLM-L6-v2")


def retrieve_snippets(query: str):
    vec  = _embedder.encode(query).tolist()
    hits = _qdrant_client.search(
        collection_name=QDRANT_COLLECTION,
        query_vector=vec,
        limit=TOP_K
    )
    snippets = [hit.payload.get("snippet", "") for hit in hits]
    ids      = [hit.id for hit in hits]
    return snippets, ids


def build_prompt(snippets: list[str], query: str) -> str:
    prompt = (
        f"Answer the following question as accurately as possible, using the context below.\n\n"
        f"Question: {query}\n\nContext:\n"
    )
    for i, snip in enumerate(snippets, start=1):
        prompt += f"{i}. {snip}\n"
    prompt += "\nPlease provide a concise answer and cite the snippet numbers you used."
    return prompt


def classify(prompt: str) -> str:
    """
    Use the new v1.x interface for Chat Completions.
    """
    response = openai.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()


def retrieve_and_classify(query: str) -> dict:
    snippets, source_ids = retrieve_snippets(query)
    prompt = build_prompt(snippets, query)
    answer = classify(prompt)
    return {
        "answer": answer,
        "source_ids": source_ids
    }


if __name__ == "__main__":
    # Quick local test
    res = retrieve_and_classify("Test connectivity")
    print(json.dumps(res, indent=2))
