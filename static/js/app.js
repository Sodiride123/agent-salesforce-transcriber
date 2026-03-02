// Application State
const state = {
    currentPage: 'chat',
    reports: [],
    mediaFiles: [],
    selectedFile: null,
    sessionId: null
};

// Generate or retrieve session ID
function getSessionId() {
    let sessionId = localStorage.getItem('salesiq_session_id');
    if (!sessionId) {
        sessionId = generateUUID();
        localStorage.setItem('salesiq_session_id', sessionId);
        console.log('[SESSION] Created new session:', sessionId);
    } else {
        console.log('[SESSION] Retrieved existing session:', sessionId);
    }
    return sessionId;
}

// Generate UUID for session ID
function generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        const r = Math.random() * 16 | 0;
        const v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    state.sessionId = getSessionId();
    initializeNavigation();
    initializeChat();
    loadReports();
    loadMediaLibrary();
    updateContextIndicator(0);
});

// Navigation
function initializeNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        item.addEventListener('click', () => {
            const page = item.dataset.page;
            switchPage(page);
        });
    });
}

function switchPage(page) {
    // Update navigation
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });
    document.querySelector(`[data-page="${page}"]`).classList.add('active');
    
    // Update content
    document.querySelectorAll('.page').forEach(p => {
        p.classList.remove('active');
    });
    document.getElementById(`${page}-page`).classList.add('active');
    
    // Update header
    const headers = {
        'chat': 'SalesIQ Chat Assistant',
        'reports': 'Sales Call Reports',
        'media': 'Media Library'
    };
    document.querySelector('.content-header h2').textContent = headers[page];
    
    state.currentPage = page;
    
    // Reload data if needed
    if (page === 'reports') {
        loadReports();
    } else if (page === 'media') {
        loadMediaLibrary();
    }
}

// Chat functionality
function initializeChat() {
    const chatForm = document.getElementById('chatForm');
    const audioFileInput = document.getElementById('audioFile');
    const uploadLabel = document.querySelector('.upload-label');
    const selectedFileDiv = document.getElementById('selectedFile');
    
    // File selection
    audioFileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            const file = e.target.files[0];
            state.selectedFile = file;
            selectedFileDiv.textContent = `Selected: ${file.name}`;
            selectedFileDiv.style.display = 'block';
        }
    });
    
    // Chat form submission
    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const messageInput = document.getElementById('messageInput');
        const message = messageInput.value.trim();
        
        if (!message && !state.selectedFile) return;
        
        // If there's a file, upload it
        if (state.selectedFile) {
            await uploadAudioFile(state.selectedFile);
            state.selectedFile = null;
            audioFileInput.value = '';
            selectedFileDiv.style.display = 'none';
        }
        
        // If there's a message, send it
        if (message) {
            addMessageToChat('user', message);
            messageInput.value = '';
            
            // Send to backend
            await sendChatMessage(message);
        }
    });
}

function addMessageToChat(sender, text) {
    const messagesContainer = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;
    
    const avatar = sender === 'user' 
        ? 'U' 
        : '<img src="/static/images/salesiq-avatar.png" alt="SalesIQ">';
    
    // For assistant messages, render markdown. For user messages, escape HTML.
    let content;
    if (sender === 'assistant' && typeof marked !== 'undefined') {
        // Configure marked for better formatting
        marked.setOptions({
            breaks: true,  // Convert \n to <br>
            gfm: true,     // GitHub Flavored Markdown
            headerIds: false,
            mangle: false
        });
        content = marked.parse(text);
    } else {
        content = escapeHtml(text).replace(/\n/g, '<br>');
    }
    
    messageDiv.innerHTML = `
        <div class="message-avatar">${avatar}</div>
        <div class="message-content">${content}</div>
    `;
    
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function showTypingIndicator() {
    const messagesContainer = document.getElementById('chatMessages');
    const typingDiv = document.createElement('div');
    typingDiv.className = 'message assistant typing-indicator';
    typingDiv.id = 'typingIndicator';
    
    typingDiv.innerHTML = `
        <div class="message-avatar">
            <img src="/static/images/salesiq-avatar.png" alt="SalesIQ">
        </div>
        <div class="message-content">
            <div class="typing-dots">
                <span></span>
                <span></span>
                <span></span>
            </div>
        </div>
    `;
    
    messagesContainer.appendChild(typingDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function hideTypingIndicator() {
    const typingIndicator = document.getElementById('typingIndicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }
}

async function sendChatMessage(message) {
    try {
        // Show typing indicator
        showTypingIndicator();
        
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                message: message,
                session_id: state.sessionId
            })
        });
        
        const data = await response.json();
        
        // Hide typing indicator
        hideTypingIndicator();
        
        // Update context indicator if provided
        if (data.num_reports !== undefined) {
            updateContextIndicator(data.num_reports);
        }
        
        addMessageToChat('assistant', data.message);
    } catch (error) {
        console.error('Error sending message:', error);
        hideTypingIndicator();
        addMessageToChat('assistant', 'Sorry, I encountered an error. Please try again.');
    }
}

async function uploadAudioFile(file) {
    const formData = new FormData();
    formData.append('audio', file);
    formData.append('session_id', state.sessionId);
    
    addMessageToChat('user', `Uploading audio file: ${file.name}`);
    
    // Show typing indicator for processing
    showTypingIndicator();
    
    try {
        const response = await fetch('/api/upload-audio', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        // Hide typing indicator
        hideTypingIndicator();
        
        if (data.success) {
            addMessageToChat('assistant', `✅ Success! Audio processed successfully!\n\n${data.message}\n\nYou now have ${data.num_reports_in_context} call(s) in context. Ask me anything about the call!`);
            
            // Update context indicator
            updateContextIndicator(data.num_reports_in_context);
            
            // Reload reports if on reports page
            if (state.currentPage === 'reports') {
                loadReports();
            }
        } else {
            addMessageToChat('assistant', `Error: Failed to process audio - ${data.error}`);
        }
    } catch (error) {
        console.error('Error uploading audio:', error);
        hideTypingIndicator();
        addMessageToChat('assistant', 'Error: Failed to upload audio file. Please try again.');
    }
}

// Reports functionality
async function loadReports() {
    try {
        const response = await fetch('/api/reports');
        const reports = await response.json();
        state.reports = reports;
        displayReports(reports);
    } catch (error) {
        console.error('Error loading reports:', error);
    }
}

function displayReports(reports) {
    const container = document.getElementById('reportsContainer');
    
    if (reports.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">
                    <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" style="width: 64px; height: 64px; fill: #cbd5e1;">
                        <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zM9 17H7v-7h2v7zm4 0h-2V7h2v10zm4 0h-2v-4h2v4z"/>
                    </svg>
                </div>
                <h3>No reports yet</h3>
                <p>Upload audio files in the chat to generate reports</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = reports.map(report => `
        <div class="report-card" onclick="viewReport('${report.id}')">
            <div class="report-card-header">
                <div>
                    <h3>${escapeHtml(report.title || report.filename)}</h3>
                    <div class="report-date">${formatDate(report.created_at)}</div>
                </div>
            </div>
            <div class="report-summary">${escapeHtml(report.summary)}</div>
            <div class="report-actions">
                <button class="btn btn-small btn-primary" onclick="event.stopPropagation(); viewReport('${report.id}')">
                    View Details
                </button>
                <button class="btn btn-small btn-danger" onclick="event.stopPropagation(); deleteReport('${report.id}')">
                    Delete
                </button>
            </div>
        </div>
    `).join('');
}

async function viewReport(reportId) {
    try {
        const response = await fetch(`/api/reports/${reportId}`);
        const report = await response.json();
        showReportModal(report);
    } catch (error) {
        console.error('Error loading report:', error);
    }
}

function showReportModal(report) {
    const modal = document.getElementById('reportModal');
    const modalBody = document.getElementById('reportModalBody');
    
    modalBody.innerHTML = `
        <div class="report-detail">
            <h2>${escapeHtml(report.title || report.filename)}</h2>
            <div class="report-date" style="margin-bottom: 30px;">${formatDate(report.created_at)}</div>
            
            <div class="report-section">
                <h3>Summary</h3>
                <p>${escapeHtml(report.analysis.summary)}</p>
            </div>
            
            <div class="report-section">
                <h3>Key Points</h3>
                <ul>
                    ${report.analysis.key_points.map(point => `<li>${escapeHtml(point)}</li>`).join('')}
                </ul>
            </div>
            
            <div class="report-section">
                <h3>Sentiment Analysis</h3>
                <p><strong>Overall Sentiment:</strong> ${escapeHtml(report.analysis.sentiment)}</p>
            </div>
            
            <div class="report-section">
                <h3>Action Items</h3>
                <ul>
                    ${report.analysis.action_items.map(item => `<li>${escapeHtml(item)}</li>`).join('')}
                </ul>
            </div>
            
            <div class="report-section">
                <h3>Customer Needs</h3>
                <ul>
                    ${report.analysis.customer_needs.map(need => `<li>${escapeHtml(need)}</li>`).join('')}
                </ul>
            </div>
            
            <div class="report-section">
                <h3>Next Steps</h3>
                <p>${escapeHtml(report.analysis.next_steps)}</p>
            </div>
            
            <!-- Salesforce Actions Section -->
            <div class="report-section salesforce-section">
                <h3>
                    <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" style="width: 24px; height: 24px; fill: #00A1E0; vertical-align: middle; margin-right: 8px;">
                        <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                    </svg>
                    Salesforce Actions
                </h3>
                
                <!-- Account Search -->
                <div class="salesforce-subsection">
                    <label for="accountSearch">Link to Salesforce Account:</label>
                    <div style="display: flex; gap: 10px; margin-top: 8px;">
                        <input type="text" id="accountSearch" placeholder="Search for account..." style="flex: 1;">
                        <button class="btn btn-small" onclick="searchAccounts('${report.id}')">Search</button>
                    </div>
                    <div id="accountResults" style="margin-top: 10px;"></div>
                    <div id="selectedAccount" style="margin-top: 10px; display: none;">
                        <strong>Selected Account:</strong> <span id="selectedAccountName"></span>
                        <button class="btn btn-small" onclick="clearSelectedAccount()" style="margin-left: 10px;">Clear</button>
                    </div>
                </div>
                
                <!-- Create Tasks -->
                <div class="salesforce-subsection">
                    <h4>Create Tasks from Action Items</h4>
                    <p style="color: #64748b; font-size: 14px; margin-bottom: 10px;">
                        Select action items to create as Salesforce tasks:
                    </p>
                    <div id="actionItemsCheckboxes">
                        ${report.analysis.action_items.map((item, index) => `
                            <label style="display: block; margin-bottom: 8px; cursor: pointer;">
                                <input type="checkbox" class="action-item-checkbox" value="${escapeHtml(item)}" checked>
                                ${escapeHtml(item)}
                            </label>
                        `).join('')}
                    </div>
                    <button class="btn" onclick="createTasksFromReport('${report.id}')" style="margin-top: 10px;">
                        Create Selected Tasks
                    </button>
                </div>
                
                <!-- Update Account -->
                <div class="salesforce-subsection">
                    <h4>Update Account Information</h4>
                    <p style="color: #64748b; font-size: 14px; margin-bottom: 10px;">
                        Add customer needs to account notes:
                    </p>
                    <textarea id="accountNotes" rows="4" style="width: 100%; padding: 10px; border: 1px solid #e2e8f0; border-radius: 8px; font-family: inherit; box-sizing: border-box; resize: vertical;">${(report.analysis.customer_needs || []).map(need => `• ${need}`).join('\n') || 'No customer needs identified'}</textarea>
                    <button class="btn" onclick="updateAccountFromReport('${report.id}')" style="margin-top: 10px;">
                        Update Account
                    </button>
                </div>
                
                <div id="salesforceStatus" style="margin-top: 15px;"></div>
            </div>
            
            <div class="report-section">
                <h3>Full Transcription</h3>
                <div class="transcription-text">${escapeHtml(report.transcription)}</div>
            </div>
        </div>
    `;
    
    modal.classList.add('active');
}

function closeReportModal() {
    document.getElementById('reportModal').classList.remove('active');
}

async function deleteReport(reportId) {
    if (!confirm('Are you sure you want to delete this report?')) return;

    // Optimistic UI: immediately remove from DOM and state
    state.reports = state.reports.filter(r => r.id !== reportId);
    displayReports(state.reports);

    try {
        const response = await fetch(`/api/reports/${reportId}`, {
            method: 'DELETE'
        });

        if (!response.ok) {
            // If failed, reload to restore
            loadReports();
        }
    } catch (error) {
        console.error('Error deleting report:', error);
        loadReports();
    }
}

// Media Library functionality
async function loadMediaLibrary() {
    try {
        const response = await fetch('/api/media');
        const mediaFiles = await response.json();
        state.mediaFiles = mediaFiles;
        displayMediaLibrary(mediaFiles);
    } catch (error) {
        console.error('Error loading media library:', error);
    }
}

function displayMediaLibrary(mediaFiles) {
    const container = document.getElementById('mediaContainer');
    
    if (mediaFiles.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">
                    <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" style="width: 64px; height: 64px; fill: #cbd5e1;">
                        <path d="M12 3v9.28c-.47-.17-.97-.28-1.5-.28C8.01 12 6 14.01 6 16.5S8.01 21 10.5 21c2.31 0 4.2-1.75 4.45-4H15V6h4V3h-7z"/>
                    </svg>
                </div>
                <h3>No media files yet</h3>
                <p>Upload audio files in the chat to see them here</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = mediaFiles.map(file => `
        <div class="media-card">
            <div class="media-icon">
                <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" style="width: 32px; height: 32px; fill: white;">
                    <path d="M12 3v9.28c-.47-.17-.97-.28-1.5-.28C8.01 12 6 14.01 6 16.5S8.01 21 10.5 21c2.31 0 4.2-1.75 4.45-4H15V6h4V3h-7z"/>
                </svg>
            </div>
            <div class="media-info">
                <h3>${escapeHtml(file.filename)}</h3>
                <div class="media-meta">
                    Size: ${formatFileSize(file.size)}<br>
                    Uploaded: ${formatDate(file.created_at)}
                </div>
            </div>
            <div class="media-actions">
                <button class="btn btn-small btn-danger" onclick="deleteMedia(\`${file.filename}\`)">
                    Delete
                </button>
            </div>
        </div>
    `).join('');
}

async function deleteMedia(filename) {
    if (!confirm('Are you sure you want to delete this media file?')) return;

    // Optimistic UI: immediately remove from DOM and state
    state.mediaFiles = state.mediaFiles.filter(f => f.filename !== filename);
    displayMediaLibrary(state.mediaFiles);

    try {
        const response = await fetch(`/api/media/${encodeURIComponent(filename)}`, {
            method: 'DELETE'
        });

        if (!response.ok) {
            loadMediaLibrary();
        }
    } catch (error) {
        console.error('Error deleting media:', error);
        loadMediaLibrary();
    }
}

// Utility functions
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
}

// Salesforce Actions Functions
let selectedAccountId = null;
let selectedAccountName = null;

async function searchAccounts(reportId) {
    const searchInput = document.getElementById('accountSearch');
    const query = searchInput.value.trim();
    const resultsDiv = document.getElementById('accountResults');
    
    if (!query) {
        resultsDiv.innerHTML = '<p style="color: #ef4444;">Please enter a search term</p>';
        return;
    }
    
    resultsDiv.innerHTML = '<p style="color: #64748b;">Searching...</p>';
    
    try {
        const response = await fetch(`/api/salesforce/search-accounts?query=${encodeURIComponent(query)}`);
        const data = await response.json();
        
        // Check for Salesforce session errors
        if (data.error && data.error.includes('Session expired')) {
            resultsDiv.innerHTML = `
                <div style="padding: 15px; background: #fef3c7; border: 1px solid #fbbf24; border-radius: 8px;">
                    <p style="color: #92400e; margin: 0; font-weight: 500;">⚠️ Salesforce Session Expired</p>
                    <p style="color: #92400e; margin: 10px 0 0 0; font-size: 14px;">
                        Please reconnect to Salesforce to use this feature. For demo purposes, you can manually enter an Account ID below.
                    </p>
                    <div style="margin-top: 10px;">
                        <input type="text" id="manualAccountId" placeholder="Enter Account ID (e.g., 001...)" 
                               style="width: 100%; padding: 8px; border: 1px solid #fbbf24; border-radius: 4px;">
                        <button onclick="useManualAccountId()" class="btn btn-small" style="margin-top: 8px;">Use This Account</button>
                    </div>
                </div>
            `;
            return;
        }
        
        if (data.success === false) {
            resultsDiv.innerHTML = `<p style="color: #ef4444;">Error: ${escapeHtml(data.error)}</p>`;
            return;
        }
        
        // Handle different response formats
        const accounts = data.records || data.accounts || data.result || data;
        
        if (!accounts || !Array.isArray(accounts) || accounts.length === 0) {
            resultsDiv.innerHTML = '<p style="color: #64748b;">No accounts found</p>';
            return;
        }
        
        resultsDiv.innerHTML = `
            <div style="max-height: 200px; overflow-y: auto; border: 1px solid #e2e8f0; border-radius: 8px; padding: 10px;">
                ${accounts.map(account => `
                    <div class="account-result" onclick="selectAccount('${account.accountId || account.Id}', '${escapeHtml(account.name || account.Name)}')" 
                         style="padding: 10px; cursor: pointer; border-bottom: 1px solid #e2e8f0; transition: background 0.2s;">
                        <strong>${escapeHtml(account.name || account.Name)}</strong>
                        ${(account.industry || account.Industry) ? `<br><small style="color: #64748b;">${escapeHtml(account.industry || account.Industry)}</small>` : ''}
                    </div>
                `).join('')}
            </div>
        `;
        
        // Add hover effect
        document.querySelectorAll('.account-result').forEach(el => {
            el.addEventListener('mouseenter', () => el.style.background = '#f1f5f9');
            el.addEventListener('mouseleave', () => el.style.background = 'transparent');
        });
        
    } catch (error) {
        console.error('Error searching accounts:', error);
        resultsDiv.innerHTML = `<p style="color: #ef4444;">Error searching accounts: ${escapeHtml(error.message)}</p>`;
    }
}

function useManualAccountId() {
    const accountId = document.getElementById('manualAccountId').value.trim();
    if (accountId) {
        selectAccount(accountId, `Account (${accountId})`);
        document.getElementById('accountResults').innerHTML = '';
    }
}

function selectAccount(accountId, accountName) {
    selectedAccountId = accountId;
    selectedAccountName = accountName;
    
    document.getElementById('accountResults').innerHTML = '';
    document.getElementById('accountSearch').value = '';
    
    const selectedDiv = document.getElementById('selectedAccount');
    document.getElementById('selectedAccountName').textContent = accountName;
    selectedDiv.style.display = 'block';
}

function clearSelectedAccount() {
    selectedAccountId = null;
    selectedAccountName = null;
    document.getElementById('selectedAccount').style.display = 'none';
}

async function createTasksFromReport(reportId) {
    const statusDiv = document.getElementById('salesforceStatus');
    
    if (!selectedAccountId) {
        statusDiv.innerHTML = '<p style="color: #ef4444;">Please select a Salesforce account first</p>';
        return;
    }
    
    // Get selected action items
    const checkboxes = document.querySelectorAll('.action-item-checkbox:checked');
    const selectedItems = Array.from(checkboxes).map(cb => cb.value);
    
    if (selectedItems.length === 0) {
        statusDiv.innerHTML = '<p style="color: #ef4444;">Please select at least one action item</p>';
        return;
    }
    
    statusDiv.innerHTML = '<p style="color: #3b82f6;">Creating tasks...</p>';
    
    try {
        const response = await fetch('/api/salesforce/create-tasks', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                action_items: selectedItems,
                account_id: selectedAccountId
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            statusDiv.innerHTML = `
                <p style="color: #10b981;">
                    ✓ Successfully created ${data.created_tasks.length} task(s) in Salesforce!
                </p>
            `;
        } else {
            statusDiv.innerHTML = `<p style="color: #ef4444;">Error creating tasks: ${escapeHtml(JSON.stringify(data.errors))}</p>`;
        }
        
    } catch (error) {
        console.error('Error creating tasks:', error);
        statusDiv.innerHTML = `<p style="color: #ef4444;">Error: ${escapeHtml(error.message)}</p>`;
    }
}



async function updateAccountFromReport(reportId) {
    const statusDiv = document.getElementById('salesforceStatus');
    
    if (!selectedAccountId) {
        statusDiv.innerHTML = '<p style="color: #ef4444;">Please select a Salesforce account first</p>';
        return;
    }
    
    const notes = document.getElementById('accountNotes').value.trim();
    
    if (!notes) {
        statusDiv.innerHTML = '<p style="color: #ef4444;">Please enter notes to update the account</p>';
        return;
    }
    
    statusDiv.innerHTML = '<p style="color: #3b82f6;">Updating account...</p>';
    
    try {
        const response = await fetch('/api/salesforce/update-account', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                account_id: selectedAccountId,
                updates: {
                    Description: notes
                }
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            statusDiv.innerHTML = `
                <p style="color: #10b981;">
                    ✓ Successfully updated account information in Salesforce!
                </p>
            `;
        } else {
            statusDiv.innerHTML = `<p style="color: #ef4444;">Error updating account: ${escapeHtml(data.error)}</p>`;
        }
        
    } catch (error) {
        console.error('Error updating account:', error);
        statusDiv.innerHTML = `<p style="color: #ef4444;">Error: ${escapeHtml(error.message)}</p>`;
    }
}



// Context Indicator
function updateContextIndicator(numReports) {
    const indicator = document.getElementById('contextIndicator');
    if (!indicator) {
        // Create indicator if it doesn't exist
        const chatHeader = document.querySelector('.chat-header');
        if (chatHeader) {
            const indicatorDiv = document.createElement('div');
            indicatorDiv.id = 'contextIndicator';
            indicatorDiv.className = 'context-indicator';
            chatHeader.appendChild(indicatorDiv);
        }
    }
    
    const indicatorElement = document.getElementById('contextIndicator');
    if (indicatorElement) {
        if (numReports > 0) {
            indicatorElement.innerHTML = `📄 ${numReports} call${numReports > 1 ? 's' : ''} in context`;
            indicatorElement.style.display = 'block';
        } else {
            indicatorElement.style.display = 'none';
        }
    }
}

// New Session
async function showNewSessionModal() {
    closeMobileMenu();

    const modal = document.getElementById('newSessionModal');
    const filesSection = document.getElementById('existingFilesSection');
    const filesList = document.getElementById('existingFilesList');

    // Fetch latest media files
    try {
        const response = await fetch('/api/media');
        const mediaFiles = await response.json();

        if (mediaFiles.length > 0) {
            filesSection.style.display = 'block';
            filesList.innerHTML = mediaFiles.map(file => `
                <label class="existing-file-item" onclick="this.querySelector('input').checked = true; document.querySelectorAll('.existing-file-item').forEach(el => el.classList.remove('selected')); this.classList.add('selected');">
                    <input type="radio" name="existingFile" value="${escapeHtml(file.filename)}">
                    <div class="file-details">
                        <div class="file-name">${escapeHtml(file.filename)}</div>
                        <div class="file-meta">${formatFileSize(file.size)} &middot; ${formatDate(file.created_at)}</div>
                    </div>
                </label>
            `).join('');
        } else {
            filesSection.style.display = 'none';
            filesList.innerHTML = '';
        }
    } catch (error) {
        console.error('Error loading media files:', error);
        filesSection.style.display = 'none';
    }

    modal.classList.add('active');
}

function closeNewSessionModal() {
    document.getElementById('newSessionModal').classList.remove('active');
}

async function confirmNewSession() {
    // Check if a file was selected
    const selectedRadio = document.querySelector('input[name="existingFile"]:checked');
    const selectedFilename = selectedRadio ? selectedRadio.value : null;

    closeNewSessionModal();

    // Generate new session ID
    const newSessionId = generateUUID();
    localStorage.setItem('salesiq_session_id', newSessionId);
    state.sessionId = newSessionId;
    console.log('[SESSION] Started new session:', newSessionId);

    // Clear chat messages (keep the welcome message)
    const messagesContainer = document.getElementById('chatMessages');
    messagesContainer.innerHTML = `
        <div class="message assistant">
            <div class="message-avatar">
                <img src="/static/images/salesiq-avatar.png" alt="SalesIQ">
            </div>
            <div class="message-content">
                <strong>Welcome to SalesIQ!</strong> I'm your AI sales assistant. I can help you analyze sales calls by:
                <br><br>
                • Transcribing audio recordings<br>
                • Identifying key discussion points<br>
                • Analyzing customer sentiment<br>
                • Extracting action items<br>
                • Providing strategic insights<br>
                <br>
                Upload an MP3 file of your sales call to get started, or ask me anything about sales analysis!
            </div>
        </div>
    `;

    // Reset context indicator
    updateContextIndicator(0);

    // Reset file selection
    state.selectedFile = null;
    const audioFileInput = document.getElementById('audioFile');
    if (audioFileInput) audioFileInput.value = '';
    const selectedFileDiv = document.getElementById('selectedFile');
    if (selectedFileDiv) selectedFileDiv.style.display = 'none';

    // Switch to chat page
    switchPage('chat');

    // If user selected an existing file, re-upload it to the new session
    if (selectedFilename) {
        addMessageToChat('user', `Re-analyzing existing file: ${selectedFilename}`);
        showTypingIndicator();

        try {
            // Fetch the file from media library and re-upload to new session
            const fileResponse = await fetch(`/api/media/${encodeURIComponent(selectedFilename)}/download`);
            if (fileResponse.ok) {
                const blob = await fileResponse.blob();
                const formData = new FormData();
                formData.append('audio', blob, selectedFilename);
                formData.append('session_id', state.sessionId);

                const uploadResponse = await fetch('/api/upload-audio', {
                    method: 'POST',
                    body: formData
                });

                const data = await uploadResponse.json();
                hideTypingIndicator();

                if (data.success) {
                    addMessageToChat('assistant', `Audio processed successfully!\n\n${data.message}\n\nYou now have ${data.num_reports_in_context} call(s) in context. Ask me anything about the call!`);
                    updateContextIndicator(data.num_reports_in_context);
                } else {
                    addMessageToChat('assistant', `Error: Failed to process audio - ${data.error}`);
                }
            } else {
                hideTypingIndicator();
                addMessageToChat('assistant', 'Error: Could not retrieve the selected audio file.');
            }
        } catch (error) {
            console.error('Error re-uploading file:', error);
            hideTypingIndicator();
            addMessageToChat('assistant', 'Error: Failed to process the selected audio file.');
        }
    }
}

// Mobile Menu Toggle
function toggleMobileMenu() {
    const nav = document.getElementById('leftNav');
    const overlay = document.getElementById('navOverlay');
    nav.classList.toggle('open');
    overlay.classList.toggle('active');
}

function closeMobileMenu() {
    const nav = document.getElementById('leftNav');
    const overlay = document.getElementById('navOverlay');
    if (nav) nav.classList.remove('open');
    if (overlay) overlay.classList.remove('active');
}

// Close mobile menu when a nav item is clicked
document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', closeMobileMenu);
});

// Close modals when clicking outside
document.addEventListener('click', (e) => {
    const reportModal = document.getElementById('reportModal');
    if (e.target === reportModal) {
        closeReportModal();
    }
    const newSessionModal = document.getElementById('newSessionModal');
    if (e.target === newSessionModal) {
        closeNewSessionModal();
    }
});