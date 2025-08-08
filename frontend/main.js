const chatLog = document.getElementById('chat-log');

async function sendQuery() {
  const query = document.getElementById('query').value;
  if (!query) return;
  try {
    const res = await fetch('/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query })
    });
    const data = await res.json();
    chatLog.textContent = data.answer || data.detail || 'Error';
  } catch (err) {
    chatLog.textContent = 'Request failed';
  }
}

async function ingestUrl() {
  const url = document.getElementById('url').value;
  if (!url) return;
  try {
    const res = await fetch('/ingest', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url })
    });
    const data = await res.json();
    alert(data.status ? `Ingested. Total documents: ${data.documents}` : data.detail);
  } catch (err) {
    alert('Request failed');
  }
}

document.getElementById('send').addEventListener('click', sendQuery);
document.getElementById('add-url').addEventListener('click', ingestUrl);
