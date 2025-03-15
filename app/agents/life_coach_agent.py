"""
Life Coach Agent Module for the Bahai Life Coach.
"""

from typing import Dict, List, Any, Optional

# Import the new LangChain-based coaching chain
from app.chains.langchain_coach import LangChainCoach
from app.config.settings import ENABLE_GOOGLE_INTEGRATION
from app.utils.memory import MemoryManager
from app.models.llm import get_llm_model


class LifeCoachAgent:
    """
    A life coach agent that provides coaching based on Bahai principles.
    """
    
    def __init__(self, conversation_id: Optional[str] = None):
        """
        Initialize the life coach agent.
        
        Args:
            conversation_id: An optional conversation ID to continue an existing conversation.
        """
        self.conversation_id = conversation_id or None
        # Use the new LangChain-based coaching chain
        self.coaching_chain = LangChainCoach(conversation_id=conversation_id)
        
        # Initialize memory manager with conversation_id
        self.memory_manager = MemoryManager(conversation_id=self.coaching_chain.conversation_id)
        
        # Store Google integration data that can be accessed from outside
        self.google_integration_data = self.coaching_chain.google_integration_data if hasattr(self.coaching_chain, 'google_integration_data') else {}
        
        # Initialize LLM for dynamic content generation
        self.llm = get_llm_model()
        
    def provide_coaching(self, user_input: str) -> Dict[str, Any]:
        """
        Process user input and provide coaching response.
        
        Args:
            user_input: The user's input message.
            
        Returns:
            A dictionary containing the coaching response, conversation ID, and any insights.
        """
        # Check for explicit memory requests
        if "remember" in user_input.lower() or "store this" in user_input.lower():
            # We'll process actual extraction in the memory manager later
            pass
            
        # Process the input through the coaching chain
        chain_response = self.coaching_chain.process(user_input)
        
        # Extract key insights from the response
        insights = self._extract_insights(user_input, chain_response['response'])
        
        # Update Google integration data
        if hasattr(self.coaching_chain, 'google_integration_data'):
            self.google_integration_data = self.coaching_chain.google_integration_data
        
        # Extract and store facts after the conversation
        self._process_memory_after_conversation()
        
        # Format the response
        formatted_response = self._format_response(chain_response['response'])
        
        # Return the response with all necessary information
        result = {
            'response': formatted_response,
            'conversation_id': self.coaching_chain.conversation_id,
            'insights': insights
        }
        
        # Add any session state from the chain
        if 'session_state' in chain_response:
            result['session_state'] = chain_response['session_state']
        
        # Add integration info
        if 'integration_used' in chain_response:
            result['integration_used'] = chain_response['integration_used']
        
        return result
    
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
            context = "You are a compassionate Bahá'í life coach starting a new coaching session."
            
            if memory_summary:
                context += f"\n\nHere's a summary of previous sessions with this user:\n{memory_summary}"
            
            greeting_prompt = f"""
{context}

Generate a warm, natural greeting to start a new conversation with the user. 
Your greeting should be welcoming and establish a connection while avoiding rigid templated language.
Be spontaneous and genuine, maintaining the coaching relationship.
If there are previous session insights, reference them naturally without a formulaic approach.
Keep your response concise (2-3 sentences) and conversational in tone.
"""
            
            greeting = self.llm.invoke(greeting_prompt).content.strip()
            
        except Exception as e:
            # Fallback greeting if LLM fails
            greeting = "Welcome back to your Bahá'í life coach session."
            if memory_summary:
                greeting += "\n\n" + memory_summary
        
        return {
            'response': greeting,
            'conversation_id': self.coaching_chain.conversation_id
        }
    
    def _extract_insights(self, user_input: str, coach_response: str) -> List[str]:
        """
        Extract key insights from the conversation.
        
        Args:
            user_input: The user's input message.
            coach_response: The coach's response.
            
        Returns:
            A list of key insights.
        """
        # Use reflection questions as insights
        return self._generate_reflection_questions(user_input, coach_response)
    
    def _format_response(self, response: str) -> str:
        """
        Format the response from the coaching chain.
        
        Args:
            response: The raw response from the coaching chain.
            
        Returns:
            A formatted response.
        """
        # For now, we'll just return the response as is
        return response
    
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
            return [
                "How might you apply this wisdom to your current situation?",
                "What spiritual principle resonates most with you from this conversation?"
            ]
    
    def _process_memory_after_conversation(self) -> None:
        """
        Process and store memories after the conversation.
        """
        # Extract conversation history from the coaching chain
        # Convert LangChain messages to the format expected by memory manager
        conversation_history = []
        
        # If using a LangChain coach, the messages might be in a different format
        if hasattr(self.coaching_chain, 'messages'):
            # Convert LangChain message objects to dictionaries
            for msg in self.coaching_chain.messages:
                conversation_history.append({
                    'role': msg.type if hasattr(msg, 'type') else 'unknown',
                    'content': msg.content
                })
        elif hasattr(self.coaching_chain, 'conversation_history'):
            # For backward compatibility with the original coaching chain
            conversation_history = self.coaching_chain.conversation_history
        
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