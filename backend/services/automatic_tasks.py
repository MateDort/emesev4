"""
Automatic Tasks Service
Handles scheduled automatic tasks (scheduling, study, news)
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, date
from database.database import get_db
from agents.scheduling_agent import SchedulingAgent
from agents.study_agent import StudyAgent
from agents.news_agent import NewsAgent
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AutomaticTasks:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.scheduling_agent = SchedulingAgent()
        self.study_agent = StudyAgent()
        self.news_agent = NewsAgent()
        self.active_connections = []  # WebSocket connections for notifications
    
    def set_connections(self, connections):
        """Set the active WebSocket connections"""
        self.active_connections = connections
    
    def create_schedule(self):
        """Create daily schedule at 4am"""
        try:
            db = next(get_db())
            self.scheduling_agent.create_daily_schedule(db)
            message = "Schedule done!"
            logger.info(message)
            self._notify_connections(message)
        except Exception as e:
            message = f"Schedule failed due to {str(e)}"
            logger.error(message)
            self._notify_connections(message)
    
    def create_study(self):
        """Create daily study at 4:30am"""
        try:
            db = next(get_db())
            self.study_agent.create_daily_study(db)
            message = "Study created!"
            logger.info(message)
            self._notify_connections(message)
        except Exception as e:
            message = f"Study creation failed due to {str(e)}"
            logger.error(message)
            self._notify_connections(message)
    
    def create_newsletter(self):
        """Create daily newsletter at midnight"""
        try:
            db = next(get_db())
            self.news_agent.create_daily_newsletter(db)
            message = "News letter created"
            logger.info(message)
            self._notify_connections(message)
        except Exception as e:
            message = f"News letter creation failed due to {str(e)}"
            logger.error(message)
            self._notify_connections(message)
    
    def _notify_connections(self, message: str):
        """Notify all active WebSocket connections"""
        import asyncio
        notification = {
            "type": "automatic_task",
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        for connection in self.active_connections:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(connection.send_json(notification))
                else:
                    loop.run_until_complete(connection.send_json(notification))
            except Exception as e:
                logger.error(f"Error notifying connection: {e}")
                pass
    
    def start_scheduler(self):
        """Start the scheduler with all automatic tasks"""
        # Schedule creation at 4:00 AM
        self.scheduler.add_job(
            self.create_schedule,
            trigger=CronTrigger(hour=4, minute=0),
            id='create_schedule',
            name='Create Daily Schedule',
            replace_existing=True
        )
        
        # Study creation at 4:30 AM
        self.scheduler.add_job(
            self.create_study,
            trigger=CronTrigger(hour=4, minute=30),
            id='create_study',
            name='Create Daily Study',
            replace_existing=True
        )
        
        # Newsletter creation at midnight
        self.scheduler.add_job(
            self.create_newsletter,
            trigger=CronTrigger(hour=0, minute=0),
            id='create_newsletter',
            name='Create Daily Newsletter',
            replace_existing=True
        )
        
        self.scheduler.start()
        logger.info("Automatic tasks scheduler started")
    
    def stop_scheduler(self):
        """Stop the scheduler"""
        self.scheduler.shutdown()
        logger.info("Automatic tasks scheduler stopped")

