"""
Reminder Service
Handles reminder creation and management
"""

from datetime import datetime
from database.database import Reminder
from sqlalchemy.orm import Session
from services.time_parser import TimeParser

class ReminderService:
    def __init__(self):
        self.time_parser = TimeParser()
    
    def create_reminder(self, db: Session, reminder_data: dict):
        """Create a new reminder"""
        # If reminder_time is a string, try to parse it
        reminder_time = reminder_data.get("reminder_time")
        if isinstance(reminder_time, str):
            if "T" in reminder_time or " " in reminder_time:
                try:
                    reminder_time = datetime.fromisoformat(reminder_time.replace("Z", "+00:00"))
                except:
                    reminder_time = datetime.fromisoformat(reminder_time)
            else:
                reminder_time = datetime.fromisoformat(reminder_time)
        
        reminder = Reminder(
            title=reminder_data.get("title", "Reminder"),
            description=reminder_data.get("description", ""),
            reminder_time=reminder_time,
            is_completed=False
        )
        db.add(reminder)
        db.commit()
        db.refresh(reminder)
        return reminder
    
    def create_reminder_from_text(self, db: Session, text: str):
        """Create a reminder by parsing natural language text"""
        import traceback
        try:
            target_time, reminder_text = self.time_parser.parse_time(text)
            
            if target_time is None:
                return None, "Could not parse time from your message. Please specify a time like 'in 5 minutes' or 'at 3pm'."
            
            reminder = Reminder(
                title=reminder_text,
                description="",
                reminder_time=target_time,
                is_completed=False
            )
            db.add(reminder)
            db.commit()
            db.refresh(reminder)
            
            print(f"Reminder created successfully: ID={reminder.id}, Title='{reminder.title}', Time={reminder.reminder_time}")
            return reminder, None
        except Exception as e:
            db.rollback()
            print(f"Error in create_reminder_from_text: {e}\n{traceback.format_exc()}")
            return None, f"Error creating reminder: {str(e)}"
    
    def get_active_reminders(self, db: Session):
        """Get all active (non-completed) reminders"""
        now = datetime.now()
        reminders = db.query(Reminder).filter(
            Reminder.is_completed == False
        ).order_by(Reminder.reminder_time.asc()).all()
        
        result = []
        for r in reminders:
            time_until = r.reminder_time - now
            if time_until.total_seconds() <= 0:
                # Past due
                countdown = "Overdue"
            else:
                countdown = self._format_countdown(time_until)
            
            result.append({
                "id": r.id,
                "title": r.title,
                "description": r.description,
                "reminder_time": r.reminder_time.isoformat(),
                "is_completed": r.is_completed,
                "countdown": countdown
            })
        
        return result
    
    def _format_countdown(self, time_delta):
        """Format time delta as countdown string (e.g., '1h 3m 30s')"""
        total_seconds = int(time_delta.total_seconds())
        
        days = total_seconds // 86400
        hours = (total_seconds % 86400) // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        parts = []
        if days > 0:
            parts.append(f"{days}d")
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0:
            parts.append(f"{minutes}m")
        if seconds > 0 or len(parts) == 0:
            parts.append(f"{seconds}s")
        
        return " ".join(parts)
    
    def complete_reminder(self, db: Session, reminder_id: int):
        """Mark a reminder as completed"""
        reminder = db.query(Reminder).filter(Reminder.id == reminder_id).first()
        if reminder:
            reminder.is_completed = True
            db.commit()
            db.refresh(reminder)
        return reminder
    
    def delete_reminder(self, db: Session, reminder_id: int):
        """Delete a reminder"""
        reminder = db.query(Reminder).filter(Reminder.id == reminder_id).first()
        if reminder:
            # Store reminder info before deletion
            deleted_id = reminder.id
            db.delete(reminder)
            db.commit()
            # Return a simple dict-like object to indicate success
            class DeletedReminder:
                def __init__(self, id):
                    self.id = id
            return DeletedReminder(deleted_id)
        return None

