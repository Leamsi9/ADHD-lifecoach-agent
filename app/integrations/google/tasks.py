"""
Google Tasks integration for the Bahai Life Coach agent.
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
from app.integrations.google.calendar import get_google_credentials

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/tasks']

def get_tasks(max_results=10, list_id=None):
    """
    Get tasks from Google Tasks.
    
    Args:
        max_results: Maximum number of tasks to return.
        list_id: Task list ID to get tasks from (defaults to primary).
        
    Returns:
        A list of tasks.
    """
    try:
        # Get credentials
        creds = get_google_credentials()
        if not creds:
            logger.warning("No valid credentials found for Google Tasks")
            return _get_mock_tasks(max_results)
        
        # Build the service
        service = build('tasks', 'v1', credentials=creds)
        
        # Get the task list ID if not provided
        if not list_id:
            # Get the default task list
            lists = service.tasklists().list().execute()
            if not lists or 'items' not in lists:
                logger.warning("No task lists found")
                return _get_mock_tasks(max_results)
            
            list_id = lists['items'][0]['id']
        
        # Get tasks from the list
        tasks_result = service.tasks().list(
            tasklist=list_id,
            maxResults=max_results,
            showCompleted=False
        ).execute()
        
        # Process the tasks
        tasks = tasks_result.get('items', [])
        
        # Format the tasks
        formatted_tasks = []
        for task in tasks:
            formatted_tasks.append({
                'id': task['id'],
                'title': task['title'],
                'notes': task.get('notes', ''),
                'due': task.get('due', ''),
                'status': task.get('status', 'needsAction')
            })
        
        return formatted_tasks
    
    except Exception as e:
        logger.error(f"Error getting tasks: {str(e)}")
        return _get_mock_tasks(max_results)

def create_task(title, notes=None, due_date=None, list_id=None):
    """
    Create a task in Google Tasks.
    
    Args:
        title: Title of the task.
        notes: Notes for the task.
        due_date: Due date for the task.
        list_id: Task list ID to create the task in (defaults to primary).
        
    Returns:
        The created task.
    """
    try:
        # Get credentials
        creds = get_google_credentials()
        if not creds:
            logger.warning("No valid credentials found for Google Tasks")
            return _create_mock_task(title, notes, due_date)
        
        # Build the service
        service = build('tasks', 'v1', credentials=creds)
        
        # Get the task list ID if not provided
        if not list_id:
            # Get the default task list
            lists = service.tasklists().list().execute()
            if not lists or 'items' not in lists:
                logger.warning("No task lists found")
                return _create_mock_task(title, notes, due_date)
            
            list_id = lists['items'][0]['id']
        
        # Create the task
        task_body = {
            'title': title,
            'status': 'needsAction'
        }
        
        if notes:
            task_body['notes'] = notes
        
        if due_date:
            # Convert due_date to RFC 3339 format if it's not already
            if isinstance(due_date, str) and 'T' not in due_date:
                due_date = f"{due_date}T00:00:00.000Z"
            task_body['due'] = due_date
        
        # Create the task
        task = service.tasks().insert(
            tasklist=list_id,
            body=task_body
        ).execute()
        
        # Format the task
        formatted_task = {
            'id': task['id'],
            'title': task['title'],
            'notes': task.get('notes', ''),
            'due': task.get('due', ''),
            'status': task.get('status', 'needsAction')
        }
        
        return formatted_task
    
    except Exception as e:
        logger.error(f"Error creating task: {str(e)}")
        return _create_mock_task(title, notes, due_date)

def _get_mock_tasks(max_results=10):
    """
    Get mock tasks for testing.
    
    Args:
        max_results: Maximum number of tasks to return.
        
    Returns:
        A list of mock tasks.
    """
    # Create some mock tasks
    mock_tasks = [
        {
            'id': '1',
            'title': 'Read Bahá\'í writings',
            'notes': 'Focus on the Hidden Words',
            'due': (datetime.datetime.now() + datetime.timedelta(days=1)).strftime('%Y-%m-%dT00:00:00.000Z'),
            'status': 'needsAction'
        },
        {
            'id': '2',
            'title': 'Prepare for devotional gathering',
            'notes': 'Select prayers and readings',
            'due': (datetime.datetime.now() + datetime.timedelta(days=3)).strftime('%Y-%m-%dT00:00:00.000Z'),
            'status': 'needsAction'
        },
        {
            'id': '3',
            'title': 'Contact community members',
            'notes': 'Check in with friends who missed the last Feast',
            'due': (datetime.datetime.now() + datetime.timedelta(days=2)).strftime('%Y-%m-%dT00:00:00.000Z'),
            'status': 'needsAction'
        }
    ]
    
    # Return only the requested number of tasks
    return mock_tasks[:max_results]

def _create_mock_task(title, notes=None, due_date=None):
    """
    Create a mock task for testing.
    
    Args:
        title: Title of the task.
        notes: Notes for the task.
        due_date: Due date for the task.
        
    Returns:
        A mock task.
    """
    # Format the due date if provided
    if due_date:
        # Convert due_date to RFC 3339 format if it's not already
        if isinstance(due_date, str) and 'T' not in due_date:
            due_date = f"{due_date}T00:00:00.000Z"
    else:
        # Default to tomorrow
        due_date = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime('%Y-%m-%dT00:00:00.000Z')
    
    # Create a mock task
    mock_task = {
        'id': f"mock_{datetime.datetime.now().timestamp()}",
        'title': title,
        'notes': notes or '',
        'due': due_date,
        'status': 'needsAction'
    }
    
    return mock_task

class TaskCreate(BaseModel):
    """Input for creating a task."""
    title: str = Field(..., description="Title of the task")
    notes: Optional[str] = Field(None, description="Notes for the task")
    due_date: Optional[str] = Field(None, description="Due date in ISO format or natural language (e.g., 'tomorrow')")
    list_id: Optional[str] = Field(None, description="The task list ID to create the task in (defaults to primary)")

class GoogleTaskCreateTool(BaseTool):
    """Tool for creating Google Tasks."""
    name = "google_task_create"
    description = """
    Create a task in Google Tasks.
    This tool is useful when the user wants to add a to-do item, reminder, or task to their list.
    Input should include title, and optionally notes, due_date, and list_id.
    """
    args_schema = TaskCreate
    
    def _run(self, title: str, notes: Optional[str] = None, 
             due_date: Optional[str] = None, list_id: Optional[str] = None) -> str:
        """Run the tool."""
        try:
            creds = get_google_credentials()
            service = build('tasks', 'v1', credentials=creds)
            
            # If no list ID is provided, get the default task list
            if not list_id:
                task_lists = service.tasklists().list().execute()
                if not task_lists or 'items' not in task_lists:
                    return "No task lists found. Please create a task list first."
                list_id = task_lists['items'][0]['id']  # Use the first list as default
            
            # Parse due date if provided
            if due_date:
                try:
                    due_datetime = datetime.datetime.fromisoformat(due_date)
                    # Google Tasks API requires RFC 3339 timestamp format
                    due_date = due_datetime.isoformat() + 'Z'
                except ValueError:
                    # In a real implementation, use a natural language date parser here
                    # For now, just default to tomorrow
                    tomorrow = datetime.datetime.now() + datetime.timedelta(days=1)
                    tomorrow = tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)
                    due_date = tomorrow.isoformat() + 'Z'
            
            # Create the task
            task = {
                'title': title
            }
            
            if notes:
                task['notes'] = notes
            
            if due_date:
                task['due'] = due_date
            
            # Call the Tasks API
            task = service.tasks().insert(tasklist=list_id, body=task).execute()
            
            return f"Task created successfully. Task ID: {task.get('id')}"
        
        except Exception as e:
            if DEBUG:
                return f"Error creating task: {str(e)}"
            return "Error creating task. Please check your Google Tasks access."

class TaskQuery(BaseModel):
    """Input for querying tasks."""
    list_id: Optional[str] = Field(None, description="The task list ID to query (defaults to primary)")
    show_completed: Optional[bool] = Field(False, description="Whether to include completed tasks")
    max_results: Optional[int] = Field(100, description="Maximum number of results to return")
    due_min: Optional[str] = Field(None, description="Minimum due date in ISO format or natural language")
    due_max: Optional[str] = Field(None, description="Maximum due date in ISO format or natural language")

class GoogleTaskViewTool(BaseTool):
    """Tool for viewing Google Tasks."""
    name = "google_task_view"
    description = """
    View tasks from Google Tasks.
    This tool is useful when the user wants to check their to-do list or look for specific tasks.
    Input should include optional list_id, show_completed, max_results, due_min, and due_max parameters.
    """
    args_schema = TaskQuery
    
    def _run(self, list_id: Optional[str] = None, show_completed: Optional[bool] = False,
             max_results: Optional[int] = 100, due_min: Optional[str] = None,
             due_max: Optional[str] = None) -> str:
        """Run the tool."""
        try:
            creds = get_google_credentials()
            service = build('tasks', 'v1', credentials=creds)
            
            # If no list ID is provided, get the default task list
            if not list_id:
                task_lists = service.tasklists().list().execute()
                if not task_lists or 'items' not in task_lists:
                    return "No task lists found. Please create a task list first."
                list_id = task_lists['items'][0]['id']  # Use the first list as default
            
            # Parse date boundaries if provided
            params = {
                'tasklist': list_id,
                'maxResults': max_results,
                'showCompleted': show_completed
            }
            
            if due_min:
                try:
                    due_min_datetime = datetime.datetime.fromisoformat(due_min)
                    params['dueMin'] = due_min_datetime.isoformat() + 'Z'
                except ValueError:
                    # Ignore invalid dates for simplicity
                    pass
            
            if due_max:
                try:
                    due_max_datetime = datetime.datetime.fromisoformat(due_max)
                    params['dueMax'] = due_max_datetime.isoformat() + 'Z'
                except ValueError:
                    # Ignore invalid dates for simplicity
                    pass
            
            # Get tasks from the Google Tasks API
            tasks_result = service.tasks().list(**params).execute()
            
            tasks = tasks_result.get('items', [])
            
            if not tasks:
                return "No tasks found."
            
            # Format the tasks for display
            task_list = []
            for task in tasks:
                status = "✓" if task.get('status') == 'completed' else "○"
                due_date = ""
                if 'due' in task:
                    due_date_str = task['due']
                    due_dt = datetime.datetime.fromisoformat(due_date_str.replace('Z', '+00:00'))
                    due_date = f" (due: {due_dt.strftime('%Y-%m-%d')})"
                
                task_list.append(f"{status} {task['title']}{due_date}")
            
            return "\n".join(task_list)
        
        except Exception as e:
            if DEBUG:
                return f"Error viewing tasks: {str(e)}"
            return "Error viewing tasks. Please check your Google Tasks access."

class TaskComplete(BaseModel):
    """Input for completing a task."""
    task_id: str = Field(..., description="ID of the task to complete")
    list_id: Optional[str] = Field(None, description="The task list ID containing the task (defaults to primary)")

class GoogleTaskCompleteTool(BaseTool):
    """Tool for completing Google Tasks."""
    name = "google_task_complete"
    description = """
    Mark a task as completed in Google Tasks.
    This tool is useful when the user has finished a task and wants to mark it as done.
    Input should include task_id and optionally list_id.
    """
    args_schema = TaskComplete
    
    def _run(self, task_id: str, list_id: Optional[str] = None) -> str:
        """Run the tool."""
        try:
            creds = get_google_credentials()
            service = build('tasks', 'v1', credentials=creds)
            
            # If no list ID is provided, get the default task list
            if not list_id:
                task_lists = service.tasklists().list().execute()
                if not task_lists or 'items' not in task_lists:
                    return "No task lists found. Please create a task list first."
                list_id = task_lists['items'][0]['id']  # Use the first list as default
            
            # Get the task first
            task = service.tasks().get(tasklist=list_id, task=task_id).execute()
            
            # Update the task status to 'completed'
            task['status'] = 'completed'
            task['completed'] = datetime.datetime.utcnow().isoformat() + 'Z'
            
            # Call the Tasks API to update the task
            updated_task = service.tasks().update(tasklist=list_id, task=task_id, body=task).execute()
            
            return f"Task '{updated_task.get('title')}' marked as completed."
        
        except Exception as e:
            if DEBUG:
                return f"Error completing task: {str(e)}"
            return "Error completing task. Please check your Google Tasks access." 