# let's burn Chatbot

An open-source web app that lets you build a Burning Man knowledge base by feeding it URLs. The backend uses a simple retrieval system so answers reference ingested pages. The UI is served directly by FastAPI and works in Safari.

## Features
- Add website URLs to grow the knowledge base
- Ask questions and get responses citing the most relevant source
- Frontend served as static files for easy GitHub Pages hosting

## Setup
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the server:
   ```bash
   uvicorn backend.app:app --reload
   ```
3. Open [http://localhost:8000](http://localhost:8000) in your browser and start chatting.

## Tests
Run the test suite with:
```bash
pytest
```

## License
MIT
