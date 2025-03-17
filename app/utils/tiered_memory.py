"""
Tiered Memory Management System for Bahá'í Life Coach

This module provides tiered memory capabilities, organizing memories into short,
mid, and long-term categories. It uses SQLite for fast, efficient storage and
retrieval.
"""
import os
import json
import time
import logging
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple, Union
from functools import lru_cache

from app.config.settings import ENABLE_MEMORY_TRACKING
from app.models.llm import get_llm_model
from app.utils.memory_db import MemoryDatabase

# Set up logging
logger = logging.getLogger(__name__)

class TieredMemoryManager:
    """
    Manages tiered memory storage and retrieval optimized for performance.
    
    Features:
    - Caches memory retrieval results to reduce database calls
    - Only injects memory context at the start of a conversation
    - Creates memories only when explicitly requested or at conversation end
    - Uses SQLite for efficient storage and querying
    """
    
    def __init__(self, user_id: str = "default_user"):
        """
        Initialize the memory manager for a specific user.
        
        Args:
            user_id: The user identifier for managing memories
        """
        self.user_id = user_id
        self.db = MemoryDatabase()
        self.memory_cache = {}  # Cache to store retrieved memories
        self.memory_enabled = ENABLE_MEMORY_TRACKING
        self.current_conversation_id = None
        self.current_messages = []
        
        logger.info(f"TieredMemoryManager initialized for user {user_id}")
        
        if not self.memory_enabled:
            logger.warning("Memory tracking is disabled in settings")
    
    def start_conversation(self, conversation_id: Optional[str] = None) -> str:
        """
        Start a new conversation and prepare memory context.
        
        Args:
            conversation_id: Optional conversation ID. If None, a new ID is generated.
            
        Returns:
            The conversation ID
        """
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
            
        self.current_conversation_id = conversation_id
        self.current_messages = []
        
        # Clear cached memories for this conversation
        if conversation_id in self.memory_cache:
            del self.memory_cache[conversation_id]
            
        logger.info(f"Started conversation {conversation_id}")
        return conversation_id
    
    def add_message(self, role: str, content: str):
        """
        Add a message to the current conversation.
        
        Args:
            role: Message role (user, assistant, system)
            content: Message content
        """
        if not self.current_conversation_id:
            logger.warning("No active conversation found, starting a new one")
            self.start_conversation()
            
        self.current_messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
    
    @lru_cache(maxsize=32)
    def get_memory_context(self, conversation_id: str) -> str:
        """
        Get memory context for a conversation, formatted for inclusion in a prompt.
        Uses caching to avoid redundant database calls.
        
        Args:
            conversation_id: The conversation ID
            
        Returns:
            Formatted memory context string
        """
        if not self.memory_enabled:
            return ""
            
        memories = self.get_memories_for_conversation(conversation_id)
        if not any(memories.values()):
            return ""
            
        context_parts = []
        context_parts.append("Here are relevant memories about previous interactions:")
        
        # Add long-term memories if available
        if memories.get("long"):
            context_parts.append("\nLong-term memories (key insights and patterns):")
            context_parts.append(memories["long"]["content"])
            
        # Add mid-term memories if available
        if memories.get("mid"):
            context_parts.append("\nMid-term memories (recent conversations and topics):")
            context_parts.append(memories["mid"]["content"])
            
        # Add short-term memories if available
        if memories.get("short"):
            context_parts.append("\nShort-term memories (latest conversation):")
            context_parts.append(memories["short"]["content"])
            
        return "\n".join(context_parts)
    
    def get_memories_for_conversation(self, conversation_id: str) -> Dict[str, Any]:
        """
        Get memories relevant to a conversation.
        Uses caching to optimize performance.
        
        Args:
            conversation_id: The conversation ID
            
        Returns:
            Dictionary of memories by type
        """
        if not self.memory_enabled:
            return {"short": None, "mid": None, "long": None}
            
        # Check cache first
        if conversation_id in self.memory_cache:
            logger.debug(f"Using cached memories for conversation {conversation_id}")
            return self.memory_cache[conversation_id]
        
        # Retrieve from database
        memories = self.db.get_latest_memories(self.user_id)
        
        # Store in cache
        self.memory_cache[conversation_id] = memories
        
        return memories
    
    def end_conversation(self, remember: bool = True) -> Optional[str]:
        """
        End the current conversation and optionally create a memory.
        
        Args:
            remember: Whether to create a memory from this conversation
            
        Returns:
            Memory ID if created, None otherwise
        """
        if not self.current_conversation_id or not self.current_messages:
            logger.warning("No active conversation to end")
            return None
            
        conversation_id = self.current_conversation_id
        
        # Store conversation transcript
        if self.memory_enabled:
            self.db.store_conversation_transcript(
                self.user_id,
                conversation_id,
                self.current_messages
            )
        
        # Create memory if requested
        memory_id = None
        if remember and self.memory_enabled:
            memory_id = self.create_memory_from_conversation(conversation_id, self.current_messages)
            
        # Reset current conversation
        self.current_conversation_id = None
        self.current_messages = []
        
        logger.info(f"Ended conversation {conversation_id}")
        return memory_id
    
    def create_memory_from_conversation(
        self, 
        conversation_id: str, 
        messages: List[Dict[str, Any]], 
        memory_type: str = "short"
    ) -> Optional[str]:
        """
        Create a memory from a conversation.
        
        Args:
            conversation_id: The conversation ID
            messages: List of message objects
            memory_type: Memory type (short, mid, long)
            
        Returns:
            Memory ID if created, None otherwise
        """
        if not self.memory_enabled or not messages:
            return None
            
        # Check if there are enough messages to create a memory
        user_messages = [m for m in messages if m.get("role") == "user"]
        if len(user_messages) < 3:
            logger.info(f"Not enough user messages ({len(user_messages)}) to create memory")
            return None
            
        try:
            # Generate summary using LLM
            summary = self._generate_summary(messages)
            
            # Create memory object
            timestamp = datetime.now().isoformat()
            memory_id = f"{conversation_id}-{memory_type}-{int(time.time())}"
            
            memory_data = {
                "id": memory_id,
                "user_id": self.user_id,
                "conversation_id": conversation_id,
                "content": summary,
                "type": memory_type,
                "created_at": timestamp,
                "updated_at": timestamp
            }
            
            # Store in database
            success = self.db.store_memory(memory_data)
            
            if success:
                # Clear cache to ensure fresh memories next time
                if conversation_id in self.memory_cache:
                    del self.memory_cache[conversation_id]
                logger.info(f"Created {memory_type} memory for conversation {conversation_id}")
                return memory_id
            else:
                logger.error(f"Failed to store memory for conversation {conversation_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating memory: {e}")
            return None
    
    def create_memory_now(self, content: str, memory_type: str = "short") -> Optional[str]:
        """
        Create a memory immediately with custom content.
        
        Args:
            content: Memory content
            memory_type: Memory type (short, mid, long)
            
        Returns:
            Memory ID if created, None otherwise
        """
        if not self.memory_enabled:
            return None
            
        if not self.current_conversation_id:
            logger.warning("No active conversation for creating memory")
            return None
            
        try:
            # Create memory object
            timestamp = datetime.now().isoformat()
            memory_id = f"{self.current_conversation_id}-{memory_type}-{int(time.time())}"
            
            memory_data = {
                "id": memory_id,
                "user_id": self.user_id,
                "conversation_id": self.current_conversation_id,
                "content": content,
                "type": memory_type,
                "created_at": timestamp,
                "updated_at": timestamp
            }
            
            # Store in database
            success = self.db.store_memory(memory_data)
            
            if success:
                # Clear cache to ensure fresh memories next time
                if self.current_conversation_id in self.memory_cache:
                    del self.memory_cache[self.current_conversation_id]
                logger.info(f"Created custom {memory_type} memory for conversation {self.current_conversation_id}")
                return memory_id
            else:
                logger.error(f"Failed to store custom memory for conversation {self.current_conversation_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating custom memory: {e}")
            return None
    
    def _generate_summary(self, messages: List[Dict[str, Any]]) -> str:
        """
        Generate a summary of a conversation using the LLM.
        
        Args:
            messages: List of message objects
            
        Returns:
            Summary text
        """
        try:
            # Format conversation for LLM
            conversation_text = ""
            for msg in messages:
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                if content and role in ["user", "assistant"]:
                    conversation_text += f"{role.capitalize()}: {content}\n\n"
            
            # Create prompt for LLM
            prompt = f"""
            Below is a conversation between a user and a Bahá'í life coach assistant.
            Please generate a concise summary of this conversation in 20-100 words.
            Focus on the key points, questions asked, and insights shared.
            
            Conversation:
            {conversation_text}
            
            Summary:
            """
            
            # Get LLM instance (using singleton pattern)
            llm = get_llm_model()
            
            # Generate summary
            response = llm.invoke(prompt)
            
            # Extract content from response
            if hasattr(response, 'content'):
                summary = response.content
            else:
                summary = str(response)
                
            # Clean up summary
            summary = summary.strip()
            
            # Ensure summary is not too long
            words = summary.split()
            if len(words) > 100:
                summary = " ".join(words[:100]) + "..."
                
            logger.info(f"Generated summary: {summary[:50]}...")
            return summary
            
        except Exception as e:
            logger.error(f"Error creating conversation summary: {e}")
            # Fallback to a simple summary
            return self._create_fallback_summary(messages)
    
    def _create_fallback_summary(self, messages: List[Dict[str, Any]]) -> str:
        """
        Create a simple summary by extracting parts of messages when LLM is unavailable.
        
        Args:
            messages: List of message objects
            
        Returns:
            Basic summary text
        """
        logger.info("Using fallback summary method")
        
        # Get recent messages (up to 5)
        recent_messages = messages[-min(5, len(messages)):]
        
        # Extract content
        content_parts = []
        for msg in recent_messages:
            role = msg.get("role", "unknown")
            text = msg.get("content", "")
            if text and role in ["user", "assistant"]:
                # Take first sentence or truncate
                first_sentence = text.split('.')[0]
                if len(first_sentence) > 50:
                    first_sentence = first_sentence[:50] + "..."
                content_parts.append(f"{role.capitalize()}: {first_sentence}")
        
        # Join content parts
        summary = " ".join(content_parts)
        
        # Ensure minimum length
        if len(summary.split()) < 20:
            summary += " This conversation explored Bahá'í principles and spiritual guidance."
            
        logger.info(f"Fallback summary: {summary[:50]}...")
        return summary
    
    def get_all_memories(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get all memories for the current user.
        
        Returns:
            Dictionary with memory types as keys and lists of memories as values
        """
        if not self.memory_enabled:
            return {"short": [], "mid": [], "long": []}
            
        result = {"short": [], "mid": [], "long": []}
        
        try:
            conn = self.db._get_connection()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT * FROM memories WHERE user_id = ? ORDER BY created_at DESC",
                (self.user_id,)
            )
            
            rows = cursor.fetchall()
            conn.close()
            
            for row in rows:
                data = dict(row)
                memory_type = data.get("memory_type", "short")
                if memory_type in result:
                    result[memory_type].append(data)
                    
            return result
            
        except Exception as e:
            logger.error(f"Error retrieving all memories: {e}")
            return result
    
    def clear_memory_cache(self):
        """Clear the memory cache to force fresh database queries"""
        self.memory_cache.clear()
        self.get_memory_context.cache_clear()
        logger.info("Memory cache cleared") 