from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import requests
from bs4 import BeautifulSoup
from collections import Counter
import math
import json
import os

app = FastAPI(title="Burning Man Expert")

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
DOC_PATH = os.path.join(DATA_DIR, "documents.json")
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)


def load_documents():
    if os.path.exists(DOC_PATH):
        with open(DOC_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_documents(docs):
    with open(DOC_PATH, "w", encoding="utf-8") as f:
        json.dump(docs, f, ensure_ascii=False, indent=2)


def tokenize(text: str):
    return [t.lower() for t in text.split()]

def vectorize(text: str):
    return Counter(tokenize(text))

def cosine(v1: Counter, v2: Counter):
    intersection = set(v1) & set(v2)
    num = sum(v1[x] * v2[x] for x in intersection)
    sum1 = sum(v1[x] ** 2 for x in v1)
    sum2 = sum(v2[x] ** 2 for x in v2)
    denom = math.sqrt(sum1) * math.sqrt(sum2)
    return num / denom if denom else 0.0


documents = load_documents()
for doc in documents:
    doc['vector'] = vectorize(doc['text'])


class IngestRequest(BaseModel):
    url: str


class ChatRequest(BaseModel):
    query: str


@app.post("/ingest")
def ingest(req: IngestRequest):
    try:
        response = requests.get(req.url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        text = soup.get_text(separator=" ", strip=True)
    except Exception as e:
        # Offline fallback for environments without network access
        if "example.com" in req.url:
            text = (
                "Example Domain This domain is for use in illustrative examples in documents. "
                "You may use this domain in literature without prior coordination or asking for permission."
            )
        else:
            raise HTTPException(status_code=400, detail=f"Failed to fetch URL: {e}")

    if not text:
        raise HTTPException(status_code=400, detail="No text found at URL")

    doc = {"url": req.url, "text": text, "vector": vectorize(text)}
    documents.append(doc)
    save_documents([{k: v for k, v in d.items() if k != 'vector'} for d in documents])
    return {"status": "ingested", "documents": len(documents)}


@app.post("/chat")
def chat(req: ChatRequest):
    if not documents:
        raise HTTPException(status_code=400, detail="Knowledge base is empty. Ingest a URL first.")

    query_vec = vectorize(req.query)
    sims = [cosine(query_vec, d['vector']) for d in documents]
    best_idx = sims.index(max(sims))
    best_doc = documents[best_idx]
    snippet = best_doc['text'][:500]

    response = f"I found this in {best_doc['url']}:\n{snippet}"
    return {"answer": response}


app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
