"""
Reminder Service
Handles reminder creation and management
"""

from datetime import datetime
from database.database import Reminder
from sqlalchemy.orm import Session

class ReminderService:
    def create_reminder(self, db: Session, reminder_data: dict):
        """Create a new reminder"""
        reminder = Reminder(
            title=reminder_data.get("title", "Reminder"),
            description=reminder_data.get("description", ""),
            reminder_time=datetime.fromisoformat(reminder_data.get("reminder_time")),
            is_completed=False
        )
        db.add(reminder)
        db.commit()
        db.refresh(reminder)
        return reminder
    
    def get_active_reminders(self, db: Session):
        """Get all active (non-completed) reminders"""
        now = datetime.now()
        reminders = db.query(Reminder).filter(
            Reminder.is_completed == False,
            Reminder.reminder_time <= now
        ).all()
        
        return [
            {
                "id": r.id,
                "title": r.title,
                "description": r.description,
                "reminder_time": r.reminder_time.isoformat(),
                "is_completed": r.is_completed
            }
            for r in reminders
        ]
    
    def complete_reminder(self, db: Session, reminder_id: int):
        """Mark a reminder as completed"""
        reminder = db.query(Reminder).filter(Reminder.id == reminder_id).first()
        if reminder:
            reminder.is_completed = True
            db.commit()
        return reminder
    
    def delete_reminder(self, db: Session, reminder_id: int):
        """Delete a reminder"""
        reminder = db.query(Reminder).filter(Reminder.id == reminder_id).first()
        if reminder:
            db.delete(reminder)
            db.commit()
        return reminder

