"""
Natural language date parser for Google integrations.
"""

import re
import datetime
from typing import Optional, Tuple

def parse_natural_language_date(text: str) -> Optional[datetime.datetime]:
    """
    Parse natural language date/time references into datetime objects.
    
    Args:
        text: Natural language text containing date references
        
    Returns:
        datetime object if parsing succeeds, None otherwise
    """
    text = text.lower().strip()
    
    # Current time reference
    now = datetime.datetime.now()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Try to match common date patterns
    
    # Today
    if text in ['today', 'now']:
        return now
    
    # Tomorrow
    if text == 'tomorrow':
        return today + datetime.timedelta(days=1)
    
    # Day after tomorrow
    if text in ['day after tomorrow', 'the day after tomorrow']:
        return today + datetime.timedelta(days=2)
    
    # This week
    if text == 'this week':
        # Return the end of the current week (Sunday)
        days_until_sunday = 6 - now.weekday()
        return today + datetime.timedelta(days=days_until_sunday)
    
    # Next week
    if text == 'next week':
        # Return Monday of next week
        days_until_next_monday = 7 - now.weekday()
        return today + datetime.timedelta(days=days_until_next_monday)
    
    # This weekend
    if text == 'this weekend':
        # Return Saturday
        days_until_saturday = 5 - now.weekday()
        if days_until_saturday < 0:  # It's already weekend
            days_until_saturday += 7
        return today + datetime.timedelta(days=days_until_saturday)
    
    # Next weekend
    if text == 'next weekend':
        # Return Saturday of next week
        days_until_next_saturday = 12 - now.weekday()
        if days_until_next_saturday < 7:  # Make sure it's not this week's weekend
            days_until_next_saturday += 7
        return today + datetime.timedelta(days=days_until_next_saturday)
    
    # This month
    if text == 'this month':
        # Return the last day of the current month
        if now.month == 12:
            next_month = datetime.datetime(now.year + 1, 1, 1)
        else:
            next_month = datetime.datetime(now.year, now.month + 1, 1)
        return next_month - datetime.timedelta(days=1)
    
    # Next month
    if text == 'next month':
        # Return the 1st day of the next month
        if now.month == 12:
            return datetime.datetime(now.year + 1, 1, 1)
        else:
            return datetime.datetime(now.year, now.month + 1, 1)
    
    # Days of the week
    days = {
        'monday': 0, 'mon': 0,
        'tuesday': 1, 'tue': 1, 'tues': 1,
        'wednesday': 2, 'wed': 2,
        'thursday': 3, 'thu': 3, 'thur': 3, 'thurs': 3,
        'friday': 4, 'fri': 4,
        'saturday': 5, 'sat': 5,
        'sunday': 6, 'sun': 6
    }
    
    for day_name, day_num in days.items():
        if text.startswith(f'next {day_name}'):
            days_ahead = day_num - now.weekday()
            if days_ahead <= 0:  # Target day already happened this week
                days_ahead += 7
            
            return today + datetime.timedelta(days=days_ahead)
        
        if text.startswith(day_name) or text == day_name:
            days_ahead = day_num - now.weekday()
            if days_ahead <= 0:  # Target day already happened this week
                days_ahead += 7
            
            return today + datetime.timedelta(days=days_ahead)
    
    # Try matching specific date formats
    # Format: MM/DD/YYYY or MM-DD-YYYY
    date_match = re.match(r'(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})', text)
    if date_match:
        month, day, year = map(int, date_match.groups())
        try:
            return datetime.datetime(year, month, day)
        except ValueError:
            pass
    
    # Try matching time formats
    # With AM/PM: HH:MM AM/PM
    time_match = re.search(r'(\d{1,2}):?(\d{2})?\s*(am|pm)', text)
    if time_match:
        hour, minute, ampm = time_match.groups()
        hour = int(hour)
        minute = int(minute) if minute else 0
        
        if ampm.lower() == 'pm' and hour < 12:
            hour += 12
        elif ampm.lower() == 'am' and hour == 12:
            hour = 0
        
        return now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    
    # 24-hour format: HH:MM
    time_match_24h = re.search(r'(\d{1,2}):(\d{2})(?!\s*[ap]m)', text)
    if time_match_24h:
        hour, minute = map(int, time_match_24h.groups())
        return now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    
    # Try "at X" format
    at_time_match = re.search(r'at\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)?', text)
    if at_time_match:
        hour, minute, ampm = at_time_match.groups()
        hour = int(hour)
        minute = int(minute) if minute else 0
        
        if ampm and ampm.lower() == 'pm' and hour < 12:
            hour += 12
        elif ampm and ampm.lower() == 'am' and hour == 12:
            hour = 0
        
        return now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    
    # Try "in X hours/minutes" format
    in_time_match = re.search(r'in\s+(\d+)\s+(hour|minute|min|hr)s?', text)
    if in_time_match:
        amount, unit = in_time_match.groups()
        amount = int(amount)
        
        if unit in ['hour', 'hr']:
            return now + datetime.timedelta(hours=amount)
        elif unit in ['minute', 'min']:
            return now + datetime.timedelta(minutes=amount)
    
    # Special case for common time expressions like "half past three", "quarter to five", etc.
    if 'half past' in text or 'thirty past' in text:
        hour_match = re.search(r'(half|thirty) past (\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)(?:\s*(am|pm))?', text)
        if hour_match:
            _, hour_str, ampm = hour_match.groups()
            hour_map = {'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5, 'six': 6, 
                      'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10, 'eleven': 11, 'twelve': 12}
            
            try:
                hour = int(hour_str)
            except ValueError:
                hour = hour_map.get(hour_str.lower(), 0)
            
            if ampm and ampm.lower() == 'pm' and hour < 12:
                hour += 12
            elif ampm and ampm.lower() == 'am' and hour == 12:
                hour = 0
            
            return now.replace(hour=hour, minute=30, second=0, microsecond=0)
    
    if 'quarter past' in text or 'fifteen past' in text:
        hour_match = re.search(r'(quarter|fifteen) past (\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)(?:\s*(am|pm))?', text)
        if hour_match:
            _, hour_str, ampm = hour_match.groups()
            hour_map = {'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5, 'six': 6, 
                      'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10, 'eleven': 11, 'twelve': 12}
            
            try:
                hour = int(hour_str)
            except ValueError:
                hour = hour_map.get(hour_str.lower(), 0)
            
            if ampm and ampm.lower() == 'pm' and hour < 12:
                hour += 12
            elif ampm and ampm.lower() == 'am' and hour == 12:
                hour = 0
            
            return now.replace(hour=hour, minute=15, second=0, microsecond=0)
    
    if 'quarter to' in text or 'fifteen to' in text:
        hour_match = re.search(r'(quarter|fifteen) to (\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)(?:\s*(am|pm))?', text)
        if hour_match:
            _, hour_str, ampm = hour_match.groups()
            hour_map = {'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5, 'six': 6, 
                      'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10, 'eleven': 11, 'twelve': 12}
            
            try:
                hour = int(hour_str)
            except ValueError:
                hour = hour_map.get(hour_str.lower(), 0)
            
            if ampm and ampm.lower() == 'pm' and hour < 12:
                hour += 12
            elif ampm and ampm.lower() == 'am' and hour == 12:
                hour = 0
            
            if hour > 0:
                hour -= 1
            else:
                hour = 23
            
            return now.replace(hour=hour, minute=45, second=0, microsecond=0)
    
    # Handle "half X" (British English for half past X-1)
    half_hour_match = re.search(r'half (\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)(?:\s*(am|pm))?', text)
    if half_hour_match:
        hour_str, ampm = half_hour_match.groups()
        hour_map = {'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5, 'six': 6, 
                  'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10, 'eleven': 11, 'twelve': 12}
        
        try:
            hour = int(hour_str)
        except ValueError:
            hour = hour_map.get(hour_str.lower(), 0)
        
        if hour > 0:
            hour -= 1
        else:
            hour = 11
        
        if ampm and ampm.lower() == 'pm' and hour < 12:
            hour += 12
        elif ampm and ampm.lower() == 'am' and hour == 12:
            hour = 0
        
        return now.replace(hour=hour, minute=30, second=0, microsecond=0)
    
    # Failed to parse the date
    return None

def parse_date_time_range(text: str) -> Tuple[Optional[datetime.datetime], Optional[datetime.datetime]]:
    """
    Parse a natural language date/time range into start and end datetime objects.
    
    Args:
        text: Natural language text containing date range reference
        
    Returns:
        Tuple of (start datetime, end datetime), either may be None if parsing fails
    """
    text = text.lower().strip()
    
    # Try to find patterns like "from X to Y" or "between X and Y"
    from_to_match = re.search(r'(?:from|between) (.*?) (?:to|and) (.*)', text)
    if from_to_match:
        start_text, end_text = from_to_match.groups()
        start_time = parse_natural_language_date(start_text)
        end_time = parse_natural_language_date(end_text)
        return start_time, end_time
    
    # Check for "until" or "till" patterns
    until_match = re.search(r'(?:until|till) (.*)', text)
    if until_match:
        end_text = until_match.group(1)
        end_time = parse_natural_language_date(end_text)
        return datetime.datetime.now(), end_time
    
    # Check for duration patterns like "for X hours/minutes"
    duration_match = re.search(r'for (\d+) (hour|minute|min|hr)s?', text)
    if duration_match:
        amount, unit = duration_match.groups()
        amount = int(amount)
        start_time = datetime.datetime.now()
        
        if unit in ['hour', 'hr']:
            end_time = start_time + datetime.timedelta(hours=amount)
        elif unit in ['minute', 'min']:
            end_time = start_time + datetime.timedelta(minutes=amount)
        else:
            end_time = None
            
        return start_time, end_time
    
    # If we can't find a range, try to parse it as a single date/time
    single_time = parse_natural_language_date(text)
    if single_time:
        # For a single time reference, default to a 1-hour event
        return single_time, single_time + datetime.timedelta(hours=1)
    
    # Failed to parse
    return None, None 