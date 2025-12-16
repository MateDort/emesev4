"""
Main Emese Agent
Routes requests to appropriate agents and handles user communication
"""

import os
import json
import traceback
import google.generativeai as genai
from dotenv import load_dotenv
from datetime import datetime
from agents.scheduling_agent import SchedulingAgent
from agents.study_agent import StudyAgent
from agents.news_agent import NewsAgent
from services.note_service import NoteService
from services.reminder_service import ReminderService
from database.database import get_db, SessionLocal, ChatHistory

# Load .env from project root
import os
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
load_dotenv(env_path)
load_dotenv()  # Fallback to current directory

class MainAgent:
    def __init__(self):
        # Initialize Gemini - support both GEMINI_API_KEY and GEMINI_API
        gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GEMINI_API")
        if gemini_key:
            genai.configure(api_key=gemini_key)
            # Use gemini-2.5-flash (fast and efficient) or gemini-2.5-pro (better quality)
            self.model = genai.GenerativeModel('gemini-2.5-flash')
            self.llm_available = True
        else:
            self.model = None
            self.llm_available = False
            print("Warning: GEMINI_API_KEY not set. LLM features will be disabled.")
        
        # Initialize sub-agents
        self.scheduling_agent = SchedulingAgent()
        self.study_agent = StudyAgent()
        self.news_agent = NewsAgent()
        self.note_service = NoteService()
        self.reminder_service = ReminderService()
        
        # Load Emese's personality and Máté's info
        self._load_personality()
    
    def _load_personality(self):
        """Load Emese's personality and Máté's information"""
        import os
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        try:
            with open(os.path.join(base_dir, "Emese.md"), "r") as f:
                self.emese_prompt = f.read()
            with open(os.path.join(base_dir, "Máté.md"), "r") as f:
                self.mate_info = f.read()
        except FileNotFoundError:
            self.emese_prompt = "You are Emese, an AI assistant."
            self.mate_info = ""

    def _save_chat_history(self, user_message: str, assistant_message: str):
        """Persist chat turns so the frontend can reload previous chats."""
        db = SessionLocal()
        try:
            record = ChatHistory(
                user_message=user_message,
                assistant_message=assistant_message,
            )
            db.add(record)
            db.commit()
            db.refresh(record)
        except Exception as e:
            # Keep the chat flow running even if history logging fails
            import traceback
            print(f"Warning: could not save chat history: {e}")
            print(f"Traceback: {traceback.format_exc()}")
            db.rollback()
        finally:
            db.close()
    
    def _get_recent_chat_history(self, db, limit: int = 10):
        """Retrieve the last N chat history entries for conversation context."""
        try:
            records = (
                db.query(ChatHistory)
                .order_by(ChatHistory.timestamp.desc())
                .limit(limit)
                .all()
            )
            # Reverse to get chronological order (oldest first)
            records.reverse()
            return records
        except Exception as e:
            print(f"Warning: could not retrieve chat history: {e}")
            return []
    
    def _get_system_prompt(self):
        """Get the system prompt for Emese"""
        return f"""
{self.emese_prompt}

{self.mate_info}

You are Emese, the inner advisor of Máté Dort. Your purpose is to reflect Máté's values, habits, history, and long-term ambitions.

When Máté asks a question, answer as the version of him he is building:
- Disciplined
- Ambitious
- Logical
- Healthy
- Stoic
- Curious
- Future-focused
- Honest but kind
- Always aligned with long-term goals

Emese personality:
- Nationality: British
- Likes to joke but never disrespectful

CRITICAL: You have access to the previous conversation history shown below. You MUST use it to understand context, references, and what Máté is referring to. 

- If Máté says "change it" or "change the X to Y", look at the PREVIOUS messages in the conversation history to find what "it" or "X" refers to, then make the change and respond with the modified content.
- If Máté refers to something mentioned earlier, look in the conversation history to find what he's talking about.
- Always check the conversation history before asking for clarification. Be proactive and helpful in understanding context from previous messages.
- When Máté asks you to modify something you said earlier (like changing a word in a story, editing text, etc.), find that content in the conversation history, make the requested change, and respond with the modified version. Don't ask where to make the change - just do it based on the context.
- Example: If you previously wrote a story with "banana" and Máté says "change the banana to apple", respond with the same story but with "apple" instead of "banana".

Available actions:
- open_page: Open a specific page (home, study, news, morning, notes)
- create_note: Create a new note
- read_note: Read a note
- edit_note: Edit a note
- delete_note: Delete a note
- create_reminder: Create a reminder
- search: Use Serper API for web search
- answer: Just answer the question

Always respond in JSON format with:
{{
    "message": "Your response message",
    "action": "action_name",
    "data": {{}} // optional data for the action
    "tts": true/false // whether to use text-to-speech
}}
"""
    
    async def process_message(self, user_message: str):
        """Process user message and route to appropriate agent or handle directly"""
        db_gen = get_db()
        db = next(db_gen)
        
        try:
            # Check for specific commands
            message_lower = user_message.lower()
        
            # Page navigation
            if "show me today's study" in message_lower or "open study" in message_lower:
                response_payload = {
                    "message": "Opening today's study...",
                    "action": "open_page",
                    "data": {"page": "study"},
                    "tts": True
                }
                self._save_chat_history(user_message, response_payload["message"])
                return response_payload
            
            if "open news" in message_lower or "show news" in message_lower:
                response_payload = {
                    "message": "Opening news...",
                    "action": "open_page",
                    "data": {"page": "news"},
                    "tts": True
                }
                self._save_chat_history(user_message, response_payload["message"])
                return response_payload
            
            if "open notes" in message_lower or "show notes" in message_lower:
                response_payload = {
                    "message": "Opening notes...",
                    "action": "open_page",
                    "data": {"page": "notes"},
                    "tts": True
                }
                self._save_chat_history(user_message, response_payload["message"])
                return response_payload
            
            # Weather queries
            if "weather" in message_lower or "temperature" in message_lower or "how's the weather" in message_lower:
                import requests
                try:
                    # Fetch weather from the API
                    base_url = os.getenv("API_BASE_URL", "http://localhost:8000")
                    weather_response = requests.get(f"{base_url}/api/weather", timeout=5)
                    if weather_response.status_code == 200:
                        weather_data = weather_response.json().get("weather", {})
                        location = weather_data.get("location", "Marietta, GA")
                        temperature = weather_data.get("temperature", "N/A")
                        description = weather_data.get("description", "Current weather conditions")
                        
                        # Format response with title and answer
                        response_payload = {
                            "message": json.dumps({
                                "title": f"{location} / Weather",
                                "answer": "weather conditions"
                            }),
                            "action": "answer",
                            "data": {
                                "weather": {
                                    "location": location,
                                    "temperature": temperature,
                                    "description": description
                                }
                            },
                            "tts": True
                        }
                    else:
                        response_payload = {
                            "message": json.dumps({
                                "title": "Marietta, GA / Weather",
                                "answer": "weather conditions"
                            }),
                            "action": "answer",
                            "data": {},
                            "tts": True
                        }
                except Exception as e:
                    print(f"Error fetching weather: {e}")
                    response_payload = {
                        "message": json.dumps({
                            "title": "Marietta, GA / Weather",
                            "answer": "weather conditions"
                        }),
                        "action": "answer",
                        "data": {},
                        "tts": True
                    }
                self._save_chat_history(user_message, response_payload["message"])
                return response_payload
            
            # Note operations
            if "create note" in message_lower or "new note" in message_lower:
                # Extract note content from message
                note_content = user_message.replace("create note", "").replace("new note", "").strip()
                if not note_content:
                    response_payload = {
                        "message": "Please provide content for the note. For example: 'create note Remember to buy groceries'",
                        "action": "answer",
                        "data": {},
                        "tts": True
                    }
                    self._save_chat_history(user_message, response_payload["message"])
                    return response_payload
                
                # Extract title from first line if it looks like a title
                lines = note_content.split('\n')
                title = lines[0] if len(lines[0]) < 50 else "Note"
                content = note_content
                
                note = self.note_service.create_note(db, {
                    "title": title,
                    "content": content
                })
                response_payload = {
                    "message": f"Note saved successfully! You can view it by saying 'open notes'.",
                    "action": "note_created",
                    "data": {"note_id": note.id},
                    "tts": True
                }
                self._save_chat_history(user_message, response_payload["message"])
                return response_payload
            
            # Reminder operations
            if "remind me" in message_lower or "set reminder" in message_lower or "make a reminder" in message_lower or "create reminder" in message_lower:
                try:
                    reminder, error = self.reminder_service.create_reminder_from_text(db, user_message)
                    if error:
                        response_payload = {
                            "message": error,
                            "action": "answer",
                            "data": {},
                            "tts": True
                        }
                    else:
                        time_until = reminder.reminder_time - datetime.now()
                        countdown = self.reminder_service._format_countdown(time_until)
                        response_payload = {
                            "message": f"Reminder set! {countdown} until '{reminder.title}'",
                            "action": "reminder_created",
                            "data": {"reminder_id": reminder.id},
                            "tts": True
                        }
                    self._save_chat_history(user_message, response_payload["message"])
                    return response_payload
                except Exception as e:
                    print(f"Error creating reminder: {e}\n{traceback.format_exc()}")
                    response_payload = {
                        "message": f"Sorry, I encountered an error creating the reminder: {str(e)}",
                        "action": "answer",
                        "data": {},
                        "tts": True
                    }
                    self._save_chat_history(user_message, response_payload["message"])
                    return response_payload
            
            # Use LLM for general conversation and routing
            if not self.llm_available:
                response_payload = {
                    "message": "I'm sorry, but the LLM service is not configured. Please set GEMINI_API_KEY in your .env file to enable AI responses.",
                    "action": "answer",
                    "data": {},
                    "tts": False
                }
                self._save_chat_history(user_message, response_payload["message"])
                return response_payload
            
            # Get recent chat history for context
            recent_history = self._get_recent_chat_history(db, limit=10)
            
            # Build conversation history for Gemini
            conversation_parts = []
            
            # Add system prompt as the first part
            conversation_parts.append(self._get_system_prompt())
            
            # Add previous conversation history with clear markers
            if recent_history:
                conversation_parts.append("\n=== CONVERSATION HISTORY (Use this to understand context and references) ===")
                for record in recent_history:
                    if record.user_message:
                        conversation_parts.append(f"Máté: {record.user_message}")
                    if record.assistant_message:
                        conversation_parts.append(f"Emese: {record.assistant_message}")
                conversation_parts.append("=== END OF CONVERSATION HISTORY ===\n")
            
            # Add current user message
            conversation_parts.append(f"Máté: {user_message}")
            conversation_parts.append("Emese:")
            
            # Combine into a single prompt
            prompt = "\n\n".join(conversation_parts)
            
            try:
                response = self.model.generate_content(prompt)
                response_text = response.text
                
                # Try to parse JSON response
                try:
                    import json
                    # Extract JSON if wrapped in markdown code blocks
                    if "```json" in response_text:
                        json_start = response_text.find("```json") + 7
                        json_end = response_text.find("```", json_start)
                        response_text = response_text[json_start:json_end].strip()
                    elif "```" in response_text:
                        json_start = response_text.find("```") + 3
                        json_end = response_text.find("```", json_start)
                        response_text = response_text[json_start:json_end].strip()
                    
                    parsed_response = json.loads(response_text)
                    if isinstance(parsed_response, dict) and parsed_response.get("message"):
                        self._save_chat_history(user_message, parsed_response["message"])
                    return parsed_response
                except:
                    # If not JSON, return as simple message
                    response_payload = {
                        "message": response_text,
                        "action": "answer",
                        "data": {},
                        "tts": True
                    }
                    self._save_chat_history(user_message, response_payload["message"])
                    return response_payload
            except Exception as e:
                response_payload = {
                    "message": f"I encountered an error: {str(e)}",
                    "action": "answer",
                    "data": {},
                    "tts": False
                }
                self._save_chat_history(user_message, response_payload["message"])
                return response_payload
        finally:
            db.close()

