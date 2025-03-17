// Global variables to track state
let conversationId = null;
let settingsInitialized = false;
let currentSettings = {
    speechEnabled: window.speechEnabled || false,
    googleEnabled: window.googleEnabled || false,
    memoryEnabled: window.memoryEnabled || true,
    llmProvider: window.llmProvider || 'openai'
};

// Global variables
let currentConversationId = null;
let isListening = false;
let recognition = null;
let recognitionTimeout = null;
let voiceIndicator = null;

// Main app initialization
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, initializing app');
    
    // Initialize components
    setupChat();
    if (!settingsInitialized) {
        initializeSettings();
        setupSettingsPanel();
        setupMemoryBrowser();
        settingsInitialized = true;
    }
    
    // Setup voice toggle button
    setupVoiceToggle();
    
    // Setup end session button
    setupEndSessionButton();
    
    // Load existing conversation if available
    if (conversationId) {
        loadConversationHistory(conversationId);
    }
    
    // Setup speech recognition if enabled
    if (currentSettings.speechEnabled) {
        setupSpeechRecognition();
    }
});

// Setup chat functionality
function setupChat() {
    const sendButton = document.getElementById('send-btn');
    const messageInput = document.getElementById('message-input');
    const newChatButton = document.getElementById('new-chat-btn');
    
    if (sendButton && messageInput) {
        // Send message when Send button is clicked
        sendButton.addEventListener('click', function() {
            sendMessage();
        });
        
        // Send message when Enter key is pressed (but not with Shift)
        messageInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
        
        // Auto-resize textarea as user types
        messageInput.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = (this.scrollHeight) + 'px';
        });
    }
    
    if (newChatButton) {
        // Start new conversation when New Chat button is clicked
        newChatButton.addEventListener('click', function() {
            startNewConversation();
        });
    }
}

// Send message to server and display response
function sendMessage() {
    const messageInput = document.getElementById('message-input');
    const chatMessages = document.getElementById('chat-messages');
    const loadingOverlay = document.getElementById('loading-overlay');
    
    // Get user input and clear input field
    const userInput = messageInput.value.trim();
    if (!userInput) return; // Don't send empty messages
    
    messageInput.value = '';
    messageInput.style.height = 'auto'; // Reset height
    
    // Display user message
    const userMessageElement = document.createElement('div');
    userMessageElement.className = 'message user';
    userMessageElement.innerHTML = `
        <div class="message-content">
            <p>${formatMessage(userInput)}</p>
        </div>
    `;
    chatMessages.appendChild(userMessageElement);
    
    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    // Show loading
    if (loadingOverlay) loadingOverlay.classList.remove('hidden');
    
    // Stop listening while processing
    if (window.isListening && typeof window.stopListening === 'function') {
        window.stopListening();
    }
    
    // Send request to server
    fetch('/api/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            user_input: userInput,
            conversation_id: conversationId,
            speech_enabled: currentSettings.speechEnabled,
            google_enabled: currentSettings.googleEnabled,
            llm_provider: currentSettings.llmProvider,
            memory_enabled: currentSettings.memoryEnabled
        })
    })
    .then(response => response.json())
    .then(data => {
        // Hide loading
        if (loadingOverlay) loadingOverlay.classList.add('hidden');
        
        // Store conversation ID for future requests
        conversationId = data.conversation_id;
        
        // Display assistant message
        const assistantMessageElement = document.createElement('div');
        assistantMessageElement.className = 'message assistant';
        assistantMessageElement.innerHTML = `
            <div class="message-content">
                <p>${formatMessage(data.reply)}</p>
            </div>
        `;
        chatMessages.appendChild(assistantMessageElement);
        
        // Scroll to bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        // Speak the reply if speech is enabled
        if (currentSettings.speechEnabled && typeof window.speakText === 'function') {
            window.speakText(data.reply);
        }
        
        // Update any insights if available
        if (data.insights && data.insights.length > 0) {
            updateInsights(data.insights);
        }
        
        // Resume listening after response if it was active before
        if (currentSettings.speechEnabled && typeof window.startListening === 'function') {
            setTimeout(() => {
                window.startListening();
            }, 1000); // Small delay to avoid conflict with TTS
        }
    })
    .catch(error => {
        console.error('Error sending message:', error);
        
        // Hide loading
        if (loadingOverlay) loadingOverlay.classList.add('hidden');
        
        // Display error message
        const errorMessageElement = document.createElement('div');
        errorMessageElement.className = 'message assistant error';
        errorMessageElement.innerHTML = `
            <div class="message-content">
                <p>Sorry, there was an error processing your request. Please try again.</p>
            </div>
        `;
        chatMessages.appendChild(errorMessageElement);
        
        // Scroll to bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        // Resume listening if it was active
        if (currentSettings.speechEnabled && typeof window.startListening === 'function') {
            setTimeout(() => {
                window.startListening();
            }, 1000);
        }
    });
}

// Function to start a new conversation
function startNewConversation() {
    console.log('Starting new conversation');
    
    const chatMessages = document.getElementById('chat-messages');
    const loadingOverlay = document.getElementById('loading-overlay');
    
    // Clear existing messages
    if (chatMessages) {
        chatMessages.innerHTML = '';
    }
    
    // Show loading overlay
    if (loadingOverlay) {
        loadingOverlay.classList.remove('hidden');
    }
    
    // Clear conversation ID
    sessionStorage.removeItem('conversationId');
    
    // Get current settings
    const modelValue = document.getElementById('model-selector')?.value || 'gemini';
    const speechEnabled = document.getElementById('speech-toggle')?.checked || false;
    const googleEnabled = document.getElementById('google-toggle')?.checked || false;
    const memoryEnabled = document.getElementById('memory-toggle')?.checked || false;
    
    // Request a new conversation from the server
    fetch('/api/new_conversation', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            speech_enabled: speechEnabled,
            google_enabled: googleEnabled,
            memory_enabled: memoryEnabled,
            llm_provider: modelValue
        })
    })
    .then(response => response.json())
    .then(data => {
        console.log('New conversation:', data);
        
        // Hide loading overlay
        if (loadingOverlay) {
            loadingOverlay.classList.add('hidden');
        }
        
        // Add greeting message
        if (chatMessages) {
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message assistant';
            messageDiv.innerHTML = `
                <div class="message-content">
                    <p>${data.reply}</p>
                </div>
            `;
            chatMessages.appendChild(messageDiv);
        }
        
        // Store conversation ID
        if (data.conversation_id) {
            sessionStorage.setItem('conversationId', data.conversation_id);
        }
    })
    .catch(error => {
        console.error('Error starting new conversation:', error);
        
        // Hide loading overlay
        if (loadingOverlay) {
            loadingOverlay.classList.add('hidden');
        }
        
        // Add error message
        if (chatMessages) {
            const errorDiv = document.createElement('div');
            errorDiv.className = 'message assistant error';
            errorDiv.innerHTML = `
                <div class="message-content">
                    <p>I'm sorry, there was an error starting a new conversation. Please try again.</p>
                </div>
            `;
            chatMessages.appendChild(errorDiv);
        }
    });
}

// Setup settings panel functionality
function setupSettingsPanel() {
    const settingsToggle = document.getElementById('settings-toggle');
    const settingsPanel = document.getElementById('settings-panel');
    const settingsClose = document.getElementById('settings-close');
    
    console.log('Setting up settings panel', {settingsToggle, settingsPanel, settingsClose});
    
    if (settingsToggle && settingsPanel) {
        settingsToggle.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            console.log('Settings toggle clicked');
            
            // Force display toggle
            if (settingsPanel.style.display === 'none' || settingsPanel.style.display === '') {
                settingsPanel.style.display = 'block';
            } else {
                settingsPanel.style.display = 'none';
            }
        });
    }
    
    if (settingsClose && settingsPanel) {
        settingsClose.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            settingsPanel.style.display = 'none';
        });
    }
    
    // Close settings when clicking outside
    document.addEventListener('click', function(event) {
        if (settingsPanel && settingsPanel.style.display === 'block') {
            if (!settingsPanel.contains(event.target) && event.target !== settingsToggle) {
                settingsPanel.style.display = 'none';
            }
        }
    });
}

// Setup voice recognition toggle
function setupVoiceToggle() {
    const voiceToggle = document.getElementById('voice-toggle');
    
    if (voiceToggle) {
        console.log('Setting up voice toggle button');
        voiceToggle.addEventListener('click', function() {
            console.log('Voice toggle clicked, current state:', currentSettings.speechEnabled);
            
            // Toggle speech recognition
            if (currentSettings.speechEnabled) {
                console.log('Speech is enabled, toggling listening state');
                if (typeof window.toggleListening === 'function') {
                    window.toggleListening();
                } else {
                    console.warn('toggleListening function not available');
                    // Try to setup speech recognition again
                    setupSpeechRecognition();
                    if (typeof window.toggleListening === 'function') {
                        window.toggleListening();
                    }
                }
            } else {
                // Enable speech in settings first
                alert('Please enable Text-to-Speech in settings first');
                const settingsPanel = document.getElementById('settings-panel');
                if (settingsPanel) {
                    settingsPanel.style.display = 'block';
                }
            }
        });
    } else {
        console.warn('Voice toggle button not found');
    }
}

// Initialize speech recognition
function setupSpeechRecognition() {
    console.log('Setting up speech recognition');
    
    if (!window.SpeechRecognition && !window.webkitSpeechRecognition) {
        console.warn('Speech Recognition is not supported in this browser');
        return;
    }
    
    // Create SpeechRecognition instance if not already created
    if (!window.recognition) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        window.recognition = new SpeechRecognition();
        
        // Configure recognition
        window.recognition.continuous = true;
        window.recognition.interimResults = true;
        window.recognition.lang = 'en-US';
        
        console.log('Speech recognition object created');
    }
    
    // Set global variables
    window.isListening = false;
    
    // Pause threshold (seconds of silence before sending)
    const pauseThreshold = 2.0;
    let lastResult = '';
    let timer = null;
    
    // Setup event handlers
    window.recognition.onstart = function() {
        console.log('Speech recognition started');
        window.isListening = true;
        document.getElementById('voice-toggle').classList.add('active');
        
        const voiceIndicator = document.getElementById('voice-indicator');
        if (voiceIndicator) {
            voiceIndicator.classList.remove('hidden');
        }
    };
    
    window.recognition.onend = function() {
        console.log('Speech recognition ended');
        window.isListening = false;
        document.getElementById('voice-toggle').classList.remove('active');
        
        const voiceIndicator = document.getElementById('voice-indicator');
        if (voiceIndicator) {
            voiceIndicator.classList.add('hidden');
        }
    };
    
    window.recognition.onresult = function(event) {
        console.log('Speech recognition result received');
        let transcript = '';
        
        // Collect final results
        for (let i = event.resultIndex; i < event.results.length; i++) {
            if (event.results[i].isFinal) {
                transcript += event.results[i][0].transcript;
            }
        }
        
        if (transcript.trim() !== '') {
            console.log('Transcript:', transcript);
            
            // Update input field
            const messageInput = document.getElementById('message-input');
            if (messageInput) {
                messageInput.value = transcript;
                
                // Auto-resize the input field
                messageInput.style.height = 'auto';
                messageInput.style.height = messageInput.scrollHeight + 'px';
            }
            
            // Clear previous timer
            if (timer) {
                clearTimeout(timer);
            }
            
            // Set timer to send message after pause
            if (transcript !== lastResult) {
                lastResult = transcript;
                timer = setTimeout(function() {
                    if (transcript.trim() !== '') {
                        console.log('Sending message after pause:', transcript);
                        sendMessage();
                    }
                }, pauseThreshold * 1000);
            }
        }
    };
    
    window.recognition.onerror = function(event) {
        console.error('Speech recognition error:', event.error);
        window.isListening = false;
        
        const voiceIndicator = document.getElementById('voice-indicator');
        if (voiceIndicator) {
            voiceIndicator.classList.add('hidden');
        }
        
        document.getElementById('voice-toggle').classList.remove('active');
    };
    
    console.log('Speech recognition setup complete');
    
    // Define global functions for starting/stopping speech recognition
    window.startListening = function() {
        console.log('Starting speech recognition');
        if (!window.isListening) {
            try {
                window.recognition.start();
            } catch (e) {
                console.error('Error starting speech recognition:', e);
            }
        }
    };
    
    window.stopListening = function() {
        console.log('Stopping speech recognition');
        if (window.isListening) {
            try {
                window.recognition.stop();
            } catch (e) {
                console.error('Error stopping speech recognition:', e);
            }
        }
    };
    
    window.toggleListening = function() {
        console.log('Toggling speech recognition');
        if (window.isListening) {
            window.stopListening();
        } else {
            window.startListening();
        }
    };
    
    // Setup text-to-speech
    window.speakText = function(text) {
        console.log('Speaking text:', text.substring(0, 50) + '...');
        if (!currentSettings.speechEnabled) return;
        
        // Cancel any ongoing speech
        if ('speechSynthesis' in window) {
            window.speechSynthesis.cancel();
        }
        
        // Check if speech synthesis is supported
        if (!('speechSynthesis' in window)) {
            console.warn('Speech synthesis not supported in this browser');
            return;
        }
        
        // Create utterance
        const utterance = new SpeechSynthesisUtterance(text);
        
        // Configure utterance
        utterance.lang = 'en-US';
        utterance.rate = 1.0;
        utterance.pitch = 1.0;
        
        // Speak the text
        window.speechSynthesis.speak(utterance);
    };
}

// Setup End Session Button
function setupEndSessionButton() {
    const endSessionBtn = document.getElementById('end-session-btn');
    
    if (endSessionBtn) {
        console.log('Setting up end session button');
        endSessionBtn.addEventListener('click', function() {
            endSession();
        });
    }
}

// End the current session
function endSession() {
    console.log('Ending session');
    
    const chatMessages = document.getElementById('chat-messages');
    const loadingOverlay = document.getElementById('loading-overlay');
    
    // Show loading overlay
    if (loadingOverlay) {
        loadingOverlay.classList.remove('hidden');
    }
    
    // Get current conversation ID
    const conversationId = sessionStorage.getItem('conversationId');
    
    if (!conversationId) {
        // No active conversation
        if (loadingOverlay) {
            loadingOverlay.classList.add('hidden');
        }
        
        // Add goodbye message
        if (chatMessages) {
            const goodbyeDiv = document.createElement('div');
            goodbyeDiv.className = 'message system';
            goodbyeDiv.innerHTML = `
                <div class="message-content">
                    <p>Thank you for chatting with Bahá'í Life Coach. The session has ended. Feel free to start a new conversation anytime.</p>
                </div>
            `;
            chatMessages.appendChild(goodbyeDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
        return;
    }
    
    // Send session end request to server
    fetch('/api/end_session', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            conversation_id: conversationId
        })
    })
    .then(response => response.json())
    .then(data => {
        console.log('Session ended:', data);
        
        // Hide loading overlay
        if (loadingOverlay) {
            loadingOverlay.classList.add('hidden');
        }
        
        // Add goodbye message
        if (chatMessages) {
            const goodbyeDiv = document.createElement('div');
            goodbyeDiv.className = 'message system';
            goodbyeDiv.innerHTML = `
                <div class="message-content">
                    <p>Thank you for chatting with Bahá'í Life Coach. Your session has been saved. Feel free to start a new conversation anytime.</p>
                </div>
            `;
            chatMessages.appendChild(goodbyeDiv);
        }
        
        // Clear conversation ID
        sessionStorage.removeItem('conversationId');
        
        // Scroll to the bottom
        if (chatMessages) {
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
    })
    .catch(error => {
        console.error('Error ending session:', error);
        
        // Hide loading overlay
        if (loadingOverlay) {
            loadingOverlay.classList.add('hidden');
        }
        
        // Add error message
        if (chatMessages) {
            const errorDiv = document.createElement('div');
            errorDiv.className = 'message system error';
            errorDiv.innerHTML = `
                <div class="message-content">
                    <p>There was an error ending your session. Your conversation may not have been saved properly.</p>
                </div>
            `;
            chatMessages.appendChild(errorDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
    });
}

// Initialize settings from localStorage or window defaults
function initializeSettings() {
    console.log('Initializing settings');
    
    // Get references to all settings elements
    const modelSelector = document.getElementById('model-selector');
    const speechToggle = document.getElementById('speech-toggle');
    const googleToggle = document.getElementById('google-toggle');
    const memoryToggle = document.getElementById('memory-toggle');
    
    // Load settings from localStorage or use defaults from window
    currentSettings = {
        speechEnabled: localStorage.getItem('speechEnabled') === 'true' || window.speechEnabled || false,
        googleEnabled: localStorage.getItem('googleEnabled') === 'true' || window.googleEnabled || false,
        memoryEnabled: localStorage.getItem('memoryEnabled') === 'true' || window.memoryEnabled || true,
        llmProvider: localStorage.getItem('llmProvider') || window.llmProvider || 'openai'
    };
    
    console.log('Loaded settings:', currentSettings);
    
    // Set UI elements to match current settings
    if (modelSelector) {
        modelSelector.value = currentSettings.llmProvider;
        modelSelector.addEventListener('change', function() {
            currentSettings.llmProvider = this.value;
            localStorage.setItem('llmProvider', this.value);
            updateSettings();
        });
    }
    
    if (speechToggle) {
        speechToggle.checked = currentSettings.speechEnabled;
        speechToggle.addEventListener('change', function() {
            currentSettings.speechEnabled = this.checked;
            localStorage.setItem('speechEnabled', this.checked);
            updateSettings();
            
            // Initialize speech if enabled
            if (this.checked && typeof setupSpeechRecognition === 'function') {
                setupSpeechRecognition();
            }
        });
    }
    
    if (googleToggle) {
        googleToggle.checked = currentSettings.googleEnabled;
        googleToggle.addEventListener('change', function() {
            currentSettings.googleEnabled = this.checked;
            localStorage.setItem('googleEnabled', this.checked);
            updateSettings();
        });
    }
    
    if (memoryToggle) {
        memoryToggle.checked = currentSettings.memoryEnabled;
        memoryToggle.addEventListener('change', function() {
            currentSettings.memoryEnabled = this.checked;
            localStorage.setItem('memoryEnabled', this.checked);
            updateSettings();
        });
    }
    
    // Also initialize the voice toggle and memory buttons
    setupVoiceToggle();
    
    // Send initial settings to the server
    updateSettings();
}

// Send settings to server
function updateSettings() {
    console.log('Updating settings on server:', currentSettings);
    
    fetch('/api/settings', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(currentSettings)
    })
    .then(response => response.json())
    .then(data => {
        console.log('Settings updated successfully:', data);
    })
    .catch(error => {
        console.error('Error updating settings:', error);
    });
}

// Setup memory browser functionality
function setupMemoryBrowser() {
    const showMemoriesBtn = document.getElementById('show-memories');
    const createMemoryBtn = document.getElementById('create-memory');
    const memoryBrowser = document.getElementById('memory-browser');
    const closeMemoryBrowser = document.querySelector('.close-memory-browser');
    const memoryTabs = document.querySelectorAll('.memory-tab');
    const memoryModal = document.getElementById('memory-modal');
    const closeModal = document.querySelector('.close-modal');
    const saveMemoryBtn = document.getElementById('save-memory');
    const deleteMemoryBtn = document.getElementById('delete-memory');
    const searchMemoriesBtn = document.getElementById('search-memories');
    const memorySearchInput = document.getElementById('memory-search');
    
    console.log('Setting up memory browser', {
        showMemoriesBtn, 
        createMemoryBtn, 
        memoryBrowser, 
        closeMemoryBrowser
    });
    
    let currentMemoryId = null;
    let currentMemoryType = 'short';
    
    // Show memory browser
    if (showMemoriesBtn && memoryBrowser) {
        showMemoriesBtn.addEventListener('click', function() {
            console.log('Show memories clicked');
            memoryBrowser.style.display = 'flex';
            loadMemories(currentMemoryType);
        });
    }
    
    // Create memory button
    if (createMemoryBtn) {
        createMemoryBtn.addEventListener('click', function() {
            console.log('Create memory clicked');
            createShortTermMemory();
        });
    }
    
    // Close memory browser
    if (closeMemoryBrowser && memoryBrowser) {
        closeMemoryBrowser.addEventListener('click', function() {
            memoryBrowser.style.display = 'none';
        });
    }
    
    // Memory tabs
    if (memoryTabs) {
        memoryTabs.forEach(tab => {
            tab.addEventListener('click', function() {
                // Remove active class from all tabs
                memoryTabs.forEach(t => t.classList.remove('active'));
                // Add active class to clicked tab
                this.classList.add('active');
                // Update current memory type
                currentMemoryType = this.dataset.type;
                // Load memories for this type
                loadMemories(currentMemoryType);
            });
        });
    }
    
    // Close memory modal
    if (closeModal && memoryModal) {
        closeModal.addEventListener('click', function() {
            memoryModal.style.display = 'none';
        });
    }
    
    // Save memory changes
    if (saveMemoryBtn) {
        saveMemoryBtn.addEventListener('click', function() {
            if (!currentMemoryId) return;
            
            const content = document.getElementById('memory-content').value;
            
            console.log('Saving memory:', {id: currentMemoryId, content});
            
            // Send update to server
            fetch('/api/memories/' + currentMemoryId, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ content })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Close modal and reload memories
                    memoryModal.style.display = 'none';
                    loadMemories(currentMemoryType);
                } else {
                    console.error('Failed to update memory:', data.message);
                }
            })
            .catch(error => {
                console.error('Error updating memory:', error);
            });
        });
    }
    
    // Delete memory
    if (deleteMemoryBtn) {
        deleteMemoryBtn.addEventListener('click', function() {
            if (!currentMemoryId) return;
            
            if (confirm('Are you sure you want to delete this memory?')) {
                console.log('Deleting memory:', currentMemoryId);
                
                // Send delete request to server
                fetch('/api/memories/' + currentMemoryId, {
                    method: 'DELETE'
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Close modal and reload memories
                        memoryModal.style.display = 'none';
                        loadMemories(currentMemoryType);
                    } else {
                        console.error('Failed to delete memory:', data.message);
                    }
                })
                .catch(error => {
                    console.error('Error deleting memory:', error);
                });
            }
        });
    }
    
    // Search memories
    if (searchMemoriesBtn && memorySearchInput) {
        searchMemoriesBtn.addEventListener('click', function() {
            const query = memorySearchInput.value.trim();
            if (query) {
                searchMemories(query);
            } else {
                loadMemories(currentMemoryType);
            }
        });
        
        // Search on enter key
        memorySearchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                const query = this.value.trim();
                if (query) {
                    searchMemories(query);
                } else {
                    loadMemories(currentMemoryType);
                }
            }
        });
    }
}

// Load memories from server
function loadMemories(type = 'short') {
    const memoryList = document.getElementById('memory-list');
    const conversationId = sessionStorage.getItem('conversationId');
    
    if (!memoryList) {
        console.error('Memory list element not found');
        return;
    }
    
    if (!conversationId) {
        memoryList.innerHTML = '<div class="memory-empty">No active conversation. Start a chat to create memories.</div>';
        return;
    }
    
    // Show loading state
    memoryList.innerHTML = '<div class="memory-empty">Loading memories...</div>';
    
    console.log('Loading memories:', {type, conversationId});
    
    // Fetch memories from server
    fetch(`/api/memories?type=${type}&conversation_id=${conversationId}`)
        .then(response => response.json())
        .then(data => {
            console.log('Memories loaded:', data);
            
            if (data.memories && data.memories.length > 0) {
                // Render memories
                memoryList.innerHTML = '';
                data.memories.forEach(memory => {
                    const memoryItem = document.createElement('div');
                    memoryItem.className = 'memory-item';
                    memoryItem.dataset.id = memory.id;
                    memoryItem.dataset.type = memory.type;
                    memoryItem.dataset.created = memory.created_at;
                    memoryItem.dataset.content = memory.content;
                    
                    // Create memory preview
                    const title = document.createElement('div');
                    title.className = 'memory-item-title';
                    title.textContent = formatDate(memory.created_at);
                    
                    const preview = document.createElement('div');
                    preview.className = 'memory-item-preview';
                    preview.textContent = memory.content;
                    
                    memoryItem.appendChild(title);
                    memoryItem.appendChild(preview);
                    
                    // Add click event to open memory details
                    memoryItem.addEventListener('click', function() {
                        openMemoryDetails(this.dataset.id, this.dataset.type, this.dataset.created, this.dataset.content);
                    });
                    
                    memoryList.appendChild(memoryItem);
                });
            } else {
                // No memories found
                memoryList.innerHTML = '<div class="memory-empty">No memories found for this conversation.</div>';
            }
        })
        .catch(error => {
            console.error('Error loading memories:', error);
            memoryList.innerHTML = '<div class="memory-empty">Error loading memories. Please try again.</div>';
        });
}

// Search memories
function searchMemories(query) {
    const memoryList = document.getElementById('memory-list');
    const conversationId = sessionStorage.getItem('conversationId');
    
    if (!memoryList) {
        console.error('Memory list element not found');
        return;
    }
    
    if (!conversationId) {
        memoryList.innerHTML = '<div class="memory-empty">No active conversation. Start a chat to create memories.</div>';
        return;
    }
    
    // Show loading state
    memoryList.innerHTML = '<div class="memory-empty">Searching memories...</div>';
    
    console.log('Searching memories:', {query, conversationId});
    
    // Fetch memories from server with search query
    fetch(`/api/memories/search?query=${encodeURIComponent(query)}&conversation_id=${conversationId}`)
        .then(response => response.json())
        .then(data => {
            console.log('Search results:', data);
            
            if (data.memories && data.memories.length > 0) {
                // Render memories
                memoryList.innerHTML = '';
                data.memories.forEach(memory => {
                    const memoryItem = document.createElement('div');
                    memoryItem.className = 'memory-item';
                    memoryItem.dataset.id = memory.id;
                    memoryItem.dataset.type = memory.type;
                    memoryItem.dataset.created = memory.created_at;
                    memoryItem.dataset.content = memory.content;
                    
                    // Create memory preview
                    const title = document.createElement('div');
                    title.className = 'memory-item-title';
                    title.textContent = `${memory.type} - ${formatDate(memory.created_at)}`;
                    
                    const preview = document.createElement('div');
                    preview.className = 'memory-item-preview';
                    preview.textContent = memory.content;
                    
                    memoryItem.appendChild(title);
                    memoryItem.appendChild(preview);
                    
                    // Add click event to open memory details
                    memoryItem.addEventListener('click', function() {
                        openMemoryDetails(this.dataset.id, this.dataset.type, this.dataset.created, this.dataset.content);
                    });
                    
                    memoryList.appendChild(memoryItem);
                });
            } else {
                // No memories found
                memoryList.innerHTML = `<div class="memory-empty">No memories found matching "${query}".</div>`;
            }
        })
        .catch(error => {
            console.error('Error searching memories:', error);
            memoryList.innerHTML = '<div class="memory-empty">Error searching memories. Please try again.</div>';
        });
}

// Open memory details in modal
function openMemoryDetails(id, type, created, content) {
    const memoryModal = document.getElementById('memory-modal');
    const memoryType = document.getElementById('memory-type');
    const memoryCreated = document.getElementById('memory-created');
    const memoryContent = document.getElementById('memory-content');
    
    if (!memoryModal || !memoryType || !memoryCreated || !memoryContent) {
        console.error('Memory modal elements not found');
        return;
    }
    
    console.log('Opening memory details:', {id, type, created});
    
    // Set current memory ID (global variable)
    window.currentMemoryId = id;
    
    // Update modal content
    memoryType.textContent = type === 'short' ? 'Short-term' : type === 'mid' ? 'Mid-term' : 'Long-term';
    memoryCreated.textContent = formatDate(created);
    memoryContent.value = content;
    
    // Show modal
    memoryModal.style.display = 'block';
}

// Function to create a short-term memory manually
function createShortTermMemory() {
    const conversationId = sessionStorage.getItem('conversationId');
    
    if (!conversationId) {
        console.error('No active conversation');
        alert('Please start a conversation before creating a memory');
        return;
    }
    
    // Get chat messages
    const chatMessages = document.querySelectorAll('.message');
    if (chatMessages.length < 2) {
        console.error('Not enough messages to create a memory');
        alert('Please exchange at least one message to create a memory');
        return;
    }
    
    // Extract last few messages (up to 5)
    const recentMessages = [];
    const maxMessages = Math.min(chatMessages.length, 5);
    for (let i = chatMessages.length - maxMessages; i < chatMessages.length; i++) {
        const message = chatMessages[i];
        const role = message.classList.contains('user') ? 'user' : 'assistant';
        const content = message.querySelector('.message-content').textContent.trim();
        recentMessages.push({ role, content });
    }
    
    // Create a summary of the conversation (100 words max)
    const conversationText = recentMessages.map(msg => `${msg.role}: ${msg.content}`).join('\n');
    
    console.log('Creating memory:', {conversationId, conversationText});
    
    // Send request to create memory
    fetch('/api/memories', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            conversation_id: conversationId,
            content: conversationText,
            type: 'short'
        })
    })
    .then(response => response.json())
    .then(data => {
        console.log('Memory created:', data);
        
        if (data.success) {
            alert('Short-term memory created successfully!');
        } else {
            console.error('Failed to create memory:', data.message);
            alert('Failed to create memory: ' + (data.message || 'Unknown error'));
        }
    })
    .catch(error => {
        console.error('Error creating memory:', error);
        alert('Error creating memory. Please try again.');
    });
}

// Format date for display
function formatDate(dateString) {
    try {
        const date = new Date(dateString);
        return date.toLocaleString();
    } catch (e) {
        console.error('Error formatting date:', e);
        return dateString || 'Unknown date';
    }
}

// Format message for display
function formatMessage(message) {
    // Implement your formatting logic here
    return message;
}

// Format date for display
function formatDate(dateString) {
    try {
        const date = new Date(dateString);
        return date.toLocaleString();
    } catch (e) {
        console.error('Error formatting date:', e);
        return dateString || 'Unknown date';
    }
} 