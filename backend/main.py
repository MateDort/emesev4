"""
Emese v0.4.1 - Main Backend Server
FastAPI server that handles all requests from the frontend
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request, Depends
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
from database.database import init_db, get_db, SessionLocal, ChatHistory
from services.voice_service import VoiceService
from services.tts_service import TTSService
from services.reminder_service import ReminderService
from services.note_service import NoteService
from services.automatic_tasks import AutomaticTasks
from typing import List

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
async def get_schedule(db = Depends(get_db)):
    """Get today's schedule"""
    try:
        schedule = scheduling_agent.get_today_schedule(db)
        
        # If no schedule exists, create one
        if not schedule or len(schedule) == 0:
            try:
                scheduling_agent.create_daily_schedule(db)
                schedule = scheduling_agent.get_today_schedule(db)
            except Exception as e:
                print(f"Error creating schedule: {e}")
        
        return {"schedule": schedule}
    finally:
        db.close()

@app.get("/api/study")
async def get_study(db = Depends(get_db)):
    """Get today's study"""
    try:
        study = study_agent.get_today_study(db)
        
        # If no study exists, create one
        if not study:
            try:
                study_agent.create_daily_study(db)
                study = study_agent.get_today_study(db)
            except Exception as e:
                print(f"Error creating study: {e}")
        
        return {"study": study}
    finally:
        db.close()

@app.get("/api/news")
async def get_news(db = Depends(get_db)):
    """Get today's news"""
    try:
        news = news_agent.get_today_news(db)
        
        # If no news exists, create one
        if not news:
            try:
                news_agent.create_daily_newsletter(db)
                news = news_agent.get_today_news(db)
            except Exception as e:
                print(f"Error creating newsletter: {e}")
        
        return {"news": news}
    finally:
        db.close()

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
            city = "Marietta,GA"  # Default location
            url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=imperial"
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                return {
                    "weather": {
                        "temperature": data["main"]["temp"],
                        "description": data["weather"][0]["description"],
                        "location": "Marietta, GA"
                    }
                }
    except:
        pass
    
    return {
        "weather": {
            "temperature": "N/A",
            "description": "Weather service not configured",
            "location": "Marietta, GA"
        }
    }

@app.get("/api/time")
async def get_time():
    """Get current time"""
    return {"time": datetime.now().isoformat()}

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    """HTTP endpoint for chat (fallback when WebSocket not available)"""
    response = await main_agent.process_message(request.message)
    return response

@app.get("/api/chat/history")
async def chat_history(limit: int = 50, db = Depends(get_db)):
    """Return recent chat history for the client to preload messages."""
    try:
        records = (
            db.query(ChatHistory)
            .order_by(ChatHistory.timestamp.asc())
            .limit(limit)
            .all()
        )
        history = []
        for record in records:
            history.append({
                "user": record.user_message,
                "assistant": record.assistant_message,
                "timestamp": record.timestamp.isoformat() if record.timestamp else None
            })
        return {"history": history}
    finally:
        db.close()

# Reminder routes - specific routes first to avoid conflicts
@app.post("/api/reminders/{reminder_id}/complete")
async def complete_reminder(reminder_id: int, db = Depends(get_db)):
    """Mark a reminder as completed"""
    try:
        reminder = reminder_service.complete_reminder(db, reminder_id)
        if reminder:
            return {
                "message": "Reminder completed",
                "reminder": {
                    "id": reminder.id,
                    "title": reminder.title,
                    "is_completed": reminder.is_completed
                }
            }
        else:
            raise HTTPException(status_code=404, detail="Reminder not found")
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error completing reminder: {e}")
        raise HTTPException(status_code=500, detail=f"Error completing reminder: {str(e)}")
    finally:
        db.close()

@app.delete("/api/reminders/{reminder_id}")
async def delete_reminder(reminder_id: int, db = Depends(get_db)):
    """Delete a reminder"""
    try:
        reminder = reminder_service.delete_reminder(db, reminder_id)
        if reminder:
            return {"message": "Reminder deleted", "id": reminder.id}
        else:
            raise HTTPException(status_code=404, detail="Reminder not found")
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting reminder: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting reminder: {str(e)}")
    finally:
        db.close()

@app.post("/api/reminders")
async def create_reminder(reminder_data: dict, db = Depends(get_db)):
    """Create a new reminder"""
    try:
        reminder = reminder_service.create_reminder(db, reminder_data)
        return {"reminder": reminder}
    finally:
        db.close()

@app.get("/api/reminders")
async def get_reminders(db = Depends(get_db)):
    """Get all active reminders"""
    try:
        reminders = reminder_service.get_active_reminders(db)
        return {"reminders": reminders}
    finally:
        db.close()

@app.post("/api/notes")
async def create_note(note_data: dict, db = Depends(get_db)):
    """Create a new note"""
    try:
        note = note_service.create_note(db, note_data)
        return {"note": note}
    finally:
        db.close()

@app.get("/api/notes")
async def get_notes(db = Depends(get_db)):
    """Get all notes"""
    try:
        notes = note_service.get_all_notes(db)
        return {"notes": notes}
    finally:
        db.close()

@app.get("/api/notes/{note_id}")
async def get_note(note_id: int, db = Depends(get_db)):
    """Get a specific note"""
    try:
        note = note_service.get_note(db, note_id)
        if note:
            return {"note": note}
        else:
            raise HTTPException(status_code=404, detail="Note not found")
    finally:
        db.close()

@app.post("/api/notes/{note_id}")
async def update_note(note_id: int, note_data: dict, db = Depends(get_db)):
    """Update a note"""
    try:
        note = note_service.update_note(db, note_id, note_data)
        return {"note": note}
    finally:
        db.close()

@app.delete("/api/notes/{note_id}")
async def delete_note(note_id: int, db = Depends(get_db)):
    """Delete a note"""
    try:
        note_service.delete_note(db, note_id)
        return {"message": "Note deleted"}
    finally:
        db.close()

# Startup and shutdown are now handled by lifespan context manager

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

