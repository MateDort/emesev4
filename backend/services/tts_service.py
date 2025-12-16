"""
Text-to-Speech Service
Handles TTS using ElevenLabs API with local fallback
"""

import os
from elevenlabs import generate, set_api_key, VoiceSettings
from dotenv import load_dotenv
import io

# Load .env from project root
import os
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
load_dotenv(env_path)
load_dotenv()  # Fallback to current directory

class TTSService:
    def __init__(self):
        # Support both ELEVENLABS_API_KEY and ELEVENLABS_API
        self.elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY") or os.getenv("ELEVENLABS_API")
        if self.elevenlabs_api_key:
            set_api_key(self.elevenlabs_api_key)
        self.use_elevenlabs = bool(self.elevenlabs_api_key)
    
    async def synthesize(self, text: str, voice_id: str = "21m00Tcm4TlvDq8ikWAM"):
        """Synthesize text to speech"""
        try:
            if self.use_elevenlabs:
                # Use ElevenLabs
                audio = generate(
                    text=text,
                    voice=voice_id,
                    model="eleven_monolingual_v1",
                    voice_settings=VoiceSettings(
                        stability=0.5,
                        similarity_boost=0.75
                    )
                )
                return audio
            else:
                # Fallback to local TTS (using pyttsx3 or similar)
                return self._local_tts(text)
        except Exception as e:
            # Fallback to local TTS on error
            return self._local_tts(text)
    
    def _local_tts(self, text: str):
        """Local TTS fallback"""
        try:
            # Try pyttsx3 if available
            try:
                import pyttsx3
                import tempfile
                engine = pyttsx3.init()
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
                temp_path = temp_file.name
                temp_file.close()
                
                engine.save_to_file(text, temp_path)
                engine.runAndWait()
                
                with open(temp_path, "rb") as f:
                    audio_data = f.read()
                os.remove(temp_path)
                return audio_data
            except ImportError:
                # pyttsx3 not installed - that's okay, it's optional
                pass
        except Exception as e:
            # Final fallback: return empty
            print(f"Local TTS error: {e}")
        return b""

