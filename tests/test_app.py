from fastapi.testclient import TestClient
from backend.app import app, documents, DOC_PATH
import os

client = TestClient(app)

def setup_function(func):
    # Ensure clean state
    if os.path.exists(DOC_PATH):
        os.remove(DOC_PATH)
    documents.clear()


def test_ingest_and_chat():
    resp = client.post('/ingest', json={'url': 'https://www.example.com'})
    assert resp.status_code == 200
    data = resp.json()
    assert data['status'] == 'ingested'

    resp2 = client.post('/chat', json={'query': 'Example Domain'})
    assert resp2.status_code == 200
    assert 'Example Domain' in resp2.json()['answer']
