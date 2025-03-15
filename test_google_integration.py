#!/usr/bin/env python3
"""
Test script for Google Calendar and Tasks integrations.
"""

import sys
import os
import datetime

# Add the project root to the path so we can import app modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.integrations.google.calendar import GoogleCalendarCreateTool, GoogleCalendarViewTool
from app.integrations.google.tasks import GoogleTaskCreateTool, GoogleTaskViewTool
from app.integrations.google.date_parser import parse_natural_language_date

def test_google_calendar():
    """Test Google Calendar integration."""
    print("\n=== Testing Google Calendar Integration ===\n")
    
    # Create calendar event tool
    calendar_create = GoogleCalendarCreateTool()
    
    # Test creating an event
    title = "Test Event from Bahai Life Coach"
    start_time = datetime.datetime.now() + datetime.timedelta(hours=1)
    start_time = start_time.replace(minute=0, second=0, microsecond=0).isoformat()
    end_time = datetime.datetime.now() + datetime.timedelta(hours=2)
    end_time = end_time.replace(minute=0, second=0, microsecond=0).isoformat()
    
    print(f"Creating calendar event: {title}")
    result = calendar_create._run(
        title=title,
        start_time=start_time, 
        end_time=end_time,
        description="This is a test event created by the Bahai Life Coach agent."
    )
    print(f"Result: {result}\n")
    
    # View calendar events
    calendar_view = GoogleCalendarViewTool()
    
    print("Viewing calendar events for today:")
    today = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    tomorrow = (datetime.datetime.now() + datetime.timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    result = calendar_view._run(time_min=today, time_max=tomorrow)
    print(f"Today's events:\n{result}\n")

def test_google_tasks():
    """Test Google Tasks integration."""
    print("\n=== Testing Google Tasks Integration ===\n")
    
    # Create task tool
    task_create = GoogleTaskCreateTool()
    
    # Test creating a task
    title = "Test Task from Bahai Life Coach"
    due_date = (datetime.datetime.now() + datetime.timedelta(days=1)).replace(hour=12, minute=0, second=0, microsecond=0).isoformat()
    
    print(f"Creating task: {title}")
    result = task_create._run(
        title=title,
        notes="This is a test task created by the Bahai Life Coach agent.",
        due_date=due_date
    )
    print(f"Result: {result}\n")
    
    # View tasks
    task_view = GoogleTaskViewTool()
    
    print("Viewing tasks:")
    result = task_view._run(show_completed=False)
    print(f"Active tasks:\n{result}\n")

def test_date_parser():
    """Test natural language date parsing."""
    print("\n=== Testing Natural Language Date Parser ===\n")
    
    test_phrases = [
        "tomorrow at 3pm",
        "next Monday at 10am",
        "today at 5:30pm",
        "in 2 hours",
        "this weekend",
        "next Friday",
        "half past 4",
        "quarter to 3",
    ]
    
    for phrase in test_phrases:
        result = parse_natural_language_date(phrase)
        print(f"Phrase: '{phrase}'")
        print(f"Parsed date: {result.isoformat() if result else 'Failed to parse'}\n")

def main():
    """Main function."""
    print("Testing Google Integrations for Bahai Life Coach agent")
    print("====================================================")
    
    if not os.path.exists('credentials.json'):
        print("Error: credentials.json file not found.")
        print("Please download your OAuth 2.0 Client ID credentials file from the Google Cloud Console")
        print("and save it as 'credentials.json' in the project root directory.")
        return
    
    # Test the date parser
    try:
        test_date_parser()
    except Exception as e:
        print(f"Error testing date parser: {str(e)}")
    
    # Test Google Calendar integration
    try:
        test_google_calendar()
    except Exception as e:
        print(f"Error testing Google Calendar: {str(e)}")
    
    # Test Google Tasks integration
    try:
        test_google_tasks()
    except Exception as e:
        print(f"Error testing Google Tasks: {str(e)}")
    
    print("\nTests completed. Please check the results above.")

if __name__ == "__main__":
    main() 