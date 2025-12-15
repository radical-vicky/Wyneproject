class ChatManager {
    constructor(conversationId, otherUserId) {
        this.conversationId = conversationId;
        this.otherUserId = otherUserId;
        this.messagesContainer = document.getElementById('messages-container');
        this.messageForm = document.getElementById('message-form');
        this.messageInput = document.getElementById('message-input');
        this.sendBtn = document.getElementById('send-btn');
        this.typingIndicator = document.getElementById('typing-indicator');
        this.isTyping = false;
        this.typingTimeout = null;
        this.pollInterval = null;
        this.lastMessageId = 0;
        this.csrfToken = this.getCsrfToken();
        
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.scrollToBottom();
        this.startPolling();
    }
    
    bindEvents() {
        // Form submission
        this.messageForm.addEventListener('submit', (e) => this.handleSubmit(e));
        
        // Typing detection
        this.messageInput.addEventListener('input', () => this.handleTyping());
        
        // Enter key to send (Shift+Enter for new line)
        this.messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.messageForm.requestSubmit();
            }
        });
        
        // Auto-resize textarea
        this.messageInput.addEventListener('input', () => this.autoResize());
        
        // Focus on input
        this.messageInput.focus();
    }
    
    async handleSubmit(e) {
        e.preventDefault();
        
        const formData = new FormData(this.messageForm);
        const message = this.messageInput.value.trim();
        
        // Reset typing indicator
        this.resetTypingIndicator();
        
        if (!message && !formData.has('media_file')) {
            return;
        }
        
        // Disable send button
        this.sendBtn.disabled = true;
        this.sendBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
        
        try {
            const response = await fetch('', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': this.csrfToken,
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Clear input and reset form
                this.messageInput.value = '';
                this.messageForm.reset();
                this.autoResize();
                
                // Add message to UI
                this.addMessage(data.message, true);
                
                // Update last message ID
                this.lastMessageId = data.message.id;
                
                // Scroll to bottom
                this.scrollToBottom();
            } else {
                console.error('Failed to send message:', data.errors);
                alert('Failed to send message. Please try again.');
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Failed to send message. Please check your connection.');
        } finally {
            // Re-enable send button
            this.sendBtn.disabled = false;
            this.sendBtn.innerHTML = '<i class="fas fa-paper-plane"></i>';
        }
    }
    
    handleTyping() {
        if (!this.isTyping) {
            this.isTyping = true;
            this.sendTypingIndicator(true);
        }
        
        clearTimeout(this.typingTimeout);
        this.typingTimeout = setTimeout(() => {
            this.isTyping = false;
            this.sendTypingIndicator(false);
        }, 1000);
    }
    
    sendTypingIndicator(isTyping) {
        // Send typing indicator via WebSocket or polling
        fetch('/api/typing-indicator/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.csrfToken,
            },
            body: JSON.stringify({
                conversation_id: this.conversationId,
                is_typing: isTyping,
            })
        });
    }
    
    resetTypingIndicator() {
        clearTimeout(this.typingTimeout);
        this.isTyping = false;
        this.sendTypingIndicator(false);
    }
    
    async fetchNewMessages() {
        try {
            const response = await fetch(`/api/conversation/${this.conversationId}/messages/?last_id=${this.lastMessageId}`);
            const data = await response.json();
            
            if (data.messages && data.messages.length > 0) {
                data.messages.forEach(message => {
                    this.addMessage(message, false);
                    this.lastMessageId = Math.max(this.lastMessageId, message.id);
                });
                
                // Scroll to bottom if we were near the bottom
                const isNearBottom = this.messagesContainer.scrollHeight - this.messagesContainer.scrollTop <= this.messagesContainer.clientHeight + 100;
                if (isNearBottom) {
                    this.scrollToBottom();
                }
            }
            
            // Update typing indicator
            if (data.typing && data.typing[this.otherUserId]) {
                this.showTypingIndicator();
            } else {
                this.hideTypingIndicator();
            }
            
        } catch (error) {
            console.error('Error fetching messages:', error);
        }
    }
    
    startPolling() {
        this.pollInterval = setInterval(() => this.fetchNewMessages(), 2000);
    }
    
    stopPolling() {
        if (this.pollInterval) {
            clearInterval(this.pollInterval);
        }
    }
    
    addMessage(message, isSent = false) {
        const messageRow = document.createElement('div');
        messageRow.className = 'message-row';
        messageRow.dataset.messageId = message.id;
        
        const messageBubble = document.createElement('div');
        messageBubble.className = `message-bubble ${isSent ? 'sent' : 'received'}`;
        
        const sentAt = new Date(message.sent_at);
        const timeString = sentAt.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        
        let contentHTML = '';
        
        if (message.media_url) {
            if (message.message_type === 'image') {
                contentHTML = `
                    <div class="message-media">
                        <img src="${message.media_url}" onclick="openImageModal('${message.media_url}')" loading="lazy">
                    </div>
                `;
            } else if (message.message_type === 'video') {
                contentHTML = `
                    <div class="message-media">
                        <video controls>
                            <source src="${message.media_url}" type="video/mp4">
                        </video>
                    </div>
                `;
            } else if (message.message_type === 'audio') {
                contentHTML = `
                    <div class="message-media">
                        <audio controls>
                            <source src="${message.media_url}" type="audio/mpeg">
                        </audio>
                    </div>
                `;
            }
        }
        
        if (message.content) {
            contentHTML += `<div class="message-content">${this.escapeHtml(message.content).replace(/\n/g, '<br>')}</div>`;
        }
        
        contentHTML += `
            <div class="message-footer">
                <span class="message-time">${timeString}</span>
                ${isSent ? `<span class="message-status ${message.is_read ? 'read' : ''}">
                    <i class="fas ${message.is_read ? 'fa-check-double' : 'fa-check'}"></i>
                </span>` : ''}
            </div>
        `;
        
        messageBubble.innerHTML = contentHTML;
        messageRow.appendChild(messageBubble);
        this.messagesContainer.appendChild(messageRow);
        
        // Add animation
        messageRow.style.animation = 'fadeIn 0.3s ease-out';
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    showTypingIndicator() {
        this.typingIndicator.style.display = 'block';
    }
    
    hideTypingIndicator() {
        this.typingIndicator.style.display = 'none';
    }
    
    autoResize() {
        this.messageInput.style.height = 'auto';
        this.messageInput.style.height = Math.min(this.messageInput.scrollHeight, 120) + 'px';
    }
    
    scrollToBottom() {
        this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
    }
    
    getCsrfToken() {
        const cookieValue = document.cookie
            .split('; ')
            .find(row => row.startsWith('csrftoken='))
            ?.split('=')[1];
        
        return cookieValue || document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    }
    
    destroy() {
        this.stopPolling();
        this.messageForm.removeEventListener('submit', this.handleSubmit);
    }
}