// State management
let tickets = [];
let selectedTicketId = null;
let currentFilters = {
    status: 'all',
    priority: 'all',
    sort: 'newest'
};

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    initializeEventListeners();
    loadTickets();
    loadStats();
});

// Event listeners
function initializeEventListeners() {
    // New ticket modal
    document.getElementById('btn-new-ticket').addEventListener('click', openNewTicketModal);
    document.getElementById('btn-cancel').addEventListener('click', closeNewTicketModal);
    document.getElementById('new-ticket-form').addEventListener('submit', handleCreateTicket);

    // Close modal on outside click
    document.getElementById('modal-backdrop').addEventListener('click', (e) => {
        if (e.target.id === 'modal-backdrop') {
            closeNewTicketModal();
        }
    });

    // Filters
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', handleStatusFilter);
    });
    // Priority filter and sort are not in the current HTML, so commenting out
    // document.getElementById('priorityFilter').addEventListener('change', handlePriorityFilter);
    // document.getElementById('sortOrder').addEventListener('change', handleSortChange);
}

// API calls
async function loadTickets() {
    try {
        const statusParam = currentFilters.status !== 'all' ? `?status=${currentFilters.status}` : '';
        const response = await fetch(`/api/tickets${statusParam}`);
        
        if (!response.ok) {
            throw new Error(`Failed to load tickets: ${response.statusText}`);
        }
        
        tickets = await response.json();
        applyFiltersAndSort();
        renderTicketList();
        loadStats();
    } catch (error) {
        showError('Failed to load tickets. Please refresh the page.');
        console.error('Error loading tickets:', error);
    }
}

async function createTicket(ticketData) {
    try {
        const response = await fetch('/api/tickets', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(ticketData)
        });
        
        if (!response.ok) {
            throw new Error(`Failed to create ticket: ${response.statusText}`);
        }
        
        await loadTickets();
        closeNewTicketModal();
    } catch (error) {
        showError('Failed to create ticket. Please try again.');
        console.error('Error creating ticket:', error);
    }
}

async function updateTicketStatus(ticketId, status) {
    try {
        const response = await fetch(`/api/tickets/${ticketId}/status`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ status })
        });
        
        if (!response.ok) {
            throw new Error(`Failed to update status: ${response.statusText}`);
        }
        
        await loadTickets();
        if (selectedTicketId === ticketId) {
            await loadTicketDetail(ticketId);
        }
    } catch (error) {
        showError('Failed to update ticket status. Please try again.');
        console.error('Error updating status:', error);
    }
}

async function loadTicketDetail(ticketId) {
    try {
        const ticket = tickets.find(t => t.ticket_id === ticketId);
        if (!ticket) {
            throw new Error('Ticket not found');
        }
        
        const response = await fetch(`/api/tickets/${ticketId}/messages`);
        if (!response.ok) {
            throw new Error(`Failed to load messages: ${response.statusText}`);
        }
        
        const messages = await response.json();
        selectedTicketId = ticketId;
        renderTicketDetail(ticket, messages);
    } catch (error) {
        showError('Failed to load ticket details. Please try again.');
        console.error('Error loading ticket detail:', error);
    }
}

async function addMessage(ticketId, messageText, author) {
    try {
        const response = await fetch(`/api/tickets/${ticketId}/messages`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message_text: messageText, author })
        });
        
        if (!response.ok) {
            throw new Error(`Failed to add message: ${response.statusText}`);
        }
        
        await loadTicketDetail(ticketId);
    } catch (error) {
        showError('Failed to add message. Please try again.');
        console.error('Error adding message:', error);
    }
}

async function deleteTicket(ticketId) {
    if (!confirm('Are you sure you want to delete this ticket? This action cannot be undone.')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/tickets/${ticketId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            throw new Error(`Failed to delete ticket: ${response.statusText}`);
        }
        
        if (selectedTicketId === ticketId) {
            selectedTicketId = null;
            document.getElementById('detail').innerHTML = '<div class="empty-state"><p>Select a ticket to view details</p></div>';
        }
        await loadTickets();
    } catch (error) {
        showError('Failed to delete ticket. Please try again.');
        console.error('Error deleting ticket:', error);
    }
}

// Filtering and sorting
function applyFiltersAndSort() {
    let filtered = [...tickets];
    
    // Priority filter
    if (currentFilters.priority !== 'all') {
        filtered = filtered.filter(t => t.priority === currentFilters.priority);
    }
    
    // Sort
    filtered.sort((a, b) => {
        const dateA = new Date(a.created_at);
        const dateB = new Date(b.created_at);
        return currentFilters.sort === 'newest' ? dateB - dateA : dateA - dateB;
    });
    
    tickets = filtered;
}

function handleStatusFilter(e) {
    const status = e.target.dataset.status || 'all';
    currentFilters.status = status;
    
    // Update active button
    document.querySelectorAll('.filter-btn').forEach(btn => btn.classList.remove('active'));
    e.target.classList.add('active');
    
    loadTickets();
}

function handlePriorityFilter(e) {
    currentFilters.priority = e.target.value;
    applyFiltersAndSort();
    renderTicketList();
}

function handleSortChange(e) {
    currentFilters.sort = e.target.value;
    applyFiltersAndSort();
    renderTicketList();
}

// Rendering functions
function renderTicketList() {
    const listContainer = document.getElementById('ticket-list');
    
    if (tickets.length === 0) {
        listContainer.innerHTML = '<div class="empty-state"><p>No tickets found</p></div>';
        return;
    }
    
    listContainer.innerHTML = tickets.map(ticket => createTicketCard(ticket)).join('');
    
    // Add click listeners
    document.querySelectorAll('.ticket-card').forEach(card => {
        card.addEventListener('click', () => {
            const ticketId = parseInt(card.dataset.ticketId);
            loadTicketDetail(ticketId);
            
            // Update active state
            document.querySelectorAll('.ticket-card').forEach(c => c.classList.remove('active'));
            card.classList.add('active');
        });
    });
}

function createTicketCard(ticket) {
    const messageCount = ticket.message_count || 0;
    const statusClass = getStatusClass(ticket.status);
    const priorityIcon = getPriorityIcon(ticket.priority);
    
    return `
        <div class="ticket-card ${selectedTicketId === ticket.ticket_id ? 'active' : ''}" data-ticket-id="${ticket.ticket_id}">
            <div class="ticket-card-header">
                <h3>${escapeHtml(ticket.title)}</h3>
                <span class="status-badge ${statusClass}">${formatStatus(ticket.status)}</span>
            </div>
            <div class="ticket-card-meta">
                <span class="priority ${ticket.priority}">${priorityIcon} ${capitalizeFirst(ticket.priority)}</span>
                <span class="message-count">💬 ${messageCount}</span>
            </div>
        </div>
    `;
}

function renderTicketDetail(ticket, messages) {
    const detailContainer = document.getElementById('detail');
    const createdDate = formatDate(ticket.created_at);
    
    detailContainer.innerHTML = `
        <div class="ticket-detail-header">
            <div>
                <h2>${escapeHtml(ticket.title)}</h2>
                <div class="ticket-meta">
                    <span>Created by ${escapeHtml(ticket.created_by)}</span>
                    <span>•</span>
                    <span>${createdDate}</span>
                    ${ticket.category ? `<span>•</span><span>${escapeHtml(ticket.category)}</span>` : ''}
                </div>
            </div>
            <button class="btn btn-danger" onclick="deleteTicket(${ticket.ticket_id})">Delete</button>
        </div>
        
        <div class="ticket-detail-info">
            <div class="info-item">
                <label>Status:</label>
                <select class="status-select" onchange="updateTicketStatus(${ticket.ticket_id}, this.value)">
                    <option value="open" ${ticket.status === 'open' ? 'selected' : ''}>Open</option>
                    <option value="in_progress" ${ticket.status === 'in_progress' ? 'selected' : ''}>In Progress</option>
                    <option value="resolved" ${ticket.status === 'resolved' ? 'selected' : ''}>Resolved</option>
                </select>
            </div>
            <div class="info-item">
                <label>Priority:</label>
                <span class="priority ${ticket.priority}">${getPriorityIcon(ticket.priority)} ${capitalizeFirst(ticket.priority)}</span>
            </div>
        </div>
        
        <div class="messages-section">
            <h3>Messages</h3>
            <div class="messages-list">
                ${messages.length > 0 ? messages.map(msg => createMessageItem(msg)).join('') : '<p class="no-messages">No messages yet</p>'}
            </div>
            
            <div class="message-input">
                <input type="text" id="messageText" placeholder="Type your message..." />
                <input type="text" id="messageAuthor" placeholder="Your name" />
                <button class="btn btn-primary" onclick="handleAddMessage(${ticket.ticket_id})">Send</button>
            </div>
        </div>
    `;
}

function createMessageItem(message) {
    const messageDate = formatDate(message.created_at);
    return `
        <div class="message-item">
            <div class="message-header">
                <strong>${escapeHtml(message.author)}</strong>
                <span class="message-date">${messageDate}</span>
            </div>
            <div class="message-text">${escapeHtml(message.message_text)}</div>
        </div>
    `;
}

// Event handlers
function openNewTicketModal() {
    document.getElementById('modal-backdrop').style.display = 'flex';
    document.getElementById('new-ticket-form').reset();
}

function closeNewTicketModal() {
    document.getElementById('modal-backdrop').style.display = 'none';
}

async function handleCreateTicket(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const ticketData = {
        title: formData.get('title'),
        created_by: formData.get('created_by'),
        priority: formData.get('priority'),
        category: formData.get('category') || null
    };
    
    await createTicket(ticketData);
}

async function handleAddMessage(ticketId) {
    const messageText = document.getElementById('messageText').value.trim();
    const author = document.getElementById('messageAuthor').value.trim();
    
    if (!messageText || !author) {
        showError('Please enter both message and your name.');
        return;
    }
    
    await addMessage(ticketId, messageText, author);
    document.getElementById('messageText').value = '';
    document.getElementById('messageAuthor').value = '';
}

// Stats
async function loadStats() {
    try {
        const response = await fetch('/api/stats');
        if (!response.ok) {
            throw new Error('Failed to load stats');
        }
        const data = await response.json();
        
        document.getElementById('stat-total').textContent = data.total || 0;
        document.getElementById('stat-open').textContent = data.by_status.open || 0;
        document.getElementById('stat-in_progress').textContent = data.by_status.in_progress || 0;
        document.getElementById('stat-resolved').textContent = data.by_status.resolved || 0;
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

// Utility functions
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function getStatusClass(status) {
    const classes = {
        'open': 'status-open',
        'in_progress': 'status-in-progress',
        'resolved': 'status-resolved'
    };
    return classes[status] || '';
}

function formatStatus(status) {
    return status.split('_').map(word => capitalizeFirst(word)).join(' ');
}

function getPriorityIcon(priority) {
    const icons = {
        'high': '🔴',
        'medium': '🟡',
        'low': '🟢'
    };
    return icons[priority] || '';
}

function capitalizeFirst(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
}

function formatDate(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now - date;
    
    // Less than a minute
    if (diff < 60000) {
        return 'Just now';
    }
    
    // Less than an hour
    if (diff < 3600000) {
        const mins = Math.floor(diff / 60000);
        return `${mins} minute${mins > 1 ? 's' : ''} ago`;
    }
    
    // Less than a day
    if (diff < 86400000) {
        const hours = Math.floor(diff / 3600000);
        return `${hours} hour${hours > 1 ? 's' : ''} ago`;
    }
    
    // Format as date
    return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined,
        hour: '2-digit',
        minute: '2-digit'
    });
}

function showError(message) {
    const errorDiv = document.getElementById('form-error');
    if (errorDiv) {
        errorDiv.textContent = message;
    } else {
        console.error(message);
        alert(message);
    }
}