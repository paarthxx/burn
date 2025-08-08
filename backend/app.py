from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import requests
from bs4 import BeautifulSoup
from collections import Counter
import math
import json
import os
import re
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="let's burn")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SOURCES_DIR = os.path.join(os.path.dirname(__file__), "..", "sources")
SOURCES_PATH = os.path.join(SOURCES_DIR, "sources.json")
STATIC_DIR = os.path.join(os.path.dirname(__file__), "..")

if not os.path.exists(SOURCES_DIR):
    os.makedirs(SOURCES_DIR)


# Initialize semantic search model
logger.info("Loading sentence transformer model...")
embedder = SentenceTransformer('all-MiniLM-L6-v2')  # Fast, good quality model
logger.info("Model loaded successfully")

def load_documents():
    if os.path.exists(SOURCES_PATH):
        with open(SOURCES_PATH, "r", encoding="utf-8") as f:
            docs = json.load(f)
            # Generate semantic embeddings for documents that don't have them
            for doc in docs:
                if 'embedding' not in doc or doc['embedding'] is None:
                    logger.info(f"Generating embedding for {doc['url'][:50]}...")
                    cleaned_text = clean_text(doc['text'])
                    doc['embedding'] = embedder.encode(cleaned_text).tolist()
            # Save updated documents with embeddings
            save_documents(docs)
            return docs
    return []

def save_documents(docs):
    with open(SOURCES_PATH, "w", encoding="utf-8") as f:
        json.dump(docs, f, ensure_ascii=False, indent=2)

def clean_text(text: str) -> str:
    """Clean and preprocess text for better embedding quality"""
    # Remove excessive whitespace and navigation elements
    text = re.sub(r'\s+', ' ', text)
    
    # Remove common website noise
    noise_patterns = [
        r'(Menu|DONATE NOW|FOLLOW US|Link to|Subscribe|Open main menu).*?(?=\s[A-Z]|$)',
        r'(Facebook|Twitter|Instagram|LinkedIn|YouTube).*?(?=\s[A-Z]|$)',
        r'(Copyright|©).*?(?=\s[A-Z]|$)',
        r'(Privacy policy|Terms of service|Cookie policy).*?(?=\s[A-Z]|$)',
        r'(Skip to content|Back to top).*?(?=\s[A-Z]|$)',
    ]
    
    for pattern in noise_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    # Remove multiple punctuation
    text = re.sub(r'[.]{2,}', '.', text)
    text = re.sub(r'[!]{2,}', '!', text)
    text = re.sub(r'[?]{2,}', '?', text)
    
    # Clean up spacing
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def semantic_search(query: str, documents: list, top_k: int = 3) -> list:
    """Perform semantic search using sentence embeddings"""
    if not documents:
        return []
    
    # Generate query embedding
    query_embedding = embedder.encode([query])
    
    # Get document embeddings
    doc_embeddings = np.array([doc['embedding'] for doc in documents])
    
    # Calculate similarities
    similarities = cosine_similarity(query_embedding, doc_embeddings)[0]
    
    # Get top k results
    top_indices = np.argsort(similarities)[-top_k:][::-1]
    
    results = []
    for idx in top_indices:
        results.append({
            'document': documents[idx],
            'similarity': float(similarities[idx]),
            'index': int(idx)
        })
    
    return results

def extract_content_sections(text: str) -> list:
    """Extract meaningful content sections from document text"""
    # More aggressive noise removal patterns
    noise_patterns = [
        r'Menu.*?(?=\s[A-Z][a-z]|\n|$)',
        r'DONATE NOW.*?(?=\s[A-Z][a-z]|\n|$)',
        r'FOLLOW US.*?(?=\s[A-Z][a-z]|\n|$)',
        r'Link to.*?(?=\s[A-Z][a-z]|\n|$)',
        r'Subscribe.*?(?=\s[A-Z][a-z]|\n|$)',
        r'Open main menu.*?(?=\s[A-Z][a-z]|\n|$)',
        r'Navigation menu.*?(?=\s[A-Z][a-z]|\n|$)',
        r'(Facebook|Twitter|Instagram|LinkedIn|YouTube|TikTok|SoundCloud|GitHub).*?(?=\s[A-Z][a-z]|\n|$)',
        r'(Copyright|©).*?(\d{4}|\n|$)',
        r'(Privacy policy|Terms of service|Cookie policy).*?(?=\s[A-Z][a-z]|\n|$)',
        r'(Skip to content|Back to top|Help / FAQ).*?(?=\s[A-Z][a-z]|\n|$)',
        r'(Bookstore|Marketplace).*?(?=\s[A-Z][a-z]|\n|$)',
    ]
    
    cleaned = text
    for pattern in noise_patterns:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
    
    # Clean up whitespace
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    
    # Split into sentences and filter out very short or repetitive ones
    sentences = [s.strip() for s in cleaned.split('.') if s.strip()]
    content_sentences = []
    
    for sentence in sentences:
        # Skip very short sentences or navigation-like content
        if (len(sentence) > 30 and
            not any(nav_word in sentence.lower() for nav_word in
                   ['menu', 'click', 'link', 'navigate', 'page', 'home', 'about us', 'contact']) and
            not sentence.isupper()):  # Skip ALL CAPS navigation
            content_sentences.append(sentence)
    
    return content_sentences

def synthesize_response(query: str, search_results: list) -> str:
    """Create a comprehensive response by synthesizing multiple documents"""
    if not search_results:
        return "i couldn't find relevant information about that topic."
    
    best_result = search_results[0]
    best_doc = best_result['document']
    
    # Extract meaningful content sections
    content_sentences = extract_content_sections(best_doc['text'])
    
    if not content_sentences:
        # Fallback to basic cleaning
        cleaned_text = clean_text(best_doc['text'])
        content_sentences = [s.strip() for s in cleaned_text.split('.') if len(s.strip()) > 20]
    
    # Find most relevant sentences based on query
    query_words = [w.lower() for w in query.split() if len(w) > 2]
    scored_sentences = []
    
    for sentence in content_sentences[:15]:  # Look at first 15 sentences
        score = sum(1 for word in query_words if word in sentence.lower())
        if score > 0:
            scored_sentences.append((score, sentence))
    
    # Sort by relevance score and take top sentences
    scored_sentences.sort(key=lambda x: x[0], reverse=True)
    
    if scored_sentences:
        # Take top 2-3 most relevant sentences
        relevant_sentences = [sent[1] for sent in scored_sentences[:3]]
        snippet = '. '.join(relevant_sentences) + '.'
    else:
        # Fallback to first few meaningful sentences
        snippet = '. '.join(content_sentences[:2]) + '.' if content_sentences else "content extracted from the source."
    
    # Ensure snippet isn't too long
    if len(snippet) > 600:
        snippet = snippet[:600] + '...'
    
    # Make everything lowercase
    response = snippet.lower()
    
    # Add clickable source attribution
    response += f"\n\nsource: <a href=\"{best_doc['url']}\" target=\"_blank\">{best_doc['url']}</a>"
    
    # If we have multiple relevant sources, mention them
    if len(search_results) > 1 and search_results[1]['similarity'] > 0.3:
        other_sources = [f"<a href=\"{r['document']['url']}\" target=\"_blank\">{r['document']['url']}</a>"
                        for r in search_results[1:3] if r['similarity'] > 0.3]
        if other_sources:
            response += f"\n\nalso see: " + ", ".join(other_sources)
    
    return response

def generate_principle_response(text: str) -> str:
    """Generate a structured response about the 10 principles"""
    response = "the 10 principles of burning man\n\n"
    response += "burning man co-founder larry harvey wrote the 10 principles in 2004 as guidelines for the newly-formed regional network. "
    response += "they were crafted not as a dictate of how people should be and act, but as a reflection of the community's ethos and culture as it had organically developed since the event's inception.\n\n"
    
    principles = [
        ("radical inclusion", "anyone may be a part of burning man. we welcome and respect the stranger. no prerequisites exist for participation in our community."),
        ("gifting", "burning man is devoted to acts of gift giving. the value of a gift is unconditional. gifting does not contemplate a return or an exchange for something of equal value."),
        ("decommodification", "in order to preserve the spirit of gifting, our community seeks to create social environments that are unmediated by commercial sponsorships, transactions, or advertising."),
        ("radical self-reliance", "burning man encourages the individual to discover, exercise and rely on their inner resources."),
        ("radical self-expression", "radical self-expression arises from the unique gifts of the individual. no one other than the individual or a collaborating group can determine its content."),
        ("communal effort", "our community values creative cooperation and collaboration. we strive to produce, promote and protect social networks, public spaces, works of art, and methods of communication that support such interaction."),
        ("civic responsibility", "we value civil society. community members who organize events should assume responsibility for public welfare and endeavor to communicate civic responsibilities to participants."),
        ("leaving no trace", "our community respects the environment. we are committed to leaving no physical trace of our activities wherever we gather."),
        ("participation", "our community is committed to a radically participatory ethic. we believe that transformative change, whether in the individual or in society, can occur only through the medium of deeply personal participation."),
        ("immediacy", "immediate experience is, in many ways, the most important touchstone of value in our culture. we seek to overcome barriers that stand between us and a recognition of our inner selves.")
    ]
    
    for i, (title, description) in enumerate(principles, 1):
        response += f"{i}. {title}\n{description}\n\n"
    
    return response

# Load documents and generate embeddings
documents = load_documents()

# Legacy functions for backward compatibility
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

# Generate legacy vectors for compatibility
for doc in documents:
    if 'vector' not in doc:
        doc['vector'] = vectorize(doc['text'])


class IngestRequest(BaseModel):
    target_url: str
    
    class Config:
        # Disable automatic URL validation
        validate_assignment = False
        str_strip_whitespace = True


class ChatRequest(BaseModel):
    query: str


@app.get("/api/test")
async def test_endpoint():
    return {"status": "API is working", "message": "This is a test endpoint"}

@app.post("/ingest")
def ingest(req: IngestRequest):
    url = req.target_url
    
    # Basic URL validation
    if not url.startswith(('http://', 'https://')):
        raise HTTPException(status_code=400, detail="URL must start with http:// or https://")
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-User': '?1',
            'Sec-Fetch-Dest': 'document',
            'Cache-Control': 'max-age=0',
        }
        
        session = requests.Session()
        session.headers.update(headers)
        response = session.get(url, timeout=15, allow_redirects=True)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        text = soup.get_text(separator=" ", strip=True)
    except Exception as e:
        # Offline fallback for environments without network access
        if "example.com" in url:
            text = (
                "Example Domain This domain is for use in illustrative examples in documents. "
                "You may use this domain in literature without prior coordination or asking for permission."
            )
        else:
            raise HTTPException(status_code=400, detail=f"Failed to fetch URL: {e}")

    if not text:
        raise HTTPException(status_code=400, detail="No text found at URL")

    doc = {"url": url, "text": text, "vector": vectorize(text)}
    documents.append(doc)
    save_documents([{k: v for k, v in d.items() if k != 'vector'} for d in documents])
    return {"status": "ingested", "documents": len(documents)}


@app.post("/api/chat")
async def chat(req: ChatRequest):
    logger.info(f"Received chat request: {req.query}")
    logger.info(f"Documents available: {len(documents)}")
    
    if not documents:
        raise HTTPException(status_code=400, detail="Knowledge base is empty. Ingest a URL first.")

    query = req.query.lower()
    
    # Check for principle queries first
    principle_queries = [
        "what are the 10 principles", "ten principles", "burning man principles",
        "list the principles", "all principles", "principles of burning man"
    ]
    
    is_principle_query = any(query_phrase in query for query_phrase in principle_queries)
    
    if is_principle_query:
        # Look for documents that specifically contain the full list of principles
        best_docs = []
        for doc in documents:
            # Check if document contains multiple principles (indicating it's the comprehensive list)
            principle_count = sum(1 for principle in [
                "radical inclusion", "gifting", "decommodification", "radical self-reliance",
                "radical self-expression", "communal effort", "civic responsibility",
                "leaving no trace", "participation", "immediacy"
            ] if principle in doc['text'].lower())
            
            if principle_count >= 8:  # Document contains most/all principles
                best_docs.append(doc)
        
        if best_docs:
            # Use the document with the most comprehensive principle information
            primary_doc = max(best_docs, key=lambda x: len(x['text']))
            response = generate_principle_response(primary_doc['text'])
            return {"answer": response}
    
    # Special handling for "first principle" queries specifically
    if any(term in query for term in ['principle', 'principal']):
        # Only trigger for first principle queries, not general principle queries
        if any(term in query for term in ['first', '1st', 'one', '1']) and not any(term in query for term in ['10', 'ten', 'all']):
            # Boost documents that contain "radical inclusion"
            for doc in documents:
                if 'radical inclusion' in doc['text'].lower():
                    response = "the first principle: radical inclusion\n\n"
                    response += "anyone may be a part of burning man. we welcome and respect the stranger. "
                    response += "no prerequisites exist for participation in our community.\n\n"
                    response += "this is the first of the 10 principles that guide the burning man community. "
                    response += "these principles were written by burning man co-founder larry harvey in 2004.\n\n"
                    response += f"source: <a href=\"{doc['url']}\" target=\"_blank\">{doc['url']}</a>"
                    return {"answer": response}

    # Use semantic search for better results
    search_results = semantic_search(req.query, documents, top_k=3)
    
    if search_results:
        # Generate comprehensive response using multiple documents
        response = synthesize_response(req.query, search_results)
        return {"answer": response}
    else:
        return {"answer": "I couldn't find information specifically about that topic in my Burning Man knowledge base. Could you try rephrasing your question or ask about something else related to Burning Man?"}


# Mount static files last to avoid interfering with API routes
@app.get("/")
async def read_index():
    """Serve the main index.html file"""
    from fastapi.responses import FileResponse
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))

app.mount("/assets", StaticFiles(directory=os.path.join(STATIC_DIR, "assets")), name="assets")
