from fastapi.testclient import TestClient
from backend.app import app, documents, SOURCES_PATH
import os

client = TestClient(app)

def setup_function(func):
    # Ensure clean state
    if os.path.exists(SOURCES_PATH):
        os.remove(SOURCES_PATH)
    documents.clear()


def test_ingest_and_chat():
    resp = client.post('/ingest', json={'target_url': 'https://www.example.com'})
    assert resp.status_code == 200
    data = resp.json()
    assert data['status'] == 'ingested'

    resp2 = client.post('/chat', json={'query': 'Example Domain'})
    assert resp2.status_code == 200
    assert 'Example Domain' in resp2.json()['answer']
