"""
Text-to-Speech Service
Handles TTS using ElevenLabs API with local fallback
"""

import os
import asyncio
from dotenv import load_dotenv
import tempfile
import subprocess
import platform

# Try to import elevenlabs, but make it optional
try:
    from elevenlabs import generate, set_api_key, VoiceSettings
    ELEVENLABS_AVAILABLE = True
except ImportError:
    ELEVENLABS_AVAILABLE = False
    print("Warning: elevenlabs package not available. TTS will use local fallback only.")

# Load .env from project root
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
load_dotenv(env_path)
load_dotenv()  # Fallback to current directory

class TTSService:
    def __init__(self):
        # Support both ELEVENLABS_API_KEY and ELEVENLABS_API
        self.elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY") or os.getenv("ELEVENLABS_API")
        self.use_elevenlabs = bool(self.elevenlabs_api_key and ELEVENLABS_AVAILABLE)
        if self.use_elevenlabs:
            try:
                set_api_key(self.elevenlabs_api_key)
            except Exception as e:
                print(f"Warning: Failed to set ElevenLabs API key: {e}")
                self.use_elevenlabs = False
        print(f"TTS Service initialized - ElevenLabs: {self.use_elevenlabs}")
    
    async def synthesize(self, text: str, voice_id: str = "21m00Tcm4TlvDq8ikWAM"):
        """Synthesize text to speech"""
        try:
            if self.use_elevenlabs and ELEVENLABS_AVAILABLE:
                # Use ElevenLabs - generate() returns a generator, convert to bytes
                try:
                    audio_generator = generate(
                        text=text,
                        voice=voice_id,
                        model="eleven_monolingual_v1",
                        voice_settings=VoiceSettings(
                            stability=0.5,
                            similarity_boost=0.75
                        )
                    )
                    # Convert generator to bytes
                    audio_bytes = b"".join(audio_generator)
                    if audio_bytes:
                        return audio_bytes
                    else:
                        print("ElevenLabs returned empty audio, falling back to local TTS")
                        return await self._local_tts(text)
                except Exception as e:
                    print(f"ElevenLabs TTS error: {e}, falling back to local TTS")
                    return await self._local_tts(text)
            else:
                # Fallback to local TTS
                return await self._local_tts(text)
        except Exception as e:
            print(f"TTS synthesis error: {e}, trying local fallback")
            # Fallback to local TTS on error
            return await self._local_tts(text)
    
    async def _local_tts(self, text: str):
        """Local TTS fallback using system TTS"""
        try:
            # Run in executor to avoid blocking
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = asyncio.get_event_loop()
            audio_data = await loop.run_in_executor(None, self._system_tts, text)
            return audio_data
        except Exception as e:
            print(f"Local TTS error: {e}")
            return b""
    
    def _system_tts(self, text: str):
        """System TTS using platform-specific commands"""
        try:
            system = platform.system()
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
            temp_path = temp_file.name
            temp_file.close()
            
            if system == "Darwin":  # macOS
                # Use macOS 'say' command to generate audio (creates AIFF)
                aiff_path = temp_path.replace(".wav", ".aiff")
                subprocess.run(
                    ["say", "-v", "Samantha", "-o", aiff_path, text],
                    check=True,
                    timeout=30,
                    capture_output=True
                )
                # Convert AIFF to WAV using afconvert
                if os.path.exists(aiff_path):
                    subprocess.run(
                        ["afconvert", "-f", "WAVE", "-d", "LEI16", aiff_path, temp_path],
                        check=True,
                        timeout=10,
                        capture_output=True
                    )
                    # Remove the AIFF file
                    if os.path.exists(aiff_path):
                        os.remove(aiff_path)
            elif system == "Linux":
                # Try espeak or festival
                try:
                    subprocess.run(
                        ["espeak", "-s", "150", "-w", temp_path, text],
                        check=True,
                        timeout=30,
                        capture_output=True
                    )
                except (subprocess.CalledProcessError, FileNotFoundError):
                    # Try festival
                    try:
                        subprocess.run(
                            ["festival", "--tts", "--otype", "wav", "-o", temp_path],
                            input=text.encode(),
                            check=True,
                            timeout=30,
                            capture_output=True
                        )
                    except (subprocess.CalledProcessError, FileNotFoundError):
                        raise Exception("No TTS engine found (tried espeak and festival)")
            elif system == "Windows":
                # Try pyttsx3 on Windows
                try:
                    import pyttsx3
                    engine = pyttsx3.init()
                    engine.save_to_file(text, temp_path)
                    engine.runAndWait()
                except ImportError:
                    raise Exception("pyttsx3 not available on Windows")
            else:
                raise Exception(f"Unsupported platform: {system}")
            
            # Read the generated audio file
            if os.path.exists(temp_path):
                with open(temp_path, "rb") as f:
                    audio_data = f.read()
                os.remove(temp_path)
                return audio_data
            else:
                raise Exception("TTS file was not created")
                
        except subprocess.TimeoutExpired:
            print("TTS generation timed out")
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return b""
        except Exception as e:
            print(f"System TTS error: {e}")
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except:
                    pass
            return b""

