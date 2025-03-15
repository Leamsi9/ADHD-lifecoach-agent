"""
Routes for the Bahai Life Coach web interface.
"""

import json
import uuid
import traceback
from flask import Blueprint, render_template, request, jsonify, session
import os
import logging

from app.agents.direct_coach_agent import DirectCoachAgent
from app.config.settings import (
    ENABLE_GOOGLE_INTEGRATION,
    ENABLE_SPEECH,
    SPEECH_VOICE,
    SPEECH_RATE,
    SPEECH_PITCH,
    SPEECH_PAUSE_THRESHOLD,
    validate_config
)
from app.utils.memory import MemoryManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create the blueprint
main = Blueprint('main', __name__)

# Validate configuration
validate_config()

# Initialize the agent only when needed
agent = None

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
    global agent
    
    try:
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({'error': 'No message provided'}), 400
        
        message = data['message']
        
        # Initialize or retrieve agent with conversation ID
        conversation_id = data.get('conversation_id')
        
        if not agent or (conversation_id and agent.conversation_id != conversation_id):
            agent = DirectCoachAgent(conversation_id=conversation_id)
        
        # Process the message
        result = agent.provide_coaching(message)
        
        # Create response
        response = {
            'response': result['response'],
            'conversation_id': result['conversation_id']
        }
        
        # Add insights if available
        if 'insights' in result:
            response['insights'] = result['insights']
        
        # Add Google integration data if applicable
        if ENABLE_GOOGLE_INTEGRATION:
            response['google_integration'] = {
                'enabled': agent.google_integration_data.get('enabled', False),
                'integration_used': result.get('integration_used', False),
                'calendar_events': agent.google_integration_data.get('calendar_events', []),
                'tasks': agent.google_integration_data.get('tasks', [])
            }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error processing chat: {str(e)}")
        return jsonify({'error': str(e)}), 500

@main.route('/api/reset', methods=['POST'])
def reset_conversation():
    """
    Reset the conversation and start a new one.
    
    Returns:
        dict: JSON response confirming the reset
    """
    global agent
    
    try:
        # Create a new agent with a fresh conversation ID
        agent = DirectCoachAgent()
        
        # Get a greeting for the new conversation
        result = agent.start_new_conversation()
        
        return jsonify({
            'response': result['response'],
            'conversation_id': result['conversation_id']
        })
        
    except Exception as e:
        logger.error(f"Error resetting conversation: {str(e)}")
        return jsonify({'error': str(e)}), 500

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
    global agent
    
    if not agent:
        return jsonify({'error': 'No active conversation'}), 400
    
    try:
        query = request.args.get('query')
        memories = agent.get_memories(query)
        
        return jsonify({
            'memories': memories,
            'conversation_id': agent.conversation_id
        })
        
    except Exception as e:
        logger.error(f"Error retrieving memories: {str(e)}")
        return jsonify({'error': str(e)}), 500

@main.route('/api/memories', methods=['POST'])
def add_memory():
    """
    Add an explicit memory to the current conversation.
    
    Returns:
        dict: JSON response confirming the addition
    """
    global agent
    
    if not agent:
        return jsonify({'error': 'No active conversation'}), 400
    
    try:
        data = request.get_json()
        
        if not data or 'content' not in data:
            return jsonify({'error': 'No memory content provided'}), 400
        
        content = data['content']
        agent.add_explicit_memory(content)
        
        return jsonify({
            'success': True,
            'message': 'Memory added successfully',
            'conversation_id': agent.conversation_id
        })
        
    except Exception as e:
        logger.error(f"Error adding memory: {str(e)}")
        return jsonify({'error': str(e)}), 500

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