"""
Database setup and configuration
SQLite database for local storage
"""

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.pool import NullPool
from datetime import datetime
import os

Base = declarative_base()

# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "emese.db")
# Use NullPool for SQLite - creates new connection for each session, no pooling
# This avoids connection pool exhaustion issues with SQLite
engine = create_engine(
    f"sqlite:///{DB_PATH}", 
    connect_args={
        "check_same_thread": False,
        "timeout": 30.0  # Wait up to 30 seconds for locks
    },
    poolclass=NullPool,  # No connection pooling for SQLite
    echo=False  # Set to True for SQL debugging
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Schedule(Base):
    __tablename__ = "schedules"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(String, index=True)
    event_title = Column(String)
    start_time = Column(String)
    end_time = Column(String)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Study(Base):
    __tablename__ = "studies"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(String, index=True)
    title = Column(String)
    content = Column(Text)
    source_url = Column(String, nullable=True)
    topics = Column(String)  # Comma-separated topics
    created_at = Column(DateTime, default=datetime.utcnow)

class News(Base):
    __tablename__ = "news"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(String, index=True)
    title = Column(String)
    content = Column(Text)
    source_url = Column(String, nullable=True)
    topics = Column(String)  # Comma-separated topics
    created_at = Column(DateTime, default=datetime.utcnow)

class Reminder(Base):
    __tablename__ = "reminders"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(Text, nullable=True)
    reminder_time = Column(DateTime)
    is_completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Note(Base):
    __tablename__ = "notes"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    content = Column(Text)
    file_path = Column(String, nullable=True)  # Path to .txt file if saved
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ChatHistory(Base):
    __tablename__ = "chat_history"
    
    id = Column(Integer, primary_key=True, index=True)
    user_message = Column(Text)
    assistant_message = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)

def init_db():
    """Initialize database and create tables"""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

