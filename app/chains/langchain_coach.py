"""
LangChain-based coaching chain for the Bahai Life Coach agent.
"""

from typing import Dict, Any, Optional, List
import uuid
import random
import logging
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from app.config.settings import (
    LLM_PROVIDER, TEMPERATURE, MODEL_NAME, 
    USE_OPENAI, USE_OLLAMA, USE_HUGGINGFACE,
    ENABLE_GOOGLE_INTEGRATION
)
from app.prompts.life_coach_prompts import (
    LIFE_COACH_SYSTEM_PROMPT, INITIAL_GREETING_TEMPLATE, FOLLOW_UP_TEMPLATE,
    GROUND_CONNECT_TEMPLATE, EXPLORE_TEMPLATE, SUMMARIZE_TEMPLATE, BAHAI_QUOTES,
    COACHING_TEMPLATE
)
from app.models.llm import get_llm_model

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import Google integration modules if enabled
GOOGLE_IMPORTS_SUCCESSFUL = False
if ENABLE_GOOGLE_INTEGRATION:
    try:
        # Mock implementations for when Google API client is not installed
        def get_mock_events(max_results=5):
            """Get mock calendar events."""
            import datetime
            now = datetime.datetime.now()
            return [
                {
                    'id': '1',
                    'summary': 'Meditation Session',
                    'description': 'Daily meditation practice',
                    'start': (now + datetime.timedelta(days=1)).strftime('%Y-%m-%dT09:00:00'),
                    'end': (now + datetime.timedelta(days=1)).strftime('%Y-%m-%dT09:30:00'),
                    'location': 'Home'
                },
                {
                    'id': '2',
                    'summary': 'Bahá\'í Study Circle',
                    'description': 'Weekly study of Bahá\'í writings',
                    'start': (now + datetime.timedelta(days=2)).strftime('%Y-%m-%dT18:00:00'),
                    'end': (now + datetime.timedelta(days=2)).strftime('%Y-%m-%dT19:30:00'),
                    'location': 'Community Center'
                }
            ][:max_results]
        
        def get_mock_tasks(max_results=10):
            """Get mock tasks."""
            import datetime
            now = datetime.datetime.now()
            return [
                {
                    'id': '1',
                    'title': 'Read Bahá\'í writings',
                    'notes': 'Focus on the Hidden Words',
                    'due': (now + datetime.timedelta(days=1)).strftime('%Y-%m-%dT00:00:00.000Z'),
                    'status': 'needsAction'
                },
                {
                    'id': '2',
                    'title': 'Prepare for devotional gathering',
                    'notes': 'Select prayers and readings',
                    'due': (now + datetime.timedelta(days=3)).strftime('%Y-%m-%dT00:00:00.000Z'),
                    'status': 'needsAction'
                }
            ][:max_results]
        
        def create_mock_task(title, notes=None, due_date=None):
            """Create a mock task."""
            import datetime
            now = datetime.datetime.now()
            return {
                'id': f"mock_{now.timestamp()}",
                'title': title,
                'notes': notes or '',
                'due': due_date or (now + datetime.timedelta(days=1)).strftime('%Y-%m-%dT00:00:00.000Z'),
                'status': 'needsAction'
            }
        
        # Try to import the real implementations
        try:
            from app.integrations.google.calendar import get_upcoming_events
            from app.integrations.google.tasks import get_tasks, create_task
            GOOGLE_IMPORTS_SUCCESSFUL = True
            logger.info("✅ Google integration modules imported successfully")
        except ImportError:
            # Use mock implementations if imports fail
            logger.warning("⚠️ Google API client not installed. Using mock implementations.")
            logger.info("To enable real Google integration, install the Google client libraries with:")
            logger.info("    pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
            get_upcoming_events = get_mock_events
            get_tasks = get_mock_tasks
            create_task = create_mock_task
            GOOGLE_IMPORTS_SUCCESSFUL = True  # We're using mock implementations
    except Exception as e:
        logger.warning(f"❌ Error setting up Google integration: {str(e)}")


class SessionState:
    """
    Class to manage session-specific data and state.
    """
    
    def __init__(self):
        """Initialize the session state with default values."""
        self.current_stage = "initial"
        self.conversation_turns = 0
        self.calendar_events = []
        self.tasks = []
        self.quoted_principles = set()
        self.session_insights = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the session state to a dictionary."""
        return {
            "current_stage": self.current_stage,
            "conversation_turns": self.conversation_turns,
            "calendar_events": self.calendar_events,
            "tasks": self.tasks,
            "quoted_principles": list(self.quoted_principles),
            "session_insights": self.session_insights
        }
    
    def update_stage(self, turns: int) -> None:
        """
        Update the current stage based on the number of conversation turns.
        
        Args:
            turns: The total number of conversation turns.
        """
        if turns == 0:
            self.current_stage = "initial"
        elif turns % 5 == 1:
            self.current_stage = "ground_connect"
        elif turns % 5 == 3:
            self.current_stage = "explore"
        elif turns % 5 == 0:
            self.current_stage = "summarize"
        else:
            self.current_stage = "follow_up"


class LangChainCoach:
    """
    LangChain-based coaching chain for life coaching conversations based on Bahá'í principles.
    """
    
    def __init__(self, conversation_id: Optional[str] = None):
        """
        Initialize the LangChain coaching chain.
        
        Args:
            conversation_id: Optional ID for continuing an existing conversation.
        """
        self.conversation_id = conversation_id or str(uuid.uuid4())
        self.messages = []
        self.session_state = SessionState()
        self.llm = get_llm_model()
        
        # Set up the system message
        self.system_message = SystemMessage(content=LIFE_COACH_SYSTEM_PROMPT)
        
        # Initialize Google integrations if enabled
        self.google_enabled = ENABLE_GOOGLE_INTEGRATION and GOOGLE_IMPORTS_SUCCESSFUL
        if self.google_enabled:
            try:
                # Try to get some initial data
                self._update_google_data()
                logger.info("Google integration initialized successfully")
            except Exception as e:
                logger.warning(f"Google integration initialization error: {str(e)}")
                self.google_enabled = False
        
        # Store integration data that can be accessed by the agent
        self.google_integration_data = {
            'enabled': self.google_enabled,
            'integration_used': False,
            'calendar_events': [],
            'tasks': []
        }
    
    def process(self, user_message: str) -> Dict[str, Any]:
        """
        Process a user message and generate a coaching response.
        
        Args:
            user_message: The user's message.
            
        Returns:
            Dictionary with the coach's response and session information.
        """
        # Check for integration requests
        integration_used = False
        if self.google_enabled:
            # Check for calendar-related keywords
            if any(keyword in user_message.lower() for keyword in ["calendar", "schedule", "appointment", "meeting", "event"]):
                self._update_google_data()
                integration_used = True
            
            # Check for task-related keywords
            if any(keyword in user_message.lower() for keyword in ["task", "todo", "to-do", "to do", "reminder"]):
                # Check if this is a task creation request
                if any(verb in user_message.lower() for verb in ["add", "create", "make", "set"]):
                    self._try_create_task(user_message)
                    integration_used = True
                else:
                    self._update_google_data()
                    integration_used = True
        
        # Increment turn counter and update stage
        self.session_state.conversation_turns += 1
        self.session_state.update_stage(self.session_state.conversation_turns)
        
        # Add user message to history
        user_msg = HumanMessage(content=user_message)
        self.messages.append(user_msg)
        
        # Get the appropriate stage-specific prompt
        stage_prompt = self._get_stage_specific_prompt()
        
        # Create the full prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", LIFE_COACH_SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="history"),
            ("system", stage_prompt),
            ("human", "{input}")
        ])
        
        # Create the chain
        chain = prompt | self.llm
        
        # Generate the response
        try:
            # Pass in the messages history except the most recent message (which is included in the prompt)
            chain_response = chain.invoke({
                "history": self.messages[:-1] if len(self.messages) > 1 else [],
                "input": user_message
            })
            
            # LangChain returns different types based on the provider
            if hasattr(chain_response, 'content'):
                coach_response = chain_response.content
            else:
                coach_response = str(chain_response)
            
            # Add assistant message to history
            ai_msg = AIMessage(content=coach_response)
            self.messages.append(ai_msg)
            
            # Update Google integration data for the response
            self.google_integration_data = {
                'enabled': self.google_enabled,
                'integration_used': integration_used,
                'calendar_events': self.session_state.calendar_events,
                'tasks': self.session_state.tasks
            }
            
            return {
                'response': coach_response,
                'conversation_id': self.conversation_id,
                'integration_used': integration_used,
                'session_state': self.session_state.to_dict()
            }
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return {
                'response': f"I'm sorry, I encountered an error: {str(e)}. Please try again or contact support.",
                'conversation_id': self.conversation_id,
                'error': str(e)
            }
    
    def get_session_state(self) -> Dict[str, Any]:
        """
        Get the current session state as a dictionary.
        
        Returns:
            The session state dictionary.
        """
        return self.session_state.to_dict()
    
    def _get_stage_specific_prompt(self) -> str:
        """
        Get the appropriate prompt based on the current conversation stage.
        
        Returns:
            The stage-specific prompt.
        """
        stage = self.session_state.current_stage
        
        if stage == "initial":
            return INITIAL_GREETING_TEMPLATE
        
        elif stage == "ground_connect":
            # Select a Baháʼí quote for grounding
            available_quotes = [q for q in BAHAI_QUOTES if q["theme"] not in self.session_state.quoted_principles]
            
            # If we've used all quotes, reset the tracking
            if not available_quotes:
                self.session_state.quoted_principles.clear()
                available_quotes = BAHAI_QUOTES
            
            quote_data = random.choice(available_quotes)
            self.session_state.quoted_principles.add(quote_data["theme"])
            
            # Format the template with the selected quote
            return GROUND_CONNECT_TEMPLATE.format(
                bahai_quote=quote_data["quote"],
                quote_source=quote_data["source"]
            )
        
        elif stage == "explore":
            return EXPLORE_TEMPLATE
        
        elif stage == "summarize":
            return SUMMARIZE_TEMPLATE
        
        else:  # follow_up
            return FOLLOW_UP_TEMPLATE
    
    def _update_google_data(self) -> None:
        """Update calendar events and tasks from Google APIs."""
        if not self.google_enabled:
            return
        
        try:
            # Get calendar events
            self.session_state.calendar_events = get_upcoming_events(max_results=5)
            logger.info(f"Retrieved {len(self.session_state.calendar_events)} calendar events")
            
            # Get tasks
            self.session_state.tasks = get_tasks(max_results=10)
            logger.info(f"Retrieved {len(self.session_state.tasks)} tasks")
        
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
            # Simple extraction of task title (in a real app, use NLP for better extraction)
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
                    # Add to our local list
                    self.session_state.tasks.append(task)
                    logger.info(f"Created task: {task_title}")
                    return True
        
        except Exception as e:
            logger.error(f"Error creating task: {str(e)}")
        
        return False 