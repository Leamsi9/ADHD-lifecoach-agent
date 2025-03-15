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
MEMORY_DIR = "data/memories"
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
    
    def extract_facts(self, conversation_history: List[Dict[str, str]]) -> List[str]:
        """
        Extract key facts from a conversation history.
        
        Args:
            conversation_history: List of message dictionaries with role and content.
            
        Returns:
            List of extracted facts.
        """
        # Combine all messages into a single text for analysis
        full_text = "\n".join([msg["content"] for msg in conversation_history])
        
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
    
    def store_facts(self, facts: List[str]) -> None:
        """
        Store facts in memory.
        
        Args:
            facts: List of facts to store.
        """
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
    
    def get_relevant_memories(self, query: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get memories relevant to a query.
        
        Args:
            query: Optional query to filter memories.
            
        Returns:
            List of relevant memories.
        """
        if not query:
            # Return all memories sorted by recency
            return sorted(self.memories, key=lambda x: x["timestamp"], reverse=True)
        
        # Simple keyword matching for now
        # In a more advanced implementation, this could use vector embeddings for semantic search
        query_terms = query.lower().split()
        scored_memories = []
        
        for memory in self.memories:
            content = memory["content"].lower()
            # Count how many query terms appear in the memory
            score = sum(1 for term in query_terms if term in content)
            if score > 0:
                scored_memories.append((memory, score))
        
        # Sort by score (descending), then by timestamp (most recent first)
        return [memory for memory, score in sorted(
            scored_memories, 
            key=lambda x: (x[1], x[0]["timestamp"]), 
            reverse=True
        )]
    
    def add_explicit_memory(self, content: str) -> None:
        """
        Add an explicitly requested memory.
        
        Args:
            content: The content to remember.
        """
        if not self._fact_exists(content):
            self.memories.append({
                "content": content,
                "timestamp": datetime.now().isoformat(),
                "source": "explicit_request"
            })
            self._save_memories()
            logger.info(f"Stored explicit memory: {content}")
    
    def get_summary_for_new_conversation(self) -> str:
        """
        Get a summary of important memories for a new conversation.
        
        Returns:
            A summary string with important memories.
        """
        if not self.memories:
            return ""
        
        # Prioritize explicit memories and recent memories
        explicit_memories = [m for m in self.memories if m["source"] == "explicit_request"]
        recent_memories = sorted(self.memories, key=lambda x: x["timestamp"], reverse=True)[:5]
        
        # Combine and deduplicate
        important_memories = []
        seen_contents = set()
        
        for memory in explicit_memories + recent_memories:
            if memory["content"] not in seen_contents:
                important_memories.append(memory)
                seen_contents.add(memory["content"])
        
        # Format summary
        if not important_memories:
            return ""
        
        summary = "Previous session information:\n"
        for memory in important_memories[:7]:  # Limit to 7 most important facts
            summary += f"- {memory['content']}\n"
        
        return summary
    
    def _ensure_memory_dir_exists(self) -> None:
        """Ensure the memory directory exists."""
        os.makedirs(MEMORY_DIR, exist_ok=True)
    
    def _get_memory_file_path(self) -> str:
        """Get the path to the memory file for this conversation."""
        return os.path.join(MEMORY_DIR, f"{self.conversation_id}.json")
    
    def _load_memories(self) -> List[Dict[str, Any]]:
        """Load memories from file."""
        file_path = self._get_memory_file_path()
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                logger.error(f"Error loading memories from {file_path}")
                return []
        return []
    
    def _save_memories(self) -> None:
        """Save memories to file."""
        file_path = self._get_memory_file_path()
        with open(file_path, 'w') as f:
            json.dump(self.memories, f, indent=2)
    
    def _fact_exists(self, fact: str) -> bool:
        """Check if a fact already exists or is very similar to an existing fact."""
        fact_lower = fact.lower()
        for memory in self.memories:
            existing_fact = memory["content"].lower()
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
        # Convert texts to sets of words
        set1 = set(text1.split())
        set2 = set(text2.split())
        
        # Calculate Jaccard similarity
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        return intersection / union if union > 0 else 0
    
    def _extract_explicit_memories(self, text: str) -> List[str]:
        """Extract explicitly requested memories from text."""
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
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                fact = match.group(0).strip()
                if fact and len(fact) > 10:
                    facts.append(fact)
        
        return facts
    
    def _filter_similar_facts(self, facts: List[str]) -> List[str]:
        """Filter out facts that are similar to each other."""
        if not facts:
            return []
        
        unique_facts = [facts[0]]
        
        for fact in facts[1:]:
            # Check if this fact is similar to any existing unique fact
            if not any(self._calculate_similarity(fact.lower(), unique.lower()) > SIMILARITY_THRESHOLD 
                      for unique in unique_facts):
                unique_facts.append(fact)
        
        return unique_facts 