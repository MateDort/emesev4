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
        
        # Expand each article with longer content using LLM
        expanded_articles = []
        for article in articles:
            try:
                # Extract source domain from URL for display
                source_url = article.get('link', '')
                source_domain = 'Unknown'
                if source_url:
                    try:
                        from urllib.parse import urlparse
                        parsed = urlparse(source_url)
                        source_domain = parsed.netloc.replace('www.', '')
                    except:
                        pass
                
                # Create a longer summary/expansion of the article
                expansion_prompt = f"""
Based on this news article snippet, write a comprehensive article summary (3-4 paragraphs, approximately 300-400 words) that covers:
- The main story and key details
- Why this matters
- Context and background information
- Implications or next steps

Article title: {article.get('title', '')}
Article snippet: {article.get('snippet', '')}
Source: {source_url}

Write a detailed, engaging article summary that someone could read to understand the full story. Make it informative, well-written, and comprehensive. Expand on the snippet to provide more context and details.
"""
                expansion_response = self.model.generate_content(expansion_prompt)
                expanded_content = expansion_response.text
                
                expanded_articles.append({
                    "title": article.get('title', ''),
                    "content": expanded_content,
                    "source_url": source_url,
                    "snippet": article.get('snippet', ''),
                    "source": article.get('source', source_domain)  # Use Serper's source field or fallback to domain
                })
            except Exception as e:
                print(f"Error expanding article {article.get('title', 'unknown')}: {e}")
                # If expansion fails, use original snippet but make it longer
                source_url = article.get('link', '')
                source_domain = 'Unknown'
                if source_url:
                    try:
                        from urllib.parse import urlparse
                        parsed = urlparse(source_url)
                        source_domain = parsed.netloc.replace('www.', '')
                    except:
                        pass
                
                expanded_articles.append({
                    "title": article.get('title', ''),
                    "content": article.get('snippet', ''),
                    "source_url": source_url,
                    "snippet": article.get('snippet', ''),
                    "source": article.get('source', source_domain)
                })
        
        # Store articles as JSON
        articles_json = json.dumps(expanded_articles, indent=2)
        
        # Create news entry with articles JSON
        news = News(
            date=target_date,
            title=f"Daily News - {target_date}",
            content=articles_json,  # Store as JSON
            source_url="",  # Not used anymore, articles have individual URLs
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
            # Try to parse content as JSON (new format) or return as text (old format)
            try:
                articles = json.loads(news.content)
                return {
                    "id": news.id,
                    "title": news.title,
                    "articles": articles,  # Array of articles
                    "content": news.content,  # Keep for backward compatibility
                    "topics": news.topics,
                    "format": "json"  # Indicate new format
                }
            except (json.JSONDecodeError, TypeError):
                # Old format - return as text content
                return {
                    "id": news.id,
                    "title": news.title,
                    "content": news.content,
                    "source_url": news.source_url,
                    "topics": news.topics,
                    "format": "text"  # Indicate old format
                }
        return None

