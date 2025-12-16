"""
Scheduling Agent
Handles all scheduling-related tasks
"""

import os
import google.generativeai as genai
from dotenv import load_dotenv
from datetime import datetime, date
from database.database import Schedule
from sqlalchemy.orm import Session

# Load .env from project root
import os
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
load_dotenv(env_path)
load_dotenv()  # Fallback to current directory

class SchedulingAgent:
    def __init__(self):
        # Support both GEMINI_API_KEY and GEMINI_API
        gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GEMINI_API")
        if gemini_key:
            genai.configure(api_key=gemini_key)
            # Use gemini-2.5-flash (fast and efficient) or gemini-2.5-pro (better quality)
            self.model = genai.GenerativeModel('gemini-2.5-flash')
            self.llm_available = True
        else:
            self.model = None
            self.llm_available = False
        self._load_parameters()
    
    def _load_parameters(self):
        """Load scheduling parameters"""
        import os
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        try:
            with open(os.path.join(base_dir, "scheduling_parameters.md"), "r") as f:
                self.parameters = f.read()
        except FileNotFoundError:
            self.parameters = ""
    
    def create_daily_schedule(self, db: Session, target_date: str = None):
        """Create a daily schedule based on scheduling parameters"""
        if not self.llm_available:
            raise Exception("GEMINI_API_KEY not set. Cannot create schedule.")
        
        if target_date is None:
            target_date = date.today().isoformat()
        
        prompt = f"""
{self.parameters}

Create a detailed daily schedule for {target_date} following all the rules and non-negotiables.
Return the schedule as a JSON array with this format:
[
    {{
        "event_title": "Event name",
        "start_time": "HH:MM",
        "end_time": "HH:MM",
        "description": "Optional description"
    }}
]

Make sure to include all non-negotiable times and follow the ideal day structure when possible.
"""
        
        try:
            response = self.model.generate_content(prompt)
            response_text = response.text
            
            # Extract JSON from response
            import json
            import re
            
            # Try to find JSON array in response
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if json_match:
                schedule_data = json.loads(json_match.group())
            else:
                # Fallback: try to parse entire response
                schedule_data = json.loads(response_text)
            
            # Clear existing schedule for this date
            db.query(Schedule).filter(Schedule.date == target_date).delete()
            
            # Create new schedule entries
            schedule_entries = []
            for event in schedule_data:
                schedule_entry = Schedule(
                    date=target_date,
                    event_title=event.get("event_title", ""),
                    start_time=event.get("start_time", ""),
                    end_time=event.get("end_time", ""),
                    description=event.get("description", "")
                )
                db.add(schedule_entry)
                schedule_entries.append(schedule_entry)
            
            db.commit()
            return schedule_entries
        
        except Exception as e:
            db.rollback()
            raise Exception(f"Failed to create schedule: {str(e)}")
    
    def get_today_schedule(self, db: Session):
        """Get today's schedule"""
        today = date.today().isoformat()
        schedule = db.query(Schedule).filter(Schedule.date == today).order_by(Schedule.start_time).all()
        
        return [
            {
                "id": s.id,
                "event_title": s.event_title,
                "start_time": s.start_time,
                "end_time": s.end_time,
                "description": s.description
            }
            for s in schedule
        ]
    
    def get_current_and_next_event(self, db: Session):
        """Get current and next event"""
        schedule = self.get_today_schedule(db)
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        
        current_event = None
        next_event = None
        
        for event in schedule:
            if event["start_time"] <= current_time <= event["end_time"]:
                current_event = event
            elif event["start_time"] > current_time and next_event is None:
                next_event = event
        
        return {
            "current": current_event,
            "next": next_event
        }

