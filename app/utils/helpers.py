"""
Helper functions for the Bahai Life Coach agent.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional

def save_conversation(conversation_id: str, messages: List[Dict[str, Any]]) -> None:
    """
    Save conversation history to a JSON file.
    
    Args:
        conversation_id: Unique identifier for the conversation
        messages: List of message dictionaries
    """
    os.makedirs("conversations", exist_ok=True)
    
    # Create a filename based on the conversation ID
    filename = f"conversations/{conversation_id}.json"
    
    # Add timestamp to each message if not present
    for message in messages:
        if "timestamp" not in message:
            message["timestamp"] = datetime.now().isoformat()
    
    # Save to file
    with open(filename, "w") as f:
        json.dump(messages, f, indent=2)

def load_conversation(conversation_id: str) -> Optional[List[Dict[str, Any]]]:
    """
    Load conversation history from a JSON file.
    
    Args:
        conversation_id: Unique identifier for the conversation
        
    Returns:
        List of message dictionaries or None if file doesn't exist
    """
    filename = f"conversations/{conversation_id}.json"
    
    if not os.path.exists(filename):
        return None
    
    with open(filename, "r") as f:
        return json.load(f)

def extract_key_insights(text: str) -> List[str]:
    """
    A simple function to extract key insights from text.
    In a real application, this could use more sophisticated NLP techniques.
    
    Args:
        text: The text to analyze
        
    Returns:
        List of key insights extracted from the text
    """
    # Simple implementation - split by sentences and filter for length
    sentences = [s.strip() for s in text.split('.') if len(s.strip()) > 20]
    return sentences[:3]  # Return top 3 longest sentences as "insights"

def format_coaching_response(advice: str, reflections: List[str] = None) -> str:
    """
    Format a coaching response with advice and reflections.
    
    Args:
        advice: The main advice text
        reflections: Optional list of reflection questions
        
    Returns:
        Formatted response string
    """
    response = advice
    
    if reflections:
        response += "\n\nReflections to consider:\n"
        for i, reflection in enumerate(reflections, 1):
            response += f"{i}. {reflection}\n"
    
    return response 