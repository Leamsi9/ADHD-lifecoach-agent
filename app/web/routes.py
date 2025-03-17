"""
Routes for the Bahai Life Coach web interface.
"""

# Import Flask and Blueprint classes first to avoid circular imports
from flask import Blueprint, render_template, request, jsonify, session

# Create a Blueprint before importing anything from app
web_bp = Blueprint('web', __name__)

# Now import the rest of the needed modules
import json
import uuid
import traceback
import os
import logging
from datetime import datetime
from pathlib import Path
import re

from app.agents.agent_adapter import get_agent
from app.config.settings import (
    ENABLE_GOOGLE_INTEGRATION,
    ENABLE_SPEECH,
    SPEECH_VOICE,
    SPEECH_RATE,
    SPEECH_PITCH,
    SPEECH_PAUSE_THRESHOLD,
    validate_configuration
)
from app.models.llm import get_llm_model
from app.utils.memory_db import MemoryDB

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Validate configuration
validate_configuration()

# Initialize the agent only when needed
agent = None

# Memory storage path
MEMORY_STORAGE_PATH = Path("memory_storage")

# Ensure memory directory exists
MEMORY_STORAGE_PATH.mkdir(parents=True, exist_ok=True)

@web_bp.route('/')
def index():
    """Render the main chat interface."""
    # Get settings from session or use defaults
    settings = {
        'speech_enabled': session.get('speech_enabled', True),
        'google_enabled': session.get('google_enabled', False),
        'llm_model': session.get('llm_model', 'gemini-2.0-flash')
    }
    
    return render_template('index.html', settings=settings)

@web_bp.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat API requests."""
    try:
        data = request.json
        user_input = data.get('message', '')
        conversation_id = data.get('conversation_id')
        include_memories = data.get('include_memories', False)
        settings = data.get('settings', {})
        
        # Update session settings if provided
        if settings:
            session['speech_enabled'] = settings.get('speech_enabled', True)
            session['google_enabled'] = settings.get('google_enabled', False)
            session['llm_model'] = settings.get('llm_model', 'gemini-2.0-flash')
        
        # Get agent with current settings
        agent = get_agent(
            llm_model=session.get('llm_model', 'gemini-2.0-flash'),
            google_enabled=session.get('google_enabled', False),
            conversation_id=conversation_id,
            include_memories=include_memories
        )
        
        # Process user input
        response, metadata = agent.process_input(user_input)
        
        # Format response
        result = {
            'status': 'success',
            'response': response,
            'conversation_id': metadata.get('conversation_id'),
            'insights': metadata.get('insights', [])
        }
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'error': str(e)
        })

@web_bp.route('/api/settings', methods=['POST'])
def update_settings():
    """Update user settings."""
    try:
        data = request.json
        
        # Update session with new settings
        session['speech_enabled'] = data.get('speech_enabled', True)
        session['google_enabled'] = data.get('google_enabled', False)
        session['llm_model'] = data.get('llm_model', 'gemini-2.0-flash')
        
        return jsonify({
            'status': 'success',
            'settings': {
                'speech_enabled': session.get('speech_enabled'),
                'google_enabled': session.get('google_enabled'),
                'llm_model': session.get('llm_model')
            }
        })
    
    except Exception as e:
        logger.error(f"Error updating settings: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'error': str(e)
        })

@web_bp.route('/api/new_conversation', methods=['POST'])
def new_conversation():
    """Start a new conversation."""
    try:
        data = request.json
        remember = data.get('remember', True)
        
        # Get a fresh agent (this will create a new conversation ID)
        agent = get_agent(
            llm_model=session.get('llm_model', 'gemini-2.0-flash'),
            google_enabled=session.get('google_enabled', False)
        )
        
        return jsonify({
            'status': 'success',
            'conversation_id': agent.conversation_id
        })
    
    except Exception as e:
        logger.error(f"Error starting new conversation: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'error': str(e)
        })

@web_bp.route('/api/memories', methods=['GET'])
def get_memories():
    """Retrieve memories for the current user."""
    try:
        # Initialize memory DB
        memory_db = MemoryDB()
        
        # Get most recent memory of each type
        short_term = memory_db.get_latest_memory('short')
        mid_term = memory_db.get_latest_memory('mid')
        long_term = memory_db.get_latest_memory('long')
        
        # Format response
        memories = {
            'short': short_term,
            'mid': mid_term,
            'long': long_term
        }
        
        return jsonify(memories)
    
    except Exception as e:
        logger.error(f"Error retrieving memories: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'error': str(e)
        })

@web_bp.route('/api/memories/search', methods=['GET'])
def search_memories():
    """Search memories using a query string."""
    try:
        query = request.args.get('query', '')
        
        # Initialize memory DB
        memory_db = MemoryDB()
        
        # Search memories
        memories = memory_db.search_memories(query)
        
        return jsonify({
            'status': 'success',
            'memories': memories
        })
    except Exception as e:
        logger.error(f"Error searching memories: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': str(e),
            'memories': []
        })

@web_bp.route('/api/memories', methods=['POST'])
def create_memory():
    """Create a new memory manually."""
    try:
        data = request.json
        conversation_id = data.get('conversation_id')
        content = data.get('content')
        memory_type = data.get('type', 'short')
        
        if not conversation_id or not content:
            return jsonify({
                'status': 'error',
                'message': 'Missing required fields (conversation_id, content)'
            }), 400
        
        # Initialize memory DB
        memory_db = MemoryDB()
        
        # Create memory
        timestamp = datetime.now().isoformat()
        memory_id = f"{conversation_id}-{memory_type}-{int(datetime.now().timestamp())}"
        
        memory_data = {
            'id': memory_id,
            'conversation_id': conversation_id,
            'content': content,
            'type': memory_type,
            'created_at': timestamp,
            'updated_at': timestamp
        }
        
        # Store memory
        memory_db.add_memory(memory_data)
        
        return jsonify({
            'status': 'success',
            'memory': memory_data
        })
    except Exception as e:
        logger.error(f"Error creating memory: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@web_bp.route('/api/memories/<memory_id>', methods=['DELETE'])
def delete_memory(memory_id):
    """Delete a memory."""
    try:
        # Initialize memory DB
        memory_db = MemoryDB()
        
        # Delete memory
        success = memory_db.delete_memory(memory_id)
        
        if not success:
            return jsonify({
                'status': 'error',
                'message': f'Memory with ID {memory_id} not found'
            }), 404
        
        return jsonify({
            'status': 'success',
            'message': 'Memory deleted successfully'
        })
    except Exception as e:
        logger.error(f"Error deleting memory: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@web_bp.route('/api/end_session', methods=['POST'])
def end_session():
    """End a conversation session and store it permanently."""
    try:
        data = request.json
        conversation_id = data.get('conversation_id')
        remember = data.get('remember', True)
        
        if not conversation_id:
            return jsonify({'status': 'error', 'message': 'No conversation ID provided'}), 400
        
        # Get agent with the existing conversation ID
        agent = get_agent(
            llm_model=session.get('llm_model', 'gemini-2.0-flash'),
            google_enabled=session.get('google_enabled', False),
            conversation_id=conversation_id
        )
        
        # End conversation
        result = agent.agent.end_conversation(remember=remember)
        
        return jsonify({
            'status': 'success',
            'message': 'Conversation ended successfully',
            'memory_id': result
        })
    except Exception as e:
        logger.error(f"Error ending session: {str(e)}", exc_info=True)
        return jsonify({'status': 'error', 'message': str(e)}), 500

# Helper functions for memory management

def create_short_term_memory(conversation_id, user_input, assistant_response):
    """
    Create a short-term memory from a conversation exchange.
    
    Args:
        conversation_id (str): The conversation ID
        user_input (str): The user's message
        assistant_response (str): The assistant's response
        
    Returns:
        str: The ID of the created memory
    """
    # Create a summary of the conversation (100 words max)
    conversation_text = f"User: {user_input}\nAssistant: {assistant_response}"
    
    # Truncate to approximately 100 words if needed
    words = re.findall(r'\w+', conversation_text)
    if len(words) > 100:
        # Find the end of the sentence closest to 100 words
        end_markers = ['. ', '! ', '? ']
        truncated_text = ' '.join(words[:100])
        
        # Find the last sentence end before 100 words
        last_end = -1
        for marker in end_markers:
            pos = conversation_text.rfind(marker, 0, len(truncated_text) + 20)
            if pos > last_end:
                last_end = pos
        
        if last_end > 0:
            conversation_text = conversation_text[:last_end + 1]
        else:
            # If no sentence end found, just truncate at 100 words
            conversation_text = truncated_text + '...'
    
    # Create memory
    memory_id = str(uuid.uuid4())
    memory = {
        'id': memory_id,
        'conversation_id': conversation_id,
        'content': conversation_text,
        'type': 'short',
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat()
    }
    
    # Save memory to storage
    save_memory(memory)
    
    return memory_id

def save_memory(memory):
    """
    Save a memory to storage.
    
    Args:
        memory (dict): The memory to save
    """
    # Create memory directory if it doesn't exist
    memory_dir = MEMORY_STORAGE_PATH / memory['conversation_id'] / memory['type']
    memory_dir.mkdir(parents=True, exist_ok=True)
    
    # Save memory to file
    memory_file = memory_dir / f"{memory['id']}.json"
    with open(memory_file, 'w') as f:
        json.dump(memory, f, indent=2)

def load_memories(conversation_id, memory_type='short'):
    """
    Load memories for a conversation.
    
    Args:
        conversation_id (str): The conversation ID
        memory_type (str): The type of memories to load (short, mid, long)
        
    Returns:
        list: List of memories
    """
    memory_dir = MEMORY_STORAGE_PATH / conversation_id / memory_type
    
    if not memory_dir.exists():
        return []
    
    memories = []
    for memory_file in memory_dir.glob('*.json'):
        try:
            with open(memory_file, 'r') as f:
                memory = json.load(f)
                memories.append(memory)
        except Exception as e:
            logger.error(f"Error loading memory from {memory_file}: {str(e)}")
    
    # Sort memories by creation date (newest first)
    memories.sort(key=lambda m: m.get('created_at', ''), reverse=True)
    
    return memories

def find_memory_by_id(memory_id):
    """
    Find a memory by ID.
    
    Args:
        memory_id (str): The memory ID
        
    Returns:
        dict: The memory if found, None otherwise
    """
    # Search all memory directories
    for conversation_dir in MEMORY_STORAGE_PATH.glob('*'):
        if not conversation_dir.is_dir():
            continue
            
        for memory_type_dir in conversation_dir.glob('*'):
            if not memory_type_dir.is_dir():
                continue
                
            memory_file = memory_type_dir / f"{memory_id}.json"
            if memory_file.exists():
                try:
                    with open(memory_file, 'r') as f:
                        return json.load(f)
                except Exception as e:
                    logger.error(f"Error loading memory from {memory_file}: {str(e)}")
    
    return None

def delete_memory_from_storage(memory_id):
    """
    Delete a memory from storage.
    
    Args:
        memory_id (str): The memory ID
    """
    # Search all memory directories
    for conversation_dir in MEMORY_STORAGE_PATH.glob('*'):
        if not conversation_dir.is_dir():
            continue
            
        for memory_type_dir in conversation_dir.glob('*'):
            if not memory_type_dir.is_dir():
                continue
                
            memory_file = memory_type_dir / f"{memory_id}.json"
            if memory_file.exists():
                memory_file.unlink()
                return 