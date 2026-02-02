const API_BASE = 'http://localhost:8001';

// DOM Elements
const fileInput = document.getElementById('fileInput');
const uploadArea = document.getElementById('uploadArea');
const uploadBtn = document.getElementById('uploadBtn');
const statusSection = document.getElementById('statusSection');
const resultsSection = document.getElementById('resultsSection');
const validationSection = document.getElementById('validationSection');

let selectedFile = null;
let currentDocId = null;

// File Upload Handlers
uploadArea.addEventListener('click', () => fileInput.click());

fileInput.addEventListener('change', (e) => {
    handleFileSelect(e.target.files[0]);
});

uploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadArea.classList.add('dragover');
});

uploadArea.addEventListener('dragleave', () => {
    uploadArea.classList.remove('dragover');
});

uploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadArea.classList.remove('dragover');
    handleFileSelect(e.dataTransfer.files[0]);
});

function handleFileSelect(file) {
    if (!file) return;
    
    const validTypes = ['.pdf', '.docx', '.xlsx', '.png', '.jpg', '.jpeg'];
    const fileExt = '.' + file.name.split('.').pop().toLowerCase();
    
    if (!validTypes.includes(fileExt)) {
        alert('Invalid file type. Please upload PDF, DOCX, XLSX, PNG, or JPG files.');
        return;
    }
    
    selectedFile = file;
    uploadArea.classList.add('has-file');
    uploadArea.innerHTML = `
        <div class="file-info">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"></path>
                <polyline points="13 2 13 9 20 9"></polyline>
            </svg>
            <span>${file.name}</span>
        </div>
    `;
    uploadBtn.disabled = false;
}

// Upload and Process
uploadBtn.addEventListener('click', async () => {
    if (!selectedFile) return;
    
    uploadBtn.disabled = true;
    uploadBtn.textContent = 'Uploading...';
    
    try {
        // Upload
        const formData = new FormData();
        formData.append('file', selectedFile);
        
        const uploadResponse = await fetch(`${API_BASE}/documents/upload`, {
            method: 'POST',
            body: formData
        });
        
        if (!uploadResponse.ok) throw new Error('Upload failed');
        
        const uploadData = await uploadResponse.json();
        currentDocId = uploadData.document_id;
        
        // Show status section
        statusSection.style.display = 'block';
        document.getElementById('docId').textContent = currentDocId;
        document.getElementById('status').textContent = 'Processing';
        document.getElementById('status').className = 'value badge processing';
        document.getElementById('stage').textContent = 'Uploading...';
        document.getElementById('progressFill').style.width = '25%';
        
        uploadBtn.textContent = 'Processing...';
        
        // Process
        const processResponse = await fetch(`${API_BASE}/documents/process/${currentDocId}`, {
            method: 'POST'
        });
        
        if (!processResponse.ok) throw new Error('Processing failed');
        
        const processData = await processResponse.json();
        
        // Update status
        document.getElementById('status').textContent = processData.status;
        document.getElementById('status').className = `value badge ${processData.status}`;
        document.getElementById('stage').textContent = processData.current_stage || 'Complete';
        document.getElementById('progressFill').style.width = '100%';
        
        // Show results
        if (processData.structured_data) {
            displayResults(processData.structured_data);
        }
        
        // Show validation
        if (processData.validation_result) {
            displayValidation(processData.validation_result);
        }
        
        uploadBtn.textContent = 'Upload & Process';
        uploadBtn.disabled = false;
        
    } catch (error) {
        console.error('Error:', error);
        alert('Error processing document: ' + error.message);
        uploadBtn.textContent = 'Upload & Process';
        uploadBtn.disabled = false;
    }
});

function displayResults(data) {
    resultsSection.style.display = 'block';
    
    const resultsContent = document.getElementById('resultsContent');
    resultsContent.innerHTML = `
        <div class="result-item">
            <span class="label">Vendor</span>
            <span class="value">${data.vendor || 'N/A'}</span>
        </div>
        <div class="result-item">
            <span class="label">Invoice Number</span>
            <span class="value">${data.invoice_number || 'N/A'}</span>
        </div>
        <div class="result-item">
            <span class="label">Invoice Date</span>
            <span class="value">${data.invoice_date || 'N/A'}</span>
        </div>
        <div class="result-item">
            <span class="label">Subtotal</span>
            <span class="value">${data.currency || ''} ${data.subtotal || 'N/A'}</span>
        </div>
        <div class="result-item">
            <span class="label">Tax</span>
            <span class="value">${data.currency || ''} ${data.tax || 'N/A'}</span>
        </div>
        <div class="result-item">
            <span class="label">Total</span>
            <span class="value">${data.currency || ''} ${data.total || 'N/A'}</span>
        </div>
    `;
    
    // Add line items if available
    if (data.line_items && data.line_items.length > 0) {
        const lineItemsHtml = data.line_items.map((item, idx) => `
            <div class="result-item">
                <span class="label">Item ${idx + 1}</span>
                <span class="value">${item.description || 'N/A'} (${item.quantity || 0} × ${item.unit_price || 0})</span>
            </div>
        `).join('');
        resultsContent.innerHTML += lineItemsHtml;
    }
}

function displayValidation(validation) {
    validationSection.style.display = 'block';
    
    const validationContent = document.getElementById('validationContent');
    
    const overallHtml = `
        <div class="validation-rule ${validation.overall_status.toLowerCase()}">
            <span class="validation-icon">${getStatusIcon(validation.overall_status)}</span>
            <div class="validation-text">
                <span class="rule-name">Overall Status: ${validation.overall_status}</span>
                <span class="rule-message">
                    ${validation.rules_passed || 0} passed, 
                    ${validation.rules_failed || 0} failed, 
                    ${validation.rules_review || 0} need review
                </span>
            </div>
        </div>
    `;
    
    const rulesHtml = (validation.validation_results || []).map(rule => `
        <div class="validation-rule ${rule.status.toLowerCase()}">
            <span class="validation-icon">${getStatusIcon(rule.status)}</span>
            <div class="validation-text">
                <span class="rule-name">${formatRuleName(rule.rule)}</span>
                <span class="rule-message">${rule.message}</span>
            </div>
        </div>
    `).join('');
    
    validationContent.innerHTML = overallHtml + rulesHtml;
}

function getStatusIcon(status) {
    const icons = {
        'PASS': '✓',
        'FAIL': '✗',
        'NEEDS_REVIEW': '⚠',
        'pass': '✓',
        'fail': '✗',
        'review': '⚠'
    };
    return icons[status] || '•';
}

function formatRuleName(rule) {
    return rule.split('_').map(word => 
        word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ');
}

// Check API health on load
async function checkHealth() {
    try {
        const response = await fetch(`${API_BASE}/health`);
        const data = await response.json();
        console.log('API Health:', data);
    } catch (error) {
        console.error('API not available:', error);
        alert('Warning: API server is not running. Please start it with: python api.py');
    }
}

checkHealth();
