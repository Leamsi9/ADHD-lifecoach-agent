/**
 * Bahá'í Life Coach - Main JavaScript
 * Handles core application functionality, UI interactions, and API communication
 */

document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-btn');
    const chatMessages = document.getElementById('chat-messages');
    const newChatButton = document.getElementById('new-chat-btn');
    const voiceToggleButton = document.getElementById('voice-toggle');
    const loadingOverlay = document.getElementById('loading-overlay');
    const sidebar = document.querySelector('.sidebar');
    const sidebarToggleBtn = document.getElementById('sidebar-toggle-btn');
    const closeSidebarBtn = document.querySelector('.close-btn');
    const googleToggle = document.getElementById('google-toggle');
    const speechToggle = document.getElementById('speech-toggle');
    const speechSettings = document.querySelector('.speech-settings');
    const rateSlider = document.getElementById('rate');
    const rateValue = document.getElementById('rate-value');
    const pitchSlider = document.getElementById('pitch');
    const pitchValue = document.getElementById('pitch-value');
    const memorySearchInput = document.getElementById('memory-search-input');
    const memorySearchBtn = document.getElementById('memory-search-btn');
    const memoriesContent = document.getElementById('memories-content');
    const insightsContent = document.getElementById('insights-content');

    // Application state
    let conversationId = null;
    let isVoiceModeActive = false;
    let speechManager = null;

    // Initialize speech functionality if enabled
    if (typeof speechEnabled !== 'undefined' && speechEnabled) {
        speechManager = new SpeechManager({
            enabled: speechEnabled,
            pauseThreshold: speechPauseThreshold,
            rate: speechRate,
            pitch: speechPitch
        });

        // Initialize speech recognition and synthesis
        if (speechManager.initialize()) {
            speechManager.onTranscript = handleTranscript;
        }
    }

    // Initialize UI based on settings
    function initializeUI() {
        // Set up textarea auto-resize
        messageInput.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = (this.scrollHeight) + 'px';
        });

        // Update UI for speech settings
        if (speechToggle.checked) {
            speechSettings.style.display = 'block';
        } else {
            speechSettings.style.display = 'none';
        }

        // Set up speech toggle
        if (speechManager) {
            if (speechToggle.checked) {
                voiceToggleButton.innerHTML = '<i class="fas fa-microphone"></i>';
            } else {
                voiceToggleButton.innerHTML = '<i class="fas fa-microphone-slash"></i>';
            }
        } else {
            voiceToggleButton.style.display = 'none';
        }
    }

    // Event listeners
    function setupEventListeners() {
        // Sidebar toggle
        sidebarToggleBtn.addEventListener('click', function() {
            sidebar.classList.add('active');
        });

        closeSidebarBtn.addEventListener('click', function() {
            sidebar.classList.remove('active');
        });

        // Click outside sidebar to close
        document.addEventListener('click', function(event) {
            if (sidebar.classList.contains('active') && 
                !sidebar.contains(event.target) && 
                !sidebarToggleBtn.contains(event.target)) {
                sidebar.classList.remove('active');
            }
        });

        // Send message on button click
        sendButton.addEventListener('click', sendMessage);

        // Send message on Enter key (but allow Shift+Enter for new line)
        messageInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });

        // Voice mode toggle
        if (speechManager) {
            voiceToggleButton.addEventListener('click', toggleVoiceMode);
        }

        // New chat button
        newChatButton.addEventListener('click', startNewChat);

        // Google toggle
        googleToggle.addEventListener('change', function() {
            const googleStatus = document.getElementById('google-status');
            const googleActions = document.querySelector('.google-actions');
            
            if (this.checked) {
                googleStatus.textContent = 'Google Integration: Enabled';
                googleStatus.classList.remove('disabled');
                googleStatus.classList.add('enabled');
                googleActions.style.display = 'block';
            } else {
                googleStatus.textContent = 'Google Integration: Disabled';
                googleStatus.classList.remove('enabled');
                googleStatus.classList.add('disabled');
                googleActions.style.display = 'none';
            }

            // Save to server
            updateSettings('google_enabled', this.checked);
        });

        // Speech toggle
        speechToggle.addEventListener('change', function() {
            if (this.checked) {
                speechSettings.style.display = 'block';
                if (speechManager) {
                    speechManager.setEnabled(true);
                }
            } else {
                speechSettings.style.display = 'none';
                if (speechManager) {
                    speechManager.setEnabled(false);
                    if (isVoiceModeActive) {
                        toggleVoiceMode();
                    }
                }
            }

            // Save to server
            updateSettings('speech_enabled', this.checked);
        });

        // Speech rate slider
        rateSlider.addEventListener('input', function() {
            rateValue.textContent = this.value;
            if (speechManager) {
                speechManager.setRate(parseFloat(this.value));
            }
        });

        rateSlider.addEventListener('change', function() {
            updateSettings('speech_rate', this.value);
        });

        // Speech pitch slider
        pitchSlider.addEventListener('input', function() {
            pitchValue.textContent = this.value;
            if (speechManager) {
                speechManager.setPitch(parseFloat(this.value));
            }
        });

        pitchSlider.addEventListener('change', function() {
            updateSettings('speech_pitch', this.value);
        });

        // Memory search
        memorySearchBtn.addEventListener('click', function() {
            searchMemories();
        });

        memorySearchInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                searchMemories();
            }
        });
    }

    // Chat Functions
    function sendMessage() {
        const message = messageInput.value.trim();
        if (!message) return;

        // Add user message to chat
        addMessageToChat('user', message);
        
        // Clear input and reset height
        messageInput.value = '';
        messageInput.style.height = 'auto';
        
        // Send message to server
        processMessage(message);
    }

    function handleTranscript(transcript) {
        if (transcript && isVoiceModeActive) {
            messageInput.value = transcript;
            sendMessage();
        }
    }

    function toggleVoiceMode() {
        if (!speechManager) return;

        isVoiceModeActive = !isVoiceModeActive;
        const voiceIndicator = document.getElementById('voice-indicator');

        if (isVoiceModeActive) {
            voiceToggleButton.innerHTML = '<i class="fas fa-microphone-slash"></i>';
            voiceIndicator.classList.remove('hidden');
            speechManager.startListening();
        } else {
            voiceToggleButton.innerHTML = '<i class="fas fa-microphone"></i>';
            voiceIndicator.classList.add('hidden');
            speechManager.stopListening();
        }
    }

    function startNewChat() {
        // Clear chat messages except for the first welcome message
        while (chatMessages.children.length > 1) {
            chatMessages.removeChild(chatMessages.lastChild);
        }

        // Reset conversation ID
        conversationId = null;

        // Clear insights
        insightsContent.innerHTML = '<p>No insights available yet. Continue your conversation to generate insights.</p>';

        // Disable voice mode if active
        if (isVoiceModeActive) {
            toggleVoiceMode();
        }
    }

    function addMessageToChat(sender, content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        // Process content for paragraphs
        content.split('\n').forEach(paragraph => {
            if (paragraph.trim()) {
                const p = document.createElement('p');
                p.textContent = paragraph;
                contentDiv.appendChild(p);
            }
        });
        
        messageDiv.appendChild(contentDiv);
        chatMessages.appendChild(messageDiv);
        
        // Scroll to bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // API Interactions
    function processMessage(message) {
        showLoading();

        const requestData = {
            message: message,
            conversation_id: conversationId,
            google_enabled: googleToggle.checked
        };

        fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        })
        .then(response => response.json())
        .then(data => {
            hideLoading();
            
            // Store conversation ID for future requests
            conversationId = data.conversation_id;
            
            // Add assistant response to chat
            addMessageToChat('assistant', data.reply);
            
            // Speak response if speech is enabled
            if (speechToggle.checked && speechManager) {
                speechManager.speak(data.reply);
            }
            
            // Update insights if available
            if (data.insights && data.insights.length > 0) {
                updateInsights(data.insights);
            }

            // Handle Google data if available
            if (data.google_data) {
                handleGoogleData(data.google_data);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            hideLoading();
            addMessageToChat('assistant', 'Sorry, there was an error processing your request. Please try again.');
        });
    }

    function searchMemories() {
        const query = memorySearchInput.value.trim();
        if (!query) return;

        showLoading();
        
        fetch(`/api/memories?query=${encodeURIComponent(query)}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            hideLoading();
            displayMemories(data.memories);
        })
        .catch(error => {
            console.error('Error fetching memories:', error);
            hideLoading();
            memoriesContent.innerHTML = '<p class="error">Failed to load memories. Please try again.</p>';
        });
    }

    function updateSettings(setting, value) {
        fetch('/api/settings', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ [setting]: value })
        })
        .then(response => response.json())
        .then(data => {
            console.log('Setting updated:', data);
        })
        .catch(error => {
            console.error('Error updating setting:', error);
        });
    }

    // UI Helpers
    function showLoading() {
        loadingOverlay.classList.remove('hidden');
    }

    function hideLoading() {
        loadingOverlay.classList.add('hidden');
    }

    function updateInsights(insights) {
        let html = '';
        insights.forEach(insight => {
            html += `<p>${insight}</p>`;
        });
        insightsContent.innerHTML = html;
    }

    function displayMemories(memories) {
        if (!memories || memories.length === 0) {
            memoriesContent.innerHTML = '<p>No memories found.</p>';
            return;
        }
        
        let html = '';
        memories.forEach(memory => {
            const date = new Date(memory.timestamp);
            const formattedDate = date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
            html += `<div class="memory-item">
                <p>${memory.content}</p>
                <small>${formattedDate}</small>
            </div>`;
        });
        
        memoriesContent.innerHTML = html;
    }

    function handleGoogleData(googleData) {
        if (googleData.calendar_events) {
            // Handle calendar events
            console.log('Calendar events:', googleData.calendar_events);
        }
        
        if (googleData.tasks) {
            // Handle tasks
            console.log('Tasks:', googleData.tasks);
        }
    }

    // Initialize the application
    initializeUI();
    setupEventListeners();
}); 