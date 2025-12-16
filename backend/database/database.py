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

# Database path - use absolute path and ensure directory exists
# For cloud deployments, ensure we use a writable path
_db_dir = os.path.dirname(__file__)

# In cloud environments (Railway, Vercel, Heroku), use the app directory
# Railway's filesystem is persistent, so we can use the app directory
if os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("VERCEL") or os.getenv("DYNO"):
    # Cloud environment - use current working directory (usually /app in Docker)
    # Or use a custom DATABASE_DIR env var if set
    _db_dir = os.getenv("DATABASE_DIR", os.getcwd())
else:
    # Local environment - use backend directory
    _db_dir = os.path.join(os.path.dirname(__file__), "..")

# Ensure directory exists and is writable
try:
    os.makedirs(_db_dir, exist_ok=True)
    # Test write permissions
    test_file = os.path.join(_db_dir, ".write_test")
    try:
        with open(test_file, 'w') as f:
            f.write("test")
        os.remove(test_file)
    except Exception as e:
        print(f"⚠️ Warning: Database directory {_db_dir} may not be writable: {e}")
        # Fallback to /tmp if current directory not writable
        _db_dir = "/tmp"
        os.makedirs(_db_dir, exist_ok=True)
except Exception as e:
    print(f"⚠️ Warning: Could not create database directory {_db_dir}: {e}")
    _db_dir = "/tmp"
    os.makedirs(_db_dir, exist_ok=True)

# Use absolute path for database
DB_PATH = os.path.abspath(os.path.join(_db_dir, "emese.db"))
print(f"📁 Database path: {DB_PATH}")
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

