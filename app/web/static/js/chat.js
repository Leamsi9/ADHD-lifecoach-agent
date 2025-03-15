/**
 * Bahai Life Coach Chat Application
 * Handles UI interactions, speech functionality, and integrations
 */
document.addEventListener('DOMContentLoaded', () => {
    // Get DOM elements
    const chatMessages = document.getElementById('chat-messages');
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-btn');
    const resetButton = document.getElementById('reset-btn');
    const voiceToggleButton = document.getElementById('voice-toggle-btn');
    const voiceIndicator = document.getElementById('voice-indicator');
    const voiceStatus = document.getElementById('voice-status');
    const voiceTimer = document.getElementById('voice-timer');
    const googleToggle = document.getElementById('google-toggle');
    const insightsPanel = document.getElementById('insights-panel');
    
    // Set initial state
    let isWaitingForResponse = false;
    let voiceTimerInterval = null;
    let voiceTimerSeconds = 0;
    
    // Initialize speech manager with settings from the page
    const speechManager = new SpeechManager({
        enabled: window.speechEnabled || false,
        pauseThreshold: window.speechPauseThreshold || 5.0,
        voice: window.speechVoice || '',
        rate: window.speechRate || 1.0,
        pitch: window.speechPitch || 1.0
    });
    
    // Add event listeners
    sendButton.addEventListener('click', sendMessage);
    if (resetButton) {
        resetButton.addEventListener('click', resetConversation);
    }
    messageInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    if (voiceToggleButton) {
        voiceToggleButton.addEventListener('click', toggleVoiceMode);
    }
    
    if (googleToggle) {
        googleToggle.addEventListener('change', toggleGoogleIntegration);
    }
    
    // Set up speech manager callbacks
    speechManager.onTranscriptChange = (transcript) => {
        messageInput.value = transcript;
    };
    
    speechManager.onListeningStart = () => {
        if (voiceIndicator) {
            voiceIndicator.classList.remove('hidden');
        }
        if (voiceStatus) {
            voiceStatus.textContent = 'Listening...';
        }
        if (voiceToggleButton) {
            voiceToggleButton.classList.add('active');
        }
        startVoiceTimer();
    };
    
    speechManager.onListeningEnd = () => {
        if (voiceIndicator) {
            voiceIndicator.classList.add('hidden');
        }
        if (voiceStatus) {
            voiceStatus.textContent = 'Voice Off';
        }
        if (voiceToggleButton) {
            voiceToggleButton.classList.remove('active');
        }
        stopVoiceTimer();
    };
    
    speechManager.onSendRequest = (transcript) => {
        messageInput.value = transcript;
        sendMessage();
    };
    
    /**
     * Send a message to the API and handle the response
     */
    function sendMessage() {
        const message = messageInput.value.trim();
        
        if (message === '' || isWaitingForResponse) {
            return;
        }
        
        // Add user message to chat
        addMessageToChat('user', message);
        
        // Clear input
        messageInput.value = '';
        
        // Show loading indicator
        isWaitingForResponse = true;
        addLoadingIndicator();
        
        // Send request to API
        fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message }),
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            // Remove loading indicator
            removeLoadingIndicator();
            
            // Add assistant message to chat
            addMessageToChat('assistant', data.response);
            
            // Display integration data if available
            if (data.google_integration && data.google_integration.integration_used) {
                displayGoogleIntegrationData(data.google_integration);
            }
            
            // Speak the response if voice mode is active
            if (speechManager.isListening) {
                speechManager.speak(data.response);
            }
            
            // Update insights panel with memories
            updateInsightsPanel();
            
            // Reset state
            isWaitingForResponse = false;
            
            // Scroll to bottom
            scrollToBottom();
        })
        .catch(error => {
            console.error('Error:', error);
            removeLoadingIndicator();
            
            // Add error message to chat
            addMessageToChat('assistant', 'Sorry, there was an error processing your request. Please try again.');
            
            isWaitingForResponse = false;
        });
        
        // Scroll to bottom
        scrollToBottom();
    }
    
    /**
     * Reset the conversation
     */
    function resetConversation() {
        // Show loading indicator
        addLoadingIndicator();
        
        // Send reset request to API
        fetch('/api/reset', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json())
        .then(data => {
            // Clear chat
            chatMessages.innerHTML = '';
            
            // Add welcome message with greeting from memory if available
            if (data.greeting) {
                addMessageToChat('assistant', data.greeting);
            } else {
                addMessageToChat('assistant', 'Welcome to your personal life coach, guided by Baháʼí principles. Share your thoughts, concerns, or questions, and receive compassionate guidance.');
            }
            
            // Remove loading indicator
            removeLoadingIndicator();
            
            // Update insights panel with memories
            updateInsightsPanel();
            
            // Scroll to bottom
            scrollToBottom();
        })
        .catch(error => {
            console.error('Error resetting conversation:', error);
            removeLoadingIndicator();
            addMessageToChat('assistant', 'Error resetting conversation. Please try again.');
        });
    }
    
    /**
     * Toggle Google integration
     */
    function toggleGoogleIntegration() {
        const isEnabled = googleToggle.checked;
        
        if (isEnabled) {
            // Initiate OAuth flow if needed
            initiateGoogleAuth();
        } else {
            // Update UI to reflect disabled state
            updateGoogleIntegrationUI(false);
        }
    }
    
    /**
     * Initiate Google OAuth flow
     */
    function initiateGoogleAuth() {
        // Show loading indicator
        addLoadingIndicator();
        
        // Get auth URL from API
        fetch('/api/google/auth_url')
            .then(response => response.json())
            .then(data => {
                removeLoadingIndicator();
                
                if (data.auth_url) {
                    // Open OAuth window
                    const authWindow = window.open(data.auth_url, 'googleOAuth', 'width=600,height=600');
                    
                    // Check for auth completion
                    const checkAuth = setInterval(() => {
                        fetch('/api/google/check_auth')
                            .then(response => response.json())
                            .then(data => {
                                if (data.authorized) {
                                    clearInterval(checkAuth);
                                    
                                    // Update UI for enabled state
                                    updateGoogleIntegrationUI(true);
                                    
                                    // Notify user
                                    addMessageToChat('assistant', 'Google integration successfully connected! You can now use calendar and task features.');
                                }
                            })
                            .catch(error => {
                                console.error('Error checking auth status:', error);
                            });
                    }, 2000);
                    
                    // Handle window close
                    const checkClosed = setInterval(() => {
                        if (authWindow.closed) {
                            clearInterval(checkClosed);
                            clearInterval(checkAuth);
                            
                            // Check one last time
                            fetch('/api/google/check_auth')
                                .then(response => response.json())
                                .then(data => {
                                    if (!data.authorized) {
                                        // Reset toggle if not authorized
                                        googleToggle.checked = false;
                                        updateGoogleIntegrationUI(false);
                                        addMessageToChat('assistant', 'Google integration was not connected. Please try again if you want to use Google Calendar and Tasks.');
                                    }
                                })
                                .catch(error => {
                                    console.error('Error checking final auth status:', error);
                                    googleToggle.checked = false;
                                    updateGoogleIntegrationUI(false);
                                });
                        }
                    }, 1000);
                } else {
                    // Error getting auth URL
                    googleToggle.checked = false;
                    updateGoogleIntegrationUI(false);
                    addMessageToChat('assistant', 'Could not initiate Google authentication. Please check your settings and try again.');
                }
            })
            .catch(error => {
                console.error('Error initiating Google auth:', error);
                removeLoadingIndicator();
                googleToggle.checked = false;
                updateGoogleIntegrationUI(false);
                addMessageToChat('assistant', 'Error connecting to Google. Please try again later.');
            });
    }
    
    /**
     * Update Google integration UI elements
     */
    function updateGoogleIntegrationUI(isEnabled) {
        const integrationBadge = document.getElementById('google-integration-badge');
        if (integrationBadge) {
            integrationBadge.classList.toggle('enabled', isEnabled);
            integrationBadge.classList.toggle('disabled', !isEnabled);
            integrationBadge.innerHTML = isEnabled 
                ? '<i class="fas fa-check-circle"></i> Google Integration Active'
                : '<i class="fas fa-times-circle"></i> Google Integration Disabled';
        }
        
        const googleActions = document.getElementById('google-actions');
        if (googleActions) {
            googleActions.classList.toggle('hidden', !isEnabled);
        }
    }
    
    /**
     * Toggle voice mode
     */
    function toggleVoiceMode() {
        if (speechManager.isListening) {
            speechManager.stopListening();
        } else {
            speechManager.startListening();
        }
    }
    
    /**
     * Start voice timer
     */
    function startVoiceTimer() {
        voiceTimerSeconds = 0;
        updateVoiceTimer();
        
        if (voiceTimerInterval) {
            clearInterval(voiceTimerInterval);
        }
        
        voiceTimerInterval = setInterval(() => {
            const elapsed = (Date.now() - speechManager.lastSpeechTime) / 1000;
            const remaining = Math.max(0, Math.ceil(speechManager.options.pauseThreshold - elapsed));
            
            if (voiceTimer) {
                voiceTimer.textContent = remaining;
            }
        }, 250);
    }
    
    /**
     * Stop voice timer
     */
    function stopVoiceTimer() {
        if (voiceTimerInterval) {
            clearInterval(voiceTimerInterval);
            voiceTimerInterval = null;
        }
        
        if (voiceTimer) {
            voiceTimer.textContent = '';
        }
    }
    
    /**
     * Update voice timer display
     */
    function updateVoiceTimer() {
        if (voiceTimer) {
            const elapsed = (Date.now() - speechManager.lastSpeechTime) / 1000;
            const remaining = Math.max(0, Math.ceil(speechManager.options.pauseThreshold - elapsed));
            voiceTimer.textContent = remaining;
        }
    }
    
    /**
     * Add a message to the chat
     */
    function addMessageToChat(role, content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        
        // Format the content with line breaks
        messageContent.innerHTML = formatMessage(content);
        
        messageDiv.appendChild(messageContent);
        chatMessages.appendChild(messageDiv);
        
        scrollToBottom();
    }
    
    /**
     * Add loading indicator to chat
     */
    function addLoadingIndicator() {
        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'message assistant loading';
        loadingDiv.innerHTML = '<div class="loading-dots"><span></span><span></span><span></span></div>';
        loadingDiv.id = 'loading-indicator';
        chatMessages.appendChild(loadingDiv);
        scrollToBottom();
    }
    
    /**
     * Remove loading indicator from chat
     */
    function removeLoadingIndicator() {
        const loadingIndicator = document.getElementById('loading-indicator');
        if (loadingIndicator) {
            loadingIndicator.remove();
        }
    }
    
    /**
     * Format message content with line breaks and links
     */
    function formatMessage(content) {
        if (!content) return '';
        
        // Convert line breaks to HTML
        let formatted = content.replace(/\n/g, '<br>');
        
        // Convert URLs to links
        formatted = formatted.replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank">$1</a>');
        
        return formatted;
    }
    
    /**
     * Display Google integration data (calendar events, tasks)
     */
    function displayGoogleIntegrationData(googleData) {
        if (!googleData) return;

        let integrationContent = '';

        // Display calendar events if available
        if (googleData.calendar_events && googleData.calendar_events.length > 0) {
            integrationContent += '<div class="integration-section">';
            integrationContent += '<h4><i class="far fa-calendar-alt"></i> Calendar Events</h4>';
            integrationContent += '<ul class="integration-list">';
            googleData.calendar_events.forEach(event => {
                integrationContent += `<li><strong>${event.summary}</strong>: ${event.start} - ${event.end}</li>`;
            });
            integrationContent += '</ul></div>';
        }

        // Display tasks if available
        if (googleData.tasks && googleData.tasks.length > 0) {
            integrationContent += '<div class="integration-section">';
            integrationContent += '<h4><i class="far fa-check-square"></i> Tasks</h4>';
            integrationContent += '<ul class="integration-list">';
            googleData.tasks.forEach(task => {
                integrationContent += `<li><strong>${task.title}</strong>${task.due ? ` (Due: ${task.due})` : ''}</li>`;
            });
            integrationContent += '</ul></div>';
        }

        // Add integration data to chat if we have any
        if (integrationContent) {
            const integrationDiv = document.createElement('div');
            integrationDiv.className = 'message integration';
            integrationDiv.innerHTML = `
                <div class="message-content">
                    <div class="integration-data">
                        <h3><i class="fab fa-google"></i> Google Integration Data</h3>
                        ${integrationContent}
                    </div>
                </div>
            `;
            chatMessages.appendChild(integrationDiv);
            scrollToBottom();
        }
    }
    
    /**
     * Update insights panel with memories
     */
    function updateInsightsPanel() {
        if (!insightsPanel) return;
        
        // Fetch memories from API
        fetch('/api/memories')
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success' && data.memories && data.memories.length > 0) {
                    insightsPanel.innerHTML = '<h3>Key Insights</h3>';
                    
                    const insightsList = document.createElement('ul');
                    insightsList.className = 'insights-list';
                    
                    // Add memories to the list
                    data.memories.slice(0, 5).forEach(memory => {
                        const li = document.createElement('li');
                        li.textContent = memory.content;
                        insightsList.appendChild(li);
                    });
                    
                    insightsPanel.appendChild(insightsList);
                    
                    // Add a way to add explicit memories
                    const addMemoryForm = document.createElement('div');
                    addMemoryForm.className = 'add-memory-form';
                    addMemoryForm.innerHTML = `
                        <input type="text" id="new-memory" placeholder="Add a memory...">
                        <button id="add-memory-btn">Add</button>
                    `;
                    insightsPanel.appendChild(addMemoryForm);
                    
                    // Add event listener for the add memory button
                    document.getElementById('add-memory-btn').addEventListener('click', addExplicitMemory);
                    
                    // Show the panel
                    insightsPanel.classList.remove('hidden');
                } else {
                    insightsPanel.innerHTML = '<h3>Key Insights</h3><p>No insights available yet.</p>';
                }
            })
            .catch(error => {
                console.error('Error fetching memories:', error);
                insightsPanel.innerHTML = '<h3>Key Insights</h3><p>Error loading insights.</p>';
            });
    }
    
    /**
     * Add an explicit memory
     */
    function addExplicitMemory() {
        const memoryInput = document.getElementById('new-memory');
        const memory = memoryInput.value.trim();
        
        if (memory === '') return;
        
        // Send the memory to the API
        fetch('/api/memories', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ memory }),
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                // Clear input
                memoryInput.value = '';
                
                // Update insights panel
                updateInsightsPanel();
                
                // Notify user
                addMessageToChat('assistant', `I'll remember that: "${memory}"`);
            } else {
                addMessageToChat('assistant', 'Sorry, I couldn\'t save that memory. Please try again.');
            }
        })
        .catch(error => {
            console.error('Error adding memory:', error);
            addMessageToChat('assistant', 'Sorry, there was an error saving your memory. Please try again.');
        });
    }
    
    /**
     * Scroll chat to bottom
     */
    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    // Initialize
    
    // Check if speech recognition is available
    if (!speechManager.isAvailable()) {
        if (voiceToggleButton) {
            voiceToggleButton.disabled = true;
            voiceToggleButton.title = 'Speech functionality not available in this browser';
        }
    }
    
    // Check initial Google integration status
    if (googleToggle) {
        fetch('/api/google/check_auth')
            .then(response => response.json())
            .then(data => {
                googleToggle.checked = data.authorized || false;
                updateGoogleIntegrationUI(data.authorized || false);
            })
            .catch(error => {
                console.error('Error checking Google auth status:', error);
                googleToggle.checked = false;
                updateGoogleIntegrationUI(false);
            });
    }
    
    // Update insights panel on load
    updateInsightsPanel();
}); 