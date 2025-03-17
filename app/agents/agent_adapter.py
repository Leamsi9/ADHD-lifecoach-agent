"""
Agent Adapter Module for the Bahai Life Coach.

This module provides a simplified interface for accessing the LifeCoachAgent.
"""

from typing import Dict, List, Any, Optional, Tuple, Union
import logging
import os
import json
import uuid

from app.models.llm import get_llm_model
from app.utils.memory_db import MemoryDB
from app.agents.life_coach_agent import LifeCoachAgent
from app.config.settings import ENABLE_MEMORY_TRACKING

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AgentAdapter:
    """
    Adapter class to provide a unified interface for different agent implementations.
    """
    def __init__(self, 
                 llm_model: str = 'gemini-2.0-flash',
                 google_enabled: bool = False,
                 conversation_id: Optional[str] = None,
                 include_memories: bool = False):
        """
        Initialize the agent adapter.
        
        Args:
            llm_model: The LLM model to use (e.g., 'gemini-2.0-flash', 'gpt-4o')
            google_enabled: Whether to enable Google search integration
            conversation_id: Optional conversation ID to continue
            include_memories: Whether to include memories in the prompt
        """
        self.llm_model = llm_model
        self.google_enabled = google_enabled
        self.include_memories = include_memories
        
        # Initialize LLM using singleton pattern
        # Note: We're not using llm directly in this class anymore, but keeping
        # the initialization for consistency and potential future use
        self.llm = get_llm_model()
        
        # Set conversation ID
        self.conversation_id = conversation_id or str(uuid.uuid4())
        
        # Initialize memory database if memory tracking is enabled
        self.memory_db = MemoryDB() if ENABLE_MEMORY_TRACKING else None
        
        # Initialize agent implementation
        self.agent = self._initialize_agent()
        
        logger.info(f"Agent initialized with model: {llm_model}, "
                    f"conversation_id: {self.conversation_id}, "
                    f"google_enabled: {google_enabled}, "
                    f"include_memories: {include_memories}")
    
    def _initialize_agent(self) -> Any:
        """
        Initialize the appropriate agent implementation.
        """
        # Pass user_id as conversation_id to maintain existing behavior
        # This approach ensures backward compatibility
        return LifeCoachAgent(
            conversation_id=self.conversation_id,
            google_enabled=self.google_enabled,
            llm_model=self.llm_model,
            include_memories=self.include_memories
        )
    
    def process_input(self, user_input: str) -> Tuple[str, Dict[str, Any]]:
        """
        Process user input and return a response.
        
        Args:
            user_input: The user's input message
            
        Returns:
            Tuple containing (response_text, metadata)
        """
        try:
            # Get response from agent
            result = self.agent.provide_coaching(user_input)
            
            # Extract response and metadata
            response = result.get('response', '')
            
            # Get additional metadata
            metadata = {
                'conversation_id': self.conversation_id,
                'insights': result.get('insights', [])
            }
            
            return response, metadata
            
        except Exception as e:
            logger.error(f"Error processing input: {str(e)}", exc_info=True)
            return f"I'm sorry, I encountered an error processing your request: {str(e)}", {
                'conversation_id': self.conversation_id,
                'error': str(e)
            }

def get_agent(llm_model: str = 'gemini-2.0-flash',
              google_enabled: bool = False,
              conversation_id: Optional[str] = None,
              include_memories: bool = False) -> AgentAdapter:
    """
    Factory function to create an agent adapter.
    
    Args:
        llm_model: The LLM model to use (e.g., 'gemini-2.0-flash', 'gpt-4o')
        google_enabled: Whether to enable Google search integration
        conversation_id: Optional conversation ID to continue
        include_memories: Whether to include memories in the prompt
        
    Returns:
        An initialized agent adapter
    """
    return AgentAdapter(
        llm_model=llm_model,
        google_enabled=google_enabled,
        conversation_id=conversation_id,
        include_memories=include_memories
    )

def retrieve_memories_for_agent(agent, conversation_id):
    """
    Retrieve memories for a specific conversation and load them into the agent.
    
    Args:
        agent: The agent instance
        conversation_id: The conversation ID to load memories for
    """
    logger.info(f"Retrieving memories for conversation {conversation_id}")
    
    if not hasattr(agent, 'memory_manager') or not agent.memory_manager:
        logger.warning("Agent does not have a memory manager, cannot retrieve memories")
        return
        
    # Use optimized memory retrieval if available
    if hasattr(agent.memory_manager, 'get_memories_for_conversation'):
        try:
            # Retrieve memories using optimized method
            memories = agent.memory_manager.get_memories_for_conversation(conversation_id)
            if memories:
                logger.info(f"Retrieved memories for conversation {conversation_id}: {list(memories.keys())}")
        except Exception as e:
            logger.error(f"Error retrieving memories: {str(e)}")
    else:
        # Legacy method for backward compatibility
        try:
            # Get memory context from agent
            # This is a simplified version that doesn't actually retrieve memories
            # but can be extended if needed
            logger.info("Using legacy memory retrieval method")
        except Exception as e:
            logger.error(f"Error retrieving memories: {str(e)}") 