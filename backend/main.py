"""
Emese v0.4.1 - Main Backend Server
FastAPI server that handles all requests from the frontend
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn
from dotenv import load_dotenv
import os
import json
from datetime import datetime
from pydantic import BaseModel

from agents.main_agent import MainAgent
from agents.scheduling_agent import SchedulingAgent
from agents.study_agent import StudyAgent
from agents.news_agent import NewsAgent
from database.database import init_db, get_db
from services.voice_service import VoiceService
from services.tts_service import TTSService
from services.reminder_service import ReminderService
from services.note_service import NoteService
from services.automatic_tasks import AutomaticTasks

# Load .env from project root (parent directory)
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(env_path)
# Also try loading from current directory as fallback
load_dotenv()

# Initialize database
init_db()

# Initialize services
main_agent = MainAgent()
scheduling_agent = SchedulingAgent()
study_agent = StudyAgent()
news_agent = NewsAgent()
voice_service = VoiceService()
tts_service = TTSService()
reminder_service = ReminderService()
note_service = NoteService()
automatic_tasks = AutomaticTasks()

# WebSocket connections
active_connections = []

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    # Startup
    automatic_tasks.start_scheduler()
    yield
    # Shutdown
    automatic_tasks.stop_scheduler()

app = FastAPI(title="Emese API", version="0.4.1", lifespan=lifespan)

# Request models
class ChatRequest(BaseModel):
    message: str

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your Vercel domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time chat and voice communication"""
    await websocket.accept()
    active_connections.append(websocket)
    automatic_tasks.set_connections(active_connections)
    try:
        while True:
            data = await websocket.receive_json()
            message_type = data.get("type")
            
            if message_type == "chat":
                # Handle chat message
                user_message = data.get("message", "")
                response = await main_agent.process_message(user_message)
                await websocket.send_json({
                    "type": "chat_response",
                    "message": response["message"],
                    "action": response.get("action"),
                    "data": response.get("data"),
                    "tts": response.get("tts", False)
                })
            
            elif message_type == "voice":
                # Handle voice input
                audio_data = data.get("audio")
                transcription = await voice_service.transcribe(audio_data)
                response = await main_agent.process_message(transcription)
                audio_response = None
                if response.get("tts"):
                    audio_response = await tts_service.synthesize(response["message"])
                await websocket.send_json({
                    "type": "voice_response",
                    "transcription": transcription,
                    "message": response["message"],
                    "audio": audio_response
                })
            
            elif message_type == "wakeword_detected":
                # Wake word "computer" detected
                await websocket.send_json({
                    "type": "wakeword_ack",
                    "message": "Listening..."
                })
    
    except WebSocketDisconnect:
        active_connections.remove(websocket)
        automatic_tasks.set_connections(active_connections)

@app.get("/")
async def root():
    return {"message": "Emese API v0.4.1", "status": "running"}

@app.get("/api/schedule")
async def get_schedule():
    """Get today's schedule"""
    db = next(get_db())
    schedule = scheduling_agent.get_today_schedule(db)
    
    # If no schedule exists, create one
    if not schedule or len(schedule) == 0:
        try:
            scheduling_agent.create_daily_schedule(db)
            schedule = scheduling_agent.get_today_schedule(db)
        except Exception as e:
            print(f"Error creating schedule: {e}")
    
    return {"schedule": schedule}

@app.get("/api/study")
async def get_study():
    """Get today's study"""
    db = next(get_db())
    study = study_agent.get_today_study(db)
    
    # If no study exists, create one
    if not study:
        try:
            study_agent.create_daily_study(db)
            study = study_agent.get_today_study(db)
        except Exception as e:
            print(f"Error creating study: {e}")
    
    return {"study": study}

@app.get("/api/news")
async def get_news():
    """Get today's news"""
    db = next(get_db())
    news = news_agent.get_today_news(db)
    
    # If no news exists, create one
    if not news:
        try:
            news_agent.create_daily_newsletter(db)
            news = news_agent.get_today_news(db)
        except Exception as e:
            print(f"Error creating newsletter: {e}")
    
    return {"news": news}

@app.get("/api/weather")
async def get_weather():
    """Get current weather"""
    # Using a free weather API (OpenWeatherMap or similar)
    # For now, return placeholder
    import requests
    try:
        # You can add OpenWeatherMap API key to .env
        api_key = os.getenv("WEATHER_API_KEY")
        if api_key:
            # Example with OpenWeatherMap
            city = "Atlanta"  # Default location
            url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=imperial"
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                return {
                    "weather": {
                        "temperature": data["main"]["temp"],
                        "description": data["weather"][0]["description"],
                        "location": city
                    }
                }
    except:
        pass
    
    return {"weather": {"temperature": "N/A", "description": "Weather service not configured"}}

@app.get("/api/time")
async def get_time():
    """Get current time"""
    return {"time": datetime.now().isoformat()}

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    """HTTP endpoint for chat (fallback when WebSocket not available)"""
    response = await main_agent.process_message(request.message)
    return response

@app.post("/api/reminders")
async def create_reminder(reminder_data: dict):
    """Create a new reminder"""
    db = next(get_db())
    reminder = reminder_service.create_reminder(db, reminder_data)
    return {"reminder": reminder}

@app.get("/api/reminders")
async def get_reminders():
    """Get all active reminders"""
    db = next(get_db())
    reminders = reminder_service.get_active_reminders(db)
    return {"reminders": reminders}

@app.post("/api/notes")
async def create_note(note_data: dict):
    """Create a new note"""
    db = next(get_db())
    note = note_service.create_note(db, note_data)
    return {"note": note}

@app.get("/api/notes")
async def get_notes():
    """Get all notes"""
    db = next(get_db())
    notes = note_service.get_all_notes(db)
    return {"notes": notes}

@app.post("/api/notes/{note_id}")
async def update_note(note_id: int, note_data: dict):
    """Update a note"""
    db = next(get_db())
    note = note_service.update_note(db, note_id, note_data)
    return {"note": note}

@app.delete("/api/notes/{note_id}")
async def delete_note(note_id: int):
    """Delete a note"""
    db = next(get_db())
    note_service.delete_note(db, note_id)
    return {"message": "Note deleted"}

# Startup and shutdown are now handled by lifespan context manager

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

