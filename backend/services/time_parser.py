"""
Time Parser Service
Parses natural language time expressions into datetime objects
"""

import re
from datetime import datetime, timedelta
from dateutil import parser as date_parser
from dateutil.relativedelta import relativedelta

class TimeParser:
    def __init__(self):
        # Patterns for relative time
        self.relative_patterns = [
            (r'in\s+(\d+)\s+minute[s]?', 'minutes'),
            (r'in\s+(\d+)\s+min[s]?', 'minutes'),
            (r'in\s+(\d+)\s+hour[s]?', 'hours'),
            (r'in\s+(\d+)\s+hr[s]?', 'hours'),
            (r'in\s+(\d+)\s+day[s]?', 'days'),
            (r'in\s+(\d+)\s+d', 'days'),
            (r'in\s+(\d+)\s+week[s]?', 'weeks'),
            (r'in\s+(\d+)\s+wk[s]?', 'weeks'),
            (r'in\s+(\d+)\s+month[s]?', 'months'),
            (r'in\s+(\d+)\s+mo[s]?', 'months'),
            (r'in\s+(\d+)\s+year[s]?', 'years'),
            (r'in\s+(\d+)\s+yr[s]?', 'years'),
        ]
        
        # Patterns for absolute time
        self.absolute_patterns = [
            r'at\s+(\d{1,2}):(\d{2})\s*(am|pm)?',
            r'at\s+(\d{1,2})\s*(am|pm)',
            r'on\s+(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})',
            r'(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})',
        ]
    
    def parse_time(self, text: str):
        """
        Parse time from text and return (datetime, reminder_text)
        Returns (None, text) if no time found
        """
        text_lower = text.lower()
        now = datetime.now()
        
        # Try relative time patterns first
        for pattern, unit in self.relative_patterns:
            match = re.search(pattern, text_lower)
            if match:
                value = int(match.group(1))
                reminder_text = re.sub(pattern, '', text_lower, flags=re.IGNORECASE).strip()
                
                if unit == 'minutes':
                    target_time = now + timedelta(minutes=value)
                elif unit == 'hours':
                    target_time = now + timedelta(hours=value)
                elif unit == 'days':
                    target_time = now + timedelta(days=value)
                elif unit == 'weeks':
                    target_time = now + timedelta(weeks=value)
                elif unit == 'months':
                    target_time = now + relativedelta(months=value)
                elif unit == 'years':
                    target_time = now + relativedelta(years=value)
                else:
                    continue
                
                # Clean up reminder text
                reminder_text = re.sub(r'^(remind\s+me|set\s+reminder|reminder)\s+(to\s+)?', '', reminder_text, flags=re.IGNORECASE).strip()
                reminder_text = re.sub(r'^\s*to\s+', '', reminder_text, flags=re.IGNORECASE).strip()
                if not reminder_text:
                    reminder_text = "Reminder"
                
                return target_time, reminder_text
        
        # Try absolute time patterns
        # Time today (e.g., "at 3pm", "at 1:30pm", "at 15:30")
        # First try pattern with colon and am/pm without space (e.g., "at 1:30pm")
        time_match = re.search(r'at\s+(\d{1,2}):(\d{2})(am|pm)', text_lower)
        if not time_match:
            # Try pattern with optional colon and optional space before am/pm (e.g., "at 3pm", "at 3 pm")
            time_match = re.search(r'at\s+(\d{1,2}):?(\d{2})?\s*(am|pm)', text_lower)
        if not time_match:
            # Try pattern without am/pm (assume 24-hour or infer from context)
            time_match = re.search(r'at\s+(\d{1,2}):?(\d{2})?', text_lower)
        
        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2)) if time_match.group(2) and len(time_match.groups()) >= 2 else 0
            am_pm = time_match.group(3) if len(time_match.groups()) >= 3 and time_match.group(3) else None
            
            if am_pm:
                if am_pm == 'pm' and hour != 12:
                    hour += 12
                elif am_pm == 'am' and hour == 12:
                    hour = 0
            elif hour < 12:  # Assume PM if no am/pm and hour < 12
                hour += 12
            
            target_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if target_time < now:
                target_time += timedelta(days=1)
            
            # Extract reminder text by removing time patterns and trigger phrases
            # Remove time patterns (try multiple formats)
            reminder_text = re.sub(r'at\s+\d{1,2}:\d{2}(am|pm)', '', text_lower, flags=re.IGNORECASE).strip()
            reminder_text = re.sub(r'at\s+\d{1,2}:?\d{0,2}\s*(am|pm)', '', reminder_text, flags=re.IGNORECASE).strip()
            reminder_text = re.sub(r'at\s+\d{1,2}:?\d{0,2}', '', reminder_text, flags=re.IGNORECASE).strip()
            # Remove "today" if present
            reminder_text = re.sub(r'\s+today\s*$', '', reminder_text, flags=re.IGNORECASE).strip()
            reminder_text = re.sub(r'^\s*today\s+', '', reminder_text, flags=re.IGNORECASE).strip()
            # Remove trigger phrases and "to"
            reminder_text = re.sub(r'^(make\s+a\s+reminder|remind\s+me|set\s+reminder|create\s+reminder|reminder)\s+(to\s+)?', '', reminder_text, flags=re.IGNORECASE).strip()
            reminder_text = re.sub(r'^\s*to\s+', '', reminder_text, flags=re.IGNORECASE).strip()
            # Clean up extra whitespace
            reminder_text = re.sub(r'\s+', ' ', reminder_text).strip()
            if not reminder_text:
                reminder_text = "Reminder"
            
            return target_time, reminder_text
        
        # Try dateutil parser for complex dates
        try:
            # Try to parse as date string
            parsed_date = date_parser.parse(text, fuzzy=True, default=now)
            if parsed_date > now:
                reminder_text = re.sub(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', '', text, flags=re.IGNORECASE).strip()
                reminder_text = re.sub(r'^(remind\s+me|set\s+reminder|reminder|on)\s+', '', reminder_text, flags=re.IGNORECASE).strip()
                if not reminder_text:
                    reminder_text = "Reminder"
                return parsed_date, reminder_text
        except:
            pass
        
        # No time found
        return None, text

