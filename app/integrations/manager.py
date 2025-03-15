"""
Integration manager for the Bahai Life Coach agent.

This module handles detection, parsing, and execution of integration-related actions.
"""

import re
import os
import datetime
from typing import Dict, Any, List, Optional, Tuple, Union

from langchain_core.tools import BaseTool

try:
    # Import the Google integration tools
    from app.integrations.google.calendar import (
        GoogleCalendarCreateTool,
        GoogleCalendarViewTool
    )
    from app.integrations.google.tasks import (
        GoogleTaskCreateTool,
        GoogleTaskViewTool,
        GoogleTaskCompleteTool
    )
    from app.integrations.google.date_parser import (
        parse_natural_language_date,
        parse_date_time_range
    )
    GOOGLE_INTEGRATIONS_AVAILABLE = True
except ImportError:
    GOOGLE_INTEGRATIONS_AVAILABLE = False

from app.config.settings import DEBUG

class IntegrationManager:
    """Manager for handling integrations with external services."""
    
    def __init__(self):
        """Initialize the integration manager."""
        self.tools = {}
        
        # Load available integrations
        if GOOGLE_INTEGRATIONS_AVAILABLE and os.path.exists('credentials.json'):
            self._load_google_integrations()
    
    def _load_google_integrations(self):
        """Load Google services integrations."""
        try:
            # Calendar tools
            self.tools['google_calendar_create'] = GoogleCalendarCreateTool()
            self.tools['google_calendar_view'] = GoogleCalendarViewTool()
            
            # Tasks tools
            self.tools['google_task_create'] = GoogleTaskCreateTool()
            self.tools['google_task_view'] = GoogleTaskViewTool()
            self.tools['google_task_complete'] = GoogleTaskCompleteTool()
            
            if DEBUG:
                print("Google integrations loaded successfully")
        except Exception as e:
            if DEBUG:
                print(f"Error loading Google integrations: {str(e)}")
    
    def get_available_tools(self) -> List[BaseTool]:
        """Get list of available integration tools."""
        return list(self.tools.values())
    
    def has_integration(self, integration_name: str) -> bool:
        """Check if a specific integration is available."""
        return integration_name in self.tools
    
    def detect_integration_action(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Detect if the text contains a request for an integration action.
        
        Args:
            text: The user's message
            
        Returns:
            Dictionary with integration details if detected, None otherwise
        """
        # Check for calendar-related actions
        calendar_patterns = [
            r"(schedule|create|add|set up|organize|book|plan)\s+(a|an|the)?\s*(meeting|event|appointment|reminder)",
            r"remind me (to|about|of)",
            r"(add|put) (this|that|it) (on|in) my calendar",
            r"add (an|a) event",
            r"schedule (for|on|at)"
        ]
        
        for pattern in calendar_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                # Extract potential event details
                title = self._extract_event_title(text)
                time_info = self._extract_time_info(text)
                
                return {
                    'action': 'create_calendar_event',
                    'tool': 'google_calendar_create',
                    'params': {
                        'title': title or "New Event",
                        'start_time': time_info.get('start_time'),
                        'end_time': time_info.get('end_time'),
                        'description': time_info.get('description')
                    }
                }
        
        # Check for calendar view actions
        calendar_view_patterns = [
            r"(show|check|view|get|what( is|'s))\s+my\s+(calendar|schedule|agenda)",
            r"(what do I have|what's|what is)(\s+planned|\s+scheduled)?\s+(today|tomorrow|this week|next week|on)",
            r"(do I have|are there) any (events|meetings|appointments)"
        ]
        
        for pattern in calendar_view_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                # Extract potential time range
                time_info = self._extract_time_info(text)
                
                return {
                    'action': 'view_calendar_events',
                    'tool': 'google_calendar_view',
                    'params': {
                        'time_min': time_info.get('start_time'),
                        'time_max': time_info.get('end_time'),
                        'query': time_info.get('query')
                    }
                }
        
        # Check for task-related actions
        task_patterns = [
            r"(add|create|make)\s+(a|an|the)?\s*(task|to-?do|item|reminder)",
            r"(remind me to|add to my to-?do list)",
            r"I need to (remember to|do)"
        ]
        
        for pattern in task_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                # Extract potential task details
                title = self._extract_task_title(text)
                due_date = self._extract_due_date(text)
                
                return {
                    'action': 'create_task',
                    'tool': 'google_task_create',
                    'params': {
                        'title': title or "New Task",
                        'notes': None,
                        'due_date': due_date
                    }
                }
        
        # Check for task view actions
        task_view_patterns = [
            r"(show|check|view|get|what( is|'s))\s+my\s+(tasks|to-?do list)",
            r"what do I need to do",
            r"(show|list) (all|my)?\s*(tasks|to-?dos)"
        ]
        
        for pattern in task_view_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return {
                    'action': 'view_tasks',
                    'tool': 'google_task_view',
                    'params': {
                        'show_completed': 'completed' in text.lower()
                    }
                }
        
        # Check for task completion actions
        task_complete_patterns = [
            r"(mark|set)\s+(as)?\s*completed",
            r"(I('ve| have)|i) (finished|completed|done)",
            r"(mark|check) off"
        ]
        
        for pattern in task_complete_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                # This is tricky since we need the task ID, which we don't know from text alone
                # We'll need the LLM to prompt for more information or clarify
                return {
                    'action': 'complete_task',
                    'tool': 'google_task_complete',
                    'params': {
                        'task_id': None  # We don't have this from the text alone
                    },
                    'needs_more_info': True
                }
        
        # No integration action detected
        return None
    
    def execute_integration_action(self, action_details: Dict[str, Any]) -> str:
        """
        Execute an integration action.
        
        Args:
            action_details: Dictionary with action details
            
        Returns:
            Result of the action as a string
        """
        tool_name = action_details.get('tool')
        if not tool_name or tool_name not in self.tools:
            return "This integration is not available."
        
        try:
            tool = self.tools[tool_name]
            params = action_details.get('params', {})
            
            # Clean up params
            clean_params = {}
            for k, v in params.items():
                if v is not None:
                    clean_params[k] = v
            
            # Check if we have sufficient information
            if action_details.get('needs_more_info'):
                return "I need more information to complete this action. Please provide more details."
            
            # Execute the tool
            return tool._run(**clean_params)
        except Exception as e:
            if DEBUG:
                return f"Error executing integration action: {str(e)}"
            return "Error executing the requested action. Please try again."
    
    def _extract_event_title(self, text: str) -> Optional[str]:
        """Extract potential event title from text."""
        # Look for patterns like "schedule a meeting about X" or "add an event called X"
        title_patterns = [
            r"(?:schedule|create|add|set up|organize|book|plan)\s+(?:a|an|the)?\s*(?:meeting|event|appointment|reminder)\s+(?:about|for|on|to|with|called|titled)\s+(.*?)(?:on|at|from|tomorrow|today|next|this|\.|$)",
            r"(?:schedule|create|add|set up|organize|book|plan)\s+(?:a|an|the)?\s*(.*?)(?:on|at|from|tomorrow|today|next|this|\.|$)",
            r"(?:remind me to|add to calendar)\s+(.*?)(?:on|at|tomorrow|today|next|this|\.|$)"
        ]
        
        for pattern in title_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _extract_task_title(self, text: str) -> Optional[str]:
        """Extract potential task title from text."""
        # Look for patterns like "add a task to X" or "remind me to X"
        title_patterns = [
            r"(?:add|create|make)\s+(?:a|an|the)?\s*(?:task|to-?do|item|reminder)\s+(?:to|for|about)?\s+(.*?)(?:by|on|at|tomorrow|today|next|this|\.|$)",
            r"remind me to\s+(.*?)(?:by|on|at|tomorrow|today|next|this|\.|$)",
            r"I need to (?:remember to|do)\s+(.*?)(?:by|on|at|tomorrow|today|next|this|\.|$)"
        ]
        
        for pattern in title_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _extract_time_info(self, text: str) -> Dict[str, Any]:
        """Extract time-related information from text."""
        if not GOOGLE_INTEGRATIONS_AVAILABLE:
            return {}
        
        result = {}
        
        # Try to find a time range
        start_time, end_time = parse_date_time_range(text)
        
        if start_time:
            result['start_time'] = start_time.isoformat()
        
        if end_time:
            result['end_time'] = end_time.isoformat()
        
        # Try to extract a description
        description_match = re.search(r"(?:details|description|about|note)[s:]\s+(.*)", text, re.IGNORECASE)
        if description_match:
            result['description'] = description_match.group(1).strip()
        
        # Try to extract a query term for event/task searches
        query_patterns = [
            r"(?:related to|about|containing|with)\s+(.*?)(?:on|at|from|tomorrow|today|next|this|\.|$)",
            r"(?:called|titled|named)\s+(.*?)(?:on|at|from|tomorrow|today|next|this|\.|$)"
        ]
        
        for pattern in query_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result['query'] = match.group(1).strip()
                break
        
        return result
    
    def _extract_due_date(self, text: str) -> Optional[str]:
        """Extract potential due date from text."""
        if not GOOGLE_INTEGRATIONS_AVAILABLE:
            return None
        
        # Look for patterns like "due on X" or "by X"
        due_patterns = [
            r"(?:due|by)\s+(.*?)(?:\.|\?|$)",
            r"(?:complete|finish)\s+by\s+(.*?)(?:\.|\?|$)"
        ]
        
        for pattern in due_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                date_text = match.group(1).strip()
                parsed_date = parse_natural_language_date(date_text)
                if parsed_date:
                    return parsed_date.isoformat()
        
        # If no explicit due date but there's a time reference, check for it
        time_references = [
            "tomorrow", "next week", "tonight", "this evening", 
            "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"
        ]
        
        for ref in time_references:
            if ref in text.lower():
                parsed_date = parse_natural_language_date(ref)
                if parsed_date:
                    return parsed_date.isoformat()
        
        return None


# Create a singleton instance
integration_manager = IntegrationManager() 