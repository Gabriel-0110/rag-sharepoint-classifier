# Minimal stub for EmbeddingGenerator and test_embedding_search

class DummyQdrantClient:
    def search(self, collection_name, query_vector, limit=3):
        class DummyResult:
            def __init__(self, i):
                self.payload = {'filename': f'dummy_file_{i}.txt'}
                self.score = 1.0 - 0.1 * i
        return [DummyResult(i) for i in range(limit)]

class EmbeddingGenerator:
    def __init__(self, *args, **kwargs):
        self.qdrant_client = DummyQdrantClient()
        self.embedding_model = None

    def generate(self, *args, **kwargs):
        return []

    def process_text_file(self, *args, **kwargs):
        return []

    def create_embedding_for_file(self, *args, **kwargs):
        return []

    def search_similar(self, *args, **kwargs):
        return []

    def stats(self):
        return {"total_embeddings": 0}

    def process_directory(self, *args, **kwargs):
        return {"processed": 0}

    def encode(self, texts):
        if self.embedding_model and hasattr(self.embedding_model, 'encode'):
            return self.embedding_model.encode(texts)
        return [[0.0] * 384 for _ in texts]

def test_embedding_search(*args, **kwargs):
    return {"result": "stub"}
