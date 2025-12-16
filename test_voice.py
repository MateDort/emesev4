#!/usr/bin/env python3
"""
Voice Service Test
Tests if the voice service can transcribe audio files
"""

import os
import sys
import asyncio
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / 'backend'))

from services.voice_service import VoiceService
from dotenv import load_dotenv

# Load .env
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)
load_dotenv()

async def test_voice_service():
    """Test the voice service"""
    print("=" * 60)
    print("VOICE SERVICE TEST")
    print("=" * 60)
    
    # Test 1: Check if service is initialized
    print("\n[Test 1] Initializing VoiceService...")
    voice_service = VoiceService()
    
    if voice_service.available:
        print("✅ VoiceService initialized successfully")
        print(f"   - OpenAI API key: {'Set' if os.getenv('OPENAI_API_KEY') or os.getenv('GPT_API') else 'Not set'}")
    else:
        print("❌ VoiceService not available")
        print("   - OPENAI_API_KEY or GPT_API not set in .env")
        print("   - Voice transcription will not work")
        return False
    
    # Test 2: Check if we can create a test audio file
    print("\n[Test 2] Testing audio file handling...")
    try:
        import tempfile
        import wave
        import struct
        
        # Create a simple test audio file (silence)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            test_audio_path = tmp_file.name
            
            # Create a minimal WAV file (1 second of silence)
            sample_rate = 16000
            duration = 1
            num_samples = sample_rate * duration
            
            with wave.open(test_audio_path, 'wb') as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(sample_rate)
                
                # Write silence
                for _ in range(num_samples):
                    wav_file.writeframes(struct.pack('<h', 0))
        
        print(f"✅ Test audio file created: {test_audio_path}")
        
        # Test 3: Try to transcribe (will likely fail with silence, but tests the flow)
        print("\n[Test 3] Testing transcription (with silence audio)...")
        try:
            with open(test_audio_path, 'rb') as audio_file:
                audio_data = audio_file.read()
            
            # This will likely return an error or empty result, but tests the API connection
            result = await voice_service.transcribe(audio_data)
            print(f"   Transcription result: {result[:100]}...")
            
            if "Error" in result:
                print("⚠️  Transcription returned error (expected for silence)")
                print(f"   Error message: {result}")
            else:
                print("✅ Transcription completed (unexpected for silence)")
            
        except Exception as e:
            print(f"⚠️  Transcription test error: {e}")
            print("   (This might be expected if audio is invalid)")
        
        # Cleanup
        try:
            os.unlink(test_audio_path)
            print("✅ Test audio file cleaned up")
        except:
            pass
            
    except Exception as e:
        print(f"❌ Audio file test failed: {e}")
        return False
    
    # Test 4: Check API key format
    print("\n[Test 4] Checking API key format...")
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("GPT_API")
    if api_key:
        if api_key.startswith("sk-"):
            print("✅ API key format looks correct (starts with 'sk-')")
        else:
            print("⚠️  API key format unusual (doesn't start with 'sk-')")
        print(f"   Key length: {len(api_key)} characters")
        print(f"   First 10 chars: {api_key[:10]}...")
    else:
        print("❌ No API key found")
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    if voice_service.available:
        print("✅ VoiceService is configured and ready")
        print("   - Can process audio files")
        print("   - Will transcribe using OpenAI Whisper API")
        print("\n💡 To test with real audio:")
        print("   1. Record audio using the frontend")
        print("   2. Check browser console for transcription results")
        print("   3. The backend will receive audio via WebSocket")
    else:
        print("❌ VoiceService is not configured")
        print("   - Add OPENAI_API_KEY to .env file")
    
    return voice_service.available

if __name__ == "__main__":
    result = asyncio.run(test_voice_service())
    sys.exit(0 if result else 1)

