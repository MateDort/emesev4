"""
Main Emese Agent
Routes requests to appropriate agents and handles user communication
"""

import os
import google.generativeai as genai
from dotenv import load_dotenv
from agents.scheduling_agent import SchedulingAgent
from agents.study_agent import StudyAgent
from agents.news_agent import NewsAgent
from services.note_service import NoteService
from services.reminder_service import ReminderService
from database.database import get_db

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
- Nationality: Hungarian
- Likes to joke but never disrespectful

Available actions:
- open_page: Open a specific page (home, study, news, morning)
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
        db = next(get_db())
        
        # Check for specific commands
        message_lower = user_message.lower()
        
        # Page navigation
        if "show me today's study" in message_lower or "open study" in message_lower:
            return {
                "message": "Opening today's study...",
                "action": "open_page",
                "data": {"page": "study"},
                "tts": True
            }
        
        if "open news" in message_lower or "show news" in message_lower:
            return {
                "message": "Opening news...",
                "action": "open_page",
                "data": {"page": "news"},
                "tts": True
            }
        
        # Note operations
        if "create note" in message_lower or "new note" in message_lower:
            # Extract note content from message
            note_content = user_message.replace("create note", "").replace("new note", "").strip()
            note = self.note_service.create_note(db, {
                "title": "Note",
                "content": note_content
            })
            return {
                "message": f"Note created successfully!",
                "action": "note_created",
                "data": {"note_id": note.id},
                "tts": True
            }
        
        # Reminder operations
        if "remind me" in message_lower or "set reminder" in message_lower:
            # This would need more sophisticated parsing
            return {
                "message": "I'll help you create a reminder. Please provide the time and details.",
                "action": "create_reminder",
                "data": {},
                "tts": True
            }
        
        # Use LLM for general conversation and routing
        if not self.llm_available:
            return {
                "message": "I'm sorry, but the LLM service is not configured. Please set GEMINI_API_KEY in your .env file to enable AI responses.",
                "action": "answer",
                "data": {},
                "tts": False
            }
        
        prompt = f"{self._get_system_prompt()}\n\nUser: {user_message}\n\nAssistant:"
        
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
                return parsed_response
            except:
                # If not JSON, return as simple message
                return {
                    "message": response_text,
                    "action": "answer",
                    "data": {},
                    "tts": True
                }
        except Exception as e:
            return {
                "message": f"I encountered an error: {str(e)}",
                "action": "answer",
                "data": {},
                "tts": False
            }

