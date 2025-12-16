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
from services.wake_word_service import WakeWordService
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

# Wake word service
wake_word_service = None
wake_word_event_loop = None

def on_wake_word_detected():
    """Callback when wake word is detected - notify all connected clients"""
    import asyncio
    print("🔔 Wake word detected - notifying clients...")
    
    # Send wake word event to all connected clients
    async def notify_clients():
        for connection in active_connections.copy():
            try:
                await connection.send_json({
                    "type": "wake_word_detected",
                    "message": "Wake word 'computer' detected"
                })
            except Exception as e:
                print(f"Error sending wake word notification: {e}")
    
    # Use the stored event loop or get the current one
    try:
        if wake_word_event_loop:
            asyncio.run_coroutine_threadsafe(notify_clients(), wake_word_event_loop)
        else:
            # Fallback: try to get the current event loop
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(notify_clients())
            else:
                loop.run_until_complete(notify_clients())
    except Exception as e:
        print(f"Error in wake word callback: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    global wake_word_service, wake_word_event_loop
    import asyncio
    
    # Store the event loop for wake word callback
    wake_word_event_loop = asyncio.get_event_loop()
    
    # Startup
    automatic_tasks.start_scheduler()
    
    # Initialize and start wake word detection
    try:
        wake_word_service = WakeWordService(wake_word_callback=on_wake_word_detected)
        if wake_word_service.available:
            wake_word_service.start_listening()
            print("✅ Wake word detection started")
        else:
            print("⚠️ Wake word detection not available (check PICOVOICE_ACCESS_KEY)")
    except Exception as e:
        print(f"Error starting wake word detection: {e}")
    
    yield
    
    # Shutdown
    automatic_tasks.stop_scheduler()
    if wake_word_service:
        wake_word_service.stop_listening()
    wake_word_event_loop = None

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
                if not audio_data:
                    await websocket.send_json({
                        "type": "voice_response",
                        "transcription": "",
                        "message": "No audio data received",
                        "audio": None
                    })
                    continue
                
                transcription = await voice_service.transcribe(audio_data)
                
                # Only process if transcription is valid (not an error message)
                if transcription.startswith("Error"):
                    await websocket.send_json({
                        "type": "voice_response",
                        "transcription": "",
                        "message": transcription,
                        "audio": None
                    })
                    continue
                
                response = await main_agent.process_message(transcription)
                audio_response = None
                if response.get("tts"):
                    try:
                        audio_bytes = await tts_service.synthesize(response["message"])
                        if audio_bytes:
                            # Convert to base64 for JSON transmission
                            import base64
                            audio_response = base64.b64encode(audio_bytes).decode('utf-8')
                    except Exception as e:
                        print(f"Error generating TTS: {e}")
                
                await websocket.send_json({
                    "type": "voice_response",
                    "transcription": transcription,
                    "message": response["message"],
                    "action": response.get("action"),
                    "data": response.get("data"),
                    "audio": audio_response
                })
            
            elif message_type == "start_recording":
                # Client is ready to record after wake word detection
                await websocket.send_json({
                    "type": "recording_started",
                    "message": "Recording started - speak now"
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
    """Get current weather using Serper API"""
    import requests
    import re
    try:
        serper_api_key = os.getenv("SERPER_API_KEY") or os.getenv("SERPER_API")
        if not serper_api_key:
            return {
                "weather": {
                    "temperature": "N/A",
                    "description": "Weather service not configured - SERPER_API_KEY not set",
                    "location": "Marietta, GA"
                }
            }
        
        # Search for current weather using Serper
        city = "Marietta, GA"  # Default location
        search_query = f"weather {city} today"
        
        headers = {
            "X-API-KEY": serper_api_key,
            "Content-Type": "application/json"
        }
        payload = {
            "q": search_query,
            "num": 3
        }
        
        response = requests.post(
            "https://google.serper.dev/search",
            headers=headers,
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            
            temperature = None
            description = None
            
            # Check answer box first (Google often provides weather in answerBox)
            if "answerBox" in data:
                answer = data["answerBox"]
                answer_text = str(answer)
                
                # Try to extract temperature (look for patterns like "72°F" or "72 F")
                temp_patterns = [
                    r'(\d+)\s*°\s*F',
                    r'(\d+)\s*°F',
                    r'(\d+)\s*F\b',
                    r'(\d+)\s*degrees?\s*F',
                ]
                for pattern in temp_patterns:
                    temp_match = re.search(pattern, answer_text, re.IGNORECASE)
                    if temp_match:
                        temperature = temp_match.group(1)
                        break
                
                # Extract description (look for weather conditions)
                if "sunny" in answer_text.lower():
                    description = "Sunny"
                elif "cloudy" in answer_text.lower():
                    description = "Cloudy"
                elif "rain" in answer_text.lower():
                    description = "Rainy"
                elif "clear" in answer_text.lower():
                    description = "Clear"
                else:
                    # Take first 50 chars as description
                    description = answer_text[:50].strip()
            
            # Fallback to organic results
            if not temperature and "organic" in data and len(data["organic"]) > 0:
                for result in data["organic"][:2]:  # Check first 2 results
                    snippet = result.get("snippet", "") + " " + result.get("title", "")
                    
                    # Try to extract temperature
                    temp_patterns = [
                        r'(\d+)\s*°\s*F',
                        r'(\d+)\s*°F',
                        r'(\d+)\s*F\b',
                    ]
                    for pattern in temp_patterns:
                        temp_match = re.search(pattern, snippet, re.IGNORECASE)
                        if temp_match:
                            temperature = temp_match.group(1)
                            break
                    
                    if temperature:
                        # Extract description
                        if "sunny" in snippet.lower():
                            description = "Sunny"
                        elif "cloudy" in snippet.lower():
                            description = "Cloudy"
                        elif "rain" in snippet.lower():
                            description = "Rainy"
                        elif "clear" in snippet.lower():
                            description = "Clear"
                        else:
                            description = snippet[:50].strip() if snippet else "Current weather"
                        break
            
            if temperature:
                return {
                    "weather": {
                        "temperature": temperature,
                        "description": description or "Current weather conditions",
                        "location": city
                    }
                }
        
        # If we couldn't extract weather, return a message
        return {
            "weather": {
                "temperature": "N/A",
                "description": "Unable to fetch weather data from search results",
                "location": city
            }
        }
    except Exception as e:
        print(f"Error fetching weather: {e}")
        return {
            "weather": {
                "temperature": "N/A",
                "description": f"Error: {str(e)}",
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

