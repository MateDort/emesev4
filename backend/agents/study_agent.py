"""
Study Agent
Handles study creation and retrieval
"""

import os
import google.generativeai as genai
from dotenv import load_dotenv
from datetime import datetime, date
from database.database import Study
from sqlalchemy.orm import Session
import requests
import json

# Load .env from project root
import os
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
load_dotenv(env_path)
load_dotenv()  # Fallback to current directory

class StudyAgent:
    def __init__(self):
        # Support both GEMINI_API_KEY and GEMINI_API
        gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GEMINI_API")
        if gemini_key:
            genai.configure(api_key=gemini_key)
            # Use gemini-2.5-flash (fast and efficient) or gemini-2.5-pro (better quality)
            self.model = genai.GenerativeModel('gemini-2.5-flash')
            self.llm_available = True
        else:
            self.model = None
            self.llm_available = False
        # Support both SERPER_API_KEY and SERPER_API
        self.serper_api_key = os.getenv("SERPER_API_KEY") or os.getenv("SERPER_API")
        self._load_parameters()
    
    def _load_parameters(self):
        """Load study parameters"""
        import os
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        try:
            with open(os.path.join(base_dir, "studies_parameters.md"), "r") as f:
                self.parameters = f.read()
        except FileNotFoundError:
            self.parameters = ""
    
    def create_daily_study(self, db: Session, target_date: str = None):
        """Create a daily study using Serper API to find recent studies"""
        if not self.llm_available:
            raise Exception("GEMINI_API_KEY not set. Cannot create study.")
        
        if target_date is None:
            target_date = date.today().isoformat()
        
        # Check if study already exists for today
        existing = db.query(Study).filter(Study.date == target_date).first()
        if existing:
            return existing
        
        # Extract topics from parameters
        topics = [
            "AI and Machine learning",
            "AI glasses",
            "interaction design (UI,UX)",
            "3d modelling for AI glasses",
            "brain and Neural networks",
            "body language"
        ]
        
        # Search for recent studies using Serper API
        study_found = None
        for topic in topics:
            try:
                # Search for recent studies
                search_query = f"recent study research paper {topic} 2024"
                headers = {
                    "X-API-KEY": self.serper_api_key,
                    "Content-Type": "application/json"
                }
                payload = {
                    "q": search_query,
                    "num": 5
                }
                
                response = requests.post(
                    "https://google.serper.dev/search",
                    headers=headers,
                    json=payload
                )
                
                if response.status_code == 200:
                    results = response.json()
                    if results.get("organic"):
                        study_found = results["organic"][0]
                        break
            except Exception as e:
                continue
        
        if not study_found:
            raise Exception("No recent study found")
        
        # Use LLM to enhance the study
        prompt = f"""
{self.parameters}

I found this study: {study_found.get('title', '')}
URL: {study_found.get('link', '')}
Snippet: {study_found.get('snippet', '')}

Please:
1. Find and read the full study (it should be less than 6 months old)
2. Explain it in a way that's easy to understand
3. Add examples and explain complex concepts like explaining to an 8-year-old
4. Add additional information that might be interesting
5. Keep the original study content intact but enhance it with explanations

Return the enhanced study content in a clear, readable format.
"""
        
        try:
            response = self.model.generate_content(prompt)
            study_content = response.text
            
            # Create study entry
            study = Study(
                date=target_date,
                title=study_found.get("title", "Daily Study"),
                content=study_content,
                source_url=study_found.get("link", ""),
                topics=", ".join(topics)
            )
            
            db.add(study)
            db.commit()
            db.refresh(study)
            
            return study
        
        except Exception as e:
            db.rollback()
            raise Exception(f"Failed to create study: {str(e)}")
    
    def get_today_study(self, db: Session):
        """Get today's study"""
        today = date.today().isoformat()
        study = db.query(Study).filter(Study.date == today).first()
        
        if study:
            return {
                "id": study.id,
                "title": study.title,
                "content": study.content,
                "source_url": study.source_url,
                "topics": study.topics
            }
        return None

