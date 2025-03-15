"""
Main entry point for the Bahai Life Coach agent application.
"""

import os
import sys
import uuid
from typing import Dict, Any

# Add the parent directory to the Python path for proper imports
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from app.agents.life_coach_agent import LifeCoachAgent
from app.config.settings import validate_config

def process_input(user_input: str, conversation_id: str = None) -> Dict[str, Any]:
    """
    Process user input and return coaching response.
    
    Args:
        user_input: The user's message
        conversation_id: Optional ID for continuing an existing conversation
        
    Returns:
        Dict containing the coaching response and conversation metadata
    """
    agent = LifeCoachAgent(conversation_id=conversation_id)
    return agent.provide_coaching(user_input)

def print_welcome_message():
    """Print a welcome message for the console interface."""
    print("\n" + "=" * 80)
    print("""
    🌟 Bahai Life Coach Agent 🌟
    
    Welcome to your personal life coach, guided by Bahai principles.
    Share your thoughts, concerns, or questions, and receive compassionate guidance.
    
    Type 'exit' to end the conversation.
    """)
    print("=" * 80 + "\n")

def console_interface():
    """Run a simple console interface for interacting with the life coach agent."""
    try:
        print_welcome_message()
        
        conversation_id = str(uuid.uuid4())
        print(f"Conversation ID: {conversation_id}\n")
        
        while True:
            user_input = input("You: ")
            
            if user_input.lower() in ('exit', 'quit', 'bye'):
                print("\nThank you for the conversation. Wishing you peace and growth on your journey.\n")
                break
            
            try:
                result = process_input(user_input, conversation_id)
                print(f"\nCoach: {result['response']}\n")
            except Exception as e:
                print(f"An error occurred: {str(e)}")
                print("Please try again or type 'exit' to quit.")
    
    except KeyboardInterrupt:
        print("\n\nConversation ended. Farewell!\n")
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    try:
        # Validate configuration before starting
        validate_config()
        
        # Run the console interface
        sys.exit(console_interface())
    except ValueError as e:
        print(f"Configuration error: {str(e)}")
        print("Please check your .env file and ensure all required variables are set.")
        sys.exit(1) 