"""
Life Coach Agent Module

This module implements the core Bahá'í Life Coach agent functionality.
The LifeCoachAgent class handles the main conversation flow, memory management,
and response generation using a singleton LLM pattern and optimized memory access.

Conversation Processing Logic:

1. System Prompt Injection:
   - A carefully crafted system prompt defines the agent's persona as a Bahá'í Life Coach
   - The prompt instructs the agent on how to interact, common topics, and boundaries
   - Values and principles from the Bahá'í Faith are embedded in the system prompt

2. Memory Handling:
   - Short-term memories (current session): Stored for immediate context
   - Medium-term memories (past sessions): Provide continuity between sessions
   - Long-term memories (important insights): Preserve core user information
   - Memories are retrieved at conversation start (latest of each type)
   - Explicit memories are created when the user wants to remember something specific

3. Response Generation Rules:
   - Responses are empathetic and supportive
   - Quotes from Bahá'í writings are included when relevant
   - The agent avoids giving medical advice or replacing professional therapy
   - Responses may include follow-up questions to encourage reflection
   - The agent can suggest prayers or spiritual practices

4. Conversation Flow:
   - Initial welcome message establishes the coaching relationship
   - Agent maintains context throughout the conversation
   - The agent can create insights by analyzing the conversation
"""

from typing import Dict, List, Any, Optional
import uuid
import logging
import os
import time
from datetime import datetime

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from app.config.settings import ENABLE_GOOGLE_INTEGRATION, ENABLE_MEMORY_TRACKING
from app.utils.tiered_memory import TieredMemoryManager
from app.models.llm import get_llm_model
from app.prompts.life_coach_prompts import LIFE_COACH_SYSTEM_PROMPT, BAHAI_QUOTES
from app.utils.memory_db import MemoryDB

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import Google integration modules if enabled
GOOGLE_IMPORTS_SUCCESSFUL = False
if ENABLE_GOOGLE_INTEGRATION:
    try:
        # Try to import the real implementations
        try:
            from app.integrations.google.calendar import get_upcoming_events
            from app.integrations.google.tasks import get_tasks, create_task
            GOOGLE_IMPORTS_SUCCESSFUL = True
            logger.info("✅ Google integration modules imported successfully")
        except ImportError:
            # Log the situation but don't provide mock implementations here
            logger.warning("⚠️ Google API client not installed.")
            logger.info("To enable Google integration, install the Google client libraries with:")
            logger.info("    pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
    except Exception as e:
        logger.warning(f"❌ Error setting up Google integration: {str(e)}")


class LifeCoachAgent:
    """
    A Bahá'í life coach agent that provides coaching based on Bahá'í principles,
    using an optimized memory system and singleton LLM instance for improved performance.
    """
    
    def __init__(self, 
                 conversation_id: Optional[str] = None, 
                 user_id: str = "default_user",
                 llm_model: str = "gemini-2.0-flash",
                 google_enabled: bool = False,
                 include_memories: bool = False):
        """
        Initialize the life coach agent with optimized memory and LLM access.
        
        Args:
            conversation_id: Optional conversation ID to continue an existing conversation
            user_id: User identifier for memory isolation
            llm_model: The LLM model to use (e.g., 'gemini-2.0-flash', 'gpt-4o')
            google_enabled: Whether to enable Google integration
            include_memories: Whether to include memories in responses
        """
        self.user_id = user_id or "default_user"
        self.conversation_id = conversation_id or str(uuid.uuid4())
        self.llm_model = llm_model
        self.google_enabled = google_enabled
        self.include_memories = include_memories
        
        # Initialize LLM using singleton pattern with the specified model
        # We use get_llm_model() which will use LLM_MODEL from settings unless overridden by env var
        if llm_model:
            # Set the environment variable to override the default model
            os.environ['LLM_MODEL'] = llm_model
            
        self.llm = get_llm_model(force_refresh=True)
        
        # Set memory tracking based on settings
        self.enable_memory = ENABLE_MEMORY_TRACKING
        if self.enable_memory:
            self.memory_manager = TieredMemoryManager(user_id=self.user_id)
            # Start conversation in memory manager
            if self.memory_manager:
                self.memory_manager.start_conversation(self.conversation_id)
        else:
            self.memory_manager = None
        
        # Initialize memory database if memory tracking is enabled
        self.memory_db = MemoryDB() if ENABLE_MEMORY_TRACKING else None
        
        # Initialize message history with system prompt
        self.messages = [
            SystemMessage(content=LIFE_COACH_SYSTEM_PROMPT)
        ]
        
        # Track if context has been initialized
        self.context_initialized = False
        
        logger.info("Initializing LifeCoachAgent with system prompt:")
        logger.info(LIFE_COACH_SYSTEM_PROMPT[:50] + "...")  # Show first 50 chars
        
        # Initialize Google integration status
        self.google_enabled = ENABLE_GOOGLE_INTEGRATION and GOOGLE_IMPORTS_SUCCESSFUL
        self.google_integration_data = {
            'enabled': self.google_enabled,
            'integration_used': False,
            'calendar_events': [],
            'tasks': []
        }
        
        # Track conversation messages for summary
        self.conversation_messages = []
        
        # Ensure context is initialized
        self._init_context()
    
    def _init_context(self):
        """Initialize the conversation context with system prompt and memories."""
        if not self.context_initialized:
            # Add system prompt (already added in __init__)
            
            # Get memory context if available
            if self.enable_memory and self.memory_manager:
                memory_context = self.memory_manager.get_memory_context(self.conversation_id)
                if memory_context:
                    self.messages.append(SystemMessage(content=memory_context))
            
            self.context_initialized = True
    
    def provide_coaching(self, user_input: str) -> Dict[str, Any]:
        """
        Process user input and provide coaching response directly using the LLM.
        
        Args:
            user_input: The user's input message.
            
        Returns:
            A dictionary containing the coaching response, conversation ID, and any insights.
        """
        start_time = time.time()
        
        # Check for explicit memory requests
        is_memory_request = False
        memory_query = None
        
        if "what do you remember about" in user_input.lower() or "recall our discussions on" in user_input.lower():
            is_memory_request = True
            memory_query = user_input
            
        # Check for integration requests
        integration_used = False
        if self.google_enabled:
            # Check for calendar-related keywords
            if any(keyword in user_input.lower() for keyword in ["calendar", "schedule", "appointment", "meeting", "event"]):
                self._update_google_data()
                integration_used = True
            
            # Check for task-related keywords
            if any(keyword in user_input.lower() for keyword in ["task", "todo", "to-do", "to do", "reminder"]):
                # Check if this is a task creation request
                if any(verb in user_input.lower() for verb in ["add", "create", "make", "set"]):
                    self._try_create_task(user_input)
                    integration_used = True
                else:
                    self._update_google_data()
                    integration_used = True
                
        # Add any relevant context from Google integration
        context = ""
        if integration_used and self.google_integration_data['calendar_events']:
            context += "\n\nUser's upcoming events:\n"
            for event in self.google_integration_data['calendar_events'][:3]:  # Limit to 3 events
                start_time = event.get('start', 'Unknown time')
                context += f"- {event.get('summary', 'Event')} at {start_time}\n"
        
        if integration_used and self.google_integration_data['tasks']:
            context += "\n\nUser's current tasks:\n"
            for task in self.google_integration_data['tasks'][:3]:  # Limit to 3 tasks
                context += f"- {task.get('title', 'Task')}\n"
                
        # Handle memory queries
        if is_memory_request and self.enable_memory and self.memory_manager:
            relevant_memories = self.memory_manager.get_memories_for_conversation(self.conversation_id)
            if relevant_memories:
                context += "\n\nRelevant memories from previous conversations:\n"
                for memory_type, memory in relevant_memories.items():
                    if memory:
                        context += f"- {memory_type.capitalize()}: {memory.get('content', '')}\n"
        # Get relevant memories if not a specific memory request
        elif self.enable_memory and self.memory_manager:
            memories = self.memory_manager.get_memories_for_conversation(self.conversation_id)
            if memories:
                context += "\n\nRelevant information from previous conversations:\n"
                for memory_type, memory in memories.items():
                    if memory:
                        context += f"- {memory_type.capitalize()}: {memory.get('content', '')}\n"
        
        # If we have context, add it as a system message
        if context:
            self.messages.append(SystemMessage(content=f"Context for your response:{context}"))
            
        # Add user message to history
        user_msg = HumanMessage(content=user_input)
        self.messages.append(user_msg)
        
        # Track for conversation summary and memory
        self.conversation_messages.append({"role": "user", "content": user_input})
        
        # Add message to memory manager
        if self.enable_memory and self.memory_manager:
            self.memory_manager.add_message("user", user_input)
        
        # Generate the response directly using the LLM
        try:
            response = self.llm.invoke(self.messages)
            coach_response = response.content if hasattr(response, 'content') else str(response)
            
            # Add assistant message to history
            ai_msg = AIMessage(content=coach_response)
            self.messages.append(ai_msg)
            
            # Track for conversation summary
            self.conversation_messages.append({"role": "assistant", "content": coach_response})
            
            # Add to memory manager
            if self.enable_memory and self.memory_manager:
                self.memory_manager.add_message("assistant", coach_response)
            
            # Extract insights for reflection only if memory tracking is enabled
            if self.enable_memory:
                insights = self._generate_reflection_questions(user_input, coach_response)
            else:
                insights = []
            
            # Log response time
            end_time = time.time()
            logger.info(f"Response generated in {end_time - start_time:.2f} seconds")
            
            # Return the response with all necessary information
            result = {
                'response': coach_response,
                'conversation_id': self.conversation_id,
                'insights': insights,
                'integration_used': integration_used
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return {
                'response': f"I'm sorry, I encountered an error: {str(e)}. Please try again or contact support.",
                'conversation_id': self.conversation_id,
                'error': str(e)
            }
    
    def start_new_conversation(self) -> Dict[str, Any]:
        """
        Start a new conversation with context from previous sessions.
        
        Returns:
            A dictionary with the greeting and conversation ID.
        """
        # Reset conversation messages for the new session
        self.conversation_messages = []
        self.context_initialized = False
        
        # Start a new conversation in memory manager
        if self.enable_memory and self.memory_manager:
            self.memory_manager.start_conversation(self.conversation_id)
        
        # Get memory context from optimized memory system
        memory_context = ""
        if self.enable_memory and self.memory_manager:
            memory_context = self.memory_manager.get_memory_context(self.conversation_id)
        
        # Generate a context-aware greeting using the LLM
        try:
            prompt = "You are a compassionate Bahá'í life coach starting a new coaching session."
            
            if memory_context:
                prompt += f"\n\n{memory_context}"
            
            prompt += "\n\nGenerate a warm, natural greeting to start a new conversation with the user."
            
            # Reset message history for new conversation
            self.messages = [
                SystemMessage(content=LIFE_COACH_SYSTEM_PROMPT),
                SystemMessage(content=prompt)
            ]
            
            # Mark context as initialized
            self.context_initialized = True
            
            response = self.llm.invoke(self.messages)
            greeting = response.content.strip()
            
            # Add assistant message to history
            ai_msg = AIMessage(content=greeting)
            self.messages.append(ai_msg)
            
            # Track for conversation summary
            self.conversation_messages.append({"role": "assistant", "content": greeting})
            
            # Add to memory manager
            if self.enable_memory and self.memory_manager:
                self.memory_manager.add_message("assistant", greeting)
            
        except Exception as e:
            # Fallback greeting if LLM fails
            logger.error(f"Error generating greeting: {str(e)}")
            greeting = "Welcome to your Bahá'í life coach session. How can I support you today?"
            
            # Add fallback greeting to history
            self.messages.append(AIMessage(content=greeting))
            self.conversation_messages.append({"role": "assistant", "content": greeting})
            
            # Add to memory manager
            if self.enable_memory and self.memory_manager:
                self.memory_manager.add_message("assistant", greeting)
        
        return {
            'response': greeting,
            'conversation_id': self.conversation_id
        }
    
    def _generate_reflection_questions(self, user_input: str, coach_response: str) -> List[str]:
        """
        Generate reflection questions based on the user input and coach response.
        
        Args:
            user_input: The user's input message.
            coach_response: The coach's response.
            
        Returns:
            A list of reflection questions.
        """
        # Use the LLM to generate personalized reflection questions
        try:
            # Create a prompt for the LLM
            prompt = f"""
Based on the following conversation between a user and a Bahá'í life coach, generate 3 thought-provoking reflection questions.
These questions should be personalized, insightful, and encourage deep thinking about the discussed topics.
They should relate to Bahá'í principles and help the user apply the wisdom to their specific situation.
Avoid formulaic expressions and create spontaneous, meaningful questions.

User: {user_input}

Coach: {coach_response}

Generate 3 reflection questions:
"""
            
            # Get response from LLM
            response = self.llm.invoke(prompt).content
            
            # Parse out the questions (assuming they're numbered or on separate lines)
            questions = []
            for line in response.strip().split('\n'):
                # Remove any numbering or bullet points
                clean_line = line.strip()
                if clean_line.startswith('1.') or clean_line.startswith('2.') or clean_line.startswith('3.'):
                    clean_line = clean_line[2:].strip()
                elif clean_line.startswith('-'):
                    clean_line = clean_line[1:].strip()
                    
                if clean_line and '?' in clean_line and len(clean_line) > 10:
                    questions.append(clean_line)
            
            # Return at least 1, maximum 3 questions
            return questions[:3] or ["How does this perspective align with your spiritual values?"]
            
        except Exception as e:
            # Fallback in case of errors
            logger.error(f"Error generating reflection questions: {str(e)}")
            return [
                "How might you apply this wisdom to your current situation?",
                "What spiritual principle resonates most with you from this conversation?"
            ]
    
    def end_conversation(self, remember: bool = True) -> Optional[str]:
        """
        End the current conversation and optionally create a memory.
        
        Args:
            remember: Whether to create a memory from this conversation
            
        Returns:
            Memory ID if created, None otherwise
        """
        if not self.conversation_id:
            return None
            
        memory_id = None
        if self.enable_memory and self.memory_manager:
            memory_id = self.memory_manager.end_conversation(remember)
        
        # Reset current conversation
        self.conversation_id = str(uuid.uuid4())
        self.conversation_messages = []
        self.messages = [SystemMessage(content=LIFE_COACH_SYSTEM_PROMPT)]
        self.context_initialized = False
        
        return memory_id
    
    def add_explicit_memory(self, content: str, memory_type: str = "short") -> Optional[str]:
        """
        Add an explicitly requested memory.
        
        Args:
            content: The content to remember.
            memory_type: The type of memory (short, mid, long).
            
        Returns:
            Memory ID if created, None otherwise.
        """
        if self.enable_memory and self.memory_manager:
            return self.memory_manager.create_memory_now(content, memory_type)
        return None
    
    def get_memories(self) -> Dict[str, Any]:
        """
        Get memories relevant to the current conversation.
        
        Returns:
            Dictionary with memories by type
        """
        if not self.enable_memory or not self.memory_manager or not self.conversation_id:
            return {"short": None, "mid": None, "long": None}
            
        return self.memory_manager.get_memories_for_conversation(self.conversation_id)
    
    def _update_google_data(self) -> None:
        """Update calendar events and tasks from Google APIs."""
        if not self.google_enabled:
            return
        
        try:
            # Get calendar events
            calendar_events = get_upcoming_events(max_results=5)
            logger.info(f"Retrieved {len(calendar_events)} calendar events")
            
            # Get tasks
            tasks = get_tasks(max_results=10)
            logger.info(f"Retrieved {len(tasks)} tasks")
            
            # Update integration data
            self.google_integration_data = {
                'enabled': self.google_enabled,
                'integration_used': True,
                'calendar_events': calendar_events,
                'tasks': tasks
            }
            
        except Exception as e:
            logger.error(f"Error updating Google data: {str(e)}")
            
    def _try_create_task(self, user_message: str) -> bool:
        """
        Try to create a task based on the user message.
        
        Args:
            user_message: The user's message containing a task request.
            
        Returns:
            True if task creation was attempted, False otherwise.
        """
        if not self.google_enabled:
            return False
        
        try:
            # Extract task title using LLM
            task_detection_prompt = f"""
You are helping to extract a task from a user message. The user wants to create a new task or reminder.
From the following message, identify the main task title. Return ONLY the task title, nothing else.

User message: {user_message}

Task title:
"""
            
            try:
                task_title = self.llm.invoke(task_detection_prompt).content.strip()
                
                # Create the task
                if task_title:
                    task = create_task(task_title)
                    if task:
                        # Update tasks in integration data
                        tasks = self.google_integration_data.get('tasks', [])
                        tasks.append(task)
                        self.google_integration_data['tasks'] = tasks
                        
                        logger.info(f"Created task: {task_title}")
                        return True
                        
            except Exception as e:
                logger.error(f"Error extracting task title with LLM: {str(e)}")
                
                # Fallback to simple extraction if LLM fails
                task_indicators = ["add task ", "create task ", "remind me to ", "i need to "]
                task_title = None
                
                for indicator in task_indicators:
                    if indicator in user_message.lower():
                        task_title = user_message.lower().split(indicator, 1)[1].strip()
                        task_title = task_title.capitalize()
                        break
                
                if task_title:
                    # Create the task
                    task = create_task(task_title)
                    if task:
                        # Update tasks in integration data
                        tasks = self.google_integration_data.get('tasks', [])
                        tasks.append(task)
                        self.google_integration_data['tasks'] = tasks
                        
                        logger.info(f"Created task (fallback method): {task_title}")
                        return True
                        
        except Exception as e:
            logger.error(f"Error creating task: {str(e)}")
            
        return False

    def get_response(self, user_input: str) -> str:
        """
        Get a response from the agent for the given user input.
        
        Args:
            user_input: The user's message
            
        Returns:
            str: The agent's response
        """
        try:
            # Use the existing provide_coaching method
            result = self.provide_coaching(user_input)
            
            # Return the response text
            return result.get("response", "I'm sorry, I wasn't able to process your request.")
        except Exception as e:
            logging.error(f"Error getting response: {str(e)}")
            return "I'm sorry, I encountered an error. Please try again."

    def get_welcome_message(self) -> str:
        """
        Get a welcome message to start a new conversation.
        
        Returns:
            str: The welcome message
        """
        try:
            # Use the existing start_new_conversation method
            result = self.start_new_conversation()
            
            # Return the response text
            return result.get("response", "Hello! I'm your Bahá'í Life Coach. How can I assist you today?")
        except Exception as e:
            logging.error(f"Error getting welcome message: {str(e)}")
            return "Hello! I'm your Bahá'í Life Coach. How can I assist you today?"

    def get_insights(self) -> List[str]:
        """
        Get insights from the current conversation.
        
        Returns:
            List[str]: A list of insights
        """
        try:
            # Get the last few exchanges
            last_exchanges = []
            for i in range(min(len(self.conversation_messages), 4)):
                if i >= len(self.conversation_messages):
                    break
                msg = self.conversation_messages[-i-1]
                if msg["role"] == "user":
                    last_exchanges.append(f"User: {msg['content']}")
                else:
                    last_exchanges.append(f"Coach: {msg['content']}")
            
            # If we have enough conversation, generate insights
            if len(last_exchanges) >= 2:
                conversation_text = "\n".join(last_exchanges)
                
                # Create prompt for LLM
                prompt = f"""
Based on this conversation between a user and a Bahá'í life coach, identify 1-3 key insights or themes.
Make these relevant to Bahá'í principles and the user's spiritual growth.

Conversation:
{conversation_text}

Key insights (brief bullet points):
"""
                # Get insights from LLM
                response = self.llm.invoke(prompt).content
                
                # Parse out the insights (bullet points or numbered)
                insights = []
                for line in response.strip().split('\n'):
                    clean_line = line.strip()
                    if clean_line.startswith('-') or clean_line.startswith('*'):
                        clean_line = clean_line[1:].strip()
                    elif clean_line[0].isdigit() and clean_line[1:3] in ['. ', ') ']:
                        clean_line = clean_line[3:].strip()
                        
                    if clean_line and len(clean_line) > 10:
                        insights.append(clean_line)
                
                return insights[:3]
            
            return []
            
        except Exception as e:
            logger.error(f"Error generating insights: {str(e)}")
            return []

    def finalize_conversation(self) -> Dict[str, Any]:
        """
        Finalize the current conversation, saving it as a memory.
        
        Returns:
            Dict with success status and message
        """
        try:
            if not self.conversation_id:
                return {
                    "success": False,
                    "message": "No active conversation to finalize"
                }
            
            # End conversation and create memory
            memory_id = self.end_conversation(remember=True)
            
            if memory_id:
                return {
                    "success": True,
                    "message": "Conversation finalized successfully",
                    "memory_id": memory_id
                }
            else:
                return {
                    "success": True,
                    "message": "Conversation finalized (no memory created)"
                }
                
        except Exception as e:
            logger.error(f"Error finalizing conversation: {str(e)}")
            return {
                "success": False,
                "message": f"Error: {str(e)}"
            } 