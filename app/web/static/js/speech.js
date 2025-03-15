/**
 * Speech functionality for the Bahai Life Coach web interface.
 * Implements browser-based speech synthesis and recognition.
 */

class SpeechManager {
    /**
     * Constructor
     * @param {Object} options - Speech configuration options
     * @param {boolean} options.enabled - Whether speech is enabled
     * @param {number} options.pauseThreshold - Seconds of silence before auto-sending
     * @param {string} options.voice - Preferred voice name
     * @param {number} options.rate - Speech rate (0.1 to 10)
     * @param {number} options.pitch - Speech pitch (0 to 2)
     */
    constructor(options = {}) {
        // Set default options
        this.options = {
            enabled: options.enabled || false,
            pauseThreshold: options.pauseThreshold || 5.0,
            voice: options.voice || '',
            rate: options.rate || 1.0,
            pitch: options.pitch || 1.0
        };
        
        // Initialize state
        this.isListening = false;
        this.recognition = null;
        this.synthesis = window.speechSynthesis;
        this.transcript = '';
        this.lastSpeechTime = Date.now();
        this.pauseTimer = null;
        this.selectedVoice = null;
        
        // Callback functions
        this.onTranscriptChange = null;
        this.onListeningStart = null;
        this.onListeningEnd = null;
        this.onSendRequest = null;
        
        // Initialize if enabled
        if (this.options.enabled) {
            this.initialize();
        }
    }
    
    /**
     * Check if speech recognition is available in the browser
     * @returns {boolean} Whether speech recognition is available
     */
    isAvailable() {
        return 'SpeechRecognition' in window || 'webkitSpeechRecognition' in window;
    }
    
    /**
     * Initialize speech recognition and synthesis
     */
    initialize() {
        // Skip if not available
        if (!this.isAvailable()) {
            console.warn('Speech recognition is not available in this browser');
            return;
        }
        
        // Initialize speech recognition
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        this.recognition = new SpeechRecognition();
        this.recognition.continuous = true;
        this.recognition.interimResults = true;
        
        // Set up event listeners
        this.recognition.onresult = (event) => {
            this.lastSpeechTime = Date.now();
            let interimTranscript = '';
            let finalTranscript = '';
            
            // Process results
            for (let i = event.resultIndex; i < event.results.length; i++) {
                const transcript = event.results[i][0].transcript;
                if (event.results[i].isFinal) {
                    finalTranscript += transcript;
                } else {
                    interimTranscript += transcript;
                }
            }
            
            // Update transcript
            if (finalTranscript !== '') {
                this.transcript += finalTranscript;
            }
            
            // Call transcript change callback
            if (this.onTranscriptChange) {
                this.onTranscriptChange(this.transcript + interimTranscript);
            }
            
            // Reset pause timer
            this.resetPauseTimer();
        };
        
        this.recognition.onerror = (event) => {
            console.error('Speech recognition error:', event.error);
            if (event.error === 'no-speech') {
                // Nothing detected for a while, this is expected
                return;
            }
            
            // For actual errors, stop listening
            if (['audio-capture', 'network', 'not-allowed', 'service-not-allowed'].includes(event.error)) {
                this.stopListening();
            }
        };
        
        this.recognition.onend = () => {
            // Restart if still in listening mode
            if (this.isListening) {
                this.recognition.start();
            } else {
                if (this.onListeningEnd) {
                    this.onListeningEnd();
                }
            }
        };
        
        // Initialize speech synthesis
        if (this.synthesis) {
            // Get available voices
            this.updateVoices();
            
            // Set up voice change listener
            if (this.synthesis.onvoiceschanged !== undefined) {
                this.synthesis.onvoiceschanged = this.updateVoices.bind(this);
            }
        }
    }
    
    /**
     * Update available voices and select preferred voice
     */
    updateVoices() {
        if (!this.synthesis) return;
        
        const voices = this.synthesis.getVoices();
        
        // Select preferred voice if specified
        if (this.options.voice && voices.length > 0) {
            // Try to find exact match
            this.selectedVoice = voices.find(voice => 
                voice.name.toLowerCase() === this.options.voice.toLowerCase());
            
            // If no exact match, try to find voice containing the preference
            if (!this.selectedVoice) {
                this.selectedVoice = voices.find(voice => 
                    voice.name.toLowerCase().includes(this.options.voice.toLowerCase()));
            }
        }
        
        // Default to first voice if no match found
        if (!this.selectedVoice && voices.length > 0) {
            // Prefer English voices
            const englishVoices = voices.filter(voice => 
                voice.lang.startsWith('en-'));
            
            this.selectedVoice = englishVoices.length > 0 ? 
                englishVoices[0] : voices[0];
        }
    }
    
    /**
     * Start listening for speech input
     */
    startListening() {
        if (!this.isAvailable() || !this.recognition) {
            this.initialize();
            if (!this.recognition) {
                console.error('Speech recognition failed to initialize');
                return;
            }
        }
        
        try {
            this.isListening = true;
            this.transcript = '';
            this.recognition.start();
            this.lastSpeechTime = Date.now();
            this.resetPauseTimer();
            
            if (this.onListeningStart) {
                this.onListeningStart();
            }
        } catch (error) {
            console.error('Error starting speech recognition:', error);
            this.isListening = false;
        }
    }
    
    /**
     * Stop listening for speech input
     */
    stopListening() {
        if (this.recognition && this.isListening) {
            this.isListening = false;
            try {
                this.recognition.stop();
            } catch (error) {
                console.error('Error stopping speech recognition:', error);
            }
            
            if (this.pauseTimer) {
                clearTimeout(this.pauseTimer);
                this.pauseTimer = null;
            }
            
            if (this.onListeningEnd) {
                this.onListeningEnd();
            }
        }
    }
    
    /**
     * Toggle listening state
     */
    toggleListening() {
        if (this.isListening) {
            this.stopListening();
        } else {
            this.startListening();
        }
    }
    
    /**
     * Reset pause timer
     */
    resetPauseTimer() {
        // Clear existing timer
        if (this.pauseTimer) {
            clearTimeout(this.pauseTimer);
            this.pauseTimer = null;
        }
        
        // Set new timer
        if (this.isListening && this.transcript.trim() !== '') {
            this.pauseTimer = setTimeout(() => {
                // Send transcript if pause threshold exceeded
                if (this.onSendRequest && this.transcript.trim() !== '') {
                    this.onSendRequest(this.transcript);
                    this.transcript = '';
                }
            }, this.options.pauseThreshold * 1000);
        }
    }
    
    /**
     * Send the current transcript
     */
    sendTranscript() {
        if (this.onSendRequest && this.transcript.trim() !== '') {
            this.onSendRequest(this.transcript);
            this.transcript = '';
        }
    }
    
    /**
     * Speak text using speech synthesis
     * @param {string} text - Text to speak
     */
    speak(text) {
        if (!this.synthesis) return;
        
        // Cancel any ongoing speech
        this.synthesis.cancel();
        
        // Create utterance
        const utterance = new SpeechSynthesisUtterance(text);
        
        // Set voice if available
        if (this.selectedVoice) {
            utterance.voice = this.selectedVoice;
        }
        
        // Set rate and pitch
        utterance.rate = this.options.rate;
        utterance.pitch = this.options.pitch;
        
        // Speak
        this.synthesis.speak(utterance);
    }
}

// Export for use in other modules
window.SpeechManager = SpeechManager; 