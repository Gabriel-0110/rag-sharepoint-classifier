import os
import re
import uuid
from openai import OpenAI
from docx import Document
import fitz  # PyMuPDF
from PIL import Image
import pytesseract
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams, Distance

def extract_text(path):
    ext = path.lower().split('.')[-1]
    if ext == 'pdf':
        doc = fitz.open(path)
        text = ''
        for page in doc:
            t = page.get_text().strip()
            if t:
                text += t + '\n'
            else:
                pix = page.get_pixmap(dpi=300)
                img = Image.frombytes('RGB', [pix.width, pix.height], pix.samples)
                text += pytesseract.image_to_string(img) + '\n'
        return text
    elif ext == 'docx':
        doc = Document(path)
        return '\n'.join(p.text for p in doc.paragraphs)
    else:
        return pytesseract.image_to_string(Image.open(path))

def classify_with_llm(text: str) -> tuple[str, str]:
    # configure OpenAI-compatible client
    client = OpenAI(
        api_key="sk-mistral-local",  # dummy key
        base_url="http://localhost:8001"  # your FastAPI server
    )

    prompt = (
        "You are a legal document classification assistant.\n\n"
        "Determine the Document Type and Document Category of the following document.\n\n"
        "Document text:\n"
        f"{text[:4000]}\n\n"
        "Provide the answer in this format only:\n"
        "Document Type: <type>\n"
        "Document Category: <category>\n"
    )

    resp = client.chat.completions.create(
        model="mistral-7b-instruct-v0.3",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=200
    )
    result = resp.choices[0].message.content

    type_match = re.search(r"Document Type:\s*(.*)", result)
    cat_match = re.search(r"Document Category:\s*(.*)", result)

    return (
        type_match.group(1).strip() if type_match else "Unknown",
        cat_match.group(1).strip() if cat_match else "Unknown"
    )

if __name__ == '__main__':
    # locate the latest file in downloads/
    downloads = os.path.join(os.getcwd(), 'downloads')
    files = [f for f in os.listdir(downloads) if os.path.isfile(os.path.join(downloads, f))]
    if not files:
        print("No files found in downloads/")
        exit()

    latest = max(files, key=lambda f: os.path.getctime(os.path.join(downloads, f)))
    path = os.path.join(downloads, latest)
    print(f"Processing {path}")

    # extract and classify
    text = extract_text(path)
    doc_type, doc_cat = classify_with_llm(text)
    print(f"→ Type: {doc_type} | Category: {doc_cat}")

    # embed & upsert to Qdrant
    embedder = SentenceTransformer('all-MiniLM-L6-v2', device='cpu')
    qdrant = QdrantClient(url='http://localhost:6333')
    vec = embedder.encode([text])[0]

    collections = qdrant.get_collections().collections
    existing_names = [col.name for col in collections]

    if 'documents' not in existing_names:
        qdrant.create_collection(
            collection_name='documents',
            vectors_config=VectorParams(size=len(vec), distance=Distance.COSINE)
        )

    point_id = str(uuid.uuid4())
    qdrant.upsert(
        collection_name='documents',
        points=[{
            'id': point_id,
            'vector': vec.tolist(),
            'payload': {
                'file_name': latest,
                'text_snippet': text[:200],
                'doc_type': doc_type,
                'doc_category': doc_cat
            }
        }]
    )
    print("✅ Embedded and upserted as", point_id)
