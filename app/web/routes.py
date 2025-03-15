"""
Routes for the Bahai Life Coach web interface.
"""

import json
import uuid
import traceback
from flask import Blueprint, render_template, request, jsonify, session
import os

from app.agents.life_coach_agent import LifeCoachAgent
from app.config.settings import (
    ENABLE_GOOGLE_INTEGRATION,
    ENABLE_SPEECH,
    SPEECH_VOICE,
    SPEECH_RATE,
    SPEECH_PITCH,
    SPEECH_PAUSE_THRESHOLD
)
from app.utils.memory import MemoryManager

# Create the blueprint
main = Blueprint('main', __name__)

# Initialize the life coach agent
life_coach_agent = LifeCoachAgent()

@main.route('/')
def index():
    """
    Render the main chat interface.
    
    Returns:
        str: Rendered HTML template
    """
    # Pass speech and Google integration settings to template
    return render_template('index.html', 
                           google_integration_enabled=ENABLE_GOOGLE_INTEGRATION,
                           speech_enabled=ENABLE_SPEECH,
                           speech_voice=SPEECH_VOICE,
                           speech_rate=SPEECH_RATE,
                           speech_pitch=SPEECH_PITCH,
                           speech_pause_threshold=SPEECH_PAUSE_THRESHOLD)

@main.route('/api/chat', methods=['POST'])
def chat():
    """
    Process a chat message and return the response.
    
    Returns:
        dict: JSON response containing the coach's reply
    """
    data = request.json
    user_message = data.get('message', '')
    
    if not user_message:
        return jsonify({'error': 'No message provided'}), 400
    
    try:
        # Get the conversation ID from the session
        conversation_id = session.get('conversation_id', str(uuid.uuid4()))
        
        # Process the message with the enhanced agent
        agent = LifeCoachAgent(conversation_id=conversation_id)
        result = agent.provide_coaching(user_message)
        
        # Store the conversation ID for future requests
        session['conversation_id'] = result['conversation_id']
        
        # Get Google integration data from the agent
        google_integration_data = {}
        if ENABLE_GOOGLE_INTEGRATION and hasattr(agent, 'google_integration_data'):
            google_integration_data = agent.google_integration_data
        
        # Return the response with all necessary information
        response_data = {
            'response': result['response'],
            'conversation_id': result['conversation_id'],
            'insights': result.get('insights', []),
            'google_integration': google_integration_data
        }
        
        return jsonify(response_data)
    
    except Exception as e:
        # Get the full stacktrace
        error_traceback = traceback.format_exc()
        print(f"Error in chat endpoint: {str(e)}")
        print(error_traceback)
        
        # Return a detailed error to the client
        return jsonify({
            'error': str(e),
            'error_type': e.__class__.__name__,
            'error_details': "Check the server logs for the complete traceback."
        }), 500

@main.route('/api/reset', methods=['POST'])
def reset_conversation():
    """
    Reset the conversation by creating a new conversation ID.
    
    Returns:
        dict: JSON response confirming the reset
    """
    session['conversation_id'] = str(uuid.uuid4())
    
    # Start a new conversation with context from previous sessions
    agent = LifeCoachAgent(conversation_id=session['conversation_id'])
    result = agent.start_new_conversation()
    
    return jsonify({
        'status': 'success', 
        'message': 'Conversation reset', 
        'conversation_id': session['conversation_id'],
        'greeting': result['response']
    })

@main.route('/api/integration_status', methods=['GET'])
def integration_status():
    """
    Get the status of integrations.
    
    Returns:
        dict: JSON response with integration status
    """
    return jsonify({
        'google_integration': {
            'enabled': ENABLE_GOOGLE_INTEGRATION
        }
    })

@main.route('/api/memories', methods=['GET'])
def get_memories():
    """
    Get memories for the current conversation.
    
    Returns:
        dict: JSON response with memories
    """
    conversation_id = session.get('conversation_id')
    if not conversation_id:
        return jsonify({'error': 'No active conversation'}), 400
    
    query = request.args.get('query', '')
    
    agent = LifeCoachAgent(conversation_id=conversation_id)
    memories = agent.get_memories(query if query else None)
    
    return jsonify({
        'status': 'success',
        'memories': memories
    })

@main.route('/api/memories', methods=['POST'])
def add_memory():
    """
    Add an explicit memory to the current conversation.
    
    Returns:
        dict: JSON response confirming the addition
    """
    data = request.json
    content = data.get('content', '')
    
    if not content:
        return jsonify({'error': 'No memory content provided'}), 400
    
    conversation_id = session.get('conversation_id')
    if not conversation_id:
        return jsonify({'error': 'No active conversation'}), 400
    
    agent = LifeCoachAgent(conversation_id=conversation_id)
    agent.add_explicit_memory(content)
    
    return jsonify({
        'status': 'success',
        'message': 'Memory added successfully'
    })

@main.route('/api/google/auth_url', methods=['GET'])
def get_google_auth_url():
    """Get Google OAuth URL for authorization"""
    if not ENABLE_GOOGLE_INTEGRATION:
        return jsonify({
            'status': 'error',
            'message': 'Google integration is disabled'
        })
    
    # Generate auth URL
    # This would typically call a function from your Google integration module
    auth_url = "Google auth URL would be returned here"
    
    return jsonify({
        'status': 'success',
        'auth_url': auth_url
    })

@main.route('/api/google/check_auth', methods=['GET'])
def check_google_auth():
    """Check if Google authorization is complete"""
    if not ENABLE_GOOGLE_INTEGRATION:
        return jsonify({
            'status': 'error',
            'message': 'Google integration is disabled',
            'authorized': False
        })
    
    # Check auth status
    # This would typically call a function from your Google integration module
    authorized = False
    
    return jsonify({
        'status': 'success',
        'authorized': authorized
    }) 