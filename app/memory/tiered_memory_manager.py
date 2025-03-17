import os
import json
import time
import logging
import datetime
from typing import Dict, List, Optional, Any, Union

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TieredMemoryManager:
    """
    Manage tiered memory storage with short-term, medium-term, and long-term memories.
    
    This class handles the creation, retrieval, and management of memory objects across
    different tiers based on their importance and recency.
    """
    
    def __init__(self, storage_path: str = "data/memories"):
        """
        Initialize the TieredMemoryManager.
        
        Args:
            storage_path: Base path for memory storage
        """
        self.storage_path = storage_path
        self._ensure_directories()
        logger.info(f"Initialized TieredMemoryManager with storage path: {storage_path}")
    
    def _ensure_directories(self):
        """Ensure all necessary directories exist."""
        # Main data directory
        os.makedirs("data", exist_ok=True)
        
        # Memory type directories
        os.makedirs(os.path.join(self.storage_path, "short"), exist_ok=True)
        os.makedirs(os.path.join(self.storage_path, "medium"), exist_ok=True)
        os.makedirs(os.path.join(self.storage_path, "long"), exist_ok=True)
        
        logger.info("Memory directories ensured")
    
    def get_memory_by_query(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve memories by semantic search based on a query.
        
        Args:
            query: The search query
            limit: Maximum number of memories to return (default 5)
            
        Returns:
            A list of memory objects matching the query
        """
        if not query:
            return self._get_latest_memories(limit)
        
        # In a real implementation, this would perform semantic search
        # For now, we'll just do a simple text search across all memory types
        
        memories = []
        memory_types = ["short", "medium", "long"]
        
        for memory_type in memory_types:
            memory_dir = os.path.join(self.storage_path, memory_type)
            if not os.path.exists(memory_dir):
                continue
            
            # Check each memory file for matches
            for filename in os.listdir(memory_dir):
                if not filename.endswith('.json'):
                    continue
                
                try:
                    file_path = os.path.join(memory_dir, filename)
                    with open(file_path, 'r') as f:
                        memory = json.load(f)
                    
                    content = memory.get("content", "")
                    if query.lower() in content.lower():
                        memories.append(memory)
                        
                        if len(memories) >= limit:
                            return memories
                except Exception as e:
                    logger.error(f"Error loading memory file {filename}: {str(e)}")
        
        return memories
    
    def _get_latest_memories(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get the most recent memories across all types."""
        all_memories = []
        memory_types = ["short", "medium", "long"]
        
        for memory_type in memory_types:
            memory_dir = os.path.join(self.storage_path, memory_type)
            if not os.path.exists(memory_dir):
                continue
            
            for filename in os.listdir(memory_dir):
                if not filename.endswith('.json'):
                    continue
                
                try:
                    file_path = os.path.join(memory_dir, filename)
                    with open(file_path, 'r') as f:
                        memory = json.load(f)
                    
                    memory['file_path'] = file_path
                    all_memories.append(memory)
                except Exception as e:
                    logger.error(f"Error loading memory file {filename}: {str(e)}")
        
        # Sort by creation date (newest first)
        all_memories.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        # Return only the requested number of memories
        return all_memories[:limit]
    
    def create_memory(self, conversation_id: str, content: str, memory_type: str = "short") -> Dict[str, Any]:
        """
        Create a new memory in the specified tier.
        
        Args:
            conversation_id: ID of the associated conversation
            content: The memory content
            memory_type: Type of memory ("short", "medium", or "long")
            
        Returns:
            The created memory object
        """
        # Validate memory type
        if memory_type not in ["short", "medium", "long"]:
            memory_type = "short"  # Default to short-term memory
        
        try:
            # Generate timestamp for filename
            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            filename = f"{conversation_id}_{timestamp}.json"
            file_path = os.path.join(self.storage_path, memory_type, filename)
            
            # Create memory object
            memory = {
                "id": f"{conversation_id}_{timestamp}",
                "conversation_id": conversation_id,
                "content": content,
                "type": memory_type,
                "created_at": datetime.datetime.now().isoformat(),
                "updated_at": datetime.datetime.now().isoformat()
            }
            
            # Save to file
            with open(file_path, 'w') as f:
                json.dump(memory, f, indent=2)
            
            logger.info(f"Created {memory_type} memory for conversation {conversation_id}")
            return memory
        except Exception as e:
            logger.error(f"Error creating memory: {str(e)}")
            raise
    
    def create_conversation_summary(self, conversation_id: str, summary: str, type: str = "short") -> Dict[str, Any]:
        """
        Create a summary memory for a conversation.
        
        Args:
            conversation_id: The conversation ID
            summary: The summary text
            type: Memory type (short, medium, long)
            
        Returns:
            The created memory object
        """
        return self.create_memory(conversation_id, summary, type)
    
    def get_memories_by_conversation(self, conversation_id: str, memory_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all memories for a specific conversation.
        
        Args:
            conversation_id: The conversation ID
            memory_type: Optional memory type filter
            
        Returns:
            List of memory objects
        """
        memories = []
        
        # Determine which memory types to search
        memory_types = ["short", "medium", "long"] if memory_type is None else [memory_type]
        
        for type_name in memory_types:
            memory_dir = os.path.join(self.storage_path, type_name)
            if not os.path.exists(memory_dir):
                continue
            
            # Find memory files for this conversation
            for filename in os.listdir(memory_dir):
                if filename.startswith(f"{conversation_id}_") and filename.endswith('.json'):
                    try:
                        file_path = os.path.join(memory_dir, filename)
                        with open(file_path, 'r') as f:
                            memory = json.load(f)
                        
                        memories.append(memory)
                    except Exception as e:
                        logger.error(f"Error loading memory file {filename}: {str(e)}")
        
        # Sort by created_at date (newest first)
        memories.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        return memories
    
    def promote_memory(self, memory_id: str, target_type: str) -> Dict[str, Any]:
        """
        Promote a memory to a higher tier.
        
        Args:
            memory_id: The memory ID to promote
            target_type: The target memory type
            
        Returns:
            The updated memory object
        """
        # Ensure target_type is valid
        if target_type not in ["medium", "long"]:
            raise ValueError(f"Invalid target memory type: {target_type}")
        
        # Find the memory file
        memory_types = ["short", "medium", "long"]
        memory_file = None
        memory = None
        
        for type_name in memory_types:
            memory_dir = os.path.join(self.storage_path, type_name)
            if not os.path.exists(memory_dir):
                continue
            
            for filename in os.listdir(memory_dir):
                if filename.endswith('.json'):
                    try:
                        file_path = os.path.join(memory_dir, filename)
                        with open(file_path, 'r') as f:
                            data = json.load(f)
                        
                        if data.get("id") == memory_id:
                            memory_file = file_path
                            memory = data
                            break
                    except Exception as e:
                        logger.error(f"Error checking memory file {filename}: {str(e)}")
            
            if memory_file:
                break
        
        if not memory_file or not memory:
            raise ValueError(f"Memory with ID {memory_id} not found")
        
        # Skip if already at target type
        if memory.get("type") == target_type:
            return memory
        
        # Create new memory in target type
        conversation_id = memory.get("conversation_id")
        content = memory.get("content")
        
        # Create the promoted memory
        promoted = self.create_memory(conversation_id, content, target_type)
        
        # Delete the original memory file
        try:
            os.remove(memory_file)
            logger.info(f"Deleted original memory after promotion: {memory_file}")
        except Exception as e:
            logger.error(f"Error deleting original memory file: {str(e)}")
        
        return promoted 