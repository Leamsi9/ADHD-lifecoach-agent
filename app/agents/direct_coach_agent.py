"""
Direct Life Coach Agent Module for the Bahai Life Coach.
This version bypasses the structured coaching chain and relies directly on the LLM with the system prompt.
"""

from typing import Dict, List, Any, Optional
import uuid
import logging

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from app.config.settings import ENABLE_GOOGLE_INTEGRATION
from app.utils.memory import MemoryManager
from app.models.llm import get_llm_model
from app.prompts.life_coach_prompts import LIFE_COACH_SYSTEM_PROMPT, BAHAI_QUOTES

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


class DirectCoachAgent:
    """
    A simplified life coach agent that provides coaching based on Bahai principles,
    directly using the LLM without the structured coaching chain.
    """
    
    def __init__(self, conversation_id: Optional[str] = None):
        """
        Initialize the direct life coach agent.
        
        Args:
            conversation_id: An optional conversation ID to continue an existing conversation.
        """
        self.conversation_id = conversation_id or str(uuid.uuid4())
        
        # Initialize memory manager
        self.memory_manager = MemoryManager(conversation_id=self.conversation_id)
        
        # Initialize LLM
        self.llm = get_llm_model()
        
        # Initialize message history
        self.messages = [
            SystemMessage(content=LIFE_COACH_SYSTEM_PROMPT)
        ]
        
        # Initialize Google integration status
        self.google_enabled = ENABLE_GOOGLE_INTEGRATION and GOOGLE_IMPORTS_SUCCESSFUL
        self.google_integration_data = {
            'enabled': self.google_enabled,
            'integration_used': False,
            'calendar_events': [],
            'tasks': []
        }
    
    def provide_coaching(self, user_input: str) -> Dict[str, Any]:
        """
        Process user input and provide coaching response directly using the LLM.
        
        Args:
            user_input: The user's input message.
            
        Returns:
            A dictionary containing the coaching response, conversation ID, and any insights.
        """
        # Check for explicit memory requests
        is_memory_request = False
        if "remember" in user_input.lower() or "store this" in user_input.lower():
            is_memory_request = True
            
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
                
        # Get relevant memories to provide context
        memories = self.memory_manager.get_relevant_memories(user_input)
        if memories:
            context += "\n\nRelevant information from previous conversations:\n"
            for memory in memories[:3]:  # Limit to 3 memories
                context += f"- {memory.get('content', '')}\n"
        
        # If we have context, add it as a system message
        if context:
            self.messages.append(SystemMessage(content=f"Context for your response:{context}"))
            
        # Add user message to history
        user_msg = HumanMessage(content=user_input)
        self.messages.append(user_msg)
        
        # Generate the response directly using the LLM
        try:
            response = self.llm.invoke(self.messages)
            coach_response = response.content
            
            # Add assistant message to history
            ai_msg = AIMessage(content=coach_response)
            self.messages.append(ai_msg)
            
            # Extract and store facts after the conversation
            self._process_memory_after_conversation()
            
            # If this was a memory request, explicitly store it
            if is_memory_request:
                self.memory_manager.add_explicit_memory(user_input)
            
            # Extract insights for reflection
            insights = self._generate_reflection_questions(user_input, coach_response)
            
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
        # Get relevant memories from previous sessions
        memory_summary = self.memory_manager.get_summary_for_new_conversation()
        
        # Generate a context-aware greeting using the LLM
        try:
            prompt = "You are a compassionate Bahá'í life coach starting a new coaching session."
            
            if memory_summary:
                prompt += f"\n\nHere's a summary of previous sessions with this user:\n{memory_summary}"
            
            prompt += "\n\nGenerate a warm, natural greeting to start a new conversation with the user."
            
            # Reset message history for new conversation
            self.messages = [
                SystemMessage(content=LIFE_COACH_SYSTEM_PROMPT),
                SystemMessage(content=prompt)
            ]
            
            response = self.llm.invoke(self.messages)
            greeting = response.content.strip()
            
            # Add assistant message to history
            ai_msg = AIMessage(content=greeting)
            self.messages.append(ai_msg)
            
        except Exception as e:
            # Fallback greeting if LLM fails
            logger.error(f"Error generating greeting: {str(e)}")
            greeting = "Welcome to your Bahá'í life coach session. How can I support you today?"
            if memory_summary:
                greeting += "\n\n" + memory_summary
            
            # Add fallback greeting to history
            self.messages.append(AIMessage(content=greeting))
        
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
    
    def _process_memory_after_conversation(self) -> None:
        """
        Process and store memories after the conversation.
        """
        # Convert LangChain messages to the format expected by memory manager
        conversation_history = []
        
        # Convert message objects to dictionaries
        for msg in self.messages:
            if hasattr(msg, 'type') and msg.type != 'system':  # Skip system messages
                conversation_history.append({
                    'role': msg.type,
                    'content': msg.content
                })
        
        # Extract facts from the conversation history
        facts = self.memory_manager.extract_facts(conversation_history)
        
        # Store new facts
        if facts:
            self.memory_manager.store_facts(facts)
    
    def get_memories(self, query: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get memories relevant to a query.
        
        Args:
            query: Optional query to filter memories.
            
        Returns:
            List of relevant memories.
        """
        return self.memory_manager.get_relevant_memories(query)
    
    def add_explicit_memory(self, content: str) -> None:
        """
        Add an explicitly requested memory.
        
        Args:
            content: The content to remember.
        """
        self.memory_manager.add_explicit_memory(content)
        
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