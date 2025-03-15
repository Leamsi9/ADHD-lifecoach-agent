"""
Agent Adapter Module for the Bahai Life Coach.

This module serves as an adapter that replaces the LifeCoachAgent with DirectCoachAgent 
while maintaining the same interface for the routes.
"""

from typing import Dict, List, Any, Optional
import logging
from app.agents.direct_coach_agent import DirectCoachAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global agent instance
_direct_agent = None

def get_agent(conversation_id: Optional[str] = None) -> DirectCoachAgent:
    """
    Get the current agent instance or create a new one if needed.
    
    Args:
        conversation_id: Optional conversation ID.
        
    Returns:
        The DirectCoachAgent instance.
    """
    global _direct_agent
    
    if _direct_agent is None or (conversation_id and _direct_agent.conversation_id != conversation_id):
        _direct_agent = DirectCoachAgent(conversation_id=conversation_id)
        
    return _direct_agent

# Function to replace the original LifeCoachAgent
class LifeCoachAgent:
    """
    Adapter class that mimics the interface of LifeCoachAgent but uses DirectCoachAgent internally.
    """
    
    def __init__(self, conversation_id: Optional[str] = None):
        """
        Initialize the adapter with a DirectCoachAgent.
        
        Args:
            conversation_id: An optional conversation ID to continue an existing conversation.
        """
        self._agent = get_agent(conversation_id)
        self.conversation_id = self._agent.conversation_id
        self.google_integration_data = self._agent.google_integration_data
        
    def provide_coaching(self, user_input: str) -> Dict[str, Any]:
        """
        Process user input and provide coaching response.
        
        Args:
            user_input: The user's input message.
            
        Returns:
            A dictionary containing the coaching response, conversation ID, and any insights.
        """
        result = self._agent.provide_coaching(user_input)
        self.google_integration_data = self._agent.google_integration_data
        return result
    
    def start_new_conversation(self) -> Dict[str, Any]:
        """
        Start a new conversation with context from previous sessions.
        
        Returns:
            A dictionary with the greeting and conversation ID.
        """
        return self._agent.start_new_conversation()
    
    def get_memories(self, query: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get memories relevant to a query.
        
        Args:
            query: Optional query to filter memories.
            
        Returns:
            List of relevant memories.
        """
        return self._agent.get_memories(query)
    
    def add_explicit_memory(self, content: str) -> None:
        """
        Add an explicitly requested memory.
        
        Args:
            content: The content to remember.
        """
        self._agent.add_explicit_memory(content)
        
# Patch the import system to use this adapter
import sys
import builtins
original_import = builtins.__import__

def patched_import(name, globals=None, locals=None, fromlist=(), level=0):
    result = original_import(name, globals, locals, fromlist, level)
    if name == 'app.agents.life_coach_agent' and fromlist and 'LifeCoachAgent' in fromlist:
        # Replace the LifeCoachAgent with our adapter
        logger.info("🔄 Using DirectCoachAgent via adapter instead of LifeCoachAgent")
        result.LifeCoachAgent = LifeCoachAgent
    return result

# Apply the patch
builtins.__import__ = patched_import 