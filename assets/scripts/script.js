const chatLog = document.getElementById('chat-log');
const queryInput = document.getElementById('query');
const sendButton = document.getElementById('send');

// Add chat message to log
function addMessage(message, isUser = false) {
  const messageDiv = document.createElement('div');
  messageDiv.className = `message ${isUser ? 'user-message' : 'bot-message'}`;
  messageDiv.textContent = message;
  chatLog.appendChild(messageDiv);
  chatLog.scrollTop = chatLog.scrollHeight;
}

// Add formatted bot response
function addBotResponse(response) {
  const messageDiv = document.createElement('div');
  messageDiv.className = 'message bot-message';
  
  // Format response with line breaks
  const formattedResponse = response.replace(/\n/g, '<br>');
  messageDiv.innerHTML = formattedResponse;
  
  chatLog.appendChild(messageDiv);
  chatLog.scrollTop = chatLog.scrollHeight;
}

async function sendQuery() {
  const query = queryInput.value.trim();
  if (!query) return;
  
  // Add user message to chat
  addMessage(query, true);
  
  // Show loading state
  const loadingDiv = document.createElement('div');
  loadingDiv.className = 'message bot-message loading';
  loadingDiv.textContent = 'searching the playa for answers...';
  chatLog.appendChild(loadingDiv);
  chatLog.scrollTop = chatLog.scrollHeight;
  
  // Clear input and disable button
  queryInput.value = '';
  sendButton.disabled = true;
  sendButton.textContent = 'searching...';
  
  try {
    console.log('Sending query:', query);
    
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      body: JSON.stringify({ query: query })
    });
    
    console.log('Response status:', res.status);
    console.log('Response headers:', res.headers);
    
    // Remove loading message
    if (loadingDiv.parentNode) {
      chatLog.removeChild(loadingDiv);
    }
    
    const responseText = await res.text();
    console.log('Raw response:', responseText);
    
    if (!res.ok) {
      console.error('Response not OK:', res.status, res.statusText);
      try {
        const errorData = JSON.parse(responseText);
        addMessage(`error: ${errorData.detail || 'unknown error'}`, false);
      } catch (parseErr) {
        addMessage(`server error: ${res.status} - ${responseText}`, false);
      }
      return;
    }
    
    let data;
    try {
      data = JSON.parse(responseText);
    } catch (parseErr) {
      console.error('JSON parse error:', parseErr);
      addMessage(`invalid response format: ${parseErr.message}`, false);
      return;
    }
    
    addBotResponse(data.answer || 'No answer received');
  } catch (err) {
    // Remove loading message if still there
    if (loadingDiv.parentNode) {
      chatLog.removeChild(loadingDiv);
    }
    console.error('Full error details:', err);
    addMessage(`request failed: ${err.message}`, false);
  } finally {
    // Re-enable button
    sendButton.disabled = false;
    sendButton.textContent = '⇡';
    queryInput.focus();
  }
}

// Add enter key support for textarea
queryInput.addEventListener('keydown', function(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendQuery();
  }
});

async function ingestUrl() {
  const urlInput = document.getElementById('url');
  const addButton = document.getElementById('add-url');
  const url = urlInput.value.trim();
  
  if (!url) return;
  
  // Disable button and show loading
  addButton.disabled = true;
  addButton.textContent = 'adding...';
  
  try {
    const res = await fetch('/ingest', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ target_url: url })
    });
    
    if (!res.ok) {
      const errorData = await res.json();
      alert(`❌ Error: ${errorData.detail || 'Unknown error'}`);
      return;
    }
    
    const data = await res.json();
    alert(`✅ ${data.status}! Total documents: ${data.documents}`);
    urlInput.value = ''; // Clear input on success
  } catch (err) {
    alert(`❌ Request failed: ${err.message}`);
    console.error('Ingest error:', err);
  } finally {
    // Re-enable button
    addButton.disabled = false;
    addButton.textContent = 'add website';
  }
}

// Add enter key support for URL input
document.getElementById('url').addEventListener('keypress', function(e) {
  if (e.key === 'Enter') {
    ingestUrl();
  }
});

document.getElementById('send').addEventListener('click', sendQuery);
document.getElementById('add-url').addEventListener('click', ingestUrl);
