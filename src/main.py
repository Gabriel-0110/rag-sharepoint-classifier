from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from src.upsert_documents import main as ingest
from src.retrieve_and_classify import retrieve_and_classify

app = FastAPI(title="RAG Document Classification Service")

class QueryRequest(BaseModel):
    query: str

@app.get("/")
def healthcheck():
    return {"status": "ok"}

@app.post("/ingest")
def ingest_endpoint():
    try:
        ingest()
        return {"status": "ingest started"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query")
def query_endpoint(req: QueryRequest):
    try:
        result = retrieve_and_classify(req.query)
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
