#!/usr/bin/env python3
"""
Script to generate memories from conversation files.

This script:
1. Scans the conversations directory
2. For each conversation file, checks if it has at least 3 user prompts
3. Generates a 20-100 word summary using Gemini API
4. Saves the summary in the appropriate memory directory (short/medium/long)
5. Uses a filename that includes conversation ID and timestamp

Usage:
    python create_memories.py [--force]

Options:
    --force    Process all conversations, even if they already have associated memories
"""

import os
import sys
import json
import time
import argparse
import logging
from datetime import datetime
import re
import random
from typing import Dict, List, Any, Tuple, Optional, Union
from dotenv import load_dotenv
from pathlib import Path
import shutil
import uuid

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
CONVERSATIONS_DIR = "data/conversations"
MEMORIES_DIR = "data/memories"
MIN_USER_PROMPTS = 3
MAX_SUMMARY_WORDS = 100
MIN_SUMMARY_WORDS = 20

# Load environment variables
load_dotenv()

# Initialize LLM - Only use Gemini
llm = None
try:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    if GEMINI_API_KEY:
        from langchain_google_genai import ChatGoogleGenerativeAI
        # Use the model from environment or a fallback
        gemini_model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        logger.info(f"Loading Gemini model from environment: {gemini_model}")
        llm = ChatGoogleGenerativeAI(
            model=gemini_model,
            google_api_key=GEMINI_API_KEY,
            temperature=0.7
        )
        logger.info(f"Gemini LLM initialized with model: {gemini_model}")
    else:
        logger.warning("Gemini API key not found in environment variables, will use fallback method")
except ImportError as e:
    logger.error(f"Error importing Gemini dependencies: {e}")
except Exception as e:
    logger.error(f"Error initializing Gemini: {e}")

def create_summary(messages: List[Dict[str, Any]]) -> str:
    """
    Create a 20-100 word summary of the conversation using Gemini.
    
    Uses Gemini to generate a concise summary, with a fallback
    method if Gemini is unavailable.
    """
    if not messages or len(messages) < MIN_USER_PROMPTS:
        return "Conversation was too brief to summarize meaningfully."
    
    # Try to use Gemini for summary
    if llm:
        try:
            # Format the conversation for the LLM
            conversation_text = ""
            for msg in messages:
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                if content and role in ["user", "assistant"]:
                    conversation_text += f"{role.capitalize()}: {content}\n\n"
            
            # Create a prompt for the LLM
            prompt = f"""
            Below is a conversation between a user and a Bahá'í life coach assistant.
            Please generate a concise summary of this conversation in {MIN_SUMMARY_WORDS}-{MAX_SUMMARY_WORDS} words.
            Focus on the key points, questions asked, and insights shared.
            
            Conversation:
            {conversation_text}
            
            Summary:
            """
            
            # Generate summary using Gemini
            response = llm.invoke(prompt).content
            
            # Clean up and ensure word count requirements
            summary = response.strip()
            words = summary.split()
            
            if len(words) > MAX_SUMMARY_WORDS:
                summary = " ".join(words[:MAX_SUMMARY_WORDS]) + "..."
            elif len(words) < MIN_SUMMARY_WORDS:
                summary += " " + "This conversation explored Bahá'í principles and teachings."
                
            logger.info(f"Generated Gemini summary: {summary[:50]}...")
            return summary
            
        except Exception as e:
            logger.error(f"Error generating summary with Gemini: {e}")
            logger.info("Falling back to simple summary method")
    else:
        logger.warning("Gemini not available for summary generation, using fallback method")
    
    # Fallback summary method
    # Get the last few messages (up to 5)
    recent_messages = messages[-min(5, len(messages)):]
    
    # Extract content from messages
    content = []
    for msg in recent_messages:
        role = msg.get("role", "unknown")
        text = msg.get("content", "")
        if text and role in ["user", "assistant"]:
            # Take first sentence or truncate
            first_sentence = re.split(r'[.!?]', text)[0]
            content.append(f"{role.capitalize()}: {first_sentence}")
    
    # Join all parts
    full_summary = " ".join(content)
    
    # Count words
    words = full_summary.split()
    
    # Ensure summary is between 20-100 words
    if len(words) > MAX_SUMMARY_WORDS:
        full_summary = " ".join(words[:MAX_SUMMARY_WORDS]) + "..."
    elif len(words) < MIN_SUMMARY_WORDS:
        full_summary += " " + "This was a brief exchange about Bahá'í principles."
        
    logger.info(f"Generated fallback summary: {full_summary[:50]}...")
    return full_summary

def load_conversation(file_path: str) -> List[Dict[str, Any]]:
    """
    Load conversation from a file.
    Handles different data structures for conversation files.
    """
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Handle different data structures
        if isinstance(data, list):
            # Direct list of messages
            messages = data
        elif isinstance(data, dict):
            # Check for messages field
            if 'messages' in data:
                messages = data['messages']
            elif 'conversation' in data:
                messages = data['conversation']
            else:
                # Try to extract messages from the first key that contains a list
                for key, value in data.items():
                    if isinstance(value, list) and value and isinstance(value[0], dict) and 'role' in value[0]:
                        messages = value
                        break
                else:
                    logger.warning(f"Could not find messages in conversation file: {file_path}")
                    return []
        else:
            logger.warning(f"Unexpected data format in file: {file_path}")
            return []
        
        # Process messages to ensure they're in the correct format
        processed_messages = []
        for msg in messages:
            # If message is a string, convert to dict
            if isinstance(msg, str):
                # Try to determine if it's a user or assistant message
                if msg.startswith("User:") or msg.lower().startswith("user:"):
                    processed_messages.append({"role": "user", "content": msg.split(":", 1)[1].strip()})
                elif msg.startswith("Assistant:") or msg.lower().startswith("assistant:"):
                    processed_messages.append({"role": "assistant", "content": msg.split(":", 1)[1].strip()})
                else:
                    # Default to user message if can't determine
                    processed_messages.append({"role": "user", "content": msg})
            elif isinstance(msg, dict):
                # Ensure each message has role and content
                if 'role' not in msg:
                    msg['role'] = 'unknown'
                if 'content' not in msg and 'text' in msg:
                    msg['content'] = msg['text']
                processed_messages.append(msg)
        
        conversation_id = get_conversation_id_from_filename(file_path)
        logger.info(f"Loaded conversation {conversation_id} with {len(processed_messages)} messages")
        return processed_messages
    except json.JSONDecodeError:
        logger.error(f"Error decoding JSON from file: {file_path}")
        return []
    except Exception as e:
        logger.error(f"Error loading conversation from {file_path}: {e}")
        return []

def get_conversation_id_from_filename(filename: str) -> str:
    """Extract conversation ID from filename."""
    # Remove file extension and any path components
    base_name = os.path.basename(filename)
    conversation_id = os.path.splitext(base_name)[0]
    return conversation_id

def get_timestamp() -> str:
    """Generate a timestamp for memory filenames."""
    return datetime.now().strftime("%Y%m%d%H%M%S")

def ensure_memory_structure():
    """Ensure memory directory structure exists."""
    # Make sure base memory directory exists
    Path(MEMORIES_DIR).mkdir(parents=True, exist_ok=True)
    
    # We don't need to create conversation-specific directories in advance
    # They will be created as needed when processing each conversation

def create_memory_file(conversation_id: str, summary: str, memory_type: str = "short") -> Optional[str]:
    """
    Create a memory file for a conversation.
    
    Args:
        conversation_id: ID of the conversation
        summary: Summary text of the conversation
        memory_type: Type of memory (short, mid, long)
    
    Returns:
        Path to the created memory file or None if failed
    """
    if not summary:
        logger.warning(f"Empty summary for conversation {conversation_id}, skipping")
        return None
    
    # Make sure we're using a valid memory type
    if memory_type not in ["short", "mid", "long"]:
        logger.warning(f"Invalid memory type: {memory_type}, defaulting to short")
        memory_type = "short"
    
    # Create directory structure
    memory_dir = Path(MEMORIES_DIR) / memory_type
    memory_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate filename with timestamp
    timestamp = get_timestamp()
    memory_id = f"{conversation_id}-{memory_type}-{timestamp}"
    filename = f"{memory_id}.json"
    file_path = memory_dir / filename
    
    # Create memory object
    memory_data = {
        "id": memory_id,
        "conversation_id": conversation_id,
        "content": summary,
        "type": memory_type,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    # Write to file
    try:
        with open(file_path, 'w') as f:
            json.dump(memory_data, f, indent=2)
        logger.info(f"Created {memory_type} memory for conversation {conversation_id}: {file_path}")
        return str(file_path)
    except Exception as e:
        logger.error(f"Failed to create memory file: {e}")
        return None

def process_conversation_file(file_path: str, force: bool = False) -> Optional[str]:
    """
    Process a single conversation file and create a memory.
    
    Args:
        file_path: Path to conversation file
        force: Force processing even if memory already exists
    
    Returns:
        Path to created memory file or None if failed
    """
    # Extract conversation ID from filename
    conversation_id = get_conversation_id_from_filename(os.path.basename(file_path))
    
    # Check if memory already exists for this conversation
    memory_dir = Path(MEMORIES_DIR) / conversation_id / "short"
    if memory_dir.exists() and not force:
        existing_files = list(memory_dir.glob("*.json"))
        if existing_files:
            logger.info(f"Memory already exists for conversation {conversation_id}, skipping")
            return None
    
    # Load conversation
    messages = load_conversation(file_path)
    if not messages:
        logger.warning(f"No valid messages found in {file_path}")
        return None
    
    # Count user prompts
    user_prompts = sum(1 for msg in messages if msg.get('role') == 'user')
    if user_prompts < MIN_USER_PROMPTS:
        logger.info(f"Skipping {file_path}: only {user_prompts} user prompts (need {MIN_USER_PROMPTS})")
        return None
    
    # Create summary
    summary = create_summary(messages)
    
    # Create memory file
    return create_memory_file(conversation_id, summary, "short")

def process_all_conversations(force: bool = False) -> List[str]:
    """
    Process all conversation files and create memories.
    
    Args:
        force: Force processing even if memories already exist
    
    Returns:
        List of created memory files
    """
    # Ensure the memory structure is in place
    ensure_memory_structure()
    
    created_files = []
    conversations_dir = Path(CONVERSATIONS_DIR)
    if not conversations_dir.exists():
        logger.error(f"Conversations directory not found: {CONVERSATIONS_DIR}")
        return []
    
    conversation_files = list(conversations_dir.glob("*.json"))
    
    logger.info(f"Found {len(conversation_files)} conversation files")
    
    for file_path in conversation_files:
        memory_file = process_conversation_file(str(file_path), force)
        if memory_file:
            created_files.append(memory_file)
    
    logger.info(f"Created {len(created_files)} memory files")
    return created_files

def migrate_legacy_data(source_dir: str = "memory_storage") -> int:
    """
    Migrate data from legacy directory structure to new structure.
    
    Args:
        source_dir: Legacy source directory
    
    Returns:
        Number of files migrated
    """
    if not os.path.exists(source_dir):
        logger.warning(f"Legacy source directory not found: {source_dir}")
        return 0
    
    migrated_count = 0
    source_path = Path(source_dir)
    
    # Look for conversation directories
    for conv_dir in source_path.iterdir():
        if not conv_dir.is_dir():
            continue
        
        conversation_id = conv_dir.name
        
        # Process memory types (short, mid, long)
        for mem_type_dir in conv_dir.iterdir():
            if not mem_type_dir.is_dir():
                continue
            
            memory_type = mem_type_dir.name
            if memory_type not in ["short", "mid", "long"]:
                continue
            
            # Create target directory
            target_dir = Path(MEMORIES_DIR) / memory_type
            target_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy memory files
            for memory_file in mem_type_dir.glob("*.json"):
                try:
                    # Check if file needs timestamp
                    target_filename = memory_file.name
                    if not re.search(r'\d{14}', target_filename):
                        # Add timestamp to filename
                        timestamp = get_timestamp()
                        base_name = os.path.splitext(target_filename)[0]
                        target_filename = f"{base_name}-{timestamp}.json"
                    
                    target_path = target_dir / target_filename
                    
                    # Copy file
                    shutil.copy2(memory_file, target_path)
                    migrated_count += 1
                    logger.info(f"Migrated: {memory_file} -> {target_path}")
                    
                except Exception as e:
                    logger.error(f"Error migrating {memory_file}: {e}")
    
    logger.info(f"Migrated {migrated_count} memory files from legacy structure")
    return migrated_count

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Create memories from conversation data")
    parser.add_argument("--force", action="store_true", help="Force recreation of memories")
    parser.add_argument("--migrate", action="store_true", help="Migrate data from legacy structure")
    parser.add_argument("--memory-type", choices=["short", "mid", "long"], default="short", 
                        help="Memory type to create (default: short)")
    args = parser.parse_args()
    
    if args.migrate:
        migrate_count = migrate_legacy_data()
        if migrate_count > 0:
            logger.info(f"Successfully migrated {migrate_count} memory files")
        else:
            logger.warning("No files were migrated")
    
    created_files = process_all_conversations(force=args.force)
    
    if created_files:
        logger.info(f"Successfully created {len(created_files)} memory files")
    else:
        logger.info("No new memory files were created")

if __name__ == "__main__":
    main() 