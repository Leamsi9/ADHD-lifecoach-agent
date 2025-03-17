"""
Memory Database Module for Bahá'í Life Coach Application

This module implements database operations for storing and retrieving memories.
Uses SQLite for lightweight, file-based storage with fast query capabilities.
"""
import os
import json
import sqlite3
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Union
import glob
import threading

# Setup logging
logger = logging.getLogger(__name__)

class MemoryDB:
    """
    A singleton database class for managing memory operations.
    This class provides optimized memory storage and retrieval.
    """
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(MemoryDB, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._initialized = True
        self._cache = {
            'short': {},
            'mid': {},
            'long': {}
        }
        self._latest_memory = {
            'short': None,
            'mid': None,
            'long': None
        }
        self._memory_path = os.environ.get('MEMORY_STORAGE_PATH', 'memory_storage')
        self._initialize_memory_path()
        self._load_cache()
    
    def _initialize_memory_path(self):
        """Initialize the memory storage directories."""
        if not os.path.exists(self._memory_path):
            os.makedirs(self._memory_path)
            logger.info(f"Created memory storage directory at {self._memory_path}")
    
    def _load_cache(self):
        """Load all memories into cache for faster access."""
        logger.info("Loading memory cache...")
        
        # Walk through memory directory structure
        for memory_type in ['short', 'mid', 'long']:
            type_path = os.path.join(self._memory_path, '**', memory_type)
            memory_files = glob.glob(f"{type_path}/*.json", recursive=True)
            
            latest_timestamp = None
            latest_memory = None
            
            for file_path in memory_files:
                try:
                    with open(file_path, 'r') as f:
                        memory = json.load(f)
                    
                    conversation_id = memory.get('conversation_id', 'default')
                    if conversation_id not in self._cache[memory_type]:
                        self._cache[memory_type][conversation_id] = []
                    
                    self._cache[memory_type][conversation_id].append(memory)
                    
                    # Track latest memory of each type
                    timestamp = memory.get('created_at')
                    if timestamp and (latest_timestamp is None or timestamp > latest_timestamp):
                        latest_timestamp = timestamp
                        latest_memory = memory
                
                except Exception as e:
                    logger.error(f"Error loading memory from {file_path}: {str(e)}")
            
            # Set latest memory for this type
            self._latest_memory[memory_type] = latest_memory
        
        logger.info("Memory cache loaded successfully")
    
    def add_memory(self, memory: Dict[str, Any]) -> None:
        """
        Add a new memory to the database.
        
        Args:
            memory: Dictionary containing memory data
        """
        try:
            # Validate memory
            required_fields = ['id', 'conversation_id', 'content', 'type']
            for field in required_fields:
                if field not in memory:
                    raise ValueError(f"Memory missing required field: {field}")
            
            memory_type = memory['type']
            conversation_id = memory['conversation_id']
            
            # Set timestamps if not present
            if 'created_at' not in memory:
                memory['created_at'] = datetime.now().isoformat()
            if 'updated_at' not in memory:
                memory['updated_at'] = memory['created_at']
            
            # Create directory structure
            conversation_path = os.path.join(self._memory_path, conversation_id, memory_type)
            os.makedirs(conversation_path, exist_ok=True)
            
            # Create file path with timestamp in name
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            file_name = f"{memory['id']}_{timestamp}.json"
            file_path = os.path.join(conversation_path, file_name)
            
            # Save to file
            with open(file_path, 'w') as f:
                json.dump(memory, f, indent=2)
            
            # Update cache
            if conversation_id not in self._cache[memory_type]:
                self._cache[memory_type][conversation_id] = []
            
            self._cache[memory_type][conversation_id].append(memory)
            
            # Update latest memory if this is newer
            current_latest = self._latest_memory[memory_type]
            if current_latest is None or memory['created_at'] > current_latest['created_at']:
                self._latest_memory[memory_type] = memory
            
            logger.info(f"Added {memory_type} memory for conversation {conversation_id}")
            
        except Exception as e:
            logger.error(f"Error adding memory: {str(e)}")
            raise
    
    def get_memories(self, memory_type: str, conversation_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get memories of a specific type, optionally filtered by conversation.
        
        Args:
            memory_type: Type of memory to retrieve (short, mid, long)
            conversation_id: Optional conversation ID to filter by
        
        Returns:
            List of memory objects
        """
        if memory_type not in ['short', 'mid', 'long']:
            raise ValueError(f"Invalid memory type: {memory_type}")
        
        # If conversation_id provided, filter by it
        if conversation_id:
            return self._cache[memory_type].get(conversation_id, [])
        
        # Otherwise, return all memories of this type
        all_memories = []
        for conv_memories in self._cache[memory_type].values():
            all_memories.extend(conv_memories)
        
        # Sort by created_at timestamp, newest first
        all_memories.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        return all_memories
    
    def get_latest_memory(self, memory_type: str) -> Optional[Dict[str, Any]]:
        """
        Get the most recent memory of a specific type.
        
        Args:
            memory_type: Type of memory to retrieve (short, mid, long)
        
        Returns:
            Most recent memory object or None if no memories exist
        """
        if memory_type not in ['short', 'mid', 'long']:
            raise ValueError(f"Invalid memory type: {memory_type}")
        
        return self._latest_memory[memory_type]
    
    def search_memories(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for memories containing the given query.
        
        Args:
            query: Search string to look for in memory content
        
        Returns:
            List of memory objects matching the query
        """
        results = []
        
        # Search across all memory types and conversations
        for memory_type in ['short', 'mid', 'long']:
            for conversation_memories in self._cache[memory_type].values():
                for memory in conversation_memories:
                    content = memory.get('content', '').lower()
                    if query.lower() in content:
                        results.append(memory)
        
        # Sort by created_at timestamp, newest first
        results.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        return results
    
    def delete_memory(self, memory_id: str) -> bool:
        """
        Delete a memory by ID.
        
        Args:
            memory_id: ID of the memory to delete
        
        Returns:
            True if successful, False otherwise
        """
        # Search for the memory in the cache
        for memory_type in ['short', 'mid', 'long']:
            for conversation_id, memories in self._cache[memory_type].items():
                for i, memory in enumerate(memories):
                    if memory.get('id') == memory_id:
                        # Remove from cache
                        removed_memory = self._cache[memory_type][conversation_id].pop(i)
                        
                        # Remove file
                        conversation_path = os.path.join(self._memory_path, conversation_id, memory_type)
                        memory_files = glob.glob(f"{conversation_path}/{memory_id}_*.json")
                        
                        for file_path in memory_files:
                            try:
                                os.remove(file_path)
                                logger.info(f"Deleted memory file: {file_path}")
                            except Exception as e:
                                logger.error(f"Error deleting memory file {file_path}: {str(e)}")
                        
                        # Update latest memory if needed
                        if self._latest_memory[memory_type] and self._latest_memory[memory_type].get('id') == memory_id:
                            # Find new latest memory
                            memories = self.get_memories(memory_type)
                            if memories:
                                self._latest_memory[memory_type] = memories[0]
                            else:
                                self._latest_memory[memory_type] = None
                        
                        return True
        
        logger.warning(f"Memory {memory_id} not found for deletion")
        return False
    
    def clear_cache(self):
        """Clear the memory cache and reload from disk."""
        self._cache = {
            'short': {},
            'mid': {},
            'long': {}
        }
        self._latest_memory = {
            'short': None,
            'mid': None,
            'long': None
        }
        self._load_cache()
        
    def get_memory_stats(self):
        """
        Get statistics about memories in the database.
        
        Returns:
            Dictionary with memory statistics
        """
        stats = {
            'total_memories': 0,
            'short_term': 0,
            'mid_term': 0,
            'long_term': 0,
            'conversations': set()
        }
        
        for memory_type in ['short', 'mid', 'long']:
            for conversation_id, memories in self._cache[memory_type].items():
                count = len(memories)
                stats['total_memories'] += count
                
                if memory_type == 'short':
                    stats['short_term'] += count
                elif memory_type == 'mid':
                    stats['mid_term'] += count
                elif memory_type == 'long':
                    stats['long_term'] += count
                
                stats['conversations'].add(conversation_id)
        
        # Convert set to list for JSON serialization
        stats['conversations'] = list(stats['conversations'])
        stats['conversation_count'] = len(stats['conversations'])
        
        return stats

class MemoryDatabase:
    """
    SQLite database for memory storage and retrieval.
    Provides fast, indexed queries for memory operations.
    """
    
    def __init__(self, db_path='data/memory.db'):
        """
        Initialize the memory database.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._ensure_directory_exists()
        self._initialize_db()
        logger.info(f"Memory database initialized at {db_path}")
    
    def _ensure_directory_exists(self):
        """Ensure the directory for the database file exists"""
        db_dir = os.path.dirname(self.db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
    
    def _initialize_db(self):
        """Create tables and indexes if they don't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create memories table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS memories (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            conversation_id TEXT NOT NULL,
            content TEXT NOT NULL,
            memory_type TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            relevance_score REAL DEFAULT 0.0
        )
        ''')
        
        # Create conversation_transcripts table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversation_transcripts (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            messages TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        ''')
        
        # Create indexes for faster retrieval
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_id ON memories(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_memory_type ON memories(memory_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_created_at ON memories(created_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_conversation_id ON memories(conversation_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_transcript_user_id ON conversation_transcripts(user_id)')
        
        conn.commit()
        conn.close()
    
    def get_latest_memories(self, user_id: str, limit_per_type: int = 1) -> Dict[str, Any]:
        """
        Get the latest memory of each type for a user.
        
        Args:
            user_id: User identifier
            limit_per_type: Number of memories to retrieve per type
            
        Returns:
            Dictionary with memory types as keys and memory objects as values
        """
        result = {
            "short": None,
            "mid": None,
            "long": None
        }
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Return results as dictionaries
        cursor = conn.cursor()
        
        for memory_type in ["short", "mid", "long"]:
            cursor.execute(
                """
                SELECT * FROM memories 
                WHERE user_id = ? AND memory_type = ? 
                ORDER BY created_at DESC LIMIT ?
                """,
                (user_id, memory_type, limit_per_type)
            )
            
            rows = cursor.fetchall()
            if rows:
                # Convert row to dictionary
                result[memory_type] = dict(rows[0])
        
        conn.close()
        return result
    
    def get_memory_by_id(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific memory by ID.
        
        Args:
            memory_id: Memory identifier
            
        Returns:
            Memory object if found, None otherwise
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM memories WHERE id = ?", (memory_id,))
        row = cursor.fetchone()
        
        conn.close()
        return dict(row) if row else None
    
    def get_memories_by_conversation(self, conversation_id: str) -> List[Dict[str, Any]]:
        """
        Get all memories for a specific conversation.
        
        Args:
            conversation_id: Conversation identifier
            
        Returns:
            List of memory objects
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM memories WHERE conversation_id = ? ORDER BY created_at DESC",
            (conversation_id,)
        )
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def store_memory(self, memory_data: Dict[str, Any]) -> bool:
        """
        Store a new memory in the database.
        
        Args:
            memory_data: Memory data dictionary with:
                - id: Unique identifier
                - user_id: User identifier
                - conversation_id: Conversation identifier
                - content: Memory content
                - type: Memory type (short, mid, long)
                - created_at: Creation timestamp
                - updated_at: Update timestamp
                
        Returns:
            True if successful, False otherwise
        """
        try:
            if 'id' not in memory_data:
                memory_data['id'] = f"{memory_data.get('conversation_id', 'unknown')}-{memory_data.get('type', 'unknown')}-{int(time.time())}"
            
            required_fields = ['id', 'user_id', 'conversation_id', 'content', 'type', 'created_at', 'updated_at']
            for field in required_fields:
                if field not in memory_data and field != 'type':
                    # Handle 'type' separately since it might be 'memory_type' instead
                    if field == 'type' and 'memory_type' in memory_data:
                        memory_data['type'] = memory_data['memory_type']
                    else:
                        logger.error(f"Missing required field {field} in memory data")
                        return False
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Handling both "type" and "memory_type" fields for flexibility
            memory_type = memory_data.get('type', memory_data.get('memory_type', 'short'))
            
            cursor.execute(
                """
                INSERT OR REPLACE INTO memories 
                (id, user_id, conversation_id, content, memory_type, created_at, updated_at, relevance_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    memory_data['id'],
                    memory_data['user_id'],
                    memory_data['conversation_id'],
                    memory_data['content'],
                    memory_type,
                    memory_data['created_at'],
                    memory_data['updated_at'],
                    memory_data.get('relevance_score', 0.0)
                )
            )
            
            conn.commit()
            conn.close()
            logger.info(f"Stored {memory_type} memory with ID {memory_data['id']}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing memory: {e}")
            return False
    
    def store_conversation_transcript(self, user_id: str, conversation_id: str, messages: List[Dict[str, Any]]) -> bool:
        """
        Store a conversation transcript.
        
        Args:
            user_id: User identifier
            conversation_id: Conversation identifier
            messages: List of message objects
            
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Convert messages to JSON string
            messages_json = json.dumps(messages)
            timestamp = datetime.now().isoformat()
            
            cursor.execute(
                """
                INSERT OR REPLACE INTO conversation_transcripts
                (id, user_id, messages, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (
                    conversation_id,
                    user_id,
                    messages_json,
                    timestamp
                )
            )
            
            conn.commit()
            conn.close()
            logger.info(f"Stored transcript for conversation {conversation_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing conversation transcript: {e}")
            return False
    
    def get_conversation_transcript(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a conversation transcript.
        
        Args:
            conversation_id: Conversation identifier
            
        Returns:
            Transcript object if found, None otherwise
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM conversation_transcripts WHERE id = ?",
            (conversation_id,)
        )
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            data = dict(row)
            # Parse messages JSON
            data['messages'] = json.loads(data['messages'])
            return data
        
        return None
    
    def search_memories(self, user_id: str, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search memories using simple text matching.
        
        Args:
            user_id: User identifier
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of matching memory objects
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(
            """
            SELECT * FROM memories
            WHERE user_id = ? AND content LIKE ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (user_id, f"%{query}%", limit)
        )
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def delete_memory(self, memory_id: str) -> bool:
        """
        Delete a memory from the database.
        
        Args:
            memory_id: Memory identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
            
            deleted = cursor.rowcount > 0
            conn.commit()
            conn.close()
            
            if deleted:
                logger.info(f"Deleted memory with ID {memory_id}")
            else:
                logger.warning(f"Memory with ID {memory_id} not found for deletion")
                
            return deleted
            
        except Exception as e:
            logger.error(f"Error deleting memory: {e}")
            return False
            
    def clean_database(self):
        """
        Vacuum the database to reclaim space and optimize performance.
        Should be called periodically for maintenance.
        """
        conn = sqlite3.connect(self.db_path)
        conn.execute("VACUUM")
        conn.close()
        logger.info("Database cleaned and optimized") 