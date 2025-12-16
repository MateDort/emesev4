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
    from elevenlabs import generate, set_api_key
    try:
        from elevenlabs.client import ElevenLabs
        ELEVENLABS_CLIENT_AVAILABLE = True
    except ImportError:
        ELEVENLABS_CLIENT_AVAILABLE = False
    ELEVENLABS_AVAILABLE = True
except ImportError:
    ELEVENLABS_AVAILABLE = False
    ELEVENLABS_CLIENT_AVAILABLE = False
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
        
        # Get voice ID from environment, with fallback to default
        # Support multiple env var names: ELEVENLABS_VOICE_ID, ELEVENLABS_VOICE, VOICE_ID
        self.default_voice_id = (
            os.getenv("ELEVENLABS_VOICE_ID") or 
            os.getenv("ELEVENLABS_VOICE") or 
            os.getenv("VOICE_ID") or 
            "21m00Tcm4TlvDq8ikWAM"  # Default voice
        )
        
        if self.use_elevenlabs:
            try:
                set_api_key(self.elevenlabs_api_key)
                # Also initialize client if available
                if ELEVENLABS_CLIENT_AVAILABLE:
                    self.client = ElevenLabs(api_key=self.elevenlabs_api_key)
                else:
                    self.client = None
                print(f"TTS Service initialized - ElevenLabs: True, Voice ID: {self.default_voice_id}")
            except Exception as e:
                print(f"Warning: Failed to set ElevenLabs API key: {e}")
                self.use_elevenlabs = False
                self.client = None
        else:
            self.client = None
            print(f"TTS Service initialized - ElevenLabs: False")
    
    async def synthesize(self, text: str, voice_id: str = None):
        """Synthesize text to speech"""
        # Use provided voice_id or fall back to default from env
        if voice_id is None:
            voice_id = self.default_voice_id
            
        try:
            if self.use_elevenlabs and ELEVENLABS_AVAILABLE:
                # Try using Client API first (more reliable)
                if self.client and ELEVENLABS_CLIENT_AVAILABLE:
                    try:
                        # Use the Client API which is more reliable
                        audio_generator = self.client.generate(
                            text=text,
                            voice=voice_id,
                            model="eleven_turbo_v2_5"
                        )
                    except Exception as e1:
                        try:
                            # Try without model
                            audio_generator = self.client.generate(
                                text=text,
                                voice=voice_id
                            )
                        except Exception as e2:
                            # Fallback to direct generate()
                            audio_generator = None
                else:
                    audio_generator = None
                
                # Fallback to direct generate() if client not available or failed
                if audio_generator is None:
                    try:
                        # Try newer models available on free tier, fallback to no model (uses default)
                        try:
                            # Try eleven_turbo_v2_5 (newer, faster, free tier compatible)
                            audio_generator = generate(
                                text=text,
                                voice=voice_id,
                                model="eleven_turbo_v2_5"
                            )
                        except Exception as e1:
                            try:
                                # Fallback to eleven_multilingual_v2
                                audio_generator = generate(
                                    text=text,
                                    voice=voice_id,
                                    model="eleven_multilingual_v2"
                                )
                            except Exception as e2:
                                # Final fallback: no model parameter (uses account default)
                                audio_generator = generate(
                                    text=text,
                                    voice=voice_id
                                )
                    except Exception as e3:
                        print(f"Failed to create audio generator: {e3}")
                        return await self._local_tts(text)
                
                # Convert generator/iterator to bytes
                # The generate() function returns a generator that yields bytes chunks
                audio_chunks = []
                chunk_count = 0
                try:
                    for chunk in audio_generator:
                        chunk_count += 1
                        chunk_type = type(chunk).__name__
                        
                        # Handle different chunk types
                        if isinstance(chunk, bytes):
                            audio_chunks.append(chunk)
                        elif isinstance(chunk, bytearray):
                            audio_chunks.append(bytes(chunk))
                        elif isinstance(chunk, int):
                            # ElevenLabs sometimes returns integers (byte values) - convert to bytes
                            audio_chunks.append(bytes([chunk]))
                        elif isinstance(chunk, (list, tuple)):
                            # If it's a list/tuple of integers, convert to bytes
                            try:
                                audio_chunks.append(bytes(chunk))
                            except (TypeError, ValueError):
                                # Skip if conversion fails
                                if chunk_count <= 3:
                                    print(f"ElevenLabs chunk {chunk_count}: type={chunk_type}, couldn't convert to bytes")
                        else:
                            # Log what we're skipping for debugging
                            if chunk_count <= 3:  # Only log first few to avoid spam
                                print(f"ElevenLabs chunk {chunk_count}: type={chunk_type}, value={str(chunk)[:50]}")
                except Exception as iter_error:
                    print(f"Error iterating ElevenLabs generator: {iter_error}")
                    return await self._local_tts(text)
                
                print(f"ElevenLabs: collected {len(audio_chunks)} audio chunks from {chunk_count} total chunks")
                
                # Join all byte chunks
                if audio_chunks:
                    audio_bytes = b"".join(audio_chunks)
                    if audio_bytes:
                        print(f"ElevenLabs: generated {len(audio_bytes)} bytes of audio")
                        return audio_bytes
                
                print(f"ElevenLabs returned empty or invalid audio ({chunk_count} chunks, {len(audio_chunks)} valid), falling back to local TTS")
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

