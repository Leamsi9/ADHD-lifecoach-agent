/**
 * Voice interaction for the Bahai Life Coach
 * Using browser's Web Speech API for speech recognition and synthesis
 */
document.addEventListener('DOMContentLoaded', () => {
    // Check if browser supports the Web Speech API
    const browserSupportsVoice = 'webkitSpeechRecognition' in window || 'SpeechRecognition' in window;
    
    // Elements
    const voiceToggleBtn = document.getElementById('voice-toggle-btn');
    const voiceIcon = voiceToggleBtn.querySelector('i');
    const voiceIndicator = document.getElementById('voice-indicator');
    const voiceStatus = document.getElementById('voice-status');
    const voiceTimer = document.getElementById('voice-timer');
    const messageInput = document.getElementById('message-input');
    const sendBtn = document.getElementById('send-btn');
    
    // State
    let isVoiceModeActive = false;
    let isListening = false;
    let timeoutId = null;
    let countdownInterval = null;
    let secondsLeft = 20;
    
    // Initialize speech recognition
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    let recognition = null;
    
    // Initialize speech synthesis
    const speechSynthesis = window.speechSynthesis;
    
    // Hide voice button if not supported
    if (!browserSupportsVoice) {
        voiceToggleBtn.style.display = 'none';
        console.warn('Speech Recognition is not supported in this browser');
        return;
    }
    
    // Set up speech recognition
    function setupSpeechRecognition() {
        recognition = new SpeechRecognition();
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.lang = 'en-US';
        
        // Event: Result received
        recognition.onresult = (event) => {
            const transcript = Array.from(event.results)
                .map(result => result[0])
                .map(result => result.transcript)
                .join('');
                
            // Update the message input
            messageInput.value = transcript;
            
            // Reset timer if speech detected
            resetListeningTimer();
        };
        
        // Event: End of speech
        recognition.onend = () => {
            if (isVoiceModeActive) {
                // If still in voice mode, restart
                startListening();
            } else {
                stopListening();
            }
        };
        
        // Event: Error
        recognition.onerror = (event) => {
            console.error('Speech recognition error', event.error);
            if (event.error === 'no-speech') {
                // No need to show an error for no speech
                return;
            }
            
            voiceStatus.textContent = `Error: ${event.error}`;
            setTimeout(() => {
                if (isVoiceModeActive) {
                    voiceStatus.textContent = 'Listening...';
                }
            }, 3000);
        };
    }
    
    // Toggle voice mode
    voiceToggleBtn.addEventListener('click', () => {
        isVoiceModeActive = !isVoiceModeActive;
        
        // Update UI
        voiceToggleBtn.classList.toggle('active', isVoiceModeActive);
        
        if (isVoiceModeActive) {
            // Switch to microphone icon
            voiceIcon.className = 'fas fa-microphone';
            // Start listening
            startListening();
            // Show voice indicator
            voiceIndicator.classList.remove('hidden');
        } else {
            // Switch to microphone-slash icon
            voiceIcon.className = 'fas fa-microphone-slash';
            // Stop listening
            stopListening();
            // Hide voice indicator
            voiceIndicator.classList.add('hidden');
        }
    });
    
    // Start listening for voice input
    function startListening() {
        if (!recognition) {
            setupSpeechRecognition();
        }
        
        if (!isListening) {
            try {
                recognition.start();
                isListening = true;
                
                // Start the listening timer
                resetListeningTimer();
                
                console.log('Voice recognition started');
            } catch (error) {
                console.error('Error starting speech recognition:', error);
            }
        }
    }
    
    // Stop listening for voice input
    function stopListening() {
        if (isListening && recognition) {
            recognition.stop();
            isListening = false;
            clearTimeout(timeoutId);
            clearInterval(countdownInterval);
            console.log('Voice recognition stopped');
        }
    }
    
    // Reset the listening timer
    function resetListeningTimer() {
        // Clear existing timers
        clearTimeout(timeoutId);
        clearInterval(countdownInterval);
        
        // Reset countdown
        secondsLeft = 20;
        voiceTimer.textContent = secondsLeft;
        
        // Start new countdown
        countdownInterval = setInterval(() => {
            secondsLeft -= 1;
            voiceTimer.textContent = secondsLeft;
            
            if (secondsLeft <= 0) {
                clearInterval(countdownInterval);
            }
        }, 1000);
        
        // Set timeout to stop listening after 20 seconds of inactivity
        timeoutId = setTimeout(() => {
            if (messageInput.value.trim() !== '') {
                // If there's text, send it
                sendBtn.click();
            }
            
            // If voice mode is still active but we're timing out due to inactivity
            if (isVoiceModeActive) {
                voiceStatus.textContent = 'Paused due to inactivity...';
                stopListening();
                
                // Restart listening after a pause
                setTimeout(() => {
                    if (isVoiceModeActive) {
                        voiceStatus.textContent = 'Listening...';
                        startListening();
                    }
                }, 1500);
            }
        }, 20000);
    }
    
    // Speak text using speech synthesis
    function speakText(text) {
        if (!isVoiceModeActive || !speechSynthesis) return;
        
        // Stop any ongoing speech
        speechSynthesis.cancel();
        
        // Remove reflection questions from spoken text
        let speechText = text;
        if (text.includes('Reflections to consider:')) {
            speechText = text.split('Reflections to consider:')[0];
        }
        
        // Create utterance
        const utterance = new SpeechSynthesisUtterance(speechText);
        utterance.lang = 'en-US';
        utterance.rate = 1.0;
        utterance.pitch = 1.0;
        
        // Speak
        speechSynthesis.speak(utterance);
    }
    
    // Hook into the chat.js message handling
    const originalAddMessageToChat = window.addMessageToChat;
    if (typeof originalAddMessageToChat === 'function') {
        window.addMessageToChat = function(role, content) {
            // Call the original function
            originalAddMessageToChat(role, content);
            
            // If it's an assistant message and voice mode is active, speak it
            if (role === 'assistant' && isVoiceModeActive) {
                speakText(content);
            }
        };
    } else {
        // If the function isn't available yet, try again after a short delay
        setTimeout(() => {
            const delayedOriginal = window.addMessageToChat;
            if (typeof delayedOriginal === 'function') {
                window.addMessageToChat = function(role, content) {
                    delayedOriginal(role, content);
                    if (role === 'assistant' && isVoiceModeActive) {
                        speakText(content);
                    }
                };
            }
        }, 500);
    }
}); 