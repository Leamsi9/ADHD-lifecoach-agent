"""
Memory module for the Bahai Life Coach agent.

This module handles the extraction, storage, and retrieval of facts from conversations.
"""

import json
import os
import re
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
MEMORY_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/memories"))
SIMILARITY_THRESHOLD = 0.7  # Threshold for considering facts similar


class MemoryManager:
    """Manager for handling the extraction, storage, and retrieval of facts."""
    
    def __init__(self, conversation_id: str):
        """
        Initialize the memory manager.
        
        Args:
            conversation_id: The ID of the conversation to manage memories for.
        """
        self.conversation_id = conversation_id
        self._ensure_memory_dir_exists()
        
        # Load existing memories
        self.memories = self._load_memories()
        
        # Track explicitly requested memories
        self.explicit_memory_requests = []
        
        logger.info(f"Memory manager initialized for conversation {conversation_id}")
        logger.info(f"Using memory directory: {MEMORY_DIR}")
    
    def extract_facts(self, conversation_history: List[Dict[str, str]]) -> List[str]:
        """
        Extract key facts from a conversation history.
        
        Args:
            conversation_history: List of message dictionaries with role and content.
            
        Returns:
            List of extracted facts.
        """
        if not conversation_history:
            return []
            
        try:
            # Combine all messages into a single text for analysis
            full_text = "\n".join([msg.get("content", "") for msg in conversation_history if msg.get("content")])
            
            # Extract explicit memory requests
            explicit_memories = self._extract_explicit_memories(full_text)
            
            # Extract key information based on patterns
            facts = []
            
            # Add explicit memories
            facts.extend(explicit_memories)
            
            # Extract information about goals, challenges, preferences
            facts.extend(self._extract_pattern_based_facts(full_text))
            
            # Filter out duplicates and similar facts
            unique_facts = self._filter_similar_facts(facts)
            
            return unique_facts
        except Exception as e:
            logger.error(f"Error extracting facts: {str(e)}")
            return []
    
    def store_facts(self, facts: List[str]) -> None:
        """
        Store facts in memory.
        
        Args:
            facts: List of facts to store.
        """
        if not facts:
            return
            
        try:
            # Check if facts already exist
            new_facts = []
            for fact in facts:
                if not self._fact_exists(fact):
                    new_facts.append({
                        "content": fact,
                        "timestamp": datetime.now().isoformat(),
                        "source": "conversation"
                    })
            
            # Add new facts to memory
            if new_facts:
                self.memories.extend(new_facts)
                self._save_memories()
                logger.info(f"Stored {len(new_facts)} new facts")
        except Exception as e:
            logger.error(f"Error storing facts: {str(e)}")
    
    def get_relevant_memories(self, query: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get memories relevant to a query.
        
        Args:
            query: Optional query to filter memories.
            limit: Maximum number of memories to return.
            
        Returns:
            List of relevant memories.
        """
        try:
            if not self.memories:
                logger.info("No memories found for retrieval")
                return []
                
            if not query:
                # Return all memories sorted by recency, limited to the specified limit
                return sorted(self.memories, key=lambda x: x.get("timestamp", ""), reverse=True)[:limit]
            
            # Simple keyword matching for now
            # In a more advanced implementation, this could use vector embeddings for semantic search
            query_terms = query.lower().split()
            scored_memories = []
            
            for memory in self.memories:
                content = memory.get("content", "").lower()
                # Count how many query terms appear in the memory
                score = sum(1 for term in query_terms if term in content)
                if score > 0:
                    scored_memories.append((memory, score))
            
            # Sort by score (descending), then by timestamp (most recent first)
            sorted_memories = [memory for memory, score in sorted(
                scored_memories, 
                key=lambda x: (x[1], x[0].get("timestamp", "")), 
                reverse=True
            )]
            
            return sorted_memories[:limit]
        except Exception as e:
            logger.error(f"Error retrieving memories: {str(e)}")
            return []
    
    def add_explicit_memory(self, content: str) -> None:
        """
        Add an explicitly requested memory.
        
        Args:
            content: The content to remember.
        """
        if not content:
            return
            
        try:
            if not self._fact_exists(content):
                self.memories.append({
                    "content": content,
                    "timestamp": datetime.now().isoformat(),
                    "source": "explicit_request"
                })
                self._save_memories()
                logger.info(f"Stored explicit memory: {content}")
        except Exception as e:
            logger.error(f"Error adding explicit memory: {str(e)}")
    
    def get_summary_for_new_conversation(self) -> str:
        """
        Get a summary of important memories for a new conversation.
        
        Returns:
            A summary string with important memories.
        """
        try:
            if not self.memories:
                return ""
            
            # Prioritize explicit memories and recent memories
            explicit_memories = [m for m in self.memories if m.get("source") == "explicit_request"]
            recent_memories = sorted(self.memories, key=lambda x: x.get("timestamp", ""), reverse=True)[:5]
            
            # Combine and deduplicate
            important_memories = []
            seen_contents = set()
            
            for memory in explicit_memories + recent_memories:
                if memory.get("content") not in seen_contents:
                    important_memories.append(memory)
                    seen_contents.add(memory.get("content", ""))
            
            # Format summary
            if not important_memories:
                return ""
            
            summary = "Previous session information:\n"
            for memory in important_memories[:7]:  # Limit to 7 most important facts
                summary += f"- {memory.get('content')}\n"
            
            return summary
        except Exception as e:
            logger.error(f"Error generating conversation summary: {str(e)}")
            return ""
    
    def _ensure_memory_dir_exists(self) -> None:
        """Ensure the memory directory exists."""
        global MEMORY_DIR  # Moved global declaration to beginning of function
        try:
            os.makedirs(MEMORY_DIR, exist_ok=True)
            logger.info(f"Ensured memory directory exists: {MEMORY_DIR}")
        except Exception as e:
            logger.error(f"Failed to create memory directory {MEMORY_DIR}: {str(e)}")
            # Try creating in a different location as fallback
            fallback_dir = os.path.join(os.getcwd(), "data", "memories")
            try:
                os.makedirs(fallback_dir, exist_ok=True)
                MEMORY_DIR = fallback_dir
                logger.info(f"Using fallback memory directory: {MEMORY_DIR}")
            except Exception as e2:
                logger.error(f"Failed to create fallback memory directory: {str(e2)}")
    
    def _get_memory_file_path(self) -> str:
        """Get the path to the memory file for this conversation."""
        return os.path.join(MEMORY_DIR, f"{self.conversation_id}.json")
    
    def _load_memories(self) -> List[Dict[str, Any]]:
        """Load memories from file."""
        file_path = self._get_memory_file_path()
        logger.info(f"Loading memories from: {file_path}")
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    memories = json.load(f)
                    logger.info(f"Loaded {len(memories)} memories")
                    return memories
            except json.JSONDecodeError as e:
                logger.error(f"Error loading memories from {file_path}: {str(e)}")
                return []
            except Exception as e:
                logger.error(f"Unexpected error loading memories: {str(e)}")
                return []
        else:
            logger.info(f"No existing memory file found at {file_path}")
            return []
    
    def _save_memories(self) -> None:
        """Save memories to file."""
        file_path = self._get_memory_file_path()
        try:
            with open(file_path, 'w') as f:
                json.dump(self.memories, f, indent=2)
            logger.info(f"Saved {len(self.memories)} memories to {file_path}")
        except Exception as e:
            logger.error(f"Error saving memories to {file_path}: {str(e)}")
    
    def _fact_exists(self, fact: str) -> bool:
        """Check if a fact already exists or is very similar to an existing fact."""
        if not fact:
            return False
            
        fact_lower = fact.lower()
        for memory in self.memories:
            existing_fact = memory.get("content", "").lower()
            # Simple string similarity using Jaccard similarity
            if self._calculate_similarity(fact_lower, existing_fact) > SIMILARITY_THRESHOLD:
                return True
        return False
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate text similarity using Jaccard similarity.
        
        Args:
            text1: First text string
            text2: Second text string
            
        Returns:
            Similarity score between 0 and 1
        """
        if not text1 or not text2:
            return 0.0
            
        # Convert texts to sets of words
        set1 = set(text1.split())
        set2 = set(text2.split())
        
        # Calculate Jaccard similarity
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        return intersection / union if union > 0 else 0
    
    def _extract_explicit_memories(self, text: str) -> List[str]:
        """Extract explicitly requested memories from text."""
        if not text:
            return []
            
        # Patterns for memory requests
        patterns = [
            r"remember that (.+?)(?:\.|$)",
            r"remember this:?\s*(.+?)(?:\.|$)",
            r"please remember (?:that )?(.+?)(?:\.|$)",
            r"can you remember (?:that )?(.+?)(?:\.|$)",
            r"store this (?:information|fact):?\s*(.+?)(?:\.|$)"
        ]
        
        memories = []
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                memory = match.group(1).strip()
                if memory and len(memory) > 5:
                    memories.append(memory)
        
        return memories
    
    def _extract_pattern_based_facts(self, text: str) -> List[str]:
        """Extract facts based on patterns indicating important information."""
        if not text:
            return []
            
        # Patterns for key information
        patterns = [
            # Goals
            r"my goal is (.+?)(?:\.|$)",
            r"i want to (.+?)(?:\.|$)",
            r"i'm trying to (.+?)(?:\.|$)",
            r"i am working on (.+?)(?:\.|$)",
            
            # Challenges
            r"i struggle with (.+?)(?:\.|$)",
            r"my challenge is (.+?)(?:\.|$)",
            r"i find it difficult to (.+?)(?:\.|$)",
            
            # Preferences
            r"i prefer (.+?)(?:\.|$)",
            r"i like (.+?)(?:\.|$)",
            r"i don't like (.+?)(?:\.|$)",
            
            # Personal information
            r"my name is (.+?)(?:\.|$)",
            r"i am (.+? years old)(?:\.|$)",
            r"i live in (.+?)(?:\.|$)",
            r"i work as a (.+?)(?:\.|$)",
            r"i work at (.+?)(?:\.|$)",
            
            # Bahá'í specific
            r"i've been a bahá'í for (.+?)(?:\.|$)",
            r"i'm involved with (.+? bahá'í.+?)(?:\.|$)"
        ]
        
        facts = []
        for pattern in patterns:
            try:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    fact = match.group(0).strip()
                    if fact and len(fact) > 10:
                        facts.append(fact)
            except Exception as e:
                logger.error(f"Error with pattern '{pattern}': {str(e)}")
                continue
        
        return facts
    
    def _filter_similar_facts(self, facts: List[str]) -> List[str]:
        """Filter out facts that are similar to each other."""
        if not facts:
            return []
        
        unique_facts = [facts[0]]
        
        for fact in facts[1:]:
            # Check if this fact is similar to any existing unique fact
            is_similar = False
            for unique in unique_facts:
                try:
                    if self._calculate_similarity(fact.lower(), unique.lower()) > SIMILARITY_THRESHOLD:
                        is_similar = True
                        break
                except Exception as e:
                    logger.error(f"Error calculating similarity: {str(e)}")
                    continue
                    
            if not is_similar:
                unique_facts.append(fact)
        
        return unique_facts 