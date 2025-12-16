"""
Wake Word Detection Service
Uses pvporcupine for offline wake word detection with pyaudio for microphone input
"""

import pvporcupine
import pyaudio
import struct
import threading
import os
from typing import Callable, Optional
from dotenv import load_dotenv

# Load .env from project root
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
load_dotenv(env_path)
load_dotenv()

class WakeWordService:
    def __init__(self, wake_word_callback: Optional[Callable] = None):
        """
        Initialize wake word detection service
        
        Args:
            wake_word_callback: Function to call when wake word is detected
        """
        self.wake_word_callback = wake_word_callback
        self.is_listening = False
        self.porcupine = None
        self.audio_stream = None
        self.audio = None
        self.listening_thread = None
        
        # Get Picovoice access key from environment
        self.access_key = os.getenv("PICOVOICE_ACCESS_KEY")
        if not self.access_key:
            print("Warning: PICOVOICE_ACCESS_KEY not set. Wake word detection will be disabled.")
            print("Get a free access key at: https://console.picovoice.ai/")
            self.available = False
            return
        
        try:
            # Initialize Porcupine with "computer" wake word
            # Using default keyword_paths for "computer" - you can customize this
            self.porcupine = pvporcupine.create(
                access_key=self.access_key,
                keywords=['computer']  # You can add more keywords like ['computer', 'hey computer']
            )
            self.available = True
            print("✅ Wake word service initialized successfully")
        except Exception as e:
            print(f"Error initializing Porcupine: {e}")
            self.available = False
    
    def start_listening(self):
        """Start listening for wake word in a separate thread"""
        if not self.available:
            print("Wake word service not available")
            return
        
        if self.is_listening:
            print("Already listening for wake word")
            return
        
        self.is_listening = True
        self.listening_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.listening_thread.start()
        print("🎤 Started listening for wake word 'computer'...")
    
    def stop_listening(self):
        """Stop listening for wake word"""
        self.is_listening = False
        if self.audio_stream:
            try:
                self.audio_stream.stop_stream()
                self.audio_stream.close()
            except:
                pass
        if self.audio:
            try:
                self.audio.terminate()
            except:
                pass
        print("🛑 Stopped listening for wake word")
    
    def _listen_loop(self):
        """Main listening loop - runs in separate thread"""
        try:
            # Initialize PyAudio
            self.audio = pyaudio.PyAudio()
            
            # Get audio parameters from Porcupine
            sample_rate = self.porcupine.sample_rate
            frame_length = self.porcupine.frame_length
            channels = 1  # Mono audio
            
            # Open audio stream
            self.audio_stream = self.audio.open(
                rate=sample_rate,
                channels=channels,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=frame_length
            )
            
            print(f"🎧 Audio stream opened: {sample_rate}Hz, {channels} channel(s), frame_length={frame_length}")
            
            # Main detection loop
            while self.is_listening:
                try:
                    # Read audio frame
                    pcm = self.audio_stream.read(frame_length, exception_on_overflow=False)
                    pcm = struct.unpack_from("h" * frame_length, pcm)
                    
                    # Process with Porcupine
                    keyword_index = self.porcupine.process(pcm)
                    
                    # If wake word detected
                    if keyword_index >= 0:
                        print("✅ WAKE WORD DETECTED: 'computer'")
                        if self.wake_word_callback:
                            self.wake_word_callback()
                
                except Exception as e:
                    if self.is_listening:  # Only log if we're still supposed to be listening
                        print(f"Error in wake word detection loop: {e}")
                    break
        
        except Exception as e:
            print(f"Error in wake word listening thread: {e}")
        finally:
            # Cleanup
            if self.audio_stream:
                try:
                    self.audio_stream.stop_stream()
                    self.audio_stream.close()
                except:
                    pass
            if self.audio:
                try:
                    self.audio.terminate()
                except:
                    pass
    
    def __del__(self):
        """Cleanup on deletion"""
        self.stop_listening()
        if self.porcupine:
            try:
                self.porcupine.delete()
            except:
                pass

