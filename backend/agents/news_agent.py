"""
News Agent
Handles news letter creation and retrieval
"""

import os
import google.generativeai as genai
from dotenv import load_dotenv
from datetime import datetime, date, timedelta
from database.database import News
from sqlalchemy.orm import Session
import requests
import json

# Load .env from project root
import os
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
load_dotenv(env_path)
load_dotenv()  # Fallback to current directory

class NewsAgent:
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
        """Load news parameters"""
        import os
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        try:
            with open(os.path.join(base_dir, "news_letter_parameters.md"), "r") as f:
                self.parameters = f.read()
        except FileNotFoundError:
            self.parameters = ""
    
    def create_daily_newsletter(self, db: Session, target_date: str = None):
        """Create a daily newsletter with 10 articles"""
        if not self.llm_available:
            raise Exception("GEMINI_API_KEY not set. Cannot create newsletter.")
        
        if target_date is None:
            target_date = date.today().isoformat()
        
        # Check if news already exists for today
        existing = db.query(News).filter(News.date == target_date).first()
        if existing:
            return existing
        
        topics = [
            "AI and Machine learning",
            "AI glasses",
            "interaction design (UI,UX)",
            "3d modelling for AI glasses",
            "brain and Neural networks",
            "body language",
            "Formula 1"
        ]
        
        # Search for recent news articles
        articles = []
        for topic in topics:
            try:
                search_query = f"{topic} news yesterday"
                headers = {
                    "X-API-KEY": self.serper_api_key,
                    "Content-Type": "application/json"
                }
                payload = {
                    "q": search_query,
                    "num": 3,
                    "tbs": "qdr:d"  # Past day
                }
                
                response = requests.post(
                    "https://google.serper.dev/search",
                    headers=headers,
                    json=payload
                )
                
                if response.status_code == 200:
                    results = response.json()
                    if results.get("organic"):
                        articles.extend(results["organic"][:2])  # Get top 2 per topic
            except Exception as e:
                continue
        
        # Limit to 10 best articles
        articles = articles[:10]
        
        if len(articles) < 5:
            raise Exception("Not enough articles found")
        
        # Format as newspaper style
        prompt = f"""
{self.parameters}

Create a newspaper-style newsletter with these articles:
{json.dumps(articles, indent=2)}

Format it like an old newspaper with:
- Headlines
- Article summaries
- Clear sections
- Professional newspaper layout

Make it interesting and engaging while maintaining a newspaper aesthetic.
"""
        
        try:
            response = self.model.generate_content(prompt)
            news_content = response.text
            
            # Create news entry
            news = News(
                date=target_date,
                title=f"Daily News - {target_date}",
                content=news_content,
                source_url="",
                topics=", ".join(topics)
            )
            
            db.add(news)
            db.commit()
            db.refresh(news)
            
            return news
        
        except Exception as e:
            db.rollback()
            raise Exception(f"Failed to create newsletter: {str(e)}")
    
    def get_today_news(self, db: Session):
        """Get today's news"""
        today = date.today().isoformat()
        news = db.query(News).filter(News.date == today).first()
        
        if news:
            return {
                "id": news.id,
                "title": news.title,
                "content": news.content,
                "source_url": news.source_url,
                "topics": news.topics
            }
        return None

