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
const REACTIONS = [
    { emoji: '👍', name: 'thumbs_up' },
    { emoji: '❤️', name: 'heart' },
    { emoji: '😄', name: 'smile' },
    { emoji: '🎉', name: 'party' }
];

function displayMessage(message) {
    const messageElement = document.createElement('div');
    messageElement.className = 'message';
    
    const reactionsHtml = REACTIONS.map(reaction => {
        const count = (message.reactions && message.reactions[reaction.name]) || 0;
        return `
            <button class="reaction-button" 
                    data-reaction="${reaction.name}" 
                    data-message-id="${message.id}">
                <span class="reaction-emoji">${reaction.emoji}</span>
                <span class="reaction-count">${count}</span>
            </button>
        `;
    }).join('');

    messageElement.innerHTML = `
        <div class="message-content">${escapeHtml(message.content)}</div>
        <div class="reactions">${reactionsHtml}</div>
        <div class="message-footer">
            <span>${escapeHtml(message.author)}</span>
            <span>${formatDate(message.timestamp)}</span>
        </div>
    `;

    messageElement.querySelectorAll('.reaction-button').forEach(button => {
        button.addEventListener('click', handleReaction);
    });

    return messageElement;
}

async function handleReaction(event) {
    event.preventDefault();
    const button = event.currentTarget;
    const messageId = button.dataset.messageId;
    const reaction = button.dataset.reaction;

    try {
        const response = await fetch(`/messages/${messageId}/reactions`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                reaction: reaction,
                action: 'add'
            })
        });

        if (response.ok) {
            // Refresh messages to show updated reaction counts
            await fetchAndDisplayMessages();
        }
    } catch (error) {
        console.error('Error handling reaction:', error);
        showError('Failed to update reaction');
    }
}

function showError(message, autoDismiss = true) {
    const errorElement = document.getElementById('error-message');
    if (errorElement) {
        errorElement.textContent = message;
        errorElement.style.display = 'block';

        if (autoDismiss) {
            setTimeout(() => {
                errorElement.style.display = 'none';
            }, 5000);
        }
    }
}

async function fetchAndDisplayMessages() {
    try {
        console.log('Fetching messages...');
        const response = await fetch('/messages');
        console.log('Response:', response);
        
        if (!response.ok) {
            throw new Error('Failed to fetch messages');
        }

        const data = await response.json();
        console.log('Received data:', data);

        const messagesContainer = document.getElementById('messages');
        if (!messagesContainer) {
            console.error('Messages container not found');
            return;
        }

        messagesContainer.innerHTML = '';

        if (data.status === 'success' && Array.isArray(data.messages)) {
            console.log('Displaying messages:', data.messages);
            data.messages.forEach(message => {
                messagesContainer.appendChild(displayMessage(message));
            });
        } else {
            console.error('Invalid data structure:', data);
            throw new Error('Invalid response format');
        }
    } catch (error) {
        console.error('Error fetching messages:', error);
        showError('Failed to load messages');
    }
}

async function handleSubmit(event) {
    event.preventDefault();
    console.log('Form submitted');
    
    const form = event.target;
    const submitButton = form.querySelector('button[type="submit"]');
    const messageInput = form.querySelector('#message');
    const authorInput = form.querySelector('#author');
    const repositoryInput = form.querySelector('#repository');

    if (!messageInput || !submitButton) {
        console.error('Required form elements not found');
        return;
    }

    const messageText = messageInput.value.trim();
    if (!messageText) {
        showError('Message cannot be empty');
        return;
    }

    console.log('Sending message:', {
        message: messageText,
        author: authorInput ? authorInput.value.trim() : 'Anonymous',
        repository: repositoryInput ? repositoryInput.value.trim() : 'local'
    });

    submitButton.disabled = true;
    submitButton.textContent = 'Sending...';

    try {
        const response = await fetch('/messages', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: messageText,
                author: (authorInput ? authorInput.value.trim() : '') || 'Anonymous',
                repository: (repositoryInput ? repositoryInput.value.trim() : '') || 'local'
            }),
        });

        console.log('Server response:', response);
        if (!response.ok) {
            const errorData = await response.json();
            console.error('Server error:', errorData);
            throw new Error(errorData.message || 'Failed to send message');
        }

        // Clear form
        messageInput.value = '';
        if (authorInput) authorInput.value = '';
        if (repositoryInput) repositoryInput.value = '';

        // Refresh messages
        await fetchAndDisplayMessages();
    } catch (error) {
        console.error('Error sending message:', error);
        showError(error.message || 'Failed to send message');
    } finally {
        submitButton.disabled = false;
        submitButton.textContent = 'Submit';
    }
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    console.log('Initializing chat application...');
    const form = document.getElementById('message-form');
    const messageInput = document.getElementById('message');
    const charCount = document.getElementById('char-count');
    
    console.log('Form elements:', { form, messageInput, charCount });
    
    if (messageInput && charCount) {
        messageInput.addEventListener('input', () => {
            const count = messageInput.value.length;
            charCount.textContent = `${count}/280`;
            charCount.style.color = count > 280 ? '#ef4444' : 'rgba(74, 59, 59, 0.6)';
        });
    }

    if (form) {
        form.addEventListener('submit', handleSubmit);
    } else {
        console.error('Message form not found');
    }

    // Initial load
    fetchAndDisplayMessages();

    // Auto-refresh every 30 seconds
    setInterval(fetchAndDisplayMessages, 30000);
});
