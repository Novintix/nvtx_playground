const API_BASE = 'http://localhost:8002';

// DOM Elements
const queryInput = document.getElementById('queryInput');
const queryBtn = document.getElementById('queryBtn');
const resultsSection = document.getElementById('resultsSection');
const resultsContent = document.getElementById('resultsContent');
const sourceBadge = document.getElementById('sourceBadge');

// Set query from example chip
function setQuery(text) {
    queryInput.value = text;
    queryInput.focus();
}

// Query handler
queryBtn.addEventListener('click', async () => {
    const query = queryInput.value.trim();
    if (!query) return;
    
    queryBtn.disabled = true;
    queryBtn.innerHTML = '<span class="btn-icon">⏳</span> Searching...';
    
    // Show loading
    resultsSection.style.display = 'block';
    resultsContent.innerHTML = `
        <div class="loading">
            <div class="spinner"></div>
            <p class="loading-text">AI is analyzing your question...</p>
        </div>
    `;
    
    try {
        const response = await fetch(`${API_BASE}/query`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ query })
        });
        
        if (!response.ok) throw new Error('Query failed');
        
        const data = await response.json();
        
        displayResults(data);
        
    } catch (error) {
        console.error('Error:', error);
        resultsContent.innerHTML = `
            <div class="error">
                <strong>Error:</strong> ${error.message}
                <br><br>
                Make sure the query service is running on port 8002.
            </div>
        `;
    } finally {
        queryBtn.disabled = false;
        queryBtn.innerHTML = '<span class="btn-icon">🔍</span> Search';
    }
});

// Enter key to search
queryInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        queryBtn.click();
    }
});

function displayResults(data) {
    // Update source badge
    const source = data.source || 'unknown';
    const status = data.status || 'success';
    
    sourceBadge.textContent = source === 'mongodb' ? '🗄️ MongoDB (HR)' : 
                              source === 'rag' ? '🧾 RAG (Invoices)' : 
                              source === 'error' ? '⚠️ Error' :
                              '🤖 AI Router';
    sourceBadge.className = `source-badge ${source}`;
    
    // Display answer
    const answer = data.answer || 'No answer found';
    
    // Check if it's an error status
    if (status === 'error' || status === 'quota_exceeded' || source === 'error') {
        resultsContent.innerHTML = `
            <div class="error-message">
                ${formatAnswer(answer)}
            </div>
        `;
    } else {
        resultsContent.innerHTML = `
            <div class="answer-text">${formatAnswer(answer)}</div>
        `;
    }
}

function formatAnswer(answer) {
    // Format JSON if present
    if (answer.includes('{') || answer.includes('[')) {
        try {
            // Try to extract and format JSON
            const jsonMatch = answer.match(/\{[\s\S]*\}|\[[\s\S]*\]/);
            if (jsonMatch) {
                const jsonStr = jsonMatch[0];
                const jsonObj = JSON.parse(jsonStr);
                const formatted = JSON.stringify(jsonObj, null, 2);
                return answer.replace(jsonStr, `<pre>${formatted}</pre>`);
            }
        } catch (e) {
            // Not valid JSON, return as is
        }
    }
    
    // Convert newlines to <br>
    return answer.replace(/\n/g, '<br>');
}

// Check API health on load
async function checkHealth() {
    try {
        const response = await fetch(`${API_BASE}/health`);
        const data = await response.json();
        console.log('Query Service Health:', data);
    } catch (error) {
        console.error('Query service not available:', error);
        alert('Warning: Query service is not running. Please start it with: python query_service.py');
    }
}

checkHealth();
