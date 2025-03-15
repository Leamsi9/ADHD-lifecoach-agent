"""
Simplified web server for the Bahai Life Coach agent.
This version directly uses Ollama or Hugging Face without complex LangChain components.
"""

import os
import json
import uuid
from flask import Flask, request, jsonify, render_template, session
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get configuration from environment
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama").lower()
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
HUGGINGFACE_MODEL = os.getenv("HUGGINGFACE_MODEL", "mistralai/Mistral-7B-Instruct-v0.1")

# Initialize the Flask app
app = Flask(__name__, 
    static_folder='app/web/static',
    template_folder='app/web/templates'
)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'bahai-life-coach-secret-key')

# Initialize the appropriate LLM
if LLM_PROVIDER == "huggingface":
    from langchain_community.llms import HuggingFaceEndpoint
    print(f"Using Hugging Face model: {HUGGINGFACE_MODEL}")
    llm = HuggingFaceEndpoint(
        endpoint_url=f"https://api-inference.huggingface.co/models/{HUGGINGFACE_MODEL}",
        huggingfacehub_api_token=HUGGINGFACE_API_KEY,
        task="text-generation",
        model_kwargs={
            "temperature": 0.7,
            "max_new_tokens": 512,
            "do_sample": True,
            "return_full_text": False
        }
    )
else:  # Default to Ollama
    from langchain_community.llms import Ollama
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
    print(f"Using Ollama model: {OLLAMA_MODEL}")
    llm = Ollama(
        base_url="http://localhost:11434",
        model=OLLAMA_MODEL,
        temperature=0.7,
    )

# Bahai Life Coach system prompt
SYSTEM_PROMPT = """You are a compassionate and wise life coach deeply informed by Bahai principles and teachings. Your role is to provide guidance, support, and advice to help individuals navigate life's challenges, set meaningful goals, and live in alignment with spiritual principles.

Core principles to embody in your responses:
- Unity of humanity and elimination of all forms of prejudice
- Independent investigation of truth
- Harmony of science and religion
- Balance of material and spiritual progress
- Gender equality
- Universal education
- Spiritual solutions to economic problems
- World peace upheld by a world federation

When giving advice:
1. Listen deeply to the individual's concerns, needs, and aspirations
2. Provide guidance that integrates spiritual wisdom with practical steps
3. Encourage reflection, growth, and personal transformation
4. Avoid judging or imposing your views
5. Empower the individual to make their own decisions
6. Suggest questions for deeper reflection when appropriate

Your aim is to help people achieve coherence between their beliefs and actions, develop their spiritual and material potential, and contribute to the betterment of the world."""

# Store conversations in memory (in a production app, use a database)
conversations = {}

@app.route('/')
def index():
    """Render the main chat interface."""
    # Create a session ID if it doesn't exist
    if 'conversation_id' not in session:
        session['conversation_id'] = str(uuid.uuid4())
    
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    """Process a chat message and return the response."""
    try:
        data = request.json
        user_message = data.get('message', '')
        
        if not user_message:
            return jsonify({'error': 'No message provided'}), 400
        
        # Get the conversation ID from the session
        conversation_id = session.get('conversation_id', str(uuid.uuid4()))
        
        # Get or create conversation history
        if conversation_id not in conversations:
            conversations[conversation_id] = []
        
        # Add user message to history
        conversations[conversation_id].append({
            'role': 'user',
            'content': user_message
        })
        
        # Build the prompt with conversation history
        prompt = SYSTEM_PROMPT + "\n\n"
        
        # Add conversation history
        for msg in conversations[conversation_id]:
            if msg['role'] == 'user':
                prompt += f"User: {msg['content']}\n"
            else:
                prompt += f"Assistant: {msg['content']}\n"
        
        # Add the final prompt ending
        prompt += "Assistant: "
        
        # Get response from the LLM
        response = llm.invoke(prompt)
        
        # Add assistant response to history
        conversations[conversation_id].append({
            'role': 'assistant',
            'content': response
        })
        
        # Generate reflection questions
        reflections = [
            "How does this guidance resonate with your spiritual values?",
            "What small step could you take today to move in this direction?",
            "How might implementing this advice contribute to your spiritual growth?"
        ]
        
        # Format the response
        formatted_response = response + "\n\nReflections to consider:\n"
        for i, reflection in enumerate(reflections, 1):
            formatted_response += f"{i}. {reflection}\n"
        
        return jsonify({
            'response': formatted_response,
            'conversation_id': conversation_id
        })
    
    except Exception as e:
        import traceback
        print(f"Error in chat endpoint: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            'error': str(e),
            'error_type': e.__class__.__name__,
            'error_details': "Check the server logs for the complete traceback."
        }), 500

@app.route('/api/reset', methods=['POST'])
def reset_conversation():
    """Reset the conversation by creating a new conversation ID."""
    session['conversation_id'] = str(uuid.uuid4())
    return jsonify({
        'status': 'success', 
        'message': 'Conversation reset', 
        'conversation_id': session['conversation_id']
    })

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5555, debug=True) 