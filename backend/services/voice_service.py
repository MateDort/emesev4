"""
Voice Service
Handles speech-to-text using Whisper API
"""

import os
from openai import OpenAI
from dotenv import load_dotenv

# Load .env from project root
import os
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
load_dotenv(env_path)
load_dotenv()  # Fallback to current directory

class VoiceService:
    def __init__(self):
        # Support both OPENAI_API_KEY and GPT_API
        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("GPT_API")
        if api_key:
            self.client = OpenAI(api_key=api_key)
            self.available = True
        else:
            self.client = None
            self.available = False
            print("Warning: OPENAI_API_KEY not set. Voice transcription will be disabled.")
    
    async def transcribe(self, audio_data):
        """Transcribe audio to text using Whisper API"""
        if not self.available:
            return "Error: Voice transcription is not available. Please set OPENAI_API_KEY in your .env file."
        try:
            # Save audio data temporarily
            import tempfile
            import base64
            
            # Decode base64 audio if needed
            if isinstance(audio_data, str):
                # Remove data URL prefix if present
                if ',' in audio_data:
                    audio_data = audio_data.split(',')[1]
                audio_bytes = base64.b64decode(audio_data)
            else:
                audio_bytes = audio_data
            
            # Determine file extension based on audio format
            # WebM/Opus is common from browser, but Whisper accepts various formats
            # We'll use .webm extension and let Whisper handle it
            with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp_file:
                tmp_file.write(audio_bytes)
                tmp_file_path = tmp_file.name
            
            # Transcribe using Whisper
            with open(tmp_file_path, "rb") as audio_file:
                transcript = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language="en"  # Optional: specify language for better accuracy
                )
            
            # Clean up
            os.unlink(tmp_file_path)
            
            return transcript.text
        except Exception as e:
            return f"Error transcribing audio: {str(e)}"
    
    def detect_wakeword(self, audio_data):
        """Detect wake word 'computer' in audio"""
        # This would need a wake word detection model
        # For now, we'll use a simple approach with transcription
        # In production, use a dedicated wake word detection library
        transcription = self.transcribe(audio_data)
        return "computer" in transcription.lower()

