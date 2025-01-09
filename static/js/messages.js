// Utility functions
function escapeHtml(unsafe) {
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function formatDate(isoString) {
    const date = new Date(isoString);
    return new Intl.DateTimeFormat('default', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    }).format(date);
}

// Message display
function displayMessage(message) {
    const messageElement = document.createElement('div');
    messageElement.className = 'message';
    messageElement.innerHTML = `
        <div class="message-content">${escapeHtml(message.content)}</div>
        <div class="message-footer">
            <span class="author">${escapeHtml(message.author)}</span>
            <span class="timestamp">${formatDate(message.timestamp)}</span>
            ${message.repository !== 'local' ? 
                `<span class="repository">${escapeHtml(message.repository)}</span>` : 
                ''}
            ${message.github_url ? 
                `<a href="${escapeHtml(message.github_url)}" target="_blank">View on GitHub</a>` : 
                ''}
        </div>
    `;
    return messageElement;
}

// Error handling
function showError(message, autoDismiss = true) {
    const errorElement = document.getElementById('error-message');
    errorElement.textContent = message;
    errorElement.style.display = 'block';

    if (autoDismiss) {
        setTimeout(() => {
            errorElement.style.display = 'none';
        }, 5000);
    }
}

// Message fetching
async function fetchAndDisplayMessages() {
    try {
        const response = await fetch('/messages?limit=100');
        if (!response.ok) {
            throw new Error('Failed to fetch messages');
        }

        const data = await response.json();
        const messagesContainer = document.getElementById('messages');
        messagesContainer.innerHTML = '';

        data.messages.forEach(message => {
            messagesContainer.appendChild(displayMessage(message));
        });
    } catch (error) {
        showError('Error loading messages');
        console.error('Error:', error);
    }
}

// Form submission
async function handleSubmit(event) {
    event.preventDefault();
    
    const submitButton = document.getElementById('submit-button');
    const messageInput = document.getElementById('message');
    const authorInput = document.getElementById('author');
    const repositoryInput = document.getElementById('repository');

    // Validate input
    if (!messageInput.value.trim()) {
        showError('Message cannot be empty');
        return;
    }

    // Disable submit button
    submitButton.disabled = true;
    submitButton.textContent = 'Submitting...';

    try {
        const response = await fetch('/messages', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: messageInput.value.trim(),
                author: authorInput.value.trim() || 'Anonymous',
                repository: repositoryInput.value.trim() || 'local'
            }),
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.message || 'Failed to post message');
        }

        // Clear form
        messageInput.value = '';
        authorInput.value = '';
        repositoryInput.value = '';

        // Refresh messages
        await fetchAndDisplayMessages();
    } catch (error) {
        showError(error.message);
        console.error('Error:', error);
    } finally {
        // Re-enable submit button
        submitButton.disabled = false;
        submitButton.textContent = 'Submit';
    }
}

// Auto-refresh
function startAutoRefresh() {
    setInterval(async () => {
        try {
            await fetchAndDisplayMessages();
        } catch (error) {
            console.error('Error refreshing messages:', error);
        }
    }, 30000);
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('message-form');
    form.addEventListener('submit', handleSubmit);

    fetchAndDisplayMessages();
    startAutoRefresh();
});
