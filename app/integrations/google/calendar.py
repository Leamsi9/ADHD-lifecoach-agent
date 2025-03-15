"""
Google Calendar integration for the Bahai Life Coach agent.
"""

import os
import datetime
from typing import Dict, Any, List, Optional
import json
import logging

from langchain_core.tools import BaseTool
from langchain_core.pydantic_v1 import BaseModel, Field
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

from app.config.settings import DEBUG

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar']
TOKEN_FILE = 'token.json'
CREDENTIALS_FILE = 'credentials.json'

def get_google_credentials():
    """Get Google OAuth2 credentials."""
    creds = None
    # The file token.json stores the user's access and refresh tokens
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_info(
            json.loads(open(TOKEN_FILE).read()), SCOPES)
    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_FILE):
                logger.error(f"Credentials file {CREDENTIALS_FILE} not found")
                return None
            
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
    
    return creds

def get_upcoming_events(max_results=10, time_min=None, calendar_id='primary'):
    """
    Get upcoming events from Google Calendar.
    
    Args:
        max_results: Maximum number of events to return.
        time_min: Minimum time for events (defaults to now).
        calendar_id: Calendar ID to get events from.
        
    Returns:
        A list of calendar events.
    """
    try:
        # Get credentials
        creds = get_google_credentials()
        if not creds:
            logger.warning("No valid credentials found for Google Calendar")
            return _get_mock_events(max_results)
        
        # Build the service
        service = build('calendar', 'v3', credentials=creds)
        
        # Set default time_min to now if not provided
        if not time_min:
            time_min = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
        
        # Call the Calendar API
        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=time_min,
            maxResults=max_results,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        # Process the events
        events = events_result.get('items', [])
        
        # Format the events
        formatted_events = []
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))
            
            formatted_events.append({
                'id': event['id'],
                'summary': event['summary'],
                'description': event.get('description', ''),
                'start': start,
                'end': end,
                'location': event.get('location', '')
            })
        
        return formatted_events
    
    except Exception as e:
        logger.error(f"Error getting calendar events: {str(e)}")
        return _get_mock_events(max_results)

def _get_mock_events(max_results=10):
    """
    Get mock calendar events for testing.
    
    Args:
        max_results: Maximum number of events to return.
        
    Returns:
        A list of mock calendar events.
    """
    # Create some mock events
    now = datetime.datetime.now()
    mock_events = [
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
        },
        {
            'id': '3',
            'summary': 'Service Project Planning',
            'description': 'Planning session for community service project',
            'start': (now + datetime.timedelta(days=3)).strftime('%Y-%m-%dT14:00:00'),
            'end': (now + datetime.timedelta(days=3)).strftime('%Y-%m-%dT15:30:00'),
            'location': 'Virtual Meeting'
        }
    ]
    
    # Return only the requested number of events
    return mock_events[:max_results]

class CalendarEventCreate(BaseModel):
    """Input for creating a calendar event."""
    title: str = Field(..., description="Title of the event")
    start_time: str = Field(..., description="Start time in ISO format or natural language (e.g., 'tomorrow at 3pm')")
    end_time: Optional[str] = Field(None, description="End time in ISO format or natural language (e.g., 'tomorrow at 4pm')")
    description: Optional[str] = Field(None, description="Description of the event")
    location: Optional[str] = Field(None, description="Location of the event")
    attendees: Optional[List[str]] = Field(None, description="List of email addresses for attendees")
    reminders: Optional[Dict[str, int]] = Field(None, description="Reminders for the event, e.g., {'useDefault': True} or {'minutes': [10, 30]}")

class GoogleCalendarCreateTool(BaseTool):
    """Tool for creating Google Calendar events."""
    name = "google_calendar_create"
    description = """
    Create an event in Google Calendar.
    This tool is useful when the user wants to schedule a reminder, meeting, or any event in their calendar.
    Input should include title, start_time, and optionally end_time, description, location, and attendees.
    """
    args_schema = CalendarEventCreate
    
    def _run(self, title: str, start_time: str, end_time: Optional[str] = None, 
             description: Optional[str] = None, location: Optional[str] = None,
             attendees: Optional[List[str]] = None, reminders: Optional[Dict[str, int]] = None) -> str:
        """Run the tool."""
        try:
            creds = get_google_credentials()
            service = build('calendar', 'v3', credentials=creds)
            
            # Parse start and end times
            # For simplicity, we'll use the datetime library, but in a full implementation
            # you would want to use something more robust for natural language parsing like dateparser
            # This is a placeholder implementation
            try:
                start_datetime = datetime.datetime.fromisoformat(start_time)
            except ValueError:
                # In a real implementation, use a natural language date parser here
                # For now, just default to now + 1 hour
                start_datetime = datetime.datetime.now() + datetime.timedelta(hours=1)
                start_datetime = start_datetime.replace(minute=0, second=0, microsecond=0)
            
            if end_time:
                try:
                    end_datetime = datetime.datetime.fromisoformat(end_time)
                except ValueError:
                    # Default to start time + 1 hour
                    end_datetime = start_datetime + datetime.timedelta(hours=1)
            else:
                # Default to start time + 1 hour
                end_datetime = start_datetime + datetime.timedelta(hours=1)
            
            # Create the event
            event = {
                'summary': title,
                'start': {
                    'dateTime': start_datetime.isoformat(),
                    'timeZone': 'America/Los_Angeles',  # Should be user's timezone
                },
                'end': {
                    'dateTime': end_datetime.isoformat(),
                    'timeZone': 'America/Los_Angeles',  # Should be user's timezone
                }
            }
            
            if description:
                event['description'] = description
            
            if location:
                event['location'] = location
            
            if attendees:
                event['attendees'] = [{'email': email} for email in attendees]
            
            if reminders:
                event['reminders'] = reminders
            else:
                event['reminders'] = {'useDefault': True}
            
            # Call the Calendar API
            event = service.events().insert(calendarId='primary', body=event).execute()
            
            return f"Event created successfully. Event ID: {event.get('id')}"
        
        except Exception as e:
            if DEBUG:
                return f"Error creating calendar event: {str(e)}"
            return "Error creating calendar event. Please check your Google Calendar access."

class CalendarEventQuery(BaseModel):
    """Input for querying calendar events."""
    time_min: Optional[str] = Field(None, description="Start time in ISO format or natural language (e.g., 'today')")
    time_max: Optional[str] = Field(None, description="End time in ISO format or natural language (e.g., 'tomorrow')")
    max_results: Optional[int] = Field(10, description="Maximum number of results to return")
    query: Optional[str] = Field(None, description="Search term to filter events")

class GoogleCalendarViewTool(BaseTool):
    """Tool for viewing Google Calendar events."""
    name = "google_calendar_view"
    description = """
    View events from Google Calendar.
    This tool is useful when the user wants to check their schedule or look for specific events.
    Input should include optional time_min, time_max, max_results, and query parameters.
    """
    args_schema = CalendarEventQuery
    
    def _run(self, time_min: Optional[str] = None, time_max: Optional[str] = None, 
             max_results: Optional[int] = 10, query: Optional[str] = None) -> str:
        """Run the tool."""
        try:
            creds = get_google_credentials()
            service = build('calendar', 'v3', credentials=creds)
            
            # Parse time boundaries
            # For simplicity in this example
            if not time_min:
                time_min = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
            
            if not time_max:
                # Default to time_min + 1 week
                time_max = (datetime.datetime.utcnow() + datetime.timedelta(days=7)).isoformat() + 'Z'
            
            # Get events from the Google Calendar API
            events_result = service.events().list(
                calendarId='primary', 
                timeMin=time_min,
                timeMax=time_max, 
                maxResults=max_results, 
                singleEvents=True,
                orderBy='startTime',
                q=query
            ).execute()
            
            events = events_result.get('items', [])
            
            if not events:
                return "No upcoming events found."
            
            # Format the events for display
            event_list = []
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                # Convert to a more readable format
                if 'T' in start:  # This is a datetime
                    start_dt = datetime.datetime.fromisoformat(start.replace('Z', '+00:00'))
                    start_str = start_dt.strftime('%Y-%m-%d %H:%M')
                else:  # This is a date
                    start_str = start
                
                event_list.append(f"{start_str}: {event['summary']}")
            
            return "\n".join(event_list)
        
        except Exception as e:
            if DEBUG:
                return f"Error viewing calendar events: {str(e)}"
            return "Error viewing calendar events. Please check your Google Calendar access." 