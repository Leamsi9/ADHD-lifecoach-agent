#!/usr/bin/env python3
"""
Test script for the tiered memory system in the Bahai Life Coach application.
This demonstrates the memory summarization and tiered promotion functionality.
"""

import os
import time
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set memory tracking to enabled
os.environ["ENABLE_MEMORY_TRACKING"] = "True"

from app.utils.tiered_memory import TieredMemoryManager
from app.agents.life_coach_agent import LifeCoachAgent

def display_header(text):
    """Display a formatted header."""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80)

def display_memory(memory, indent=0):
    """Display a memory object in a readable format."""
    indent_str = " " * indent
    if not memory:
        print(f"{indent_str}No memory found")
        return
    
    print(f"{indent_str}Timestamp: {memory.get('timestamp', 'Unknown')}")
    print(f"{indent_str}Type: {memory.get('type', 'Unknown')}")
    print(f"{indent_str}Summary: {memory.get('summary', 'No summary')}")
    
    # Show source memories or conversation ID
    if 'source_memories' in memory:
        print(f"{indent_str}Source memories: {len(memory.get('source_memories', []))} items")
    elif 'conversation_id' in memory:
        print(f"{indent_str}Conversation ID: {memory.get('conversation_id', 'Unknown')}")
    
    print()

def test_memory_system():
    """Test the tiered memory system with simulated conversations."""
    display_header("TESTING TIERED MEMORY SYSTEM")
    
    # Create memory manager and agent
    memory_manager = TieredMemoryManager(user_id="test_user")
    agent = LifeCoachAgent()
    
    # Simulate multiple conversations
    display_header("SIMULATING CONVERSATIONS")
    
    # Generate 12 simulated conversations (to trigger mid-term memory)
    for i in range(1, 13):
        print(f"Simulating conversation {i}...")
        
        # Create simulated messages
        messages = [
            {"role": "user", "content": f"I've been thinking about the Bahá'í concept of unity. Can you tell me more about it in conversation {i}?"},
            {"role": "assistant", "content": f"Unity is indeed a central concept in the Bahá'í Faith. Bahá'u'lláh teaches that humanity is one family and that 'The earth is but one country, and mankind its citizens.' This principle applies to both our spiritual and social reality."},
            {"role": "user", "content": f"How can I apply this principle of unity in my daily life during conversation {i}?"},
            {"role": "assistant", "content": f"You can practice unity in daily life by seeing everyone as part of one human family, eliminating prejudice from your heart, and actively working to build bridges between different groups. Small acts of including others and respecting diverse perspectives embody this principle."},
            {"role": "user", "content": f"That's helpful. I'll try to be more inclusive in conversation {i}."},
            {"role": "assistant", "content": f"That's a wonderful start! Remember that unity doesn't mean uniformity—it celebrates our diversity while recognizing our essential oneness. I look forward to hearing about your experiences as you practice this principle."}
        ]
        
        # Store conversation and summary
        conversation_id = f"test_convo_{i}"
        memory = memory_manager.create_conversation_summary(conversation_id, messages)
        
        print(f"Created short-term memory for conversation {i}")
        
        # Small delay to ensure different timestamps
        time.sleep(0.5)
    
    # Display memory hierarchy
    display_header("MEMORY HIERARCHY AFTER SIMULATIONS")
    
    # Check short-term memories
    short_term_memories = memory_manager._get_memories_in_dir(memory_manager.short_term_path)
    print(f"Short-term memories: {len(short_term_memories)}")
    
    # Check mid-term memories
    mid_term_memories = memory_manager._get_memories_in_dir(memory_manager.mid_term_path)
    print(f"Mid-term memories: {len(mid_term_memories)}")
    if mid_term_memories:
        print("\nMost recent mid-term memory:")
        display_memory(sorted(mid_term_memories, key=lambda x: x.get("timestamp", ""), reverse=True)[0], indent=2)
    
    # Check long-term memories
    long_term_memories = memory_manager._get_memories_in_dir(memory_manager.long_term_path)
    print(f"Long-term memories: {len(long_term_memories)}")
    
    # Demonstrate memory query
    display_header("MEMORY QUERY TEST")
    query = "Tell me about unity in the Bahá'í Faith"
    print(f"Query: '{query}'")
    relevant_memories = memory_manager.get_memory_by_query(query)
    
    print(f"Found {len(relevant_memories)} relevant memories\n")
    for i, memory in enumerate(relevant_memories):
        print(f"Memory {i+1} (Relevance score: {memory.get('relevance_score', 'N/A')}):")
        display_memory(memory, indent=2)
    
    # Demonstrate session context
    display_header("SESSION CONTEXT TEST")
    session_context = memory_manager.get_session_context()
    
    print("Session context contains:")
    for key, memory in session_context.items():
        print(f"\n{key.upper()}:")
        display_memory(memory, indent=2)
    
    display_header("TEST COMPLETED")
    print("The tiered memory system has been tested with simulated conversations.")
    print("The system should have created short-term memories for each conversation.")
    print("It should also have created at least one mid-term memory (after 10 short-term memories).")
    print("\nMEMORY STORAGE LOCATION:")
    print(f"Memory files are stored in: {memory_manager.memory_base_path}")

if __name__ == "__main__":
    test_memory_system() 